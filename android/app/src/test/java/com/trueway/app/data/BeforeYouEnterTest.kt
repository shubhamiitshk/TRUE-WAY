package com.trueway.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * P0.5 "Before You Enter" briefing gates (blueprint v3.0 §3, §5B, §6).
 *
 * Invariants:
 * - Restricted sites (Mahabodhi) have DEVICE_PROHIBITED level.
 * - Every briefing provides permitted boundary guidance and screen-free observation points.
 * - Every briefing placeId resolves to a known Place in PlaceRepository.
 */
class BeforeYouEnterTest {

    @Test
    fun corpusIsPopulatedAndResolvesToPlaces() {
        val all = BeforeYouEnterData.all()
        assertTrue(all.isNotEmpty())
        for (briefing in all) {
            val place = PlaceRepository.get(briefing.placeId)
            assertNotNull("Place must exist for briefing: ${briefing.placeId}", place)
            assertTrue(briefing.authorityNotice.isNotBlank())
            assertTrue(briefing.permittedUseBoundary.isNotBlank())
            assertTrue(briefing.keyObservations.isNotEmpty())
            assertTrue(briefing.preparationAdvice.isNotBlank())
        }
    }

    @Test
    fun mahabodhiHasStrictDeviceProhibition() {
        val mahabodhi = BeforeYouEnterData.get("in-bihar-bodhgaya-mahabodhi")
        assertNotNull(mahabodhi)
        assertEquals(RestrictionLevel.DEVICE_PROHIBITED, mahabodhi!!.restrictionLevel)
        assertTrue(mahabodhi.permittedUseBoundary.contains("outside", ignoreCase = true))
        assertTrue(mahabodhi.authorityNotice.contains("complex generally", ignoreCase = true))
        assertTrue(mahabodhi.authorityNotice.contains("without restricting this to the sanctum", ignoreCase = true))
        assertTrue(mahabodhi.authorityNotice.contains("strictly obey security and site staff instructions", ignoreCase = true))
        assertTrue(mahabodhi.keyObservations.any { it.contains("Vajrasana", ignoreCase = true) })
        assertTrue(mahabodhi.keyObservations.any { it.contains("Bodhi Tree", ignoreCase = true) })
    }

    @Test
    fun nalandaHasFragileRuinsCaution() {
        val nalanda = BeforeYouEnterData.get("in-bihar-nalanda-mahavihara")
        assertNotNull(nalanda)
        assertEquals(RestrictionLevel.ARCHAEOLOGICAL_CAUTION, nalanda!!.restrictionLevel)
        assertTrue(nalanda.keyObservations.any { it.contains("stupa", ignoreCase = true) })
    }

    @Test
    fun griddhakutaHasSteepTerrainCaution() {
        val griddhakuta = BeforeYouEnterData.get("in-bihar-rajgir-vultures-peak")
        assertNotNull(griddhakuta)
        assertEquals(RestrictionLevel.ASCENT_SAFETY_HAZARD, griddhakuta!!.restrictionLevel)
        assertTrue(griddhakuta.authorityNotice.contains("steep", ignoreCase = true))
    }
}
