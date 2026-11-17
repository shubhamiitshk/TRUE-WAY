package com.trueway.app.pack

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * In-app HTTPS pack downloader (delivery Option A, see
 * TRUEWAY_PARTNERSHIP_AND_MONETISATION_STRATEGY.md and the delivery decision:
 * in-app download from CDN / FastAPI for expansion corridors).
 *
 * Mirrors `PackImporter.installPackage` end-to-end: download manifest bytes +
 * each listed component over HTTPS, reassemble a byte-preserved `.twpkg`, then
 * verify + activate through the exact same importer used for manual import.
 * Transparency: no inference, no invention — only the bytes the signed
 * manifest lists, in listed order.
 */
object PackDownloader {
    private const val CONNECT_TIMEOUT_MS = 10_000
    private const val READ_TIMEOUT_MS = 30_000

    /**
     * Pack version an OTA entitlement unlocks. The CDN catalog (pack-builder/catalog.json)
     * registers the flat dist pack archives (release_version 2026.10.1); the 2026.11.1 rebuilds are nested in
     * same-named directories and are NOT served yet. Bump to 2026.11.1 once they are
     * flattened + re-registered in the catalog. GT/global-icons packs are also
     * unverified content until the candidate corpora pass human review.
     */
    const val ENTITLED_PACK_VERSION = "2026.10.1"

    /** Default distribution origin. Swap for staging by setting [TRUEWAY_BASE_URL]. */
    const val TRUEWAY_BASE_URL = "https://trueway.travel"

    data class Progress(
        val fetchedComponents: Int,
        val totalComponents: Int,
        val bytesDownloaded: Long,
        val totalBytesExpected: Long,
    )

    sealed interface Result {
        data class Active(val summary: PackSummary) : Result
        data class Failed(val stage: String, val detail: String) : Result
    }

    /** One `Path/Bytes/Sha256` row from the manifest's `files` array. */
    data class ManifestFile(val path: String, val bytes: Long, val sha256: String)

    /** URL-encode each path segment (paths from the manifest are ASCII but be safe). */
    fun encodeComponent(path: String): String =
        path.split('/')
            .filter { it.isNotEmpty() }
            .joinToString("/") { java.net.URLEncoder.encode(it, "UTF-8").replace("+", "%20") }

    /** Parse the signed manifest's file list (path/bytes/sha256). Throws on bad input. */
    fun parseManifestFiles(manifestBytes: ByteArray): List<ManifestFile> {
        val obj = JSONObject(String(manifestBytes, Charsets.UTF_8))
        val arr = obj.optJSONArray("files") ?: return emptyList()
        val out = mutableListOf<ManifestFile>()
        for (i in 0 until arr.length()) {
            val f = arr.optJSONObject(i) ?: continue
            val path = f.optString("path").takeIf { it.isNotBlank() && it != "null" } ?: continue
            out.add(ManifestFile(path, f.optLong("bytes", 0L), f.optString("sha256")))
        }
        return out
    }

    private fun httpGet(url: String): ByteArray {
        val conn = (URL(url).openConnection() as HttpURLConnection).apply {
            connectTimeout = CONNECT_TIMEOUT_MS
            readTimeout = READ_TIMEOUT_MS
            requestMethod = "GET"
            instanceFollowRedirects = true
        }
        try {
            val code = conn.responseCode
            if (code !in 200..299) throw java.io.IOException("HTTP $code for $url")
            return conn.inputStream.use { it.readBytes() }
        } finally {
            conn.disconnect()
        }
    }

    /**
     * Download [packId]@[version] from [baseUrl] and install it.
     * [onProgress] is called on every completed component.
     */
    suspend fun downloadAndInstall(
        context: Context,
        packId: String,
        version: String,
        baseUrl: String = TRUEWAY_BASE_URL,
        allowDemo: Boolean = false,
        minSafeVersion: String? = null,
        onProgress: (Progress) -> Unit = {},
    ): Result = withContext(Dispatchers.IO) {
        val packsDir = File(context.filesDir, "packs")
        try {
            onProgress(Progress(0, -1, 0, 0))
            val manifestBytes = httpGet("$baseUrl/v1/packs/$packId/$version/manifest.cjson")
            val sigBytes = httpGet("$baseUrl/v1/packs/$packId/$version/manifest.ed25519")
            val files = parseManifestFiles(manifestBytes)
            if (files.isEmpty()) return@withContext Result.Failed("manifest", "manifest has no files")
            val totalBytes = files.sumOf { it.bytes }

            val tmp = File(context.cacheDir, "download-$packId-$version.twpkg")
            try {
                FileOutputStream(tmp).use { out ->
                    ZipOutputStream(out).use { zip ->
                        zip.setLevel(6)
                        zip.putNextEntry(ZipEntry("manifest.cjson")); zip.write(manifestBytes); zip.closeEntry()
                        zip.putNextEntry(ZipEntry("manifest.ed25519")); zip.write(sigBytes); zip.closeEntry()
                        var done = 0L
                        for ((i, f) in files.withIndex()) {
                            val bytes = httpGet("$baseUrl/v1/packs/$packId/$version/${encodeComponent(f.path)}")
                            zip.putNextEntry(ZipEntry(f.path)); zip.write(bytes); zip.closeEntry()
                            done += bytes.size
                            onProgress(Progress(i + 1, files.size, done, totalBytes))
                        }
                    }
                }
                val activeStore = PrefsActivePackStore(context)
                val install = PackImporter.installPackage(
                    pkg = tmp,
                    packsDir = packsDir,
                    trust = PackPublisherTrust.load(context),
                    allowDemo = allowDemo,
                    minSafeVersion = minSafeVersion,
                    activeStore = activeStore,
                )
                when (install) {
                    is PackInstallResult.Active -> Result.Active(install.summary)
                    is PackInstallResult.Rejected ->
                        Result.Failed("install", "${install.reason} ${install.detail}".trim())
                }
            } finally {
                runCatching { tmp.delete() }
            }
        } catch (e: java.io.IOException) {
            Result.Failed("network", e.message ?: "download failed")
        } catch (e: Exception) {
            Result.Failed("error", "${e.javaClass.simpleName}: ${e.message}")
        }
    }
}
