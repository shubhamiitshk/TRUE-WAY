package com.trueway.app.data

/**
 * P1A Heritage Passport commemorative collection (blueprint v3.0 §3, §7, F107).
 *
 * Design constraints:
 * - Private, offline-first personal travel memory collection.
 * - Self-recorded visits (no mandatory GPS proof or tracking).
 * - Clear disclaimer: Personal memory collection — NOT an official government or archaeological credential.
 */
data class PassportStamp(
    val stampId: String,
    val placeId: String,
    val stampTitle: String,
    val stampTitleHindi: String,
    val circuitName: String,
    val emblemDescription: String,
    val historicalInscription: String,
)

object HeritagePassportCorpus {
    const val DISCLAIMER =
        "Personal commemorative collection. Stamped entries are self-recorded by the traveler on this device and do not constitute official archaeological, government, or temple credentials."

    val stamps: Map<String, PassportStamp> = mapOf(
        "in-bihar-bodhgaya-mahabodhi" to PassportStamp(
            stampId = "stamp-bodhgaya-mahabodhi",
            placeId = "in-bihar-bodhgaya-mahabodhi",
            stampTitle = "Bodh Gaya Enlightenment Seal",
            stampTitleHindi = "बोधगया संबोधि मुद्रा",
            circuitName = "Bodh Gaya Circuit",
            emblemDescription = "Sacred Bodhi leaf and Diamond Throne (Vajrasana) motif",
            historicalInscription = "Bodh Gaya — Where Siddhartha Gautama attained Supreme Enlightenment (c. 6th-5th c. BCE)",
        ),
        "in-bihar-bodhgaya-great-buddha" to PassportStamp(
            stampId = "stamp-bodhgaya-great-buddha",
            placeId = "in-bihar-bodhgaya-great-buddha",
            stampTitle = "Great Buddha Peace Seal",
            stampTitleHindi = "महान बुद्ध शांति मुद्रा",
            circuitName = "Bodh Gaya Circuit",
            emblemDescription = "Dhyana Mudra meditative posture silhouette",
            historicalInscription = "Daibutsu — Dedicated to Universal World Peace",
        ),
        "in-bihar-nalanda-mahavihara" to PassportStamp(
            stampId = "stamp-nalanda-mahavihara",
            placeId = "in-bihar-nalanda-mahavihara",
            stampTitle = "Nalanda Scholar Seal",
            stampTitleHindi = "नालंदा महाविहार विद्वान मुद्रा",
            circuitName = "Nalanda Circuit",
            emblemDescription = "Ancient Dharmachakra flanked by two gazelles",
            historicalInscription = "Sri Nalanda Mahavihariyarya Bhikshu Sanghasya — Seal of the Venerable Monastic Order of Nalanda",
        ),
        "in-bihar-nalanda-temple-03" to PassportStamp(
            stampId = "stamp-nalanda-temple-03",
            placeId = "in-bihar-nalanda-temple-03",
            stampTitle = "Stupa of Sariputra Seal",
            stampTitleHindi = "सारिपुत्र स्तूप मुद्रा",
            circuitName = "Nalanda Circuit",
            emblemDescription = "Seven-tiered stepped stupa with votive chaityas",
            historicalInscription = "Temple 3 — Commemorating the birthplace and parinirvana of Sariputra",
        ),
        "in-bihar-rajgir-vultures-peak" to PassportStamp(
            stampId = "stamp-rajgir-vultures-peak",
            placeId = "in-bihar-rajgir-vultures-peak",
            stampTitle = "Griddhakuta Summit Seal",
            stampTitleHindi = "गृद्धकूट शिखर मुद्रा",
            circuitName = "Rajgir Circuit",
            emblemDescription = "Vulture crag silhouette above mountain ridgeline",
            historicalInscription = "Rajgir — Retreat where the Buddha taught the Heart Sutra and Lotus Sutra",
        ),
        "in-bihar-rajgir-cyclopean-wall" to PassportStamp(
            stampId = "stamp-rajgir-cyclopean-wall",
            placeId = "in-bihar-rajgir-cyclopean-wall",
            stampTitle = "Magadhan Fortress Seal",
            stampTitleHindi = "मगध दुर्ग प्राचीर मुद्रा",
            circuitName = "Rajgir Circuit",
            emblemDescription = "Interlocking dry stone masonry fortress bastion",
            historicalInscription = "Cyclopean Wall of Rajagriha — 6th Century BCE Magadhan Ramparts",
        ),
    )

    fun get(placeId: String): PassportStamp? = stamps[placeId]
    fun all(): List<PassportStamp> = stamps.values.toList()
}
