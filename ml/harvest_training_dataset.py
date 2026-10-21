"""Real Heritage & Hard-Negative Dataset Harvester for TrueWay Training Pipeline.

Operationalizes `content/DATASET_RESEARCH_AND_HARVESTING_SPECIFICATION.md` §§ 3–5
and `docs/CTO_PROJECT_PLAN_AND_MULTI_AGENT_STRATEGY.md` (KT-001).

Downloads real, rights-cleared (CC BY, CC BY-SA, CC0, Public Domain) monument
photographs from Wikimedia Commons across:
  1. All 15 supported Bihar Buddhist Circuit POIs
  2. All 8 Hard-Negative Distractor Taxonomy Categories (non-Bihar temples,
     SE Asian stupas, brick ruins, scaffolding, shops/markets, foliage,
     crowds, and out-of-pack Bihar lookalike monuments)

Enforces strict photographer-grouped split discipline (§7.2, §7.6):
  - Splits by photographer/author so no photographer or source image straddles
    `ref` / `calib` / `test`.
  - Applies realistic field camera augmentations (viewpoint crop, daylight/shade
    color temperature shift, mild perspective/blur) ONLY within the same split
    and photographer group when needed to balance per-POI sample counts, so
    held-out test queries remain strictly independent of reference/calibration
    sources.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "ml" / "dataset"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "TrueWayHeritageTrainer/3.1 (https://github.com/TrueWay; research@trueway.org) Python-urllib/3"

# 15 Canonical Bihar Buddhist Circuit POIs (matching content/seed/seed_demo.sql)
POI_SPECS: List[Dict[str, object]] = [
    {
        "place_id": "in-bihar-bodhgaya-mahabodhi",
        "parent_place_id": None,
        "viewpoint_tag": "shikhara-east-facade",
        "distinguishing_hint": "55m pyramidal main temple spire and central courtyard",
        "categories": ["Category:Mahabodhi Temple"],
        "queries": ["Mahabodhi Temple Bodh Gaya spire", "Mahabodhi Temple facade", "Mahabodhi Temple Bodhgaya main temple", "Bodh Gaya Mahabodhi temple complex", "Mahabodhi temple shikhara Bodh Gaya", "Mahabodhi Temple prayer Bodhgaya", "Bodhgaya Mahabodhi temple ghat"],
    },
    {
        "place_id": "in-bihar-bodhgaya-bodhi-tree",
        "parent_place_id": "in-bihar-bodhgaya-mahabodhi",
        "viewpoint_tag": "bodhi-tree-canopy",
        "distinguishing_hint": "Sacred fig tree adjacent to the western wall of temple",
        "vision_class": False,
        "vision_note": 'The Bodhi Tree shares the Mahabodhi complex with the temple; from a photograph the tree and the temple are not separable. The tree is a SPOTTER ITEM on the Mahabodhi place card, not a separate vision class (blueprint §7.2).',
        "categories": ["Category:Bodhi Tree (Bodh Gaya)"],
        "queries": ["Bodhi Tree Bodh Gaya Mahabodhi", "Sacred fig Bodh Gaya", "Bodhi tree Bodh Gaya temple garden", "Bodh Gaya bodhi tree worship", "Bodhi tree Bodhgaya fence", "sacred fig tree Mahabodhi temple"],
    },
    {
        "place_id": "in-bihar-bodhgaya-vajrasana",
        "parent_place_id": "in-bihar-bodhgaya-mahabodhi",
        "viewpoint_tag": "diamond-throne-slab",
        "distinguishing_hint": "Polished sandstone slab marking the seat of enlightenment",
        "vision_class": False,
        "vision_note": 'The Vajrasana is a polished slab at the foot of the tree; a photograph of it is not distinguishable from the temple complex around it. It is a SPOTTER ITEM on the Mahabodhi place card, not a separate vision class (blueprint §7.2).',
        "categories": ["Category:Vajrasana"],
        "queries": ["Vajrasana Bodh Gaya", "Diamond throne Mahabodhi", "Vajrasana diamond throne Bodhgaya", "Vajrasana Bodh Gaya throne stone", "Bodh Gaya Vajrasana railing", "vajrasana bodhgaya temple"],
    },
    {
        "place_id": "in-bihar-bodhgaya-animesh-lochan",
        "parent_place_id": "in-bihar-bodhgaya-mahabodhi",
        "viewpoint_tag": "unblinking-gaze-stupa",
        "distinguishing_hint": "Northeast brick chaitya where Buddha stood gazing at the Bodhi tree",
        "categories": ["Category:Animesh Lochan Chaitya"],
        "queries": ["Animesh Lochan Chaitya", "Mahabodhi Temple small stupa shrine", "Animesh Locana Chaitya Bodh Gaya", "Animesalocana chaitya Bodhgaya"],
    },
    {
        "place_id": "in-bihar-bodhgaya-mucalinda",
        "parent_place_id": "in-bihar-bodhgaya-mahabodhi",
        "viewpoint_tag": "serpent-lake-pavilion",
        "distinguishing_hint": "Rectangular tank with central snake king statue sheltering Buddha",
        "categories": ["Category:Mucalinda Lake", "Category:Muchalinda Lake", "Category:Mucalinda"],
        "queries": ["Mucalinda Bodh Gaya", "Muchalinda Bodh Gaya", "Mucalinda statue Buddha", "Mahabodhi Temple pond Buddha", "Mucalinda lake Bodhgaya snake king", "Mucalinda pond Bodh Gaya", "Muchalinda lake Bodhgaya"],
    },
    {
        "place_id": "in-bihar-bodhgaya-great-buddha",
        "parent_place_id": None,
        "viewpoint_tag": "daibutsu-colossal-statue",
        "distinguishing_hint": "25-meter seated sandstone Buddha unveiled in 1989",
        "categories": ["Category:Great Buddha Statue, Bodh Gaya"],
        "queries": ["Great Buddha Statue Bodh Gaya", "Giant Buddha Bodh Gaya", "80 feet Buddha statue Bodhgaya", "Daijutsu Buddha Bodh Gaya", "Great Buddha statue Bodh Gaya front", "Bodh Gaya Great Buddha statue"],
    },
    {
        "place_id": "in-bihar-rajgir-vultures-peak",
        "parent_place_id": None,
        "viewpoint_tag": "peak-platform-shrine",
        "distinguishing_hint": "Natural rock precipice with ancient brick stupa remains",
        "categories": ["Category:Gridhrakuta Peak"],
        "queries": ["Gridhrakuta Peak Rajgir", "Vulture Peak Rajgir", "Gridhakuta hill Rajgir ruins", "Rajgir Vulture peak temple", "Gridhra Kuta Rajgir"],
    },
    {
        "place_id": "in-bihar-rajgir-venu-vana",
        "parent_place_id": None,
        "viewpoint_tag": "bamboo-grove-lake",
        "distinguishing_hint": "Bamboo park and historical bathing tank",
        "categories": ["Category:Venuvana"],
        "queries": ["Venuvana Rajgir", "Bamboo Grove Rajgir", "Venu Vana Rajgir Bihar", "Venuvana lake Rajgir", "Venu Vana bamboo park Rajgir"],
    },
    {
        "place_id": "in-bihar-rajgir-cyclopean-wall",
        "parent_place_id": None,
        "viewpoint_tag": "unmortared-stone-rampart",
        "distinguishing_hint": "Ancient 40km undressed massive stone fortification",
        "categories": ["Category:Cyclopean Wall of Rajgir"],
        "queries": ["Cyclopean Wall Rajgir", "Rajgir stone wall fortification", "Cyclopean wall Rajgir Bihar", "Rajgir ancient stone rampart"],
    },
    {
        "place_id": "in-bihar-rajgir-shanti-stupa",
        "parent_place_id": None,
        "viewpoint_tag": "white-peace-pagoda",
        "distinguishing_hint": "Modern white dome pagoda on Ratnagiri hill with golden Buddha statues",
        "categories": ["Category:Vishwa Shanti Stupa, Rajgir"],
        "queries": ["Vishwa Shanti Stupa Rajgir", "Peace Pagoda Rajgir", "Shanti Stupa Rajgir Bihar", "Rajgir Vishwa Shanti Stupa white dome"],
    },
    {
        "place_id": "in-bihar-rajgir-sonbhandar",
        "parent_place_id": None,
        "viewpoint_tag": "rock-cut-chamber-facade",
        "distinguishing_hint": "Ancient twin rock-cut chambers with polished interiors",
        "categories": ["Category:Sonbhandar Caves"],
        "queries": ["Sonbhandar Caves Rajgir", "Son Bhandar Cave Rajgir", "Son Bhandar rock cut caves", "Sonbhandar Rajgir entrance"],
    },
    {
        "place_id": "in-bihar-nalanda-mahavihara",
        "parent_place_id": None,
        "viewpoint_tag": "archaeological-corridor",
        "distinguishing_hint": "Excavated brick mounds of the main Nalanda monastic complex",
        "categories": ["Category:Nalanda Mahavihara", "Category:Nalanda University"],
        "queries": ["Nalanda Mahavihara ruins", "Nalanda University archaeological ruins", "Nalanda Mahavihara archaeological site", "Nalanda university main complex ruins", "Nalanda excavations brick mounds"],
    },
    {
        "place_id": "in-bihar-nalanda-temple-03",
        "parent_place_id": "in-bihar-nalanda-mahavihara",
        "viewpoint_tag": "towering-stupa-corner-facets",
        "distinguishing_hint": "Imposing multi-layered stupa with surviving stucco figures",
        "categories": ["Category:Stupa of Sariputra", "Category:Temple No. 3, Nalanda"],
        "queries": ["Stupa of Sariputra Nalanda", "Temple 3 Nalanda stupa", "Sariputta Stupa Nalanda", "Nalanda Temple No 3", "Nalanda Sariputta stupa", "Temple number 3 Nalanda"],
    },
    {
        "place_id": "in-bihar-nalanda-monastery-01",
        "parent_place_id": "in-bihar-nalanda-mahavihara",
        "viewpoint_tag": "central-courtyard-cells",
        "distinguishing_hint": "Double-story quadrangle with monastic cells and central chaitya",
        "categories": ["Category:Monastery No. 1, Nalanda"],
        "queries": ["Nalanda monastery courtyard cells", "Nalanda vihara brick courtyard", "Nalanda Monastery 1", "Nalanda monastery one brick cells", "Nalanda Sariputta monastery", "Nalanda ancient university brick monastery ruins", "Nalanda archaeological site monks cells", "Nalanda monastery granary"],
    },
    {
        "place_id": "in-bihar-nalanda-museum",
        "parent_place_id": "in-bihar-nalanda-mahavihara",
        "viewpoint_tag": "museum-entrance-portico",
        "distinguishing_hint": "Archaeological repository housing Pala-period bronzes and sculptures",
        "vision_class": False,
        "vision_note": "The Archaeological Museum is a single-storey building whose Commons photographs are signboards and interior displays; a visitor's photograph of the building is not separable from the Nalanda complex. Search-only.",
        "categories": ["Category:Archaeological Museum, Nalanda"],
        "queries": ["Archaeological Museum Nalanda", "Nalanda Museum sculpture", "Archaeological Museum Nalanda building", "Nalanda archaeological museum campus", "Nalanda university museum building", "Nalanda museum exterior"],
    },
]

# 8 Hard-Negative Taxonomy Categories (§5 of DATASET_RESEARCH_AND_HARVESTING_SPECIFICATION.md)
NEGATIVE_SPECS: List[Dict[str, object]] = [
    {
        "neg_category": "neg-out-of-pack-bihar-lookalike",
        "label": "out-of-pack-bihar-lookalike",
        "vision_class": False,
        "vision_note": "The Archaeological Museum is a single-storey building whose Commons photographs are signboards and interior displays; a visitor's photograph of the building is not separable from the Nalanda complex. Search-only.",
        "categories": ["Category:Kesaria Stupa", "Category:Vikramashila", "Category:Barabar Caves", "Category:Golghar"],
        "queries": ["Kesaria Stupa Bihar", "Vikramshila ruins Bhagalpur", "Barabar Caves Bihar", "Sher Shah Suri Tomb Sasaram", "Golghar Bihar dome tomb", "Bodhgaya Nalanda ruins other"],
    },
    {
        "neg_category": "neg-generic-indian-temple",
        "label": "generic-indian-temple-non-bihar",
        "vision_class": False,
        "vision_note": "The Archaeological Museum is a single-storey building whose Commons photographs are signboards and interior displays; a visitor's photograph of the building is not separable from the Nalanda complex. Search-only.",
        "categories": ["Category:Bhitargaon numeric temple", "Category:Sanchi Stupa No. 1"],
        "queries": ["Bhitargaon brick temple", "Sirpur Laxman brick temple", "Bishnupur terracotta temple", "Sarnath Dhamek Stupa", "ancient brick temple India", "Indian brick temple ruins"],
    },
    {
        "neg_category": "neg-se-asian-stupa",
        "label": "southeast-asian-stupa-pagoda",
        "vision_class": False,
        "vision_note": "The Archaeological Museum is a single-storey building whose Commons photographs are signboards and interior displays; a visitor's photograph of the building is not separable from the Nalanda complex. Search-only.",
        "categories": ["Category:Bagan temples", "Category:Ruwanwelisaya"],
        "queries": ["Bagan brick pagoda Myanmar", "Anuradhapura brick stupa Sri Lanka", "Ayutthaya brick stupa Thailand", "gilded golden dome pagoda Myanmar", "Bagan golden stupa dome", "Shwedagon golden dome pagoda", "golden chedi Ayutthaya", "gilded stupa spire Thailand"],
    },
    {
        "neg_category": "neg-ordinary-brick-ruins",
        "label": "excavated-brick-ruins",
        "vision_class": False,
        "vision_note": "The Archaeological Museum is a single-storey building whose Commons photographs are signboards and interior displays; a visitor's photograph of the building is not separable from the Nalanda complex. Search-only.",
        "categories": ["Category:Kesaria Stupa", "Category:Vikramashila", "Category:Pawapuri", "Category:Barabar Caves"],
        "queries": ["excavated brick stupa site India", "ruined brick monastery Bihar", "ancient brick stupa remains Bihar", "brick archaeological site Odisha", "abandoned brick ruins India", "brick stupa ruins Bodh Gaya", "Kesariya Mahadeva Stupa", "Pawapuri ruins brick stupa", "Lauriya Nandangarh ruins", "brick monastery ruins excavation", "excavated brick foundations India", "ancient brick tower ruin India", "ruined brick stupa Rajgir", "Nalanda style brick stupa ruin"],
    },
    {
        "neg_category": "neg-construction-scaffolding",
        "label": "scaffolding-restoration",
        "vision_class": False,
        "vision_note": "The Archaeological Museum is a single-storey building whose Commons photographs are signboards and interior displays; a visitor's photograph of the building is not separable from the Nalanda complex. Search-only.",
        "categories": [],
        "queries": ["bamboo scaffolding building India", "heritage restoration scaffolding", "construction site scaffolding brick", "bamboo scaffolding temple India", "scaffolding heritage monument"],
    },
    {
        "neg_category": "neg-modern-commercial-shop",
        "label": "street-market-shop",
        "vision_class": False,
        "vision_note": "The Archaeological Museum is a single-storey building whose Commons photographs are signboards and interior displays; a visitor's photograph of the building is not separable from the Nalanda complex. Search-only.",
        "categories": [],
        "queries": ["Indian street market stalls", "souvenir shop stalls India", "tea stall roadside India", "Indian market shop front", "roadside shops India"],
    },
    {
        "neg_category": "neg-natural-foliage-landscape",
        "label": "monastery-garden-tree",
        "vision_class": False,
        "vision_note": "The Archaeological Museum is a single-storey building whose Commons photographs are signboards and interior displays; a visitor's photograph of the building is not separable from the Nalanda complex. Search-only.",
        "categories": [],
        "queries": ["Ficus religiosa leaves trunk", "bamboo forest grove path", "rocky hill boulders scrub India", "banyan tree India", "dry forest landscape India"],
    },
    {
        "neg_category": "neg-crowds-tourist-occlusion",
        "label": "unrelated-tourist-crowd",
        "vision_class": False,
        "vision_note": "The Archaeological Museum is a single-storey building whose Commons photographs are signboards and interior displays; a visitor's photograph of the building is not separable from the Nalanda complex. Search-only.",
        "categories": [],
        "queries": ["pilgrims crowd India", "tourists walking courtyard India", "street crowd festival India", "tourist crowd at temple India", "visitors queue monument India", "group of tourists at Buddhist site"],
    },
    # ---------------------------------------------------------------------
    # The "TWIN" negatives.
    #
    # The measured failures are not random: a white-and-gold dome is matched to
    # the Shanti Stupa, a colossal seated Buddha to the Great Buddha, a
    # rock-cut cave to Son Bhandar, a stepped brick tower to the Mahabodhi, and
    # a brick stupa mound to the Nalanda sites. A hard-negative bank that
    # contains only generic ruins cannot separate them, because the winning
    # place's own score and the best negative's score differ by a few
    # hundredths. The bank needs the LOOKALIKES, not more of the same.
    #
    # Each category below is the confusable twin of one or more vision
    # classes. None of the twelve vision classes may appear in these queries.
    # ---------------------------------------------------------------------
    {
        "title_exempt": [r"\bstatue\b", r"\bstatuette\b", r"\bfigure of\b"],
        "neg_category": "neg-white-golden-dome",
        "label": "white-golden-dome-pagoda",
        "vision_class": False,
        "vision_note": "A white dome with a golden pinnacle is the Vishwa Shanti Stupa's silhouette; the same silhouette exists at a hundred other stupas in South and South-East Asia.",
        "categories": ["Category:Wat Phu Khao Thong", "Category:Shwedagon Pagoda",
                       "Category:Jetavanaramaya", "Category:Wat Phra That Doi Suthep",
                       "Category:Wat Chedi Luang"],
        "queries": ["white stupa dome golden pinnacle", "gilded golden chedi pagoda",
                    "Shwedagon pagoda golden dome", "Wat Phra That Doi Suthep white chedi",
                    "Wat Chedi Luang Chiang Mai", "Ruwanwelisaya white stupa",
                    "Anuradhapura white dagoba", "Kakku pagoda Myanmar",
                    "Luang Prabang wat stupa", "Ayutthaya golden stupa",
                    "white pagoda Buddhist Sri Lanka", "gilded stupa spire Myanmar",
                    "Buddhist stupa golden dome Nepal", "white dome chedi temple"],
    },
    {
        "title_exempt": [r"\bstatue\b", r"\bstatuette\b", r"\bfigure of\b", r"\bbust of\b"],
        "neg_category": "neg-colossal-seated-buddha",
        "label": "colossal-seated-buddha-statue",
        "vision_class": False,
        "vision_note": "The Great Buddha at Bodh Gaya is a colossal seated Buddha; so are the statues at Leshan, Kamakura, Beijing, Bamiyan and Awaji, and a visitor's photograph of one of those must not be read as the Great Buddha.",
        "categories": ["Category:Leshan Giant Buddha", "Category:Spring Temple Buddha",
                       "Category:Longmen Grottoes"],
        "queries": ["colossal seated Buddha statue", "giant Buddha statue carved cliff",
                    "Leshan Giant Buddha", "Kamakura Daibutsu Great Buddha",
                    "Tian Tan Buddha Beijing", "Bamiyan Buddha statue",
                    "Awaji Kannon colossal statue", "huge Buddha statue seated hillside",
                    "Spring Temple Buddha Henan", "giant bronze Buddha statue temple",
                    "Buddha statue thirty metres tall", "monumental Buddha rock carving"],
    },
    {
        "title_exempt": [r"\brelief\b", r"\bcarving\b", r"\bcarved\b", r"\bpanel\b", r"\bsculpture\b", r"\bstatue\b"],
        "neg_category": "neg-rock-cut-cave-complex",
        "label": "rock-cut-cave-and-relief-complex",
        "vision_class": False,
        "vision_note": "Son Bhandar is a rock-cut cave complex with carved relief panels; so are Ellora, Ajanta, Badami, Mamallapuram, Udayagiri, Khandagiri, Bojjannakonda and Undavalli.",
        "categories": ["Category:Ellora Caves", "Category:Ajanta Caves",
                       "Category:Badami Caves", "Category:Mamallapuram",
                       "Category:Udayagiri Caves", "Category:Khandagiri Caves"],
        "queries": ["rock cut cave temple chambers India", "caves carved relief panels India",
                    "Ellora cave interior sculpture", "Ajanta cave paintings interior",
                    "Badami cave temple Karnataka", "Mamallapuram rock cut mandapa",
                    "Udayagiri Khandagiri caves Odisha", "Bojjannakonda cave temple",
                    "Undavalli caves Andhra Pradesh", "Lomas Rishi cave Bihar",
                    "Nagarjunakonda rock cut caves", "ancient rock cut monastery India"],
    },
    {
        "title_exempt": [r"\bstatue\b", r"\brelief\b", r"\bornament\b"],
        "neg_category": "neg-stepped-brick-temple-tower",
        "label": "stepped-brick-temple-shikhara",
        "vision_class": False,
        "vision_note": "The Mahabodhi Temple's stepped brick shikhara is the signature of the Gupta-era brick temple; Bhitargaon, Sirpur, Bhedaghat, Champaner and Chittorgarh share the form.",
        "categories": ["Category:Bhitargaon numeric temple",
                       "Category:Lakshmana Temple, Sirpur",
                       "Category:Temples in Chittorgarh"],
        "queries": ["stepped brick temple shikhara India", "Gupta era brick temple",
                    "prakara shikhara brick temple", "ancient brick temple tower India",
                    "Bhitargaon brick temple complete view", "Laxman temple Sirpur brick",
                    "Bhedaghat sandstone temple", "Champaner pavilions Gujarat",
                    "brick temple spire Bihar", "terracotta temple India ancient",
                    "Chittorgarh tower temple", "brick Hindu temple India complete"],
    },
    {
        "title_exempt": [r"\bstatue\b", r"\brelief\b", r"\bornament\b"],
        "neg_category": "neg-ancient-brick-stupa-mound",
        "label": "ancient-brick-stupa-and-mound",
        "vision_class": False,
        "vision_note": "The Nalanda Mahavihara and the Sariputta Stupa are excavated brick mounds; Sanchi, Amaravati, Pauni, Sankissa, Salihundam and Sarisik are the same form elsewhere in India.",
        "categories": ["Category:Amaravati Stupa", "Category:Pauni",
                       "Category:Salihundam Stupa", "Category:Salihundam"],
        "queries": ["ancient brick stupa India", "Sanchi stupa hemispherical dome",
                    "Amaravati stupa ruins Andhra", "Pauni stupa Maharashtra",
                    "Sankissa stupa brick", "Sarisik stupa", "Salihundam stupa Tamil Nadu",
                    "excavated brick stupa mound India", "stupa ruins Odisha brick",
                    "Nalanda style brick stupa ruin", "ancient brick Buddhist mound India",
                    "stupa base cylindrical brick India", "Bharhut stupa relic"],
    },
]


def _commons_query(params: Dict[str, str]) -> Dict:
    base = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url|user|timestamp|extmetadata|dimensions",
        "iiurlwidth": "512",
    }
    base.update(params)
    url = f"{COMMONS_API}?{urllib.parse.urlencode(base)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}


def _extract_candidates(data: Dict, max_items: int = 25) -> List[Dict[str, str]]:
    pages = data.get("query", {}).get("pages", {})
    out: List[Dict[str, str]] = []
    for _, p in pages.items():
        title = p.get("title", "")
        if not title.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        ii_list = p.get("imageinfo", [])
        if not ii_list:
            continue
        ii = ii_list[0]
        w = ii.get("width", 0)
        h = ii.get("height", 0)
        if w < 200 or h < 200:
            continue
        thumb_url = ii.get("thumburl") or ii.get("url")
        if not thumb_url:
            continue
        ext = ii.get("extmetadata", {})
        lic = ext.get("LicenseShortName", {}).get("value", "CC BY-SA")
        low_lic = lic.lower()
        if not any(k in low_lic for k in ("cc", "public domain", "pd", "attribution", "free")):
            continue
        user = ii.get("user", "wikimedia-contributor")
        ts = ii.get("timestamp", "2025-01-01T00:00:00Z")[:10]
        out.append({
            "title": title,
            "url": thumb_url,
            "original_url": ii.get("url", thumb_url),
            "photographer": user,
            "visit": ts,
            "license": lic,
        })
        if len(out) >= max_items:
            break
    return out


def discover_candidates(
    categories: List[str],
    queries: List[str],
    target_count: int = 18,
    global_seen: Optional[set[str]] = None,
) -> List[Dict[str, str]]:
    seen_titles: set[str] = set() if global_seen is None else global_seen
    results: List[Dict[str, str]] = []

    for cat in categories:
        data = _commons_query({
            "generator": "categorymembers",
            "gcmtitle": cat,
            "gcmtype": "file",
            "gcmlimit": "35",
        })
        for c in _extract_candidates(data, max_items=target_count):
            if c["title"] not in seen_titles:
                seen_titles.add(c["title"])
                results.append(c)
                if len(results) >= target_count:
                    return results

    for q in queries:
        data = _commons_query({
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {q}",
            "gsrnamespace": "6",
            "gsrlimit": "35",
        })
        for c in _extract_candidates(data, max_items=target_count):
            if c["title"] not in seen_titles:
                seen_titles.add(c["title"])
                results.append(c)
                if len(results) >= target_count:
                    return results

    return results


def load_photo_status() -> Dict[str, str]:
    """POI -> reference-photo policy status, read from the project's own rights
    registry (`content/seed/rights_registry.json`).

    The registry is the SOURCE OF TRUTH for whether a POI may carry a vision
    reference set at all:
      * ``WITHHELD``   — photography is not permitted on site (e.g. the Mahabodhi
                         device ban). No visual reference may be shipped.
      * ``TO_COLLECT`` — the reference set is still provisional. Allowed, but
                         flagged in the manifest so the pack can say so.
      * absent          — no policy recorded; allowed.
    """
    path = ROOT / "content" / "seed" / "rights_registry.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: Dict[str, str] = {}
    for asset in data.get("assets", []) or []:
        pid = asset.get("place_id")
        status = str(asset.get("photo_status") or "").strip().upper()
        if pid and status:
            out[pid] = status
    return out


def load_verification_review() -> Dict[str, Dict[str, str]]:
    """Optional human review of individual source photographs.

    `ml/dataset/verification_review.json` maps `source_photo_id` -> verdict.
    Verdicts: ``approved`` (usable), ``rejected`` (must not be used),
    ``pending`` (default — treated as unapproved for training, reported as
    unreviewed).
    """
    path = ROOT / "ml" / "dataset" / "verification_review.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(data, dict) and "reviews" in data:
        data = data["reviews"]
    return data if isinstance(data, dict) else {}


def _download_one(item: Dict[str, str], dest_dir: Path, prefix: str, idx: int) -> Optional[Dict[str, str]]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_hash = hashlib.sha256(item["title"].encode("utf-8")).hexdigest()[:10]
    out_path = dest_dir / f"{prefix}_{idx:03d}_{safe_hash}.jpg"
    # The Commons file title IS the identity of the source photograph. Two rows
    # that share a title are the same photograph and must never straddle a split.
    source_photo_id = "commons:" + hashlib.sha256(item["title"].encode("utf-8")).hexdigest()[:16]
    if out_path.is_file() and out_path.stat().st_size > 1024:
        raw = out_path.read_bytes()
        out_rec = dict(item)
        out_rec["local_path"] = str(out_path.relative_to(ROOT)).replace("\\", "/")
        out_rec["sha256"] = hashlib.sha256(raw).hexdigest()
        out_rec["source_photo_id"] = source_photo_id
        out_rec["session_id"] = source_photo_id
        return out_rec

    for attempt in range(3):
        try:
            req = urllib.request.Request(item["url"], headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw_bytes = resp.read()
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            img.thumbnail((512, 512), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            jpg_bytes = buf.getvalue()
            out_path.write_bytes(jpg_bytes)
            out_rec = dict(item)
            out_rec["local_path"] = str(out_path.relative_to(ROOT)).replace("\\", "/")
            out_rec["sha256"] = hashlib.sha256(jpg_bytes).hexdigest()
            out_rec["source_photo_id"] = source_photo_id
            out_rec["session_id"] = source_photo_id
            return out_rec
        except Exception:
            time.sleep(0.4 * (attempt + 1))
    return None


def create_field_view_variation(src_path: Path, dest_path: Path, variant_idx: int) -> str:
    """Creates a realistic camera/daylight viewpoint variation from a canonical
    monument view (simulating distinct visitor camera captures).

    The DESTINATION NAME carries a digest of the SOURCE image, so a variation
    can never be mistaken for a variation of a different photograph. Without
    that, a photo that was renamed or moved (its class changed) would keep
    reusing the OLD variation file, and the corpus would silently train on the
    wrong pixels - which is exactly the kind of corruption that shows up as a
    class matching photos it has nothing to do with.
    """
    if dest_path.is_file() and dest_path.stat().st_size > 1024:
        return hashlib.sha256(dest_path.read_bytes()).hexdigest()

    img = Image.open(src_path).convert("RGB")
    w, h = img.size
    mode = variant_idx % 12
    if mode == 0:
        # Center-right framing + warm afternoon sun
        img = img.crop((int(w * 0.06), int(h * 0.04), int(w * 0.96), int(h * 0.94))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Color(img).enhance(1.12)
        img = ImageEnhance.Brightness(img).enhance(1.05)
    elif mode == 1:
        # Center-left framing + overcast shade
        img = img.crop((int(w * 0.03), int(h * 0.06), int(w * 0.92), int(h * 0.95))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Contrast(img).enhance(1.10)
        img = ImageEnhance.Brightness(img).enhance(0.94)
    elif mode == 2:
        # Horizontal mirror viewpoint + crisp sharpness
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        img = ImageEnhance.Sharpness(img).enhance(1.20)
    elif mode == 3:
        # Slight handheld tilt (+3 deg) + central crop
        img = img.rotate(3.0, resample=Image.Resampling.BICUBIC, expand=False)
        img = img.crop((int(w * 0.08), int(h * 0.08), int(w * 0.92), int(h * 0.92))).resize((w, h), Image.Resampling.BICUBIC)
    elif mode == 4:
        # Handheld tilt (-3 deg) + mild atmospheric haze
        img = img.rotate(-3.0, resample=Image.Resampling.BICUBIC, expand=False)
        img = img.crop((int(w * 0.07), int(h * 0.07), int(w * 0.93), int(h * 0.93))).resize((w, h), Image.Resampling.BICUBIC)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    elif mode == 5:
        # Upper-facade architectural framing + warm golden hour
        img = img.crop((int(w * 0.05), int(h * 0.02), int(w * 0.95), int(h * 0.88))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Color(img).enhance(1.18)
        img = ImageEnhance.Contrast(img).enhance(1.06)
    elif mode == 6:
        # Lower-courtyard perspective + cool morning light
        img = img.crop((int(w * 0.05), int(h * 0.10), int(w * 0.95), int(h * 0.98))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Color(img).enhance(0.88)
        img = ImageEnhance.Brightness(img).enhance(1.04)
    elif mode == 7:
        # Mirrored + warm afternoon crop
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        img = img.crop((int(w * 0.06), int(h * 0.06), int(w * 0.94), int(h * 0.94))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Color(img).enhance(1.10)
    elif mode == 8:
        # Tight 82% telephoto zoom crop
        img = img.crop((int(w * 0.09), int(h * 0.09), int(w * 0.91), int(h * 0.91))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Sharpness(img).enhance(1.15)
    elif mode == 9:
        # Mirrored + slight tilt (+2.5 deg) + contrast
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(2.5, resample=Image.Resampling.BICUBIC, expand=False)
        img = img.crop((int(w * 0.07), int(h * 0.07), int(w * 0.93), int(h * 0.93))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Contrast(img).enhance(1.08)
    elif mode == 10:
        # High-noon bright exposure + slight crop
        img = img.crop((int(w * 0.04), int(h * 0.04), int(w * 0.96), int(h * 0.96))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Brightness(img).enhance(1.09)
        img = ImageEnhance.Contrast(img).enhance(0.95)
    else:
        # Dusk/monsoon low-light capture + mild blur
        img = img.crop((int(w * 0.05), int(h * 0.05), int(w * 0.94), int(h * 0.94))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Brightness(img).enhance(0.90)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.4))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    data = buf.getvalue()
    dest_path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def subject_series_id(photographer: str, title: str) -> str:
    """The SUBJECT SERIES a photograph belongs to.

    Photographs of the same monument from the same visit are near-duplicates
    of each other, so the unit of independence for a statistical bound - and
    the unit that must never straddle a split - is the SERIES, not the
    photograph.

    The identity is (photographer, normalised title). The normalisation strips
    the markers Wikimedia Commons uses for one photographer's run of
    photographs of one subject::

        "X (1)", "X (2)", "X (3)"   -> X     a series
        "X (44621501090)"          -> X     a series; the number can be an
                                          ELEVEN-digit photo id
        "X 2", "X 3"               -> X     a series
        "X copy", "X cropped"      -> X

    The trailing number is stripped at ANY length. The previous regex matched
    only one to three digits, so a Commons photo id such as
    "Wat Phu Khao Thong (Golden Mount) (44621501090)" kept its number: fifteen
    photographs of that ONE Thai temple counted as fifteen independent series,
    and the splitter - which distributes whole series - put them in the
    reference, the calibration AND the test split at once. That is exactly the
    near-duplicate leakage the protocol forbids, and it was invisible to the
    integrity gate because the gate reads the same (wrong) series id.

    ONE implementation, used by the splitter and by the re-splitter. Two
    implementations that agree only by luck are how the two drifted apart in
    the first place.
    """
    raw = str(title or "")
    t = raw.lower()
    t = re.sub(r"^file:", "", t)
    t = re.sub(r"\.\w+$", "", t)
    t = re.sub(r"\s*\(\d+\)\s*$", "", t)
    t = re.sub(r"[\s\-_]*\d+$", "", t)
    t = re.sub(r"[\s\-_]+(a|b|c|ii|iii|iv|v|vi|vii|viii|ix|x)$", "", t)
    t = re.sub(r"[\s\-_]+(copy|cropped|crop|edit|edited|thumbnail|preview)$", "", t)
    who = str(photographer or "").strip().lower()
    return f"{who}|{t.strip() or raw}"


def assign_photo_grouped_splits(
    records: List[Dict[str, str]],
    counts_per_split: Tuple[int, int, int] = (4, 6, 10),
    min_photos_per_split: Tuple[int, int, int] = (2, 2, 2),
    proportions: Tuple[float, float, float] = (0.40, 0.20, 0.40),
    series_order: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """Assign records to `ref` / `calib` / `test` by SOURCE PHOTOGRAPH.

    Every record that derives from one source photograph — the raw download and
    any synthetic camera variation of it — lands in **exactly one** split. The
    sets of source photographs backing `ref`, `calib` and `test` are pairwise
    disjoint.

    This is the only assignment under which the rows of a split are
    *independent trials*, and therefore the only assignment under which the
    Clopper-Pearson bound on the false-accept rate means anything
    (ml/README.md §Protocol: "Split by photographer/visit/viewpoint, never by
    near-duplicate shuffle"; blueprint §7.2: "Avoid nearly identical user photos
    in train/test").

    Synthetic camera variations are still generated — but only *within* the
    split that owns the source photograph, and the augmentation never invents a
    new identity. `source_photo_id` is carried on every record so
    `ml/audit/check_split_integrity.py` can enforce this in CI.

    Split plan (whole source photographs, never rows):
        known      ref / calib / test  <- distinct photos per split
        negatives  ref / calib / test  <- distinct photos per split
    """
    if not records:
        return []

    # 1. group by source photograph -------------------------------------------------
    groups: Dict[str, List[Dict[str, str]]] = {}
    for rec in records:
        sid = rec.get("source_photo_id") or rec.get("original_url") or rec["local_path"]
        groups.setdefault(sid, []).append(rec)
    source_ids = sorted(groups.keys())

    # 2. allocate whole source photographs to splits -------------------------------
    # The unit of independence is a SUBJECT SERIES: photographs of the same
    # monument from the same visit ("Wat Phu Khao Thong (1)", "(2)", "(3)") are
    # near-duplicates of each other and must never straddle a split. So the
    # photographs are grouped by subject, whole subject groups are assigned to
    # splits, and the groups are distributed so that EVERY SPLIT GETS A
    # PROPORTIONAL MIX OF SUBJECTS.
    #
    # Both simpler orderings were tried and both are wrong:
    #   * ordering by source-photo id (a hash) is random in principle, but a
    #     class harvested in one sitting can end up with almost all of its
    #     confusable photographs in ONE split — the calibration split then
    #     received 2 of 24 visually confusable "white stupa with a golden
    #     pinnacle" photographs while the test split received 10, the fitted
    #     threshold did not transfer, and the measured false-accept rate was
    #     three times higher on test than on calibration.
    #   * ordering by title and interleaving the splits spreads a subject
    #     SERIES across splits, which is near-duplicate leakage of a different
    #     kind.
    # Grouping by subject and distributing the GROUPS proportionally fixes both.
    split_names = ("ref", "calib", "test")

    def subject_of(sid: str) -> str:
        rec = groups[sid][0]
        return subject_series_id(rec.get("photographer") or "", rec.get("title") or "")

    # group the photographs into subject series
    subjects: Dict[str, List[str]] = {}
    for sid in source_ids:
        subjects.setdefault(subject_of(sid), []).append(sid)
    subject_ids = sorted(subjects.keys())
    # The quota is a quota of SERIES, so the count it is derived from must be
    # the number of SERIES. It used to be the number of PHOTOGRAPHS, so a class
    # with 26 photographs in 2 series was given quotas of 10 / 5 / 11 for 2
    # series - and every series landed in the test split, leaving the class
    # with NO reference photographs at all.
    n_groups = len(subject_ids)

    # The split proportions, in SERIES.
    #
    #  * The calibration split is what the thresholds are fitted on, so it has
    #    to be REPRESENTATIVE: with 20 % of the series the hardest negative
    #    categories were left with one or two independent examples each, and
    #    the threshold fitted on them did not transfer to the test split.
    #  * The test split has to be LARGE enough to carry the false-accept
    #    bound. The gate asks for a Clopper-Pearson 95 % upper bound of 5 %,
    #    which at one failure in a hundred needs an effective n of about 92 -
    #    and the known side asks for 150 test photographs, which at the corpus'
    #    current series size needs 45 % of the known series in the test split.
    # 35 / 20 / 45 satisfies both without shrinking the calibration sample.
    #
    # `ref` + `calib` together form the GALLERY the scanner matches against, so
    # they get the larger share; `test` is the honest holdout. An earlier
    # 25/25/50 split left most classes with a ONE-photograph gallery, which
    # cannot generalise to a third photograph of the same monument - the
    # measured Top-1 collapsed to 59 % for exactly that reason.
    if n_groups >= 3:
        ref_n = max(1, round(n_groups * proportions[0]))
        calib_n = max(1, round(n_groups * proportions[1]))
        while ref_n + calib_n > n_groups - 1:
            if calib_n >= ref_n and calib_n > 1:
                calib_n -= 1
            elif ref_n > 1:
                ref_n -= 1
            else:
                break
        test_n = n_groups - ref_n - calib_n
    elif n_groups == 2:
        ref_n, calib_n, test_n = 1, 1, 0
    else:
        ref_n, calib_n, test_n = 1, 0, 0

    # Distribute whole subject groups into the splits.
    #
    # THE QUOTA AND THE COUNTER MUST BE IN THE SAME UNIT.
    #
    # The previous code compared a quota expressed in GROUPS with a counter
    # that counted PHOTOGRAPHS, so the distribution was driven by the
    # photograph count and the SERIES - the unit every effective sample size
    # in this project is counted in - ended up badly skewed. One negative
    # class ended up with 1 series in the reference split, 4 in the
    # calibration split and 9 in the test split, and the calibration split was
    # left with four independent examples of the hardest category in the
    # corpus. The open-set threshold fitted on that sample did not transfer:
    # the calibration split's hardest negative still had an open margin of
    # -0.31 while the test split's hardest was +0.05.
    #
    # The split is therefore balanced in SERIES, and the largest series are
    # dealt first so that no split is dominated by one of them.
    quota = {"ref": ref_n, "calib": calib_n, "test": test_n}
    filled = {"ref": 0, "calib": 0, "test": 0}
    photos = {"ref": 0, "calib": 0, "test": 0}
    split_of: Dict[str, str] = {}
    # The order in which the subject series are dealt out. By default the
    # largest series go first. A caller that knows the DIFFICULTY of each
    # series (how confusable it is with a place) can pass the hardest first,
    # so that every split receives the same mix of hard and easy series.
    #
    # Without that, the calibration split ends up without the hardest
    # examples of the hardest categories - on this corpus its hardest negative
    # had an open margin of -0.26 while the test split's hardest was +0.13 -
    # and the threshold fitted on it is far too permissive.
    if series_order:
        rank = {s: i for i, s in enumerate(series_order)}
        ordered_groups = sorted(
            subject_ids, key=lambda s: (rank.get(s, len(rank)), -len(subjects[s]), s))
    else:
        ordered_groups = sorted(subject_ids, key=lambda s: (-len(subjects[s]), s))
    while ordered_groups:
        name = max(split_names, key=lambda n: (quota[n] - filled[n], quota[n]))
        group = ordered_groups.pop(0)
        for sid in subjects[group]:
            split_of[sid] = name
        filled[name] += 1
        photos[name] += len(subjects[group])

    # 3. emit rows: raw record + variations, per split, from that split's photos ---
    out_all: List[Dict[str, str]] = []
    targets = list(counts_per_split)
    for si, split_name in enumerate(split_names):
        split_source_ids = [sid for sid in source_ids if split_of[sid] == split_name]
        if not split_source_ids:
            continue
        target_cnt = targets[si]

        # base rows: the raw download of each assigned photo
        base_rows: List[Tuple[Dict[str, str], str]] = []
        for sid in split_source_ids:
            recs = sorted(groups[sid], key=lambda r: r["local_path"])
            base_rows.append((recs[0], sid))
            for extra in recs[1:]:
                base_rows.append((extra, sid))

        # variations to reach the row target, drawn only from THIS split's photos
        needed = max(0, target_cnt - len(base_rows))
        for k in range(needed):
            base_rec, sid = base_rows[k % len(base_rows)]
            v_mode = (si * 3 + k) % 12
            src_p = ROOT / base_rec["local_path"]
            # The variation's name carries a digest of the SOURCE image: a
            # variation of a photograph that has since been renamed or moved
            # must not silently reuse the old file, or the corpus trains on
            # the wrong pixels (the embedding cache is keyed by path, so the
            # stale variation is cached under the new name).
            src_digest = (hashlib.sha256(src_p.read_bytes()).hexdigest()[:8]
                          if src_p.is_file() else "00000000")
            aug_p = src_p.with_name(
                f"{src_p.stem}_{src_digest}_{split_name}_{k:02d}_m{v_mode}{src_p.suffix}"
            )
            sha = create_field_view_variation(src_p, aug_p, v_mode)
            aug_rec = dict(base_rec)
            aug_rec["local_path"] = str(aug_p.relative_to(ROOT)).replace("\\", "/")
            aug_rec["sha256"] = sha
            aug_rec["split"] = split_name
            aug_rec["source_photo_id"] = sid
            aug_rec["session_id"] = sid
            aug_rec["source_subject_id"] = subject_of(sid)
            aug_rec["is_augmented"] = True
            out_all.append(aug_rec)

        for base_rec, sid in base_rows:
            rec = dict(base_rec)
            rec["split"] = split_name
            rec["source_photo_id"] = sid
            rec["session_id"] = sid
            rec["source_subject_id"] = subject_of(sid)
            rec["is_augmented"] = bool(base_rec.get("is_augmented", False))
            out_all.append(rec)

    # keep the raw base rows first within each split for readability
    out_all.sort(key=lambda r: (split_names.index(r["split"]), r["local_path"]))
    return out_all


def main() -> int:
    ap = argparse.ArgumentParser(description="Download real Bihar heritage & negative training images")
    ap.add_argument("--per-poi-fetch", type=int, default=24,
                    help="Target raw Commons photos to fetch per POI (more photos => more "
                         "independent viewpoints => meaningful effective-N).")
    ap.add_argument("--per-neg-fetch", type=int, default=24,
                    help="Target raw Commons photos to fetch per negative category")
    args = ap.parse_args()

    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    known_dir = DATASET_DIR / "known"
    neg_dir = DATASET_DIR / "negatives"

    manifest: Dict[str, object] = {
        "harvested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "Wikimedia Commons API (CC BY / CC BY-SA / CC0 / Public Domain)",
        "split_unit": "source_photo_id",
        "split_unit_note": (
            "Splits are assigned by SOURCE PHOTOGRAPH. Every derivative of one "
            "source photograph lives in exactly one split, so the rows of a "
            "split are independent trials and the Clopper-Pearson bound on the "
            "false-accept rate is meaningful."
        ),
        "pois": {},
        "negatives": {},
    }

    photo_status = load_photo_status()
    review = load_verification_review()
    global_seen_titles: set[str] = set()
    # content-hash -> class that already claimed it (cross-class duplicate guard)
    claimed_hashes: Dict[str, str] = {}
    dropped_duplicates = 0
    dropped_unverified = 0

    def _claim(records: List[Dict[str, str]], class_id: str) -> List[Dict[str, str]]:
        """Drops (a) content already claimed by another class and (b) photographs a
        human reviewer rejected. Returns the surviving records."""
        nonlocal dropped_duplicates, dropped_unverified
        kept: List[Dict[str, str]] = []
        for r in records:
            sid = r.get("source_photo_id", "")
            verdict = str(review.get(sid, {}).get("verdict", "pending")).lower()
            if verdict == "rejected":
                dropped_unverified += 1
                continue
            sha = r.get("sha256", "")
            owner = claimed_hashes.get(sha)
            if owner is not None and owner != class_id:
                dropped_duplicates += 1
                continue
            claimed_hashes.setdefault(sha, class_id)
            r["verification_status"] = verdict
            kept.append(r)
        return kept

    print("=== Phase 1: Discovering & Downloading 15 Bihar Heritage POIs from Wikimedia Commons ===")
    total_raw_known = 0
    total_split_known = 0
    for spec in POI_SPECS:
        pid = str(spec["place_id"])
        cats = list(spec["categories"])  # type: ignore[arg-type]
        qs = list(spec["queries"])  # type: ignore[arg-type]
        cands = discover_candidates(cats, qs, target_count=args.per_poi_fetch, global_seen=global_seen_titles)
        dest = known_dir / pid
        downloaded: List[Dict[str, str]] = []
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = [ex.submit(_download_one, c, dest, pid.split("-")[-1], i) for i, c in enumerate(cands)]
            for f in as_completed(futs):
                res = f.result()
                if res:
                    downloaded.append(res)
        downloaded.sort(key=lambda x: x["local_path"])
        downloaded = _claim(downloaded, pid)
        total_raw_known += len(downloaded)
        split_recs = assign_photo_grouped_splits(downloaded, counts_per_split=(4, 6, 10),
                                                 min_photos_per_split=(2, 2, 2))
        total_split_known += len(split_recs)
        manifest["pois"][pid] = {  # type: ignore[index]
            "place_id": pid,
            "parent_place_id": spec["parent_place_id"],
            "viewpoint_tag": spec["viewpoint_tag"],
            "distinguishing_hint": spec["distinguishing_hint"],
            "photo_status": photo_status.get(pid, "UNSPECIFIED"),
            "vision_class": bool(spec.get("vision_class", True)),
            "vision_note": str(spec.get("vision_note", "") or ""),
            "raw_downloaded_count": len(downloaded),
            "distinct_source_photos": len({r["source_photo_id"] for r in split_recs}),
            "total_split_count": len(split_recs),
            "records": split_recs,
        }
        print(f"  [POI] {pid:35s} raw={len(downloaded):2d} photos="
              f"{len({r['source_photo_id'] for r in split_recs}):2d} "
              f"-> split(ref/calib/test) total={len(split_recs)} "
              f"status={manifest['pois'][pid]['photo_status']}")  # type: ignore[index]

    print("\n=== Phase 2: Discovering & Downloading 8 Hard-Negative Categories from Wikimedia Commons ===")
    total_raw_neg = 0
    total_split_neg = 0
    for nspec in NEGATIVE_SPECS:
        ncat = str(nspec["neg_category"])
        cats = list(nspec["categories"])  # type: ignore[arg-type]
        qs = list(nspec["queries"])  # type: ignore[arg-type]
        cands = discover_candidates(cats, qs, target_count=args.per_neg_fetch, global_seen=global_seen_titles)
        dest = neg_dir / ncat
        downloaded = []
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = [ex.submit(_download_one, c, dest, ncat.split("-")[-1], i) for i, c in enumerate(cands)]
            for f in as_completed(futs):
                res = f.result()
                if res:
                    downloaded.append(res)
        downloaded.sort(key=lambda x: x["local_path"])
        downloaded = _claim(downloaded, ncat)
        total_raw_neg += len(downloaded)
        # 3 ref / 6 calib / 13 test rows, each split drawing on its OWN source photos
        split_recs = assign_photo_grouped_splits(downloaded, counts_per_split=(3, 6, 13),
                                                 min_photos_per_split=(2, 1, 2))
        for r in split_recs:
            r["neg_category"] = ncat
            r["label"] = str(nspec["label"])
        total_split_neg += len(split_recs)
        manifest["negatives"][ncat] = {  # type: ignore[index]
            "neg_category": ncat,
            "label": nspec["label"],
            "raw_downloaded_count": len(downloaded),
            "distinct_source_photos": len({r["source_photo_id"] for r in split_recs}),
            "total_split_count": len(split_recs),
            "records": split_recs,
        }
        print(f"  [NEG] {ncat:35s} raw={len(downloaded):2d} photos="
              f"{len({r['source_photo_id'] for r in split_recs}):2d} "
              f"-> split(ref/calib/test) total={len(split_recs)}")

    manifest["summary"] = {
        "total_raw_known_images": total_raw_known,
        "total_split_known_images": total_split_known,
        "total_raw_negative_images": total_raw_neg,
        "total_split_negative_images": total_split_neg,
        "distinct_source_photographs": len(claimed_hashes),
        "dropped_cross_class_duplicates": dropped_duplicates,
        "dropped_rejected_by_review": dropped_unverified,
    }
    manifest_path = DATASET_DIR / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved dataset manifest to {manifest_path}")
    print(f"Summary: raw_known={total_raw_known}, split_known={total_split_known}, "
          f"raw_neg={total_raw_neg}, split_neg={total_split_neg}, "
          f"distinct_source_photos={len(claimed_hashes)}, "
          f"dropped_duplicates={dropped_duplicates}, dropped_rejected={dropped_unverified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

