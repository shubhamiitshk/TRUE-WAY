package com.trueway.app.data

import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * P1A "Then & Now" archival comparisons gates (blueprint v3.0 §3, §7, §8, F108).
 *
 * Invariants:
 * - Archival comparisons provide documented 19th/early-20th-century surveys.
 * - Archival rights statements are explicitly documented (ASI survey archives / Public Domain).
 * - Modern conservation status and curatorial descriptions are non-blank.
 * - All placeIds resolve to valid places in PlaceRepository.
 */
class ThenAndNowTest {

    @Test
    fun archivalCorpusPopulatedAndResolvesToPlaces() {
        val comparisons = ThenAndNowCorpus.all()
        assertTrue("Then & Now corpus must not be empty", comparisons.isNotEmpty())
        org.junit.Assert.assertEquals("Corpus must contain exactly 3 comparison pairs", 3, comparisons.size)

        for (item in comparisons) {
            val place = PlaceRepository.get(item.placeId)
            assertNotNull("PlaceId ${item.placeId} must resolve to Place", place)

            assertTrue(item.archivalEra.isNotBlank())
            assertTrue(item.rightsStatement.isNotBlank())
            assertTrue(item.archivalDescription.isNotBlank())
            assertTrue(item.modernObservation.isNotBlank())
            assertTrue(item.preservationNotes.isNotBlank())
            assertTrue(item.historicalPhotoTitle.isNotBlank())
            assertTrue(item.historicalPhotographer.isNotBlank())
            assertTrue(item.historicalArchive.isNotBlank())
            assertTrue(item.historicalAccessionId.isNotBlank())
            assertTrue(item.historicalPhotoAssetPath.isNotBlank())
            assertTrue(item.modernPhotoAssetPath.isNotBlank())
            assertTrue(item.viewpointAlignmentNotes.isNotBlank())
            assertTrue(item.modernPhotoTitle.isNotBlank())
            assertTrue(item.modernPhotographer.isNotBlank())
            assertTrue(item.modernRightsHolder.isNotBlank())
            assertTrue(item.modernLicence.contains("CC BY-SA 4.0"))
            assertTrue(item.statutoryCopyrightAnalysis.contains("Section 25 (term in photographs) was omitted"))
            assertTrue(item.statutoryCopyrightAnalysis.contains("Section 22"))
            assertTrue(item.statutoryCopyrightAnalysis.contains("Section 28"))
            assertTrue(item.statutoryCopyrightAnalysis.contains("Transitional") || item.statutoryCopyrightAnalysis.contains("Legacy"))
        }
    }

    @Test
    fun mahabodhiHasCunninghamArchivalDocumentation() {
        val mahabodhi = ThenAndNowCorpus.get("in-bihar-bodhgaya-mahabodhi")
        assertNotNull(mahabodhi)
        assertTrue(mahabodhi!!.archivalEra.contains("1880"))
        assertTrue(mahabodhi.archivalDescription.contains("Cunningham", ignoreCase = true))
        assertTrue(mahabodhi.rightsStatement.contains("Public Domain", ignoreCase = true))
        assertTrue(mahabodhi.historicalPhotographer.contains("Beglar", ignoreCase = true))
        assertTrue(mahabodhi.historicalAccessionId.contains("Photo 1003/(1130)"))
        assertTrue(mahabodhi.historicalAccessionId.contains("Photo 1003(49)"))
        assertTrue(mahabodhi.historicalAccessionId.contains("Photo 1003(50)"))
        assertTrue(mahabodhi.historicalRedistributionNotice.contains("unavailable online", ignoreCase = true))
        assertTrue(mahabodhi.historicalRedistributionNotice.contains("provenance", ignoreCase = true))
        assertTrue(mahabodhi.statutoryCopyrightAnalysis.contains("Photo 1003(49)"))
        assertTrue(mahabodhi.statutoryCopyrightAnalysis.contains("Photo 1003(50)"))
        assertTrue(mahabodhi.modernLicence.contains("CC BY-SA 4.0"))
        assertTrue(mahabodhi.statutoryCopyrightAnalysis.contains("1907")) // Beglar death year
    }

    @Test
    fun nalandaHasSpoonerExcavationDocumentation() {
        val nalanda = ThenAndNowCorpus.get("in-bihar-nalanda-temple-03")
        assertNotNull(nalanda)
        assertTrue(nalanda!!.archivalEra.contains("1915"))
        assertTrue(nalanda.archivalDescription.contains("Spooner", ignoreCase = true))
        assertTrue(nalanda.historicalPhotographer.contains("Spooner", ignoreCase = true))
        assertTrue(nalanda.historicalAccessionId.contains("Plate XVI"))
        assertTrue(nalanda.statutoryCopyrightAnalysis.contains("1925")) // Spooner death year
    }

    @Test
    fun rajgirWallHasMarshallDocumentation() {
        val rajgir = ThenAndNowCorpus.get("in-bihar-rajgir-cyclopean-wall")
        assertNotNull(rajgir)
        assertTrue(rajgir!!.archivalEra.contains("1905"))
        assertTrue(rajgir.historicalPhotographer.contains("Marshall", ignoreCase = true))
        assertTrue(rajgir.historicalAccessionId.contains("Plate XXIX"))
        assertTrue(rajgir.statutoryCopyrightAnalysis.contains("1958")) // Marshall death year
        assertTrue(rajgir.statutoryCopyrightAnalysis.contains("2019")) // Expired 2019
    }

    @Test
    fun threeSiteAssetScheduleConsistency() {
        val comparisons = ThenAndNowCorpus.all()
        org.junit.Assert.assertEquals("Target must be exactly 3 sites / 3 comparison pairs (6 images total)", 3, comparisons.size)
        val siteIds = comparisons.map { it.placeId }.toSet()
        assertTrue(siteIds.contains("in-bihar-bodhgaya-mahabodhi"))
        assertTrue(siteIds.contains("in-bihar-nalanda-temple-03"))
        assertTrue(siteIds.contains("in-bihar-rajgir-cyclopean-wall"))

        val mahabodhi = ThenAndNowCorpus.get("in-bihar-bodhgaya-mahabodhi")!!
        assertTrue("Must identify Photo 1003(50) as primary plate", mahabodhi.historicalAccessionId.contains("Photo 1003(50)"))
        assertTrue("Must clarify Photo 1003(49) is not a substitute for other sites", mahabodhi.historicalAccessionId.contains("not a substitute for Nalanda or Rajgir"))
    }
}
