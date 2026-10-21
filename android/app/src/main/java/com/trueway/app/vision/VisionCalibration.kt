package com.trueway.app.vision

import org.json.JSONObject
import kotlin.math.exp

/**
 * Pack-supplied decision calibration (blueprint §7.5, §18.2).
 *
 * Everything the accept/abstain gate needs is LEARNED on a held-out
 * calibration split and shipped inside the pack. Nothing here is a constant
 * tuned by hand:
 *
 *  * [acceptThreshold] — absolute cosine floor. A safety net, not the gate.
 *  * [relativeThreshold] — the PRIMARY gate. The *relative* score
 *    `winner − max(second-best place, best hard negative)` is far more stable
 *    than an absolute cosine, which shifts with the encoder, the quantisation,
 *    the input resolution and the number of prototypes (Miller et al., ECCV
 *    2024, arXiv:2403.16528 — raw similarity is the weakest of the
 *    open-set statistics; relative scores transfer across encoder swaps).
 *  * [hardNegativeMargin] — how far above the best hard negative the winner
 *    must sit.
 *  * [siblingMargin] — below this gap between two sibling structures the
 *    result is reported as an ambiguous pair, never a forced identity.
 *  * [topKMean] — how many of a place's reference similarities are averaged.
 *    The blueprint specifies a *robust top-2 mean*, not a MAX: a MAX over M
 *    prototypes is a multiple-comparisons statistic whose null distribution
 *    grows with M, which silently makes the threshold depend on M.
 *  * [calibrator] — an optional 1-D logistic map from the relative score to
 *    P(correct). Used for QA provenance only; the UI must not show a
 *    percentage until calibrated probabilities are validated in the field.
 *
 * The pack is the source of truth. If the pack carries no calibration the
 * index is reported as UNCALIBRATED and the scanner must not present names
 * (§3 principle 2 — abstention over fabrication).
 */
data class VisionCalibration(
    val acceptThreshold: Double,
    val relativeThreshold: Double,
    val hardNegativeMargin: Double,
    val siblingMargin: Double,
    val minMargin: Double,
    val topKMean: Int,
    val relatedMargin: Double = 0.0,
    /**
     * The CSLS neighbourhood size: the number of nearest neighbours used to
     * estimate the local density of a gallery vector. 10 is the value the
     * CSLS paper reports as insensitive.
     */
    val cslsK: Int = 10,
    val calibrator: ScoreCalibrator,
    val source: String,
) {
    fun probabilityOfCorrect(relativeScore: Double): Double = calibrator.probability(relativeScore)

    companion object {
        /**
         * Placeholder used ONLY when a pack carries no calibration. It is
         * deliberately conservative and is tagged `source = "default"` so the
         * provenance can be surfaced; a pack without calibration is reported
         * as UNCALIBRATED and never used to present a name.
         */
        val UNCALIBRATED = VisionCalibration(
            acceptThreshold = Double.NaN,
            relativeThreshold = Double.NaN,
            hardNegativeMargin = Double.NaN,
            siblingMargin = Double.NaN,
            minMargin = Double.NaN,
            topKMean = 2,
            relatedMargin = 0.0,
            calibrator = ScoreCalibrator.DISABLED,
            source = "none",
        )

        /** Parses the pack's `calibration` object. Returns null when incomplete. */
        fun parse(json: JSONObject?): VisionCalibration? {
            if (json == null) return null
            fun num(key: String): Double? {
                if (!json.has(key)) return null
                val v = json.optDouble(key, Double.NaN)
                return if (v.isNaN()) null else v
            }
            val accept = num("accept_threshold") ?: return null
            val rel = num("relative_threshold") ?: return null
            val hardNeg = num("hard_negative_margin") ?: return null
            val sib = num("sibling_margin") ?: return null
            val minMargin = num("min_margin") ?: return null
            val k = json.optInt("top_k_mean", 2).coerceIn(1, 8)
            val related = json.optDouble("related_margin", 0.0).let { if (it.isNaN()) 0.0 else it }
            val cslsK = json.optInt("csls_k", 10).coerceIn(1, 64)
            val cal = json.optJSONObject("calibrator")?.let { ScoreCalibrator.parse(it) }
                ?: ScoreCalibrator.DISABLED
            return VisionCalibration(
                acceptThreshold = accept,
                relativeThreshold = rel,
                hardNegativeMargin = hardNeg,
                siblingMargin = sib,
                minMargin = minMargin,
                topKMean = k,
                relatedMargin = related,
                cslsK = cslsK,
                calibrator = cal,
                source = "pack",
            )
        }
    }
}

/**
 * 1-D logistic (Platt) calibration of the relative score to P(correct).
 *
 * Two parameters, fitted on the held-out calibration split. Deliberately not
 * an open-set-recognition head: OSR heads are classification heads, they
 * change the score distribution that has to be re-calibrated anyway, and the
 * open-set literature gives no evidence of a gain at this scale
 * (arXiv:2312.08785; arXiv:2403.16528).
 */
data class ScoreCalibrator(
    val slope: Double,
    val intercept: Double,
    val enabled: Boolean,
) {
    fun probability(relativeScore: Double): Double {
        if (!enabled) return relativeScore
        val z = slope * relativeScore + intercept
        if (z > 40.0) return 1.0
        if (z < -40.0) return 0.0
        return 1.0 / (1.0 + exp(-z))
    }

    companion object {
        val DISABLED = ScoreCalibrator(0.0, 0.0, false)

        fun parse(json: JSONObject): ScoreCalibrator {
            val a = json.optDouble("a", Double.NaN)
            val b = json.optDouble("b", Double.NaN)
            if (a.isNaN() || b.isNaN()) return DISABLED
            return ScoreCalibrator(a, b, enabled = true)
        }
    }
}
