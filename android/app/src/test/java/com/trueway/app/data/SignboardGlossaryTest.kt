package com.trueway.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Unit tests for P1B F103 Offline Signboard & ASI Plaque Decoder ([SignboardGlossary]).
 */
class SignboardGlossaryTest {

    @Test
    fun allSignboardGlossaryEntriesHaveCompleteBilingualMetadata() {
        val all = SignboardGlossary.all()
        assertTrue("Expected at least 12 signboard/plaque entries", all.size >= 12)
        val validPlaceIds = DemoCorpus.places.map { it.placeId }.toSet()

        for (entry in all) {
            assertTrue(entry.termId.isNotBlank())
            assertTrue(entry.scriptDevanagari.isNotBlank())
            assertTrue(entry.transliteration.isNotBlank())
            assertTrue(entry.englishTitle.isNotBlank())
            assertTrue(entry.meaningEn.isNotBlank())
            assertTrue(entry.meaningHi.isNotBlank())
            assertTrue(entry.whereSeenPlaceIds.isNotEmpty())
            assertTrue(entry.keywords.isNotEmpty())
            entry.whereSeenPlaceIds.forEach { pid ->
                assertTrue("Unknown placeId $pid in ${entry.termId}", pid in validPlaceIds)
            }
        }
    }

    @Test
    fun searchResolvesHindiDevanagariTransliteratedAndEnglishSignTerms() {
        val mobileHits = SignboardGlossary.search("मोबाइल varjit")
        assertTrue(mobileHits.any { it.termId == "sign-mobile-prohibited" })

        val viharaHits = SignboardGlossary.search("vihara quadrangle")
        assertTrue(viharaHits.any { it.termId == "term-mahavihara" })

        val mudraHits = SignboardGlossary.search("bhumisparsha")
        assertTrue(mudraHits.any { it.termId == "mudra-bhumisparsha" })
    }

    @Test
    fun shankhalipiEntryPreservesContestedEpistemicBoundary() {
        val sonbhandarSigns = SignboardGlossary.forPlace("in-bihar-rajgir-sonbhandar")
        val shankhalipi = sonbhandarSigns.find { it.termId == "term-shankhalipi" }
        assertTrue("Expected Shankhalipi term for Sonbhandar", shankhalipi != null)
        assertEquals(ClaimType.CONTESTED, shankhalipi!!.claimType)
        assertTrue(SignboardGlossary.EPIGRAPHY_BOUNDARY_NOTICE.contains("undeciphered"))
    }
}
