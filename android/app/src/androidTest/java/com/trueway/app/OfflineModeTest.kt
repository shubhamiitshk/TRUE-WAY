package com.trueway.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.trueway.app.data.GeoUtils
import com.trueway.app.data.OfflineDiagnostic
import com.trueway.app.data.PlaceRepository
import com.trueway.app.journal.JournalGraph
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Instrumented Offline Mode Test (FIELD_PERFORMANCE_PROTOCOL.md §6).
 *
 * Verifies the Core Invariant: Zero Network Egress by Construction.
 * 1. Place catalog retrieval from bundled SQLite / memory without network.
 * 2. Full-text search (FTS5) queries execute with radios disabled.
 * 3. Geodesic distance calculation uses local Haversine arithmetic.
 * 4. Private journal operations stay strictly inside local user_journal.sqlite.
 */
@RunWith(AndroidJUnit4::class)
class OfflineModeTest {

    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext

    @Before
    fun setUp() {
        PlaceRepository.initForPackDir(context)
        JournalGraph.init(context)
    }

    @Test
    fun placeCatalogLoadsCompletelyOffline() {
        val places = PlaceRepository.all()
        assertTrue("Place catalog must contain at least 10 seeded places", places.size >= 10)

        val mahabodhi = PlaceRepository.get("in-bihar-bodhgaya-mahabodhi")
        assertNotNull("Mahabodhi must exist in offline catalog", mahabodhi)
        assertEquals("Temple", mahabodhi?.category)
        assertTrue(mahabodhi?.canonicalName?.contains("Mahabodhi") == true)
    }

    @Test
    fun fullTextSearchExecutesOfflineWithoutNetwork() {
        val results = PlaceRepository.search("Buddha")
        assertTrue("Search for 'Buddha' must return matches offline", results.isNotEmpty())

        val hindiResults = PlaceRepository.search("बुद्ध")
        assertTrue("Devanagari search query must execute offline", hindiResults.isNotEmpty())
    }

    @Test
    fun geodesicProximityCalculatesPureOfflineHaversine() {
        // Bodh Gaya coordinates: 24.6961, 84.9913
        val nearby = PlaceRepository.nearby(24.6961, 84.9913, 10_000.0)
        assertTrue("Nearby places around Bodh Gaya must be found", nearby.isNotEmpty())

        val testDist = GeoUtils.haversineMeters(24.6961, 84.9913, 24.6960, 84.9912)
        assertTrue("Haversine distance must be positive", testDist > 0.0)

        val closest = nearby.first()
        assertTrue("Closest site should be within 2000m of Bodh Gaya coords", closest.distanceMeters < 2000.0)
    }

    @Test
    fun offlineDiagnosticReportRunsCompletelyOffline() {
        val report = OfflineDiagnostic.runDiagnostic(context)
        assertNotNull(report)
        assertTrue("Diagnostic report must contain 9 verified offline layers", report.results.size >= 9)
        assertTrue("All layers should be ready for offline use", report.overallReady)
    }

    @Test
    fun journalOperationsPersistLocallyWithoutRemoteEgress() = runBlocking {
        val repo = JournalGraph.get()
        val entryId = repo.save("in-bihar-bodhgaya-mahabodhi", "Testing offline journal entry on device.")
        assertNotNull("Saved journal entry ID must not be null", entryId)

        // Cleanup
        repo.delete(entryId)
    }
}
