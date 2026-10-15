package com.trueway.app.data

/**
 * P1A Audio Stories, narration scripts, and local phonetic pronunciation guides (blueprint v3.0 §3, §7, F101/F110).
 *
 * Design constraints:
 * - 10 flagship POIs covering the complete Bodh Gaya, Nalanda, and Rajgir circuit.
 * - Pre-authored bilingual narrative scripts (English & Hindi).
 * - Full accessible text transcripts displayed alongside interactive playback controls.
 * - Phonetic / IPA pronunciation guide for ancient Sanskrit/Pali terms.
 * - Explicit item-level rights declarations (source context vs narration production).
 * - Offline media paths for local zero-streaming playback.
 */
data class AudioStory(
    val placeId: String,
    val title: String,
    val titleHindi: String,
    val durationSeconds: Int,
    val phoneticPronunciation: String,
    val narrativeScriptEn: String,
    val narrativeScriptHi: String,
    val transcriptEn: String,
    val transcriptHi: String,
    val narratorCredit: String,
    val rightsNotice: String,
    val audioAssetPath: String,
    val reviewDate: String,
) {
    val narrativeScript: String get() = narrativeScriptEn
}

object AudioStoriesCorpus {
    val stories: Map<String, AudioStory> = mapOf(
        // 1. Mahabodhi Temple
        "in-bihar-bodhgaya-mahabodhi" to AudioStory(
            placeId = "in-bihar-bodhgaya-mahabodhi",
            title = "The Seat of Awakening: Mahabodhi",
            titleHindi = "संबोधि पीठ: महाबोधि मंदिर",
            durationSeconds = 145,
            phoneticPronunciation = "Mahābodhi [mə.ɦaː.boː.dʱi] — Sanskrit: Great Enlightenment",
            narrativeScriptEn = "You are standing before one of the oldest brick Buddhist temples still surviving in India. " +
                "Around 250 BCE, Emperor Ashoka built a modest diamond throne shrine here on the banks of the Falgu river. " +
                "The current 55-meter grand pyramidal shikhara dates primarily from the Gupta period, between the 5th and 6th centuries CE. " +
                "Directly behind this western wall grows the sacred Bodhi Tree, shading the polished sandstone slab of the Vajrasana. " +
                "Notice the sandstone railing posts surrounding the inner circumambulation: the older Mauryan sandstone carvings depict lotus rosettes and mythical animals, while the later Sunga and post-Gupta panels bear figures of stupas and floral garlands. " +
                "When you step inside the central chamber, remember that centuries of pilgrim veneration have preserved this silent sanctuary across kingdoms and eras.",
            narrativeScriptHi = "आप महाबोधि मंदिर के समक्ष खड़े हैं, जो भारत में आज भी सुरक्षित सबसे प्राचीन ईंट-निर्मित बौद्ध मंदिरों में से एक है। " +
                "लगभग 250 ईसा पूर्व, सम्राट अशोक ने फल्गु नदी के तट पर वज्रासन पीठ की स्थापना की थी। " +
                "वर्तमान 55 मीटर ऊँचा भव्य शिखर मुख्य रूप से 5वीं और 6वीं शताब्दी ईस्वी के गुप्त काल का है। " +
                "इस पश्चिमी दीवार के ठीक पीछे पवित्र बोधि वृक्ष स्थित है, जो पॉलिश किए गए बलुआ पत्थर के वज्रासन को अपनी छाया प्रदान करता है। " +
                "परिक्रमा पथ की पत्थर की वेदिका पर उत्कीर्ण मौर्य और शुंग कालीन कलाकृतियों का ध्यानपूर्वक अवलोकन करें।",
            transcriptEn = "Mahabodhi Temple Complex — Complete audio guide transcript: 55-meter pyramidal tower, 5th-century Gupta brick architecture, Ashokan origin, circumambulation railing inscriptions.",
            transcriptHi = "महाबोधि मंदिर परिसर — संपूर्ण ऑडियो गाइड प्रतिलेख: 55-मीटर शिखर, गुप्तकालीन ईंट स्थापत्य, सम्राट अशोक द्वारा शिलान्यास, प्रदक्षिणा वेदिका नक्काशी।",
            narratorCredit = "TrueWay Curatorial Editorial / Scholar Reviewed",
            rightsNotice = "Public Domain historical survey basis / TrueWay Curatorial Audio CC BY-SA 4.0",
            audioAssetPath = "audio/mahabodhi_guide.ogg",
            reviewDate = "2026-10-12",
        ),

        // 2. Bodhi Tree
        "in-bihar-bodhgaya-bodhi-tree" to AudioStory(
            placeId = "in-bihar-bodhgaya-bodhi-tree",
            title = "The Tree of Illumination",
            titleHindi = "बोधिवृक्ष: प्रज्ञा का साक्षी",
            durationSeconds = 120,
            phoneticPronunciation = "Bodhi Vṛkṣa [boː.dʱi vr̩k.ʂə] — Ficus religiosa",
            narrativeScriptEn = "Standing directly behind the main sanctum of the Mahabodhi Temple, this sacred pipal tree marks the revered spot where Siddhartha Gautama meditated for 49 days and attained supreme awakening. " +
                "The current tree is a direct descendant of the original specimen. In the 3rd century BCE, Emperor Ashoka's daughter, Princess Sanghamitta, carried a sapling of this tree to Sri Lanka, where it was planted at Anuradhapura. " +
                "When this tree in Bodh Gaya was destroyed in later centuries, a cutting from the Anuradhapura tree was brought back and replanted here, preserving an unbroken botanical lineage.",
            narrativeScriptHi = "महाबोधि मंदिर के गर्भगृह के ठीक पीछे स्थित यह पवित्र पीपल वृक्ष उस पावन स्थल का साक्षी है जहाँ सिद्धार्थ गौतम ने 49 दिनों तक ध्यान लगाकर सम्यक संबोधि प्राप्त की थी। " +
                "वर्तमान वृक्ष मूल वृक्ष का ही वंशज है, जिसकी शाखा राजकुमारी संघमित्रा 3री सदी ईसा पूर्व में श्रीलंका के अनुराधापुर ले गई थीं।",
            transcriptEn = "Bodhi Tree transcript: Sacred Pipal tree (Ficus religiosa), 49 days of meditation, Sanghamitta's sapling lineage to Anuradhapura, botanical preservation history.",
            transcriptHi = "बोधि वृक्ष प्रतिलेख: पवित्र पीपल, 49 दिवसीय ध्यान साधना, राजकुमारी संघमित्रा द्वारा श्रीलंका शाखा ले जाना, पुनर्रोपण इतिहास।",
            narratorCredit = "TrueWay Curatorial Editorial / Scholar Reviewed",
            rightsNotice = "Historical botanical documentation / TrueWay Audio CC BY-SA 4.0",
            audioAssetPath = "audio/bodhi_tree_guide.ogg",
            reviewDate = "2026-10-12",
        ),

        // 3. Vajrasana (Diamond Throne)
        "in-bihar-bodhgaya-vajrasana" to AudioStory(
            placeId = "in-bihar-bodhgaya-vajrasana",
            title = "The Diamond Throne: Unshakeable Ground",
            titleHindi = "वज्रासन: अविचल धरातल",
            durationSeconds = 115,
            phoneticPronunciation = "Vajrāsana [ʋədʑ.raː.sə.nə] — Sanskrit: Diamond Throne",
            narrativeScriptEn = "Resting between the western wall of the Mahabodhi Temple and the trunk of the Bodhi Tree lies the Vajrasana, or Diamond Throne. " +
                "Carved from a single massive slab of Chunar polished sandstone, this seat was commissioned by Emperor Ashoka around 250 BCE. " +
                "The border is intricately carved with honeysuckles, geese (hamsa), and geometric rosettes characteristic of Mauryan imperial stone craft. " +
                "Tradition identifies this stone as the navel of the earth—the one immovable center capable of supporting the spiritual weight of Enlightenment.",
            narrativeScriptHi = "महाबोधि मंदिर की पश्चिमी दीवार और बोधि वृक्ष के तने के मध्य चुनार के पॉलिश किए गए बलुआ पत्थर से निर्मित विशाल शिलापट ही वज्रासन है। " +
                "सम्राट अशोक द्वारा 250 ईसा पूर्व में स्थापित इस आसन के किनारों पर हंसों और कमलों की भव्य मौर्यकालीन नक्काशी देखी जा सकती है।",
            transcriptEn = "Vajrasana transcript: Ashokan Chunar sandstone slab, 3rd c. BCE, hamsa and palmette motifs, Mauryan high polish.",
            transcriptHi = "वज्रासन प्रतिलेख: चुनार बलुआ पत्थर, सम्राट अशोक कालीन निर्माण, मौर्य पॉलिश और हंस रूपांकन।",
            narratorCredit = "TrueWay Curatorial Editorial / Scholar Reviewed",
            rightsNotice = "ASI survey documentation / TrueWay Audio CC BY-SA 4.0",
            audioAssetPath = "audio/vajrasana_guide.ogg",
            reviewDate = "2026-10-12",
        ),

        // 4. Great Buddha Statue
        "in-bihar-bodhgaya-great-buddha" to AudioStory(
            placeId = "in-bihar-bodhgaya-great-buddha",
            title = "Eighty Feet of Contemplation: The Great Buddha",
            titleHindi = "अस्सी फीट महाबुद्ध प्रतिमा",
            durationSeconds = 100,
            phoneticPronunciation = "Daibutsu [daɪ.bʊt.suː] — Great Buddha of Bodh Gaya",
            narrativeScriptEn = "Towering eighty feet into the sky, the Great Buddha statue was consecrated in 1989 by the 14th Dalai Lama. " +
                "Constructed over seven years using sandstone and red granite, the statue depicts the Buddha seated in the Dhyana Mudra, or meditative posture, atop a grand lotus pedestal. " +
                "Inside the hollow sculpture rests a spiraling staircase leading past bronze statues of the Buddha's ten principal disciples, symbolizing international peace and Buddhist unity.",
            narrativeScriptHi = "अस्सी फीट ऊँची यह भव्य महाबुद्ध प्रतिमा 1989 में प्रतिष्ठित की गई थी। सात वर्षों में निर्मित यह प्रतिमा लाल ग्रेनाइट और बलुआ पत्थर से तैयार की गई है, जिसमें भगवान बुद्ध ध्यान मुद्रा में विराजमान हैं।",
            transcriptEn = "Great Buddha transcript: 80-foot seated sandstone and granite statue, 1989 dedication, Dhyana Mudra posture, Daijokyo monastery craftsmanship.",
            transcriptHi = "महाबुद्ध प्रतिमा प्रतिलेख: 80 फीट ऊँचाई, ध्यान मुद्रा, लाल ग्रेनाइट और बलुआ पत्थर, अंतरराष्ट्रीय शांति प्रतीक।",
            narratorCredit = "TrueWay Curatorial Editorial / Scholar Reviewed",
            rightsNotice = "Monument archival context / TrueWay Audio CC BY-SA 4.0",
            audioAssetPath = "audio/great_buddha_guide.ogg",
            reviewDate = "2026-10-12",
        ),

        // 5. Nalanda Mahavihara
        "in-bihar-nalanda-mahavihara" to AudioStory(
            placeId = "in-bihar-nalanda-mahavihara",
            title = "A Thousand Years of Scholarship: Nalanda",
            titleHindi = "सहस्र वर्ष की ज्ञान परंपरा: नालंदा",
            durationSeconds = 160,
            phoneticPronunciation = "Nālandā [naː.lən̪.d̪aː] — Etymology: Lotus-Giver or Giver of Knowledge",
            narrativeScriptEn = "Nalanda was the world's preeminent residential university, flourishing for over 700 years under the Gupta Empire and the Pala kings. " +
                "At its peak in the 7th century, Chinese monk Xuanzang documented over 10,000 students and 2,000 resident masters studying astronomy, medicine, logic, and Buddhist philosophy. " +
                "As you walk along the main north-south axis, notice the precise architectural layout: a row of monumental temples facing east, opposite a parallel row of self-contained monastic quadrangles (viharas) facing west. " +
                "Each monastery featured a central open brick courtyard surrounded by thirty to forty individual study cells, each with its own stone bed and oil-lamp alcove. " +
                "Look closely at the water wells and stepped drainage conduits — the engineering allowed sophisticated rainwater harvesting across the monastery grounds.",
            narrativeScriptHi = "नालंदा विश्व का प्राचीनतम आवासीय विश्वविद्यालय था, जो गुप्त साम्राज्य और पाल नरेशों के संरक्षण में 700 से अधिक वर्षों तक फला-फूला। " +
                "7वीं सदी में चीनी यात्री ह्वेनसांग ने यहाँ 10,000 विद्यार्थियों और 2,000 आचार्यों के निवास का उल्लेख किया था। " +
                "मुख्य अक्ष पर पूर्वोन्मुखी मंदिरों और पश्चिमोन्मुखी विहारों की सुव्यवस्थित वास्तुकला यहाँ के सुनियोजित नगर-निर्माण को दर्शाती है।",
            transcriptEn = "Nalanda Mahavihara transcript: 700-year history, Xuanzang's chronicle, 10,000 students, residential vihara architecture, hydraulic drainage channels.",
            transcriptHi = "नालंदा महाविहार प्रतिलेख: 700 वर्षीय गौरवशाली इतिहास, ह्वेनसांग यात्रा विवरण, आवासीय विहार व्यवस्था, प्राचीन जल निकासी प्रणाली।",
            narratorCredit = "TrueWay Curatorial Editorial / Scholar Reviewed",
            rightsNotice = "UNESCO & ASI excavation archives / TrueWay Audio CC BY-SA 4.0",
            audioAssetPath = "audio/nalanda_mahavihara_guide.ogg",
            reviewDate = "2026-10-12",
        ),

        // 6. Nalanda Temple 3
        "in-bihar-nalanda-temple-03" to AudioStory(
            placeId = "in-bihar-nalanda-temple-03",
            title = "The Seven Layers of Temple 3",
            titleHindi = "मंदिर संख्या 3: सात परतों का रहस्य",
            durationSeconds = 125,
            phoneticPronunciation = "Temple No. 3 [Stūpa of Śāriputra]",
            narrativeScriptEn = "Temple 3 is the visual anchor of Nalanda's excavated ruins. " +
                "Archaeologists revealed seven successive layers of construction built atop one another between the 5th and 12th centuries CE. " +
                "Rather than demolishing older structures, later builders enveloped earlier stupas in fresh coats of brickwork and stone. " +
                "The fifth layer reveals exquisite Gupta stucco sculptures set in recessed niches, portraying the Buddha and Bodhisattvas in serene meditation. " +
                "Surrounding the monument are dozens of votive stupas erected by visiting pilgrims and scholars from China, Korea, Sri Lanka, and Java to commemorate their completed studies.",
            narrativeScriptHi = "मंदिर संख्या 3 नालंदा के उत्खनित खंडहरों का सबसे भव्य स्मारक है। 5वीं से 12वीं शताब्दी के मध्य यहाँ सात क्रमिक निर्माण परतें खोजी गईं। " +
                "पाँचवीं परत में सुंदर गुप्तकालीन प्लास्टर मूर्तियाँ सुरक्षित हैं, जिनमें भगवान बुद्ध और बोधिसत्वों की मुखाकृति की सौम्यता स्पष्ट दिखाई देती है।",
            transcriptEn = "Temple 3 transcript: Seven construction phases, Stupa of Sariputra tradition, 5th-layer stucco Bodhisattvas, votive stupas field.",
            transcriptHi = "मंदिर 3 प्रतिलेख: सात निर्माण चरण, सारिपुत्र स्तूप परंपरा, पाँचवीं परत की गुप्त मूर्तियाँ, मन्नत स्तूप समूह।",
            narratorCredit = "TrueWay Curatorial Editorial / Scholar Reviewed",
            rightsNotice = "ASI survey reports / TrueWay Audio CC BY-SA 4.0",
            audioAssetPath = "audio/nalanda_temple3_guide.ogg",
            reviewDate = "2026-10-12",
        ),

        // 7. Nalanda Monastery 1
        "in-bihar-nalanda-monastery-01" to AudioStory(
            placeId = "in-bihar-nalanda-monastery-01",
            title = "Life in Monastery 1: Cells, Courtyards, Wells",
            titleHindi = "विहार संख्या 1: भिक्षु जीवन की दिनचर्या",
            durationSeconds = 130,
            phoneticPronunciation = "Mahāvihāra Ek [ʋɪ.ɦaː.rə eːk]",
            narrativeScriptEn = "Monastery 1 is the most completely excavated monastic quadrangle at Nalanda, showing nine sequential levels of occupation. " +
                "Step into the grand central courtyard where master teachers held morning disputations. " +
                "Around the perimeter, two stories of monk cells opened onto a covered pillared veranda. Inside each cell, observe the raised brick bed, the personal meditation alcove, and the lamp niche. " +
                "In the northeast corner, a deep brick-lined well provided clean drinking water throughout the dry season.",
            narrativeScriptHi = "विहार संख्या 1 नालंदा का सबसे बड़ा और महत्वपूर्ण छात्र-निवास था। इसमें नौ क्रमिक निर्माण स्तरों के प्रमाण मिले हैं। " +
                "केंद्रीय प्रांगण के चारों ओर बने छोटे-छोटे अध्ययन कक्ष, पत्थर के बिस्तर और कोने में स्थित गहरा कुआँ प्राचीन छात्र जीवन की सादगी को उजागर करते हैं।",
            transcriptEn = "Monastery 1 transcript: Nine levels of construction, student cells, brick podium, teacher-student disputation courtyard, ancient well.",
            transcriptHi = "विहार 1 प्रतिलेख: नौ निर्माण स्तर, अध्ययन कक्ष, प्राध्यापक वेदी, वाद-विवाद प्रांगण, जल आपूर्ति कुआँ।",
            narratorCredit = "TrueWay Curatorial Editorial / Scholar Reviewed",
            rightsNotice = "ASI excavation records / TrueWay Audio CC BY-SA 4.0",
            audioAssetPath = "audio/nalanda_monastery1_guide.ogg",
            reviewDate = "2026-10-12",
        ),

        // 8. Griddhakuta (Vulture's Peak)
        "in-bihar-rajgir-vultures-peak" to AudioStory(
            placeId = "in-bihar-rajgir-vultures-peak",
            title = "The Hill of the Turning Wheel: Griddhakuta",
            titleHindi = "गृद्धकूट शिखर: द्वितीय धर्मचक्र प्रवर्तन",
            durationSeconds = 135,
            phoneticPronunciation = "Gṛddhakūṭa [ɡrɪd.dʱə.kuː.ʈə] — Pali: Gijjhakūṭa, Vulture's Peak",
            narrativeScriptEn = "High above the ancient valley of Rajgir rises Griddhakuta, named for the natural crag that resembles the head and beak of a vulture perched on the hillside. " +
                "King Bimbisara of Magadha constructed an engineered stone causeway up this ridge so he could visit the Buddha during the rainy season retreats. " +
                "Here on this small open brick terrace, tradition records that Buddha delivered the Heart Sutra and the Lotus Sutra, initiating the Second Turning of the Wheel of Dharma. " +
                "As you stand on this windswept ridge, look down at the natural amphitheater of the five surrounding hills that once formed the impregnable defenses of Rajagriha, the earliest imperial capital of ancient India.",
            narrativeScriptHi = "राजगीर की सुरम्य पहाड़ियों पर स्थित गृद्धकूट शिखर का नाम इसकी गिद्ध जैसी प्राकृतिक शिला-आकृति के कारण पड़ा। " +
                "मगध सम्राट बिम्बिसार ने भगवान बुद्ध के दर्शन हेतु यहाँ तक एक भव्य पाषाण मार्ग बनवाया था। " +
                "इसी पावन स्थल पर तथागत ने प्रज्ञापारमिता और सद्धर्मपुण्डरीक सूत्र का उपदेश देकर द्वितीय धर्मचक्र का प्रवर्तन किया था।",
            transcriptEn = "Griddhakuta transcript: Vulture crag formation, Bimbisara's road, Heart Sutra terrace, panoramic view of five ancient hills of Rajagriha.",
            transcriptHi = "गृद्धकूट प्रतिलेख: गिद्ध सदृश प्राकृतिक चट्टान, बिम्बिसार मार्ग, प्रज्ञापारमिता उपदेश पीठ, राजगृह की पंच पहाड़ियाँ।",
            narratorCredit = "TrueWay Curatorial Editorial / Scholar Reviewed",
            rightsNotice = "Pali canon & ASI historical geography / TrueWay Audio CC BY-SA 4.0",
            audioAssetPath = "audio/griddhakuta_guide.ogg",
            reviewDate = "2026-10-12",
        ),

        // 9. Cyclopean Wall of Rajgir
        "in-bihar-rajgir-cyclopean-wall" to AudioStory(
            placeId = "in-bihar-rajgir-cyclopean-wall",
            title = "Forty Kilometers of Dry Stone: The Cyclopean Wall",
            titleHindi = "राजगीर की साइक्लोपियन प्राचीर",
            durationSeconds = 110,
            phoneticPronunciation = "Rajgir Durgana [raːdʑ.ɡɪr] — Cyclopean Masonry",
            narrativeScriptEn = "One of the most remarkable pre-Mauryan defensive works in South Asia, the Cyclopean Wall spanned over forty kilometers along the ridgelines of the Rajgir hills. " +
                "Constructed without mortar, massive undressed limestone blocks up to one and a half meters across were carefully fitted together by ancient Magadhan builders. " +
                "Dating to the 6th or 5th century BCE, this formidable barrier protected the royal capital from military incursions during the rise of India's earliest empires.",
            narrativeScriptHi = "दक्षिण एशिया की प्राचीनतम सैन्य fortifications में से एक, यह प्राचीर राजगीर की पहाड़ियों पर 40 किलोमीटर से अधिक दूरी तक फैली थी। " +
                "बिना किसी गारे या चूने के, विशाल अनगढ़े चूना पत्थरों को आपस में जोड़कर 6ठी शताब्दी ईसा पूर्व में मगध साम्राज्य की सुरक्षा हेतु बनाया गया था।",
            transcriptEn = "Cyclopean Wall transcript: 40-kilometer defensive stone rampart, pre-Mauryan dry-stone engineering, Magadha capital fortifications.",
            transcriptHi = "साइक्लोपियन दीवार प्रतिलेख: 40 किमी लंबी सुरक्षा प्राचीर, बिना गारे की शुष्क चिनाई, मगध राजधानी की प्राचीन रक्षा दीवार।",
            narratorCredit = "TrueWay Curatorial Editorial / Scholar Reviewed",
            rightsNotice = "ASI survey reports / TrueWay Audio CC BY-SA 4.0",
            audioAssetPath = "audio/cyclopean_wall_guide.ogg",
            reviewDate = "2026-10-12",
        ),

        // 10. Sonbhandar Cave
        "in-bihar-rajgir-sonbhandar" to AudioStory(
            placeId = "in-bihar-rajgir-sonbhandar",
            title = "The Golden Treasury: Sonbhandar Cave",
            titleHindi = "सोनभंडार गुफा: स्वर्ण कोष की किंवदंती",
            durationSeconds = 115,
            phoneticPronunciation = "Svarṇa Bhāṇḍāra [sʋər.ɳə bʱaːɳ.ɖaː.rə] — Gold Treasury",
            narrativeScriptEn = "Chiseled directly into the southern cliff of Vaibhāra Hill, Sonbhandar consists of two rock-cut chambers dating between the 3rd and 4th centuries CE. " +
                "Popular folklore long claimed that Emperor Bimbisara's hidden treasury was sealed inside behind an undeciphered inscription on the chamber wall. " +
                "However, archaeological excavations and the rock-cut Shankhalipi inscription clearly establish that the cave was dedicated by the Jain ascetic Muni Vairadeva for solitary meditation and tapas.",
            narrativeScriptHi = "वैभार पहाड़ी की तलहटी में तराशी गई सोनभंडार गुफाओं के विषय में लोककथा थी कि इसमें सम्राट बिम्बिसार का खजाना छिपा है। " +
                "किंतु पुरातात्विक अध्ययनों और ब्राह्मी-शंखलिपि अभिलेखों से सिद्ध होता है कि यह 3री-4थी सदी में जैन मुनि वैरदेव द्वारा साधना हेतु निर्मित कराई गई थी।",
            transcriptEn = "Sonbhandar transcript: Rock-cut Jain meditation cave, 3rd-4th c. CE, Muni Vairadeva inscription, folklore vs archaeological evidence.",
            transcriptHi = "सोनभंडार प्रतिलेख: शैल-उत्कीर्ण जैन साधना गुफा, मुनि वैरदेव अभिलेख, खजाने की लोककथा बनाम पुरातात्विक सत्य।",
            narratorCredit = "TrueWay Curatorial Editorial / Scholar Reviewed",
            rightsNotice = "Cunningham Archaeological Reports / TrueWay Audio CC BY-SA 4.0",
            audioAssetPath = "audio/sonbhandar_guide.ogg",
            reviewDate = "2026-10-12",
        ),
    )

    fun get(placeId: String): AudioStory? = stories[placeId]
    fun all(): List<AudioStory> = stories.values.toList()
}
