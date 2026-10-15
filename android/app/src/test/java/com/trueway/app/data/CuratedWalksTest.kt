package com.trueway.app.data

import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * P1A Curated Heritage Walking Trails gates (blueprint v3.0 §3, §7, F105/F112).
 *
 * Invariants:
 * - At least 3 curated trails exist covering Bodh Gaya, Rajgir, and Nalanda.
 * - Estimated durations are positive numbers marked as estimates.
 * - Every stop in every walk links to a known place in PlaceRepository.
 * - Waypoints are ordered in 1-based sequential order.
 * - Terrain warnings and heat advisories are non-blank.
 */
class CuratedWalksTest {

    @Test
    fun curatedWalksCorpusCoversMajorCircuits() {
        val walks = CuratedWalksCorpus.all()
        assertTrue("Must have at least 3 curated trails", walks.size >= 3)
        val circuits = walks.map { it.circuitName }.toSet()
        assertTrue(circuits.contains("Bodh Gaya"))
        assertTrue(circuits.contains("Rajgir"))
        assertTrue(circuits.contains("Nalanda"))
    }

    @Test
    fun allWalkStopsResolveToPlaces() {
        for (walk in CuratedWalksCorpus.all()) {
            assertTrue("Estimated duration must be positive", walk.estimatedMinutes > 0)
            assertTrue(walk.terrainNotes.isNotBlank())
            assertTrue(walk.seasonalAdvisory.isNotBlank())
            assertTrue("Walk must have stops", walk.stops.isNotEmpty())

            var expectedOrder = 1
            for (stop in walk.stops) {
                val place = PlaceRepository.get(stop.placeId)
                assertNotNull("Stop placeId ${stop.placeId} must resolve in PlaceRepository", place)
                assertTrue(stop.sequenceNumber == expectedOrder++)
                assertTrue(stop.segmentNotes.isNotBlank())
            }
        }
    }

    @Test
    fun getByIdFindsSpecificWalk() {
        val bodhgayaWalk = CuratedWalksCorpus.get("walk-bodhgaya-sacred-circuit")
        assertNotNull(bodhgayaWalk)
        assertTrue(bodhgayaWalk!!.title.contains("Bodh Gaya"))
        assertTrue(bodhgayaWalk.stops.any { it.placeId == "in-bihar-bodhgaya-mahabodhi" })
        assertTrue(bodhgayaWalk.stops.any { it.placeId == "in-bihar-bodhgaya-bodhi-tree" })
        assertTrue(bodhgayaWalk.stops.any { it.placeId == "in-bihar-bodhgaya-vajrasana" })
    }
}
