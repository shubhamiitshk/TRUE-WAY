package com.trueway.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Days 3-4 DoD: place_id / claim_id / source_id joins resolve locally,
 * search covers Devanagari + romanized aliases, unknown queries stay empty.
 * Mirrors content/seed/validate_seed.py gates on the JVM side.
 */
class PlaceRepositoryTest {

    @Test
    fun corpusHasAtLeastTenPlacesWithSourcedClaims() {
        assertTrue(PlaceRepository.all().size >= 10)
        for (place in PlaceRepository.all()) {
            assertTrue("empty claims: ${place.placeId}", place.claims.isNotEmpty())
            for (claim in place.claims) {
                assertTrue(claim.sourceId.isNotBlank())
                assertTrue(claim.sourceTitle.isNotBlank())
                assertTrue(claim.reviewedAt.isNotBlank())
            }
        }
    }

    @Test
    fun claimTypesUseBlueprintVocabulary() {
        val allowed = ClaimType.entries.map { it.name }.toSet()
        assertEquals(
            setOf("DOCUMENTED", "INTERPRETATION", "TRADITION", "CONTESTED", "OPERATIONAL", "HYPOTHESIS"),
            allowed,
        )
        // Mahabodhi keeps phases separate: documented listing + interpretation date + tradition.
        val mahabodhi = PlaceRepository.get("in-bihar-bodhgaya-mahabodhi")!!
        val types = mahabodhi.claims.map { it.type }.toSet()
        assertTrue(types.contains(ClaimType.DOCUMENTED))
        assertTrue(types.contains(ClaimType.TRADITION))
    }

    @Test
    fun searchFindsDevanagariAndRomanizedAliases() {
        assertTrue(PlaceRepository.search("Mahabodhi").any { it.placeId == "in-bihar-bodhgaya-mahabodhi" })
        assertTrue(PlaceRepository.search("महाबोधि").any { it.placeId == "in-bihar-bodhgaya-mahabodhi" })
        assertTrue(PlaceRepository.search("Mahabodhi Mandir").any { it.placeId == "in-bihar-bodhgaya-mahabodhi" })
        assertTrue(PlaceRepository.search("Griddhakuta").any { it.placeId == "in-bihar-rajgir-vultures-peak" })
        assertTrue(PlaceRepository.search("Nalanda").any { it.placeId == "in-bihar-nalanda-mahavihara" })
    }

    @Test
    fun unknownQueryReturnsEmptyRatherThanFabrication() {
        assertTrue(PlaceRepository.search("zxq unknown place 999").isEmpty())
        assertTrue(PlaceRepository.search("").isEmpty())
        assertTrue(PlaceRepository.search("   ").isEmpty())
    }

    @Test
    fun contestedLabelIsNeverFlattenedToDocumented() {
        val sonbhandar = PlaceRepository.get("in-bihar-rajgir-sonbhandar")!!
        assertTrue(sonbhandar.claims.all { it.type == ClaimType.CONTESTED })
    }

    @Test
    fun searchResolvesPhoneticSpellingVariants() {
        val gridhakootMatches = PlaceRepository.search("Gridhakoot")
        assertTrue("Gridhakoot matches vulture's peak", gridhakootMatches.any { it.placeId == "in-bihar-rajgir-vultures-peak" })

        val swarnaMatches = PlaceRepository.search("Swarnabhandar")
        assertTrue("Swarnabhandar matches sonbhandar", swarnaMatches.any { it.placeId == "in-bihar-rajgir-sonbhandar" })

        val mahabodiMatches = PlaceRepository.search("Mahabodi")
        assertTrue("Mahabodi matches mahabodhi", mahabodiMatches.any { it.placeId == "in-bihar-bodhgaya-mahabodhi" })
    }
}
