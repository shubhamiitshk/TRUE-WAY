package com.trueway.app.pack

import android.content.Context
import android.media.MediaPlayer
import java.io.File
import java.io.FileInputStream
import java.security.MessageDigest
import java.util.concurrent.ConcurrentHashMap
import org.json.JSONObject

sealed interface ResolvedMedia {
    data class VerifiedPackFile(
        val packId: String,
        val releaseVersion: String,
        val file: File,
        val sha256: String,
        val assetOrigin: String
    ) : ResolvedMedia

    data class BundledApkAsset(
        val assetRelativePath: String
    ) : ResolvedMedia

    data class Rejected(
        val relativePath: String,
        val reason: RejectionReason
    ) : ResolvedMedia
}

enum class RejectionReason {
    UNSAFE_PATH_TRAVERSAL,
    STAGING_OR_BACKUP_DIR,
    MISSING_MANIFEST,
    NOT_IN_MANIFEST,
    FILE_MISSING_ON_DISK,
    SHA256_MISMATCH,
    SYNTHETIC_ASSET_BLOCKED_IN_PRODUCTION,
    ASSET_NOT_FOUND
}

data class ManifestFileEntry(
    val relativePath: String,
    val bytes: Long,
    val sha256: String,
    val assetOrigin: String
)

data class ParsedPackManifest(
    val packId: String,
    val releaseVersion: String,
    val filesByPath: Map<String, ManifestFileEntry>
)

private data class VerifiedFileStamp(
    val canonicalPath: String,
    val length: Long,
    val lastModified: Long,
    val sha256: String
)

fun interface BundledAssetChecker {
    fun existsInApkAssets(relativePath: String): Boolean
}

class PackMediaResolver(
    private val bundledAssetChecker: BundledAssetChecker,
    private val requireProductionClearedOrigin: Boolean = false
) {
    private val manifestCache = ConcurrentHashMap<String, ParsedPackManifest>()
    private val verifiedStampCache = ConcurrentHashMap<String, VerifiedFileStamp>()

    constructor(
        context: Context,
        requireProductionClearedOrigin: Boolean = false
    ) : this(
        bundledAssetChecker = BundledAssetChecker { path ->
            try {
                context.assets.open(path).close()
                true
            } catch (_: Exception) {
                false
            }
        },
        requireProductionClearedOrigin = requireProductionClearedOrigin
    )

    fun evictPackCache(packDir: File) {
        val prefix = runCatching { packDir.canonicalPath }.getOrDefault(packDir.absolutePath)
        manifestCache.keys.removeIf { it.startsWith(prefix) }
        verifiedStampCache.keys.removeIf { it.startsWith(prefix) }
    }

    fun resolve(relativePath: String, activePackDir: File?): ResolvedMedia {
        val normalizedRel = normalizeSafeRelativePath(relativePath)
            ?: return ResolvedMedia.Rejected(relativePath, RejectionReason.UNSAFE_PATH_TRAVERSAL)

        if (activePackDir != null) {
            when (val packResult = resolveFromPack(normalizedRel, activePackDir)) {
                is ResolvedMedia.VerifiedPackFile -> return packResult
                is ResolvedMedia.Rejected -> {
                    if (bundledAssetChecker.existsInApkAssets(normalizedRel)) {
                        return ResolvedMedia.BundledApkAsset(normalizedRel)
                    }
                    return packResult
                }
                is ResolvedMedia.BundledApkAsset -> return packResult
            }
        }

        return if (bundledAssetChecker.existsInApkAssets(normalizedRel)) {
            ResolvedMedia.BundledApkAsset(normalizedRel)
        } else {
            ResolvedMedia.Rejected(normalizedRel, RejectionReason.ASSET_NOT_FOUND)
        }
    }

    private fun resolveFromPack(normalizedRel: String, packDir: File): ResolvedMedia {
        val dirName = packDir.name
        if (dirName.startsWith(".staging-") || dirName.startsWith(".backup-")) {
            return ResolvedMedia.Rejected(normalizedRel, RejectionReason.STAGING_OR_BACKUP_DIR)
        }

        val packCanonicalRoot = runCatching { packDir.canonicalPath }.getOrNull()
            ?: return ResolvedMedia.Rejected(normalizedRel, RejectionReason.FILE_MISSING_ON_DISK)

        if (packCanonicalRoot.contains("/.staging-") || packCanonicalRoot.contains("/.backup-") ||
            packCanonicalRoot.contains("\\.staging-") || packCanonicalRoot.contains("\\.backup-")
        ) {
            return ResolvedMedia.Rejected(normalizedRel, RejectionReason.STAGING_OR_BACKUP_DIR)
        }

        val manifest = loadOrParseManifest(packDir, packCanonicalRoot)
            ?: return ResolvedMedia.Rejected(normalizedRel, RejectionReason.MISSING_MANIFEST)

        val entry = manifest.filesByPath[normalizedRel]
            ?: return ResolvedMedia.Rejected(normalizedRel, RejectionReason.NOT_IN_MANIFEST)

        if (requireProductionClearedOrigin && entry.assetOrigin == "SYNTHETIC_DEV") {
            return ResolvedMedia.Rejected(
                normalizedRel,
                RejectionReason.SYNTHETIC_ASSET_BLOCKED_IN_PRODUCTION
            )
        }

        val targetFile = File(packDir, normalizedRel)
        if (!targetFile.isFile) {
            return ResolvedMedia.Rejected(normalizedRel, RejectionReason.FILE_MISSING_ON_DISK)
        }

        val targetCanonical = runCatching { targetFile.canonicalPath }.getOrNull()
            ?: return ResolvedMedia.Rejected(normalizedRel, RejectionReason.UNSAFE_PATH_TRAVERSAL)

        if (!targetCanonical.startsWith(packCanonicalRoot + File.separator)) {
            return ResolvedMedia.Rejected(normalizedRel, RejectionReason.UNSAFE_PATH_TRAVERSAL)
        }

        val length = targetFile.length()
        val lastModified = targetFile.lastModified()
        val cachedStamp = verifiedStampCache[targetCanonical]

        val actualSha256 = if (
            cachedStamp != null &&
            cachedStamp.length == length &&
            cachedStamp.lastModified == lastModified &&
            cachedStamp.sha256 == entry.sha256
        ) {
            cachedStamp.sha256
        } else {
            val computed = sha256Hex(targetFile)
            if (!computed.equals(entry.sha256, ignoreCase = true)) {
                verifiedStampCache.remove(targetCanonical)
                return ResolvedMedia.Rejected(normalizedRel, RejectionReason.SHA256_MISMATCH)
            }
            verifiedStampCache[targetCanonical] = VerifiedFileStamp(
                canonicalPath = targetCanonical,
                length = length,
                lastModified = lastModified,
                sha256 = computed
            )
            computed
        }

        return ResolvedMedia.VerifiedPackFile(
            packId = manifest.packId,
            releaseVersion = manifest.releaseVersion,
            file = targetFile,
            sha256 = actualSha256,
            assetOrigin = entry.assetOrigin
        )
    }

    private fun loadOrParseManifest(packDir: File, cacheKey: String): ParsedPackManifest? {
        manifestCache[cacheKey]?.let { return it }
        val manifestFile = File(packDir, "manifest.cjson")
        if (!manifestFile.isFile) return null
        return runCatching {
            val root = JSONObject(manifestFile.readText(Charsets.UTF_8))
            val packId = root.getString("pack_id")
            val version = root.getString("release_version")
            val filesArray = root.getJSONArray("files")
            val map = HashMap<String, ManifestFileEntry>(filesArray.length())
            for (i in 0 until filesArray.length()) {
                val item = filesArray.getJSONObject(i)
                val path = item.getString("path")
                val sha = item.getString("sha256").lowercase()
                val bytes = item.optLong("bytes", -1L)
                val origin = item.optString("asset_origin", "PRODUCTION_CLEARED")
                map[path] = ManifestFileEntry(path, bytes, sha, origin)
            }
            ParsedPackManifest(packId, version, map).also { manifestCache[cacheKey] = it }
        }.getOrNull()
    }

    private fun normalizeSafeRelativePath(path: String): String? {
        val trimmed = path.trim().replace('\\', '/')
        if (trimmed.isEmpty() || trimmed.startsWith("/") || trimmed.contains("..")) return null
        val segments = trimmed.split('/')
        if (segments.any { it.isEmpty() || it == "." || it == ".." }) return null
        return segments.joinToString("/")
    }

    private fun sha256Hex(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        FileInputStream(file).use { fis ->
            val buffer = ByteArray(16 * 1024)
            var read = fis.read(buffer)
            while (read > 0) {
                digest.update(buffer, 0, read)
                read = fis.read(buffer)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }
}

fun MediaPlayer.setResolvedDataSource(context: Context, media: ResolvedMedia): Boolean {
    return when (media) {
        is ResolvedMedia.VerifiedPackFile -> {
            FileInputStream(media.file).use { fis ->
                setDataSource(fis.fd)
            }
            true
        }
        is ResolvedMedia.BundledApkAsset -> {
            context.assets.openFd(media.assetRelativePath).use { afd ->
                setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
            }
            true
        }
        is ResolvedMedia.Rejected -> false
    }
}
