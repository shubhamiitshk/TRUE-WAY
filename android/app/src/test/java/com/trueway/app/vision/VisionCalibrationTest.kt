package com.trueway.app.vision

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The pack's LEARNED calibration and the geo prior.
 *
 * These are the two things that used to be hard-coded constants in Kotlin while
 * the pack quietly shipped a different, unused set of values.
 */
class VisionCalibrationTest {

    private fun block(json: String): JSONObject = JSONObject(json)

    @Test
    fun `parses a complete calibration`() {
        val cal = VisionCalibration.parse(
            block(
                """
                {"accept_threshold": 0.6646, "relative_threshold": -0.44,
                 "hard_negative_margin": 0.0, "sibling_margin": 0.06,
                 "min_margin": 0.05, "top_k_mean": 2,
                 "calibrator": {"a": 12.4, "b": -7.1}}
                """.trimIndent()
            )
        )
        assertTrue(cal != null)
        cal!!
        assertEquals(0.6646, cal.acceptThreshold, 1e-9)
        assertEquals(-0.44, cal.relativeThreshold, 1e-9)
        assertEquals(0.06, cal.siblingMargin, 1e-9)
        assertEquals(2, cal.topKMean)
        assertEquals("pack", cal.source)
        assertTrue(cal.calibrator.enabled)
    }

    @Test
    fun `an incomplete calibration is refused rather than defaulted`() {
        // A pack with only the legacy absolute pair must NOT be treated as
        // calibrated: the scanner must not present a name it cannot calibrate.
        assertNull(
            VisionCalibration.parse(
                block("""{"accept_threshold": 0.72, "min_margin": 0.05}""")
            )
        )
        assertNull(VisionCalibration.parse(null))
    }

    @Test
    fun `calibrator maps the open margin to a probability`() {
        val cal = ScoreCalibrator(slope = 10.0, intercept = -5.0, enabled = true)
        val p = cal.probability(0.5)
        assertTrue(p in 0.0..1.0)
        assertTrue("a higher margin must give a higher probability", cal.probability(0.8) > p)
        // a disabled calibrator is the identity
        assertEquals(0.42, ScoreCalibrator.DISABLED.probability(0.42), 1e-12)
    }

    @Test
    fun `policy is derived from the pack calibration and keeps its provenance`() {
        val cal = VisionCalibration(
            acceptThreshold = 0.66,
            relativeThreshold = -0.44,
            hardNegativeMargin = 0.0,
            siblingMargin = 0.06,
            minMargin = 0.05,
            topKMean = 3,
            calibrator = ScoreCalibrator.DISABLED,
            source = "pack",
        )
        val policy = SiblingCalibrationPolicy.from(cal)
        assertEquals(0.66f, policy.absThreshold, 1e-6f)
        assertEquals(-0.44f, policy.relativeThreshold, 1e-6f)
        assertEquals(3, policy.topKMean)
        assertEquals("pack", policy.source)
    }

    @Test
    fun `a missing calibration falls back to a clearly-labelled default`() {
        val policy = SiblingCalibrationPolicy.from(null)
        assertEquals("default", policy.source)
    }
}

class GeoPriorTest {

    @Test
    fun `the prior is bounded so it can never create an acceptance`() {
        val prior = GeoPrior(tauKm = 1.0, kappaKm = 5.0, lambda = 0.3)
        val near = prior.logPrior(0.0)
        val far = prior.logPrior(10_000.0)
        assertEquals(0.0, near, 1e-9)
        assertTrue("the far penalty must saturate", far >= -5.0)
        // the fused score can only be LOWER than the visual score
        assertTrue(prior.fuse(0.9, 10_000.0) <= 0.9)
    }

    @Test
    fun `the prior is disabled without a fix, with a bad fix, or when stale`() {
        assertEquals(0.0, GeoPrior.fromLocation(null, null, null, 0, 1_000L).lambda, 1e-9)
        // accuracy far worse than the places we are separating
        assertEquals(0.0, GeoPrior.fromLocation(24.7, 84.9, 5000.0, 0, 1_000L).lambda, 1e-9)
        // a fix from two hours ago
        assertEquals(0.0, GeoPrior.fromLocation(24.7, 84.9, 20.0, 0, 7_200_000L).lambda, 1e-9)
        // a good, fresh fix
        assertTrue(GeoPrior.fromLocation(24.7, 84.9, 20.0, 0, 1_000L).lambda > 0.0)
    }

    @Test
    fun `a stale fix decays the weight rather than switching it off abruptly`() {
        val fresh = GeoPrior.fromLocation(24.7, 84.9, 20.0, 0, 60_000L).lambda
        val older = GeoPrior.fromLocation(24.7, 84.9, 20.0, 0, 20 * 60_000L).lambda
        assertTrue(older < fresh)
        assertTrue(older > 0.0)
    }

    @Test
    fun `haversine distance is sane`() {
        val d = GeoDistance.km(24.6961, 84.9913, 25.0038, 85.4160)
        assertTrue("Bodh Gaya to Nalanda is ~48 km", d in 40.0..55.0)
        assertEquals(0.0, GeoDistance.km(24.6961, 84.9913, 24.6961, 84.9913), 1e-9)
    }
}
