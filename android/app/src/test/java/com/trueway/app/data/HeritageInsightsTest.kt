package com.trueway.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Unit tests for P1B Offline Heritage Insights, Audience Lenses (F104/F109),
 * and Deterministic Citation-Grounded Offline Q&A (blueprint v3.0 §1 Decision #3, §2, §7).
 */
class HeritageInsightsTest {

    @Test
    fun allFifteenCorpusPlacesHaveCompleteOfflineInsightProfiles() {
        val demoPlaces = DemoCorpus.places
        assertEquals(15, demoPlaces.size)
        assertEquals(15, HeritageInsightsCorpus.all().size)

        for (place in demoPlaces) {
            val profile = HeritageInsightsCorpus.get(place.placeId)
            assertNotNull("Missing insight profile for ${place.placeId}", profile)
            profile!!
            assertTrue("Blank EN takeaway for ${place.placeId}", profile.quickTakeawayEn.isNotBlank())
            assertTrue("Blank HI takeaway for ${place.placeId}", profile.quickTakeawayHi.isNotBlank())
            assertTrue("Blank EN traveller narrative for ${place.placeId}", profile.travellerNarrativeEn.isNotBlank())
            assertTrue("Blank HI traveller narrative for ${place.placeId}", profile.travellerNarrativeHi.isNotBlank())
            assertTrue("Blank scholar context for ${place.placeId}", profile.scholarContextEn.isNotBlank())
            assertTrue("Empty spotter list for ${place.placeId}", profile.whatToSpotOnSite.isNotEmpty())
            assertTrue("Empty timeline for ${place.placeId}", profile.timeline.isNotEmpty())
            assertTrue("Empty FAQs for ${place.placeId}", profile.faqs.isNotEmpty())

            profile.whatToSpotOnSite.forEach { item ->
                assertTrue(item.featureTitle.isNotBlank())
                assertTrue(item.whereToLook.isNotBlank())
                assertTrue(item.explanation.isNotBlank())
                assertTrue(item.sourceId.isNotBlank())
            }
            profile.faqs.forEach { faq ->
                assertTrue(faq.questionEn.isNotBlank())
                assertTrue(faq.questionHi.isNotBlank())
                assertTrue(faq.answerEn.isNotBlank())
                assertTrue(faq.answerHi.isNotBlank())
                assertTrue(faq.sourceId.isNotBlank())
                assertTrue(faq.sourceTitle.isNotBlank())
            }
        }
    }

    @Test
    fun askOfflineResolvesCuratedMonumentQuestionsWithSourceTraceability() {
        val mahabodhiRes = HeritageInsightsCorpus.askOffline(
            "in-bihar-bodhgaya-mahabodhi",
            "Why are mobile phones and cameras banned?",
        )
        assertTrue(mahabodhiRes is QaResolution.Answered)
        val answered = mahabodhiRes as QaResolution.Answered
        assertTrue(answered.matchedFaqs.isNotEmpty())
        assertEquals(ClaimType.OPERATIONAL, answered.matchedFaqs.first().claimType)

        // Sonbhandar treasure query must preserve CONTESTED epistemic classification
        val sonbhandarRes = HeritageInsightsCorpus.askOffline(
            "in-bihar-rajgir-sonbhandar",
            "Is there hidden gold treasure inside the cave?",
        )
        assertTrue(sonbhandarRes is QaResolution.Answered)
        val sonAnswered = sonbhandarRes as QaResolution.Answered
        assertTrue(sonAnswered.matchedFaqs.isNotEmpty())
        assertEquals(ClaimType.CONTESTED, sonAnswered.matchedFaqs.first().claimType)
    }

    @Test
    fun askOfflineAbstainsOnLiveOperationalAndUnsupportedQueries() {
        val liveTicketRes = HeritageInsightsCorpus.askOffline(
            "in-bihar-nalanda-mahavihara",
            "What is the live ticket price and weather today?",
        )
        assertTrue("Live query must abstain", liveTicketRes is QaResolution.Abstained)
        val abstainedLive = liveTicketRes as QaResolution.Abstained
        assertTrue(abstainedLive.reason.contains("100% offline"))
        assertTrue(abstainedLive.fallbackClaims.isNotEmpty())

        val unknownTopicRes = HeritageInsightsCorpus.askOffline(
            "in-bihar-nalanda-mahavihara",
            "mars spacecraft orbital velocity",
        )
        assertTrue("Unrelated topic must abstain", unknownTopicRes is QaResolution.Abstained)
        val abstainedUnknown = unknownTopicRes as QaResolution.Abstained
        assertTrue(abstainedUnknown.reason.contains("abstains"))
    }

    @Test
    fun studyCardForGeneratesValidEpistemicCheckForAllFifteenPlaces() {
        for (place in DemoCorpus.places) {
            val card = HeritageInsightsCorpus.studyCardFor(place.placeId)
            assertNotNull("Expected StudyLiteCard for ${place.placeId}", card)
            card!!
            assertEquals(place.placeId, card.placeId)
            assertTrue(card.promptEn.isNotBlank())
            assertTrue(card.promptHi.isNotBlank())
            assertTrue(card.explanationEn.isNotBlank())
            assertTrue(card.explanationHi.isNotBlank())
            assertTrue(card.sourceId.isNotBlank())
            assertTrue(card.sourceTitle.isNotBlank())
            assertEquals(3, card.optionsEn.size)
            assertEquals(3, card.optionsHi.size)
            assertTrue(card.correctOptionIndex in card.optionsEn.indices)
        }
    }

    @Test
    fun searchCircuitInsightsMatchesCrossMonumentTopicsAndExcludesLiveQueries() {
        val mortarHits = HeritageInsightsCorpus.searchCircuitInsights("mortar")
        assertTrue("Expected Cyclopean Wall mortar hit", mortarHits.any { it.placeId == "in-bihar-rajgir-cyclopean-wall" })

        val stuccoHits = HeritageInsightsCorpus.searchCircuitInsights("stucco")
        assertTrue("Expected Nalanda Temple 3 stucco hit", stuccoHits.any { it.placeId == "in-bihar-nalanda-temple-03" })

        val treasureHits = HeritageInsightsCorpus.searchCircuitInsights("gold treasure")
        assertTrue("Expected Sonbhandar hit", treasureHits.any { it.placeId == "in-bihar-rajgir-sonbhandar" })

        // Live queries must never return fabricated insight hits
        val liveHits = HeritageInsightsCorpus.searchCircuitInsights("live ticket price weather today")
        assertTrue("Live queries must return empty insight hits", liveHits.isEmpty())
    }
}
