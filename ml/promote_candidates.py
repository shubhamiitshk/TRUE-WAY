"""Promotes APPROVED quarantined candidates into the training corpus.

    harvest_candidates.py       -> ml/dataset/candidates/            (quarantine)
    build_verification_review.py-> ml/dataset/verification_review.json (verdicts)
    promote_candidates.py       -> ml/dataset/known|negatives/       (corpus)
    resplit_dataset.py          -> re-split by source photograph

Only candidates whose `source_photo_id` carries an `approved` verdict in the
review file are promoted. `rejected` candidates stay quarantined and `pending`
candidates are never promoted. Promotion is idempotent: re-running it does not
duplicate photographs.

    python ml/promote_candidates.py --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "ml" / "dataset"
MANIFEST = DATASET_DIR / "dataset_manifest.json"
CANDIDATES = DATASET_DIR / "candidates_manifest.json"
REVIEW = DATASET_DIR / "verification_review.json"

_spec = importlib.util.spec_from_file_location("hv", ROOT / "ml" / "harvest_training_dataset.py")
hv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hv)

_ac_spec = importlib.util.spec_from_file_location("ac", ROOT / "ml" / "audit" / "approve_candidates.py")
ac = importlib.util.module_from_spec(_ac_spec)
_ac_spec.loader.exec_module(ac)


def main() -> int:
    ap = argparse.ArgumentParser(description="Promote approved quarantined candidates into the corpus")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not MANIFEST.is_file() or not CANDIDATES.is_file() or not REVIEW.is_file():
        print("need dataset_manifest.json, candidates_manifest.json and verification_review.json")
        return 2

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))["reviews"]

    # place_id -> category id map for the corpus destination folder
    pois = manifest.get("pois", {})
    negs = manifest.get("negatives", {})

    # which candidates are approved, grouped by the class the REVIEW assigns
    # (a photograph may have been harvested under one POI's search but actually
    # show another, so the review's class wins over the candidate's class)
    approved = defaultdict(list)
    for cid, node in candidates.get("classes", {}).items():
        for rec in node.get("records", []):
            sid = rec.get("source_photo_id", "")
            entry = review.get(sid, {})
            verdict = str(entry.get("verdict", "pending")).lower()
            if verdict != "approved":
                continue
            target = entry.get("place_id") or entry.get("neg_category") or cid
            approved[target].append(rec)

    # existing source photos per class (so we never promote twice)
    existing = defaultdict(set)
    for section in ("pois", "negatives"):
        for cid, node in manifest.get(section, {}).items():
            for r in node.get("records", []):
                existing[cid].add(r.get("source_photo_id"))

    promoted = 0
    skipped = 0
    moved = 0
    for cid, recs in approved.items():
        target_section = "pois" if cid in pois else ("negatives" if cid in negs else None)
        if target_section is None:
            continue
        node = manifest[target_section][cid]
        dest_dir = DATASET_DIR / ("known" if target_section == "pois" else "negatives") / cid
        for rec in recs:
            sid = rec["source_photo_id"]
            if sid in existing[cid]:
                skipped += 1
                continue
            # The photograph may already sit in the corpus under a DIFFERENT
            # class (a verdict can be corrected after promotion). Move it.
            placed = False
            for other_section in ("pois", "negatives"):
                for other_cid, other_node in manifest.get(other_section, {}).items():
                    if other_cid == cid and other_section == target_section:
                        continue
                    keep = []
                    for r in other_node.get("records", []):
                        if r.get("source_photo_id") == sid:
                            moved += 1
                            continue
                        keep.append(r)
                    if len(keep) != len(other_node.get("records", [])):
                        other_node["records"] = keep
            src = ROOT / rec["local_path"]
            if not src.is_file():
                continue
            dest_dir.mkdir(parents=True, exist_ok=True)
            prefix = cid.split("-")[-1][:24]
            dest = dest_dir / f"{prefix}_{sid.split(':')[-1][:12]}.jpg"
            if not dest.is_file():
                shutil.copy2(src, dest)
            raw = dest.read_bytes()
            new_rec = {
                "title": rec.get("title", ""),
                "url": rec.get("url", ""),
                "original_url": rec.get("original_url", rec.get("url", "")),
                "photographer": rec.get("photographer", ""),
                "visit": rec.get("visit", ""),
                "license": rec.get("license", ""),
                "local_path": str(dest.relative_to(ROOT)).replace("\\", "/"),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "source_photo_id": sid,
                "session_id": sid,
                "verification_status": "approved",
                "is_augmented": False,
            }
            node.setdefault("records", []).append(new_rec)
            existing[cid].add(sid)
            promoted += 1

    print(f"promoted {promoted} candidate photograph(s); moved {moved} between classes; "
          f"skipped {skipped} already present")

    # ------------------------------------------------------------------
    # Corpus-level class changes for photographs that were SEEDED directly
    # into the corpus and never went through the quarantine. The candidate
    # loop above cannot reach them: they are not in the candidate pool.
    # ------------------------------------------------------------------
    corpus_moved = 0
    corpus_removed = 0
    for title, (target_cid, _reason) in getattr(ac, "MOVE_BY_TITLE", {}).items():
        target_section = "pois" if target_cid in pois else ("negatives" if target_cid in negs else None)
        if target_section is None:
            continue
        for section in ("pois", "negatives"):
            for other_cid, other_node in manifest.get(section, {}).items():
                if section == target_section and other_cid == target_cid:
                    continue
                keep, removed = [], []
                for r in other_node.get("records", []):
                    (removed if r.get("title") == title else keep).append(r)
                if not removed:
                    continue
                other_node["records"] = keep
                for r in removed:
                    src = ROOT / r["local_path"]
                    dest_dir = DATASET_DIR / ("known" if target_section == "pois"
                                              else "negatives") / target_cid
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    prefix = target_cid.split("-")[-1][:24]
                    dest = dest_dir / f"{prefix}_{r['source_photo_id'].split(':')[-1][:12]}.jpg"
                    rec = dict(r)
                    if not dest.is_file() and src.is_file():
                        shutil.copy2(src, dest)
                        rec["local_path"] = str(dest.relative_to(ROOT)).replace("\\", "/")
                        rec["sha256"] = hashlib.sha256(dest.read_bytes()).hexdigest()
                    manifest[target_section][target_cid].setdefault("records", []).append(rec)
                    corpus_moved += 1

    for title in getattr(ac, "REJECT_CORPUS_TITLES", {}):
        for section in ("pois", "negatives"):
            for other_cid, other_node in manifest.get(section, {}).items():
                keep = [r for r in other_node.get("records", []) if r.get("title") != title]
                corpus_removed += len(other_node.get("records", [])) - len(keep)
                other_node["records"] = keep

    if corpus_moved or corpus_removed:
        print(f"corpus-level: re-classed {corpus_moved} photograph(s); "
              f"removed {corpus_removed} photograph(s)")
    for section in ("pois", "negatives"):
        for cid, node in manifest.get(section, {}).items():
            photos = len({r.get("source_photo_id") for r in node.get("records", [])})
            print(f"  {section:11s} {cid:42s} source photos: {photos}")

    if not args.dry_run:
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n-> wrote {MANIFEST}")
        print("   Now run:  python ml/resplit_dataset.py")
    else:
        print("\n(dry run: manifest not written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
