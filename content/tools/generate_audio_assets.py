"""Generator for P1A Audio Stories (.ogg Vorbis files).
Generates the 20 bilingual audio recordings (10 POIs x EN/HI) using
PowerShell System.Speech.Synthesis + FFmpeg libvorbis encoder.
Saves to content/audio/ and copies to android/app/src/main/assets/audio/.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FFMPEG = r"C:\Users\sumit\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"

AUDIO_DIR = ROOT / "content" / "audio"
ASSETS_AUDIO_DIR = ROOT / "android" / "app" / "src" / "main" / "assets" / "audio"

STORIES = [
    {
        "id": "mahabodhi",
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
        "file_en": "bodhi_tree_guide.ogg",
        "file_hi": "bodhi_tree_guide_hi.ogg",
        "text_en": (
            "Bodhi Vriksha. Ficus religiosa. "
            "Standing directly behind the main sanctum of the Mahabodhi Temple, this sacred pipal tree marks the revered spot where Siddhartha Gautama meditated for 49 days and attained supreme awakening. "
            "The current tree is a direct descendant of the original specimen. "
            "In the 3rd century BCE, Emperor Ashoka's daughter, Princess Sanghamitta, carried a sapling of this tree to Sri Lanka, where it was planted at Anuradhapura. "
            "When this tree in Bodh Gaya was destroyed in later centuries, a cutting from the Anuradhapura tree was brought back and replanted here, preserving an unbroken botanical lineage."
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
        "file_en": "vajrasana_guide.ogg",
        "file_hi": "vajrasana_guide_hi.ogg",
        "text_en": (
            "Vajrasana. Sanskrit: Diamond Throne. "
            "Resting between the western wall of the Mahabodhi Temple and the trunk of the Bodhi Tree lies the Vajrasana, or Diamond Throne. "
            "Carved from a single massive slab of Chunar polished sandstone, this seat was commissioned by Emperor Ashoka around 250 BCE. "
            "The border is intricately carved with honeysuckles, geese, and geometric rosettes characteristic of Mauryan imperial stone craft. "
            "Tradition identifies this stone as the navel of the earth, the one immovable center capable of supporting the spiritual weight of Enlightenment."
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
        "file_en": "great_buddha_guide.ogg",
        "file_hi": "great_buddha_guide_hi.ogg",
        "text_en": (
            "Daibutsu. Great Buddha of Bodh Gaya. "
            "Towering eighty feet into the sky, the Great Buddha statue was consecrated in 1989 by the 14th Dalai Lama. "
            "Constructed over seven years using sandstone and red granite, the statue depicts the Buddha seated in the Dhyana Mudra, or meditative posture, atop a grand lotus pedestal. "
            "Inside the hollow sculpture rests a spiraling staircase leading past bronze statues of the Buddha's ten principal disciples, symbolizing international peace and Buddhist unity."
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
        "file_en": "nalanda_mahavihara_guide.ogg",
        "file_hi": "nalanda_mahavihara_guide_hi.ogg",
        "text_en": (
            "Nalanda. Sanskrit: Lotus-Giver or Giver of Knowledge. "
            "Nalanda was the world's preeminent residential university, flourishing for over 700 years under the Gupta Empire and the Pala kings. "
            "At its peak in the 7th century, Chinese monk Xuanzang documented over 10,000 students and 2,000 resident masters studying astronomy, medicine, logic, and Buddhist philosophy. "
            "As you walk along the main north-south axis, notice the precise architectural layout: a row of monumental temples facing east, opposite a parallel row of self-contained monastic quadrangles facing west. "
            "Each monastery featured a central open brick courtyard surrounded by study cells, each with its own stone bed and oil-lamp alcove."
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
        "text_hi": (
            "Mandir Sankhya Teen. Saat Parton ka Rahasya. "
            "Mandir sankhya teen Nalanda ke utkhanit khandaharon ka sabse bhavya smarak hai. "
            "Paanchvi se baarahvi shatabdi ke madhya yahan saat kramik nirmaan partein khoji gayin. "
            "Paanchvi parat mein sundar Guptakaaleen plaster moortiyan surakshit hain, jinmein Bhagwan Buddha aur Bodhisattvon ki mukhaakriti ki saumyata spasht dikhayi deti hai."
        ),
    },
    {
        "id": "nalanda_monastery1",
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
        "text_hi": (
            "Vihara Sankhya Ek. Bhikshu Jeevan ki Dincharya. "
            "Vihara sankhya ek Nalanda ka sabse bada aur mahatvapoorna chhatra-niwas tha. Ismein nau kramik nirmaan staron ke pramaan mile hain. "
            "Kendriya praangan ke charon or bane chhote-chhote adhyayan kaksh, patthar ke bistar aur kone mein sthit gehra kuan pracheen chhatra jeevan ki saadgi ko ujagar karte hain."
        ),
    },
    {
        "id": "griddhakuta",
        "file_en": "griddhakuta_guide.ogg",
        "file_hi": "griddhakuta_guide_hi.ogg",
        "text_en": (
            "Griddhakuta. Pali: Gijjhakuta, Vulture's Peak. "
            "High above the ancient valley of Rajgir rises Griddhakuta, named for the natural crag that resembles the head and beak of a vulture perched on the hillside. "
            "King Bimbisara of Magadha constructed an engineered stone causeway up this ridge so he could visit the Buddha during the rainy season retreats. "
            "Here on this small open brick terrace, tradition records that Buddha delivered the Heart Sutra and the Lotus Sutra, initiating the Second Turning of the Wheel of Dharma. "
            "Look down at the natural amphitheater of the five surrounding hills that once formed the defenses of Rajagriha."
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
        "file_en": "cyclopean_wall_guide.ogg",
        "file_hi": "cyclopean_wall_guide_hi.ogg",
        "text_en": (
            "Rajgir Durgana. Cyclopean Masonry Wall. "
            "One of the most remarkable pre-Mauryan defensive works in South Asia, the Cyclopean Wall spanned over forty kilometers along the ridgelines of the Rajgir hills. "
            "Constructed without mortar, massive undressed limestone blocks up to one and a half meters across were carefully fitted together by ancient Magadhan builders. "
            "Dating to the 6th or 5th century BCE, this formidable barrier protected the royal capital from military incursions during the rise of India's earliest empires."
        ),
        "text_hi": (
            "Rajgir ki Cyclopean Pracheer. "
            "Dakshin Asia ki pracheentam sainya fortifications mein se ek, yeh pracheer Rajgir ki pahadiyon par chaalees kilometer se adhik doori tak phaili thi. "
            "Bina kisi gaare ya choone ke, vishal an-gadhe choona pattharon ko aapas mein jodkar chhati shatabdi Eesa Poorva mein Magadh samrajya ki suraksha hetu banaya gaya tha."
        ),
    },
    {
        "id": "sonbhandar",
        "file_en": "sonbhandar_guide.ogg",
        "file_hi": "sonbhandar_guide_hi.ogg",
        "text_en": (
            "Svarna Bhandara. Gold Treasury Cave. "
            "Chiseled directly into the southern cliff of Vaibhara Hill, Sonbhandar consists of two rock-cut chambers dating between the 3rd and 4th centuries CE. "
            "Popular folklore long claimed that Emperor Bimbisara's hidden treasury was sealed inside behind an undeciphered inscription on the chamber wall. "
            "However, archaeological excavations and the rock-cut Shankhalipi inscription clearly establish that the cave was dedicated by the Jain ascetic Muni Vairadeva for solitary meditation and tapas."
        ),
        "text_hi": (
            "Sonbhandar Gufa. Swarna Kosh ki Kinwadanti. "
            "Vaibhāra pahadi ki talhati mein tarashi gayi Sonbhandar gufaon ke vishay mein lok-katha thi ki ismein Samrat Bimbisara ka khazana chhipa hai. "
            "Kintu puraatatvik adhyayanon aur Brahmi-Shankhalipi abhilekhon se siddha hota hai ki yeh teesri-chauthi sadi mein Jain Muni Vairadeva dwara sadhana hetu nirmit karayi gayi thi."
        ),
    },
]


def synthesize_speech(text: str, wav_path: Path) -> None:
    # Use PowerShell System.Speech to write WAV
    ps_script = f"""
Add-Type -AssemblyName System.Speech
$syn = New-Object System.Speech.Synthesis.SpeechSynthesizer
$syn.SetOutputToWaveFile('{wav_path.as_posix()}')
$syn.Speak('{text.replace("'", "''")}')
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


def main():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating 20 bilingual audio recordings using SAPI TTS + FFmpeg libvorbis...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        total = len(STORIES) * 2
        idx = 0

        for s in STORIES:
            # English
            idx += 1
            wav_en = tmp / f"{s['id']}_en.wav"
            out_en = AUDIO_DIR / s["file_en"]
            print(f"[{idx}/{total}] Synthesizing {s['file_en']}...")
            synthesize_speech(s["text_en"], wav_en)
            convert_wav_to_ogg(wav_en, out_en)
            shutil.copy2(out_en, ASSETS_AUDIO_DIR / s["file_en"])

            # Hindi
            idx += 1
            wav_hi = tmp / f"{s['id']}_hi.wav"
            out_hi = AUDIO_DIR / s["file_hi"]
            print(f"[{idx}/{total}] Synthesizing {s['file_hi']}...")
            synthesize_speech(s["text_hi"], wav_hi)
            convert_wav_to_ogg(wav_hi, out_hi)
            shutil.copy2(out_hi, ASSETS_AUDIO_DIR / s["file_hi"])

    print(f"\nSuccessfully generated {total} audio files into:")
    print(f"  - {AUDIO_DIR}")
    print(f"  - {ASSETS_AUDIO_DIR}")


if __name__ == "__main__":
    main()
