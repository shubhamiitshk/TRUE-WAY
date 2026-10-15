package com.trueway.app.pack

import android.content.Context
import com.trueway.app.touchpoint.TouchpointVerifier
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.util.zip.ZipFile

/**
 * On-device pack importer (F006; ADR-0006; System §VI; blueprint §9.3).
 * Mirrors `pack-builder/build_pack.py --verify` check-for-check:
 *
 * 1. Reject unsafe archive paths (absolute, `..`, executables) BEFORE writing.
 * 2. Verify the detached signature over the manifest bytes BEFORE trusting
 *    any digest: release Ed25519 against the pinned publisher key, or the
 *    demo scheme only when [allowDemo] is explicitly true (debug/tests).
 * 3. Enforce the replay policy: release below [minSafeVersion] is refused.
 * 4. Verify every file's SHA-256 + size, with unpacked-size caps (zip-bomb guard).
 * 5. Activate atomically (previous pack retained as backup until the new one
 *    reads back); any failure rolls back. The private journal lives in a
 *    separate database file and is never touched here (ADR-0008).
 *
 * Pure `java.io` + org.json: every rule below is JVM-testable with real
 * generated fixtures. No network anywhere in this file.
 */

data class PackSummary(
    val packId: String,
    val releaseVersion: String,
    val placeCount: Int,
    val signingKeyId: String,
    val visionModelId: String?,
    val visionDim: Int?,
)

enum class PackReject {
    BAD_FORMAT,
    UNSAFE_PATH,
    UNLISTED_ENTRY,
    BAD_SIGNATURE,
    UNKNOWN_PUBLISHER,
    DOWNGRADE,
    DIGEST_MISMATCH,
    TOO_LARGE,
    LOW_STORAGE,
    IO_ERROR,
}

sealed interface PackVerifyResult {
    data class Ok(val summary: PackSummary) : PackVerifyResult
    data class Rejected(val reason: PackReject, val detail: String = "") : PackVerifyResult
}

sealed interface PackInstallResult {
    data class Active(val summary: PackSummary) : PackInstallResult
    data class Rejected(val reason: PackReject, val detail: String = "") : PackInstallResult
}

/** keyId → raw 32-byte Ed25519 public key. */
typealias PublisherTrust = Map<String, ByteArray>

object PackImporter {
    var onBeforePackDirectorySwap: ((File) -> Unit)? = null
    const val MAX_UNPACKED_BYTES = 1024L * 1024 * 1024 // 1 GiB zip-bomb ceiling
    const val MAX_FILES = 20_000
    const val ROLLBACK_BUFFER_BYTES = 32L * 1024 * 1024 // headroom to keep a backup during activate
    private val EXECUTABLE_ENDINGS = listOf(".exe", ".dll", ".so", ".apk", ".sh", ".bat", ".ps1")

    /** Thrown when the real extracted byte count exceeds [MAX_UNPACKED_BYTES]. */
    private class UnpackTooLarge : Exception()

    fun verifyPackage(
        pkg: File,
        trust: PublisherTrust,
        allowDemo: Boolean,
        minSafeVersion: String? = null,
    ): PackVerifyResult {
        val zip: ZipFile
        try {
            zip = ZipFile(pkg)
        } catch (_: Exception) {
            return PackVerifyResult.Rejected(PackReject.BAD_FORMAT, "not a zip")
        }
        return zip.use {
            val names = it.entries().toList().map { e -> e.name }
            if (names.size > MAX_FILES) {
                return PackVerifyResult.Rejected(PackReject.TOO_LARGE, "file count")
            }
            var total = 0L
            for (e in it.entries()) {
                total += maxOf(e.size, 0L)
                if (total > MAX_UNPACKED_BYTES) {
                    return PackVerifyResult.Rejected(PackReject.TOO_LARGE, "unpacked size")
                }
            }
            unsafePath(names)?.let { bad ->
                return PackVerifyResult.Rejected(PackReject.UNSAFE_PATH, bad)
            }
            val manifestBytes = try {
                it.readEntry("manifest.cjson") ?: return PackVerifyResult.Rejected(
                    PackReject.BAD_FORMAT, "no manifest.cjson",
                )
            } catch (_: Exception) {
                return PackVerifyResult.Rejected(PackReject.BAD_FORMAT, "manifest unreadable")
            }
            val sigBytes = try {
                it.readEntry("manifest.ed25519") ?: return PackVerifyResult.Rejected(
                    PackReject.BAD_FORMAT, "no manifest.ed25519",
                )
            } catch (_: Exception) {
                return PackVerifyResult.Rejected(PackReject.BAD_FORMAT, "signature unreadable")
            }
            val manifest = try {
                JSONObject(manifestBytes.toString(Charsets.UTF_8))
            } catch (_: Exception) {
                return PackVerifyResult.Rejected(PackReject.BAD_FORMAT, "manifest not JSON")
            }
            val keyId = manifest.optString("signing_key_id").takeIf { s -> s.isNotBlank() }
                ?: return PackVerifyResult.Rejected(PackReject.BAD_FORMAT, "no signing_key_id")

            // Signature BEFORE digests (never trust listed hashes first).
            if (keyId == "DEMO-KEY-DO-NOT-SHIP") {
                if (!allowDemo) {
                    return PackVerifyResult.Rejected(PackReject.BAD_SIGNATURE, "demo key not allowed")
                }
                if (!verifyDemo(manifestBytes, sigBytes)) {
                    return PackVerifyResult.Rejected(PackReject.BAD_SIGNATURE, "demo mismatch")
                }
            } else {
                val pub = trust[keyId]
                    ?: return PackVerifyResult.Rejected(PackReject.UNKNOWN_PUBLISHER, keyId)
                if (!TouchpointVerifier.ed25519Verify(pub, manifestBytes, sigBytes)) {
                    return PackVerifyResult.Rejected(PackReject.BAD_SIGNATURE, "ed25519 mismatch")
                }
            }

            val release = manifest.optString("release_version")
            if (release.isBlank()) {
                return PackVerifyResult.Rejected(PackReject.BAD_FORMAT, "no release_version")
            }
            if (minSafeVersion != null && compareVersions(release, minSafeVersion) < 0) {
                return PackVerifyResult.Rejected(PackReject.DOWNGRADE, "$release < $minSafeVersion")
            }

            val files = manifest.optJSONArray("files")
                ?: return PackVerifyResult.Rejected(PackReject.BAD_FORMAT, "no files")
            val dig = MessageDigest.getInstance("SHA-256")
            for (i in 0 until files.length()) {
                val f = files.optJSONObject(i) ?: return PackVerifyResult.Rejected(
                    PackReject.BAD_FORMAT, "file entry $i",
                )
                val path = f.optString("path")
                val expectHex = f.optString("sha256")
                val expectSize = f.optLong("bytes", -1)
                val data = try {
                    it.readEntry(path)
                } catch (_: Exception) {
                    null
                } ?: return PackVerifyResult.Rejected(PackReject.DIGEST_MISMATCH, "missing $path")
                if (data.size.toLong() != expectSize) {
                    return PackVerifyResult.Rejected(PackReject.DIGEST_MISMATCH, "size $path")
                }
                val actual = dig.digest(data).toHex()
                if (!actual.equals(expectHex, ignoreCase = true)) {
                    return PackVerifyResult.Rejected(PackReject.DIGEST_MISMATCH, "sha256 $path")
                }
            }

            // Signed-manifest file-set completeness: the signature commits to the
            // manifest, so the manifest must commit to the EXACT archive content.
            // Reject any file entry not listed in `files` (besides the two
            // manifest parts) so a signed pack cannot smuggle extra unsigned
            // files that would extract into the live pack dir.
            val listed = buildSet {
                for (i in 0 until files.length()) {
                    files.optJSONObject(i)?.optString("path")?.let { add(it) }
                }
                add("manifest.cjson")
                add("manifest.ed25519")
            }
            val unlisted = names.firstOrNull { n ->
                !n.endsWith("/") && n !in listed
            }
            if (unlisted != null) {
                return PackVerifyResult.Rejected(PackReject.UNLISTED_ENTRY, unlisted)
            }

            val packId = manifest.optString("pack_id").takeIf { s -> s.isNotBlank() }
                ?: return PackVerifyResult.Rejected(PackReject.BAD_FORMAT, "no pack_id")
            val vision = manifest.optJSONObject("vision")
            PackVerifyResult.Ok(
                PackSummary(
                    packId = packId,
                    releaseVersion = release,
                    placeCount = manifest.optInt("place_count", 0),
                    signingKeyId = keyId,
                    visionModelId = vision?.optString("model_id")?.ifBlank { null },
                    visionDim = vision?.optInt("dim", -1)?.takeIf { d -> d > 0 },
                ),
            )
        }
    }

    /**
     * Verify → stage → atomic activate. [packsDir]/`<packId>/<version>/` holds
     * the live pack; the previous version is kept as backup until the new one
     * verifies on disk, then removed. Returns the active summary.
     */
    fun installPackage(
        pkg: File,
        packsDir: File,
        trust: PublisherTrust,
        allowDemo: Boolean,
        minSafeVersion: String? = null,
        activeStore: ActivePackStore,
    ): PackInstallResult {
        val verified = verifyPackage(pkg, trust, allowDemo, minSafeVersion)
        if (verified is PackVerifyResult.Rejected) {
            return PackInstallResult.Rejected(verified.reason, verified.detail)
        }
        val summary = (verified as PackVerifyResult.Ok).summary
        val target = File(File(packsDir, summary.packId), summary.releaseVersion)
        val staging = File(packsDir, ".staging-${summary.packId}-${summary.releaseVersion}")
        try {
            // §9.3 [G] free-storage preflight (PACK-024): refuse BEFORE staging
            // if the device can't hold compressed + unpacked + a rollback buffer,
            // so a full disk never deletes the active pack.
            val estimatedUnpacked = ZipFile(pkg).use { z ->
                z.entries().toList().sumOf { maxOf(it.size, 0L) }
            }
            val required = pkg.length() + estimatedUnpacked + ROLLBACK_BUFFER_BYTES
            packsDir.mkdirs()
            val free = packsDir.usableSpace
            if (free in 1 until required) {
                return PackInstallResult.Rejected(
                    PackReject.LOW_STORAGE, "need ~$required bytes, $free free",
                )
            }
            staging.deleteRecursively()
            staging.mkdirs()
            var written = 0L
            ZipFile(pkg).use { zip ->
                for (entry in zip.entries()) {
                    val out = File(staging, entry.name)
                    if (!out.canonicalPath.startsWith(staging.canonicalPath + File.separator)) {
                        throw SecurityException("escape: ${entry.name}")
                    }
                    if (entry.isDirectory) {
                        out.mkdirs()
                    } else {
                        out.parentFile?.mkdirs()
                        zip.getInputStream(entry).use { ins ->
                            out.outputStream().use { outs ->
                                val buf = ByteArray(64 * 1024)
                                while (true) {
                                    val r = ins.read(buf)
                                    if (r < 0) break
                                    written += r
                                    // Cap the real extraction, not just the
                                    // declared size (zip-bomb that lies about size).
                                    if (written > MAX_UNPACKED_BYTES) throw UnpackTooLarge()
                                    outs.write(buf, 0, r)
                                }
                            }
                        }
                    }
                }
            }
            // Re-verify digests post-extract (TOCTOU guard on the staged tree).
            val stagedPkg = stageAsZip(staging)
            val recheck = verifyPackage(stagedPkg, trust, allowDemo, minSafeVersion)
            stagedPkg.delete()
            if (recheck is PackVerifyResult.Rejected) {
                staging.deleteRecursively()
                return PackInstallResult.Rejected(recheck.reason, "post-extract: ${recheck.detail}")
            }
            // Atomic-ish activate with backup. Snapshot whatever currently
            // occupies `target` (covers reinstalling the SAME version, where
            // target IS the live dir) so a failed rename can be rolled back
            // instead of leaving the active pack destroyed.
            val backup = File(packsDir, ".backup-${summary.packId}")
            backup.deleteRecursively()
            target.parentFile?.mkdirs()
            onBeforePackDirectorySwap?.invoke(target)
            onBeforePackDirectorySwap?.invoke(File(packsDir, summary.packId))
            var backedUp = false
            if (target.exists()) {
                backedUp = target.renameTo(backup)
                if (!backedUp) target.deleteRecursively() // best effort if rename unsupported
            }
            if (!staging.renameTo(target)) {
                staging.deleteRecursively()
                if (backedUp) backup.renameTo(target) // restore the live pack
                return PackInstallResult.Rejected(PackReject.IO_ERROR, "activate rename")
            }
            if (!File(target, "manifest.cjson").exists()) {
                // New tree unreadable: restore the backup and fail closed.
                target.deleteRecursively()
                if (backedUp) backup.renameTo(target)
                return PackInstallResult.Rejected(PackReject.IO_ERROR, "activation lost")
            }
            activeStore.setActive(summary.packId, summary.releaseVersion)
            // Prune older versions + any backup, keep only the active one.
            File(packsDir, summary.packId).listFiles()
                ?.filter { it.isDirectory && it.name != summary.releaseVersion && !it.name.startsWith(".") }
                ?.forEach { it.deleteRecursively() }
            backup.deleteRecursively()
            return PackInstallResult.Active(summary)
        } catch (e: UnpackTooLarge) {
            staging.deleteRecursively()
            return PackInstallResult.Rejected(PackReject.TOO_LARGE, "unpacked size cap")
        } catch (e: SecurityException) {
            staging.deleteRecursively()
            return PackInstallResult.Rejected(PackReject.UNSAFE_PATH, e.message ?: "")
        } catch (e: Exception) {
            staging.deleteRecursively()
            return PackInstallResult.Rejected(PackReject.IO_ERROR, e.message ?: "")
        }
    }

    fun deletePack(packsDir: File, packId: String, activeStore: ActivePackStore): Boolean {
        val packDir = File(packsDir, packId)
        onBeforePackDirectorySwap?.invoke(packDir)
        val ok = packDir.deleteRecursively()
        activeStore.clearActive(packId)
        return ok
    }

    // ---- internals ---------------------------------------------------------

    internal fun unsafePath(names: List<String>): String? {
        for (n in names) {
            if (n.startsWith("/") || n.startsWith("\\")) return n
            val parts = n.split('/', '\\')
            if (".." in parts) return n
            val low = n.lowercase()
            if (EXECUTABLE_ENDINGS.any { low.endsWith(it) }) return n
        }
        return null
    }

    /** Demo scheme (pack-builder `--demo-key`): SHA-256(manifest) with a marker prefix. */
    internal fun verifyDemo(manifestBytes: ByteArray, sigAscii: ByteArray): Boolean {
        return try {
            val raw = java.util.Base64.getDecoder().decode(sigAscii.toString(Charsets.UTF_8).trim())
            val prefix = "DEMO-SIGNATURE:".toByteArray()
            if (!raw.copyOf(prefix.size).contentEquals(prefix)) return false
            val expect = MessageDigest.getInstance("SHA-256").digest(manifestBytes)
            raw.copyOfRange(prefix.size, raw.size).contentEquals(expect)
        } catch (_: Exception) {
            false
        }
    }

    internal fun compareVersions(a: String, b: String): Int {
        val pa = a.split(".")
        val pb = b.split(".")
        for (i in 0 until maxOf(pa.size, pb.size)) {
            val x = pa.getOrNull(i)?.toIntOrNull() ?: 0
            val y = pb.getOrNull(i)?.toIntOrNull() ?: 0
            if (x != y) return x.compareTo(y)
        }
        return 0
    }

    private fun ZipFile.readEntry(name: String): ByteArray? {
        val e = getEntry(name) ?: return null
        if (e.isDirectory) return null
        return getInputStream(e).use { it.readBytes() }
    }

    /** Re-zip a staged tree so post-extract verification reuses one code path. */
    private fun stageAsZip(staging: File): File {
        val tmp = File.createTempFile("restage", ".twpkg")
        java.util.zip.ZipOutputStream(tmp.outputStream()).use { zos ->
            staging.walkTopDown().filter { it.isFile }.forEach { f ->
                val rel = staging.toPath().relativize(f.toPath()).toString().replace('\\', '/')
                zos.putNextEntry(java.util.zip.ZipEntry(rel))
                f.inputStream().use { it.copyTo(zos) }
                zos.closeEntry()
            }
        }
        return tmp
    }

    private fun ByteArray.toHex(): String = joinToString("") { "%02x".format(it) }
}

/** Persisted active-pack pointer (pack_id → version). */
interface ActivePackStore {
    fun getActive(packId: String): String?
    fun setActive(packId: String, version: String)
    fun clearActive(packId: String)
    fun allActive(): Map<String, String> = emptyMap()
}

class PrefsActivePackStore(context: Context) : ActivePackStore {
    private val prefs = context.getSharedPreferences("trueway_packs", Context.MODE_PRIVATE)

    override fun getActive(packId: String): String? =
        prefs.getString("active:$packId", null)

    override fun setActive(packId: String, version: String) {
        prefs.edit().putString("active:$packId", version).apply()
    }

    override fun clearActive(packId: String) {
        prefs.edit().remove("active:$packId").apply()
    }

    override fun allActive(): Map<String, String> {
        val result = mutableMapOf<String, String>()
        for ((k, v) in prefs.all) {
            if (k.startsWith("active:") && v is String) {
                result[k.removePrefix("active:")] = v
            }
        }
        return result
    }
}
