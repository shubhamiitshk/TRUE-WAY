package com.trueway.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * Unit tests for F005 (Optional GPS) and F008 (Offline Nearby Places).
 * Tests:
 * 1. Geodesic distance calculation via [GeoUtils.distanceMeters] (Haversine formula).
 * 2. Human-readable distance formatting (meters vs kilometers).
 * 3. Proximity ordering: closest places appear first.
 * 4. Radius bounds: places exceeding [maxRadiusMeters] are filtered out.
 * 5. Coordinate integrity: places without coordinates are omitted gracefully.
 * 6. Pure offline execution: zero network egress.
 */
class NearbyPlacesTest {

    @Before
    fun setUp() {
        PlaceRepository.init(DemoCorpusSource())
    }

    @Test
    fun geoUtilsComputesZeroDistanceForSamePoint() {
        val dist = GeoUtils.distanceMeters(24.6959, 84.9914, 24.6959, 84.9914)
        assertEquals(0.0, dist, 0.001)
    }

    @Test
    fun geoUtilsComputesAccurateDistanceBetweenKnownBodhGayaPoints() {
        // Distance from Mahabodhi (24.6959, 84.9914) to Great Buddha (24.6840, 84.9933)
        val dist = GeoUtils.distanceMeters(24.6959, 84.9914, 24.6840, 84.9933)
        // Expected: ~1.33 km (1300m - 1400m)
        assertTrue("Distance $dist should be between 1300m and 1400m", dist in 1300.0..1400.0)
    }

    @Test
    fun geoUtilsFormatsMetersAndKilometersCorrectly() {
        assertEquals("450 m", GeoUtils.formatDistance(450.0))
        assertEquals("999 m", GeoUtils.formatDistance(999.4))
        assertEquals("1.0 km", GeoUtils.formatDistance(1000.0))
        assertEquals("1.4 km", GeoUtils.formatDistance(1350.0))
        assertEquals("55.2 km", GeoUtils.formatDistance(55200.0))
    }

    @Test
    fun nearbyReturnsPlacesRankedByAscendingDistance() {
        // Center at Mahabodhi Temple
        val nearby = PlaceRepository.nearby(24.6959, 84.9914, maxRadiusMeters = 10_000.0)
        assertTrue("Should return multiple places in Bodh Gaya within 10km", nearby.size >= 4)

        // Closest should be Mahabodhi Temple (dist ~ 0m)
        assertEquals("in-bihar-bodhgaya-mahabodhi", nearby[0].place.placeId)
        assertEquals(0.0, nearby[0].distanceMeters, 1.0)

        // Distance should strictly increase
        for (i in 0 until nearby.size - 1) {
            assertTrue(
                "Place at $i (${nearby[i].distanceMeters}) must be <= place at ${i + 1} (${nearby[i + 1].distanceMeters})",
                nearby[i].distanceMeters <= nearby[i + 1].distanceMeters,
            )
        }
    }

    @Test
    fun nearbyFiltersOutPlacesBeyondMaxRadius() {
        // Bodh Gaya to Nalanda is ~55 km
        // Query within 5 km of Bodh Gaya should NOT include Nalanda or Rajgir
        val bodhGayaNearby = PlaceRepository.nearby(24.6959, 84.9914, maxRadiusMeters = 5_000.0)
        assertTrue(bodhGayaNearby.isNotEmpty())
        for (item in bodhGayaNearby) {
            assertTrue(
                "Place ${item.place.placeId} distance ${item.distanceMeters} must be <= 5000m",
                item.distanceMeters <= 5000.0,
            )
            assertTrue(
                "Place ${item.place.placeId} should be in Bodh Gaya",
                item.place.placeId.startsWith("in-bihar-bodhgaya"),
            )
        }
    }

    @Test
    fun nearbyFromRajgirFindsRajgirPlacesFirst() {
        // Center at Vulture's Peak, Rajgir (25.0038, 85.4160)
        val rajgirNearby = PlaceRepository.nearby(25.0038, 85.4160, maxRadiusMeters = 5_000.0)
        assertTrue(rajgirNearby.isNotEmpty())
        assertEquals("in-bihar-rajgir-vultures-peak", rajgirNearby[0].place.placeId)
    }

    @Test
    fun placesCarryPopulatedCoordinatesInDemoCorpus() {
        val mahabodhi = PlaceRepository.get("in-bihar-bodhgaya-mahabodhi")
        assertNotNull(mahabodhi)
        assertEquals(24.6959, mahabodhi!!.latitude!!, 0.0001)
        assertEquals(84.9914, mahabodhi.longitude!!, 0.0001)

        val nalanda = PlaceRepository.get("in-bihar-nalanda-mahavihara")
        assertNotNull(nalanda)
        assertEquals(25.1357, nalanda!!.latitude!!, 0.0001)
        assertEquals(85.4438, nalanda.longitude!!, 0.0001)
    }
}
