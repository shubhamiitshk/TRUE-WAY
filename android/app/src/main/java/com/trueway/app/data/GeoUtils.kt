package com.trueway.app.data

import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.roundToInt
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Offline geodesic utility functions for F005 (Optional GPS) and F008 (Offline Nearby).
 * Computes great-circle distances using the standard Haversine formulation.
 *
 * Invariants:
 * - 100% offline, pure local mathematics, zero network calls.
 * - Earth mean radius: 6,371,000 meters (WGS84 spherical approximation).
 * - Distances under 1,000 meters are formatted in meters (e.g. "350 m").
 * - Distances >= 1,000 meters are formatted in kilometers with 1 decimal place (e.g. "1.4 km").
 */
object GeoUtils {
    const val EARTH_RADIUS_METERS = 6_371_000.0

    /**
     * Calculates the great-circle distance between two decimal coordinates in meters.
     */
    fun distanceMeters(
        lat1: Double,
        lon1: Double,
        lat2: Double,
        lon2: Double,
    ): Double {
        val dLat = Math.toRadians(lat2 - lat1)
        val dLon = Math.toRadians(lon2 - lon1)
        val lat1Rad = Math.toRadians(lat1)
        val lat2Rad = Math.toRadians(lat2)

        val sinDLat = sin(dLat / 2)
        val sinDLon = sin(dLon / 2)

        val a = sinDLat * sinDLat + cos(lat1Rad) * cos(lat2Rad) * sinDLon * sinDLon
        val c = 2 * atan2(sqrt(a), sqrt(1.0 - a))
        return EARTH_RADIUS_METERS * c
    }

    /**
     * Formats a distance in meters into a readable string (e.g. "250 m" or "4.2 km").
     */
    fun formatDistance(meters: Double): String {
        return if (meters < 1000.0) {
            "${meters.roundToInt()} m"
        } else {
            val km = meters / 1000.0
            String.format(java.util.Locale.ROOT, "%.1f km", km)
        }
    }

    fun haversineMeters(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double =
        distanceMeters(lat1, lon1, lat2, lon2)

    fun formatDistanceMeters(meters: Double): String = formatDistance(meters)
}
