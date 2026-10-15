package com.trueway.app.data

/**
 * 15-POI demonstrator corpus (Days 3-6). Verbatim editorial subset of
 * content/seed/seed_demo.sql — same place_ids, same claim/source anchors,
 * same §10.4 typology. Coordinates live in the seed SQL (approximate,
 * survey-pending); the app layer carries names, aliases, notices and
 * sourced claims so search + history cards work with zero network.
 *
 * Mahabodhi entries are SEARCH_ONLY: Bihar Tourism lists devices as
 * prohibited, so scanning there is never suggested (Journey C, §6.3).
 */
object DemoCorpus {
    private const val R09 = "2026-10-09"
    private const val UNESCO1056 = "UNESCO World Heritage Centre — Mahabodhi listing (whc.unesco.org/en/list/1056)"
    private const val UNESCO1502 = "UNESCO World Heritage Centre — Nalanda listing (whc.unesco.org/en/list/1502)"
    private const val BIHAR = "Bihar Tourism — Mahabodhi Temple visitor listing"
    private const val WIKIDATA = "Wikidata scaffold (CC0 identifiers; accuracy not assumed)"

    val places: List<Place> = listOf(
        Place(
            placeId = "in-bihar-bodhgaya-mahabodhi",
            canonicalName = "Mahabodhi Temple Complex",
            category = "temple-complex",
            aliases = listOf("Mahabodhi Temple", "महाबोधि मंदिर", "Mahabodhi Mandir"),
            visitorMode = "SEARCH_ONLY",
            visitorNotice = "Bihar Tourism lists mobile phones, cameras, and electronic gadgets as prohibited for the Mahabodhi Temple complex generally (without restricting this to the sanctum). Check current entry rules and strictly obey security and site staff instructions.",
            lastReviewedAt = R09,
            latitude = 24.6959,
            longitude = 84.9914,
            claims = listOf(
                SourcedClaim("cl-mahabodhi-listed", ClaimType.DOCUMENTED, "en", "UNESCO lists the Mahabodhi Temple Complex as a World Heritage property.", "src-unesco-1056", UNESCO1056, R09),
                SourcedClaim("cl-mahabodhi-date", ClaimType.INTERPRETATION, "en", "The surviving brick temple is generally dated to the 5th–6th centuries CE; the first temple at the site is attributed to Emperor Ashoka in the 3rd century BCE.", "src-unesco-1056", UNESCO1056, R09),
                SourcedClaim("cl-mahabodhi-tradition", ClaimType.TRADITION, "en", "According to Buddhist tradition, this site is associated with the Buddha's attainment of enlightenment — religious-historical context, not a laboratory-verifiable claim.", "src-unesco-1056", UNESCO1056, R09),
                SourcedClaim("cl-mahabodhi-devices", ClaimType.OPERATIONAL, "en", "Bihar Tourism lists mobile phones, cameras, and electronic gadgets as prohibited for the Mahabodhi Temple complex generally (without restricting this to the sanctum). Check current entry rules and strictly obey security and site staff instructions.", "src-bihar-mahabodhi", BIHAR, R09),
                SourcedClaim("cl-hi-mahabodhi-short", ClaimType.DOCUMENTED, "hi", "महाबोधि मंदिर परिसर यूनेस्को विश्व धरोहर सूची में अंकित है। स्रोत और समीक्षा तिथि कार्ड में देखें।", "src-unesco-1056", UNESCO1056, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-bodhgaya-bodhi-tree",
            parentPlaceId = "in-bihar-bodhgaya-mahabodhi",
            canonicalName = "Bodhi Tree context",
            category = "sacred-tree",
            aliases = listOf("Bodhi Tree", "बोधि वृक्ष", "Bodhi Vriksha"),
            visitorMode = "TEXT_REFERENCE_ONLY",
            visitorNotice = "Within the Mahabodhi complex; device rules of the parent site apply.",
            lastReviewedAt = R09,
            latitude = 24.6959,
            longitude = 84.9914,
            claims = listOf(
                SourcedClaim("cl-bodhitree-context", ClaimType.TRADITION, "en", "The Bodhi Tree setting is presented in living Buddhist tradition as the tree context of enlightenment; the present tree is a successor in a living pilgrimage landscape.", "src-unesco-1056", UNESCO1056, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-bodhgaya-vajrasana",
            parentPlaceId = "in-bihar-bodhgaya-mahabodhi",
            canonicalName = "Vajrasana (Diamond Throne)",
            category = "shrine-element",
            aliases = listOf("Vajrasana", "वज्रासन", "Diamond Throne"),
            visitorMode = "TEXT_REFERENCE_ONLY",
            visitorNotice = "Within the Mahabodhi complex; device rules of the parent site apply.",
            lastReviewedAt = R09,
            latitude = 24.6959,
            longitude = 84.9914,
            claims = listOf(
                SourcedClaim("cl-vajrasana-context", ClaimType.INTERPRETATION, "en", "The Vajrasana is interpreted as the ritual seat/throne platform associated with the enlightenment narrative; art-historical dating needs specialist sources.", "src-unesco-1056", UNESCO1056, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-bodhgaya-animesh-lochan",
            parentPlaceId = "in-bihar-bodhgaya-mahabodhi",
            canonicalName = "Animesh Lochan Chaitya",
            category = "chaitya",
            aliases = listOf("Animesh Lochan Chaitya", "Animeshlochan"),
            visitorMode = "SEARCH_ONLY",
            visitorNotice = "Small shrine in the Bodh Gaya area; confirm on-site device permission before photographing.",
            lastReviewedAt = R09,
            latitude = 24.6965,
            longitude = 84.9930,
            claims = listOf(
                SourcedClaim("cl-animesh-note", ClaimType.INTERPRETATION, "en", "Animesh Lochan Chaitya is traditionally linked to a week of contemplation after enlightenment; treat the narrative link as tradition and the standing fabric as interpretation.", "src-unesco-1056", UNESCO1056, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-bodhgaya-mucalinda",
            parentPlaceId = "in-bihar-bodhgaya-mahabodhi",
            canonicalName = "Mucalinda Sarovar (Lotus Pond)",
            category = "pond",
            aliases = listOf("Mucalinda Sarovar", "मुचलिंद सरोवर", "Lotus Pond"),
            visitorMode = "SEARCH_ONLY",
            visitorNotice = "Tank/pond context within the Bodh Gaya pilgrimage landscape.",
            lastReviewedAt = R09,
            latitude = 24.6948,
            longitude = 84.9925,
            claims = listOf(
                SourcedClaim("cl-mucalinda-note", ClaimType.TRADITION, "en", "Mucalinda Sarovar is linked in tradition to the serpent-king sheltering narrative; the tank visible today is part of the managed pilgrimage landscape.", "src-unesco-1056", UNESCO1056, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-bodhgaya-great-buddha",
            canonicalName = "Great Buddha statue (Bodh Gaya)",
            category = "statue",
            aliases = listOf("Great Buddha", "महान बुद्ध प्रतिमा", "Mahan Buddha Pratima"),
            visitorMode = "PHOTO_SUPPORTED",
            visitorNotice = "Modern statue in an accessible outdoor setting; follow local photography guidance.",
            lastReviewedAt = R09,
            latitude = 24.6840,
            longitude = 84.9933,
            claims = listOf(
                SourcedClaim("cl-greatbuddha-note", ClaimType.DOCUMENTED, "en", "The Great Buddha statue is a modern monumental image and wayfinding landmark; it is not an ancient excavated structure.", "src-wikidata-scaffold", WIKIDATA, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-rajgir-vultures-peak",
            canonicalName = "Griddhakuta (Vulture's Peak)",
            category = "hill-viewpoint",
            aliases = listOf("Vulture's Peak", "Vultures Peak", "गृध्रकूट", "Griddhakuta"),
            visitorMode = "TRAIL_STOP",
            visitorNotice = "Hill ascent; carry water, allow time, and confirm route access locally.",
            lastReviewedAt = R09,
            latitude = 25.0038,
            longitude = 85.4160,
            claims = listOf(
                SourcedClaim("cl-vulture-note", ClaimType.TRADITION, "en", "Griddhakuta is associated in Buddhist tradition with discourses and retreat; precise event-to-rock identifications are traditional rather than excavated certainties.", "src-wikidata-scaffold", WIKIDATA, R09),
                SourcedClaim("cl-vulture-access", ClaimType.OPERATIONAL, "en", "Ascent involves a hill walk of variable difficulty; confirm route access, heat precautions and water stops locally before setting out.", "src-wikidata-scaffold", WIKIDATA, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-rajgir-venu-vana",
            canonicalName = "Venu Vana",
            category = "grove",
            aliases = listOf("Venu Vana", "वेणु वन", "Venavana"),
            visitorMode = "SEARCH_ONLY",
            visitorNotice = "Garden/grove setting; confirm access and photography norms on site.",
            lastReviewedAt = R09,
            latitude = 24.9990,
            longitude = 85.4210,
            claims = listOf(
                SourcedClaim("cl-venuvana-note", ClaimType.TRADITION, "en", "Venu Vana is traditionally identified as a bamboo-grove gift associated with the Buddha's stays; treat the identification as tradition pending specialist review.", "src-wikidata-scaffold", WIKIDATA, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-rajgir-cyclopean-wall",
            canonicalName = "Cyclopean Wall (Rajgir)",
            category = "fortification",
            aliases = listOf("Cyclopean Wall", "Cyclopean Wall Rajgir"),
            visitorMode = "PHOTO_SUPPORTED",
            visitorNotice = "Long wall remains across varied terrain; photograph only where access is permitted.",
            lastReviewedAt = R09,
            latitude = 25.0120,
            longitude = 85.4230,
            claims = listOf(
                SourcedClaim("cl-wall-note", ClaimType.INTERPRETATION, "en", "The Cyclopean Wall comprises massive dry-stone walling around the Rajgir valley; full chronology and phasing need archaeological source review per segment.", "src-wikidata-scaffold", WIKIDATA, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-rajgir-shanti-stupa",
            canonicalName = "Vishwa Shanti Stupa (Rajgir)",
            category = "stupa-modern",
            aliases = listOf("Vishwa Shanti Stupa", "विश्व शांति स्तूप", "Shanti Stupa", "Peace Pagoda Rajgir"),
            visitorMode = "PHOTO_SUPPORTED",
            visitorNotice = "Modern stupa complex; ropeway/walk access varies — verify locally.",
            lastReviewedAt = R09,
            latitude = 25.0056,
            longitude = 85.4237,
            claims = listOf(
                SourcedClaim("cl-shanti-note", ClaimType.DOCUMENTED, "en", "The Vishwa Shanti Stupa is a modern peace stupa and viewpoint complex; access information changes and must be verified on site.", "src-wikidata-scaffold", WIKIDATA, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-rajgir-sonbhandar",
            canonicalName = "Sonbhandar Cave (traditional association)",
            category = "cave",
            aliases = listOf("Sonbhandar", "सोनभंडार गुफा", "Sonbhandar Gufa", "Son Bhandar Cave"),
            visitorMode = "SEARCH_ONLY",
            visitorNotice = "Traditional treasure-cave association is unverified; see TRADITION note on the history card.",
            lastReviewedAt = R09,
            latitude = 25.0090,
            longitude = 85.4300,
            claims = listOf(
                SourcedClaim("cl-sonbhandar-contested", ClaimType.CONTESTED, "en", "Sonbhandar carries a traditional treasure-cave narrative; inscriptional and chronological readings differ and are presented here as unresolved, not as established treasure fact.", "src-wikidata-scaffold", WIKIDATA, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-nalanda-mahavihara",
            canonicalName = "Nalanda Mahavihara archaeological site",
            category = "archaeological-site",
            aliases = listOf("Nalanda", "नालंदा महाविहार", "Nalanda Mahavihara", "नालंदा"),
            visitorMode = "SEARCH_ONLY",
            visitorNotice = "Parent archaeological site; individual structures are sub-place articles.",
            lastReviewedAt = R09,
            latitude = 25.1357,
            longitude = 85.4438,
            claims = listOf(
                SourcedClaim("cl-nalanda-listed", ClaimType.DOCUMENTED, "en", "UNESCO lists the Archaeological Site of Nalanda Mahavihara as a World Heritage property evidencing monastic, scholastic and Buddhist institutional development.", "src-unesco-1502", UNESCO1502, R09),
                SourcedClaim("cl-nalanda-scope", ClaimType.INTERPRETATION, "en", "The site comprises stupas, shrines, viharas and associated structures; individual building numbers are curatorial labels, not ancient names.", "src-unesco-1502", UNESCO1502, R09),
                SourcedClaim("cl-hi-nalanda-short", ClaimType.DOCUMENTED, "hi", "नालंदा महाविहार पुरातात्विक स्थल यूनेस्को विश्व धरोहर सूची में अंकित है। विस्तृत व्याख्या अंग्रेज़ी स्रोत कार्ड से सत्यापित करें।", "src-unesco-1502", UNESCO1502, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-nalanda-temple-03",
            parentPlaceId = "in-bihar-nalanda-mahavihara",
            canonicalName = "Temple 3 (illustrative label; verify with curator)",
            category = "temple",
            aliases = listOf("Temple 3", "Nalanda Temple 3"),
            visitorMode = "PHOTO_SUPPORTED",
            visitorNotice = "Excavated temple feature; confirm identification with curator before beta.",
            lastReviewedAt = R09,
            latitude = 25.1365,
            longitude = 85.4445,
            claims = listOf(
                SourcedClaim("cl-temple03-note", ClaimType.INTERPRETATION, "en", "Temple 3 is presented as one excavated temple/stupa feature of the complex; confirm the exact identification with the curator before treating it as an independent scan target.", "src-unesco-1502", UNESCO1502, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-nalanda-monastery-01",
            parentPlaceId = "in-bihar-nalanda-mahavihara",
            canonicalName = "Monastery 1 range (illustrative label)",
            category = "monastery",
            aliases = listOf("Monastery 1", "Nalanda Monastery 1", "Vihara 1"),
            visitorMode = "SEARCH_ONLY",
            visitorNotice = "Excavated monastery range; sub-place article under the parent site.",
            lastReviewedAt = R09,
            latitude = 25.1350,
            longitude = 85.4430,
            claims = listOf(
                SourcedClaim("cl-monastery01-note", ClaimType.INTERPRETATION, "en", "The monastery ranges show excavated cells, halls and drainage features; map photographic labels to surveyed plans rather than brochure names.", "src-unesco-1502", UNESCO1502, R09),
            ),
        ),
        Place(
            placeId = "in-bihar-nalanda-museum",
            parentPlaceId = "in-bihar-nalanda-mahavihara",
            canonicalName = "Nalanda Archaeological Museum (partner-gated)",
            category = "museum",
            aliases = listOf("Nalanda Museum", "Archaeological Museum Nalanda"),
            visitorMode = "QR_PARTNER",
            visitorNotice = "Indoor museum; QR touchpoints only under a signed partner agreement (P1).",
            lastReviewedAt = R09,
            latitude = 25.1370,
            longitude = 85.4450,
            claims = listOf(
                SourcedClaim("cl-museum-note", ClaimType.OPERATIONAL, "en", "The site museum displays excavated finds indoors; indoor QR/BLE experiences require a signed partner agreement and device-use permission.", "src-wikidata-scaffold", WIKIDATA, R09),
            ),
        ),
    )
}
