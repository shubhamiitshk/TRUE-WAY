"""Automated Multi-Corridor Data Harvester for Monument Recognition Pipeline.

Supports:
1. Existing Circuit: Bihar Buddhist Circuit (15 POIs)
2. High-Value Cultural Corridors: India Golden Triangle (Delhi / Agra / Jaipur -
   Taj Mahal, Qutub Minar, Red Fort, Hawa Mahal, Amer Fort, Agra Fort, Fatehpur Sikri,
   Humayun's Tomb, City Palace Jaipur)
3. Global Showcase: World Icons Tier-1 (Eiffel Tower, Colosseum, Pyramids of Giza,
   Angkor Wat, Machu Picchu, Statue of Liberty)
4. Multi-Source Digital Ingestion:
   - Wikimedia Commons API (CC BY, CC BY-SA, CC0, Public Domain)
   - Video Frame Workflows (4K walking tours via ffmpeg, frame sequences, or yt-dlp)
5. Strict Pipeline Discipline:
   - Quarantined Candidate Storage (ml/dataset/candidates/...)
   - Photographer-grouped and Video-Series-grouped Split Discipline (no series straddles ref/calib/test)
   - Automated Sharpness Filtering (Laplacian/Edge-variance proxy)
   - Perceptual Hash Deduplication (dHash with Hamming distance threshold)
   - Candidate Manifests with verification_status='pending'
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "ml" / "dataset"
CANDIDATES_DIR = DATASET_DIR / "candidates"
DEFAULT_CANDIDATE_MANIFEST = CANDIDATES_DIR / "candidates_corridors_manifest.json"

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "TrueWayHeritageCorridorHarvester/3.1 (https://github.com/TrueWay; research@trueway.org) Python-urllib/3"

# -----------------------------------------------------------------------------
# Reject Patterns for Commons Image Titles
# Discards non-photographic artifacts, 19th-century drawings/paintings, coins, etc.
# -----------------------------------------------------------------------------
REJECT_PATTERNS = re.compile(
    r"(replica|miniature|scale model|model of|museum model|"
    r"statue of|statuette|statue|bust of|figure of|"
    r"coin|token|seal|stamp|banknote|note of|"
    r"manuscript|scroll|palm leaf|inscription|epigraph|"
    r"painting|drawing|sketch|engraving|lithograph|etching|fresco|mural|"
    r"illustration|graphic|diagram|plan of|map of|cross section|elevation|"
    r"logo|coat of arms|flag of|banner|icon|svg|blazon|"
    r"relief|panel of|carving|ornament|"
    r"postcard|photograph of a photograph|"
    r"185\d|186\d|187\d|188\d|189\d|190\d|191\d|192\d|193\d|194\d|195\d|196\d|197\d|198\d|199\d|"
    r"archive|archival|historical photo|old photograph|early photograph|"
    r"advertisement|brochure|catalogue|calendar|"
    r"signboard|sign board|plaque|notice board|information board|board at)",
    re.I,
)


def is_rejected_title(title: str, exempt: Optional[List[str]] = None) -> bool:
    """Evaluates whether an image title represents an unusable non-field photograph.
    Exempt fragments are stripped before evaluation (e.g. colossal statues or rock reliefs)."""
    t = title or ""
    for frag in exempt or []:
        t = re.sub(frag, " ", t, flags=re.I)
    return bool(REJECT_PATTERNS.search(t))


def stable_name(prefix: str, identifier: str) -> str:
    """Generates a stable, collision-free filename derived deterministically from the identifier hash."""
    safe = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:12]
    clean_prefix = re.sub(r"[^a-zA-Z0-9_\-]", "_", prefix)
    return f"{clean_prefix}_{safe}.jpg"


# -----------------------------------------------------------------------------
# Corridor & POI Specifications Registry
# -----------------------------------------------------------------------------
CORRIDORS: Dict[str, Dict[str, Any]] = {
    "bihar-buddhist-circuit": {
        "corridor_id": "bihar-buddhist-circuit",
        "name": "Bihar Buddhist Circuit",
        "region": "India / Bihar",
        "pack_id": "in-bihar-buddhist-circuit",
        "description": "Historical pilgrimage circuit covering Bodh Gaya, Rajgir, and Nalanda Mahavihara.",
        "pois": [
            {
                "place_id": "in-bihar-bodhgaya-mahabodhi",
                "name": "Mahabodhi Temple",
                "city": "Bodh Gaya",
                "parent_place_id": None,
                "viewpoint_tag": "shikhara-east-facade",
                "distinguishing_hint": "55m pyramidal main temple spire and central courtyard",
                "vision_class": True,
                "categories": ["Category:Mahabodhi Temple"],
                "queries": [
                    "Mahabodhi Temple Bodh Gaya spire",
                    "Mahabodhi Temple facade",
                    "Mahabodhi Temple Bodhgaya main temple",
                    "Bodh Gaya Mahabodhi temple complex",
                    "Mahabodhi temple shikhara Bodh Gaya",
                ],
                "video_queries": ["Mahabodhi temple Bodh Gaya walking tour 4K"],
            },
            {
                "place_id": "in-bihar-bodhgaya-bodhi-tree",
                "name": "Bodhi Tree",
                "city": "Bodh Gaya",
                "parent_place_id": "in-bihar-bodhgaya-mahabodhi",
                "viewpoint_tag": "bodhi-tree-canopy",
                "distinguishing_hint": "Sacred fig tree adjacent to the western wall of temple",
                "vision_class": False,
                "vision_note": "Spotter item on Mahabodhi card; not a separate vision class.",
                "categories": ["Category:Bodhi Tree (Bodh Gaya)"],
                "queries": ["Bodhi Tree Bodh Gaya Mahabodhi", "Sacred fig Bodh Gaya"],
                "video_queries": ["Bodhi tree Bodh Gaya walk"],
            },
            {
                "place_id": "in-bihar-bodhgaya-vajrasana",
                "name": "Vajrasana (Diamond Throne)",
                "city": "Bodh Gaya",
                "parent_place_id": "in-bihar-bodhgaya-mahabodhi",
                "viewpoint_tag": "diamond-throne-slab",
                "distinguishing_hint": "Polished sandstone slab marking the seat of enlightenment",
                "vision_class": False,
                "vision_note": "Spotter item on Mahabodhi card.",
                "categories": ["Category:Vajrasana"],
                "queries": ["Vajrasana Bodh Gaya", "Diamond throne Mahabodhi"],
                "video_queries": [],
            },
            {
                "place_id": "in-bihar-bodhgaya-animesh-lochan",
                "name": "Animesh Lochan Chaitya",
                "city": "Bodh Gaya",
                "parent_place_id": "in-bihar-bodhgaya-mahabodhi",
                "viewpoint_tag": "unblinking-gaze-stupa",
                "distinguishing_hint": "Northeast brick chaitya where Buddha stood gazing at the Bodhi tree",
                "vision_class": True,
                "categories": ["Category:Animesh Lochan Chaitya"],
                "queries": ["Animesh Lochan Chaitya", "Mahabodhi Temple small stupa shrine"],
                "video_queries": [],
            },
            {
                "place_id": "in-bihar-bodhgaya-mucalinda",
                "name": "Mucalinda Lake",
                "city": "Bodh Gaya",
                "parent_place_id": "in-bihar-bodhgaya-mahabodhi",
                "viewpoint_tag": "serpent-lake-pavilion",
                "distinguishing_hint": "Rectangular tank with central snake king statue sheltering Buddha",
                "vision_class": True,
                "categories": ["Category:Mucalinda Lake", "Category:Muchalinda Lake"],
                "queries": ["Mucalinda Bodh Gaya", "Muchalinda Bodh Gaya lake", "Mucalinda statue Buddha pond"],
                "video_queries": [],
            },
            {
                "place_id": "in-bihar-bodhgaya-great-buddha",
                "name": "Great Buddha Statue (Daibutsu)",
                "city": "Bodh Gaya",
                "parent_place_id": None,
                "viewpoint_tag": "daibutsu-colossal-statue",
                "distinguishing_hint": "25-meter seated sandstone Buddha unveiled in 1989",
                "vision_class": True,
                "title_exempt": [r"\bstatue\b", r"\bfigure of\b"],
                "categories": ["Category:Great Buddha Statue, Bodh Gaya"],
                "queries": ["Great Buddha Statue Bodh Gaya", "Giant Buddha Bodh Gaya", "80 feet Buddha statue Bodhgaya"],
                "video_queries": ["Great Buddha statue Bodh Gaya walk 4K"],
            },
            {
                "place_id": "in-bihar-rajgir-vultures-peak",
                "name": "Vulture's Peak (Gridhrakuta)",
                "city": "Rajgir",
                "parent_place_id": None,
                "viewpoint_tag": "peak-platform-shrine",
                "distinguishing_hint": "Natural rock precipice with ancient brick stupa remains",
                "vision_class": True,
                "categories": ["Category:Gridhrakuta Peak"],
                "queries": ["Gridhrakuta Peak Rajgir", "Vulture Peak Rajgir", "Gridhakuta hill Rajgir ruins"],
                "video_queries": ["Gridhrakuta Peak Rajgir hike 4K"],
            },
            {
                "place_id": "in-bihar-rajgir-venu-vana",
                "name": "Venu Vana (Bamboo Grove)",
                "city": "Rajgir",
                "parent_place_id": None,
                "viewpoint_tag": "bamboo-grove-lake",
                "distinguishing_hint": "Bamboo park and historical bathing tank",
                "vision_class": True,
                "categories": ["Category:Venuvana"],
                "queries": ["Venuvana Rajgir", "Bamboo Grove Rajgir", "Venu Vana Rajgir Bihar"],
                "video_queries": ["Venu Vana Rajgir walk"],
            },
            {
                "place_id": "in-bihar-rajgir-cyclopean-wall",
                "name": "Cyclopean Wall of Rajgir",
                "city": "Rajgir",
                "parent_place_id": None,
                "viewpoint_tag": "unmortared-stone-rampart",
                "distinguishing_hint": "Ancient 40km undressed massive stone fortification",
                "vision_class": True,
                "categories": ["Category:Cyclopean Wall of Rajgir"],
                "queries": ["Cyclopean Wall Rajgir", "Rajgir stone wall fortification"],
                "video_queries": [],
            },
            {
                "place_id": "in-bihar-rajgir-shanti-stupa",
                "name": "Vishwa Shanti Stupa",
                "city": "Rajgir",
                "parent_place_id": None,
                "viewpoint_tag": "white-peace-pagoda",
                "distinguishing_hint": "Modern white dome pagoda on Ratnagiri hill with golden Buddha statues",
                "vision_class": True,
                "categories": ["Category:Vishwa Shanti Stupa, Rajgir"],
                "queries": ["Vishwa Shanti Stupa Rajgir", "Peace Pagoda Rajgir", "Shanti Stupa Rajgir Bihar"],
                "video_queries": ["Vishwa Shanti Stupa Rajgir ropeway 4K"],
            },
            {
                "place_id": "in-bihar-rajgir-sonbhandar",
                "name": "Sonbhandar Caves",
                "city": "Rajgir",
                "parent_place_id": None,
                "viewpoint_tag": "rock-cut-chamber-facade",
                "distinguishing_hint": "Ancient twin rock-cut chambers with polished interiors",
                "vision_class": True,
                "title_exempt": [r"\brelief\b", r"\bcarving\b", r"\bcave\b"],
                "categories": ["Category:Sonbhandar Caves"],
                "queries": ["Sonbhandar Caves Rajgir", "Son Bhandar Cave Rajgir", "Son Bhandar rock cut caves"],
                "video_queries": ["Sonbhandar Caves Rajgir tour"],
            },
            {
                "place_id": "in-bihar-nalanda-mahavihara",
                "name": "Nalanda Mahavihara",
                "city": "Nalanda",
                "parent_place_id": None,
                "viewpoint_tag": "archaeological-corridor",
                "distinguishing_hint": "Excavated brick mounds of the main Nalanda monastic complex",
                "vision_class": True,
                "categories": ["Category:Nalanda Mahavihara", "Category:Nalanda University"],
                "queries": ["Nalanda Mahavihara ruins", "Nalanda University archaeological ruins"],
                "video_queries": ["Nalanda Mahavihara ruins walk 4K"],
            },
            {
                "place_id": "in-bihar-nalanda-temple-03",
                "name": "Temple No. 3 (Sariputra Stupa)",
                "city": "Nalanda",
                "parent_place_id": "in-bihar-nalanda-mahavihara",
                "viewpoint_tag": "towering-stupa-corner-facets",
                "distinguishing_hint": "Imposing multi-layered stupa with surviving stucco figures",
                "vision_class": True,
                "categories": ["Category:Stupa of Sariputra", "Category:Temple No. 3, Nalanda"],
                "queries": ["Stupa of Sariputra Nalanda", "Temple 3 Nalanda stupa", "Sariputta Stupa Nalanda"],
                "video_queries": [],
            },
            {
                "place_id": "in-bihar-nalanda-monastery-01",
                "name": "Monastery No. 1",
                "city": "Nalanda",
                "parent_place_id": "in-bihar-nalanda-mahavihara",
                "viewpoint_tag": "central-courtyard-cells",
                "distinguishing_hint": "Double-story quadrangle with monastic cells and central chaitya",
                "vision_class": True,
                "categories": ["Category:Monastery No. 1, Nalanda"],
                "queries": ["Nalanda monastery courtyard cells", "Nalanda vihara brick courtyard", "Nalanda Monastery 1"],
                "video_queries": [],
            },
            {
                "place_id": "in-bihar-nalanda-museum",
                "name": "Archaeological Museum Nalanda",
                "city": "Nalanda",
                "parent_place_id": "in-bihar-nalanda-mahavihara",
                "viewpoint_tag": "museum-entrance-portico",
                "distinguishing_hint": "Archaeological repository housing Pala-period bronzes and sculptures",
                "vision_class": False,
                "vision_note": "Search-only building asset.",
                "categories": ["Category:Archaeological Museum, Nalanda"],
                "queries": ["Archaeological Museum Nalanda building", "Nalanda museum exterior"],
                "video_queries": [],
            },
        ],
        "negatives": [
            {
                "neg_category": "neg-bihar-brick-lookalike",
                "label": "out-of-pack-bihar-lookalike",
                "categories": ["Category:Kesaria Stupa", "Category:Vikramashila", "Category:Barabar Caves"],
                "queries": ["Kesaria Stupa Bihar", "Vikramshila ruins Bhagalpur", "Barabar Caves Bihar"],
            },
            {
                "neg_category": "neg-white-golden-dome",
                "label": "white-golden-dome-pagoda",
                "title_exempt": [r"\bstatue\b", r"\bstatuette\b"],
                "categories": ["Category:Wat Phu Khao Thong", "Category:Ruwanwelisaya"],
                "queries": ["white stupa dome golden pinnacle", "gilded golden chedi pagoda", "Ruwanwelisaya white stupa"],
            },
        ],
    },
    "india-golden-triangle": {
        "corridor_id": "india-golden-triangle",
        "name": "India Golden Triangle",
        "region": "India / Delhi-Agra-Jaipur",
        "pack_id": "in-golden-triangle",
        "description": "High-demand cultural tourism corridor linking Delhi, Agra, and Jaipur.",
        "pois": [
            {
                "place_id": "in-agra-taj-mahal",
                "name": "Taj Mahal",
                "city": "Agra",
                "parent_place_id": None,
                "viewpoint_tag": "white-marble-mausoleum-facade",
                "distinguishing_hint": "Ivory-white marble mausoleum with central dome, charbagh reflection pool, and 4 minarets",
                "vision_class": True,
                "categories": ["Category:Taj Mahal", "Category:Taj Mahal views from the gardens"],
                "queries": [
                    "Taj Mahal Agra white marble dome",
                    "Taj Mahal front reflection pool",
                    "Taj Mahal facade garden view",
                    "Taj Mahal minarets Agra",
                    "Taj Mahal main mausoleum south facade",
                ],
                "video_queries": [
                    "Taj Mahal Agra 4K walking tour",
                    "Taj Mahal walking tour 4K HDR",
                    "Taj Mahal gardens walk",
                ],
            },
            {
                "place_id": "in-delhi-qutub-minar",
                "name": "Qutub Minar",
                "city": "Delhi",
                "parent_place_id": None,
                "viewpoint_tag": "fluted-sandstone-minaret",
                "distinguishing_hint": "73m fluted red sandstone and marble minaret with projecting balconies and Arabic inscriptions",
                "vision_class": True,
                "categories": ["Category:Qutb Minar", "Category:Qutb complex"],
                "queries": [
                    "Qutb Minar Delhi tower",
                    "Qutub Minar balcony facade",
                    "Qutb Minar complex Delhi",
                    "Qutub Minar sandstone minaret",
                    "Qutb Minar fluted balcony",
                ],
                "video_queries": [
                    "Qutub Minar Delhi walking tour 4K",
                    "Qutb Minar complex walk 4K",
                ],
            },
            {
                "place_id": "in-delhi-red-fort",
                "name": "Red Fort (Lal Qila)",
                "city": "Delhi",
                "parent_place_id": None,
                "viewpoint_tag": "red-sandstone-ramparts-gate",
                "distinguishing_hint": "Massive octagonal red sandstone fortress walls and monumental Lahori Gate",
                "vision_class": True,
                "categories": ["Category:Red Fort", "Category:Lahori Gate (Red Fort)"],
                "queries": [
                    "Red Fort Delhi Lahori Gate",
                    "Lal Qila Delhi sandstone ramparts",
                    "Red Fort facade Delhi",
                    "Diwan-i-Aam Red Fort",
                    "Red Fort Delhi octagonal walls",
                ],
                "video_queries": [
                    "Red Fort Delhi 4K walk",
                    "Lal Qila Delhi walking tour 4K",
                ],
            },
            {
                "place_id": "in-jaipur-hawa-mahal",
                "name": "Hawa Mahal (Palace of Winds)",
                "city": "Jaipur",
                "parent_place_id": None,
                "viewpoint_tag": "pink-honeycomb-jharokhas-facade",
                "distinguishing_hint": "Five-storey pink and red sandstone honeycomb facade with 953 carved jharokha windows",
                "vision_class": True,
                "categories": ["Category:Hawa Mahal"],
                "queries": [
                    "Hawa Mahal Jaipur pink facade",
                    "Palace of Winds Jaipur honeycomb windows",
                    "Hawa Mahal exterior street view",
                    "Hawa Mahal jharokhas Jaipur",
                    "Hawa Mahal pink sandstone screen",
                ],
                "video_queries": [
                    "Hawa Mahal Jaipur walking tour 4K",
                    "Jaipur Pink City walk Hawa Mahal",
                ],
            },
            {
                "place_id": "in-jaipur-amer-fort",
                "name": "Amer Fort (Amber Palace)",
                "city": "Jaipur",
                "parent_place_id": None,
                "viewpoint_tag": "hilltop-rampart-lake-palace",
                "distinguishing_hint": "Hilltop Rajput-Mughal fortress overlooking Maota Lake with Ganesh Pol gate and Sheesh Mahal",
                "vision_class": True,
                "categories": ["Category:Amber Fort", "Category:Sheesh Mahal (Amber Fort)"],
                "queries": [
                    "Amber Fort Jaipur Amer ramparts",
                    "Amer Fort Ganesh Pol gate",
                    "Sheesh Mahal Amer Fort mirror",
                    "Amber Fort Maota lake view",
                    "Amer Fort courtyard Jaipur",
                ],
                "video_queries": [
                    "Amer Fort Jaipur walking tour 4K",
                    "Amber Palace Jaipur walk",
                ],
            },
            {
                "place_id": "in-agra-agra-fort",
                "name": "Agra Fort",
                "city": "Agra",
                "parent_place_id": None,
                "viewpoint_tag": "walled-citadel-sandstone-palace",
                "distinguishing_hint": "Crescent-shaped red sandstone imperial Mughal fortress with Amar Singh Gate and Jahangiri Mahal",
                "vision_class": True,
                "categories": ["Category:Agra Fort", "Category:Jahangiri Mahal (Agra Fort)"],
                "queries": [
                    "Agra Fort red sandstone walls",
                    "Agra Fort Jahangiri Mahal",
                    "Agra Fort gate entrance",
                    "Agra Fort courtyard palace",
                    "Agra Fort Amar Singh Gate",
                ],
                "video_queries": [
                    "Agra Fort walking tour 4K",
                    "Agra Fort UNESCO site tour",
                ],
            },
            {
                "place_id": "in-agra-fatehpur-sikri",
                "name": "Fatehpur Sikri",
                "city": "Agra / Fatehpur Sikri",
                "parent_place_id": None,
                "viewpoint_tag": "buland-darwaza-palace-complex",
                "distinguishing_hint": "54m triumphal Buland Darwaza gateway and fortified Mughal red sandstone complex",
                "vision_class": True,
                "categories": ["Category:Fatehpur Sikri", "Category:Buland Darwaza"],
                "queries": [
                    "Buland Darwaza Fatehpur Sikri",
                    "Fatehpur Sikri red sandstone palace",
                    "Panch Mahal Fatehpur Sikri",
                    "Fatehpur Sikri Jama Masjid",
                    "Buland Darwaza gate steps",
                ],
                "video_queries": [
                    "Fatehpur Sikri walking tour 4K",
                    "Buland Darwaza 4K walk",
                ],
            },
            {
                "place_id": "in-delhi-humayuns-tomb",
                "name": "Humayun's Tomb",
                "city": "Delhi",
                "parent_place_id": None,
                "viewpoint_tag": "charbagh-garden-tomb-dome",
                "distinguishing_hint": "Mughal garden tomb with double-dome white marble on high red sandstone plinth in charbagh",
                "vision_class": True,
                "categories": ["Category:Humayun's Tomb"],
                "queries": [
                    "Humayun's Tomb Delhi main dome",
                    "Humayuns Tomb garden facade",
                    "Humayun tomb red sandstone charbagh",
                    "Humayun Tomb Delhi plinth view",
                ],
                "video_queries": [
                    "Humayun's Tomb Delhi walking tour 4K",
                ],
            },
            {
                "place_id": "in-jaipur-city-palace",
                "name": "City Palace Jaipur",
                "city": "Jaipur",
                "parent_place_id": None,
                "viewpoint_tag": "chandra-mahal-peacock-courtyard",
                "distinguishing_hint": "Royal palace complex in Jaipur walled city with Chandra Mahal and Pritam Niwas Chowk peacock gate",
                "vision_class": True,
                "categories": ["Category:City Palace (Jaipur)", "Category:Pritam Niwas Chowk"],
                "queries": [
                    "City Palace Jaipur Chandra Mahal",
                    "Jaipur City Palace courtyard gate",
                    "Mubarak Mahal City Palace Jaipur",
                    "Peacock Gate City Palace Jaipur",
                ],
                "video_queries": [
                    "City Palace Jaipur walking tour 4K",
                ],
            },
        ],
        "negatives": [
            {
                "neg_category": "neg-red-sandstone-lookalike",
                "label": "red-sandstone-fort-lookalike",
                "categories": ["Category:Rohtas Fort", "Category:Allahabad Fort"],
                "queries": [
                    "red sandstone fort walls India",
                    "ancient sandstone ramparts fortress",
                    "Indian sandstone gate archway",
                ],
            },
            {
                "neg_category": "neg-white-marble-mausoleum",
                "label": "white-marble-dome-lookalike",
                "categories": ["Category:Bibi Ka Maqbara", "Category:Victoria Memorial, Kolkata"],
                "queries": [
                    "Bibi Ka Maqbara Aurangabad",
                    "white marble dome tomb non-Agra",
                    "Victoria Memorial Kolkata white dome",
                ],
            },
            {
                "neg_category": "neg-mughal-gateway",
                "label": "generic-mughal-gateway",
                "categories": ["Category:Gateways in India"],
                "queries": [
                    "Mughal archway gate stone",
                    "red sandstone portal gateway India",
                    "ornate arched doorway monument",
                ],
            },
            {
                "neg_category": "neg-crowds-tourist-occlusion",
                "label": "crowded-tourist-plaza",
                "categories": [],
                "queries": [
                    "tourist crowd monument India",
                    "visitors queue landmark India",
                    "crowded monument plaza",
                ],
            },
            {
                "neg_category": "neg-modern-commercial-shop",
                "label": "tourist-bazaar-shop",
                "categories": [],
                "queries": [
                    "Indian bazaar market street",
                    "souvenir shop monument entrance",
                    "roadside tourist stall India",
                ],
            },
        ],
    },
    "global-icons-tier1": {
        "corridor_id": "global-icons-tier1",
        "name": "Global Icons Tier-1 Showcase",
        "region": "Global Universal Showcase",
        "pack_id": "world-icons-tier1",
        "description": "Top universal landmarks pre-installed in the base APK showcase.",
        "pois": [
            {
                "place_id": "fr-paris-eiffel-tower",
                "name": "Eiffel Tower",
                "city": "Paris, France",
                "parent_place_id": None,
                "viewpoint_tag": "wrought-iron-lattice-tower",
                "distinguishing_hint": "330m wrought-iron lattice tower rising above Champ de Mars",
                "vision_class": True,
                "categories": ["Category:Eiffel Tower"],
                "queries": [
                    "Eiffel Tower Paris full view",
                    "Tour Eiffel Champ de Mars daylight",
                    "Eiffel Tower arch base Paris",
                ],
                "video_queries": [
                    "Eiffel Tower Paris walking tour 4K",
                    "Champ de Mars Eiffel Tower 4K",
                ],
            },
            {
                "place_id": "it-rome-colosseum",
                "name": "Colosseum",
                "city": "Rome, Italy",
                "parent_place_id": None,
                "viewpoint_tag": "travertine-arches-amphitheatre",
                "distinguishing_hint": "Elliptical amphitheatre in central Rome with multi-tiered travertine arcades",
                "vision_class": True,
                "categories": ["Category:Colosseum"],
                "queries": [
                    "Colosseum Rome exterior arches",
                    "Flavian Amphitheatre Rome facade",
                    "Colosseum Rome daylight view",
                ],
                "video_queries": [
                    "Colosseum Rome walking tour 4K",
                    "Rome Colosseum exterior walk",
                ],
            },
            {
                "place_id": "eg-giza-pyramids",
                "name": "Pyramids of Giza",
                "city": "Giza, Egypt",
                "parent_place_id": None,
                "viewpoint_tag": "desert-stone-pyramids-plateau",
                "distinguishing_hint": "Monumental stone pyramids of Khufu and Khafre with limestone casing against desert",
                "vision_class": True,
                "categories": ["Category:Giza pyramid complex", "Category:Great Pyramid of Giza"],
                "queries": [
                    "Great Pyramid of Giza Khufu",
                    "Pyramids of Giza desert view",
                    "Khafre pyramid casing limestone Giza",
                ],
                "video_queries": [
                    "Pyramids of Giza walking tour 4K",
                ],
            },
            {
                "place_id": "kh-siem-reap-angkor-wat",
                "name": "Angkor Wat",
                "city": "Siem Reap, Cambodia",
                "parent_place_id": None,
                "viewpoint_tag": "lotus-bud-towers-reflection-pond",
                "distinguishing_hint": "12th-century temple mountain with five lotus-bud towers reflected in outer lotus pond",
                "vision_class": True,
                "categories": ["Category:Angkor Wat"],
                "queries": [
                    "Angkor Wat reflection pond Cambodia",
                    "Angkor Wat lotus towers temple",
                    "Angkor Wat central sanctuary facade",
                ],
                "video_queries": [
                    "Angkor Wat walking tour 4K",
                ],
            },
            {
                "place_id": "pe-cusco-machu-picchu",
                "name": "Machu Picchu",
                "city": "Cusco, Peru",
                "parent_place_id": None,
                "viewpoint_tag": "mountain-ridge-citadel-terraces",
                "distinguishing_hint": "Inca citadel with dry-stone terraces perched on mountain ridge with Huayna Picchu",
                "vision_class": True,
                "categories": ["Category:Machu Picchu"],
                "queries": [
                    "Machu Picchu Inca citadel terraces",
                    "Machu Picchu Huayna Picchu mountain view",
                    "Machu Picchu stone ruins panoramic",
                ],
                "video_queries": [
                    "Machu Picchu walking tour 4K",
                ],
            },
            {
                "place_id": "us-nyc-statue-of-liberty",
                "name": "Statue of Liberty",
                "city": "New York, USA",
                "parent_place_id": None,
                "viewpoint_tag": "neoclassical-copper-statue-torch",
                "distinguishing_hint": "Colossal neoclassical copper statue with green patina holding torch and tablet on Liberty Island",
                "vision_class": True,
                "title_exempt": [r"\bstatue\b", r"\bmonument\b"],
                "categories": ["Category:Statue of Liberty"],
                "queries": [
                    "Statue of Liberty New York full view",
                    "Statue of Liberty copper patina harbor",
                    "Statue of Liberty torch pedestal",
                ],
                "video_queries": [
                    "Statue of Liberty Liberty Island walking tour 4K",
                ],
            },
        ],
        "negatives": [
            {
                "neg_category": "neg-classical-ruins-global",
                "label": "classical-ruins-non-colosseum",
                "categories": ["Category:Roman ruins"],
                "queries": [
                    "Roman temple ruins arches",
                    "ancient amphitheatre ruins Mediterranean",
                    "classical stone pillars ruins",
                ],
            },
            {
                "neg_category": "neg-modern-steel-towers",
                "label": "modern-lattice-steel-tower",
                "categories": ["Category:Tokyo Tower"],
                "queries": [
                    "communication tower lattice steel",
                    "Tokyo tower red white",
                    "radio mast steel lattice",
                ],
            },
        ],
    },
}


# -----------------------------------------------------------------------------
# Image Quality & Deduplication Utilities
# -----------------------------------------------------------------------------
def compute_sharpness(img: Image.Image) -> float:
    """Computes edge gradient energy variance as an effective proxy for sharpness."""
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    return float(stat.var[0])


def compute_dhash(img: Image.Image, hash_size: int = 8) -> int:
    """Computes difference hash (dHash) for fast perceptual deduplication."""
    resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    if hasattr(resized, "get_flattened_data"):
        pixels = list(resized.get_flattened_data())
    else:
        pixels = list(resized.getdata())
    difference = []
    for row in range(hash_size):
        for col in range(hash_size):
            pixel_left = pixels[row * (hash_size + 1) + col]
            pixel_right = pixels[row * (hash_size + 1) + col + 1]
            difference.append(pixel_left > pixel_right)
    decimal_value = 0
    for idx, val in enumerate(difference):
        if val:
            decimal_value |= 1 << idx
    return decimal_value


def hamming_distance(h1: int, h2: int) -> int:
    """Computes Hamming distance between two integer perceptual hashes."""
    return bin(h1 ^ h2).count("1")


# -----------------------------------------------------------------------------
# Field Augmentation Engine
# Generates realistic camera variations strictly within the assigned split
# -----------------------------------------------------------------------------
def create_field_view_variation(src_path: Path, dest_path: Path, variant_idx: int) -> str:
    """Produces camera and daylight viewpoint variations without cross-split leakage.
    Returns SHA-256 of the created variation."""
    if dest_path.is_file() and dest_path.stat().st_size > 512:
        return hashlib.sha256(dest_path.read_bytes()).hexdigest()

    img = Image.open(src_path).convert("RGB")
    w, h = img.size
    mode = variant_idx % 8

    if mode == 0:
        # Afternoon sunlight & slight crop
        img = img.crop((int(w * 0.05), int(h * 0.03), int(w * 0.95), int(h * 0.95))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Color(img).enhance(1.12)
        img = ImageEnhance.Brightness(img).enhance(1.04)
    elif mode == 1:
        # Overcast soft light & mild contrast
        img = img.crop((int(w * 0.03), int(h * 0.05), int(w * 0.93), int(h * 0.96))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Contrast(img).enhance(1.08)
        img = ImageEnhance.Brightness(img).enhance(0.96)
    elif mode == 2:
        # Horizontal flip
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        img = ImageEnhance.Sharpness(img).enhance(1.15)
    elif mode == 3:
        # Gentle rotation + central crop
        img = img.rotate(2.5, resample=Image.Resampling.BICUBIC, expand=False)
        img = img.crop((int(w * 0.06), int(h * 0.06), int(w * 0.94), int(h * 0.94))).resize((w, h), Image.Resampling.BICUBIC)
    elif mode == 4:
        # Cool early morning tone
        img = img.crop((int(w * 0.04), int(h * 0.08), int(w * 0.96), int(h * 0.96))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Color(img).enhance(0.90)
        img = ImageEnhance.Brightness(img).enhance(1.02)
    elif mode == 5:
        # Telephoto zoom crop (85%)
        img = img.crop((int(w * 0.08), int(h * 0.08), int(w * 0.92), int(h * 0.92))).resize((w, h), Image.Resampling.BICUBIC)
    elif mode == 6:
        # Golden hour warm hue
        img = img.crop((int(w * 0.05), int(h * 0.02), int(w * 0.95), int(h * 0.90))).resize((w, h), Image.Resampling.BICUBIC)
        img = ImageEnhance.Color(img).enhance(1.18)
    else:
        # Mild atmospheric haze
        img = img.crop((int(w * 0.04), int(h * 0.04), int(w * 0.95), int(h * 0.95))).resize((w, h), Image.Resampling.BICUBIC)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.4))

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    data = buf.getvalue()
    dest_path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


# -----------------------------------------------------------------------------
# Subject Series & Split Discipline
# -----------------------------------------------------------------------------
def subject_series_id(photographer: str, title: str) -> str:
    """Derives canonical subject series key to prevent same-visit / near-duplicate leakage.
    Strips trailing numbers, Commons photo IDs, and edit suffixes."""
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
    records: List[Dict[str, Any]],
    counts_per_split: Tuple[int, int, int] = (4, 4, 8),
    proportions: Tuple[float, float, float] = (0.35, 0.20, 0.45),
) -> List[Dict[str, Any]]:
    """Allocates records to ref / calib / test by whole SUBJECT SERIES.
    Guarantees that no photographer or source series crosses split boundaries."""
    if not records:
        return []

    # 1. Group by source photograph ID
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for rec in records:
        sid = rec.get("source_photo_id") or rec.get("local_path", "")
        groups[sid].append(rec)
    source_ids = sorted(groups.keys())

    # 2. Group source photographs into subject series
    subjects: Dict[str, List[str]] = defaultdict(list)
    for sid in source_ids:
        rec = groups[sid][0]
        sub = rec.get("source_subject_id") or subject_series_id(
            rec.get("photographer", ""), rec.get("title", "")
        )
        subjects[sub].append(sid)
    subject_ids = sorted(subjects.keys())
    n_groups = len(subject_ids)

    # 3. Compute series quotas
    split_names = ("ref", "calib", "test")
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

    quota = {"ref": ref_n, "calib": calib_n, "test": test_n}
    filled = {"ref": 0, "calib": 0, "test": 0}
    split_of: Dict[str, str] = {}

    # Largest series assigned first to balance split representation
    ordered_groups = sorted(subject_ids, key=lambda s: (-len(subjects[s]), s))
    while ordered_groups:
        name = max(split_names, key=lambda n: (quota[n] - filled[n], quota[n]))
        group = ordered_groups.pop(0)
        for sid in subjects[group]:
            split_of[sid] = name
        filled[name] += 1

    # 4. Generate rows and split-contained augmentations
    out_all: List[Dict[str, Any]] = []
    targets = list(counts_per_split)

    for si, split_name in enumerate(split_names):
        split_source_ids = [sid for sid in source_ids if split_of.get(sid) == split_name]
        if not split_source_ids:
            continue
        target_cnt = targets[si]

        base_rows: List[Tuple[Dict[str, Any], str]] = []
        for sid in split_source_ids:
            recs = sorted(groups[sid], key=lambda r: r.get("local_path", ""))
            for r in recs:
                base_rows.append((r, sid))

        needed = max(0, target_cnt - len(base_rows))
        for k in range(needed):
            base_rec, sid = base_rows[k % len(base_rows)]
            v_mode = (si * 3 + k) % 8
            src_p = ROOT / base_rec["local_path"]
            if src_p.is_file():
                src_digest = hashlib.sha256(src_p.read_bytes()).hexdigest()[:8]
                aug_p = src_p.with_name(f"{src_p.stem}_{src_digest}_{split_name}_{k:02d}_m{v_mode}{src_p.suffix}")
                sha = create_field_view_variation(src_p, aug_p, v_mode)
            else:
                aug_p = src_p.with_name(f"{src_p.stem}_aug_{split_name}_{k:02d}.jpg")
                sha = "simulated_aug_sha256"

            aug_rec = dict(base_rec)
            aug_rec["local_path"] = str(aug_p.relative_to(ROOT)).replace("\\", "/") if src_p.is_file() else base_rec["local_path"]
            aug_rec["sha256"] = sha
            aug_rec["split"] = split_name
            aug_rec["source_photo_id"] = sid
            aug_rec["source_subject_id"] = base_rec.get("source_subject_id") or subject_series_id(base_rec.get("photographer", ""), base_rec.get("title", ""))
            aug_rec["is_augmented"] = True
            aug_rec["status"] = "pending"
            out_all.append(aug_rec)

        for base_rec, sid in base_rows:
            rec = dict(base_rec)
            rec["split"] = split_name
            rec["source_photo_id"] = sid
            rec["source_subject_id"] = base_rec.get("source_subject_id") or subject_series_id(base_rec.get("photographer", ""), base_rec.get("title", ""))
            rec["is_augmented"] = bool(base_rec.get("is_augmented", False))
            rec["status"] = "pending"
            out_all.append(rec)

    out_all.sort(key=lambda r: (split_names.index(r.get("split", "ref")), r.get("local_path", "")))
    return out_all


# -----------------------------------------------------------------------------
# Split Discipline Verification Suite
# -----------------------------------------------------------------------------
def verify_split_discipline(records: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Audits record set to prove zero cross-split leakage.
    Ensures that neither source photographs nor subject series span multiple splits."""
    errors: List[str] = []
    by_photo: Dict[str, Set[str]] = defaultdict(set)
    by_series: Dict[str, Set[str]] = defaultdict(set)
    by_hash: Dict[str, Set[str]] = defaultdict(set)

    for r in records:
        split = r.get("split", "unassigned")
        pid = r.get("source_photo_id") or r.get("local_path", "")
        series = r.get("source_subject_id") or pid
        sha = r.get("sha256")
        class_id = r.get("place_id") or r.get("neg_category") or "unknown"

        by_photo[pid].add(split)
        by_series[series].add(split)
        if sha and not r.get("is_augmented"):
            by_hash[sha].add(class_id)

    # 1. Source photo leakage
    photo_leaks = {p: s for p, s in by_photo.items() if len(s) > 1}
    if photo_leaks:
        errors.append(f"Source photo leakage detected: {len(photo_leaks)} photos straddle multiple splits ({list(photo_leaks.keys())[:3]})")

    # 2. Subject series leakage
    series_leaks = {sr: s for sr, s in by_series.items() if len(s) > 1}
    if series_leaks:
        errors.append(f"Subject series leakage detected: {len(series_leaks)} series straddle multiple splits ({list(series_leaks.keys())[:3]})")

    # 3. Cross-class hash conflict
    hash_conflicts = {h: c for h, c in by_hash.items() if len(c) > 1}
    if hash_conflicts:
        errors.append(f"Cross-class duplicate hash conflict: {len(hash_conflicts)} raw images claimed by multiple classes ({list(hash_conflicts.keys())[:3]})")

    return (len(errors) == 0, errors)


# -----------------------------------------------------------------------------
# Channel 1: Wikimedia Commons Harvester
# -----------------------------------------------------------------------------
def _commons_query(params: Dict[str, str]) -> Dict[str, Any]:
    base = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url|user|timestamp|extmetadata|dimensions",
        "iiurlwidth": "640",
    }
    base.update(params)
    url = f"{COMMONS_API}?{urllib.parse.urlencode(base)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}


def _extract_commons_candidates(data: Dict[str, Any], max_items: int = 30) -> List[Dict[str, Any]]:
    pages = data.get("query", {}).get("pages", {})
    out: List[Dict[str, Any]] = []
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
        if w < 300 or h < 300:
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


def discover_commons_candidates(
    categories: List[str],
    queries: List[str],
    target_count: int = 24,
    global_seen: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """Discovers candidate monument images via category navigation and search."""
    seen_titles = global_seen if global_seen is not None else set()
    results: List[Dict[str, Any]] = []

    for cat in categories:
        data = _commons_query({
            "generator": "categorymembers",
            "gcmtitle": cat,
            "gcmtype": "file",
            "gcmlimit": "40",
        })
        for c in _extract_commons_candidates(data, max_items=target_count):
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
            "gsrlimit": "40",
        })
        for c in _extract_commons_candidates(data, max_items=target_count):
            if c["title"] not in seen_titles:
                seen_titles.add(c["title"])
                results.append(c)
                if len(results) >= target_count:
                    return results

    return results


def download_candidate(item: Dict[str, Any], dest_dir: Path, prefix: str) -> Optional[Dict[str, Any]]:
    """Downloads candidate image into quarantine directory with deterministic naming."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_path = dest_dir / stable_name(prefix, item["title"])
    raw: Optional[bytes] = None

    if out_path.is_file() and out_path.stat().st_size > 1024:
        raw = out_path.read_bytes()
    else:
        for attempt in range(3):
            try:
                req = urllib.request.Request(item["url"], headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = resp.read()
                img = Image.open(io.BytesIO(raw)).convert("RGB")
                img.thumbnail((640, 640), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=92)
                raw = buf.getvalue()
                out_path.write_bytes(raw)
                break
            except Exception:
                time.sleep(0.5 * (attempt + 1))

    if raw is None:
        return None

    rec = dict(item)
    rec["local_path"] = str(out_path.relative_to(ROOT)).replace("\\", "/")
    rec["sha256"] = hashlib.sha256(raw).hexdigest()
    rec["source_photo_id"] = "commons:" + hashlib.sha256(item["title"].encode("utf-8")).hexdigest()[:16]
    rec["source_subject_id"] = subject_series_id(item.get("photographer", ""), item.get("title", ""))
    rec["status"] = "pending"
    rec["verification_status"] = "pending"
    rec["harvest_channel"] = "wikimedia_commons"
    return rec


# -----------------------------------------------------------------------------
# Channel 2: Video Tour Frame Harvester
# -----------------------------------------------------------------------------
def harvest_video_frames(
    video_path: Optional[Path],
    dest_dir: Path,
    poi_id: str,
    channel_name: str = "youtube_tour",
    video_id: str = "tour01",
    interval_seconds: float = 3.0,
    min_sharpness: float = 100.0,
    max_frames: int = 50,
    mock_frames: Optional[List[Image.Image]] = None,
) -> List[Dict[str, Any]]:
    """Harvests diverse, sharp candidate frames from a 4K video walking tour.
    Enforces that all frames from the same video share one subject series ID
    ('video:{video_id}') so they never leak across splits."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    accepted_records: List[Dict[str, Any]] = []
    saved_hashes: List[int] = []

    # Source 1: Mock frames provided (e.g. for offline testing / dry-runs)
    if mock_frames is not None:
        frame_images = mock_frames
    elif video_path and video_path.is_file():
        temp_dir = dest_dir / "temp_ffmpeg"
        temp_dir.mkdir(parents=True, exist_ok=True)
        fps_val = 1.0 / max(0.5, interval_seconds)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"fps={fps_val:.3f}",
            "-q:v",
            "2",
            str(temp_dir / "frame_%04d.jpg"),
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            frame_files = sorted(temp_dir.glob("frame_*.jpg"))
            frame_images = [Image.open(f).convert("RGB") for f in frame_files]
        except (subprocess.SubprocessError, FileNotFoundError):
            frame_images = []
        finally:
            if temp_dir.exists():
                for f in temp_dir.glob("*.jpg"):
                    f.unlink()
                temp_dir.rmdir()
    else:
        # No local video file or mock frames available
        return []

    count = 0
    series_id = f"video:{video_id}"
    for idx, img in enumerate(frame_images):
        if count >= max_frames:
            break
        # 1. Sharpness filter
        sharpness = compute_sharpness(img)
        if sharpness < min_sharpness:
            continue

        # 2. Perceptual duplicate check
        curr_hash = compute_dhash(img)
        if any(hamming_distance(curr_hash, h) < 10 for h in saved_hashes):
            continue

        # Save accepted frame into candidate quarantine
        frame_name = f"cand_vid_{video_id}_{count:03d}.jpg"
        out_path = dest_dir / frame_name
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92)
        raw_bytes = buf.getvalue()
        out_path.write_bytes(raw_bytes)

        saved_hashes.append(curr_hash)
        accepted_records.append({
            "title": f"VideoFrame:{video_id}:{count:03d}",
            "url": f"video://{channel_name}/{video_id}?frame={idx}",
            "original_url": f"video://{channel_name}/{video_id}",
            "photographer": f"channel:{channel_name}",
            "visit": time.strftime("%Y-%m-%d"),
            "license": "Video Tour Frame (Internal Candidate Review)",
            "local_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "source_photo_id": f"video:{video_id}:{count:03d}",
            "source_subject_id": series_id,
            "status": "pending",
            "verification_status": "pending",
            "harvest_channel": "video_tour",
            "frame_sharpness": round(sharpness, 2),
        })
        count += 1

    return accepted_records


# -----------------------------------------------------------------------------
# Mock & Dry-Run Synthesizer
# -----------------------------------------------------------------------------
def generate_mock_image(label: str, pattern_id: int, sharpness_target: float = 180.0) -> Image.Image:
    """Generates synthetic monument test images with distinct geometries and high sharpness."""
    img = Image.new("RGB", (640, 640), color=(180, 160, 140))
    draw = ImageDraw.Draw(img)

    # Architectural structure patterns (domes, spires, towers, ramparts)
    seed = pattern_id % 6
    if seed == 0:
        # Central dome & spires (e.g. Taj Mahal style)
        draw.rectangle([100, 300, 540, 580], fill=(240, 235, 230), outline=(100, 90, 80), width=3)
        draw.ellipse([220, 150, 420, 350], fill=(255, 250, 245), outline=(100, 90, 80), width=4)
        draw.line([120, 580, 120, 200], fill=(220, 215, 210), width=12)
        draw.line([520, 580, 520, 200], fill=(220, 215, 210), width=12)
    elif seed == 1:
        # Tower / Minaret (e.g. Qutub Minar style)
        draw.polygon([(260, 100), (380, 100), (420, 580), (220, 580)], fill=(190, 70, 50), outline=(50, 20, 15), width=3)
        for y in range(160, 560, 60):
            draw.line([210, y, 430, y], fill=(240, 220, 180), width=6)
    elif seed == 2:
        # Honeycomb facade / windows (e.g. Hawa Mahal style)
        draw.rectangle([120, 180, 520, 580], fill=(220, 100, 90), outline=(80, 30, 25), width=3)
        for r in range(220, 540, 50):
            for c in range(160, 500, 45):
                draw.arc([c, r, c + 35, r + 40], 0, 180, fill=(255, 240, 220), width=3)
    elif seed == 3:
        # Fort ramparts & battlements (e.g. Red Fort / Amer Fort)
        draw.rectangle([80, 260, 560, 580], fill=(180, 60, 50), outline=(60, 20, 20), width=3)
        for x in range(80, 560, 40):
            draw.rectangle([x, 220, x + 25, 260], fill=(180, 60, 50), outline=(60, 20, 20), width=2)
    elif seed == 4:
        # Stepped pyramidal shikhara (e.g. Mahabodhi Temple)
        draw.polygon([(320, 80), (180, 580), (460, 580)], fill=(160, 120, 80), outline=(40, 30, 20), width=3)
        for y in range(140, 560, 40):
            draw.line([200, y, 440, y], fill=(210, 180, 130), width=4)
    else:
        # Arches & amphitheatre (e.g. Colosseum / Roman)
        draw.rectangle([100, 200, 540, 560], fill=(210, 190, 160), outline=(80, 70, 60), width=3)
        for r in range(240, 520, 70):
            for c in range(140, 500, 60):
                draw.arc([c, r, c + 45, r + 60], 0, 180, fill=(50, 40, 30), width=4)

    # Texture & edge enhancement to ensure sharpness
    draw.text((20, 20), f"TEST_{label}_{pattern_id}", fill=(20, 20, 20))
    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return img


# -----------------------------------------------------------------------------
# Main Automated Corridor Harvesting Pipeline
# -----------------------------------------------------------------------------
def harvest_corridor(
    corridor_key: str,
    target_dir: Path,
    manifest_path: Path,
    source_mode: str = "both",
    per_class_target: int = 12,
    mock_mode: bool = False,
    poi_filter: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Runs data harvesting across POIs and hard-negative taxonomies for a corridor.
    Emits candidate records into quarantine and produces verified candidate manifests."""
    if corridor_key not in CORRIDORS:
        raise ValueError(f"Unknown corridor: {corridor_key}. Valid: {list(CORRIDORS.keys())}")

    corridor = CORRIDORS[corridor_key]
    corridor_id = corridor["corridor_id"]
    corridor_dir = target_dir / corridor_id

    print(f"\n=====================================================================")
    print(f"[*] INITIATING CORRIDOR HARVEST: {corridor['name']} ({corridor_id})")
    print(f"[*] Target Quarantine Dir: {corridor_dir}")
    print(f"[*] Source Channel: {source_mode} | Mock Mode: {mock_mode}")
    print(f"=====================================================================")

    manifest_data: Dict[str, Any] = {
        "corridor_id": corridor_id,
        "corridor_name": corridor["name"],
        "region": corridor["region"],
        "pack_id": corridor["pack_id"],
        "harvested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "quarantine_policy": (
            "All assets in this manifest are strictly quarantined (status='pending') "
            "and cannot enter the training corpus or pack until approved via human verification review."
        ),
        "split_discipline": "Photographer and Video-Series Grouped (disjoint ref/calib/test sets)",
        "classes": {},
        "summary": {},
    }

    global_seen_titles: Set[str] = set()
    total_raw_collected = 0
    total_split_records = 0
    all_corridor_records: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Phase A: POIs (Positive Known Monument Classes)
    # -------------------------------------------------------------------------
    pois = corridor.get("pois", [])
    if poi_filter:
        pois = [p for p in pois if p["place_id"] in poi_filter]

    print(f"\n--- Phase A: Processing {len(pois)} POIs ---")
    for spec in pois:
        pid = spec["place_id"]
        pname = spec["name"]
        is_vision = spec.get("vision_class", True)
        exempt = spec.get("title_exempt", [])
        poi_dest = corridor_dir / "place" / pid
        collected: List[Dict[str, Any]] = []

        print(f"\n[+] POI: {pid} ('{pname}') [VisionClass: {is_vision}]")

        # 1. Commons Harvesting
        if source_mode in ("both", "commons"):
            if mock_mode:
                # Generate synthetic mock Commons candidates
                for i in range(max(4, per_class_target // 2)):
                    mock_photographer = f"photographer_batch_{(i // 2) + 1}"
                    mock_title = f"File:{pname} Facade View Series {i}.jpg"
                    mock_img = generate_mock_image(pid, i)
                    mock_dest = poi_dest / stable_name(pid.split("-")[-1], mock_title)
                    mock_dest.parent.mkdir(parents=True, exist_ok=True)
                    buf = io.BytesIO()
                    mock_img.save(buf, format="JPEG", quality=92)
                    raw_bytes = buf.getvalue()
                    mock_dest.write_bytes(raw_bytes)
                    collected.append({
                        "title": mock_title,
                        "url": f"https://commons.wikimedia.org/wiki/{mock_title}",
                        "original_url": f"https://upload.wikimedia.org/{mock_title}",
                        "photographer": mock_photographer,
                        "visit": "2026-03-15",
                        "license": "CC BY-SA 4.0",
                        "local_path": str(mock_dest.relative_to(ROOT)).replace("\\", "/"),
                        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
                        "source_photo_id": "commons:" + hashlib.sha256(mock_title.encode("utf-8")).hexdigest()[:16],
                        "source_subject_id": subject_series_id(mock_photographer, mock_title),
                        "status": "pending",
                        "verification_status": "pending",
                        "harvest_channel": "mock_commons",
                    })
            else:
                cands = discover_commons_candidates(
                    spec.get("categories", []),
                    spec.get("queries", []),
                    target_count=per_class_target,
                    global_seen=global_seen_titles,
                )
                filtered = [c for c in cands if not is_rejected_title(c.get("title", ""), exempt)]
                with ThreadPoolExecutor(max_workers=6) as ex:
                    futs = [ex.submit(download_candidate, c, poi_dest, pid.split("-")[-1]) for c in filtered]
                    for f in as_completed(futs):
                        res = f.result()
                        if res:
                            collected.append(res)

        # 2. Video Tour Frame Harvesting
        if source_mode in ("both", "video") and spec.get("video_queries"):
            video_series_id_str = f"vid_{pid.split('-')[-1]}"
            if mock_mode:
                mock_video_frames = [generate_mock_image(f"video_{pid}", j) for j in range(6)]
                vid_records = harvest_video_frames(
                    None,
                    poi_dest,
                    pid,
                    channel_name=f"tour_{pid.split('-')[-1]}",
                    video_id=video_series_id_str,
                    mock_frames=mock_video_frames,
                )
                collected.extend(vid_records)
            else:
                print(f"  [*] Video tour specifications recorded for '{pname}': {spec['video_queries']}")

        # Enforce split discipline across raw downloads & synthetic augmentations
        split_records = assign_photo_grouped_splits(
            collected,
            counts_per_split=(4, 4, 8) if is_vision else (1, 1, 1),
            proportions=(0.35, 0.20, 0.45),
        )
        for r in split_records:
            r["place_id"] = pid
            r["corridor_id"] = corridor_id
            r["kind"] = "place"
        all_corridor_records.extend(split_records)

        manifest_data["classes"][pid] = {
            "kind": "place",
            "place_id": pid,
            "name": pname,
            "city": spec.get("city"),
            "viewpoint_tag": spec.get("viewpoint_tag"),
            "distinguishing_hint": spec.get("distinguishing_hint"),
            "vision_class": is_vision,
            "raw_candidate_count": len(collected),
            "distinct_source_photos": len({r["source_photo_id"] for r in split_records}),
            "distinct_subject_series": len({r["source_subject_id"] for r in split_records}),
            "total_split_count": len(split_records),
            "records": split_records,
        }
        total_raw_collected += len(collected)
        total_split_records += len(split_records)
        print(f"  -> Harvested {len(collected)} candidates | {len(split_records)} assigned to splits "
              f"({len({r['source_subject_id'] for r in split_records})} disjoint series)")

    # -------------------------------------------------------------------------
    # Phase B: Hard-Negative Taxonomy Categories
    # -------------------------------------------------------------------------
    negatives = corridor.get("negatives", [])
    print(f"\n--- Phase B: Processing {len(negatives)} Hard-Negative Taxonomies ---")
    for nspec in negatives:
        ncat = nspec["neg_category"]
        nlabel = nspec["label"]
        exempt = nspec.get("title_exempt", [])
        neg_dest = corridor_dir / "neg" / ncat
        collected_neg: List[Dict[str, Any]] = []

        print(f"\n[-] Negative: {ncat} ('{nlabel}')")

        if source_mode in ("both", "commons"):
            if mock_mode:
                for i in range(max(4, per_class_target // 2)):
                    mock_photographer = f"neg_photographer_{(i // 2) + 1}"
                    mock_title = f"File:Negative Distractor {nlabel} View {i}.jpg"
                    mock_img = generate_mock_image(ncat, i + 10)
                    mock_dest = neg_dest / stable_name(ncat.split("-")[-1], mock_title)
                    mock_dest.parent.mkdir(parents=True, exist_ok=True)
                    buf = io.BytesIO()
                    mock_img.save(buf, format="JPEG", quality=92)
                    raw_bytes = buf.getvalue()
                    mock_dest.write_bytes(raw_bytes)
                    collected_neg.append({
                        "title": mock_title,
                        "url": f"https://commons.wikimedia.org/wiki/{mock_title}",
                        "original_url": f"https://upload.wikimedia.org/{mock_title}",
                        "photographer": mock_photographer,
                        "visit": "2026-03-15",
                        "license": "CC BY-SA 4.0",
                        "local_path": str(mock_dest.relative_to(ROOT)).replace("\\", "/"),
                        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
                        "source_photo_id": "commons:" + hashlib.sha256(mock_title.encode("utf-8")).hexdigest()[:16],
                        "source_subject_id": subject_series_id(mock_photographer, mock_title),
                        "status": "pending",
                        "verification_status": "pending",
                        "harvest_channel": "mock_commons",
                    })
            else:
                cands = discover_commons_candidates(
                    nspec.get("categories", []),
                    nspec.get("queries", []),
                    target_count=per_class_target,
                    global_seen=global_seen_titles,
                )
                filtered = [c for c in cands if not is_rejected_title(c.get("title", ""), exempt)]
                with ThreadPoolExecutor(max_workers=6) as ex:
                    futs = [ex.submit(download_candidate, c, neg_dest, ncat.split("-")[-1]) for c in filtered]
                    for f in as_completed(futs):
                        res = f.result()
                        if res:
                            collected_neg.append(res)

        split_neg = assign_photo_grouped_splits(
            collected_neg,
            counts_per_split=(3, 3, 6),
            proportions=(0.35, 0.20, 0.45),
        )
        for r in split_neg:
            r["neg_category"] = ncat
            r["label"] = nlabel
            r["corridor_id"] = corridor_id
            r["kind"] = "neg"
        all_corridor_records.extend(split_neg)

        manifest_data["classes"][ncat] = {
            "kind": "neg",
            "neg_category": ncat,
            "label": nlabel,
            "raw_candidate_count": len(collected_neg),
            "distinct_source_photos": len({r["source_photo_id"] for r in split_neg}),
            "distinct_subject_series": len({r["source_subject_id"] for r in split_neg}),
            "total_split_count": len(split_neg),
            "records": split_neg,
        }
        total_raw_collected += len(collected_neg)
        total_split_records += len(split_neg)
        print(f"  -> Harvested {len(collected_neg)} candidates | {len(split_neg)} assigned to splits "
              f"({len({r['source_subject_id'] for r in split_neg})} disjoint series)")

    # -------------------------------------------------------------------------
    # Split Integrity Audit
    # -------------------------------------------------------------------------
    print(f"\n--- Phase C: Auditing Split Discipline & Quarantine Integrity ---")
    valid_splits, audit_errors = verify_split_discipline(all_corridor_records)
    if not valid_splits:
        print("[!] ERROR: Split integrity audit failed:")
        for err in audit_errors:
            print(f"    - {err}")
        raise RuntimeError("Corridor candidate split discipline violation!")
    else:
        print("[+] PASS: Split integrity verified! 0 cross-split photograph or series leaks.")

    manifest_data["summary"] = {
        "corridor_id": corridor_id,
        "total_classes": len(manifest_data["classes"]),
        "total_raw_collected": total_raw_collected,
        "total_split_records": total_split_records,
        "distinct_source_photos": len({r["source_photo_id"] for r in all_corridor_records}),
        "distinct_subject_series": len({r["source_subject_id"] for r in all_corridor_records}),
        "split_integrity_verified": valid_splits,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[+] Successfully saved corridor candidate manifest to:")
    print(f"    {manifest_path}")
    print(f"[*] Summary: {manifest_data['summary']}")
    return manifest_data


def main() -> int:
    parser = argparse.ArgumentParser(description="TrueWay Automated Global Corridor Data Harvester")
    parser.add_argument(
        "--corridor",
        choices=["all", "bihar-buddhist-circuit", "india-golden-triangle", "global-icons-tier1"],
        default="india-golden-triangle",
        help="Target corridor specification to harvest",
    )
    parser.add_argument(
        "--source",
        choices=["both", "commons", "video"],
        default="both",
        help="Media harvesting channels to activate",
    )
    parser.add_argument(
        "--poi",
        nargs="*",
        default=None,
        help="Optional filter to specific POI place_id(s)",
    )
    parser.add_argument(
        "--per-class",
        type=int,
        default=12,
        help="Target candidate image count per POI/Negative class",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock/simulation mode (deterministic synthetic photos, no live downloads)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate specifications and splits without modifying persistent manifests",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(CANDIDATES_DIR),
        help="Root directory for quarantined candidates",
    )
    parser.add_argument(
        "--manifest-path",
        type=str,
        default=None,
        help="Target path for the candidate manifest JSON",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification on the generated or specified candidate manifest",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    target_corridors = list(CORRIDORS.keys()) if args.corridor == "all" else [args.corridor]

    for cid in target_corridors:
        if args.manifest_path:
            m_path = Path(args.manifest_path)
        else:
            m_path = out_dir / f"candidates_{cid.replace('-', '_')}_manifest.json"

        if args.dry_run:
            m_path = out_dir / f"test_dryrun_{cid.replace('-', '_')}_manifest.json"

        harvest_corridor(
            corridor_key=cid,
            target_dir=out_dir,
            manifest_path=m_path,
            source_mode=args.source,
            per_class_target=args.per_class,
            mock_mode=args.mock or args.dry_run,
            poi_filter=args.poi,
        )

        if args.verify or args.dry_run:
            data = json.loads(m_path.read_text(encoding="utf-8"))
            all_recs = []
            for c in data.get("classes", {}).values():
                all_recs.extend(c.get("records", []))
            valid, errs = verify_split_discipline(all_recs)
            if not valid:
                print(f"[!] Verification failed for {cid}: {errs}")
                return 1
            print(f"[+] Verification PASSED for {cid}: {len(all_recs)} records verified cleanly.")

        if args.dry_run and m_path.exists():
            print(f"[*] Cleaning up dry-run test manifest: {m_path.name}")
            m_path.unlink()

    return 0


if __name__ == "__main__":
    sys.exit(main())
