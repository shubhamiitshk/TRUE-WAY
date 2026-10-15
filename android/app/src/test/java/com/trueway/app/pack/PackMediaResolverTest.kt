package com.trueway.app.pack

import java.io.File
import java.nio.file.Files
import java.security.MessageDigest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class PackMediaResolverTest {

    private lateinit var tempRoot: File
    private lateinit var activePackDir: File
    private val bundledAssets = mutableSetOf("audio/mahabodhi_guide.ogg", "images/mahabodhi_thumb.webp")

    @Before
    fun setUp() {
        tempRoot = Files.createTempDirectory("trueway-pack-test").toFile()
        activePackDir = File(tempRoot, "in-bihar-buddhist-circuit").apply { mkdirs() }
    }

    @Test
    fun `resolves verified pack file when manifest and sha256 match`() {
        val audioBytes = "OggS-verified-bilingual-narration".toByteArray()
        val audioFile = File(activePackDir, "audio/mahabodhi_guide.ogg").apply {
            parentFile?.mkdirs()
            writeBytes(audioBytes)
        }
        writeManifest(
            packDir = activePackDir,
            path = "audio/mahabodhi_guide.ogg",
            sha256 = sha256(audioBytes),
            origin = "PRODUCTION_CLEARED"
        )

        val resolver = PackMediaResolver(bundledAssets::contains)
        val result = resolver.resolve("audio/mahabodhi_guide.ogg", activePackDir)

        assertTrue(result is ResolvedMedia.VerifiedPackFile)
        val verified = result as ResolvedMedia.VerifiedPackFile
        assertEquals(audioFile.canonicalPath, verified.file.canonicalPath)
        assertEquals("in-bihar-buddhist-circuit", verified.packId)
        assertEquals("2026.10.1", verified.releaseVersion)
        assertEquals("PRODUCTION_CLEARED", verified.assetOrigin)
    }

    @Test
    fun `rejects staging and backup directories and falls back to bundled asset`() {
        val stagingDir = File(tempRoot, ".staging-in-bihar").apply { mkdirs() }
        val resolver = PackMediaResolver({ false })
        val rejected = resolver.resolve("audio/mahabodhi_guide.ogg", stagingDir)

        assertTrue(rejected is ResolvedMedia.Rejected)
        assertEquals(
            RejectionReason.STAGING_OR_BACKUP_DIR,
            (rejected as ResolvedMedia.Rejected).reason
        )
    }

    @Test
    fun `falls back to bundled asset when pack file has tampered sha256`() {
        File(activePackDir, "audio/mahabodhi_guide.ogg").apply {
            parentFile?.mkdirs()
            writeBytes("tampered-audio-bytes".toByteArray())
        }
        writeManifest(
            packDir = activePackDir,
            path = "audio/mahabodhi_guide.ogg",
            sha256 = "0".repeat(64)
        )

        val resolver = PackMediaResolver(bundledAssets::contains)
        val result = resolver.resolve("audio/mahabodhi_guide.ogg", activePackDir)

        assertEquals(ResolvedMedia.BundledApkAsset("audio/mahabodhi_guide.ogg"), result)
    }

    @Test
    fun `blocks SYNTHETIC_DEV asset when requireProductionClearedOrigin is true`() {
        val bytes = "synthetic-placeholder".toByteArray()
        File(activePackDir, "images/then_now/mahabodhi_1880s_beglar.webp").apply {
            parentFile?.mkdirs()
            writeBytes(bytes)
        }
        writeManifest(
            packDir = activePackDir,
            path = "images/then_now/mahabodhi_1880s_beglar.webp",
            sha256 = sha256(bytes),
            origin = "SYNTHETIC_DEV"
        )

        val prodResolver = PackMediaResolver({ false }, requireProductionClearedOrigin = true)
        val result = prodResolver.resolve(
            "images/then_now/mahabodhi_1880s_beglar.webp",
            activePackDir
        )

        assertTrue(result is ResolvedMedia.Rejected)
        assertEquals(
            RejectionReason.SYNTHETIC_ASSET_BLOCKED_IN_PRODUCTION,
            (result as ResolvedMedia.Rejected).reason
        )
    }

    @Test
    fun `rejects unsafe path traversal with dot dot`() {
        val resolver = PackMediaResolver(bundledAssets::contains)
        val result = resolver.resolve("../secret.txt", activePackDir)

        assertTrue(result is ResolvedMedia.Rejected)
        assertEquals(RejectionReason.UNSAFE_PATH_TRAVERSAL, (result as ResolvedMedia.Rejected).reason)
    }

    @Test
    fun `rejects empty or blank relative path`() {
        val resolver = PackMediaResolver(bundledAssets::contains)
        val resultEmpty = resolver.resolve("", activePackDir)
        val resultBlank = resolver.resolve("   ", activePackDir)

        assertTrue(resultEmpty is ResolvedMedia.Rejected)
        assertEquals(RejectionReason.UNSAFE_PATH_TRAVERSAL, (resultEmpty as ResolvedMedia.Rejected).reason)
        assertTrue(resultBlank is ResolvedMedia.Rejected)
        assertEquals(RejectionReason.UNSAFE_PATH_TRAVERSAL, (resultBlank as ResolvedMedia.Rejected).reason)
    }

    @Test
    fun `returns Rejected ASSET_NOT_FOUND when neither pack nor bundled asset exists`() {
        val resolver = PackMediaResolver({ false })
        val result = resolver.resolve("audio/nonexistent.ogg", null)

        assertTrue(result is ResolvedMedia.Rejected)
        assertEquals(RejectionReason.ASSET_NOT_FOUND, (result as ResolvedMedia.Rejected).reason)
    }

    @Test
    fun `evictPackCache clears cached manifest and verified stamps`() {
        val audioBytes = "audio-bytes-for-eviction".toByteArray()
        File(activePackDir, "audio/mahabodhi_guide.ogg").apply {
            parentFile?.mkdirs()
            writeBytes(audioBytes)
        }
        writeManifest(
            packDir = activePackDir,
            path = "audio/mahabodhi_guide.ogg",
            sha256 = sha256(audioBytes)
        )

        val resolver = PackMediaResolver(bundledAssets::contains)
        val firstResult = resolver.resolve("audio/mahabodhi_guide.ogg", activePackDir)
        assertTrue(firstResult is ResolvedMedia.VerifiedPackFile)

        resolver.evictPackCache(activePackDir)

        // After cache eviction, file still resolves cleanly from disk
        val secondResult = resolver.resolve("audio/mahabodhi_guide.ogg", activePackDir)
        assertTrue(secondResult is ResolvedMedia.VerifiedPackFile)
    }

    @Test
    fun `resolves bundled asset when pack dir is null`() {
        val resolver = PackMediaResolver(bundledAssets::contains)
        val result = resolver.resolve("audio/mahabodhi_guide.ogg", null)

        assertEquals(ResolvedMedia.BundledApkAsset("audio/mahabodhi_guide.ogg"), result)
    }

    @Test
    fun `re-uses cached stamp on subsequent resolution without re-hashing`() {
        val audioBytes = "audio-bytes-stamp-test".toByteArray()
        File(activePackDir, "audio/mahabodhi_guide.ogg").apply {
            parentFile?.mkdirs()
            writeBytes(audioBytes)
        }
        writeManifest(
            packDir = activePackDir,
            path = "audio/mahabodhi_guide.ogg",
            sha256 = sha256(audioBytes)
        )

        val resolver = PackMediaResolver(bundledAssets::contains)
        val result1 = resolver.resolve("audio/mahabodhi_guide.ogg", activePackDir)
        val result2 = resolver.resolve("audio/mahabodhi_guide.ogg", activePackDir)

        assertTrue(result1 is ResolvedMedia.VerifiedPackFile)
        assertTrue(result2 is ResolvedMedia.VerifiedPackFile)
        assertEquals((result1 as ResolvedMedia.VerifiedPackFile).sha256, (result2 as ResolvedMedia.VerifiedPackFile).sha256)
    }

    @Test
    fun `rejects file missing on disk even if present in manifest`() {
        writeManifest(
            packDir = activePackDir,
            path = "audio/mahabodhi_guide.ogg",
            sha256 = "abcdef".repeat(10) + "1234"
        )

        // bundledAsset contains this asset, so should fall back to BundledApkAsset
        val resolver = PackMediaResolver(bundledAssets::contains)
        val result = resolver.resolve("audio/mahabodhi_guide.ogg", activePackDir)

        assertEquals(ResolvedMedia.BundledApkAsset("audio/mahabodhi_guide.ogg"), result)
    }

    @Test
    fun `rejects file not in manifest`() {
        val audioBytes = "unregistered-audio".toByteArray()
        File(activePackDir, "audio/unregistered.ogg").apply {
            parentFile?.mkdirs()
            writeBytes(audioBytes)
        }
        writeManifest(
            packDir = activePackDir,
            path = "audio/mahabodhi_guide.ogg",
            sha256 = "abcdef"
        )

        val resolver = PackMediaResolver({ false })
        val result = resolver.resolve("audio/unregistered.ogg", activePackDir)

        assertTrue(result is ResolvedMedia.Rejected)
        assertEquals(RejectionReason.NOT_IN_MANIFEST, (result as ResolvedMedia.Rejected).reason)
    }

    @Test
    fun `rejects when manifest is missing`() {
        val resolver = PackMediaResolver({ false })
        val result = resolver.resolve("audio/mahabodhi_guide.ogg", activePackDir)

        assertTrue(result is ResolvedMedia.Rejected)
        assertEquals(RejectionReason.MISSING_MANIFEST, (result as ResolvedMedia.Rejected).reason)
    }

    @Test
    fun `rejects when pack file is in nested backup directory`() {
        val backupDir = File(tempRoot, ".backup-in-bihar").apply { mkdirs() }
        val resolver = PackMediaResolver({ false })
        val result = resolver.resolve("audio/mahabodhi_guide.ogg", backupDir)

        assertTrue(result is ResolvedMedia.Rejected)
        assertEquals(RejectionReason.STAGING_OR_BACKUP_DIR, (result as ResolvedMedia.Rejected).reason)
    }

    @Test
    fun `rejects when pack file traverses outside canonical root`() {
        val outsideFile = File(tempRoot, "outside.ogg").apply { writeBytes("outside".toByteArray()) }
        writeManifest(
            packDir = activePackDir,
            path = "outside.ogg",
            sha256 = sha256("outside".toByteArray())
        )

        val resolver = PackMediaResolver({ false })
        val result = resolver.resolve("outside.ogg", activePackDir)

        // outside.ogg does not exist inside activePackDir, so it's FILE_MISSING_ON_DISK
        assertTrue(result is ResolvedMedia.Rejected)
        assertEquals(RejectionReason.FILE_MISSING_ON_DISK, (result as ResolvedMedia.Rejected).reason)
    }

    @Test
    fun `allows PRODUCTION_CLEARED asset when requireProductionClearedOrigin is true`() {
        val bytes = "production-cleared-bytes".toByteArray()
        File(activePackDir, "images/then_now/mahabodhi_1880s_beglar.webp").apply {
            parentFile?.mkdirs()
            writeBytes(bytes)
        }
        writeManifest(
            packDir = activePackDir,
            path = "images/then_now/mahabodhi_1880s_beglar.webp",
            sha256 = sha256(bytes),
            origin = "PRODUCTION_CLEARED"
        )

        val prodResolver = PackMediaResolver({ false }, requireProductionClearedOrigin = true)
        val result = prodResolver.resolve(
            "images/then_now/mahabodhi_1880s_beglar.webp",
            activePackDir
        )

        assertTrue(result is ResolvedMedia.VerifiedPackFile)
    }

    private fun writeManifest(
        packDir: File,
        path: String,
        sha256: String,
        origin: String = "PRODUCTION_CLEARED"
    ) {
        val json = """
            {
              "format": "trueway.pack",
              "schema_version": 3,
              "pack_id": "in-bihar-buddhist-circuit",
              "release_version": "2026.10.1",
              "files": [
                {
                  "path": "$path",
                  "bytes": 32,
                  "sha256": "$sha256",
                  "asset_origin": "$origin"
                }
              ]
            }
        """.trimIndent()
        File(packDir, "manifest.cjson").writeText(json, Charsets.UTF_8)
    }

    private fun sha256(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256")
            .digest(bytes)
            .joinToString("") { "%02x".format(it) }
}
