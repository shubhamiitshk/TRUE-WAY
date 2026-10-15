package com.trueway.app.data

/**
 * Before You Enter pre-visit briefing & compliance data (blueprint v3.0 §3, §5B, §6).
 *
 * Implements the P0.5 site restriction protocol:
 * - Outside restricted areas only: travelers view rules, save briefing, put device away.
 * - Never suggests device use inside prohibited zones (e.g. Mahabodhi Temple complex generally).
 * - Dated official notices (Bihar Tourism / BTMC).
 */
data class SiteBriefing(
    val placeId: String,
    val siteName: String,
    val authorityNotice: String,
    val restrictionLevel: RestrictionLevel,
    val lastVerified: String,
    val permittedUseBoundary: String,
    val keyObservations: List<String>,
    val preparationAdvice: String,
)

enum class RestrictionLevel {
    DEVICE_PROHIBITED, // Mobile phones, cameras strictly prohibited across temple complex (e.g. Mahabodhi)
    PHOTOGRAPHY_RESTRICTED, // Outdoor photos permitted, designated areas restricted
    ASCENT_SAFETY_HAZARD, // Steep ascents, intense heat (e.g. Griddhakuta Peak)
    ARCHAEOLOGICAL_CAUTION, // Fragile excavated structures (e.g. Nalanda ruins)
}

object BeforeYouEnterData {
    val briefings: Map<String, SiteBriefing> = mapOf(
        "in-bihar-bodhgaya-mahabodhi" to SiteBriefing(
            placeId = "in-bihar-bodhgaya-mahabodhi",
            siteName = "Mahabodhi Temple Complex",
            authorityNotice = "Bihar Tourism lists mobile phones, cameras, and electronic gadgets as prohibited for the Mahabodhi Temple complex generally (without restricting this to the sanctum). Check current entry rules and strictly obey security and site staff instructions.",
            restrictionLevel = RestrictionLevel.DEVICE_PROHIBITED,
            lastVerified = "2026-10-12",
            permittedUseBoundary = "Use TrueWay outside the temple gate only. Deposit phones in official cloakrooms before queueing. Do not attempt to carry active devices inside.",
            keyObservations = listOf(
                "Vajrasana (Diamond Throne): The polished sandstone slab behind the main shrine marking the seat of Enlightenment.",
                "The Sacred Bodhi Tree: Ficus religiosa descended from the original sapling sent to Sri Lanka by Emperor Ashoka's daughter Sanghamitta.",
                "Animesh Lochan Chaitya: Small shrine northeast of the main temple where Buddha stood for seven days gazing unblinkingly at the Bodhi Tree.",
                "Mucalinda Sarovar: South pond commemorating the serpent king Mucalinda shielding Buddha from a monsoon storm.",
            ),
            preparationAdvice = "Read your historical notes here, save this card to your device, and deposit your phone in the cloaking facility. Take your time to observe the stone carvings and circumambulation path without screens.",
        ),
        "in-bihar-nalanda-mahavihara" to SiteBriefing(
            placeId = "in-bihar-nalanda-mahavihara",
            siteName = "Nalanda Mahavihara Ruins",
            authorityNotice = "Archaeological Survey of India (ASI) centrally protected monument. Photography permitted on open paths. Climbing on brick structures is strictly forbidden.",
            restrictionLevel = RestrictionLevel.ARCHAEOLOGICAL_CAUTION,
            lastVerified = "2026-10-12",
            permittedUseBoundary = "Stay on paved tourist pathways. Maintain distance from stucco votive stupas and excavated brick plinths.",
            keyObservations = listOf(
                "Temple No. 3: The iconic stepped stupa layered across seven successive constructions (5th to 12th century CE).",
                "Monastery No. 1: Central courtyard with monk cells, drainage conduits, and evidence of multiple renovation strata.",
                "Granaries and Kitchen Wells: Evidence of community life supporting up to 10,000 students and scholars.",
            ),
            preparationAdvice = "Wear sun protection and comfortable walking shoes. The ruins cover extensive open ground with limited shade.",
        ),
        "in-bihar-rajgir-vultures-peak" to SiteBriefing(
            placeId = "in-bihar-rajgir-vultures-peak",
            siteName = "Griddhakuta (Vulture's Peak)",
            authorityNotice = "Protected natural and sacred heritage hill. High winds, steep stone steps, and remote hillside location.",
            restrictionLevel = RestrictionLevel.ASCENT_SAFETY_HAZARD,
            lastVerified = "2026-10-12",
            permittedUseBoundary = "Outdoor photography permitted. Mobile coverage is intermittent along the trail.",
            keyObservations = listOf(
                "Natural Rock Formation: The peak's distinctive rock outcrop resembling a vulture's beak.",
                "Buddha's Retreat Caves: Small brick terraces and caves where Buddha taught the Prajnaparamita and Lotus Sutras.",
                "Bimbisara's Ascent Road: Ancient stone causeway built by King Bimbisara of Magadha to visit the Buddha.",
            ),
            preparationAdvice = "Carry adequate drinking water and ascend during daylight hours. Steep steps require caution during rainy or excessively hot periods.",
        ),
    )

    fun get(placeId: String): SiteBriefing? = briefings[placeId]
    fun all(): List<SiteBriefing> = briefings.values.toList()
}
