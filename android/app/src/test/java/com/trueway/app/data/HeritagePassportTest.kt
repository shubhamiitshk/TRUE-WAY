package com.trueway.app.data

import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * P1A Offline Heritage Passport & Stamps gates (blueprint v3.0 §3, §7, F107).
 *
 * Invariants:
 * - Heritage passport seals define commemorative stamps.
 * - Every stamp includes the mandatory non-official commemorative disclaimer.
 * - Every stamp links to a known place in PlaceRepository.
 */
class HeritagePassportTest {

    @Test
    fun passportCorpusPopulatedAndResolvesToPlaces() {
        val stamps = HeritagePassportCorpus.all()
        assertTrue("Corpus must contain heritage passport stamps", stamps.isNotEmpty())

        for (stamp in stamps) {
            val place = PlaceRepository.get(stamp.placeId)
            assertNotNull("Stamp placeId ${stamp.placeId} must resolve to Place", place)

            assertTrue(stamp.stampId.isNotBlank())
            assertTrue(stamp.stampTitle.isNotBlank())
            assertTrue(stamp.stampTitleHindi.isNotBlank())
            assertTrue(stamp.circuitName.isNotBlank())
            assertTrue(stamp.emblemDescription.isNotBlank())
            assertTrue(stamp.historicalInscription.isNotBlank())
        }
        assertTrue("Must include non-official disclaimer", HeritagePassportCorpus.DISCLAIMER.contains("commemorative", ignoreCase = true))
    }

    @Test
    fun mahabodhiStampHasBodhiLeafMotif() {
        val stamp = HeritagePassportCorpus.get("in-bihar-bodhgaya-mahabodhi")
        assertNotNull(stamp)
        assertTrue(stamp!!.emblemDescription.contains("Bodhi", ignoreCase = true))
    }
}
