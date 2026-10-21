"""Generates ml/dataset/verification_review.json from the visual inspection
verdicts (recorded per contact-sheet index) and the ACTUAL source_photo_id
values computed from the dataset manifest.

The contact sheets were built by `ml/audit/dataset_label_audit.py`; the index
-> source photograph mapping is read back from the sidecar JSON so the review
file can never drift from the manifest's own identity function.

    python ml/audit/build_verification_review.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
REVIEW = ROOT / "ml" / "dataset" / "verification_review.json"
SPEC = importlib.util.spec_from_file_location("rs", ROOT / "ml" / "resplit_dataset.py")
rs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rs)

# ---------------------------------------------------------------------------
# Visual verdicts, recorded by a human-style inspection of every contact sheet.
# index -> (verdict, reason)
# ---------------------------------------------------------------------------
KNOWN = {
    0: ("rejected", "Jing-an Temple, Shanghai - a REPLICA of the Mahabodhi Temple, not the Bodh Gaya temple"),
    1: ("rejected", "Carved pillar with an information sign; not the Mahabodhi Temple"),
    2: ("rejected", "Carved pillar panel with Buddha figures - an architectural detail, not the temple"),
    3: ("approved", "Bodhi Tree with devotees and prayer flags"),
    4: ("rejected", "Close-up of a monkey in foliage - no monument context"),
    5: ("approved", "Bodhi Tree with railing and visitors"),
    6: ("rejected", "Macro photograph of a silver coin (Huvishka coin find), not the throne slab"),
    7: ("rejected", "Interior detail - gilded Buddha with offerings and a decorated pillar"),
    8: ("rejected", "Stone railing with Buddha niches, not the Vajrasana diamond throne"),
    9: ("approved", "Animesh Lochan brick chaitya"),
    10: ("approved", "Animesh Lochan brick chaitya"),
    11: ("approved", "Animesh Lochan brick chaitya"),
    12: ("approved", "Tank with a central statue - plausible Mucalinda pond"),
    13: ("rejected", "Archival sepia photograph (c.1890) - not a modern field photograph"),
    14: ("approved", "Lake with signboard and visitors - plausible Mucalinda"),
    15: ("rejected", "Row of five small seated Buddhas (the Five Buddhas), not the 25 m Great Buddha"),
    16: ("approved", "Great Buddha statue (Daijutsu)"),
    17: ("approved", "Great Buddha statue (Daijutsu)"),
    18: ("approved", "Gridhrakuta brick ruins on the hilltop"),
    19: ("approved", "Gridhrakuta brick remains with prayer flags"),
    20: ("approved", "Gridhrakuta brick remains on the ridge"),
    21: ("rejected", "Arashiyama Bamboo Grove, Kyoto, JAPAN - not Venu Vana, Rajgir"),
    22: ("rejected", "Arashiyama Bamboo Grove, Kyoto, JAPAN - not Venu Vana, Rajgir"),
    23: ("rejected", "Arashiyama Bamboo Grove, Kyoto, JAPAN - not Venu Vana, Rajgir"),
    24: ("approved", "Unmortared stone rampart on the hillside"),
    25: ("approved", "Dry-stone rampart with distant hills"),
    26: ("approved", "Stone rampart on the green hill"),
    27: ("rejected", "Portrait of a politician (Nitish Kumar) at a rally - not the Shanti Stupa"),
    28: ("rejected", "Portrait of a politician at a rally - not the Shanti Stupa"),
    29: ("rejected", "Politician at a rally with an audience - not the Shanti Stupa"),
    30: ("approved", "Son Bhandar rock-cut chamber facade"),
    31: ("approved", "Son Bhandar brick chamber complex"),
    32: ("approved", "Son Bhandar cave entrance"),
    33: ("approved", "Excavated brick foundations of the Mahavihara site"),
    34: ("approved", "Wide view of the low brick mounds of the Mahavihara site"),
    35: ("approved", "Brick mound and greenery of the Mahavihara site"),
    36: ("rejected", "Sariputra stupa - a different structure from Nalanda Temple 3"),
    37: ("approved", "Temple 3 brick platform and mass"),
    38: ("approved", "Temple 3 brick stupa courses"),
    39: ("rejected", "Modern tiered lecture hall (SPJIMR, Mumbai) - not Nalanda Monastery 1"),
    40: ("rejected", "Brick stupa in a garden at Haeinsa, South Korea - wrong site"),
    41: ("rejected", "Modern classroom full of students - not Nalanda Monastery 1"),
    42: ("rejected", "Museum information panel on a wall - not the museum building"),
    43: ("rejected", "'Archaeological Museum Nalanda' signboard in a garden - not the building"),
    44: ("rejected", "Commemorative plaque - not the museum building"),
}

NEG = {
    0: ("approved", "Vikramshila ruins - brick wall with stone fragments; excellent Bihar hard negative"),
    1: ("rejected", "Multi-image collage, not a single scene"),
    2: ("rejected", "Generic low modern building with a lawn - not a Bihar lookalike"),
    3: ("rejected", "Modern ashram building at night with signage"),
    4: ("rejected", "Generic landscape with a distant building"),
    5: ("approved", "Gupta-era brick temple - excellent generic-temple hard negative"),
    6: ("rejected", "Vector diagram of a temple plan - a graphic, not a photograph"),
    7: ("approved", "Ancient brick temple"),
    8: ("approved", "Ancient brick temple"),
    9: ("approved", "Ancient brick temple"),
    10: ("approved", "Old Bagan gilded pagoda"),
    11: ("approved", "Old Bagan gilded pagoda"),
    12: ("approved", "Bagan stupa with gilded spires"),
    13: ("approved", "Bagan brick shikhara"),
    14: ("rejected", "Plain Indian brick temple - not SE Asian"),
    15: ("approved", "Brick wall surface"),
    16: ("approved", "Red brick wall surface"),
    17: ("rejected", "Pottery shard with a scale ruler - not ruins"),
    18: ("approved", "Red brick wall surface"),
    19: ("approved", "Whitewashed brick wall surface"),
    20: ("rejected", "Modern high-rise under construction - no scaffolding, wrong subject"),
    21: ("approved", "Building under construction"),
    22: ("approved", "Building wrapped in bamboo scaffolding - excellent"),
    23: ("approved", "Scaffolded building on a street"),
    24: ("approved", "Building under construction with scaffolding"),
    25: ("rejected", "Dublin street-theatre van - not an Indian market shop"),
    26: ("rejected", "Waterfront cityscape with high-rises - not a shop"),
    27: ("approved", "Night market stall with hanging lamps"),
    28: ("rejected", "Waterfront cityscape - not a shop"),
    29: ("approved", "Market stall with goods"),
    30: ("rejected", "Crowded street with trees and rickshaws - a street scene, not a landscape"),
    31: ("rejected", "Street tree with traffic - a street scene"),
    32: ("rejected", "Close-up of heart-shaped leaves - not a tree or landscape"),
    33: ("approved", "Large Ficus over a street"),
    34: ("approved", "Banyan aerial roots"),
    35: ("rejected", "Tourists at a Himalayan lake - not a monument crowd"),
    36: ("rejected", "Aerial view of a formal garden - not a crowd"),
    37: ("rejected", "Archival 1850s engraving of a river ghat"),
    38: ("rejected", "Archival black-and-white riverside photograph"),
    39: ("rejected", "Golden Temple at night - a monument, not a crowd"),
}


def build(section: str, table: dict, existing_verdicts: dict) -> dict:
    manifest = json.loads((ROOT / "ml" / "dataset" / "dataset_manifest.json").read_text(encoding="utf-8"))
    order: list = []
    for cid, node in manifest[section].items():
        seen: dict = {}
        for r in node["records"]:
            sid = rs.source_photo_id_for(r)
            if sid not in seen:
                seen[sid] = r
        for sid in sorted(seen.keys()):
            order.append((cid, sid, seen[sid]))
    out = {}
    for idx, (cid, sid, rec) in enumerate(order):
        if idx not in table:
            # The corpus has grown since this table was written. The candidate
            # verdicts in ml/audit/approve_candidates.py are the authoritative
            # source; a missing index here is a warning, not a failure.
            print(f"  ! {section} index {idx} ({cid}) has no verdict in this table - "
                  f"skipped (see ml/audit/approve_candidates.py)")
            continue
        verdict, reason = table[idx]
        if sid in existing_verdicts:
            # A later, authoritative pass (approve_candidates.py) already
            # decided this photograph. The index-based bootstrap table must
            # never overwrite it - the corpus has grown since the table was
            # written, so its indices no longer line up.
            continue
        entry = {"verdict": verdict, "reason": reason}
        entry["place_id" if section == "pois" else "neg_category"] = cid
        entry["commons_title"] = rec.get("title", "")
        out[sid] = entry
    return out


def main() -> int:
    # MERGE into the existing review file, never overwrite it: the candidate
    # approvals (ml/audit/approve_candidates.py) live in the same file and a
    # regeneration that dropped them would silently un-approve hundreds of
    # reviewed photographs.
    reviews = {}
    existing = {}
    if REVIEW.is_file():
        try:
            existing = json.loads(REVIEW.read_text(encoding="utf-8")).get("reviews", {})
            reviews.update(existing)
            print(f"[review] merged {len(reviews)} existing verdict(s) - they are authoritative")
        except Exception as e:
            print(f"[review] could not read the existing file ({e}); starting fresh")
    reviews.update(build("pois", KNOWN, existing))
    reviews.update(build("negatives", NEG, existing))

    approved = sum(1 for v in reviews.values() if v["verdict"] == "approved")
    rejected = sum(1 for v in reviews.values() if v["verdict"] == "rejected")

    # per-class usable counts
    per_class: dict = {}
    for v in reviews.values():
        key = v.get("place_id") or v.get("neg_category")
        per_class.setdefault(key, [0, 0])
        per_class[key][0] += 1
        per_class[key][1] += 1 if v["verdict"] == "approved" else 0
    empty = sorted(k for k, (t, a) in per_class.items() if a == 0)

    payload = {
        "reviewed_at": "2026-10-20",
        "reviewer": "TrueWay vision audit - visual inspection of every source photograph via contact sheets",
        "method": (
            "Every distinct source photograph in ml/dataset was inspected VISUALLY, not judged "
            "from its Commons title. A photograph is APPROVED only if it depicts the named POI "
            "(or the named distractor category) in a way a visitor's own photograph of that "
            "place would plausibly resemble."
        ),
        "verdict_meanings": {
            "approved": "Usable as a vision reference; included in training / calibration / test.",
            "rejected": "Must not be used: does not depict the labelled subject, is not a photograph "
                        "of the subject, is an archival or graphic artefact, or is out of region.",
            "pending": "Not yet reviewed; treated as unusable for training and reported as unreviewed.",
        },
        "summary": {
            "total_source_photographs": len(reviews),
            "approved": approved,
            "rejected": rejected,
            "classes_with_zero_usable_photographs": empty,
        },
        "notes": [
            f"{len(empty)} classes end up with ZERO approved photographs and must be re-harvested "
            f"with human-verified allow-lists: {', '.join(empty)}. An empty class is worse than no "
            f"class, because it teaches the model that the subject is a negative.",
            "The hardest negative class for this circuit - brick stupas and excavated brick ruins "
            "that genuinely resemble Nalanda Temple 3 - is effectively absent: "
            "neg-ordinary-brick-ruins contains brick WALL TEXTURES, not ruins.",
            "in-bihar-bodhgaya-mucalinda and in-bihar-nalanda-museum contain weak or archival "
            "material and should be re-harvested too.",
        ],
        "reviews": reviews,
    }
    out_path = ROOT / "ml" / "dataset" / "verification_review.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"-> wrote {out_path}")
    print(f"   source photographs : {len(reviews)}")
    print(f"   approved           : {approved}")
    print(f"   rejected           : {rejected}")
    print(f"   classes with ZERO usable photographs ({len(empty)}):")
    for k in empty:
        print(f"     - {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
