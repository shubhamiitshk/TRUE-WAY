package com.trueway.app.data

/**
 * Offline Traveller Heritage Insights, Audience Lenses, On-Site Architectural Spotter,
 * and Deterministic Extractive Q&A Engine (blueprint v3.0 §1 Decision #3, §2, §3 P1B F104/F109, §7;
 * Strategic Blueprint §1.1 Tier 1 Zero-Model Extractive RAG).
 *
 * Designed for travellers visiting heritage sites with zero internet connectivity:
 * 1. Multi-Depth Audience Lenses ([InsightLens]):
 *    - TRAVELLER: Clear, engaging explanation of why the site matters (EN + HI).
 *    - ARCHITECTURE: Concrete physical details to observe on-site with the naked eye (F104).
 *    - SCHOLAR: Stratigraphic, epigraphic, and primary-source context (F109).
 * 2. Chronological Timeline ([TimelineMilestone]):
 *    - Era-by-era milestones tagged with [ClaimType] and bibliography [sourceId].
 * 3. Deterministic Offline Q&A ([askOffline]):
 *    - Matches traveller questions against curated, claim-linked FAQs using lexical +
 *      [IndicPhoneticNormalizer] skeleton matching.
 *    - Strictly abstains ([QaResolution.Abstained]) on live operational queries (weather,
 *      tickets, hotels) or unsupported topics rather than fabricating history.
 */
enum class InsightLens(val label: String) {
    TRAVELLER("Traveller Guide"),
    ARCHITECTURE("What to Spot"),
    SCHOLAR("Scholar Lens"),
}

data class ArchitecturalSpotterItem(
    val featureTitle: String,
    val whereToLook: String,
    val explanation: String,
    val claimType: ClaimType,
    val sourceId: String,
)

data class TimelineMilestone(
    val eraLabel: String,
    val summary: String,
    val claimType: ClaimType,
    val sourceId: String,
)

data class OfflineQaItem(
    val qaId: String,
    val placeId: String,
    val questionEn: String,
    val questionHi: String,
    val answerEn: String,
    val answerHi: String,
    val keywords: List<String>,
    val claimType: ClaimType,
    val sourceId: String,
    val sourceTitle: String,
    val reviewedAt: String,
)

data class PlaceInsightProfile(
    val placeId: String,
    val quickTakeawayEn: String,
    val quickTakeawayHi: String,
    val travellerNarrativeEn: String,
    val travellerNarrativeHi: String,
    val scholarContextEn: String,
    val whatToSpotOnSite: List<ArchitecturalSpotterItem>,
    val timeline: List<TimelineMilestone>,
    val faqs: List<OfflineQaItem>,
)

sealed interface QaResolution {
    data class Answered(
        val query: String,
        val matchedFaqs: List<OfflineQaItem>,
        val relatedClaims: List<SourcedClaim>,
    ) : QaResolution

    data class Abstained(
        val query: String,
        val reason: String,
        val fallbackClaims: List<SourcedClaim>,
    ) : QaResolution
}

/**
 * P1B Study Lite claim-linked self-check card (blueprint v3.0 §3 P1B F116 & §4 Rank #8).
 * Helps travellers and students distinguish DOCUMENTED history from TRADITION and CONTESTED folklore.
 */
data class StudyLiteCard(
    val cardId: String,
    val placeId: String,
    val promptEn: String,
    val promptHi: String,
    val optionsEn: List<String>,
    val optionsHi: List<String>,
    val correctOptionIndex: Int,
    val explanationEn: String,
    val explanationHi: String,
    val claimType: ClaimType,
    val sourceId: String,
    val sourceTitle: String,
)

/**
 * Circuit-wide offline insight & FAQ search hit for ExploreScreen topic/question queries.
 */
data class InsightSearchHit(
    val placeId: String,
    val placeName: String,
    val matchTitle: String,
    val matchSummary: String,
    val claimType: ClaimType,
    val sourceTitle: String,
)

object HeritageInsightsCorpus {
    private const val R12 = "2026-10-12"
    private const val UNESCO1056 = "UNESCO World Heritage Centre — Mahabodhi listing (whc.unesco.org/en/list/1056)"
    private const val UNESCO1502 = "UNESCO World Heritage Centre — Nalanda listing (whc.unesco.org/en/list/1502)"
    private const val ASI_CUNNINGHAM = "Alexander Cunningham, Mahâbodhi or the Great Buddhist Temple (1892)"
    private const val ASI_MARSHALL = "Sir John Marshall, ASI Annual Report — Rajagriha Explorations (1905–1906)"
    private const val ASI_SPOONER = "Dr. D.B. Spooner, ASI Excavations at Nalanda (1915–1916)"
    private const val BIHAR_TOURISM = "Bihar Tourism — Official Visitor & Security Advisory"

    /**
     * Terms indicating live/transactional queries that a static offline pack must NEVER
     * pretend to know (Blueprint §1 Decision #5 & §3 Explicit Exclusions).
     */
    private val LIVE_QUERY_TRIGGERS = setOf(
        "ticket", "price", "cost", "fee", "weather", "rain", "temperature",
        "hotel", "booking", "restaurant", "bus", "train", "flight", "taxi",
        "uber", "open now", "closing time", "crowd", "queue", "wifi",
    )

    val profiles: Map<String, PlaceInsightProfile> = listOf(
        // 1. Mahabodhi Temple Complex
        PlaceInsightProfile(
            placeId = "in-bihar-bodhgaya-mahabodhi",
            quickTakeawayEn = "One of the earliest surviving grand brick temples of India (5th–6th c. CE Gupta structure over a 3rd c. BCE Mauryan foundation), marking the locus of the Buddha's Awakening.",
            quickTakeawayHi = "भारत के सबसे प्राचीन जीवित ईंट मंदिरों में से एक (5वीं-6वीं शताब्दी गुप्तकालीन संरचना, 3री शताब्दी ईसा पूर्व अशोककालीन नींव), जो बुद्ध के संबोधि स्थल का प्रतीक है।",
            travellerNarrativeEn = "Read this outside the gate before depositing your phone: Mahabodhi is not a single-period building, but a 2,200-year layered sanctuary. Emperor Ashoka first enclosed the Bodhi Tree and Diamond Throne around 250 BCE. Eight centuries later, late-Gupta architects raised the 55-meter straight-sided pyramidal tower (shikhara) you see today—a blueprint that influenced stupa and temple design across Myanmar, Thailand, and Indonesia.",
            travellerNarrativeHi = "प्रवेश द्वार के बाहर मोबाइल जमा करने से पहले इसे पढ़ें: महाबोधि एक कालखंड की इमारत नहीं, बल्कि 2,200 वर्षों की जीवित धरोहर है। सम्राट अशोक ने 250 ईसा पूर्व में यहाँ प्रथम पूजा स्थली बनाई। बाद में 5वीं-6वीं शताब्दी में गुप्तकालीन वास्तुकारों ने 55 मीटर ऊँचा सीधा शिखर निर्मित किया।",
            scholarContextEn = "Cunningham's 1880s excavations beneath the inner sanctum floor documented superimposed sandstone and plaster plinth layers linking the Ashokan open-pillared shrine (depicted on the Bharhut relief, c. 1st c. BCE) to the late-Gupta brick superstructure described by Xuanzang in 637 CE.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Two-Era Stone Railing (Vedika)",
                    whereToLook = "Quadrangular stone railing surrounding the main temple base",
                    explanation = "Look closely at the stone texture: warm buff Chunar sandstone posts with mirror-like polish date to the Mauryan/Sunga era (3rd–1st c. BCE), while coarser greyish granite posts with foliate medallions are late-Gupta additions (6th c. CE).",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-unesco-1056",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Panchayatana Corner Towers",
                    whereToLook = "Four smaller replica towers at the corners of the terrace",
                    explanation = "Notice how the four corner shrines echo the central 55m shikhara, forming an early five-shrined (panchayatana) architectural layout.",
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-unesco-1056",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Chaitya-Window Gavaksha Niches",
                    whereToLook = "Tiered exterior faces of the main brick tower",
                    explanation = "Each horizontal register features horseshoe-shaped chaitya arches coated in lime stucco, originally housing gilded stucco images of the Buddha.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-unesco-1056",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("c. 250 BCE", "Emperor Ashoka visits Sambodhi and establishes the Vajrasana and open-pillared bodhighara shrine.", ClaimType.INTERPRETATION, "src-unesco-1056"),
                TimelineMilestone("1st c. BCE", "Sunga-period sandstone railing posts added with lotus, yakshi, and Surya chariot reliefs.", ClaimType.DOCUMENTED, "src-unesco-1056"),
                TimelineMilestone("5th–6th c. CE", "Construction of the standing 55-meter late-Gupta brick temple tower.", ClaimType.INTERPRETATION, "src-unesco-1056"),
                TimelineMilestone("1880–1884 CE", "Archaeological conservation and shikhara restoration by J.D. Beglar and Alexander Cunningham.", ClaimType.DOCUMENTED, "src-unesco-1056"),
                TimelineMilestone("2002 CE", "Inscribed as a UNESCO World Heritage Site (Ref. 1056).", ClaimType.DOCUMENTED, "src-unesco-1056"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-mahabodhi-1",
                    placeId = "in-bihar-bodhgaya-mahabodhi",
                    questionEn = "Why are mobile phones and cameras banned inside the Mahabodhi complex?",
                    questionHi = "महाबोधि मंदिर परिसर के अंदर मोबाइल फोन और कैमरे क्यों प्रतिबंधित हैं?",
                    answerEn = "Bihar Tourism and the temple management prohibit mobile phones, cameras, and electronic gadgets across the Mahabodhi complex for security and sanctity. Use TrueWay's 'Before You Enter' briefing outside the perimeter and deposit your phone at the cloakroom before entry.",
                    answerHi = "सुरक्षा और पवित्रता के नियमों के तहत महाबोधि मंदिर परिसर में मोबाइल फोन और इलेक्ट्रॉनिक उपकरण वर्जित हैं। प्रवेश से पहले क्लोकरूम में फोन जमा करें।",
                    keywords = listOf("phone", "camera", "mobile", "banned", "allowed", "rules", "prohibited", "security", "मोबाइल", "कैमरा"),
                    claimType = ClaimType.OPERATIONAL,
                    sourceId = "src-bihar-mahabodhi",
                    sourceTitle = BIHAR_TOURISM,
                    reviewedAt = R12,
                ),
                OfflineQaItem(
                    qaId = "qa-mahabodhi-2",
                    placeId = "in-bihar-bodhgaya-mahabodhi",
                    questionEn = "How old is the standing Mahabodhi Temple tower?",
                    questionHi = "महाबोधि मंदिर का वर्तमान शिखर कितना पुराना है?",
                    answerEn = "The surviving 55-meter brick temple dates primarily to the late Gupta period (5th–6th centuries CE), with major historical repairs by Burmese missions and British-era ASI conservation in the 1880s, built over an earlier 3rd-century BCE Ashokan shrine site.",
                    answerHi = "वर्तमान 55 मीटर ऊँचा ईंट मंदिर मुख्य रूप से 5वीं-6वीं शताब्दी ईस्वी (गुप्त काल) का है, जो 3री शताब्दी ईसा पूर्व के अशोककालीन स्थल पर बना है।",
                    keywords = listOf("old", "age", "built", "date", "century", "ashoka", "gupta", "tower", "shikhara", "पुराना", "कब"),
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-unesco-1056",
                    sourceTitle = UNESCO1056,
                    reviewedAt = R12,
                ),
            ),
        ),

        // 2. Bodhi Tree
        PlaceInsightProfile(
            placeId = "in-bihar-bodhgaya-bodhi-tree",
            quickTakeawayEn = "Sacred Ficus religiosa on the western terrace of Mahabodhi; a living botanical descendant linked via Anuradhapura (Sri Lanka) to the 3rd-century BCE Mauryan sapling.",
            quickTakeawayHi = "महाबोधि के पश्चिमी चबूतरे पर स्थित पवित्र पीपल वृक्ष; अनुराधापुर (श्रीलंका) के माध्यम से मौर्यकालीन शाखा से जुड़ा जीवित वंशज।",
            travellerNarrativeEn = "Directly behind the western wall of the temple stands the Bodhi Tree. While no individual fig tree lives for 2,500 years, this specimen represents one of the longest documented botanical lineages in human history. When the previous tree fell during a storm in 1876, Alexander Cunningham planted a sapling in 1881 associated with the ancient stock.",
            travellerNarrativeHi = "मंदिर की पश्चिमी दीवार के ठीक पीछे पवित्र बोधि वृक्ष खड़ा है। 1876 में तूफान से पुराने वृक्ष के गिरने के बाद 1881 में अलेक्जेंडर कनिंघम ने वर्तमान वृक्ष का रोपण कराया था।",
            scholarContextEn = "Pali chronicles (Mahavamsa) record Sanghamitta Theri transporting the southern branch of the Bodhi Tree to Anuradhapura (Sri Lanka) during Ashoka's reign; Cunningham (1892) documented stratigraphic root layers beneath the western platform.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Heart-Shaped Pipal Leaves (Ficus religiosa)",
                    whereToLook = "Canopy overhanging the western circumambulation terrace",
                    explanation = "Notice the elongated drip-tips (caudate apices) of the leaves—a distinctive motif carved into Mauryan and Sunga stone reliefs across the complex.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-unesco-1056",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Tiered Stone Retaining Plinth",
                    whereToLook = "Circular masonry base enclosing the trunk",
                    explanation = "Raised over centuries to protect the aerial roots and accommodate successive ground-level rises of the courtyard.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-unesco-1056",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("3rd c. BCE", "Tradition records Princess Sanghamitta carrying a sapling from Bodh Gaya to Anuradhapura.", ClaimType.TRADITION, "src-unesco-1056"),
                TimelineMilestone("1881 CE", "Present successor tree planted during Cunningham's conservation campaign after the 1876 storm.", ClaimType.DOCUMENTED, "src-unesco-1056"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-bodhitree-1",
                    placeId = "in-bihar-bodhgaya-bodhi-tree",
                    questionEn = "Is this the exact same physical tree from the Buddha's lifetime?",
                    questionHi = "क्या यह बुद्ध के समय का ही मूल वृक्ष है?",
                    answerEn = "No—it is a direct successor planted in the late 19th century on the historic spot. Buddhist tradition links its lineage to the 3rd-century BCE cutting taken by Princess Sanghamitta to Sri Lanka.",
                    answerHi = "नहीं, यह 19वीं सदी के उत्तरार्ध में उसी ऐतिहासिक स्थान पर लगाया गया वंशज वृक्ष है, जिसकी परंपरा मौर्यकालीन शाखा से जुड़ी है।",
                    keywords = listOf("original", "same", "tree", "age", "sri lanka", "sanghamitta", "sapling", "मूल", "पेड़"),
                    claimType = ClaimType.TRADITION,
                    sourceId = "src-unesco-1056",
                    sourceTitle = UNESCO1056,
                    reviewedAt = R12,
                ),
            ),
        ),

        // 3. Vajrasana (Diamond Throne)
        PlaceInsightProfile(
            placeId = "in-bihar-bodhgaya-vajrasana",
            quickTakeawayEn = "Carved Chunar sandstone throne slab (c. 250 BCE) resting between the Bodhi Tree and the western temple wall, bearing mirror-like Mauryan polish.",
            quickTakeawayHi = "बोधि वृक्ष और मंदिर की पश्चिमी दीवार के बीच स्थित चुनार बलुआ पत्थर का वज्रासन (लगभग 250 ईसा पूर्व), जिस पर मौर्यकालीन चमक है।",
            travellerNarrativeEn = "Look between the Bodhi Tree's base and the temple wall: the flat grey-buff stone slab is the Vajrasana ('Diamond Throne'). Commissioned by Emperor Ashoka to mark the exact seat of meditation, it was uncovered during 1880s excavations with its carved goose-and-palmette frieze still intact.",
            travellerNarrativeHi = "बोधि वृक्ष और मंदिर की दीवार के बीच स्थित यह शिलापट 'वज्रासन' है। सम्राट अशोक द्वारा निर्मित इस आसन के किनारों पर हंसों और कमल की बारीक नक्काशी आज भी सुरक्षित है।",
            scholarContextEn = "Measured by Cunningham at 7 ft 10.5 in by 4 ft 7.5 in, carved from buff Chunar sandstone with characteristic Mauryan high polish and a peripheral frieze of pecking geese (hamsa) and honeysuckle palmettes.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Hamsa (Sacred Geese) & Palmette Border Frieze",
                    whereToLook = "Outer vertical edges of the sandstone slab",
                    explanation = "Look for alternating carved geese and floral palmettes—a signature motif shared with Ashokan pillar capitals at Lauriya Nandangarh and Sanchi.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-unesco-1056",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Geometric Top Surface Carving",
                    whereToLook = "Upper flat face of the throne platform",
                    explanation = "Incised with diamond/lotus geometric patterns that originally lay open beneath an Ashokan pillared canopy.",
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-unesco-1056",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("c. 250 BCE", "Carved from Chunar sandstone with Mauryan polish under Emperor Ashoka.", ClaimType.INTERPRETATION, "src-unesco-1056"),
                TimelineMilestone("1st c. BCE", "Depicted in the Bharhut Stupa relief inscribed 'Bhagavato Sakamunino Bodho'.", ClaimType.DOCUMENTED, "src-unesco-1056"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-vajrasana-1",
                    placeId = "in-bihar-bodhgaya-vajrasana",
                    questionEn = "What stone is the Vajrasana made of and why does it shine?",
                    questionHi = "वज्रासन किस पत्थर से बना है और यह क्यों चमकता है?",
                    answerEn = "It is carved from Chunar sandstone quarried near Varanasi and finished with 'Mauryan polish'—a mirror-like silica-burnished surface technique characteristic of 3rd-century BCE Ashokan stone workshops.",
                    answerHi = "यह वाराणसी के पास चुनार बलुआ पत्थर से तराशा गया है और इस पर 3री शताब्दी ईसा पूर्व की विशिष्ट 'मौर्यकालीन पॉलिश' की गई है।",
                    keywords = listOf("stone", "sandstone", "shine", "polish", "material", "diamond", "throne", "पत्थर", "पॉलिश"),
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-unesco-1056",
                    sourceTitle = UNESCO1056,
                    reviewedAt = R12,
                ),
            ),
        ),

        // 4. Animesh Lochan Chaitya
        PlaceInsightProfile(
            placeId = "in-bihar-bodhgaya-animesh-lochan",
            quickTakeawayEn = "Brick shrine on the northern rise of the Mahabodhi terrace, traditionally commemorating the second week after Enlightenment ('Unblinking Gaze').",
            quickTakeawayHi = "महाबोधि परिसर के उत्तरी भाग में स्थित ईंट का चैत्य, जो परंपरा के अनुसार बोधि प्राप्ति के बाद के दूसरे सप्ताह ('अनिमेष लोचन') से जुड़ा है।",
            travellerNarrativeEn = "'Animesh Lochan' translates to 'unblinking eyes.' According to the traditional seven-weeks post-enlightenment narrative, the Buddha stood on this slight rise northeast of the Bodhi Tree and gazed in silent gratitude at the tree for seven days without blinking. The brick spire mirrors the main Mahabodhi tower on a smaller scale.",
            travellerNarrativeHi = "'अनिमेष लोचन' का अर्थ है बिना पलक झपकाए देखना। बौद्ध परंपरा के अनुसार, बुद्ध ने बोधि प्राप्ति के बाद दूसरे सप्ताह यहीं खड़े होकर बोधि वृक्ष के प्रति कृतज्ञता व्यक्त की थी।",
            scholarContextEn = "The narrative linkage belongs to canonical/commentarial pilgrimage tradition (Jataka Nidanakatha and Xuanzang's Si-Yu-Ki), while the standing brick superstructure reflects post-Gupta/modern restoration fabric.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Direct Sightline to the Bodhi Tree",
                    whereToLook = "From the shrine terrace looking southwest toward the main temple",
                    explanation = "Notice how the elevation and orientation align toward the Bodhi Tree enclave.",
                    claimType = ClaimType.TRADITION,
                    sourceId = "src-unesco-1056",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("7th c. CE", "Xuanzang records a vihara marking the spot of the Buddha's seven-day gaze north of the Bodhi Tree.", ClaimType.TRADITION, "src-unesco-1056"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-animesh-1",
                    placeId = "in-bihar-bodhgaya-animesh-lochan",
                    questionEn = "What does 'Animesh Lochan' mean?",
                    questionHi = "'अनिमेष लोचन' का क्या अर्थ है?",
                    answerEn = "It means 'unblinking gaze'—referring to the Buddhist tradition that the Buddha spent the second week after Awakening gazing steadily at the Bodhi Tree in gratitude.",
                    answerHi = "इसका अर्थ है 'बिना पलक झपकाए देखना'—जो बोधि वृक्ष के प्रति बुद्ध की सात दिनों की शांत कृतज्ञता की परंपरा से जुड़ा है।",
                    keywords = listOf("meaning", "animesh", "lochan", "unblinking", "gaze", "second week", "अर्थ"),
                    claimType = ClaimType.TRADITION,
                    sourceId = "src-unesco-1056",
                    sourceTitle = UNESCO1056,
                    reviewedAt = R12,
                ),
            ),
        ),

        // 5. Mucalinda Sarovar
        PlaceInsightProfile(
            placeId = "in-bihar-bodhgaya-mucalinda",
            quickTakeawayEn = "Sacred lotus tank south of the main shrine, associated in Buddhist tradition with the sixth week after Awakening when the Naga king Mucalinda sheltered the meditating Buddha.",
            quickTakeawayHi = "मुख्य मंदिर के दक्षिण में स्थित पवित्र सरोवर, जहाँ परंपरा के अनुसार छठे सप्ताह में नागराज मुचलिंद ने ध्यानस्थ बुद्ध की तूफान से रक्षा की थी।",
            travellerNarrativeEn = "Walk to the southern garden of the complex to find this tranquil square water tank. In Buddhist tradition, during the sixth week of meditation, a fierce unseasonal rainstorm broke out, and the serpent-king Mucalinda rose from the earth to coil seven times around the Buddha and spread his hood overhead as a shelter.",
            travellerNarrativeHi = "परिसर के दक्षिणी भाग में स्थित यह शांत सरोवर छठे सप्ताह की उस कथा को जीवंत करता है जब भयंकर वर्षा के दौरान नागराज मुचलिंद ने अपने फण से ध्यानस्थ बुद्ध को आश्रय दिया था।",
            scholarContextEn = "Recorded in the Vinaya Pitaka (Mahavagga) and visited by Chinese pilgrims; the present masonry ghats and central sculpture are modern landscaped elements over the traditional tank basin.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Central Naga-Sheltered Buddha Sculpture",
                    whereToLook = "Center of the lotus tank",
                    explanation = "Modern sculptural installation depicting the multi-hooded Naga canopy above the Buddha in dhyana mudra.",
                    claimType = ClaimType.TRADITION,
                    sourceId = "src-unesco-1056",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("Early Canon", "Mucalinda episode recorded in the Udana and Vinaya Mahavagga.", ClaimType.TRADITION, "src-unesco-1056"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-mucalinda-1",
                    placeId = "in-bihar-bodhgaya-mucalinda",
                    questionEn = "What is the story of the serpent over the Buddha at Mucalinda Pond?",
                    questionHi = "मुचलिंद सरोवर में बुद्ध के ऊपर सर्प फण की क्या कहानी है?",
                    answerEn = "According to Buddhist tradition, during a seven-day rainstorm in the sixth week after Enlightenment, the Naga king Mucalinda sheltered the meditating Buddha from wind and rain beneath his multi-headed hood.",
                    answerHi = "बौद्ध परंपरा के अनुसार, बोधि प्राप्ति के छठे सप्ताह में सात दिनों की मूसलाधार वर्षा से नागराज मुचलिंद ने अपने फण की छाया में बुद्ध की रक्षा की थी।",
                    keywords = listOf("snake", "serpent", "naga", "storm", "rain", "pond", "lotus", "नाग", "सरोवर"),
                    claimType = ClaimType.TRADITION,
                    sourceId = "src-unesco-1056",
                    sourceTitle = UNESCO1056,
                    reviewedAt = R12,
                ),
            ),
        ),

        // 6. Great Buddha Statue
        PlaceInsightProfile(
            placeId = "in-bihar-bodhgaya-great-buddha",
            quickTakeawayEn = "Monumental 24.3-meter (80-foot) seated statue of the Buddha in Dhyana Mudra, consecrated in 1989 and constructed from pink Chunar sandstone and red granite blocks.",
            quickTakeawayHi = "ध्यान मुद्रा में भगवान बुद्ध की 80 फीट (24.3 मीटर) ऊँची भव्य प्रतिमा, जिसका निर्माण लाल ग्रेनाइट और चुनार बलुआ पत्थर से 1989 में हुआ।",
            travellerNarrativeEn = "Unlike the ancient Mahabodhi complex, photography is permitted in the open garden around the Great Buddha Statue. Built between 1982 and 1989 with the involvement of the Daijokyo Buddhist sect of Japan and consecrated by the 14th Dalai Lama, the 80-foot sculpture is flanked by ten smaller statues of the Buddha's principal disciples.",
            travellerNarrativeHi = "महाबोधि के विपरीत, इस खुले उद्यान में फोटोग्राफी की अनुमति है। 1982 से 1989 के बीच निर्मित इस 80 फीट ऊँची प्रतिमा के दोनों ओर बुद्ध के दस प्रमुख शिष्यों की मूर्तियाँ स्थापित हैं।",
            scholarContextEn = "A modern monumental work (consecrated 18 November 1989) blending Indian stone masonry (12,000 dressed sandstone and granite blocks) with East Asian Daibutsu spatial axial planning.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Alternating Sandstone & Red Granite Courses",
                    whereToLook = "Lotus pedestal and main torso masonry",
                    explanation = "Notice how pink Chunar sandstone and deep red granite blocks are interlocked across the 60-foot statue body resting on a 20-foot lotus base.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-wikidata-scaffold",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Ten Principal Disciples (Mahasravakas)",
                    whereToLook = "Five standing bronze/stone figures on either side of the central plinth",
                    explanation = "Includes Sariputta, Moggallana, Ananda, Mahakassapa, and Upali framing the ceremonial approach.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-wikidata-scaffold",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("1982–1989 CE", "Constructed over seven years by 12,000+ masons; consecrated on 18 November 1989.", ClaimType.DOCUMENTED, "src-wikidata-scaffold"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-greatbuddha-1",
                    placeId = "in-bihar-bodhgaya-great-buddha",
                    questionEn = "Is the Great Buddha statue an ancient monument or modern?",
                    questionHi = "क्या महान बुद्ध प्रतिमा प्राचीन स्मारक है या आधुनिक?",
                    answerEn = "It is a modern monument consecrated in 1989, standing 80 feet (24.3 m) tall and built from sandstone and red granite blocks. Camera scanning and photography are permitted in the outdoor park.",
                    answerHi = "यह 1989 में प्रतिष्ठित एक आधुनिक स्मारक है, जिसकी ऊँचाई 80 फीट है। यहाँ खुले उद्यान में फोटोग्राफी की अनुमति है।",
                    keywords = listOf("ancient", "modern", "height", "tall", "1989", "camera", "photo", "ऊँचाई", "प्राचीन"),
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-wikidata-scaffold",
                    sourceTitle = "Wikidata / Monument Record",
                    reviewedAt = R12,
                ),
            ),
        ),

        // 7. Griddhakuta (Vulture's Peak)
        PlaceInsightProfile(
            placeId = "in-bihar-rajgir-vultures-peak",
            quickTakeawayEn = "Natural rocky crag in the Rajgir hills revered in Buddhist tradition as a primary retreat of the Buddha and setting of the Heart Sutra and Lotus Sutra discourses.",
            quickTakeawayHi = "राजगीर की पहाड़ियों में स्थित प्राकृतिक शिला-शिखर, जो बौद्ध परंपरा में बुद्ध के प्रमुख वर्षावास और प्रज्ञापारमिता एवं सद्धर्मपुण्डरीक सूत्र के उपदेश स्थल के रूप में पूजनीय है।",
            travellerNarrativeEn = "As you climb the stone-paved causeway known as the 'Bimbisara Road,' you are walking a route described by Chinese pilgrims Faxian (5th c. CE) and Xuanzang (7th c. CE). Named both for the vulture-like silhouette of its weathered quartzite crags and the birds that roosted here, Griddhakuta offers a sweeping view over the fortified valley of ancient Rajagriha.",
            travellerNarrativeHi = "बिम्बिसार मार्ग की पत्थर की सीढ़ियों से ऊपर चढ़ते हुए आप उसी ऐतिहासिक पथ पर चलते हैं जिसका वर्णन फाह्यान और ह्वेनसांग ने किया था। शिखर से प्राचीन राजगृह घाटी का विहंगम दृश्य दिखाई देता है।",
            scholarContextEn = "Marshall and Cunningham identified the stone causeway ascending Chhatha Hill with the royal road attributed to King Bimbisara in Xuanzang's account; brick foundation platforms at the summit represent late monastic shrines.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Bimbisara's Stone Causeway & Two Small Stupas",
                    whereToLook = "Along the paved hill path ascending toward the summit",
                    explanation = "Look for two stone/brick stupa bases along the climb: tradition links the first ('Dismounting from the Chariot') and second ('Sending Back the Crowd') to King Bimbisara's visit.",
                    claimType = ClaimType.TRADITION,
                    sourceId = "src-wikidata-scaffold",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Natural Rock Cavern Shelters (Ananda & Sariputta Caves)",
                    whereToLook = "Just below the final stairway to the summit platform",
                    explanation = "Weathered rock overhangs where monks traditionally meditated and where pilgrims place gold leaf and incense.",
                    claimType = ClaimType.TRADITION,
                    sourceId = "src-wikidata-scaffold",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("5th c. BCE", "Traditional era of the Buddha's retreats at Rajagriha during King Bimbisara's reign.", ClaimType.TRADITION, "src-wikidata-scaffold"),
                TimelineMilestone("c. 400 & 637 CE", "Faxian and Xuanzang climb Griddhakuta and describe its brick vihara and rock overhangs.", ClaimType.DOCUMENTED, "src-wikidata-scaffold"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-vulture-1",
                    placeId = "in-bihar-rajgir-vultures-peak",
                    questionEn = "Why is Griddhakuta called Vulture's Peak and what discourses are linked to it?",
                    questionHi = "गृध्रकूट को गिद्धकूट क्यों कहा जाता है और यहाँ कौन से उपदेश दिए गए थे?",
                    answerEn = "In Pali (Gijjhakuta) and Sanskrit (Griddhakuta), the hill is named after its vulture-beak rock formation and the vultures that inhabited the crags. Buddhist tradition associates it with major discourses including the Lotus Sutra and Heart Sutra.",
                    answerHi = "गिद्ध की चोंच जैसी चट्टानी आकृति और गिद्धों के निवास के कारण इसे गृध्रकूट कहा गया। महायान परंपरा इसे प्रज्ञापारमिता और सद्धर्मपुण्डरीक सूत्र से जोड़ती है।",
                    keywords = listOf("vulture", "name", "sutra", "lotus", "heart", "climb", "hill", "bimbisara", "गृध्रकूट", "उपदेश"),
                    claimType = ClaimType.TRADITION,
                    sourceId = "src-wikidata-scaffold",
                    sourceTitle = "Wikidata / Pilgrimage Record",
                    reviewedAt = R12,
                ),
            ),
        ),

        // 8. Venu Vana
        PlaceInsightProfile(
            placeId = "in-bihar-rajgir-venu-vana",
            quickTakeawayEn = "Tranquil bamboo grove park in Rajgir, identified in Buddhist tradition as Veluvana Kalandakanivapa—the first monastic residence (arama) gifted to the Buddhist Sangha by King Bimbisara.",
            quickTakeawayHi = "राजगीर का शांत बांस वन उद्यान, जिसे बौद्ध परंपरा में राजा बिम्बिसार द्वारा संघ को दान किए गए प्रथम विहार 'वेणुवन कलन्दकनिवाप' के रूप में पहचाना जाता है।",
            travellerNarrativeEn = "Walking among the bamboo clusters and the central Karanda Tank, you are visiting the traditional site of the very first permanent monsoon retreat gifted to the Buddha and his monastic community. Before Venu Vana, wandering ascetics had no dedicated park enclosure; Bimbisara chose this spot because it was 'neither too near nor too far from the town, quiet by night and free from crowds.'",
            travellerNarrativeHi = "बांस के झुरमुटों और करंद सरोवर के बीच स्थित यह उद्यान बौद्ध संघ को दान किए गए प्रथम स्थायी निवास (आराम) का पारंपरिक स्थल है।",
            scholarContextEn = "Identified by Cunningham and Marshall north of the outer Rajagriha gate based on directional bearings in Faxian and Xuanzang; surrounding mounds yielded medieval Pala-era sculpture fragments.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Karanda Pushkarini (Central Water Tank)",
                    whereToLook = "Center of the landscaped bamboo garden",
                    explanation = "Traditional bathing pond associated with Kalandakanivapa ('the feeding ground of squirrels').",
                    claimType = ClaimType.TRADITION,
                    sourceId = "src-wikidata-scaffold",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("5th c. BCE", "Traditional donation of Veluvana bamboo grove by King Bimbisara of Magadha.", ClaimType.TRADITION, "src-wikidata-scaffold"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-venuvana-1",
                    placeId = "in-bihar-rajgir-venu-vana",
                    questionEn = "Why was Venu Vana important in early Buddhist history?",
                    questionHi = "प्रारंभिक बौद्ध इतिहास में वेणुवन क्यों महत्वपूर्ण था?",
                    answerEn = "According to the Vinaya Pitaka, Venu Vana (Veluvana) was the first land grant (arama) accepted by the Buddha for the monastic community, donated by King Bimbisara of Magadha.",
                    answerHi = "विनय पिटक के अनुसार, वेणुवन मगध नरेश बिम्बिसार द्वारा बौद्ध संघ को भेंट किया गया प्रथम विहार (आराम) था।",
                    keywords = listOf("first", "monastery", "bamboo", "grove", "bimbisara", "gift", "वेणुवन", "बांस"),
                    claimType = ClaimType.TRADITION,
                    sourceId = "src-wikidata-scaffold",
                    sourceTitle = "Wikidata / Pilgrimage Record",
                    reviewedAt = R12,
                ),
            ),
        ),

        // 9. Cyclopean Wall (Rajgir)
        PlaceInsightProfile(
            placeId = "in-bihar-rajgir-cyclopean-wall",
            quickTakeawayEn = "Monumental ~40 km ring of dry-stone fortifications crowning the hills around the Rajgir valley, constructed from massive undressed quartzite boulders without mortar.",
            quickTakeawayHi = "राजगीर घाटी की पहाड़ियों के शिखर पर बिना गारे के विशाल अनगढ़ पत्थरों से निर्मित लगभग 40 किमी लंबी प्राचीन किलेबंदी।",
            travellerNarrativeEn = "Look closely at how these massive quartzite boulders fit together: there is zero lime or mud mortar binding them. Instead, ancient Magadhan engineers wedged smaller chink-stones into the gaps between multi-ton polygonal blocks so gravity and friction lock the rampart in place across the mountain ridges—making it one of the oldest surviving stone fortifications in South Asia.",
            travellerNarrativeHi = "इन विशाल पत्थरों की जुड़ाई को ध्यान से देखें: इनमें किसी चूने या गारे का प्रयोग नहीं हुआ है। बड़े अनगढ़ पत्थरों के बीच छोटे पत्थरों को फँसाकर गुरुत्वाकर्षण से यह दीवार खड़ी की गई है।",
            scholarContextEn = "Surveyed by Sir John Marshall (1905–06 ASI Report): the walls reach thicknesses of 14 to 17.5 feet (4.2–5.3 m) with rectangular bastions and watchtower foundations guarding the passes into Old Rajagriha.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Dry-Stone Interlocking & Chink Wedges",
                    whereToLook = "Exposed cross-section along the southern pass rampart",
                    explanation = "Notice how massive outer facings are filled with a compact core of rubble and locked with small triangular wedge stones—no mortar is used anywhere.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-wikidata-scaffold",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Rectangular Bastion Foundations",
                    whereToLook = "Projecting stone platforms along the outer face of the wall",
                    explanation = "Built at strategic intervals along the ridge to reinforce the curtain wall and overlook valley approaches.",
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-wikidata-scaffold",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("Mid-1st Millennium BCE", "Traditional & early historic fortification of Girivraja / Old Rajagriha, early capital of Magadha.", ClaimType.INTERPRETATION, "src-wikidata-scaffold"),
                TimelineMilestone("1905–1906 CE", "Comprehensive photographic and planimetric survey by Sir John Marshall (ASI).", ClaimType.DOCUMENTED, "src-wikidata-scaffold"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-cyclopean-1",
                    placeId = "in-bihar-rajgir-cyclopean-wall",
                    questionEn = "How does the Cyclopean Wall stay standing without cement or mortar?",
                    questionHi = "साइक्लोपियन दीवार बिना सीमेंट या गारे के कैसे टिकी हुई है?",
                    answerEn = "It uses cyclopean dry-stone masonry: massive 1-to-2-ton undressed quartzite boulders form the outer faces, a rubble core fills the 14–17 foot width, and small wedge stones lock the joints by gravity and friction.",
                    answerHi = "इसमें विशाल अनगढ़ क्वार्टजाइट पत्थरों को बाहरी सतहों पर रखकर बीच में पत्थर भरे गए हैं और जोड़ों को छोटे पत्थरों से बिना गारे के लॉक किया गया है।",
                    keywords = listOf("mortar", "cement", "built", "wall", "stone", "length", "cyclopean", "दीवार", "पत्थर"),
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-wikidata-scaffold",
                    sourceTitle = ASI_MARSHALL,
                    reviewedAt = R12,
                ),
            ),
        ),

        // 10. Vishwa Shanti Stupa
        PlaceInsightProfile(
            placeId = "in-bihar-rajgir-shanti-stupa",
            quickTakeawayEn = "Gleaming white 1969 marble-clad Peace Pagoda crowning Ratnagiri Hill (400 m elevation), featuring four gilded statues representing the four life stages of the Buddha.",
            quickTakeawayHi = "रत्नागिरी पहाड़ी (400 मीटर ऊँचाई) के शिखर पर 1969 में निर्मित श्वेत विश्व शांति स्तूप, जिसके चारों दिशाओं में बुद्ध के जीवन के चार चरणों की स्वर्णिम प्रतिमाएँ हैं।",
            travellerNarrativeEn = "Constructed in 1969 by the Nipponzan-Myohoji Buddhist order founded by Nichidatsu Fujii, this modern hilltop stupa overlooks Griddhakuta Peak and the entire Rajgir ring of hills. As you walk clockwise around the upper terrace, each cardinal niche shows a pivotal moment of the Buddha's life: Birth, Enlightenment, First Sermon, and Parinirvana.",
            travellerNarrativeHi = "1969 में निचिदात्सु फुजीई के निप्पोनज़ान-म्योहोजी संघ द्वारा निर्मित इस स्तूप की परिक्रमा करते समय चारों दिशाओं में बुद्ध के जन्म, संबोधि, धर्मचक्रप्रवर्तन और महापरिनिर्वाण की स्वर्ण प्रतिमाएँ दिखाई देती हैं।",
            scholarContextEn = "A modern commemorative Peace Pagoda (completed 1969) situated on Ratnagiri Hill above the historic Gridhrakuta spur; check ropeway operating hours on site as schedules vary seasonally.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Four Cardinal Gilded Buddha Niches",
                    whereToLook = "North, East, South, and West niches of the main dome (anda)",
                    explanation = "Look at the hand gestures (mudras) and postures representing Lumbini (Birth), Bodh Gaya (Awakening), Sarnath (Teaching), and Kushinagar (Parinirvana).",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-wikidata-scaffold",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("1969 CE", "Inaugurated on Ratnagiri Hill by Nipponzan-Myohoji as a monument to world peace.", ClaimType.DOCUMENTED, "src-wikidata-scaffold"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-shanti-1",
                    placeId = "in-bihar-rajgir-shanti-stupa",
                    questionEn = "What do the four golden statues around Vishwa Shanti Stupa represent?",
                    questionHi = "विश्व शांति स्तूप के चारों ओर बनी चार स्वर्ण प्रतिमाएँ क्या दर्शाती हैं?",
                    answerEn = "They represent the four principal milestones of the Buddha's life: Birth, Enlightenment, First Teaching (Dharmachakra), and Parinirvana.",
                    answerHi = "ये भगवान बुद्ध के जीवन की चार प्रमुख घटनाओं—जन्म, संबोधि, प्रथम उपदेश और महापरिनिर्वाण—को दर्शाती हैं।",
                    keywords = listOf("four", "golden", "statues", "shanti", "stupa", "peace", "pagoda", "प्रतिमा", "शांति"),
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-wikidata-scaffold",
                    sourceTitle = "Wikidata / Monument Record",
                    reviewedAt = R12,
                ),
            ),
        ),

        // 11. Sonbhandar Cave
        PlaceInsightProfile(
            placeId = "in-bihar-rajgir-sonbhandar",
            quickTakeawayEn = "Two rock-cut caves carved into the southern cliff of Vaibhara Hill (3rd–4th c. CE inscriptional evidence, with earlier Mauryan/Jain architectural parallels and contested folklore).",
            quickTakeawayHi = "वैभारगिरि पहाड़ी की दक्षिणी चट्टान में तराशी गई दो गुफाएँ (3री-4थी शताब्दी के अभिलेखीय साक्ष्य, जैन मुनि वैरदेव का शिलालेख और लोककथाएँ)।",
            travellerNarrativeEn = "Local folklore calls Sonbhandar the 'Storehouse of Gold' of King Bimbisara and claims a carved pattern on the wall is a secret password to open a hidden stone doorway. Archaeological and epigraphic evidence tells a verified story: a Sanskrit inscription outside the western cave records that the ascetic Muni Vairadeva excavated these two 'auspicious caves worthy of ascetics' and installed Jain Tirthankara images here around the 3rd–4th centuries CE.",
            travellerNarrativeHi = "लोककथाओं में इसे राजा बिम्बिसार का 'स्वर्ण भंडार' कहा जाता है, किंतु पुरातात्विक साक्ष्य भिन्न हैं: बाहरी दीवार के संस्कृत शिलालेख के अनुसार मुनि वैरदेव ने 3री-4थी शताब्दी ईस्वी में तपस्वियों के लिए इन गुफाओं का निर्माण कराया था।",
            scholarContextEn = "Notice how TrueWay separates TRADITION/CONTESTED folklore from DOCUMENTED epigraphy: Vairadeva's Gupta-character Sanskrit inscription explicitly documents Jain cave dedication, while shankhalipi (shell-script) glyphs on the wall remain undeciphered scholarly subjects, not a verified treasure cipher.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Sloping Jamb Doorway & Barrel-Vaulted Interior",
                    whereToLook = "Entrance and ceiling of the western rock-cut chamber",
                    explanation = "Notice the inward-sloping door jambs and vaulted roof—an architectural hallmark continuing the rock-cut tradition of the Barabar Hills.",
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-wikidata-scaffold",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Shankhalipi (Shell-Script) & Vairadeva Inscriptions",
                    whereToLook = "Outer rock wall beside the entrance and inner southern wall",
                    explanation = "Look for ornate swirling shell-like characters (Shankhalipi) alongside the Gupta-era Sanskrit inscription of Muni Vairadeva.",
                    claimType = ClaimType.CONTESTED,
                    sourceId = "src-wikidata-scaffold",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("3rd–4th c. CE", "Sanskrit inscription of Muni Vairadeva records cave excavation and Jain Tirthankara installation.", ClaimType.INTERPRETATION, "src-wikidata-scaffold"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-sonbhandar-1",
                    placeId = "in-bihar-rajgir-sonbhandar",
                    questionEn = "Is there really hidden gold treasure behind a secret door in Sonbhandar Cave?",
                    questionHi = "क्या सोनभंडार गुफा में गुप्त दरवाजे के पीछे वास्तव में बिम्बिसार का खजाना छिपा है?",
                    answerEn = "[CONTESTED / TRADITION] The hidden-treasure story of King Bimbisara is popular folklore, not an archaeologically verified fact. Epigraphic evidence on the cave wall (Muni Vairadeva's 3rd–4th c. CE Sanskrit inscription) documents the chambers as rock-cut ascetic caves.",
                    answerHi = "[विवादित / लोकपरंपरा] गुप्त खजाने की कहानी लोककथा है, पुरातात्विक तथ्य नहीं। गुफा के बाहर मुनि वैरदेव का संस्कृत शिलालेख इसे जैन तपस्वियों की गुफा के रूप में दर्ज करता है।",
                    keywords = listOf("gold", "treasure", "door", "secret", "bimbisara", "inscription", "jain", "खजाना", "सोना", "गुफा"),
                    claimType = ClaimType.CONTESTED,
                    sourceId = "src-wikidata-scaffold",
                    sourceTitle = "Wikidata / ASI Epigraphic Record",
                    reviewedAt = R12,
                ),
            ),
        ),

        // 12. Nalanda Mahavihara
        PlaceInsightProfile(
            placeId = "in-bihar-nalanda-mahavihara",
            quickTakeawayEn = "UNESCO World Heritage archaeological complex spanning 23 hectares; an organized residential monastic university active continuously from the 5th to late 12th/13th centuries CE.",
            quickTakeawayHi = "23 हेक्टेयर में फैला यूनेस्को विश्व धरोहर पुरातात्विक परिसर; 5वीं से 12वीं/13वीं शताब्दी ईस्वी तक निरंतर सक्रिय रहा आवासीय महाविहार विश्वविद्यालय।",
            travellerNarrativeEn = "Stand on the central lawn looking between the eastern row of brick monasteries (viharas) and the western row of temples (chaityas). For over 750 years, scholars from China, Korea, Tibet, Central Asia, and Sri Lanka traveled here to study Buddhist philosophy, logic (hetuvidya), grammar, medicine, and astronomy. What you see excavated today is roughly 10–15% of the ancient campus footprint.",
            travellerNarrativeHi = "पूर्वी छोर के विहारों (छात्रावास) और पश्चिमी छोर के चैत्यों (मंदिरों) के मध्य खड़े होकर देखें: 750 से अधिक वर्षों तक चीन, कोरिया, तिब्बत और श्रीलंका के विद्वान यहाँ तर्कशास्त्र, दर्शन, व्याकरण और आयुर्वेद का अध्ययन करने आते थे।",
            scholarContextEn = "Founded under Gupta royal patronage (Kumaragupta I / Sakraditya in Xuanzang's account), expanded by Harshavardhana of Kanauj and the Pala dynasty (Dharmapala, Devapala), and systematically excavated by the ASI starting with D.B. Spooner in 1915.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "North–South Dual-Axis Campus Masterplan",
                    whereToLook = "Central grassy avenue dividing the complex",
                    explanation = "All 11 excavated residential monasteries (Viharas) align along the eastern flank facing west toward the row of monumental temples (Temples 3, 12, 13, 14).",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-unesco-1502",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Superimposed Brick Stratigraphy",
                    whereToLook = "Exposed multi-level brick walls in the quadrangles",
                    explanation = "Notice how later Pala-era brick walls sit directly atop earlier Gupta-era foundations—sometimes up to nine successive rebuilding phases on the same footprint.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-unesco-1502",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("5th c. CE", "Imperial Gupta clay seals and royal endowments establish the organized Mahavihara.", ClaimType.DOCUMENTED, "src-unesco-1502"),
                TimelineMilestone("637–642 CE", "Chinese pilgrim-scholar Xuanzang resides and studies at Nalanda under Abbot Silabhadra.", ClaimType.DOCUMENTED, "src-unesco-1502"),
                TimelineMilestone("8th–12th c. CE", "Golden age of Pala dynasty patronage, bronze casting, and international manuscript copying.", ClaimType.DOCUMENTED, "src-unesco-1502"),
                TimelineMilestone("1915–1937 CE", "Systematic ASI excavations uncover 11 monasteries and 6 brick temples.", ClaimType.DOCUMENTED, "src-unesco-1502"),
                TimelineMilestone("2016 CE", "Inscribed as a UNESCO World Heritage Site (Ref. 1502).", ClaimType.DOCUMENTED, "src-unesco-1502"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-nalanda-1",
                    placeId = "in-bihar-nalanda-mahavihara",
                    questionEn = "Why are the buildings at Nalanda numbered (like Temple 3 or Monastery 1) instead of named?",
                    questionHi = "नालंदा की इमारतों को प्राचीन नामों के बजाय 'मंदिर 3' या 'विहार 1' जैसे नंबर क्यों दिए गए हैं?",
                    answerEn = "Building numbers (Monastery 1–11, Temple 3, 12, 13, 14) are modern archaeological survey labels assigned by the ASI during 20th-century excavations to map structures systematically without guessing unverified ancient building names.",
                    answerHi = "विहार 1-11 और मंदिर 3 जैसे क्रमांक 20वीं सदी की खुदाई के दौरान भारतीय पुरातत्व सर्वेक्षण (ASI) द्वारा दिए गए सर्वेक्षण नाम हैं।",
                    keywords = listOf("number", "named", "temple 3", "monastery 1", "label", "why", "university", "नंबर", "नालंदा"),
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-unesco-1502",
                    sourceTitle = UNESCO1502,
                    reviewedAt = R12,
                ),
            ),
        ),

        // 13. Nalanda Temple 3
        PlaceInsightProfile(
            placeId = "in-bihar-nalanda-temple-03",
            quickTakeawayEn = "Tallest standing monument at Nalanda (~31 meters high), evolved through seven successive construction stages from a small 6th-century brick stupa into a grand terraced shrine.",
            quickTakeawayHi = "नालंदा का सबसे ऊँचा स्मारक (~31 मीटर), जो एक छोटे स्तूप के ऊपर सात क्रमिक निर्माण चरणों में विकसित हुआ।",
            travellerNarrativeEn = "Standing at the southern end of the campus, Temple 3 (Sariputta Stupa) is the visual icon of Nalanda. Archaeologists discovered that builders never demolished the older shrine—instead, they encased each earlier stupa inside a larger brick shell seven times in a row. On the fifth-stage outer wall, you can still see extraordinary 6th-century Gupta stucco sculptures of the Buddha and Bodhisattvas.",
            travellerNarrativeHi = "परिसर के दक्षिणी छोर पर खड़ा मंदिर संख्या 3 नालंदा का सबसे भव्य स्मारक है। प्राचीन वास्तुकारों ने पुराने स्तूप को तोड़े बिना उसके ऊपर सात बार नया आवरण चढ़ाया। इसके पाँचवें स्तर पर गुप्तकालीन स्टुको मूर्तियाँ आज भी सुरक्षित हैं।",
            scholarContextEn = "Spooner and Page exposed seven distinct structural envelopes; the fifth integument preserves fine 6th-century CE Gupta lime-stucco figures inside pilastered chaitya niches, flanked by four corner towers and fleets of votive stupas containing inscribed clay dharma-relic sealings.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "5th-Stage Gupta Stucco Sculptures",
                    whereToLook = "Protected recessed niches on the eastern/northern corner tower",
                    explanation = "Look for the delicate white lime-stucco figures of Avalokitesvara, Tara, and the Buddha preaching in Dharmachakra mudra—surviving intact from the 6th century CE because a later brick wall sealed and protected them.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-unesco-1502",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Votive Brick Stupa Field",
                    whereToLook = "Courtyard base surrounding the main staircase",
                    explanation = "Dozens of smaller solid brick votive stupas dedicated by visiting pilgrims and scholars across seven centuries.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-unesco-1502",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("6th c. CE", "Fifth construction stage adorned with classic Gupta stucco figures.", ClaimType.DOCUMENTED, "src-unesco-1502"),
                TimelineMilestone("1915–1925 CE", "Excavated and consolidated by Dr. D.B. Spooner and J.A. Page (ASI).", ClaimType.DOCUMENTED, "src-unesco-1502"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-temple3-1",
                    placeId = "in-bihar-nalanda-temple-03",
                    questionEn = "How can I distinguish Nalanda Temple 3 from Monastery 1?",
                    questionHi = "नालंदा के मंदिर 3 और विहार 1 में क्या अंतर है?",
                    answerEn = "Temple 3 is a solid, high-rising stepped pyramid (stupa/chaitya) surrounded by small votive stupas on the southern edge. Monastery 1 is an enclosed rectangular residential quadrangle with a sunken courtyard, central well, and monk dorm cells around the perimeter.",
                    answerHi = "मंदिर 3 एक ऊँचा सीढ़ीदार स्तूप है जिसके चारों ओर छोटे मन्नत स्तूप हैं, जबकि विहार 1 आँगन, कुएँ और भिक्षु कक्षों वाला आयताकार छात्रावास परिसर है।",
                    keywords = listOf("difference", "distinguish", "monastery", "stupa", "stucco", "stages", "seven", "अंतर", "स्तूप"),
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-unesco-1502",
                    sourceTitle = UNESCO1502,
                    reviewedAt = R12,
                ),
            ),
        ),

        // 14. Nalanda Monastery 1
        PlaceInsightProfile(
            placeId = "in-bihar-nalanda-monastery-01",
            quickTakeawayEn = "Principal residential quadrangle (vihara) of Nalanda, featuring nine superimposed construction levels, monk dormitory cells, an octagonal well, and a central teaching platform.",
            quickTakeawayHi = "नालंदा का सबसे प्रमुख आवासीय चतुष्कोणीय विहार, जिसमें नौ निर्माण स्तर, भिक्षु कक्ष, अष्टकोणीय कुआँ और व्याख्यान मंच मौजूद हैं।",
            travellerNarrativeEn = "Walk through the massive western portico into the open quadrangle of Monastery 1. Imagine 300 student-monks living around this courtyard: each small doorway leads into a private brick study cell with a recessed niche in the thick wall to hold an oil lamp and palm-leaf manuscripts. In the courtyard sit the raised stone-and-brick lecture pulpit, cooking hearths, and the deep brick well.",
            travellerNarrativeHi = "पश्चिमी प्रवेश द्वार से भीतर आँगन में प्रवेश करें। चारों ओर बने छोटे कक्षों को देखें: प्रत्येक कक्ष की मोटी दीवार में दीपक और ताड़पत्र की पांडुलिपियाँ रखने के लिए आला (आला/ताक) बना है।",
            scholarContextEn = "Yielded the copper-plate inscription of King Devapala (9th c. CE) recording the endowment of five villages for the upkeep of a monastery built at Nalanda by Maharaja Balaputradeva of Suvarnadvipa (Sumatra/Srivijaya).",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Monk Cell Lamp & Manuscript Niches",
                    whereToLook = "Inside the perimeter brick rooms surrounding the courtyard",
                    explanation = "Step to the doorway of any residential cell and look for the square recessed niche built into the 2-meter-thick brick wall—used for oil lamps and texts.",
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-unesco-1502",
                ),
                ArchitecturalSpotterItem(
                    featureTitle = "Corbelled Brick Arch & Covered Drain",
                    whereToLook = "Northeastern corner and vaulted chambers of the quadrangle",
                    explanation = "Look at the corbelled brick vaulting and the brick-lined rainwater drainage channel that carried courtyard runoff outward.",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-unesco-1502",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("9th c. CE", "Devapala copper plate documents international patronage from Balaputradeva of Suvarnadvipa (Sumatra).", ClaimType.DOCUMENTED, "src-unesco-1502"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-monastery1-1",
                    placeId = "in-bihar-nalanda-monastery-01",
                    questionEn = "How did students and monks live inside Monastery 1?",
                    questionHi = "विहार 1 के अंदर छात्र और भिक्षु कैसे रहते थे?",
                    answerEn = "Monks lived in individual perimeter brick cells arranged around a colonnaded veranda and open courtyard. Each cell had a thick insulating brick wall with niches for oil lamps and books, while the courtyard provided a water well, drainage, and a central teaching podium.",
                    answerHi = "भिक्षु आँगन के चारों ओर बने व्यक्तिगत ईंट कक्षों में रहते थे, जहाँ दीपक और पुस्तकों के लिए ताक बने थे तथा आँगन में कुआँ और व्याख्यान मंच था।",
                    keywords = listOf("live", "monks", "students", "cells", "rooms", "well", "drainage", "study", "भिक्षु", "कक्ष"),
                    claimType = ClaimType.INTERPRETATION,
                    sourceId = "src-unesco-1502",
                    sourceTitle = UNESCO1502,
                    reviewedAt = R12,
                ),
            ),
        ),

        // 15. Nalanda Archaeological Museum
        PlaceInsightProfile(
            placeId = "in-bihar-nalanda-museum",
            quickTakeawayEn = "ASI site museum (established 1917) housing over 13,000 excavated artifacts from Nalanda and Rajgir, including the official 'Sri-Nalanda-Mahavihariy-Arya-Bhikshu-Sanghasya' clay seal.",
            quickTakeawayHi = "1917 में स्थापित पुरातात्विक संग्रहालय, जिसमें नालंदा की आधिकारिक भिक्षु-संघ मुद्रा, पालकालीन कांस्य मूर्तियाँ और देवपाल का ताम्रपत्र सुरक्षित हैं।",
            travellerNarrativeEn = "After walking the open brick ruins, the museum opposite the main gate connects the empty niches to their original treasures: Pala-era Kurkihar-style bronzes, black basalt sculptures, charred rice grains from ancient granaries, and the terracotta university seal showing the Wheel of Law flanked by two deer.",
            travellerNarrativeHi = "खुले खंडहरों को देखने के बाद मुख्य द्वार के सामने स्थित यह संग्रहालय नालंदा की वास्तविक कलाकृतियों—पालकालीन कांस्य प्रतिमाओं, काले बेसाल्ट की मूर्तियों और विश्वविद्यालय की आधिकारिक मिट्टी की मुहर—को प्रदर्शित करता है।",
            scholarContextEn = "Houses the primary epigraphic corpus for Nalanda Mahavihara: Gupta royal genealogical clay seals, the 9th-century Devapala copper plate, and stone inscriptions of Yasovarmadeva and Vipulasrimitra.",
            whatToSpotOnSite = listOf(
                ArchitecturalSpotterItem(
                    featureTitle = "Official Monastic Seal of Nalanda",
                    whereToLook = "Gallery 1 — Epigraphy & Seals Showcase",
                    explanation = "Look for the baked clay sealing bearing the Dharmachakra flanked by two seated deer above the Sanskrit legend 'Of the Community of Venerable Monks of the Great Monastery of Glorious Nalanda.'",
                    claimType = ClaimType.DOCUMENTED,
                    sourceId = "src-wikidata-scaffold",
                ),
            ),
            timeline = listOf(
                TimelineMilestone("1917 CE", "Established by the Archaeological Survey of India to preserve finds excavated from Nalanda and Rajgir.", ClaimType.DOCUMENTED, "src-wikidata-scaffold"),
            ),
            faqs = listOf(
                OfflineQaItem(
                    qaId = "qa-museum-1",
                    placeId = "in-bihar-nalanda-museum",
                    questionEn = "Can I use the camera scanner inside the Nalanda Archaeological Museum?",
                    questionHi = "क्या मैं नालंदा संग्रहालय के अंदर कैमरा स्कैनर का उपयोग कर सकता हूँ?",
                    answerEn = "No—Nalanda Museum is designated QR_PARTNER / indoor-regulated. Always obey gallery photography rules and staff instructions; use offline text search and insights cards instead of indoor camera capture.",
                    answerHi = "नहीं, संग्रहालय के भीतर गैलरी के फोटोग्राफी नियमों का पालन करें और कैमरा स्कैन के बजाय ऑफ़लाइन टेक्स्ट कार्ड का उपयोग करें।",
                    keywords = listOf("camera", "photo", "museum", "seal", "bronze", "inside", "संग्रहालय", "फोटो"),
                    claimType = ClaimType.OPERATIONAL,
                    sourceId = "src-wikidata-scaffold",
                    sourceTitle = BIHAR_TOURISM,
                    reviewedAt = R12,
                ),
            ),
        ),
    ).associateBy { it.placeId }

    fun get(placeId: String): PlaceInsightProfile? = profiles[placeId]

    fun all(): List<PlaceInsightProfile> = profiles.values.toList()

    /**
     * Deterministic, citation-grounded offline question matcher (Blueprint v3.0 §2 & §7).
     *
     * Rules:
     * 1. If the query asks for live operational/transactional data (weather, live ticket prices,
     *    hotels, trains), immediately abstain ([QaResolution.Abstained]) with an explicit offline caveat.
     * 2. Score curated FAQs (for [placeId] first, then corpus-wide if needed) using token +
     *    keyword + [IndicPhoneticNormalizer] skeleton matching.
     * 3. Also match against the place's verified [SourcedClaim] entries.
     * 4. If neither FAQs nor claims match with sufficient relevance, abstain cleanly rather than
     *    guessing or fabricating an answer.
     */
    fun askOffline(placeId: String, rawQuery: String): QaResolution {
        val q = rawQuery.trim()
        val place = PlaceRepository.get(placeId)
        val fallbackClaims = place?.claims.orEmpty()

        if (q.isEmpty()) {
            val defaultFaqs = profiles[placeId]?.faqs.orEmpty()
            return QaResolution.Answered(
                query = "",
                matchedFaqs = defaultFaqs,
                relatedClaims = fallbackClaims,
            )
        }

        val qLower = q.lowercase()
        // Rule 1: Reject live / transactional queries that static offline packs cannot verify
        if (LIVE_QUERY_TRIGGERS.any { trigger -> qLower.contains(trigger) }) {
            return QaResolution.Abstained(
                query = q,
                reason = "This question asks about live operational, weather, pricing, or booking data. TrueWay works 100% offline from a static verified pack and never fabricates live conditions. Please verify current hours, tickets, and weather on site.",
                fallbackClaims = fallbackClaims,
            )
        }

        val tokens = qLower
            .split(Regex("[^\\p{L}\\p{N}]+"))
            .filter { it.length >= 3 && it !in STOP_WORDS }
        val qSkeleton = IndicPhoneticNormalizer.toSkeleton(qLower)
        val skeletonTokens = qSkeleton.split(" ").filter { it.length >= 3 }

        val localProfile = profiles[placeId]
        val candidateFaqs = (localProfile?.faqs.orEmpty() + profiles.values.flatMap { it.faqs })
            .distinctBy { it.qaId }

        val scoredFaqs = candidateFaqs.mapNotNull { faq ->
            var score = 0
            if (faq.placeId == placeId) score += 2 // Boost same-place relevance

            val hay = buildString {
                append(faq.questionEn.lowercase()).append(' ')
                append(faq.questionHi.lowercase()).append(' ')
                append(faq.answerEn.lowercase()).append(' ')
                append(faq.answerHi.lowercase()).append(' ')
                faq.keywords.forEach { append(it.lowercase()).append(' ') }
            }
            val haySkeleton = IndicPhoneticNormalizer.toSkeleton(hay)

            var lexicalHits = 0
            for (tok in tokens) {
                if (faq.keywords.any { it.lowercase().contains(tok) }) {
                    score += 5
                    lexicalHits++
                } else if (hay.contains(tok)) {
                    score += 3
                    lexicalHits++
                }
            }
            for (sTok in skeletonTokens) {
                if (haySkeleton.contains(sTok)) {
                    score += 2
                    lexicalHits++
                }
            }
            if (lexicalHits > 0) Pair(faq, score) else null
        }.sortedByDescending { it.second }
            .map { it.first }
            .take(3)

        val matchedClaims = fallbackClaims.filter { claim ->
            val claimLower = (claim.text + " " + claim.sourceTitle + " " + claim.type.name).lowercase()
            val claimSkel = IndicPhoneticNormalizer.toSkeleton(claimLower)
            tokens.any { claimLower.contains(it) } ||
                skeletonTokens.any { claimSkel.contains(it) }
        }

        return if (scoredFaqs.isNotEmpty() || matchedClaims.isNotEmpty()) {
            QaResolution.Answered(
                query = q,
                matchedFaqs = scoredFaqs,
                relatedClaims = if (matchedClaims.isNotEmpty()) matchedClaims else fallbackClaims.take(2),
            )
        } else {
            QaResolution.Abstained(
                query = q,
                reason = "No verified answer for \"$q\" was found in this offline pack. TrueWay abstains rather than guessing unverified history. Showing verified historical claims for this place below.",
                fallbackClaims = fallbackClaims,
            )
        }
    }

    /**
     * P1B Study Lite (F116): Claim-linked knowledge check cards per monument.
     * Dynamically pairs curated epistemic questions with every place's FAQ and timeline corpus.
     */
    fun studyCardFor(placeId: String): StudyLiteCard? {
        val profile = profiles[placeId] ?: return null
        val faq = profile.faqs.firstOrNull() ?: return null
        return when (placeId) {
            "in-bihar-bodhgaya-mahabodhi" -> StudyLiteCard(
                cardId = "study-mahabodhi",
                placeId = placeId,
                promptEn = "How do archaeologists date the standing 55-meter brick tower of Mahabodhi vs. its earliest foundation?",
                promptHi = "पुरातत्वविद् महाबोधि के वर्तमान 55 मीटर ईंट शिखर और इसकी मूल नींव का काल निर्धारण कैसे करते हैं?",
                optionsEn = listOf(
                    "Standing brick tower: 5th–6th c. CE (Late Gupta); earliest shrine foundation: 3rd c. BCE (Ashokan)",
                    "Entire standing 55m brick tower was built intact in 250 BCE without later reconstruction",
                    "Constructed entirely in the 19th century by British surveyors",
                ),
                optionsHi = listOf(
                    "वर्तमान ईंट शिखर: 5वीं-6वीं शताब्दी (गुप्त काल); प्रथम पूजा स्थली: 3री शताब्दी ईसा पूर्व (अशोक काल)",
                    "संपूर्ण 55 मीटर शिखर 250 ईसा पूर्व में बिना किसी पुनर्निर्माण के बना",
                    "19वीं सदी में ब्रिटिश सर्वेक्षकों द्वारा पूर्णतः निर्मित",
                ),
                correctOptionIndex = 0,
                explanationEn = faq.answerEn,
                explanationHi = faq.answerHi,
                claimType = ClaimType.INTERPRETATION,
                sourceId = "src-unesco-1056",
                sourceTitle = UNESCO1056,
            )
            "in-bihar-rajgir-sonbhandar" -> StudyLiteCard(
                cardId = "study-sonbhandar",
                placeId = placeId,
                promptEn = "How does TrueWay classify the 'King Bimbisara's hidden gold treasure' story at Sonbhandar Cave?",
                promptHi = "सोनभंडार गुफा में 'राजा बिम्बिसार के गुप्त खजाने' की कहानी को TrueWay किस श्रेणी में रखता है?",
                optionsEn = listOf(
                    "CONTESTED / Folklore — Muni Vairadeva's 3rd–4th c. CE Sanskrit inscription documents ascetic caves, not verified treasure",
                    "DOCUMENTED — Archaeological excavations confirmed a vault of gold behind the southern wall",
                    "OPERATIONAL — Visitors can open the stone vault with an inscribed password",
                ),
                optionsHi = listOf(
                    "विवादित (CONTESTED) — मुनि वैरदेव का शिलालेख इसे तपस्वियों की गुफा बताता है, प्रमाणित खजाना नहीं",
                    "प्रमाणित तथ्य (DOCUMENTED) — खुदाई में सोने का भंडार मिला है",
                    "परिचालन नियम (OPERATIONAL) — यात्री गुप्त दरवाजा खोल सकते हैं",
                ),
                correctOptionIndex = 0,
                explanationEn = faq.answerEn,
                explanationHi = faq.answerHi,
                claimType = ClaimType.CONTESTED,
                sourceId = faq.sourceId,
                sourceTitle = faq.sourceTitle,
            )
            "in-bihar-nalanda-mahavihara" -> StudyLiteCard(
                cardId = "study-nalanda",
                placeId = placeId,
                promptEn = "Why are Nalanda's excavated structures called 'Monastery 1' or 'Temple 3'?",
                promptHi = "नालंदा की खुदाई वाली संरचनाओं को 'विहार 1' या 'मंदिर 3' क्यों कहा जाता है?",
                optionsEn = listOf(
                    "They are modern curatorial/ASI survey numbers used to avoid fabricating unverified ancient building names",
                    "Emperor Kumaragupta numbered each building from 1 to 14 in 450 CE",
                    "Xuanzang assigned English numbers to the buildings in 637 CE",
                ),
                optionsHi = listOf(
                    "ये 20वीं सदी की खुदाई में भारतीय पुरातत्व सर्वेक्षण (ASI) द्वारा दिए गए आधुनिक सर्वेक्षण क्रमांक हैं",
                    "सम्राट कुमारगुप्त ने 450 ईस्वी में इन्हें 1 से 14 तक नंबर दिए थे",
                    "ह्वेनसांग ने 637 ईस्वी में इन्हें नंबर दिए थे",
                ),
                correctOptionIndex = 0,
                explanationEn = faq.answerEn,
                explanationHi = faq.answerHi,
                claimType = ClaimType.INTERPRETATION,
                sourceId = "src-unesco-1502",
                sourceTitle = UNESCO1502,
            )
            else -> {
                val firstSpotter = profile.whatToSpotOnSite.firstOrNull()
                StudyLiteCard(
                    cardId = "study-$placeId",
                    placeId = placeId,
                    promptEn = faq.questionEn,
                    promptHi = faq.questionHi,
                    optionsEn = listOf(
                        faq.answerEn,
                        "Unverified local rumour not backed by archaeological or textual sources",
                        if (firstSpotter != null) "Observation focus: ${firstSpotter.featureTitle}" else "No verified historical record exists in any archive",
                    ),
                    optionsHi = listOf(
                        faq.answerHi,
                        "असत्यापित स्थानीय अफवाह जिसका कोई पुरातात्विक प्रमाण नहीं है",
                        "कोई ऐतिहासिक रिकॉर्ड उपलब्ध नहीं है",
                    ),
                    correctOptionIndex = 0,
                    explanationEn = faq.answerEn,
                    explanationHi = faq.answerHi,
                    claimType = faq.claimType,
                    sourceId = faq.sourceId,
                    sourceTitle = faq.sourceTitle,
                )
            }
        }
    }

    /**
     * Circuit-wide offline search across all 15 POI insights, architectural spotters, timelines, and FAQs.
     * Used on ExploreScreen so travellers typing historical concepts ("Ashoka", "Xuanzang", "mortar",
     * "stucco", "phone banned", "gold") immediately find verified answers and which monument to visit.
     */
    fun searchCircuitInsights(rawQuery: String, limit: Int = 5): List<InsightSearchHit> {
        val q = rawQuery.trim().lowercase()
        if (q.length < 2) return emptyList()
        if (LIVE_QUERY_TRIGGERS.any { q.contains(it) }) return emptyList()

        val tokens = q.split(Regex("[^\\p{L}\\p{N}]+")).filter { it.length >= 2 && it !in STOP_WORDS }
        if (tokens.isEmpty()) return emptyList()
        val qSkeleton = IndicPhoneticNormalizer.toSkeleton(q)

        val hits = mutableListOf<Pair<InsightSearchHit, Int>>()
        for (profile in profiles.values) {
            val placeName = PlaceRepository.get(profile.placeId)?.canonicalName ?: profile.placeId

            // Check FAQs
            for (faq in profile.faqs) {
                val hay = "${faq.questionEn} ${faq.questionHi} ${faq.answerEn} ${faq.answerHi} ${faq.keywords.joinToString(" ")}".lowercase()
                val haySkel = IndicPhoneticNormalizer.toSkeleton(hay)
                var score = 0
                for (tok in tokens) {
                    if (faq.keywords.any { it.lowercase().contains(tok) }) score += 5
                    else if (hay.contains(tok)) score += 3
                }
                if (qSkeleton.length >= 3 && haySkel.contains(qSkeleton)) score += 2
                if (score > 0) {
                    hits += InsightSearchHit(
                        placeId = profile.placeId,
                        placeName = placeName,
                        matchTitle = faq.questionEn,
                        matchSummary = faq.answerEn,
                        claimType = faq.claimType,
                        sourceTitle = faq.sourceTitle,
                    ) to score
                }
            }

            // Check Spotter & Scholar insights if no FAQ matched for this place
            if (hits.none { it.first.placeId == profile.placeId }) {
                val hay = "${profile.quickTakeawayEn} ${profile.travellerNarrativeEn} ${profile.scholarContextEn} " +
                    profile.whatToSpotOnSite.joinToString(" ") { "${it.featureTitle} ${it.explanation}" }
                val hayLower = hay.lowercase()
                val haySkel = IndicPhoneticNormalizer.toSkeleton(hayLower)
                var score = 0
                for (tok in tokens) {
                    if (hayLower.contains(tok)) score += 2
                }
                if (qSkeleton.length >= 3 && haySkel.contains(qSkeleton)) score += 1
                if (score > 0) {
                    val spotter = profile.whatToSpotOnSite.firstOrNull { s ->
                        tokens.any { tok -> s.featureTitle.lowercase().contains(tok) || s.explanation.lowercase().contains(tok) }
                    }
                    hits += InsightSearchHit(
                        placeId = profile.placeId,
                        placeName = placeName,
                        matchTitle = spotter?.featureTitle ?: "Site Insight: $placeName",
                        matchSummary = spotter?.explanation ?: profile.quickTakeawayEn,
                        claimType = spotter?.claimType ?: ClaimType.DOCUMENTED,
                        sourceTitle = "TrueWay Offline Pack Corpus",
                    ) to score
                }
            }
        }

        return hits
            .sortedByDescending { it.second }
            .map { it.first }
            .distinctBy { "${it.placeId}:${it.matchTitle}" }
            .take(limit.coerceAtLeast(1))
    }

    private val STOP_WORDS = setOf(
        "the", "and", "for", "are", "was", "were", "what", "why", "how",
        "who", "where", "when", "can", "tell", "about", "this", "that",
        "place", "site", "with", "from", "have", "has", "does",
    )
}
