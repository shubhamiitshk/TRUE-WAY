package com.trueway.app.data

/**
 * Offline essentials (blueprint F011, §5.1).
 *
 * Concise, DATED reference data — not live services. Every entry carries a
 * last-verified date and the UI always pairs calls with the mobile-network
 * caveat: these numbers cannot connect without cellular coverage (§19.3).
 * Source of truth mirrored in content/seed/essentials.json; the pack builder
 * will own single-sourcing at pack week.
 */
data class EssentialContact(
    val label: String,
    val value: String,
    val lastVerified: String,
)

data class EssentialAdvice(
    val title: String,
    val body: String,
    val lastVerified: String,
)

object Essentials {
    const val CALL_CAVEAT =
        "Saved for reference. Calling still needs mobile network coverage."
    const val FRESHNESS_NOTE =
        "Opening information was last checked on the date shown and may have changed."

    val contacts = listOf(
        EssentialContact(
            label = "All-in-one emergency helpline (India)",
            value = "112",
            lastVerified = "2026-10-09",
        ),
        EssentialContact(
            label = "Incredible India tourist helpline",
            value = "1363",
            lastVerified = "2026-10-09",
        ),
    )

    val advice = listOf(
        EssentialAdvice(
            title = "Site etiquette",
            body = "Follow current on-site notices. At the Mahabodhi complex, " +
                "mobile phones, cameras and electronic gadgets are listed as " +
                "prohibited — use TrueWay before entry or only where devices " +
                "are allowed.",
            lastVerified = "2026-10-09",
        ),
        EssentialAdvice(
            title = "Heat and hill walks",
            body = "Rajgir ascents need water, daylight margin and confirmed " +
                "route access. Offline seasonal notes are generic awareness, " +
                "not a live weather window.",
            lastVerified = "2026-10-09",
        ),
    )
}

/**
 * Pack content changelog (blueprint F013, §9.3): human-readable history of
 * what changed per release. Mirrored in content/CHANGELOG.md.
 */
data class ChangelogRelease(
    val version: String,
    val date: String,
    val changes: List<String>,
)

object PackChangelog {
    val releases = listOf(
        ChangelogRelease(
            version = "2026.10.1",
            date = "2026-10-09",
            changes = listOf(
                "15-POI Bihar demonstrator corpus: Bodh Gaya, Rajgir, Nalanda.",
                "Mahabodhi device-prohibition notice with Bihar Tourism source.",
                "Sonbhandar cave correctly labelled CONTESTED, not treasure fact.",
                "Hindi short claims + romanized search aliases added.",
            ),
        ),
    )
}
