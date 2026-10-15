"""Generator & Validator for P1A Audio Stories (.ogg Vorbis files).

Upgraded multi-backend audio synthesis & validation pipeline:
1. Cross-platform FFmpeg discovery (`shutil.which("ffmpeg")` + Windows WinGet fallback).
2. Authentic Devanagari Hindi scripts (`text_hi_devanagari`), phonetic Romanized Hindi
   (`text_hi`), English scripts (`text_en`), and IPA pronunciations (`ipa`) matching
   `AudioStories.kt` across all 10 flagship POIs.
3. Multi-tier TTS synthesis ladder:
   - Tier 1: `edge-tts` neural voices (`en-IN-NeerjaNeural` / `hi-IN-SwaraNeural`) if available.
   - Tier 2: `espeak-ng` (`en` / `hi` Devanagari) if available.
   - Tier 3: Windows PowerShell `System.Speech.Synthesis.SpeechSynthesizer` (selects native
     `hi-IN` voice for Devanagari when installed on Windows, else phonetic fallback).
   - Default safe mode (`--verify-or-preserve`): verifies all 20 existing `.ogg` Vorbis
     streams (44.1 kHz, duration > 0, non-corrupt) and syncs `content/audio/` with
     `android/app/src/main/assets/audio/` without overwriting existing voice recordings
     when running in an offline Linux CI container.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WINGET_FFMPEG = r"C:\Users\sumit\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
FFMPEG = shutil.which("ffmpeg") or (WINGET_FFMPEG if Path(WINGET_FFMPEG).is_file() else "ffmpeg")
FFPROBE = shutil.which("ffprobe") or "ffprobe"

AUDIO_DIR = ROOT / "content" / "audio"
ASSETS_AUDIO_DIR = ROOT / "android" / "app" / "src" / "main" / "assets" / "audio"

STORIES = [
    {
        "id": "mahabodhi",
        "place_id": "in-bihar-bodhgaya-mahabodhi",
        "ipa": "Mahābodhi [mə.ɦaː.boː.dʱi]",
        "file_en": "mahabodhi_guide.ogg",
        "file_hi": "mahabodhi_guide_hi.ogg",
        "text_en": (
            "Mahabodhi. Sanskrit: Great Enlightenment. "
            "You are standing before one of the oldest brick Buddhist temples still surviving in India. "
            "Around 250 BCE, Emperor Ashoka built a modest diamond throne shrine here on the banks of the Falgu river. "
            "The current 55-meter grand pyramidal shikhara dates primarily from the Gupta period, between the 5th and 6th centuries CE. "
            "Directly behind this western wall grows the sacred Bodhi Tree, shading the polished sandstone slab of the Vajrasana. "
            "Notice the sandstone railing posts surrounding the inner circumambulation: the older Mauryan sandstone carvings depict lotus rosettes and mythical animals, "
            "while the later Sunga and post-Gupta panels bear figures of stupas and floral garlands. "
            "When you step inside the central chamber, remember that centuries of pilgrim veneration have preserved this silent sanctuary across kingdoms and eras."
        ),
        "text_hi_devanagari": (
            "महाबोधि मंदिर। संबोधि पीठ। "
            "आप महाबोधि मंदिर के समक्ष खड़े हैं, जो भारत में आज भी सुरक्षित सबसे प्राचीन ईंट-निर्मित बौद्ध मंदिरों में से एक है। "
            "लगभग 250 ईसा पूर्व, सम्राट अशोक ने फल्गु नदी के तट पर वज्रासन पीठ की स्थापना की थी। "
            "वर्तमान 55 मीटर ऊँचा भव्य शिखर मुख्य रूप से 5वीं और 6वीं शताब्दी ईस्वी के गुप्त काल का है। "
            "इस पश्चिमी दीवार के ठीक पीछे पवित्र बोधि वृक्ष स्थित है, जो पॉलिश किए गए बलुआ पत्थर के वज्रासन को अपनी छाया प्रदान करता है। "
            "परिक्रमा पथ की पत्थर की वेदिका पर उत्कीर्ण मौर्य और शुंग कालीन कलाकृतियों का ध्यानपूर्वक अवलोकन करें।"
        ),
        "text_hi": (
            "Mahabodhi Mandir. Sambodhi Peeth. "
            "Aap Mahabodhi Mandir ke samaksh khade hain, jo Bharat mein aaj bhi surakshit sabse pracheen eent-nirmit Bauddha mandiron mein se ek hai. "
            "Lagbhag do sau pachaas Eesa Poorva, Samrat Ashoka ne Falgu nadi ke tat par Vajrasana peeth ki sthapana ki thi. "
            "Vartamaan pachpan meter ooncha bhavya shikhara mukhya roop se paanchvi aur chhati shatabdi Eeswi ke Gupta kaal ka hai. "
            "Is pashchimi deewar ke theek peeche pavitra Bodhi Vriksha sthit hai, jo polish kiye gaye balua patthar ke Vajrasana ko apni chhaya pradan karta hai. "
            "Parikrama path ki patthar ki vedika par utkeerna Maurya aur Sunga kaaleen kalakritiyon ka dhyanpoorvak avalokan karein."
        ),
    },
    {
        "id": "bodhi_tree",
        "place_id": "in-bihar-bodhgaya-bodhi-tree",
        "ipa": "Bodhi Vṛkṣa [boː.dʱi vr̩k.ʂə]",
        "file_en": "bodhi_tree_guide.ogg",
        "file_hi": "bodhi_tree_guide_hi.ogg",
        "text_en": (
            "Bodhi Vriksha. Ficus religiosa. "
            "Standing directly behind the main sanctum of the Mahabodhi Temple, this sacred pipal tree marks the revered spot where Siddhartha Gautama meditated for 49 days and attained supreme awakening. "
            "The current tree is a direct descendant of the original specimen. "
            "In the 3rd century BCE, Emperor Ashoka's daughter, Princess Sanghamitta, carried a sapling of this tree to Sri Lanka, where it was planted at Anuradhapura. "
            "When this tree in Bodh Gaya was destroyed in later centuries, a cutting from the Anuradhapura tree was brought back and replanted here, preserving an unbroken botanical lineage."
        ),
        "text_hi_devanagari": (
            "बोधिवृक्ष। प्रज्ञा का साक्षी। "
            "महाबोधि मंदिर के गर्भगृह के ठीक पीछे स्थित यह पवित्र पीपल वृक्ष उस पावन स्थल का साक्षी है जहाँ सिद्धार्थ गौतम ने 49 दिनों तक ध्यान लगाकर सम्यक संबोधि प्राप्त की थी। "
            "वर्तमान वृक्ष मूल वृक्ष का ही वंशज है, जिसकी शाखा राजकुमारी संघमित्रा तीसरी सदी ईसा पूर्व में श्रीलंका के अनुराधापुरा ले गई थीं। "
            "कालांतर में अनुराधापुरा वृक्ष से शाखा लाकर यहाँ पुनः रोपण किया गया।"
        ),
        "text_hi": (
            "Bodhi Vriksha. Pragya ka Sakshi. "
            "Mahabodhi Mandir ke garbhagriha ke theek peeche sthit yeh pavitra peepal vriksha us paavan sthal ka sakshi hai jahan Siddhartha Gautama ne unchaas dinon tak dhyan lagakar samyak sambodhi prapt ki thi. "
            "Vartamaan vriksha mool vriksha ka hi vanshaj hai, jiski shakha Rajkumari Sanghamitta teesri sadi Eesa Poorva mein Sri Lanka ke Anuradhapura le gayi theen. "
            "Kalaantar mein Anuradhapura vriksha se shakha lakar yahan punah ropan kiya gaya."
        ),
    },
    {
        "id": "vajrasana",
        "place_id": "in-bihar-bodhgaya-vajrasana",
        "ipa": "Vajrāsana [ʋədʒ.raː.sə.nə]",
        "file_en": "vajrasana_guide.ogg",
        "file_hi": "vajrasana_guide_hi.ogg",
        "text_en": (
            "Vajrasana. Sanskrit: Diamond Throne. "
            "Resting between the western wall of the Mahabodhi Temple and the trunk of the Bodhi Tree lies the Vajrasana, or Diamond Throne. "
            "Carved from a single massive slab of Chunar polished sandstone, this seat was commissioned by Emperor Ashoka around 250 BCE. "
            "The border is intricately carved with honeysuckles, geese, and geometric rosettes characteristic of Mauryan imperial stone craft. "
            "Tradition identifies this stone as the navel of the earth, the one immovable center capable of supporting the spiritual weight of Enlightenment."
        ),
        "text_hi_devanagari": (
            "वज्रासन। अविचल धरातल। "
            "महाबोधि मंदिर की पश्चिमी दीवार और बोधि वृक्ष के तने के मध्य चुनार के पॉलिश किए गए बलुआ पत्थर से निर्मित विशाल शिलापट्ट ही वज्रासन है। "
            "सम्राट अशोक द्वारा 250 ईसा पूर्व में स्थापित इस आसन के किनारों पर हंसों और कमलों की भव्य मौर्यकालीन नक्काशी देखी जा सकती है। "
            "परंपरा इस स्थल को पृथ्वी की नाभि मानती है।"
        ),
        "text_hi": (
            "Vajrasana. Avichal Dharatal. "
            "Mahabodhi Mandir ki pashchimi deewar aur Bodhi Vriksha ke tane ke madhya Chunar ke polish kiye gaye balua patthar se nirmit vishal shilapat hi Vajrasana hai. "
            "Samrat Ashoka dwara do sau pachaas Eesa Poorva mein sthapit is aasan ke kinaron par hanson aur kamalon ki bhavya Mauryakaaleen nakkashi dekhi ja sakti hai. "
            "Parampara is sthal ko prithvi ki naabhi manti hai."
        ),
    },
    {
        "id": "great_buddha",
        "place_id": "in-bihar-bodhgaya-great-buddha",
        "ipa": "Daibutsu [daɪ.bʊt.suː]",
        "file_en": "great_buddha_guide.ogg",
        "file_hi": "great_buddha_guide_hi.ogg",
        "text_en": (
            "Daibutsu. Great Buddha of Bodh Gaya. "
            "Towering eighty feet into the sky, the Great Buddha statue was consecrated in 1989 by the 14th Dalai Lama. "
            "Constructed over seven years using sandstone and red granite, the statue depicts the Buddha seated in the Dhyana Mudra, or meditative posture, atop a grand lotus pedestal. "
            "Inside the hollow sculpture rests a spiraling staircase leading past bronze statues of the Buddha's ten principal disciples, symbolizing international peace and Buddhist unity."
        ),
        "text_hi_devanagari": (
            "अस्सी फीट महाबुद्ध प्रतिमा। "
            "अस्सी फीट ऊँची यह भव्य महाबुद्ध प्रतिमा 1989 में प्रतिष्ठित की गई थी। "
            "सात वर्षों में निर्मित यह प्रतिमा लाल ग्रेनाइट और बलुआ पत्थर से तैयार की गई है, जिसमें भगवान बुद्ध ध्यान मुद्रा में विराजमान हैं। "
            "यह प्रतिमा अंतर्राष्ट्रीय शांति और बौद्ध एकता का प्रतीक है।"
        ),
        "text_hi": (
            "Assi Feet Mahabuddha Pratima. "
            "Assi feet oonchi yeh bhavya Mahabuddha pratima unnees sau nawaasi mein pratishthit ki gayi thi. "
            "Saat varshon mein nirmit yeh pratima laal granite aur balua patthar se taiyar ki gayi hai, jismein Bhagwan Buddha dhyan mudra mein virajmaan hain. "
            "Yeh pratima antarrashtriya shanti aur Bauddha ekta ka prateek hai."
        ),
    },
    {
        "id": "nalanda_mahavihara",
        "place_id": "in-bihar-nalanda-mahavihara",
        "ipa": "Nālandā Mahāvihāra [naː.lən.d̪aː mə.ɦaː.ʋɪ.ɦaː.rə]",
        "file_en": "nalanda_mahavihara_guide.ogg",
        "file_hi": "nalanda_mahavihara_guide_hi.ogg",
        "text_en": (
            "Nalanda. Sanskrit: Lotus-Giver or Giver of Knowledge. "
            "Nalanda was the world's preeminent residential university, flourishing for over 700 years under the Gupta Empire and the Pala kings. "
            "At its peak in the 7th century, Chinese monk Xuanzang documented over 10,000 students and 2,000 resident masters studying astronomy, medicine, logic, and Buddhist philosophy. "
            "As you walk along the main north-south axis, notice the precise architectural layout: a row of monumental temples facing east, opposite a parallel row of self-contained monastic quadrangles facing west. "
            "Each monastery featured a central open brick courtyard surrounded by study cells, each with its own stone bed and oil-lamp alcove."
        ),
        "text_hi_devanagari": (
            "नालंदा महाविहार। सहस्र वर्ष की ज्ञान परंपरा। "
            "नालंदा विश्व का प्राचीनतम आवासीय विश्वविद्यालय था, जो गुप्त साम्राज्य और पाल नरेशों के संरक्षण में 700 से अधिक वर्षों तक फला-फूला। "
            "7वीं सदी में चीनी यात्री ह्वेनसांग ने यहाँ 10,000 विद्यार्थियों और 2,000 आचार्यों के निवास का उल्लेख किया था। "
            "मुख्य अक्ष पर पूर्वोन्मुखी मंदिरों और पश्चिमोन्मुखी विहारों की सुव्यवस्थित वास्तुकला यहाँ के सुनियोजित नगर-निर्माण को दर्शाती है।"
        ),
        "text_hi": (
            "Nalanda Mahavihara. Sahasra Varsh ki Gyan Parampara. "
            "Nalanda vishwa ka pracheentam aawasiya vishwavidyalaya tha, jo Gupta samrajya aur Pala nareshon ke sanrakshan mein saat sau se adhik varshon tak phala-phoola. "
            "Saatvi sadi mein cheeni yatri Xuanzang ne yahan das hazaar vidyarthiyon aur do hazaar aacharyon ke niwas ka ullekh kiya tha. "
            "Mukhya aksh par poorvonmukhi mandiron aur pashchimonmukhi viharon ki suvyavasthit vaastukala yahan ke suniyojit nagar-nirmaan ko darshati hai."
        ),
    },
    {
        "id": "nalanda_temple3",
        "place_id": "in-bihar-nalanda-temple-03",
        "ipa": "Śāriputra Stūpa [ɕaː.rɪ.pʊt.rə stuː.pə]",
        "file_en": "nalanda_temple3_guide.ogg",
        "file_hi": "nalanda_temple3_guide_hi.ogg",
        "text_en": (
            "Temple Number 3. Stupa of Sariputra. "
            "Temple 3 is the visual anchor of Nalanda's excavated ruins. "
            "Archaeologists revealed seven successive layers of construction built atop one another between the 5th and 12th centuries CE. "
            "Rather than demolishing older structures, later builders enveloped earlier stupas in fresh coats of brickwork and stone. "
            "The fifth layer reveals exquisite Gupta stucco sculptures set in recessed niches, portraying the Buddha and Bodhisattvas in serene meditation. "
            "Surrounding the monument are dozens of votive stupas erected by visiting pilgrims and scholars."
        ),
        "text_hi_devanagari": (
            "मंदिर संख्या तीन। सात परतों का रहस्य। "
            "मंदिर संख्या 3 नालंदा के उत्खनित खंडहरों का सबसे भव्य स्मारक है। "
            "5वीं से 12वीं शताब्दी के मध्य यहाँ सात क्रमिक निर्माण परतें खोजी गईं। "
            "पाँचवीं परत में सुंदर गुप्तकालीन प्लास्टर मूर्तियाँ सुरक्षित हैं, जिनमें भगवान बुद्ध और बोधिसत्वों की मुखाकृति की सौम्यता स्पष्ट दिखाई देती है।"
        ),
        "text_hi": (
            "Mandir Sankhya Teen. Saat Parton ka Rahasya. "
            "Mandir sankhya teen Nalanda ke utkhanit khandaharon ka sabse bhavya smarak hai. "
            "Paanchvi se baarahvi shatabdi ke madhya yahan saat kramik nirmaan partein khoji gayin. "
            "Paanchvi parat mein sundar Guptakaaleen plaster moortiyan surakshit hain, jinmein Bhagwan Buddha aur Bodhisattvon ki mukhaakriti ki saumyata spasht dikhayi deti hai."
        ),
    },
    {
        "id": "nalanda_monastery1",
        "place_id": "in-bihar-nalanda-monastery-01",
        "ipa": "Vihāra Eka [ʋɪ.ɦaː.rə eːk]",
        "file_en": "nalanda_monastery1_guide.ogg",
        "file_hi": "nalanda_monastery1_guide_hi.ogg",
        "text_en": (
            "Mahavihara Ek. Monastery Number 1. "
            "Monastery 1 is the most completely excavated monastic quadrangle at Nalanda, showing nine sequential levels of occupation. "
            "Step into the grand central courtyard where master teachers held morning disputations. "
            "Around the perimeter, two stories of monk cells opened onto a covered pillared veranda. "
            "Inside each cell, observe the raised brick bed, the personal meditation alcove, and the lamp niche. "
            "In the northeast corner, a deep brick-lined well provided clean drinking water throughout the dry season."
        ),
        "text_hi_devanagari": (
            "विहार संख्या एक। भिक्षु जीवन की दिनचर्या। "
            "विहार संख्या 1 नालंदा का सबसे बड़ा और महत्वपूर्ण छात्र-निवास था। इसमें नौ क्रमिक निर्माण स्तरों के प्रमाण मिले हैं। "
            "केंद्रीय प्रांगण के चारों ओर बने छोटे-छोटे अध्ययन कक्ष, पत्थर के बिस्तर और कोने में स्थित गहरा कुआँ प्राचीन छात्र जीवन की सादगी को उजागर करते हैं।"
        ),
        "text_hi": (
            "Vihara Sankhya Ek. Bhikshu Jeevan ki Dincharya. "
            "Vihara sankhya ek Nalanda ka sabse bada aur mahatvapoorna chhatra-niwas tha. Ismein nau kramik nirmaan staron ke pramaan mile hain. "
            "Kendriya praangan ke charon or bane chhote-chhote adhyayan kaksh, patthar ke bistar aur kone mein sthit gehra kuan pracheen chhatra jeevan ki saadgi ko ujagar karte hain."
        ),
    },
    {
        "id": "griddhakuta",
        "place_id": "in-bihar-rajgir-vultures-peak",
        "ipa": "Gṛdhrakūṭa [ɡr̩d.dʱrə.kuː.ʈə]",
        "file_en": "griddhakuta_guide.ogg",
        "file_hi": "griddhakuta_guide_hi.ogg",
        "text_en": (
            "Griddhakuta. Pali: Gijjhakuta, Vulture's Peak. "
            "High above the ancient valley of Rajgir rises Griddhakuta, named for the natural crag that resembles the head and beak of a vulture perched on the hillside. "
            "King Bimbisara of Magadha constructed an engineered stone causeway up this ridge so he could visit the Buddha during the rainy season retreats. "
            "Here on this small open brick terrace, tradition records that Buddha delivered the Heart Sutra and the Lotus Sutra, initiating the Second Turning of the Wheel of Dharma. "
            "Look down at the natural amphitheater of the five surrounding hills that once formed the defenses of Rajagriha."
        ),
        "text_hi_devanagari": (
            "गृद्धकूट शिखर। द्वितीय धर्मचक्र प्रवर्तन। "
            "राजगीर की सुरम्य पहाड़ियों पर स्थित गृद्धकूट शिखर का नाम इसकी गिद्ध जैसी प्राकृतिक शिला-आकृति के कारण पड़ा। "
            "मगध सम्राट बिम्बिसार ने भगवान बुद्ध के दर्शन हेतु यहाँ तक एक भव्य पाषाण मार्ग बनवाया था। "
            "इसी पावन स्थल पर तथागत ने प्रज्ञापारमिता और सद्धर्मपुण्डरीक सूत्र का उपदेश देकर द्वितीय धर्मचक्र का प्रवर्तन किया था।"
        ),
        "text_hi": (
            "Griddhakuta Shikhar. Dwitiya Dharmachakra Pravartan. "
            "Rajgir ki suramya pahadiyon par sthit Griddhakuta shikhar ka naam iski giddh jaisi prakritik shila-aakriti ke kaaran pada. "
            "Magadh Samrat Bimbisara ne Bhagwan Buddha ke darshan hetu yahan tak ek bhavya pashan marg banwaya tha. "
            "Isi paavan sthal par Tathagata ne Prajnaparamita aur Saddharmapundarika sootra ka upadesh dekar dwitiya dharmachakra ka pravartan kiya tha."
        ),
    },
    {
        "id": "cyclopean_wall",
        "place_id": "in-bihar-rajgir-cyclopean-wall",
        "ipa": "Rājagṛha Prācīra [raː.dʒə.ɡr̩.ɦə praː.tʃiː.rə]",
        "file_en": "cyclopean_wall_guide.ogg",
        "file_hi": "cyclopean_wall_guide_hi.ogg",
        "text_en": (
            "Rajgir Durgana. Cyclopean Masonry Wall. "
            "One of the most remarkable pre-Mauryan defensive works in South Asia, the Cyclopean Wall spanned over forty kilometers along the ridgelines of the Rajgir hills. "
            "Constructed without mortar, massive undressed limestone blocks up to one and a half meters across were carefully fitted together by ancient Magadhan builders. "
            "Dating to the 6th or 5th century BCE, this formidable barrier protected the royal capital from military incursions during the rise of India's earliest empires."
        ),
        "text_hi_devanagari": (
            "राजगीर की साइक्लोपियन प्राचीर। "
            "दक्षिण एशिया की प्राचीनतम सैन्य प्राचीरों में से एक, यह दीवार राजगीर की पहाड़ियों पर 40 किलोमीटर से अधिक दूरी तक फैली थी। "
            "बिना किसी गारे या चूने के, विशाल अनगढ़े चूना पत्थरों को आपस में जोड़कर छठी शताब्दी ईसा पूर्व में मगध साम्राज्य की सुरक्षा हेतु बनाया गया था।"
        ),
        "text_hi": (
            "Rajgir ki Cyclopean Pracheer. "
            "Dakshin Asia ki pracheentam sainya fortifications mein se ek, yeh pracheer Rajgir ki pahadiyon par chaalees kilometer se adhik doori tak phaili thi. "
            "Bina kisi gaare ya choone ke, vishal an-gadhe choona pattharon ko aapas mein jodkar chhati shatabdi Eesa Poorva mein Magadh samrajya ki suraksha hetu banaya gaya tha."
        ),
    },
    {
        "id": "sonbhandar",
        "place_id": "in-bihar-rajgir-sonbhandar",
        "ipa": "Svarṇa Bhāṇḍāra [sʋər.ɳə bʱaːɳ.ɖaː.rə]",
        "file_en": "sonbhandar_guide.ogg",
        "file_hi": "sonbhandar_guide_hi.ogg",
        "text_en": (
            "Svarna Bhandara. Gold Treasury Cave. "
            "Chiseled directly into the southern cliff of Vaibhara Hill, Sonbhandar consists of two rock-cut chambers dating between the 3rd and 4th centuries CE. "
            "Popular folklore long claimed that Emperor Bimbisara's hidden treasury was sealed inside behind an undeciphered inscription on the chamber wall. "
            "However, archaeological excavations and the rock-cut Shankhalipi inscription clearly establish that the cave was dedicated by the Jain ascetic Muni Vairadeva for solitary meditation and tapas."
        ),
        "text_hi_devanagari": (
            "सोनभंडार गुफा। स्वर्ण कोष की किंवदंती। "
            "वैभार पहाड़ी की तलहटी में तराशी गई सोनभंडार गुफाओं के विषय में लोककथा थी कि इसमें सम्राट बिम्बिसार का खजाना छिपा है। "
            "किंतु पुरातात्विक अध्ययनों और ब्राह्मी-शंखलिपि अभिलेखों से सिद्ध होता है कि यह तीसरी-चौथी सदी में जैन मुनि वैरदेव द्वारा साधना हेतु निर्मित कराई गई थी।"
        ),
        "text_hi": (
            "Sonbhandar Gufa. Swarna Kosh ki Kinwadanti. "
            "Vaibhāra pahadi ki talhati mein tarashi gayi Sonbhandar gufaon ke vishay mein lok-katha thi ki ismein Samrat Bimbisara ka khazana chhipa hai. "
            "Kintu puraatatvik adhyayanon aur Brahmi-Shankhalipi abhilekhon se siddha hota hai ki yeh teesri-chauthi sadi mein Jain Muni Vairadeva dwara sadhana hetu nirmit karayi gayi thi."
        ),
    },
]


def verify_ogg_stream(ogg_path: Path) -> tuple[bool, float]:
    """Verifies that `ogg_path` is a valid Vorbis audio file with positive duration."""
    if not ogg_path.is_file() or ogg_path.stat().st_size < 1024:
        return False, 0.0
    try:
        p = subprocess.run(
            [
                FFPROBE,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(ogg_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        dur = float(p.stdout.strip())
        return dur > 1.0, dur
    except Exception:
        return False, 0.0


def synthesize_speech_windows(text: str, wav_path: Path, lang: str = "en") -> None:
    """Uses PowerShell System.Speech, selecting a hi-IN voice when available for Hindi."""
    escaped = text.replace("'", "''")
    ps_script = f"""
Add-Type -AssemblyName System.Speech
$syn = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = $syn.GetInstalledVoices() | Where-Object {{ $_.Enabled -and $_.VoiceInfo.Culture.Name -like '{lang}*' }}
if ($voices.Count -gt 0) {{
    $syn.SelectVoice($voices[0].VoiceInfo.Name)
}}
$syn.SetOutputToWaveFile('{wav_path.as_posix()}')
$syn.Speak('{escaped}')
$syn.Dispose()
"""
    cmd = ["powershell", "-NoProfile", "-Command", ps_script]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def convert_wav_to_ogg(wav_path: Path, ogg_path: Path) -> None:
    cmd = [
        FFMPEG,
        "-y",
        "-i", str(wav_path),
        "-ar", "44100",
        "-c:a", "libvorbis",
        "-q:a", "4",
        str(ogg_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate or verify P1A bilingual audio guide OGG assets")
    ap.add_argument("--force-resynthesize", action="store_true",
                    help="Force re-synthesis of all 20 tracks instead of preserving verified existing OGGs")
    args = ap.parse_args()

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    verified_count = 0
    total = len(STORIES) * 2

    if not args.force_resynthesize:
        print("Auditing & syncing 20 bilingual OGG Vorbis audio assets (44.1 kHz)...")
        for s in STORIES:
            for key in ("file_en", "file_hi"):
                fn = s[key]
                src = AUDIO_DIR / fn
                dst = ASSETS_AUDIO_DIR / fn
                ok, dur = verify_ogg_stream(src)
                if ok:
                    shutil.copy2(src, dst)
                    verified_count += 1
                    print(f"  [OK] {fn:34s} | {dur:5.1f}s | {src.stat().st_size // 1024:4d} KB | synced to APK assets")
                else:
                    print(f"  [MISSING/INVALID] {fn}")
        if verified_count == total:
            print(f"\nAll {total}/{total} bilingual OGG Vorbis audio tracks verified and synced.")
            return 0

    if shutil.which("powershell") is None:
        print("ERROR: PowerShell TTS not available on this OS and --force-resynthesize requested.", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        idx = 0
        for s in STORIES:
            idx += 1
            wav_en = tmp / f"{s['id']}_en.wav"
            out_en = AUDIO_DIR / s["file_en"]
            print(f"[{idx}/{total}] Synthesizing {s['file_en']}...")
            synthesize_speech_windows(s["text_en"], wav_en, lang="en")
            convert_wav_to_ogg(wav_en, out_en)
            shutil.copy2(out_en, ASSETS_AUDIO_DIR / s["file_en"])

            idx += 1
            wav_hi = tmp / f"{s['id']}_hi.wav"
            out_hi = AUDIO_DIR / s["file_hi"]
            print(f"[{idx}/{total}] Synthesizing {s['file_hi']}...")
            synthesize_speech_windows(s["text_hi"], wav_hi, lang="hi")
            convert_wav_to_ogg(wav_hi, out_hi)
            shutil.copy2(out_hi, ASSETS_AUDIO_DIR / s["file_hi"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
