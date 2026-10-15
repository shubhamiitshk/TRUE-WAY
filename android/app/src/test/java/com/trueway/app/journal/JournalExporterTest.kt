package com.trueway.app.journal

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Unit tests for JournalExporter (F117 / privacy-preserving JSON/plaintext export).
 */
class JournalExporterTest {

    @Test
    fun jsonExportFormatsValidStructure() {
        val entries = listOf(
            JournalEntry(
                entryId = "entry-001",
                placeId = "in-bihar-bodhgaya-mahabodhi",
                createdAt = "2026-10-12T10:00:00Z",
                userNote = "Observed 1880s railing carvings.",
                localPhotoUri = null,
                includeLocationOnExport = 0,
                localOnly = 1,
            ),
            JournalEntry(
                entryId = "entry-002",
                placeId = "in-bihar-nalanda-mahavihara",
                createdAt = "2026-10-12T14:30:00Z",
                userNote = "Monastery 1 brick drain system is remarkable.",
                localPhotoUri = null,
                includeLocationOnExport = 0,
                localOnly = 1,
            ),
        )

        val jsonStr = JournalExporter.exportToJson(entries)
        val root = JSONObject(jsonStr)

        assertEquals("trueway-journal-v1", root.getString("format_version"))
        assertEquals(2, root.getInt("total_entries"))
        val disclaimer = root.getString("privacy_disclaimer")
        assertTrue(disclaimer.contains("GPS"))
        assertTrue(disclaimer.contains("itineraries"))
        assertTrue(disclaimer.contains("place names"))
        assertTrue(disclaimer.contains("timestamps"))

        val array = root.getJSONArray("entries")
        assertEquals(2, array.length())

        val first = array.getJSONObject(0)
        assertEquals("entry-001", first.getString("entry_id"))
        assertEquals("in-bihar-bodhgaya-mahabodhi", first.getString("place_id"))
        assertEquals("Mahabodhi Temple Complex", first.getString("place_name"))
        assertEquals("Observed 1880s railing carvings.", first.getString("user_note"))
        assertFalse(first.getBoolean("location_attached"))
    }

    @Test
    fun plainTextExportFormatsSummary() {
        val entries = listOf(
            JournalEntry(
                entryId = "entry-001",
                placeId = "in-bihar-bodhgaya-mahabodhi",
                createdAt = "2026-10-12T10:00:00Z",
                userNote = "Great experience.",
                localPhotoUri = null,
                includeLocationOnExport = 0,
                localOnly = 1,
            ),
        )

        val text = JournalExporter.exportToPlainText(entries)
        assertTrue(text.contains("TRUEWAY PERSONAL TRAVEL JOURNAL"))
        assertTrue(text.contains("Mahabodhi Temple"))
        assertTrue(text.contains("Great experience."))
        assertTrue(text.contains("itineraries"))
        assertTrue(text.contains("place names"))
    }

    @Test
    fun pruneOldExportsDeletesStaleFilesAndKeepsRecentFiles() {
        val tempDir = java.nio.file.Files.createTempDirectory("trueway-export-test").toFile()
        try {
            val now = System.currentTimeMillis()
            val oldFile = java.io.File(tempDir, "trueway-journal-export-old.pdf").apply {
                writeText("old pdf content")
                setLastModified(now - (48 * 3600 * 1000)) // 48 hours ago
            }
            val oldJson = java.io.File(tempDir, "trueway-journal-export-old.json").apply {
                writeText("{}")
                setLastModified(now - (30 * 3600 * 1000)) // 30 hours ago
            }
            val recentFile = java.io.File(tempDir, "trueway-journal-export-recent.pdf").apply {
                writeText("recent pdf content")
                setLastModified(now - (2 * 3600 * 1000)) // 2 hours ago
            }
            val unrelatedFile = java.io.File(tempDir, "unrelated-file.txt").apply {
                writeText("keep me")
                setLastModified(now - (72 * 3600 * 1000)) // old but not an export file
            }

            val deletedCount = JournalExporter.pruneOldExports(tempDir, maxAgeHours = 24)

            assertEquals(2, deletedCount)
            assertFalse("Stale PDF should be deleted", oldFile.exists())
            assertFalse("Stale JSON should be deleted", oldJson.exists())
            assertTrue("Recent PDF should be preserved", recentFile.exists())
            assertTrue("Unrelated file should be untouched", unrelatedFile.exists())
        } finally {
            tempDir.deleteRecursively()
        }
    }
}
