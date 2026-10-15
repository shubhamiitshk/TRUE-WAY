package com.trueway.app.vision

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs

/**
 * Retrieval math gates (blueprint §7.5–7.6): ranking order, place-level
 * aggregation, and the accept/abstain contract. Thresholds here are test
 * fixtures — production values are learned on held-out visits.
 */
class RetrievalEngineTest {

    private fun unit(vararg xs: Float) =
        xs.map { it }.toFloatArray().let { v ->
            val n = kotlin.math.sqrt(v.sumOf { (it * it).toDouble() })
            FloatArray(v.size) { v[it] / n.toFloat() }
        }

    @Test
    fun cosineIdentityAndOrthogonal() {
        val a = unit(1f, 0f, 0f)
        assertTrue(abs(RetrievalEngine.cosine(a, a) - 1.0) < 1e-6)
        assertTrue(abs(RetrievalEngine.cosine(a, unit(0f, 1f, 0f))) < 1e-6)
        // Degenerate zero vector abstains numerically instead of NaN.
        assertEquals(0.0, RetrievalEngine.cosine(FloatArray(3), a), 1e-9)
    }

    @Test(expected = IllegalArgumentException::class)
    fun cosineDimMismatchThrows() {
        RetrievalEngine.cosine(FloatArray(4), FloatArray(8))
    }

    @Test
    fun rankOrdersBySimilarity() {
        val q = unit(1f, 0f, 0f)
        val refs = listOf(
            RefVector("far", "a1", unit(0f, 1f, 0f)),
            RefVector("near", "a2", unit(0.9f, 0.1f, 0f)),
        )
        val ranked = RetrievalEngine.rank(q, refs)
        assertEquals("near", ranked[0].first.placeId)
        assertTrue(ranked[0].second > ranked[1].second)
    }

    @Test
    fun aggregateUsesTopTwoMeanAndWinnerMargin() {
        val ranked = listOf(
            RefVector("p1", "r1", FloatArray(0)) to 0.9,
            RefVector("p2", "r1", FloatArray(0)) to 0.7,
            RefVector("p1", "r2", FloatArray(0)) to 0.8,
            RefVector("p2", "r2", FloatArray(0)) to 0.6,
        )
        val scores = RetrievalEngine.aggregateByPlace(ranked)
        assertEquals("p1", scores[0].placeId)
        assertTrue(abs(scores[0].score - 0.85) < 1e-9) // (0.9+0.8)/2
        assertTrue(abs(scores[0].margin - 0.2) < 1e-9) // 0.85-0.65
        assertEquals(2, scores[0].supporters)
        // QA provenance: matching reference asset IDs are carried (§28.5).
        assertEquals(listOf("r1", "r2"), scores[0].assetIds)
    }

    @Test
    fun soleCandidateHasUnboundedMarginAndAccepts() {
        // A pack covering a single place fills the top-K with that place's own
        // refs → one PlaceScore, no competitor. Its margin must be unbounded
        // (not zero), else the most confident case abstains as AMBIGUOUS.
        val ranked = listOf(
            RefVector("only", "r1", FloatArray(0)) to 0.92,
            RefVector("only", "r2", FloatArray(0)) to 0.88,
        )
        val scores = RetrievalEngine.aggregateByPlace(ranked)
        assertEquals(1, scores.size)
        assertEquals(Double.POSITIVE_INFINITY, scores[0].margin, 0.0)
        val d = RetrievalEngine.decide(scores, acceptThreshold = 0.8, minMargin = 0.05)
        assertTrue(d is RankDecision.Accepted)
        assertEquals("only", (d as RankDecision.Accepted).place.placeId)
    }

    @Test
    fun decideAcceptsConfidentSeparatedWinner() {
        val scores = listOf(
            PlaceScore("p1", 0.85, 0.2, 3),
            PlaceScore("p2", 0.65, 0.0, 2),
        )
        val d = RetrievalEngine.decide(scores, acceptThreshold = 0.8, minMargin = 0.05)
        assertTrue(d is RankDecision.Accepted)
        assertEquals("p1", (d as RankDecision.Accepted).place.placeId)
    }

    @Test
    fun decideAbstainsOnLowScoreAmbiguityAndEmptiness() {
        val close = listOf(
            PlaceScore("p1", 0.85, 0.01, 2),
            PlaceScore("p2", 0.84, 0.0, 2),
        )
        val amb = RetrievalEngine.decide(close, acceptThreshold = 0.8, minMargin = 0.05)
        assertTrue(amb is RankDecision.Uncertain)
        assertEquals(
            UnknownReason.AMBIGUOUS_LOOKALIKES,
            (amb as RankDecision.Uncertain).reason,
        )
        val low = RetrievalEngine.decide(
            listOf(PlaceScore("p1", 0.5, 0.4, 1)),
            acceptThreshold = 0.8, minMargin = 0.05,
        )
        assertEquals(
            UnknownReason.LOW_SCORE,
            (low as RankDecision.Uncertain).reason,
        )
        val empty = RetrievalEngine.decide(emptyList(), 0.8, 0.05)
        assertEquals(
            UnknownReason.NO_CANDIDATES,
            (empty as RankDecision.Uncertain).reason,
        )
    }
}
