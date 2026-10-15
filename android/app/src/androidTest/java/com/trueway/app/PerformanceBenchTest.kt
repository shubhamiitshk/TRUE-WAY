package com.trueway.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.trueway.app.data.PlaceRepository
import com.trueway.app.journal.JournalGraph
import com.trueway.app.vision.RefVector
import com.trueway.app.vision.RetrievalEngine
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Instrumented Performance Benchmark Test (FIELD_PERFORMANCE_PROTOCOL.md §6).
 *
 * Enforces latency budgets from SYSTEM_ARCHITECTURE_SPECIFICATION.md §X:
 * 1. Search Query Latency: P50 < 100ms over local catalog.
 * 2. In-Memory Cosine Vector Ranking: < 25ms over reference centroids.
 * 3. Geodesic Proximity Engine: < 20ms over all regional POIs.
 * 4. Local Room Journal DB round-trip write/read: < 50ms.
 */
@RunWith(AndroidJUnit4::class)
class PerformanceBenchTest {

    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext

    @Before
    fun setUp() {
        PlaceRepository.initForPackDir(context)
        JournalGraph.init(context)
    }

    @Test
    fun searchQueryLatencyIsUnderBudget() {
        val iterations = 20
        val timingsMs = mutableListOf<Double>()

        for (i in 0 until iterations) {
            val t0 = System.nanoTime()
            val results = PlaceRepository.search("Mahabodhi")
            val t1 = System.nanoTime()
            timingsMs.add((t1 - t0) / 1_000_000.0)
            assertTrue(results.isNotEmpty())
        }

        timingsMs.sort()
        val p50 = timingsMs[timingsMs.size / 2]
        val p95 = timingsMs[(timingsMs.size * 0.95).toInt()]

        // Target: P50 < 100ms, P95 < 250ms
        assertTrue("FTS Search P50 latency ($p50 ms) must be < 100 ms", p50 < 100.0)
        assertTrue("FTS Search P95 latency ($p95 ms) must be < 250 ms", p95 < 250.0)
    }

    @Test
    fun vectorRankingLatencyIsUnderBudget() {
        val dummyVector = FloatArray(512) { 0.123f }
        val refs = (1..50).map { i ->
            RefVector(
                placeId = "place-$i",
                assetId = "asset-$i",
                values = FloatArray(512) { (i * 0.01f) }
            )
        }

        val iterations = 50
        val timingsMs = mutableListOf<Double>()

        for (i in 0 until iterations) {
            val t0 = System.nanoTime()
            val ranked = RetrievalEngine.rank(
                query = dummyVector,
                refs = refs
            )
            val scores = RetrievalEngine.aggregateByPlace(ranked)
            RetrievalEngine.decide(scores, acceptThreshold = 0.60, minMargin = 0.08)
            val t1 = System.nanoTime()
            timingsMs.add((t1 - t0) / 1_000_000.0)
        }

        timingsMs.sort()
        val p50 = timingsMs[timingsMs.size / 2]
        // Cosine match across 50 centroids in memory must be sub-10ms
        assertTrue("Centroid ranking P50 latency ($p50 ms) must be < 25 ms", p50 < 25.0)
    }

    @Test
    fun geodesicProximityMathIsUnderBudget() {
        val iterations = 30
        val timingsMs = mutableListOf<Double>()

        for (i in 0 until iterations) {
            val t0 = System.nanoTime()
            PlaceRepository.nearby(24.6961, 84.9913, 50_000.0)
            val t1 = System.nanoTime()
            timingsMs.add((t1 - t0) / 1_000_000.0)
        }

        timingsMs.sort()
        val p50 = timingsMs[timingsMs.size / 2]
        assertTrue("Geodesic proximity P50 latency ($p50 ms) must be < 20 ms", p50 < 20.0)
    }

    @Test
    fun journalRoundTripLatencyIsUnderBudget() = runBlocking {
        val repo = JournalGraph.get()
        val iterations = 10
        val timingsMs = mutableListOf<Double>()

        for (i in 0 until iterations) {
            val t0 = System.nanoTime()
            val entryId = repo.save("in-bihar-bodhgaya-mahabodhi", "Benchmark iteration $i")
            repo.delete(entryId)
            val t1 = System.nanoTime()

            timingsMs.add((t1 - t0) / 1_000_000.0)
        }

        timingsMs.sort()
        val p50 = timingsMs[timingsMs.size / 2]
        assertTrue("Journal round-trip P50 latency ($p50 ms) must be < 50 ms", p50 < 50.0)
    }
}
