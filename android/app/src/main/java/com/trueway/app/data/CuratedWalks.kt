package com.trueway.app.data

/**
 * P1A Curated Heritage Walks and dated trail notes (blueprint v3.0 §3, §7, F105/F112).
 *
 * Authored stop sequences with practical constraints:
 * - Walking duration labelled explicitly as an ESTIMATE.
 * - Terrain, mobility, and heat caveats included.
 * - Offline textual stop sequence works with zero map or GPS dependency.
 */
data class WalkStop(
    val placeId: String,
    val sequenceNumber: Int,
    val stopLabel: String,
    val segmentNotes: String,
)

data class CuratedWalk(
    val walkId: String,
    val title: String,
    val titleHindi: String,
    val summary: String,
    val circuitName: String,
    val estimatedMinutes: Int,
    val totalDistanceKm: Double,
    val terrainNotes: String,
    val seasonalAdvisory: String,
    val lastVerified: String,
    val stops: List<WalkStop>,
)

object CuratedWalksCorpus {
    val walks: List<CuratedWalk> = listOf(
        CuratedWalk(
            walkId = "walk-bodhgaya-sacred-circuit",
            title = "Bodh Gaya Sacred Enclosure Walk",
            titleHindi = "बोधगया पवित्र प्रदक्षिणा पथ",
            summary = "A tranquil circumambulation through the primary sites of the Buddha's Enlightenment landscape.",
            circuitName = "Bodh Gaya",
            estimatedMinutes = 50,
            totalDistanceKm = 1.2,
            terrainNotes = "Paved flat stone and marble walkways. Shoes must be removed before entering the inner complex; socks recommended during hot midday hours.",
            seasonalAdvisory = "Best experienced in early morning or late afternoon (6:00 AM – 8:30 AM or 4:30 PM – 7:00 PM). Midday stone paving can become excessively warm from March to June.",
            lastVerified = "2026-10-12",
            stops = listOf(
                WalkStop(
                    placeId = "in-bihar-bodhgaya-mahabodhi",
                    sequenceNumber = 1,
                    stopLabel = "Main Pyramid Shrine",
                    segmentNotes = "Begin at the eastern entrance gateway facing the 55-meter main shikhara.",
                ),
                WalkStop(
                    placeId = "in-bihar-bodhgaya-vajrasana",
                    sequenceNumber = 2,
                    stopLabel = "Vajrasana (Diamond Throne)",
                    segmentNotes = "Walk around to the western rear of the temple to the polished Mauryan sandstone slab.",
                ),
                WalkStop(
                    placeId = "in-bihar-bodhgaya-bodhi-tree",
                    sequenceNumber = 3,
                    stopLabel = "The Sacred Bodhi Tree",
                    segmentNotes = "Directly shading the Vajrasana; look for meditation platforms along the outer railing.",
                ),
                WalkStop(
                    placeId = "in-bihar-bodhgaya-animesh-lochan",
                    sequenceNumber = 4,
                    stopLabel = "Animesh Lochan Chaitya",
                    segmentNotes = "Move northeast along the upper terrace where the Buddha gazed at the tree for seven days.",
                ),
                WalkStop(
                    placeId = "in-bihar-bodhgaya-mucalinda",
                    sequenceNumber = 5,
                    stopLabel = "Mucalinda Sarovar (Lotus Pond)",
                    segmentNotes = "Conclude at the peaceful southern pond commemorating the naga protector.",
                ),
            ),
        ),
        CuratedWalk(
            walkId = "walk-rajgir-ancient-ridge",
            title = "Rajgir Ancient Hills & Fortress Trail",
            titleHindi = "राजगीर प्राचीन पहाड़ी और दुर्ग मार्ग",
            summary = "A dramatic historical trek linking Emperor Bimbisara's royal ascent to Griddhakuta Peak and the Cyclopean fortifications.",
            circuitName = "Rajgir",
            estimatedMinutes = 100,
            totalDistanceKm = 3.5,
            terrainNotes = "Moderate to steep incline along stone steps and hillside causeways. Uneven rocky terrain; chairlift option available for part of the ascent.",
            seasonalAdvisory = "Carry at least 1.5 liters of drinking water. High direct sun exposure with minimal tree canopy along the ridge.",
            lastVerified = "2026-10-12",
            stops = listOf(
                WalkStop(
                    placeId = "in-bihar-rajgir-vultures-peak",
                    sequenceNumber = 1,
                    stopLabel = "Griddhakuta (Vulture's Peak)",
                    segmentNotes = "Ascend Bimbisara's stone path to the sacred retreat terraces at the summit crag.",
                ),
                WalkStop(
                    placeId = "in-bihar-rajgir-shanti-stupa",
                    sequenceNumber = 2,
                    stopLabel = "Vishwa Shanti Stupa",
                    segmentNotes = "Follow the ridge pathway west to the gleaming white Peace Pagoda constructed in 1969.",
                ),
                WalkStop(
                    placeId = "in-bihar-rajgir-cyclopean-wall",
                    sequenceNumber = 3,
                    stopLabel = "Cyclopean Wall of Rajgir",
                    segmentNotes = "Descend towards the valley entrance to inspect the 2,500-year-old unmortared dry stone fortifications.",
                ),
                WalkStop(
                    placeId = "in-bihar-rajgir-sonbhandar",
                    sequenceNumber = 4,
                    stopLabel = "Sonbhandar Cave",
                    segmentNotes = "Complete the walk at the traditional rock-cut treasury cave at the base of Vaibhāra Hill.",
                ),
            ),
        ),
        CuratedWalk(
            walkId = "walk-nalanda-monastic-quadrangles",
            title = "Nalanda Ancient University Walk",
            titleHindi = "नालंदा प्राचीन विश्वविद्यालय परिसर पथ",
            summary = "A structured exploration across the grand educational architecture of Nalanda Mahavihara.",
            circuitName = "Nalanda",
            estimatedMinutes = 65,
            totalDistanceKm = 1.8,
            terrainNotes = "Level unshaded gravel and brick pathways between excavated monuments. Sturdy walking footwear advised.",
            seasonalAdvisory = "Morning visit recommended before 11:30 AM to avoid heat radiated by ancient brick surfaces.",
            lastVerified = "2026-10-12",
            stops = listOf(
                WalkStop(
                    placeId = "in-bihar-nalanda-temple-03",
                    sequenceNumber = 1,
                    stopLabel = "Temple 3 (Main Stupa)",
                    segmentNotes = "Observe the monumental 7-stage stupa plinth and recessed stucco Bodhisattva niches.",
                ),
                WalkStop(
                    placeId = "in-bihar-nalanda-monastery-01",
                    sequenceNumber = 2,
                    stopLabel = "Monastery 1 Quadrangle",
                    segmentNotes = "Walk east into the grandest residential monastery to inspect monk cells, student wells, and lecture podiums.",
                ),
                WalkStop(
                    placeId = "in-bihar-nalanda-museum",
                    sequenceNumber = 3,
                    stopLabel = "Nalanda Archaeological Museum",
                    segmentNotes = "Exit the excavated boundary to inspect bronzes, stone inscriptions, and seals recovered during site excavations.",
                ),
            ),
        ),
    )

    fun get(walkId: String): CuratedWalk? = walks.firstOrNull { it.walkId == walkId }
    fun all(): List<CuratedWalk> = walks
}
