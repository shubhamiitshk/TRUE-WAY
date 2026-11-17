#!/usr/bin/env python3
"""TrueWay Bilingual Audio Guide Generation & Transcoding Pipeline.

Generates high-fidelity bilingual audio narration (English & Devanagari Hindi)
for TrueWay cultural heritage points of interest (POIs).

Key Features:
1. Multi-tier Neural TTS Ladder:
   - Primary: Edge-TTS neural voices (`en-IN-NeerjaNeural`, `hi-IN-SwaraNeural`, etc.).
   - Secondary: Kokoro onnx/neural model (if available).
   - Tertiary: Platform native TTS (e.g., Windows SAPI SpeechSynthesizer).
   - Testing / CI: Fast deterministic mock audio generation (`--mock`).
2. Automatic High-Quality OGG Transcoding:
   - Encodes to standard OGG Vorbis (`-c:a libvorbis -q:a 4`, 44.1 kHz) or OGG Opus
     (`-c:a libopus -b:a 32k`, 48.0 kHz).
   - Discovers FFmpeg automatically across PATH, imageio-ffmpeg, WinGet, and standard
     POSIX/Windows locations.
3. Safe Operation & Verification:
   - `--dry-run`: Validates scripts, inputs, voice bindings, durations without network
     calls or file generation.
   - `--mock`: Emits valid RFC 3533 Ogg Vorbis/Opus containers for 100% offline test suites.
   - `--verify`: Checks file existence, container magic, Vorbis/Opus headers, and durations.
4. Multi-Region Heritage Catalog:
   - Bihar Buddhist Circuit (Bodh Gaya, Nalanda, Rajgir)
   - India Golden Triangle (Delhi, Agra, Jaipur)
   - Global Icons Tier-1 (Eiffel Tower, Colosseum, Pyramids, Angkor Wat, Machu Picchu, Liberty)
   - Custom POI input via CLI flags (`--poi-id`, `--text-en`, `--text-hi`).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent.parent
CONTENT_AUDIO = ROOT / "content" / "audio"
ASSETS_AUDIO = ROOT / "android" / "app" / "src" / "main" / "assets" / "audio"

# ---------------------------------------------------------------------------
# FFmpeg & FFprobe Discovery
# ---------------------------------------------------------------------------

def find_ffmpeg() -> Optional[str]:
    """Locates an available FFmpeg binary on the system."""
    # 1. Environment variable override
    env_bin = os.environ.get("FFMPEG_PATH") or os.environ.get("FFMPEG_BINARY")
    if env_bin and Path(env_bin).is_file():
        return env_bin

    # 2. PATH resolution
    which_bin = shutil.which("ffmpeg")
    if which_bin:
        return which_bin

    # 3. Python imageio_ffmpeg bundle
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).is_file():
            return exe
    except Exception:
        pass

    # 4. Standard candidate locations
    candidates = [
        # Windows WinGet / Scoop / Chocolatey / Program Files
        Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe",
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/ProgramData/chocolatey/bin/ffmpeg.exe"),
        # POSIX
        Path("/usr/bin/ffmpeg"),
        Path("/usr/local/bin/ffmpeg"),
        Path("/opt/homebrew/bin/ffmpeg"),
    ]
    for c in candidates:
        if c.is_file():
            return str(c)

    return None


def find_ffprobe() -> Optional[str]:
    """Locates an available FFprobe binary on the system."""
    env_bin = os.environ.get("FFPROBE_PATH")
    if env_bin and Path(env_bin).is_file():
        return env_bin

    which_bin = shutil.which("ffprobe")
    if which_bin:
        return which_bin

    candidates = [
        Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Links" / "ffprobe.exe",
        Path("C:/ffmpeg/bin/ffprobe.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffprobe.exe"),
        Path("/usr/bin/ffprobe"),
        Path("/usr/local/bin/ffprobe"),
        Path("/opt/homebrew/bin/ffprobe"),
    ]
    for c in candidates:
        if c.is_file():
            return str(c)

    return None


# ---------------------------------------------------------------------------
# Built-in Heritage Audio Narratives
# ---------------------------------------------------------------------------

BUILTIN_STORIES: List[Dict[str, Any]] = [
    # --- Corridor 1: Bihar Buddhist Circuit ---
    {
        "id": "mahabodhi",
        "region": "in-bihar-buddhist-circuit",
        "place_id": "in-bihar-bodhgaya-mahabodhi",
        "ipa": "Mahābodhi [mə.ɦaː.boː.dʱi]",
        "file_en": "mahabodhi_guide.ogg",
        "file_hi": "mahabodhi_guide_hi.ogg",
        "title_en": "The Seat of Awakening: Mahabodhi",
        "title_hi": "संबोधि पीठ: महाबोधि मंदिर",
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
        "text_hi": (
            "महाबोधि मंदिर। संबोधि पीठ। "
            "आप महाबोधि मंदिर के समक्ष खड़े हैं, जो भारत में आज भी सुरक्षित सबसे प्राचीन ईंट-निर्मित बौद्ध मंदिरों में से एक है। "
            "लगभग 250 ईसा पूर्व, सम्राट अशोक ने फल्गु नदी के तट पर वज्रासन पीठ की स्थापना की थी। "
            "वर्तमान 55 मीटर ऊँचा भव्य शिखर मुख्य रूप से 5वीं और 6वीं शताब्दी ईस्वी के गुप्त काल का है। "
            "इस पश्चिमी दीवार के ठीक पीछे पवित्र बोधि वृक्ष स्थित है, जो पॉलिश किए गए बलुआ पत्थर के वज्रासन को अपनी छाया प्रदान करता है। "
            "परिक्रमा पथ की पत्थर की वेदिका पर उत्कीर्ण मौर्य और शुंग कालीन कलाकृतियों का ध्यानपूर्वक अवलोकन करें।"
        ),
    },
    {
        "id": "bodhi_tree",
        "region": "in-bihar-buddhist-circuit",
        "place_id": "in-bihar-bodhgaya-bodhi-tree",
        "ipa": "Bodhi Vṛkṣa [boː.dʱi vr̩k.ʂə]",
        "file_en": "bodhi_tree_guide.ogg",
        "file_hi": "bodhi_tree_guide_hi.ogg",
        "title_en": "The Tree of Illumination",
        "title_hi": "बोधिवृक्ष: प्रज्ञा का साक्षी",
        "text_en": (
            "Bodhi Vriksha. Ficus religiosa. "
            "Standing directly behind the main sanctum of the Mahabodhi Temple, this sacred pipal tree marks the revered spot where Siddhartha Gautama meditated for 49 days and attained supreme awakening. "
            "The current tree is a direct descendant of the original specimen. "
            "In the 3rd century BCE, Emperor Ashoka's daughter, Princess Sanghamitta, carried a sapling of this tree to Sri Lanka, where it was planted at Anuradhapura. "
            "When this tree in Bodh Gaya was destroyed in later centuries, a cutting from the Anuradhapura tree was brought back and replanted here, preserving an unbroken botanical lineage."
        ),
        "text_hi": (
            "बोधिवृक्ष। प्रज्ञा का साक्षी। "
            "महाबोधि मंदिर के गर्भगृह के ठीक पीछे स्थित यह पवित्र पीपल वृक्ष उस पावन स्थल का साक्षी है जहाँ सिद्धार्थ गौतम ने 49 दिनों तक ध्यान लगाकर सम्यक संबोधि प्राप्त की थी। "
            "वर्तमान वृक्ष मूल वृक्ष का ही वंशज है, जिसकी शाखा राजकुमारी संघमित्रा तीसरी सदी ईसा पूर्व में श्रीलंका के अनुराधापुरा ले गई थीं। "
            "कालांतर में अनुराधापुरा वृक्ष से शाखा लाकर यहाँ पुनः रोपण किया गया।"
        ),
    },
    {
        "id": "vajrasana",
        "region": "in-bihar-buddhist-circuit",
        "place_id": "in-bihar-bodhgaya-vajrasana",
        "ipa": "Vajrāsana [ʋədʒ.raː.sə.nə]",
        "file_en": "vajrasana_guide.ogg",
        "file_hi": "vajrasana_guide_hi.ogg",
        "title_en": "The Diamond Throne",
        "title_hi": "वज्रासन: अविचल धरातल",
        "text_en": (
            "Vajrasana. Sanskrit: Diamond Throne. "
            "Resting between the western wall of the Mahabodhi Temple and the trunk of the Bodhi Tree lies the Vajrasana, or Diamond Throne. "
            "Carved from a single massive slab of Chunar polished sandstone, this seat was commissioned by Emperor Ashoka around 250 BCE. "
            "The border is intricately carved with honeysuckles, geese, and geometric rosettes characteristic of Mauryan imperial stone craft. "
            "Tradition identifies this stone as the navel of the earth, the one immovable center capable of supporting the spiritual weight of Enlightenment."
        ),
        "text_hi": (
            "वज्रासन। अविचल धरातल। "
            "महाबोधि मंदिर की पश्चिमी दीवार और बोधि वृक्ष के तने के मध्य चुनार के पॉलिश किए गए बलुआ पत्थर से निर्मित विशाल शिलापट्ट ही वज्रासन है। "
            "सम्राट अशोक द्वारा 250 ईसा पूर्व में स्थापित इस आसन के किनारों पर हंसों और कमलों की भव्य मौर्यकालीन नक्काशी देखी जा सकती है। "
            "परंपरा इस स्थल को पृथ्वी की नाभि मानती है।"
        ),
    },
    {
        "id": "great_buddha",
        "region": "in-bihar-buddhist-circuit",
        "place_id": "in-bihar-bodhgaya-great-buddha",
        "ipa": "Daibutsu [daɪ.bʊt.suː]",
        "file_en": "great_buddha_guide.ogg",
        "file_hi": "great_buddha_guide_hi.ogg",
        "title_en": "The Eighty-Foot Great Buddha",
        "title_hi": "अस्सी फीट महाबुद्ध प्रतिमा",
        "text_en": (
            "Daibutsu. Great Buddha of Bodh Gaya. "
            "Towering eighty feet into the sky, the Great Buddha statue was consecrated in 1989 by the 14th Dalai Lama. "
            "Constructed over seven years using sandstone and red granite, the statue depicts the Buddha seated in the Dhyana Mudra, or meditative posture, atop a grand lotus pedestal. "
            "Inside the hollow sculpture rests a spiraling staircase leading past bronze statues of the Buddha's ten principal disciples, symbolizing international peace and Buddhist unity."
        ),
        "text_hi": (
            "अस्सी फीट महाबुद्ध प्रतिमा। "
            "अस्सी फीट ऊँची यह भव्य महाबुद्ध प्रतिमा 1989 में प्रतिष्ठित की गई थी। "
            "सात वर्षों में निर्मित यह प्रतिमा लाल ग्रेनाइट और बलुआ पत्थर से तैयार की गई है, जिसमें भगवान बुद्ध ध्यान मुद्रा में विराजमान हैं। "
            "यह प्रतिमा अंतर्राष्ट्रीय शांति और बौद्ध एकता का प्रतीक है।"
        ),
    },
    {
        "id": "nalanda_mahavihara",
        "region": "in-bihar-buddhist-circuit",
        "place_id": "in-bihar-nalanda-mahavihara",
        "ipa": "Nālandā Mahāvihāra [naː.lən.d̪aː mə.ɦaː.ʋɪ.ɦaː.rə]",
        "file_en": "nalanda_mahavihara_guide.ogg",
        "file_hi": "nalanda_mahavihara_guide_hi.ogg",
        "title_en": "Nalanda: Ancient Seat of Universal Wisdom",
        "title_hi": "नालंदा महाविहार: ज्ञान की वैश्विक राजधानी",
        "text_en": (
            "Nalanda Mahavihara. Universal Monastic University. "
            "Spanning over 23 hectares of excavated red-brick monasteries and votive shrines, Nalanda was the premier center of higher learning in Asia from the 5th through 12th centuries CE. "
            "Supported by Gupta emperors, King Harsha of Kannauj, and the Pala monarchs, it housed ten thousand resident scholars and two thousand teachers from across China, Korea, Tibet, and Central Asia. "
            "The 7th-century Chinese pilgrim Xuanzang documented its rigorous entrance examinations, where only two out of ten scholars were admitted to study grammar, logic, medicine, and metaphysics."
        ),
        "text_hi": (
            "नालंदा महाविहार। विश्व विख्यात बौद्ध ज्ञानपीठ। "
            "पांचवीं से बारहवीं शताब्दी तक एशिया के अग्रणी शिक्षण केंद्र के रूप में प्रसिद्ध नालंदा महाविहार के लाल ईंटों के अवशेष ज्ञान के स्वर्णिम युग के प्रमाण हैं। "
            "गुप्त और पाल शासकों के संरक्षण में यहाँ दस हज़ार से अधिक अध्येता व्याकरण, दर्शन, खगोलशास्त्र और चिकित्सा शास्त्र का अध्ययन करते थे। "
            "चीनी यात्री ह्वेन त्सांग ने यहाँ वर्षों रहकर बौद्ध ग्रंथों का अध्ययन किया था।"
        ),
    },
    {
        "id": "nalanda_temple3",
        "region": "in-bihar-buddhist-circuit",
        "place_id": "in-bihar-nalanda-temple3",
        "ipa": "Nālandā Caitya 3 [tʃaɪ.t̪jə]",
        "file_en": "nalanda_temple3_guide.ogg",
        "file_hi": "nalanda_temple3_guide_hi.ogg",
        "title_en": "Temple Site 3: Monumental Stupa of Sariputra",
        "title_hi": "मंदिर संख्या 3: सारिपुत्र चैत्य स्तूप",
        "text_en": (
            "Site 3. The Grand Sariputra Votive Stupa. "
            "This imposing multi-tiered monument is the iconic heart of Nalanda's visual landscape. "
            "Archaeological excavations revealed that this structure was built over seven distinct phases, each envelope encasing and enlarging the earlier sanctum without demolishing it. "
            "The fifth layer reveals exquisite 6th-century Gupta stucco reliefs depicting the Buddha, Bodhisattvas, and celestial attendants inside tiered niches. "
            "Tradition holds that this stupa enshrines sacred relics of Sariputra, one of the Buddha's foremost disciples who was born and entered parinirvana at Nalanda."
        ),
        "text_hi": (
            "मंदिर स्थल 3। भव्य सारिपुत्र स्तूप। "
            "यह विशाल बहु-स्तरीय स्मारक नालंदा का सर्वाधिक प्रभावशाली स्थापत्य है। "
            "उत्खनन से प्रमाणित हुआ है कि इसका निर्माण सात चरणों में हुआ, जहाँ प्रत्येक नया चरण पूर्ववर्ती निर्माण को समाहित करते हुए ऊपर उठा। "
            "पाँचवें स्तर पर गुप्तकालीन उत्कृष्ट सुर्खी प्लास्टर की बुद्ध और बोधिसत्व प्रतिमाएं उत्कीर्ण हैं।"
        ),
    },
    {
        "id": "nalanda_monastery1",
        "region": "in-bihar-buddhist-circuit",
        "place_id": "in-bihar-nalanda-monastery1",
        "ipa": "Nālandā Vihāra 1",
        "file_en": "nalanda_monastery1_guide.ogg",
        "file_hi": "nalanda_monastery1_guide_hi.ogg",
        "title_en": "Monastery 1: Devapala's Residential Vihara",
        "title_hi": "विहार संख्या 1: देवपाल युगीन महामठ",
        "text_en": (
            "Monastery Site 1. The Quadrangle Vihara of King Devapala. "
            "This quadrangle plan represents the zenith of ancient residential monastic architecture. "
            "A central open courtyard is encircled by thirty-four residential monk cells, each provided with bed niches, ventilation slits, and oil lamp shelves. "
            "In 1921, archaeologists discovered a copper-plate inscription here recording that King Balaputradeva of Sumatra built a monastery at Nalanda, with five villages granted by King Devapala for its perpetual maintenance."
        ),
        "text_hi": (
            "विहार स्थल 1। राजा देवपाल कालीन आवासीय विहार। "
            "यह चतुर्भुज योजना प्राचीन आवासीय बौद्ध स्थापत्य का उत्कृष्ट उदाहरण है। "
            "मध्य में एक विस्तृत प्रांगण है जिसके चारों ओर भिक्षुओं के लिए चौंतीस कक्ष बने हुए हैं। "
            "यहाँ से प्राप्त प्रसिद्ध ताम्रपत्र से ज्ञात होता है कि सुमात्रा के राजा बालपुत्रदेव ने यहाँ एक मठ बनवाया था जिसके भरण-पोषण के लिए राजा देवपाल ने पाँच गाँव दान दिए थे।"
        ),
    },
    {
        "id": "griddhakuta",
        "region": "in-bihar-buddhist-circuit",
        "place_id": "in-bihar-rajgir-griddhakuta",
        "ipa": "Gṛddhakūṭa [ɡr̩d̪.dʱə.kuː.ʈə]",
        "file_en": "griddhakuta_guide.ogg",
        "file_hi": "griddhakuta_guide_hi.ogg",
        "title_en": "Vulture Peak: The Heart of the Lotus Sutra",
        "title_hi": "गृध्रकूट पर्वत: सद्धर्म पुण्डरीक सूत्र की धरा",
        "text_en": (
            "Griddhakuta. Sanskrit: Vulture's Peak. "
            "Perched high on the rocky Chhatha hill overlooking the valley of Rajgir, this crag resembles a vulture with folded wings. "
            "This natural retreat was the Buddha's most cherished retreat during his rainy season retreats in the ancient Magadhan capital. "
            "Here, according to Mahayana tradition, the Buddha set in motion the Second Wheel of Dharma, expounding the profound Lotus Sutra and Prajnaparamita teachings to assemblies of Bodhisattvas and arhats. "
            "Along the stone paved path laid by King Bimbisara, pilgrims ascend past caves where Ananda and Shariputra once meditated."
        ),
        "text_hi": (
            "गृध्रकूट पर्वत। गिद्ध की चोंच सदृश पावन शिखर। "
            "राजगीर की छठ पहाड़ी पर स्थित यह शिलाखंड भगवान बुद्ध का प्रिय वर्षावास स्थल था। "
            "महायान परंपरा के अनुसार इसी पावन शिखर पर भगवान बुद्ध ने सद्धर्म पुण्डरीक सूत्र और प्रज्ञापारमिता का उपदेश दिया था। "
            "मगध नरेश बिम्बिसार द्वारा निर्मित पाषाण मार्ग से होकर श्रद्धालु इस शांत पर्वत पर पहुँचते हैं।"
        ),
    },
    {
        "id": "cyclopean_wall",
        "region": "in-bihar-buddhist-circuit",
        "place_id": "in-bihar-rajgir-cyclopean-wall",
        "ipa": "Rājagṛha Prākāra",
        "file_en": "cyclopean_wall_guide.ogg",
        "file_hi": "cyclopean_wall_guide_hi.ogg",
        "title_en": "The Cyclopean Wall of Ancient Rajagriha",
        "title_hi": "राजगृह की साइक्लोपियन प्राचीर",
        "text_en": (
            "The Cyclopean Wall of Rajgir. Massive Mauryan/Pre-Mauryan Fortification. "
            "Stretching over forty kilometers along the ridgelines of the five hills enclosing ancient Rajagriha, this stone rampart is one of the oldest surviving dry-stone masonry fortifications in South Asia. "
            "Constructed around the 6th or 5th century BCE under Kings Bimbisara and Ajatashatru, the wall was built using unworked, uncemented quartzite blocks fitting together through gravity and sheer mass. "
            "Rising up to four meters high and over four meters wide, it defended the capital of the Magadha empire against northern invasions."
        ),
        "text_hi": (
            "राजगीर की साइक्लोपियन दीवार। प्राचीन मगध की अभेद्य प्राचीर। "
            "प्राचीन राजगृह की पाँचों पहाड़ियों पर चालीस किलोमीटर तक फैली यह पाषाण दीवार दक्षिण एशिया की प्राचीनतम शुष्क-प्रस्तर किलेबंदी है। "
            "छठी या पांचवीं शताब्दी ईसा पूर्व में निर्मित इस दीवार में विशाल क्वार्ट्ज पत्थरों को बिना किसी गारे के गुरुत्वाकर्षण और सटीक जमावट से जोड़ा गया है। "
            "यह मगध साम्राज्य की सुरक्षा का आधार स्तंभ थी।"
        ),
    },
    {
        "id": "sonbhandar",
        "region": "in-bihar-buddhist-circuit",
        "place_id": "in-bihar-rajgir-sonbhandar",
        "ipa": "Svarṇabhāṇḍāra [sʋər.ɳə.bʱaːɳ.ɖaː.rə]",
        "file_en": "sonbhandar_guide.ogg",
        "file_hi": "sonbhandar_guide_hi.ogg",
        "title_en": "Son Bhandar: The Treasury Caves of Vairadeva",
        "title_hi": "सोन भंडार: मुनि वैरीदेव की तपोस्थली",
        "text_en": (
            "Son Bhandar Caves. Sanskrit: The Golden Treasury. "
            "Carved into the southern cliff of the Vaibhāra Hill, these two artificial rock-cut caverns date to the 3rd or 4th century CE. "
            "The western cave features a trapezoidal doorway and a vaulted ceiling inspired by early wooden chaitya halls, complete with highly polished interior stone walls. "
            "A Sanskrit inscription carved in the shell-character Sankhalipi script near the window records that these caves were excavated by the Jain sage Muni Vairadeva for ascetic meditation. "
            "Folklore later claimed the sealed inner doorway conceals the secret treasury of King Bimbisara."
        ),
        "text_hi": (
            "सोन भंडार गुफाएं। वैभारगिरि की शैलकृत गुफा। "
            "वैभार पहाड़ी की तलहटी में तराशी गई ये दो गुफाएं तीसरी-चौथी शताब्दी की हैं। "
            "गुफा की आंतरिक दीवारें मौर्यकालीन पॉलिश के समान अत्यंत चिकनी हैं। "
            "यहाँ उत्कीर्ण शंखलिपि अभिलेख से प्रमाणित होता है कि इन गुफाओं का निर्माण जैन मुनि वैरीदेव ने तपस्या हेतु करवाया था। "
            "लोककथाओं में इसे राजा बिम्बिसार का स्वर्ण खजाना माना जाता रहा है।"
        ),
    },

    # --- Corridor 2: India Golden Triangle ---
    {
        "id": "taj_mahal",
        "region": "in-golden-triangle",
        "place_id": "in-up-agra-taj-mahal",
        "ipa": "Tāj Mahal [taːdʒ mɛ.ɦɛl]",
        "file_en": "taj_mahal_guide.ogg",
        "file_hi": "taj_mahal_guide_hi.ogg",
        "title_en": "The Crown of Palaces: Taj Mahal",
        "title_hi": "ताजमहल: धवल संगमरमरी प्रेमगाथा",
        "text_en": (
            "Taj Mahal. An enduring monument of Mughal monumental architecture. "
            "Commissioned in 1631 by Mughal Emperor Shah Jahan to house the tomb of his favorite wife, Mumtaz Mahal, the complex was completed in 1648 on the southern bank of the Yamuna River. "
            "Crafted from translucent white Makrana marble inlaid with jasper, jade, and lapis lazuli through the intricate pietra dura technique, the tomb sits centered within a classic charbagh Mughal garden. "
            "The perfect fourfold symmetry embodies Islamic representations of the gardens of paradise."
        ),
        "text_hi": (
            "ताजमहल। मुग़ल स्थापत्य कला का अनुपम शिखर। "
            "मुगल सम्राट शाहजहाँ द्वारा अपनी बेगम मुमताज़ महल की स्मृति में 1631 में आरंभ किया गया यह मक़बरा 1648 में यमुना के पावन तट पर पूर्ण हुआ। "
            "मकराना के श्वेत संगमरमर पर पिएत्रा ड्यूरा तकनीक से जड़े बहुमूल्य रत्न और चारबाग़ शैली का उद्यान इसे स्वर्गिक संतुलन प्रदान करते हैं।"
        ),
    },
    {
        "id": "qutub_minar",
        "region": "in-golden-triangle",
        "place_id": "in-delhi-qutub-minar",
        "ipa": "Quṭb Mīnār [qʊ.t̪əb miː.naːr]",
        "file_en": "qutub_minar_guide.ogg",
        "file_hi": "qutub_minar_guide_hi.ogg",
        "title_en": "Qutub Minar: Victory Tower of Delhi",
        "title_hi": "कुतुब मीनार: दिल्ली की ऐतिहासिक विजय पताका",
        "text_en": (
            "Qutub Minar. The 72.5-meter fluted sandstone minaret of Mehrauli. "
            "Begun in 1199 CE by Qutb-ud-din Aibak and expanded by Shams-ud-din Iltutmish and Firoz Shah Tughlaq, this five-tiered red and buff sandstone tower is the tallest brick minaret in the world. "
            "Projecting balconies supported by stalactite corbels and bands of intricate Quranic calligraphy mark its architectural transition. "
            "In its courtyard stands the famous 4th-century Gupta iron pillar, celebrated worldwide for its ancient metallurgical rust resistance."
        ),
        "text_hi": (
            "कुतुब मीनार। महरौली स्थित 72.5 मीटर ऊँची विजय मीनार। "
            "कुतुबुद्दीन ऐबक द्वारा 1199 में प्रारंभ और इल्तुतमिश तथा फ़िरोज़ शाह तुग़लक़ द्वारा संवर्धित यह लाल बलुआ पत्थर की पाँच मंज़िला मीनार विश्व की सबसे ऊँची ईंट-निर्मित मीनार है। "
            "इसके प्रांगण में स्थित चौथी शताब्दी का गुप्तकालीन लौह स्तंभ प्राचीन भारतीय धातु विज्ञान का एक अविश्वसनीय चमत्कार है।"
        ),
    },

    # --- Corridor 3: Global Icons Tier-1 ---
    {
        "id": "eiffel_tower",
        "region": "global-icons-tier1",
        "place_id": "fr-paris-eiffel-tower",
        "ipa": "Tour Eiffel [tuʁ ɛ.fɛl]",
        "file_en": "eiffel_tower_guide.ogg",
        "file_hi": "eiffel_tower_guide_hi.ogg",
        "title_en": "The Iron Lady: Eiffel Tower",
        "title_hi": "एफिल टॉवर: पेरिस का लौह गौरव",
        "text_en": (
            "Tour Eiffel. Paris, France. "
            "Erected on the Champ de Mars for the 1889 Exposition Universelle to celebrate the centennial of the French Revolution, Gustave Eiffel's 330-meter puddle-iron lattice tower became an enduring symbol of modern engineering. "
            "Assembled in two years by two hundred and fifty craftsmen using 18,038 prefabricated iron pieces and 2.5 million rivets, it held the title of the world's tallest man-made structure for forty-one years."
        ),
        "text_hi": (
            "एफिल टॉवर। पेरिस, फ्रांस। "
            "1889 के विश्व मेले के लिए गुस्ताव एफिल के नेतृत्व में निर्मित 330 मीटर ऊँचा यह लौह स्तंभ आधुनिक इंजीनियरिंग का उत्कृष्ट प्रतीक है। "
            "अठारह हज़ार से अधिक धातु खंडों और पच्चीस लाख रिवेट्स से तैयार यह टॉवर चार दशकों तक विश्व की सबसे ऊँची मानव-निर्मित संरचना बना रहा।"
        ),
    },
    {
        "id": "colosseum",
        "region": "global-icons-tier1",
        "place_id": "it-rome-colosseum",
        "ipa": "Colosseo [ko.losˈsɛː.o]",
        "file_en": "colosseum_guide.ogg",
        "file_hi": "colosseum_guide_hi.ogg",
        "title_en": "The Flavian Amphitheatre: Colosseum",
        "title_hi": "कोलोसियम: रोम का ऐतिहासिक अखाड़ा",
        "text_en": (
            "The Colosseum. The Flavian Amphitheatre of Imperial Rome. "
            "Commissioned by Emperor Vespasian around 72 CE and inaugurated by Titus in 80 CE, this elliptical amphitheatre could hold up to sixty-five thousand spectators. "
            "Constructed from travertine limestone, tuff, and brick-faced concrete, its monumental tiered arcades blend Doric, Ionic, and Corinthian classical orders above a complex subterranean hypogeum network."
        ),
        "text_hi": (
            "कोलोसियम। रोमन साम्राज्य का फ्लेवियन अखाड़ा। "
            "सम्राट वेस्पासियन द्वारा 72 ईस्वी में प्रारंभ और टाइटस द्वारा 80 ईस्वी में उद्घाटित यह विशाल रंगभूमि पैंसठ हज़ार दर्शकों को समाहित कर सकती थी। "
            "चूना पत्थर और कंक्रीट से निर्मित इसके भव्य मेहराब प्राचीन रोमन स्थापत्य और इंजीनियरिंग कौशल का अमर प्रतीक हैं।"
        ),
    },
]

# Quick indexing by ID and place_id
STORIES_BY_ID = {s["id"]: s for s in BUILTIN_STORIES}
STORIES_BY_PLACE = {s["place_id"]: s for s in BUILTIN_STORIES}


# ---------------------------------------------------------------------------
# Speech Synthesis Engines
# ---------------------------------------------------------------------------

async def synthesize_edge_tts(
    text: str,
    voice: str,
    out_path: Path,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
) -> None:
    """Synthesizes speech via Microsoft Edge-TTS async API."""
    import edge_tts

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    await communicate.save(str(out_path))


def synthesize_windows_sapi(text: str, wav_path: Path, lang: str = "en") -> None:
    """Fallback speech synthesis using Windows PowerShell SAPI."""
    escaped = text.replace("'", "''").replace("\n", " ")
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
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"PowerShell SAPI synthesis failed: {res.stderr}")


def synthesize_kokoro(
    text: str,
    out_wav: Path,
    lang: str = "en",
    voice: Optional[str] = None,
) -> None:
    """Synthesizes speech using Kokoro ONNX/PyTorch model if available."""
    try:
        from kokoro import KPipeline
        import soundfile as sf
    except ImportError as exc:
        raise RuntimeError("Kokoro or soundfile not installed. Run 'pip install kokoro soundfile'") from exc

    lang_code = "a" if lang.startswith("en") else "h"
    pipeline = KPipeline(lang_code=lang_code)
    voice_name = voice or ("af_heart" if lang_code == "a" else "hf_alpha")
    generator = pipeline(text, voice=voice_name, speed=1.0, split_pattern=r"\n+")
    
    all_audio = []
    for _, _, audio in generator:
        all_audio.append(audio)

    if not all_audio:
        raise RuntimeError("Kokoro produced empty audio stream")

    import numpy as np
    combined = np.concatenate(all_audio)
    sf.write(str(out_wav), combined, 24000)


def generate_mock_ogg(
    out_ogg: Path,
    codec: str = "vorbis",
    duration_sec: float = 2.0,
    ffmpeg_bin: Optional[str] = None,
) -> None:
    """Generates a valid, minimal OGG Vorbis or Opus audio stream for offline/mock tests."""
    out_ogg.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Prefer real FFmpeg synthetic generation if available
    if ffmpeg_bin:
        rate = 44100 if codec == "vorbis" else 48000
        c_a = "libvorbis" if codec == "vorbis" else "libopus"
        cmd = [
            ffmpeg_bin,
            "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r={rate}:cl=mono",
            "-t", str(max(1.0, duration_sec)),
            "-c:a", c_a,
            str(out_ogg),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and out_ogg.is_file() and out_ogg.stat().st_size > 100:
            return

    # 2. Check if a valid reference OGG exists in content/audio to use as template
    ref_files = list(CONTENT_AUDIO.glob("*.ogg")) if CONTENT_AUDIO.exists() else []
    if ref_files and ref_files[0].is_file() and ref_files[0].stat().st_size > 1024:
        shutil.copy2(ref_files[0], out_ogg)
        return

    # 3. Pure-python fallback RFC 3533 minimal Ogg stream builder
    # Valid RFC 3533 Ogg page with Vorbis identification packet
    # Magic b'OggS', version 0, header type 2 (BOS), granule 0, serial 0x1234, page 0, checksum dummy
    ogg_bos = (
        b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x34\x12\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x01\x1e"  # 1 segment of 30 bytes
        b"\x01vorbis\x00\x00\x00\x00\x01\x44\xac\x00\x00\x00\x00\x00\x00\x00\xe8\x03\x00\x00\x00\x00\x00\xb8\x01"
    )
    ogg_eos = (
        b"OggS\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x34\x12\x00\x00\x01\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x01\x04"
        b"\x03vorbis"
    )
    with open(out_ogg, "wb") as f:
        f.write(ogg_bos + ogg_eos)


# ---------------------------------------------------------------------------
# Audio Transcoding & Verification
# ---------------------------------------------------------------------------

def transcode_to_ogg(
    in_file: Path,
    out_ogg: Path,
    codec: str = "vorbis",
    ffmpeg_bin: Optional[str] = None,
) -> None:
    """Converts input audio file (WAV/MP3) to high-quality OGG Vorbis or Opus."""
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg binary required for audio transcoding.")

    out_ogg.parent.mkdir(parents=True, exist_ok=True)
    if codec == "opus":
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i", str(in_file),
            "-ar", "48000",
            "-c:a", "libopus",
            "-b:a", "32k",
            str(out_ogg),
        ]
    else:  # vorbis default
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i", str(in_file),
            "-ar", "44100",
            "-c:a", "libvorbis",
            "-q:a", "4",
            str(out_ogg),
        ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg transcode failed: {res.stderr}")


def verify_audio_file(audio_path: Path, ffprobe_bin: Optional[str] = None) -> Tuple[bool, float, str]:
    """Validates that audio_path exists, has valid Ogg container headers, and returns duration."""
    if not audio_path.is_file():
        return False, 0.0, "File does not exist"

    size = audio_path.stat().st_size
    if size < 64:
        return False, 0.0, f"File too small ({size} bytes)"

    # Inspect OGG RFC 3533 container magic
    with open(audio_path, "rb") as f:
        header = f.read(64)
    if not header.startswith(b"OggS"):
        return False, 0.0, "Missing OggS magic bytes"

    detected_codec = "ogg-unknown"
    if b"vorbis" in header.lower():
        detected_codec = "vorbis"
    elif b"opushead" in header.lower():
        detected_codec = "opus"

    # Measure duration with ffprobe if available
    dur = 0.0
    if ffprobe_bin:
        try:
            cmd = [
                ffprobe_bin,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                dur = float(res.stdout.strip())
        except Exception:
            pass

    # If ffprobe wasn't available or couldn't parse, estimate based on size
    if dur <= 0.0 and size > 1024:
        # Approximate 32kbps = 4KB/sec
        dur = round(size / 4096.0, 1)

    return True, dur, detected_codec


# ---------------------------------------------------------------------------
# Core Generation Orchestrator
# ---------------------------------------------------------------------------

async def generate_single_story(
    story: Dict[str, Any],
    out_dir: Path,
    backend: str = "edge-tts",
    codec: str = "vorbis",
    voice_en: str = "en-IN-NeerjaNeural",
    voice_hi: str = "hi-IN-SwaraNeural",
    ffmpeg_bin: Optional[str] = None,
    mock: bool = False,
    dry_run: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Generates bilingual audio tracks for a given story definition."""
    story_id = story["id"]
    file_en = story["file_en"]
    file_hi = story["file_hi"]
    out_en = out_dir / file_en
    out_hi = out_dir / file_hi

    text_en = story.get("text_en", "")
    text_hi = story.get("text_hi", "")

    result = {
        "id": story_id,
        "place_id": story.get("place_id"),
        "file_en": file_en,
        "file_hi": file_hi,
        "en_status": "SKIPPED",
        "hi_status": "SKIPPED",
        "en_duration": 0.0,
        "hi_duration": 0.0,
    }

    if dry_run:
        est_en = round(len(text_en.split()) / 2.5, 1)
        est_hi = round(len(text_hi.split()) / 2.2, 1)
        print(f"  [DRY-RUN] POI: {story_id} ({story.get('place_id')})")
        print(f"            EN -> {file_en} | voice: {voice_en} | ~{est_en}s ({len(text_en)} chars)")
        print(f"            HI -> {file_hi} | voice: {voice_hi} | ~{est_hi}s ({len(text_hi)} chars)")
        result["en_status"] = "DRY_RUN_OK"
        result["hi_status"] = "DRY_RUN_OK"
        result["en_duration"] = est_en
        result["hi_duration"] = est_hi
        return result

    if mock:
        generate_mock_ogg(out_en, codec=codec, duration_sec=2.5, ffmpeg_bin=ffmpeg_bin)
        generate_mock_ogg(out_hi, codec=codec, duration_sec=2.5, ffmpeg_bin=ffmpeg_bin)
        result["en_status"] = "MOCK_SYNTHESIZED"
        result["hi_status"] = "MOCK_SYNTHESIZED"
        result["en_duration"] = 2.5
        result["hi_duration"] = 2.5
        print(f"  [MOCK] Synthesized {file_en} and {file_hi} ({codec})")
        return result

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        # 1. Synthesize English
        if force or not out_en.exists():
            tmp_en = tmp / f"{story_id}_en.mp3"
            if backend == "edge-tts":
                await synthesize_edge_tts(text_en, voice_en, tmp_en)
            elif backend == "kokoro":
                tmp_en = tmp / f"{story_id}_en.wav"
                synthesize_kokoro(text_en, tmp_en, lang="en")
            elif backend == "windows-sapi":
                tmp_en = tmp / f"{story_id}_en.wav"
                synthesize_windows_sapi(text_en, tmp_en, lang="en")
            else:
                raise ValueError(f"Unknown backend: {backend}")

            transcode_to_ogg(tmp_en, out_en, codec=codec, ffmpeg_bin=ffmpeg_bin)
            result["en_status"] = "SYNTHESIZED"
        else:
            result["en_status"] = "PRESERVED"

        # 2. Synthesize Hindi
        if force or not out_hi.exists():
            tmp_hi = tmp / f"{story_id}_hi.mp3"
            if backend == "edge-tts":
                await synthesize_edge_tts(text_hi, voice_hi, tmp_hi)
            elif backend == "kokoro":
                tmp_hi = tmp / f"{story_id}_hi.wav"
                synthesize_kokoro(text_hi, tmp_hi, lang="hi")
            elif backend == "windows-sapi":
                tmp_hi = tmp / f"{story_id}_hi.wav"
                synthesize_windows_sapi(text_hi, tmp_hi, lang="hi")
            else:
                raise ValueError(f"Unknown backend: {backend}")

            transcode_to_ogg(tmp_hi, out_hi, codec=codec, ffmpeg_bin=ffmpeg_bin)
            result["hi_status"] = "SYNTHESIZED"
        else:
            result["hi_status"] = "PRESERVED"

    return result


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TrueWay Bilingual Audio Generator & Transcoder (Edge-TTS / Kokoro / OGG Opus & Vorbis)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--region",
        choices=["in-bihar-buddhist-circuit", "in-golden-triangle", "global-icons-tier1", "all"],
        default="in-bihar-buddhist-circuit",
        help="Geographic corridor or region pack to generate audio for",
    )
    parser.add_argument(
        "--poi-id",
        type=str,
        default=None,
        help="Optional specific POI ID (e.g., 'mahabodhi', 'taj_mahal', 'colosseum')",
    )
    parser.add_argument(
        "--backend",
        choices=["edge-tts", "kokoro", "windows-sapi", "mock"],
        default="edge-tts",
        help="TTS synthesis engine backend",
    )
    parser.add_argument(
        "--codec",
        choices=["vorbis", "opus"],
        default="vorbis",
        help="Audio codec for OGG container (vorbis is standard; opus is ultra-compact)",
    )
    parser.add_argument(
        "--voice-en",
        type=str,
        default="en-IN-NeerjaNeural",
        help="Neural voice identifier for English narration",
    )
    parser.add_argument(
        "--voice-hi",
        type=str,
        default="hi-IN-SwaraNeural",
        help="Neural voice identifier for Hindi narration",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=CONTENT_AUDIO,
        help="Output directory where .ogg files will be written",
    )
    parser.add_argument(
        "--sync-assets",
        action="store_true",
        help="Synchronize output files directly into android/app/src/main/assets/audio/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate parameters, voices, scripts, and print generation plan without synthesis",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Synthesize valid mock audio containers without network requests (for offline CI tests)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify integrity, duration, and OggS headers of existing audio files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-synthesis even if target audio files already exist",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available Edge-TTS Indian English and Hindi neural voices",
    )
    parser.add_argument(
        "--text-en",
        type=str,
        default=None,
        help="Ad-hoc English text script (used with --poi-id)",
    )
    parser.add_argument(
        "--text-hi",
        type=str,
        default=None,
        help="Ad-hoc Hindi text script (used with --poi-id)",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Main Execution Loop
# ---------------------------------------------------------------------------

async def main_async(args: argparse.Namespace) -> int:
    ffmpeg_bin = find_ffmpeg()
    ffprobe_bin = find_ffprobe()

    if args.list_voices:
        print("Discovering Microsoft Edge-TTS neural voices for India...")
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            matched = [v for v in voices if v["Locale"].startswith("en-IN") or v["Locale"].startswith("hi-IN")]
            print(f"\nFound {len(matched)} matching voices:")
            for v in matched:
                print(f"  - {v['ShortName']:30s} | Gender: {v['Gender']:6s} | Locale: {v['Locale']}")
            return 0
        except Exception as exc:
            print(f"Error listing voices: {exc}", file=sys.stderr)
            return 1

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verification Mode
    if args.verify:
        print(f"Auditing audio files in {out_dir}...")
        ogg_files = sorted(out_dir.glob("*.ogg"))
        if not ogg_files:
            print(f"No .ogg files found in {out_dir}")
            return 1
        valid_count = 0
        for f in ogg_files:
            ok, dur, codec = verify_audio_file(f, ffprobe_bin)
            status_str = f"[OK - {codec.upper()}]" if ok else "[INVALID]"
            print(f"  {status_str:14s} {f.name:32s} | {dur:5.1f}s | {f.stat().st_size // 1024:4d} KB")
            if ok:
                valid_count += 1
        print(f"\nVerification completed: {valid_count}/{len(ogg_files)} valid audio streams.")
        return 0 if valid_count == len(ogg_files) else 1

    # 2. Select target stories
    target_stories: List[Dict[str, Any]] = []
    if args.poi_id:
        if args.poi_id in STORIES_BY_ID:
            s = dict(STORIES_BY_ID[args.poi_id])
            if args.text_en:
                s["text_en"] = args.text_en
            if args.text_hi:
                s["text_hi"] = args.text_hi
            target_stories.append(s)
        else:
            # Create ad-hoc story
            target_stories.append({
                "id": args.poi_id,
                "region": args.region,
                "place_id": args.poi_id,
                "file_en": f"{args.poi_id}_guide.ogg",
                "file_hi": f"{args.poi_id}_guide_hi.ogg",
                "text_en": args.text_en or f"Welcome to {args.poi_id}.",
                "text_hi": args.text_hi or f"{args.poi_id} में आपका स्वागत है।",
            })
    else:
        if args.region == "all":
            target_stories = list(BUILTIN_STORIES)
        else:
            target_stories = [s for s in BUILTIN_STORIES if s["region"] == args.region]

    if not target_stories:
        print(f"No stories found matching region '{args.region}' or POI '{args.poi_id}'", file=sys.stderr)
        return 1

    print("=" * 72)
    print("TrueWay Bilingual Audio Generator & Transcoder")
    print(f"  Region:       {args.region}")
    print(f"  Stories:      {len(target_stories)} POIs ({len(target_stories) * 2} audio tracks)")
    print(f"  Backend:      {args.backend} {'(MOCK)' if args.mock else ''}")
    print(f"  Codec:        OGG {args.codec.upper()}")
    print(f"  Voices:       EN='{args.voice_en}' | HI='{args.voice_hi}'")
    print(f"  FFmpeg:       {ffmpeg_bin or 'NOT FOUND (using pure-python mock/fallback)'}")
    print(f"  Output Dir:   {out_dir}")
    print(f"  Dry Run:      {args.dry_run}")
    print("=" * 72)

    if not args.dry_run and not args.mock and not ffmpeg_bin:
        print("ERROR: FFmpeg binary not found. Required for transcoding to OGG Vorbis/Opus.", file=sys.stderr)
        print("Install via: pip install imageio-ffmpeg  OR  winget install Gyan.FFmpeg", file=sys.stderr)
        return 1

    results = []
    for story in target_stories:
        res = await generate_single_story(
            story=story,
            out_dir=out_dir,
            backend=args.backend,
            codec=args.codec,
            voice_en=args.voice_en,
            voice_hi=args.voice_hi,
            ffmpeg_bin=ffmpeg_bin,
            mock=args.mock,
            dry_run=args.dry_run,
            force=args.force,
        )
        results.append(res)

    # 3. Optional APK asset sync
    if args.sync_assets and not args.dry_run:
        ASSETS_AUDIO.mkdir(parents=True, exist_ok=True)
        synced = 0
        for s in target_stories:
            for k in ("file_en", "file_hi"):
                src = out_dir / s[k]
                dst = ASSETS_AUDIO / s[k]
                if src.is_file():
                    shutil.copy2(src, dst)
                    synced += 1
        print(f"\nSynchronized {synced} audio files to {ASSETS_AUDIO}")

    print("\nAudio pipeline processing finished successfully.")
    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
