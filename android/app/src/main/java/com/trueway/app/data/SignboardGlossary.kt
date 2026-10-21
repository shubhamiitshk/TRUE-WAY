package com.trueway.app.data

/**
 * P1B F103 — Offline Modern Signboard & Heritage Plaque Decoder
 * (blueprint v3.0 §3 P1B F103 & §4 Rank #6).
 *
 * Helps travellers with zero internet connectivity read and understand:
 * 1. Official Hindi/Devanagari & English visitor restriction, safety, and etiquette signboards.
 * 2. Archaeological Survey of India (ASI) architectural, sculptural, and Sanskrit/Pali plaque terms.
 *
 * Explicit Epistemic Boundary (Blueprint §3 P1B F103):
 * - Designed strictly for modern visitor signage and established architectural terminology.
 * - Explicitly warns travellers that ancient undeciphered epigraphy (such as Shankhalipi
 *   shell-script at Sonbhandar) cannot be auto-deciphered by camera OCR.
 */
enum class SignboardCategory(val label: String) {
    VISITOR_SIGNAGE("Visitor & Safety Signs"),
    ARCHITECTURAL_PLAQUE("ASI Plaque & Architecture Terms"),
    ICONOGRAPHY_MUDRA("Mudras & Sacred Symbols"),
}

data class SignboardTermEntry(
    val termId: String,
    val category: SignboardCategory,
    val scriptDevanagari: String,
    val transliteration: String,
    val englishTitle: String,
    val meaningEn: String,
    val meaningHi: String,
    val whereSeenPlaceIds: List<String>,
    val claimType: ClaimType,
    val keywords: List<String>,
)

object SignboardGlossary {

    const val EPIGRAPHY_BOUNDARY_NOTICE =
        "F103 Boundary: Decodes modern Hindi/English visitor signs and standard ASI architectural terminology offline. " +
            "TrueWay never fabricates translations for undeciphered ancient rock epigraphy (e.g., Shankhalipi shell-script)."

    private val entries: List<SignboardTermEntry> = listOf(
        // 1. Visitor & Safety Signage
        SignboardTermEntry(
            termId = "sign-mobile-prohibited",
            category = SignboardCategory.VISITOR_SIGNAGE,
            scriptDevanagari = "मोबाइल फोन एवं कैमरा वर्जित है",
            transliteration = "Mobail phon evam kaimara varjit hai",
            englishTitle = "Mobile Phones & Cameras Strictly Prohibited",
            meaningEn = "Electronic devices must be deposited at the official security cloakroom before entering the inner perimeter (enforced at Mahabodhi Temple Complex).",
            meaningHi = "मंदिर के आंतरिक परिसर में प्रवेश से पूर्व मोबाइल फोन और कैमरा सुरक्षा क्लोकरूम में जमा करना अनिवार्य है।",
            whereSeenPlaceIds = listOf("in-bihar-bodhgaya-mahabodhi", "in-bihar-bodhgaya-bodhi-tree", "in-bihar-bodhgaya-vajrasana"),
            claimType = ClaimType.OPERATIONAL,
            keywords = listOf("mobile", "phone", "camera", "varjit", "prohibited", "banned", "cloakroom", "मोबाइल", "कैमरा", "वर्जित"),
        ),
        SignboardTermEntry(
            termId = "sign-footwear-deposit",
            category = SignboardCategory.VISITOR_SIGNAGE,
            scriptDevanagari = "कृपया जूते-चप्पल यहाँ उतारें",
            transliteration = "Kripaya joote-chappal yahan utaaren",
            englishTitle = "Please Remove Footwear Here (Shoe Counter)",
            meaningEn = "Sacred sanctum or circumambulation boundary ahead. Leave shoes at the designated rack before stepping onto the stone terrace.",
            meaningHi = "पवित्र परिसर में प्रवेश से पूर्व अपने जूते-चप्पल निर्धारित काउंटर पर उतारें।",
            whereSeenPlaceIds = listOf("in-bihar-bodhgaya-mahabodhi", "in-bihar-rajgir-shanti-stupa", "in-bihar-bodhgaya-great-buddha"),
            claimType = ClaimType.OPERATIONAL,
            keywords = listOf("shoes", "footwear", "joote", "chappal", "barefoot", "counter", "जूते", "चप्पल"),
        ),
        SignboardTermEntry(
            termId = "sign-asi-protected",
            category = SignboardCategory.VISITOR_SIGNAGE,
            scriptDevanagari = "संरक्षित स्मारक — भारतीय पुरातत्व सर्वेक्षण (अधिनियम 1958)",
            transliteration = "Sanrakshit Smarak — Bharatiya Puratatva Sarvekshan (1958)",
            englishTitle = "Protected National Monument (ASI Act 1958)",
            meaningEn = "Official blue/stone notice board under the Ancient Monuments and Archaeological Sites and Remains Act, 1958. Carving names, removing bricks, or damaging surfaces is a punishable offence.",
            meaningHi = "प्राचीन संस्मारक तथा पुरातत्वीय स्थल और अवशेष अधिनियम 1958 के अंतर्गत राष्ट्रीय महत्व का संरक्षित स्मारक।",
            whereSeenPlaceIds = listOf("in-bihar-nalanda-mahavihara", "in-bihar-rajgir-cyclopean-wall", "in-bihar-nalanda-temple-03", "in-bihar-nalanda-monastery-01"),
            claimType = ClaimType.DOCUMENTED,
            keywords = listOf("sanrakshit", "smarak", "asi", "protected", "monument", "1958", "law", "blue board", "संरक्षित", "स्मारक"),
        ),
        SignboardTermEntry(
            termId = "sign-do-not-climb-ruins",
            category = SignboardCategory.VISITOR_SIGNAGE,
            scriptDevanagari = "प्राचीन दीवारों पर चढ़ना या बैठना सख्त मना है",
            transliteration = "Prachin deewaron par chadhna ya baithna sakht mana hai",
            englishTitle = "Do Not Climb or Sit on Ancient Brick/Stone Walls",
            meaningEn = "Excavated Gupta and Pala brick courses and mud-mortar terraces are fragile. Stay on marked pathways and wooden/stone steps.",
            meaningHi = "उत्खनित प्राचीन ईंटों और दीवारों पर चढ़ना या बैठना निषिद्ध है; केवल निर्धारित पथ का उपयोग करें।",
            whereSeenPlaceIds = listOf("in-bihar-nalanda-mahavihara", "in-bihar-nalanda-temple-03", "in-bihar-nalanda-monastery-01", "in-bihar-rajgir-cyclopean-wall"),
            claimType = ClaimType.OPERATIONAL,
            keywords = listOf("climb", "walls", "bricks", "fragile", "deewar", "mana", "दीवार", "ईंट"),
        ),
        SignboardTermEntry(
            termId = "sign-silence-meditation",
            category = SignboardCategory.VISITOR_SIGNAGE,
            scriptDevanagari = "कृपया शांति बनाए रखें — ध्यान क्षेत्र",
            transliteration = "Kripaya shanti banaye rakhen — Dhyan Kshetra",
            englishTitle = "Maintain Silence — Meditation Zone",
            meaningEn = "Quiet contemplation zone around sacred shrines and the Bodhi Tree enclosure. Avoid loud conversation or speaker playback.",
            meaningHi = "पवित्र ध्यान क्षेत्र में कृपया मौन और शांति बनाए रखें।",
            whereSeenPlaceIds = listOf("in-bihar-bodhgaya-bodhi-tree", "in-bihar-bodhgaya-animesh-lochan", "in-bihar-bodhgaya-mucalinda"),
            claimType = ClaimType.OPERATIONAL,
            keywords = listOf("silence", "shanti", "dhyan", "meditation", "quiet", "शांति", "ध्यान"),
        ),

        // 2. ASI Plaque & Architecture Terms
        SignboardTermEntry(
            termId = "term-mahavihara",
            category = SignboardCategory.ARCHITECTURAL_PLAQUE,
            scriptDevanagari = "महाविहार / विहार (चतुष्शाल)",
            transliteration = "Mahavihara / Vihara (Chatush-shala)",
            englishTitle = "Vihara & Mahavihara (Monastic Quadrangle)",
            meaningEn = "A Vihara is a rectangular monastic residence built around an open central courtyard with monk study cells along all four sides. A Mahavihara ('Great Vihara') is an integrated university complex of multiple viharas and temples, such as Nalanda.",
            meaningHi = "विहार भिक्षुओं के निवास एवं अध्ययन का चतुष्कोणीय परिसर होता है जिसके चारों ओर छोटे कक्ष बने होते हैं। अनेक विहारों के समूह को महाविहार कहते हैं।",
            whereSeenPlaceIds = listOf("in-bihar-nalanda-mahavihara", "in-bihar-nalanda-monastery-01", "in-bihar-nalanda-museum"),
            claimType = ClaimType.DOCUMENTED,
            keywords = listOf("vihara", "mahavihara", "monastery", "quadrangle", "courtyard", "cells", "विहार", "महाविहार"),
        ),
        SignboardTermEntry(
            termId = "term-chaitya-stupa",
            category = SignboardCategory.ARCHITECTURAL_PLAQUE,
            scriptDevanagari = "चैत्य / स्तूप (अण्ड, हर्मिका, छत्रावली)",
            transliteration = "Chaitya / Stupa (Anda, Harmika, Chhatravali)",
            englishTitle = "Stupa & Chaitya (Anda, Harmika, Chhatravali)",
            meaningEn = "A Stupa is a solid hemispherical or terraced brick/stone reliquary mound. Key parts on ASI plaques: 'Medhi' (circular drum/terrace), 'Anda' (hemispherical dome), 'Harmika' (square railing pavilion on top), and 'Chhatravali' (spire of ceremonial umbrellas).",
            meaningHi = "स्तूप या चैत्य बौद्ध स्थापत्य का प्रमुख स्मारक है, जिसके मुख्य भाग मेधि (चबूतरा), अण्ड (गुंबद), हर्मिका और छत्रावली (छत्रों की श्रृंखला) हैं।",
            whereSeenPlaceIds = listOf("in-bihar-nalanda-temple-03", "in-bihar-bodhgaya-animesh-lochan", "in-bihar-rajgir-shanti-stupa"),
            claimType = ClaimType.DOCUMENTED,
            keywords = listOf("stupa", "chaitya", "anda", "harmika", "chhatravali", "medhi", "dome", "स्तूप", "चैत्य", "हर्मिका"),
        ),
        SignboardTermEntry(
            termId = "term-vajrasana",
            category = SignboardCategory.ARCHITECTURAL_PLAQUE,
            scriptDevanagari = "वज्रासन (हीरा सिंहासन)",
            transliteration = "Vajrasana (Diamond Seat)",
            englishTitle = "Vajrasana (The Diamond Throne)",
            meaningEn = "Carved and polished Mauryan sandstone slab (c. 3rd century BCE, attributed to Emperor Ashoka) resting between the Bodhi Tree and the western face of Mahabodhi Temple.",
            meaningHi = "बोधि वृक्ष के नीचे स्थित सम्राट अशोक के काल (तीसरी शताब्दी ईसा पूर्व) की पॉलिशदार बलुआ पत्थर की शिला।",
            whereSeenPlaceIds = listOf("in-bihar-bodhgaya-vajrasana", "in-bihar-bodhgaya-bodhi-tree"),
            claimType = ClaimType.DOCUMENTED,
            keywords = listOf("vajrasana", "diamond", "throne", "seat", "ashoka", "slab", "वज्रासन"),
        ),
        SignboardTermEntry(
            termId = "term-vedika-torana",
            category = SignboardCategory.ARCHITECTURAL_PLAQUE,
            scriptDevanagari = "वेदिका एवं तोरण (स्तम्भ, सूची, उष्णीष)",
            transliteration = "Vedika & Torana (Stambha, Suchi, Ushnisha)",
            englishTitle = "Vedika (Sacred Railing) & Torana (Gateway)",
            meaningEn = "Stone protective enclosure around a stupa or temple. 'Stambha' = upright post; 'Suchi' = lens-shaped horizontal crossbar; 'Ushnisha' = top coping stone; 'Torana' = arched ceremonial gateway.",
            meaningHi = "स्तूप या मंदिर के चारों ओर की पाषाण रेलिंग को वेदिका और प्रवेश द्वार को तोरण कहते हैं।",
            whereSeenPlaceIds = listOf("in-bihar-bodhgaya-mahabodhi", "in-bihar-bodhgaya-vajrasana"),
            claimType = ClaimType.DOCUMENTED,
            keywords = listOf("vedika", "torana", "railing", "stambha", "suchi", "ushnisha", "gateway", "वेदिका", "तोरण"),
        ),
        SignboardTermEntry(
            termId = "term-pradakshina-patha",
            category = SignboardCategory.ARCHITECTURAL_PLAQUE,
            scriptDevanagari = "प्रदक्षिणा पथ / चंक्रमण",
            transliteration = "Pradakshina Patha / Chankramana",
            englishTitle = "Pradakshina Patha (Circumambulation Path) & Chankramana",
            meaningEn = "'Pradakshina Patha' is the clockwise walking path around a sacred monument (keeping the shrine to your right). 'Chankramana' is the raised cloister walkway along the northern wall of Mahabodhi Temple marked with 19 stone lotus pedestals.",
            meaningHi = "स्मारक को अपनी दाईं ओर रखते हुए घड़ी की दिशा में परिक्रमा करने का मार्ग प्रदक्षिणा पथ कहलाता है।",
            whereSeenPlaceIds = listOf("in-bihar-bodhgaya-mahabodhi", "in-bihar-bodhgaya-bodhi-tree", "in-bihar-rajgir-shanti-stupa"),
            claimType = ClaimType.DOCUMENTED,
            keywords = listOf("pradakshina", "patha", "chankramana", "clockwise", "walkway", "lotus", "प्रदक्षिणा", "चंक्रमण"),
        ),
        SignboardTermEntry(
            termId = "term-shankhalipi",
            category = SignboardCategory.ARCHITECTURAL_PLAQUE,
            scriptDevanagari = "शंखलिपि (शंख-आकृति अभिलेख)",
            transliteration = "Shankhalipi (Shell-Script Inscription)",
            englishTitle = "Shankhalipi (Ornate Shell-Script Glyphs)",
            meaningEn = "[CONTESTED / UNDECIPHERED] Ornate 4th–8th century CE calligraphic inscriptions resembling conch shells carved into rock walls (such as Sonbhandar Cave). Scholars interpret them as stylized personal signatures or invocations; folklore falsely calls them a 'treasure password.'",
            meaningHi = "[विवादित / अपठित] चट्टानों पर उत्कीर्ण शंख के आकार की प्राचीन अलंकृत लिपि (4थी-8वीं शताब्दी ईस्वी), जिसे अभी तक पूर्णतः पढ़ा नहीं जा सका है।",
            whereSeenPlaceIds = listOf("in-bihar-rajgir-sonbhandar"),
            claimType = ClaimType.CONTESTED,
            keywords = listOf("shankhalipi", "shell", "script", "inscription", "cipher", "password", "sonbhandar", "शंखलिपि"),
        ),

        // 3. Iconography & Mudras
        SignboardTermEntry(
            termId = "mudra-bhumisparsha",
            category = SignboardCategory.ICONOGRAPHY_MUDRA,
            scriptDevanagari = "भूमिस्पर्श मुद्रा",
            transliteration = "Bhumisparsha Mudra",
            englishTitle = "Bhumisparsha Mudra (Earth-Touching Gesture)",
            meaningEn = "Seated meditation posture where the right hand reaches down over the right knee to touch the Earth, calling the Earth goddess (Vasundhara) to witness the Buddha's Awakening at Bodh Gaya.",
            meaningHi = "दाहिने हाथ की उंगलियों से पृथ्वी को स्पर्श करने की मुद्रा, जो बोधगया में बुद्धत्व प्राप्ति के समय पृथ्वी को साक्षी बनाने का प्रतीक है।",
            whereSeenPlaceIds = listOf("in-bihar-bodhgaya-mahabodhi", "in-bihar-bodhgaya-vajrasana", "in-bihar-nalanda-temple-03"),
            claimType = ClaimType.TRADITION,
            keywords = listOf("bhumisparsha", "mudra", "earth", "touching", "hand", "gesture", "भूमिस्पर्श", "मुद्रा"),
        ),
        SignboardTermEntry(
            termId = "mudra-dharmachakra",
            category = SignboardCategory.ICONOGRAPHY_MUDRA,
            scriptDevanagari = "धर्मचक्र प्रवर्तन मुद्रा",
            transliteration = "Dharmachakra Pravartana Mudra",
            englishTitle = "Dharmachakra Mudra (Turning the Wheel of Law)",
            meaningEn = "Both hands held in front of the chest with thumb and index fingers forming a wheel—symbolizing the teaching of the Dharma (seen on the 6th-c. Gupta stucco figures at Nalanda Temple 3 and Vishwa Shanti Stupa).",
            meaningHi = "छाती के सामने दोनों हाथों से धर्मचक्र घुमाने की मुद्रा, जो बुद्ध के प्रथम उपदेश एवं शिक्षण का प्रतीक है।",
            whereSeenPlaceIds = listOf("in-bihar-nalanda-temple-03", "in-bihar-rajgir-shanti-stupa"),
            claimType = ClaimType.DOCUMENTED,
            keywords = listOf("dharmachakra", "mudra", "wheel", "teaching", "sermon", "stucco", "धर्मचक्र"),
        ),
    )

    fun all(): List<SignboardTermEntry> = entries

    fun byCategory(category: SignboardCategory): List<SignboardTermEntry> =
        entries.filter { it.category == category }

    fun forPlace(placeId: String): List<SignboardTermEntry> =
        entries.filter { placeId in it.whereSeenPlaceIds }

    /**
     * Searches offline signboard notices and ASI plaque terms using Latin, Devanagari,
     * and [IndicPhoneticNormalizer] phonetic skeleton matching.
     */
    fun search(rawQuery: String, limit: Int = 6): List<SignboardTermEntry> {
        val q = rawQuery.trim().lowercase()
        if (q.length < 2) return emptyList()
        val tokens = q.split(Regex("[^\\p{L}\\p{N}]+")).filter { it.length >= 2 }
        if (tokens.isEmpty()) return emptyList()
        val qSkel = IndicPhoneticNormalizer.toSkeleton(q)

        val scored = mutableListOf<Pair<SignboardTermEntry, Int>>()
        for (entry in entries) {
            val hay = "${entry.scriptDevanagari} ${entry.transliteration} ${entry.englishTitle} ${entry.meaningEn} ${entry.meaningHi} ${entry.keywords.joinToString(" ")}".lowercase()
            val haySkel = IndicPhoneticNormalizer.toSkeleton(hay)
            var score = 0
            for (tok in tokens) {
                if (entry.keywords.any { it.lowercase().contains(tok) }) score += 5
                else if (entry.transliteration.lowercase().contains(tok) || entry.scriptDevanagari.contains(tok)) score += 4
                else if (hay.contains(tok)) score += 2
            }
            if (qSkel.length >= 3 && haySkel.contains(qSkel)) score += 3
            if (score > 0) {
                scored += entry to score
            }
        }
        return scored.sortedByDescending { it.second }.map { it.first }.take(limit.coerceAtLeast(1))
    }
}
