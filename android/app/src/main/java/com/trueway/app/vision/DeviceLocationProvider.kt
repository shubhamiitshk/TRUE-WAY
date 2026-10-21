package com.trueway.app.vision

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.Build
import androidx.core.content.ContextCompat

/**
 * Optional, coarse, LAST-KNOWN device location for the visual place-recognition
 * soft prior (blueprint §7.4).
 *
 * Design constraints:
 *  * No background tracking. Nothing is requested beyond a single
 *    `getLastKnownLocation` read at scan time — the app never starts a
 *    location listener and never keeps a fix.
 *  * Coarse only (`ACCESS_COARSE_LOCATION`): a place-recognition prior needs
 *    city-block accuracy, not metre accuracy.
 *  * Absence is normal, not an error. A denied, missing or stale fix simply
 *    disables the prior; the visual decision is unchanged.
 */
data class DeviceLocation(
    val latitude: Double,
    val longitude: Double,
    val accuracyMeters: Double?,
    val ageMs: Long,
)

object DeviceLocationProvider {

    /** True when the app holds the optional coarse-location permission. */
    fun hasPermission(context: Context): Boolean =
        ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION) ==
            PackageManager.PERMISSION_GRANTED

    /**
     * Best-effort last-known fix. Returns null when unavailable — the caller
     * then runs a pure-visual decision.
     */
    fun lastKnown(context: Context): DeviceLocation? {
        if (!hasPermission(context)) return null
        val lm = context.getSystemService(Context.LOCATION_SERVICE) as? LocationManager
            ?: return null
        val now = System.currentTimeMillis()
        var best: Location? = null
        for (provider in lm.getProviders(true)) {
            val loc = try {
                lm.getLastKnownLocation(provider)
            } catch (_: SecurityException) {
                null
            } catch (_: Exception) {
                null
            } ?: continue
            if (best == null || loc.time > best!!.time) best = loc
        }
        val loc = best ?: return null
        val age = (now - loc.time).coerceAtLeast(0L)
        // A fix older than a day is not a "soft prior", it is a wrong answer.
        if (age > 24L * 60 * 60 * 1000L) return null
        return DeviceLocation(
            latitude = loc.latitude,
            longitude = loc.longitude,
            accuracyMeters = if (loc.hasAccuracy()) loc.accuracy.toDouble() else null,
            ageMs = age,
        )
    }

    /**
     * Builds the prior for a scan. Returns [GeoPrior.DISABLED] when there is
     * no usable fix.
     */
    fun priorFor(context: Context, nowMs: Long = System.currentTimeMillis()): GeoPrior {
        val loc = lastKnown(context) ?: return GeoPrior.DISABLED
        return GeoPrior.fromLocation(
            latitude = loc.latitude,
            longitude = loc.longitude,
            accuracyM = loc.accuracyMeters,
            ageMs = loc.ageMs,
            nowMs = nowMs,
        )
    }

    /** Human-readable provenance for the QA record. */
    fun evidenceLabel(prior: GeoPrior): String =
        if (prior.lambda <= 0.0) "VISION" else "VISION+GPS"
}
