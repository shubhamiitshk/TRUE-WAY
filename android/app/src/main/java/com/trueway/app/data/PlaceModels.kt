package com.trueway.app.data

/**
 * Knowledge-layer models mirroring blueprint §10.1 / §10.4 and
 * content/seed/seed_demo.sql. Pure Kotlin (no Android deps) so the
 * claim/source join rules stay JVM-unit-testable (Days 3-4 DoD).
 *
 * Source ≠ licence: [sourceId] here is the editorial provenance anchor.
 * Rights metadata lives at the asset level in the pack builder (§10.4).
 */
enum class ClaimType {
    DOCUMENTED,
    INTERPRETATION,
    TRADITION,
    CONTESTED,
    OPERATIONAL,
    HYPOTHESIS,
}

data class SourcedClaim(
    val claimId: String,
    val type: ClaimType,
    val locale: String,
    val text: String,
    val sourceId: String,
    val sourceTitle: String,
    val reviewedAt: String,
)

data class Place(
    val placeId: String,
    val parentPlaceId: String? = null,
    val canonicalName: String,
    val category: String,
    /** Search surface: canonical + alternates + hi + hi-Latn (§10.3). */
    val aliases: List<String> = emptyList(),
    val visitorMode: String,
    val visitorNotice: String,
    val lastReviewedAt: String,
    val claims: List<SourcedClaim>,
    val latitude: Double? = null,
    val longitude: Double? = null,
)

/**
 * Proximity-ranked place entry for offline nearby discovery (F005/F008).
 * Pure local calculation; zero network egress.
 */
data class NearbyPlace(
    val place: Place,
    val distanceMeters: Double,
    val distanceFormatted: String,
)
