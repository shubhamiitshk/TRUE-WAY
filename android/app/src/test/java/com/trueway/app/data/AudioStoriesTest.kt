package com.trueway.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * P1A Audio stories & pronunciation guides gates (blueprint v3.0 §3, §7, F101/F110).
 *
 * Invariants:
 * - 10 flagship POIs have curated bilingual narratives.
 * - Every audio story includes both English and Hindi narrative scripts and transcripts.
 * - Phonetic pronunciation guide has valid IPA/phonetic formatting and audio duration metadata.
 * - Rights declarations and local asset paths are populated.
 * - All audio story placeIds resolve to valid places.
 */
class AudioStoriesTest {

    @Test
    fun audioStoriesExistAndResolveToPlaces() {
        val stories = AudioStoriesCorpus.all()
        assertEquals("Must contain 10 flagship POI audio stories", 10, stories.size)

        for (story in stories) {
            val place = PlaceRepository.get(story.placeId)
            assertNotNull("Audio story placeId ${story.placeId} must exist", place)

            assertTrue(story.title.isNotBlank())
            assertTrue(story.titleHindi.isNotBlank())
            assertTrue(story.durationSeconds in 30..600)
            assertTrue("English script must be non-empty", story.narrativeScriptEn.isNotBlank())
            assertTrue("Hindi script must be non-empty", story.narrativeScriptHi.isNotBlank())
            assertTrue("English transcript must be non-empty", story.transcriptEn.isNotBlank())
            assertTrue("Hindi transcript must be non-empty", story.transcriptHi.isNotBlank())
            assertTrue("Pronunciation guide must be non-empty", story.phoneticPronunciation.isNotBlank())
            assertTrue("Narrator credit must be non-empty", story.narratorCredit.isNotBlank())
            assertTrue("Rights notice must be non-empty", story.rightsNotice.isNotBlank())
            assertTrue("Audio asset path must be non-empty", story.audioAssetPath.isNotBlank())
            assertTrue("Review date must be non-empty", story.reviewDate.isNotBlank())
        }
    }

    @Test
    fun mahabodhiHasAccuratePronunciationAndScript() {
        val story = AudioStoriesCorpus.get("in-bihar-bodhgaya-mahabodhi")
        assertNotNull(story)
        assertTrue(story!!.phoneticPronunciation.contains("boː.dʱi"))
        assertTrue(story.narrativeScriptEn.contains("Ashoka", ignoreCase = true))
        assertTrue(story.narrativeScriptHi.contains("महाबोधि"))
    }
}
