package com.trueway.app.vision

/**
 * Pure ranking + decision math for visual retrieval (blueprint §7.4–7.5,
 * §28.5). No Android types: the encoder (MediaPipeEmbedder) and the
 * reference store feed it FloatArrays, so every rule below is JVM-testable.
 *
 * Thresholds are constructor/call parameters because they are LEARNED on
 * held-out visits (ml/evaluate_retrieval.py sweep) — never constants.
 * Scores are diagnostic until calibration is validated: the UI must render
 * likely/possible/unknown wording, not percentages.
 */

/** One stored reference image embedding inside the active pack. */
data class RefVector(
    val placeId: String,
    val assetId: String,
    val values: FloatArray,
    val distinguishingHint: String? = null,
)

/** Place-level aggregated score with evidence for the decision. */
data class PlaceScore(
    val placeId: String,
    /** Robust top-2 mean over this place's reference similarities. */
    val score: Double,
    /** Best place score minus second-best place score. */
    val margin: Double,
    val supporters: Int,
    /** Matching reference asset IDs (§28.5 Candidate.matchingReferenceAssetIds),
     *  best-first — recorded for QA provenance, not shown to users. */
    val assetIds: List<String> = emptyList(),
    /** Optional curatorial architectural cue disambiguating sibling structures. */
    val distinguishingHint: String? = null,
)

/** How an identity was derived (§28.5 EvidenceKind) — recorded for QA. */
enum class EvidenceKind { VISION_RANKING, QR_TOUCHPOINT, TEXT_SEARCH }

enum class UnknownReason {
    NO_CANDIDATES,
    LOW_SCORE,
    AMBIGUOUS_LOOKALIKES,
}

sealed interface RankDecision {
    data class Accepted(val place: PlaceScore, val alternatives: List<PlaceScore>) : RankDecision
    data class Uncertain(val reason: UnknownReason, val alternatives: List<PlaceScore>) : RankDecision
}

object RetrievalEngine {

    /** Cosine similarity on L2-normalized inputs; 0.0 for degenerate vectors. */
    fun cosine(a: FloatArray, b: FloatArray): Double {
        require(a.size == b.size) { "dim mismatch ${a.size} vs ${b.size}" }
        var dot = 0.0
        var na = 0.0
        var nb = 0.0
        for (i in a.indices) {
            dot += a[i] * b[i]
            na += a[i] * a[i]
            nb += b[i] * b[i]
        }
        if (na <= 0.0 || nb <= 0.0) return 0.0
        return dot / (kotlin.math.sqrt(na) * kotlin.math.sqrt(nb))
    }

    /** All references ranked against the query (brute-force: exact at pilot scale). */
    fun rank(
        query: FloatArray,
        refs: List<RefVector>,
        topK: Int = 30,
    ): List<Pair<RefVector, Double>> =
        refs.map { it to cosine(query, it.values) }
            .sortedByDescending { it.second }
            .take(topK.coerceAtLeast(1))

    /**
     * Aggregate reference hits to place level: robust top-2 mean per place,
     * mirroring the §7.5 scoring design. Margin exposes lookalike ambiguity.
     */
    fun aggregateByPlace(ranked: List<Pair<RefVector, Double>>): List<PlaceScore> {
        val byPlace = ranked.groupBy { it.first.placeId }
        val sorted = byPlace.entries.map { (placeId, hits) ->
            val top = hits.sortedByDescending { it.second }
            val score = top.take(2).map { it.second }.average()
            val hint = top.firstNotNullOfOrNull { it.first.distinguishingHint?.takeIf { h -> h.isNotBlank() } }
            PlaceAgg(placeId, score, hits.size, top.map { it.first.assetId }, hint)
        }.sortedByDescending { it.score }
        // Margin is defined on the winner only: best minus runner-up. A SOLE
        // candidate has no competitor, so its margin is unbounded (not zero) —
        // otherwise the most confident, least-ambiguous case would be wrongly
        // abstained as AMBIGUOUS_LOOKALIKES.
        return sorted.mapIndexed { i, a ->
            val runnerUp = sorted.getOrNull(i + 1)?.score
            val margin = if (i == 0) runnerUp?.let { a.score - it } ?: Double.POSITIVE_INFINITY else 0.0
            PlaceScore(a.placeId, a.score, margin, a.supporters, a.assetIds, a.distinguishingHint)
        }
    }

    private data class PlaceAgg(
        val placeId: String,
        val score: Double,
        val supporters: Int,
        val assetIds: List<String>,
        val distinguishingHint: String? = null,
    )

    /**
     * Calibrated gate. [acceptThreshold] and [minMargin] come from the
     * held-out calibration split; failing either yields an explicit
     * abstention, never a forced identity (§3 principle 2).
     *
     * When [relativeThreshold] is supplied the gate additionally requires the
     * winner to beat the strongest competitor — the second-best place or the
     * best hard negative, whichever is closer — by that margin. The RELATIVE
     * score is the primary gate because an absolute cosine moves with the
     * encoder, the quantisation, the input resolution and the number of
     * prototypes, while a relative score does not
     * (Miller et al., ECCV 2024, arXiv:2403.16528).
     */
    fun decide(
        scores: List<PlaceScore>,
        acceptThreshold: Double,
        minMargin: Double,
        relativeThreshold: Double = Double.NaN,
        maxNegativeScore: Double = -1.0,
    ): RankDecision {
        if (scores.isEmpty()) return RankDecision.Uncertain(UnknownReason.NO_CANDIDATES, emptyList())
        val best = scores[0]
        val alternatives = scores.drop(1).take(2)
        if (best.score < acceptThreshold) {
            return RankDecision.Uncertain(UnknownReason.LOW_SCORE, listOf(best) + alternatives)
        }
        if (!relativeThreshold.isNaN()) {
            val competitor = maxOf(alternatives.firstOrNull()?.score ?: -1.0, maxNegativeScore)
            val relative = best.score - competitor
            if (relative < relativeThreshold) {
                return RankDecision.Uncertain(UnknownReason.AMBIGUOUS_LOOKALIKES, listOf(best) + alternatives)
            }
        }
        if (best.margin < minMargin) {
            return RankDecision.Uncertain(UnknownReason.AMBIGUOUS_LOOKALIKES, listOf(best) + alternatives)
        }
        return RankDecision.Accepted(best, alternatives)
    }
}
