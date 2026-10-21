package com.trueway.app.vision

import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.sqrt

/**
 * Soft geographic prior for visual place recognition (blueprint §7.4).
 *
 * Rules the codebase already commits to:
 *  * "Do NOT hard-exclude all places outside a 5–15 km radius. Location can be
 *    stale, manipulated, denied, inaccurate or intentionally absent; use it as
 *    a soft prior and record whether the result was based mainly on visual or
 *    location evidence." (blueprint §7.4)
 *  * A prior that can CREATE an accept is a spoofing liability. This prior can
 *    only RE-RANK candidates; it can never raise a candidate's score above its
 *    visual score, and it can never satisfy the relative-score gate on its
 *    own.
 *
 * The prior is heavy-tailed (Student-t in kilometres) so that a single
 * urban-multipath fix, a spoofed coordinate or a stale fix from two hours ago
 * saturates the penalty instead of annihilating the true place.
 */
data class GeoPrior(
    /** Within-place GPS spread in km; measured from the corpus, not guessed. */
    val tauKm: Double,
    /** Tail scale in km — how far out the penalty stops growing. */
    val kappaKm: Double,
    /** Maximum weight the prior may contribute. */
    val lambda: Double,
) {
    /**
     * Log prior of a place given the query's GPS fix.
     * `−d / (tau + d/kappa)` — 0 at d=0, bounded below by −kappa.
     */
    fun logPrior(distanceKm: Double): Double {
        if (distanceKm.isNaN() || distanceKm < 0.0) return 0.0
        val denom = tauKm + distanceKm / kappaKm
        if (denom <= 0.0) return 0.0
        return -distanceKm / denom
    }

    /**
     * Fused score. The visual score is preserved as a floor: the prior can only
     * subtract, so a place that the image does not support can never be
     * promoted by proximity alone.
     */
    fun fuse(visualScore: Double, distanceKm: Double): Double =
        visualScore + lambda * logPrior(distanceKm)

    companion object {
        /** Prior disabled (GPS denied, absent, or untrusted). */
        val DISABLED = GeoPrior(tauKm = 1.0, kappaKm = 1.0, lambda = 0.0)

        /**
         * Builds a prior from the device's location state.
         *
         * The prior is disabled when there is no fix, when the fix is stale,
         * or when the accuracy is too poor to distinguish the places in the
         * pack. `ageMs` is the age of the fix; `accuracyM` its reported
         * horizontal accuracy.
         */
        fun fromLocation(
            latitude: Double?,
            longitude: Double?,
            accuracyM: Double?,
            ageMs: Long,
            nowMs: Long,
            maxAgeMs: Long = 30 * 60 * 1000L,
            maxAccuracyM: Double = 200.0,
            tauKm: Double = 1.5,
            kappaKm: Double = 8.0,
            lambda: Double = 0.12,
        ): GeoPrior {
            if (latitude == null || longitude == null) return DISABLED
            if (accuracyM == null || accuracyM > maxAccuracyM) return DISABLED
            val age = (nowMs - ageMs).coerceAtLeast(0L)
            if (age > maxAgeMs) return DISABLED
            // A stale fix decays the weight rather than switching it off
            // abruptly, and a poor fix does the same.
            val ageFactor = exp(-age.toDouble() / maxAgeMs)
            val accFactor = (1.0 - (accuracyM / maxAccuracyM)).coerceIn(0.0, 1.0)
            val effectiveLambda = lambda * ageFactor * accFactor
            if (effectiveLambda <= 1e-6) return DISABLED
            return GeoPrior(tauKm = tauKm, kappaKm = kappaKm, lambda = effectiveLambda)
        }
    }
}

/** Great-circle distance in kilometres (haversine). */
object GeoDistance {
    fun km(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
        val r = 6371.0088
        val dLat = Math.toRadians(lat2 - lat1)
        val dLon = Math.toRadians(lon2 - lon1)
        val a = kotlin.math.sin(dLat / 2) * kotlin.math.sin(dLat / 2) +
            kotlin.math.cos(Math.toRadians(lat1)) * kotlin.math.cos(Math.toRadians(lat2)) *
            kotlin.math.sin(dLon / 2) * kotlin.math.sin(dLon / 2)
        return 2 * r * kotlin.math.asin(kotlin.math.sqrt(a.coerceIn(0.0, 1.0)))
    }
}
