package com.trueway.app.pack

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Pure (network-free) parts of PackDownloader: component path encoding and
 * manifest file-list parsing.
 */
class PackDownloaderTest {

    @Test
    fun `encodeComponent keeps safe ASCII paths intact`() {
        assertEquals("content/places.sqlite", PackDownloader.encodeComponent("content/places.sqlite"))
        assertEquals("vision/reference_vectors.bin", PackDownloader.encodeComponent("vision/reference_vectors.bin"))
        assertEquals("audio/mahabodhi_guide_hi.ogg", PackDownloader.encodeComponent("audio/mahabodhi_guide_hi.ogg"))
    }

    @Test
    fun `encodeComponent percent-encodes unsafe path segments`() {
        assertEquals("audio/my%20file.ogg", PackDownloader.encodeComponent("audio/my file.ogg"))
        assertEquals("images/thumbs/MW%2520", PackDownloader.encodeComponent("images/thumbs/MW%20"))
        assertEquals("a/b%20c%20d.ogg", PackDownloader.encodeComponent("a/b c d.ogg"))
    }

    @Test
    fun `parseManifestFiles extracts path bytes sha256 rows`() {
        val manifest = """
        {
          "format": "trueway.pack",
          "pack_id": "in-golden-triangle",
          "release_version": "2026.11.1",
          "files": [
            {"path": "content/places.sqlite", "bytes": 4096, "sha256": "abc123", "asset_origin": "PRODUCTION_CLEARED"},
            {"path": "audio/taj_guide.ogg", "bytes": 2048, "sha256": "def456", "asset_origin": "PRODUCTION_CLEARED"}
          ]
        }
        """.trimIndent().toByteArray(Charsets.UTF_8)

        val files = PackDownloader.parseManifestFiles(manifest)
        assertEquals(2, files.size)
        assertEquals("content/places.sqlite", files[0].path)
        assertEquals(4096L, files[0].bytes)
        assertEquals("abc123", files[0].sha256)
        assertEquals("audio/taj_guide.ogg", files[1].path)
        assertEquals("def456", files[1].sha256)
    }

    @Test
    fun `parseManifestFiles tolerates missing files array`() {
        val manifest = """{"format": "trueway.pack", "pack_id": "x"}""".toByteArray(Charsets.UTF_8)
        assertTrue(PackDownloader.parseManifestFiles(manifest).isEmpty())
    }

    @Test
    fun `parseManifestFiles drops malformed file entries`() {
        val manifest = """
        {
          "files": [
            {"path": "content/places.sqlite", "bytes": 10, "sha256": "x"},
            {"bytes": 20, "sha256": "y"},
            {"path": "", "bytes": 0, "sha256": "z"}
          ]
        }
        """.trimIndent().toByteArray(Charsets.UTF_8)
        val files = PackDownloader.parseManifestFiles(manifest)
        assertEquals(1, files.size)
        assertEquals("content/places.sqlite", files[0].path)
    }
}
