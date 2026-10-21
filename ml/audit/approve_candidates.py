"""Human verdicts for the quarantined candidate pool.

The candidate pool (`ml/dataset/candidates/`) is harvested automatically and is
NEVER trained on until a reviewer approves each photograph. This file records
those verdicts.

The tables are keyed by the CANDIDATE INDEX within a class. The candidate lists
are append-only, so an index keeps its meaning; the `APPROVE_BY_TITLE` table
is the final authority for the photographs whose index may have shifted.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
REVIEW = ROOT / "ml" / "dataset" / "verification_review.json"
MANIFEST = ROOT / "ml" / "dataset" / "dataset_manifest.json"

# class -> (approved sheet indices, reason)
APPROVED = {
    # ---------------------------------------------------------------- known
    "in-bihar-bodhgaya-mahabodhi": (
        [33, 45, 46, 60, 63, 75, 76, 82, 83, 84, 85, 86, 87, 88,
         89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103,
         104, 105, 106, 107, 108, 109, 114, 119,
         59, 60, 61, 62, 64],
        "The Mahabodhi Temple shikhara itself - the stepped pyramidal spire, the "
        "only silhouette that identifies the place",
    ),
    "in-bihar-bodhgaya-bodhi-tree": (
        [],
        "search-only (see the vision_class flag in the POI spec)",
    ),
    "in-bihar-bodhgaya-vajrasana": (
        [1, 27, 28],
        "Vajrasana - the diamond throne and its railing",
    ),
    "in-bihar-bodhgaya-animesh-lochan": (
        [],
        "search-only (see the vision_class flag in the POI spec)",
    ),
    "in-bihar-bodhgaya-mucalinda": (
        [3, 4, 5, 20, 21, 24, 25, 26, 27, 28, 29, 30, 31, 35],
        "Mucalinda lake and the serpent-king statue that shelters the Buddha",
    ),
    "in-bihar-bodhgaya-great-buddha": (
        [        8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
        26, 29, 30, 31, 32, 33, 34],
        "The 80-feet Great Buddha (Daijutsu) from every side - the single silhouette that identifies the statue",
    ),
    "in-bihar-rajgir-vultures-peak": (
        [3, 4, 5, 6, 7, 8, 9, 15, 16, 17, 18, 19, 20, 21, 24, 25, 27, 28, 31, 32, 33, 34, 35],
        "Gridhrakuta - the brick stupa remains on the summit, the summit itself "
        "and the carved marker stone",
    ),
    "in-bihar-rajgir-venu-vana": (
        [18, 19, 23, 24, 26, 27, 29, 30, 31, 32, 33],
        "Venu Vana, Rajgir - the bathing tank, the grove and the Buddha shrine",
    ),
    "in-bihar-rajgir-cyclopean-wall": (
        [3, 4, 5, 6, 7, 8, 9, 11],
        "The Cyclopean Wall - the unmortared stone rampart along the ridge",
    ),
    "in-bihar-rajgir-shanti-stupa": (
        [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21, 22,
         24, 25, 26, 27, 28, 29, 30, 31, 32],
        "Vishwa Shanti Stupa - the white dome and its golden pinnacle, and the "
        "golden Buddhas in the dome's niches",
    ),
    "in-bihar-rajgir-sonbhandar": (
        [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
         22, 23, 24, 27, 29, 30, 33, 34, 35],
        "Son Bhandar - the twin rock-cut chambers and their carved relief panels",
    ),
    "in-bihar-nalanda-mahavihara": (
        [        73, 74, 75, 76, 77, 78, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 95,
        96, 97, 98, 99, 102, 103, 104, 105, 106, 107, 108, 110, 111, 112,
        113, 114, 115],
        "The Nalanda Mahavihara site seen across the excavated brick mounds - the wide site views that identify the archaeological complex",
    ),
    "in-bihar-nalanda-temple-03": (
        [],
        "moved in from the Nalanda Monastery 1 candidate list (the Sariputta Stupa IS Temple 3)",
    ),
    "in-bihar-nalanda-monastery-01": (
        [        32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48,
        49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60],
        "Nalanda Monastery 1 - the granary cells, the porches, the monks' cells and the well",
    ),
    "in-bihar-nalanda-museum": (
        [0, 1, 2, 3, 4],
        "search-only (see the vision_class flag in the POI spec)",
    ),
    # ---------------------------------------------------------------- negatives
    "neg-crowds-tourist-occlusion": (
        list(range(36, 47)) + [48],
        "Crowded religious-festival scenes - dense human crowds under stage "
        "lighting and a night-street crowd (a crowd is a hard negative for a "
        "monument: the geometry of the site is occluded)",
    ),
    "neg-se-asian-stupa": (
        list(range(0, 14)),
        "Old Bagan golden pagodas, Dhammayangi, Jetavana and Sri Lankan stupas - "
        "the golden dome is the Shanti Stupa's silhouette and the white dome is "
        "the nearest shape to a Buddhist stupa anywhere",
    ),
    "neg-ordinary-brick-ruins": (
        [35],
        "An abandoned brick ruin among trees",
    ),
    "neg-construction-scaffolding": (
        [27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45,
         46, 47, 48, 50, 51, 56, 57, 58, 59, 60],
        "Scaffolding on brick, stone and temple structures - the restoration state "
        "a monument is photographed in while it is conserved",
    ),
    "neg-out-of-pack-bihar-lookalike": (
        [3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
        25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 38, 39, 42, 43, 44, 45, 48,
        52, 53, 54, 55, 56, 59, 60, 65, 66, 71, 72, 73, 74, 75, 76, 77, 78,
        80, 81, 82, 83, 85, 86, 87, 88, 89, 90, 91, 92, 94, 95, 96, 97, 98,
        99, 100, 101, 102, 110, 111, 112, 113, 114, 121, 122, 123, 124, 125,
        126, 127, 128, 132, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143,
        144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157,
        158, 159, 160, 161, 162, 163, 164, 165],
        "Kesariya's great stupa, Vikramshila, the Gol Ghar dome at Patna, the Barabar and "
        "Nagarjuni rock-cut caves and the Sher Shah Suri tomb at Sasaram - every major "
        "Buddhist monument and every great dome of Bihar that is NOT in the circuit, and "
        "the exact lookalikes of the places it does contain",
    ),
    "neg-generic-indian-temple": (
        [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 17, 18, 19, 20, 21, 39, 40, 41, 43, 44, 45],
        "The Gupta-era brick temples of Bhitargaon, Lakshmana and Sirpur - the "
        "ancient brick masonry that reads exactly like Nalanda's cells, which is "
        "why they are the hardest negative in the corpus",
    ),
    "neg-modern-commercial-shop": (
        [1, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 21, 22],
        "Market and souvenir stalls - the cluttered modern commerce that surrounds "
        "every monument in the circuit",
    ),
    # ---------------------------------------------------------------------
    # The "TWIN" negatives.
    #
    # The measured false accepts were not random: a white-and-gold dome was
    # matched to the Vishwa Shanti Stupa, a colossal seated Buddha to the Great
    # Buddha, a rock-cut cave to Son Bhandar, a stepped brick tower to the
    # Mahabodhi, and an excavated brick stupa mound to the Nalanda sites. A
    # bank of generic ruins cannot separate them - the winning place and the
    # best bank negative differed by a few hundredths - so the bank needs the
    # LOOKALIKES. Each category below is the confusable twin of one or more
    # vision classes; none of the twelve vision classes appears in them.
    # ---------------------------------------------------------------------
    "neg-white-golden-dome": (
        [1, 6, 8, 9, 12, 13, 17, 19, 29, 30, 35, 38, 45, 50, 56],
        "White and gilded stupas, chedis and pagodas in Thailand, Myanmar and "
        "Sri Lanka - the Shanti Stupa's own silhouette",
    ),
    "neg-colossal-seated-buddha": (
        [        0, 1, 6, 8, 10, 11, 12, 13, 15, 18, 20, 22, 24, 26, 27, 28, 29, 30,
        31, 33, 34, 36, 38, 41, 42, 43, 44, 45, 46, 47, 49, 51, 56],
        "Colossal seated and standing Buddhas at the Spring Temple, Leshan, Kamakura and the Longmen Grottoes - the Great Buddha's own double, and the two photographs that were still being matched to it",
    ),
    "neg-rock-cut-cave-complex": (
        [1, 2, 4, 6, 9, 10, 14, 25, 28, 29, 30, 32, 36, 37, 39, 40, 42, 44,
         45, 46, 47, 50, 52, 53],
        "Rock-cut cave complexes at Ellora, Ajanta and Badami - the rock-cut "
        "chambers and relief panels of Son Bhandar, elsewhere",
    ),
    "neg-stepped-brick-temple-tower": (
        [3, 5, 6, 7, 9, 14, 17, 27, 31, 32, 37, 39, 42, 44, 45, 49, 51, 54,
         55, 57],
        "Gupta-era brick and stone temple towers at Chittorgarh, Sirpur and "
        "Bhitargaon - the Mahabodhi's stepped shikhara, elsewhere",
    ),
    "neg-ancient-brick-stupa-mound": (
        [0, 1, 2, 3, 5, 7, 9, 10, 11, 12, 13, 15, 16, 17, 18, 20, 21, 22, 23,
         24, 26, 27, 28, 30, 31, 32, 33, 36, 38, 39, 40, 42, 43, 44, 45, 46,
         48, 49, 50, 52, 55, 56, 58, 59, 60, 62, 63, 65, 66],
        "Excavated ancient brick stupas and mounds - Salihundam, Pauni, "
        "Amaravati, Sanchi - the Nalanda Mahavihara and the Sariputta Stupa's "
        "own form, elsewhere",
    ),
    "neg-natural-foliage-landscape": (
        [1, 2, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
         23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35],
        "Ficus benghalensis and bamboo groves - the sacred-fig trees and bamboo "
        "that surround every site, and the exact lookalikes of the Bodhi Tree and "
        "the Venu Vana grove",
    ),
}

# (candidate class, sheet index) -> (target class, reason)
# A photograph harvested under one POI's search that actually shows a DIFFERENT
# POI. It must be moved, not merely approved.
MOVES = {
    ("in-bihar-bodhgaya-mahabodhi", 6): (
        "in-bihar-bodhgaya-animesh-lochan",
        "Animesh Lochan Chaitya - a CHILD STRUCTURE inside the Mahabodhi complex"),
    ("in-bihar-bodhgaya-mahabodhi", 10): (
        "in-bihar-bodhgaya-animesh-lochan",
        "Shows the Animesh Lochan Chaitya prominently - a child structure"),
    ("in-bihar-bodhgaya-mahabodhi", 11): (
        "in-bihar-bodhgaya-animesh-lochan",
        "Shows the Animesh Lochan Chaitya prominently - a child structure"),
    ("in-bihar-bodhgaya-mahabodhi", 12): (
        "in-bihar-bodhgaya-animesh-lochan",
        "Shows the Animesh Lochan Chaitya prominently - a child structure"),
    ("in-bihar-bodhgaya-mahabodhi", 13): (
        "in-bihar-bodhgaya-animesh-lochan",
        "Shows the Animesh Lochan Chaitya prominently - a child structure"),
    ("in-bihar-bodhgaya-mahabodhi", 14): (
        "in-bihar-bodhgaya-animesh-lochan",
        "Animesh Lochan Chaitya shikhara - a child structure"),
    ("in-bihar-bodhgaya-mahabodhi", 15): (
        "in-bihar-bodhgaya-animesh-lochan",
        "Animesh Lochan Chaitya shikhara - a child structure"),
    ("in-bihar-bodhgaya-mahabodhi", 16): (
        "in-bihar-bodhgaya-animesh-lochan",
        "Animesh Lochan Chaitya shikhara - a child structure"),
    ("in-bihar-bodhgaya-mahabodhi", 17): (
        "in-bihar-bodhgaya-animesh-lochan",
        "Animesh Lochan Chaitya in the Mahabodhi temple complex"),
    ("in-bihar-bodhgaya-mahabodhi", 51): (
        "in-bihar-bodhgaya-vajrasana",
        "The Vajrasana - the polished throne slab at the foot of the Bodhi Tree"),
    ("in-bihar-bodhgaya-mahabodhi", 52): (
        "in-bihar-bodhgaya-vajrasana",
        "The Vajrasana throne slab"),
    ("in-bihar-nalanda-monastery-01", 62): (
        "in-bihar-nalanda-temple-03",
        "Nalanda Temple No 3 - the Sariputta Stupa, which IS Temple 3"),
    ("in-bihar-nalanda-monastery-01", 64): (
        "in-bihar-nalanda-temple-03",
        "Nalanda Temple No 3 - the Sariputta Stupa"),
    ("in-bihar-nalanda-monastery-01", 65): (
        "in-bihar-nalanda-mahavihara",
        "The Nalanda Mahavihara site seen across the excavated brick mounds"),
}

# Candidate verdicts to REVOKE: (class, sheet index, reason)
REVOKE = {
    ("in-bihar-bodhgaya-mahabodhi", 6): "Animesh Lochan Chaitya - a child structure, not the Mahabodhi Temple",
    ("in-bihar-bodhgaya-mahabodhi", 10): "Shows the Animesh Lochan Chaitya AND the Mahabodhi Temple - ambiguous",
    ("in-bihar-bodhgaya-mahabodhi", 11): "Shows the Animesh Lochan Chaitya AND the Mahabodhi Temple - ambiguous",
    ("in-bihar-bodhgaya-mahabodhi", 12): "Shows the Animesh Lochan Chaitya AND the Mahabodhi Temple - ambiguous",
    ("in-bihar-bodhgaya-mahabodhi", 13): "Shows the Animesh Lochan Chaitya AND the Mahabodhi Temple - ambiguous",
    ("in-bihar-bodhgaya-mahabodhi", 14): "Animesh Lochan Chaitya shikhara - a child structure",
    ("in-bihar-bodhgaya-mahabodhi", 15): "Animesh Lochan Chaitya shikhara - a child structure",
    ("in-bihar-bodhgaya-mahabodhi", 16): "Animesh Lochan Chaitya shikhara - a child structure",
    ("in-bihar-bodhgaya-mahabodhi", 17): "Animesh Lochan Chaitya in the Mahabodhi complex - a child structure",
    ("in-bihar-bodhgaya-mahabodhi", 49): "A generic tree-and-railing view in the temple complex - the tree itself is not identifiable",
    ("in-bihar-bodhgaya-mahabodhi", 50): "A generic tree-and-railing view in the temple complex - the tree itself is not identifiable",
    ("in-bihar-bodhgaya-mahabodhi", 53): "A monk seated under the trees - a person, not the Bodhi Tree",
    ("in-bihar-bodhgaya-mahabodhi", 54): "A monk seated under the trees - a person, not the Bodhi Tree",
    ("in-bihar-bodhgaya-mahabodhi", 55): "A monk seated under the trees - a person, not the Bodhi Tree",
    ("in-bihar-bodhgaya-mahabodhi", 56): "A monk seated under the trees - a person, not the Bodhi Tree",
}

# Corpus photographs rejected on a second full visual pass. Keyed by the
# Commons TITLE (stable) rather than an index.
REJECT_PHOTOS = {
    # A low brick mound on the Nalanda site that could be the Sariputta Stupa or
    # a cell block: a photograph that cannot be attributed to one place is
    # evidence for neither.
    "File:Ancient Indian Knowledge.jpg": "a low brick mound on the Nalanda site that could be the Sariputta Stupa or a cell block",
    "File:Ancient Indian Knowledge (1).jpg": "a low brick mound on the Nalanda site that could be the Sariputta Stupa or a cell block",
    "File:Ancient Indian Knowledge (2).jpg": "a low brick mound on the Nalanda site that could be the Sariputta Stupa or a cell block",
    # ---- Venu Vana: the class must be the TANK, not a detail of a statue on it.
    # A golden Buddha in a pavilion is not the Venu Vana - the same shot exists
    # at a hundred other shrines, and it was the whole of the class's Top-1
    # failure (the class scored 4/10 because 6 of its 10 test photographs were
    # statue close-ups).
    "File:Rajgir - 019 Fountains (9242355393).jpg": "a fountain in the park, not the Venu Vana tank",
    "File:Buddha-image at Venuvana Rajgir, Bihar, India.jpg": "a Buddha image in a niche - a detail of an object, not the place",
    "File:Rajgir - 013 Buddha Statue (9242420945).jpg": "golden Buddha statues in a pavilion - a detail of an object, not the place",
    "File:Rajgir - 017 Buddha Statue (9245160372).jpg": "a golden Buddha's face in close-up - a detail of an object, not the place",
    "File:Buddha in Venuvana Rajgir, Bihar, India.jpg": "a decorated shrine pavilion with festival flags - not the tank",
    # ---- the rest
    "File:Mahabodhi Temple Complex - Bodh Gaya (28).jpg": "a carved railing panel of the temple, not the temple itself",
    # ---- Shanti Stupa: the class is the white dome and its golden pinnacle.
    # These three are DIFFERENT monuments at Rajgir that happen to be next
    # door - the Parinirvana statue, the standing Bodhisattva statue and the
    # Mahavira statue.
    "File:Rajgir - 052 Parinibbana (9242003645).jpg": "the golden canopy over the Parinirvana statue - a different monument at Rajgir",
    "File:Rajgir - 049 Bodhisatta (9244812244).jpg": "the golden standing Bodhisattva statue - a different monument at Rajgir",
    "File:Rajgir lord mahavira.jpg": "the Mahavira statue - a different monument at Rajgir",
    # ---- Great Buddha: the 80-feet statue is carved stone. The golden one
    # next to it is the "Giant Lord Buddha", a different statue.
    "File:80 feet Giant Lord Buddha Statue Bodh Gaya India - panoramio.jpg": "the golden Giant Lord Buddha - a different statue from the 80-feet stone one",
    "File:Mahabodhi Temple Spires (8569625237).jpg": "the carved railing panels of the temple, not the temple itself",
    "File:Animesa Locana Chaitya inside the premises of Mahabodhi temple at Bodh Gaya in the state of Bihar 01 (1).jpg": "the Animesh Lochan chaitya - a child structure of the Mahabodhi complex",
    "File:Animesh Lochan Chaitya - Monks - Bodh Gaya (4).jpg": "a monk at the chaitya - a person, not the place",
    "File:'DAIBUTSU'.jpg": "a painted Buddha face - a detail, not the Great Buddha statue",
    "File:Gridhra Kuta - Rajgir 10.jpg": "the summit rocks, not the stupa remains of Gridhrakuta",
    "File:Gridhra Kuta - Rajgir 11.jpg": "the summit rocks, not the stupa remains of Gridhrakuta",
    "File:Amitabha Gupta - Cyclopean Wall - Rajgir - Wiki Explores Bihar II.png": "an illustration, not a photograph of the wall",
    "File:Buddhist Centre.png": "a low modern building, not a Bihar monument",
    "File:Golghar - Patna (5).jpg": "a Gol Ghar detail, not the dome",
    "File:Golghar patna Bihar India.jpg": "a Gol Ghar detail, not the dome",
    "File:Barabar And Nagarjuni Caves (2).jpg": "a rock-cut cave doorway, not a whole site",
    "File:Golghar in July 2022.jpg": "a Gol Ghar detail, not the dome",
    # NOTE: whole-site views of a SIMILAR monument are NOT rejected when they
    # sit in a NEGATIVE class - being "not the place it was photographed at" is
    # the whole point of a hard negative. Only close-up details are rejected.
}

# Titles whose verdict is FINAL regardless of the index-based tables above.
# The index tables shift as the corpus grows; these titles do not.
# title -> (target class, reason)
APPROVE_BY_TITLE = {
    "File:Ancient Brick Temple Front View.jpg": (
        "neg-generic-indian-temple",
        "The Kanpur ancient brick temple, whole-building view - the nearest hard "
        "negative to Nalanda's excavated brick cells",
    ),
    "File:Ancient Brick Temple Left View.jpg": (
        "neg-generic-indian-temple",
        "The Kanpur ancient brick temple, whole-building view",
    ),
    "File:Ancient Brick Temple Right View.jpg": (
        "neg-generic-indian-temple",
        "The Kanpur ancient brick temple, whole-building view",
    ),
    "File:Ancient brick temple kanpur.jpg": (
        "neg-generic-indian-temple",
        "The Kanpur ancient brick temple, whole-building view",
    ),
}

# Corpus photographs that were SEEDED directly into the corpus (so they never
# went through the quarantine) and must CHANGE CLASS. Keyed by the Commons
# title. The index-based tables above cannot express this: they address the
# candidate pool, and these photographs are not in it.
#
# The Nalanda Mahavihara class had swallowed photographs of the Sariputta
# Stupa - which IS Temple 3 and sits inside the Mahavihara. That made the
# "Temple 3" class unlearnable: every one of its test photographs was
# predicted as the Mahavihara, because the Mahavihara references contained
# the very stupa they were supposed to be distinguished from.
MOVE_BY_TITLE = {
    "File:Nalanda ruins and archaeological site.jpg": (
        "in-bihar-nalanda-temple-03",
        "The Sariputta Stupa - this IS Nalanda Temple 3, misfiled under the "
        "Mahavihara"),
    "File:Nalanda ruins and archaeological site 2.jpg": (
        "in-bihar-nalanda-temple-03",
        "The same visit as 'Nalanda ruins and archaeological site': the Sariputta "
        "Stupa at the upper left of the excavated grounds. A subject series must "
        "not be split across two place labels, so it moves with its partner"),
    "File:Nalanda Mahavihara UNESCO WHS.jpg": (
        "in-bihar-nalanda-temple-03",
        "The Sariputta Stupa with its shrine - this IS Nalanda Temple 3"),
    "File:Nalanda university. Shu.jpg": (
        "in-bihar-nalanda-temple-03",
        "The Sariputta Stupa - this IS Nalanda Temple 3"),
    "File:Nalanda university.jpg": (
        "in-bihar-nalanda-temple-03",
        "The Sariputta Stupa seen across the campus garden - this IS Nalanda "
        "Temple 3"),
    "File:Famed Buddhist Nalanda University ruins, 1993.jpg": (
        "in-bihar-nalanda-temple-03",
        "The Sariputta Stupa - this IS Nalanda Temple 3"),
    # Photographs that were filed under a POSITIVE class but show a DIFFERENT
    # monument - and in these cases the exact TWIN of one of the vision classes.
    # While they sat in the positive classes they were accidental hard
    # negatives; removing them (correctly) made the false-accept rate worse.
    # The right place for them is the negative bank, where they do their job
    # on purpose.
    "File:Rajgir - 017 Buddha Statue (9245160372).jpg": (
        "neg-colossal-seated-buddha",
        "A golden Buddha in a niche - the Great Buddha's twin, photographed at "
        "Venu Vana. It is not the tank, and it is a hard negative for the "
        "colossal-Buddha class",
    ),
    "File:Buddha-image at Venuvana Rajgir, Bihar, India.jpg": (
        "neg-colossal-seated-buddha",
        "A standing golden Buddha in a niche - a hard negative for the "
        "colossal-Buddha class",
    ),
    "File:Buddha in Venuvana Rajgir, Bihar, India.jpg": (
        "neg-colossal-seated-buddha",
        "A golden Buddha in a decorated pavilion - a hard negative for the "
        "colossal-Buddha class",
    ),
    "File:80 feet Giant Lord Buddha Statue Bodh Gaya India - panoramio.jpg": (
        "neg-colossal-seated-buddha",
        "The golden Giant Lord Buddha beside the 80-feet stone one - a different "
        "statue, and a hard negative for the colossal-Buddha class",
    ),
}

# Corpus photographs that must LEAVE the corpus entirely.
REJECT_CORPUS_TITLES = {
    "File:Rajgir 7 - International Convention Centre (30875640383).jpg":
        "a photograph of RAJGIR filed under Nalanda - a different place",
    "File:Nalanda University at dusk.jpg":
        "the modern university building at dusk, not the excavated archaeological "
        "site",
}

# Classes where the candidate pool yielded nothing usable at all. Recorded so
# the gap is visible instead of silent.
NO_MATCHES = {
    "neg-modern-commercial-shop":
        "The candidate pool returned mostly European street scenes; the approved "
        "subset is the Indian market and souvenir stalls.",
    "neg-natural-foliage-landscape":
        "The candidate pool returned street scenes; the approved subset is the "
        "Ficus and bamboo groves.",
    "neg-ordinary-brick-ruins":
        "The Commons 'brick' categories return MATERIALS AND TEXTURES (rendered "
        "brick, colour swatches, patterns), not ruins. Only a single usable "
        "photograph was found; the class needs archaeological-site queries.",
    "neg-generic-indian-temple":
        "Most candidates were carved-panel details rather than whole temples.",
    "in-bihar-bodhgaya-mucalinda":
        "The candidate pool mixes the Mahabodhi complex with the pond itself.",
}


def main() -> int:
    payload = json.loads(REVIEW.read_text(encoding="utf-8"))
    reviews = payload["reviews"]
    candidates = json.loads((ROOT / "ml" / "dataset" / "candidates_manifest.json").read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    added = 0
    reassigned = 0
    rejected_now = 0
    title_approved = 0
    moved = 0

    # 1. revoke verdicts recorded against the wrong class
    for (cid, i), reason in REVOKE.items():
        recs = candidates.get("classes", {}).get(cid, {}).get("records", [])
        if i >= len(recs):
            continue
        sid = recs[i]["source_photo_id"]
        if sid in reviews and reviews[sid].get("verdict") == "approved":
            reviews[sid]["verdict"] = "rejected"
            reviews[sid]["reason"] = reason
            rejected_now += 1

    # 2. approvals
    for cid, (indices, reason) in APPROVED.items():
        recs = candidates.get("classes", {}).get(cid, {}).get("records", [])
        for i in indices:
            if i >= len(recs):
                print(f"  ! {cid}: index {i} out of range ({len(recs)} candidates) - skipped")
                continue
            sid = recs[i]["source_photo_id"]
            key = "place_id" if cid.startswith("in-bihar-") else "neg_category"
            # A photograph whose TITLE is in the title-keyed rejection list is
            # never approved, whatever its index says. The two tables used to
            # contradict each other - the index table still listed photographs
            # that a later, title-keyed pass had rejected - and the index table
            # ran FIRST, so a title rejection could be undone by a stale index.
            # The title is the stable identity; the index is not.
            if recs[i].get("title", "") in REJECT_PHOTOS:
                continue
            existing = reviews.get(sid)
            if existing is not None and existing.get(key) == cid and existing.get("verdict") == "approved":
                continue
            if existing is not None and existing.get(key) != cid:
                reassigned += 1
            reviews[sid] = {
                "verdict": "approved",
                "reason": reason,
                key: cid,
                "commons_title": recs[i].get("title", ""),
            }
            added += 1

    # 3. moves: a photograph harvested under one POI that shows another
    for (src_cls, i), (dst_cls, reason) in MOVES.items():
        recs = candidates.get("classes", {}).get(src_cls, {}).get("records", [])
        if i >= len(recs):
            continue
        sid = recs[i]["source_photo_id"]
        key = "place_id" if dst_cls.startswith("in-bihar-") else "neg_category"
        reviews[sid] = {
            "verdict": "approved",
            "reason": reason,
            key: dst_cls,
            "commons_title": recs[i].get("title", ""),
            "moved_from": src_cls,
        }
        moved += 1

    # 4. title-keyed approvals (the index-based tables above shift as the corpus grows)
    by_title = {}
    for section in ("pois", "negatives"):
        for cid, node in manifest.get(section, {}).items():
            for rec in node.get("records", []):
                by_title.setdefault(str(rec.get("title") or ""), []).append((cid, rec.get("source_photo_id")))
    # 4b. title-keyed approvals - the final authority
    for title, (target_cid, reason) in APPROVE_BY_TITLE.items():
        for owner_cid, sid in by_title.get(title, []):
            key = "place_id" if owner_cid.startswith("in-bihar-") else "neg_category"
            reviews[sid] = {
                "verdict": "approved",
                "reason": reason,
                key: target_cid,
                "commons_title": title,
            }
            title_approved += 1

    # 4c. corpus-level class changes and removals (seeded photographs)
    for title, (target_cid, reason) in MOVE_BY_TITLE.items():
        for owner_cid, sid in by_title.get(title, []):
            key = "place_id" if target_cid.startswith("in-bihar-") else "neg_category"
            reviews[sid] = {
                "verdict": "approved",
                "reason": reason,
                key: target_cid,
                "commons_title": title,
                "moved_from": owner_cid,
            }
            title_approved += 1

    for title, reason in REJECT_CORPUS_TITLES.items():
        for owner_cid, sid in by_title.get(title, []):
            key = "place_id" if owner_cid.startswith("in-bihar-") else "neg_category"
            reviews[sid] = {
                "verdict": "rejected",
                "reason": reason,
                key: owner_cid,
                "commons_title": title,
            }
            rejected_now += 1

    # 5. the title-keyed rejections - the FINAL authority
    #
    # This runs last and unconditionally: a photograph whose Commons title is
    # in REJECT_PHOTOS is rejected, whatever any other table says about it.
    for title, reason in REJECT_PHOTOS.items():
        for owner_cid, sid in by_title.get(title, []):
            if reviews.get(sid, {}).get("verdict") == "rejected":
                continue
            reviews[sid] = {
                "verdict": "rejected",
                "reason": reason,
                "place_id" if owner_cid.startswith("in-bihar-") else "neg_category": owner_cid,
                "commons_title": title,
            }
            rejected_now += 1

    # 6. summary
    payload["summary"]["total_source_photographs"] = len(reviews)
    payload["summary"]["approved"] = sum(1 for v in reviews.values() if v["verdict"] == "approved")
    payload["summary"]["rejected"] = sum(1 for v in reviews.values() if v["verdict"] == "rejected")
    corpus_ids = set()
    for section in ("pois", "negatives"):
        for node in manifest.get(section, {}).values():
            for rec in node.get("records", []):
                corpus_ids.add(rec.get("source_photo_id"))
    with_places = {v.get("place_id") or v.get("neg_category")
                    for v in reviews.values() if v["verdict"] == "approved"}
    payload["summary"]["classes_with_zero_usable_photographs"] = sorted(
        {v.get("place_id") or v.get("neg_category")
         for v in reviews.values() if v["verdict"] == "rejected"} - with_places)
    payload["empty_candidate_pools"] = dict(NO_MATCHES)

    REVIEW.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  approved {added} candidate(s); re-assigned {reassigned}; moved {moved}; "
          f"rejected {rejected_now}")
    print(f"-> wrote {REVIEW}")
    print(f"   approved={payload['summary']['approved']} "
          f"rejected={payload['summary']['rejected']} "
          f"total={payload['summary']['total_source_photographs']}")
    print(f"   classes with ZERO usable photographs: "
          f"{payload['summary']['classes_with_zero_usable_photographs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
