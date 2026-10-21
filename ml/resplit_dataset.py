"""Re-split an existing harvested corpus by SOURCE PHOTOGRAPH.

Re-assigns `ref` / `calib` / `test` so that every row derived from one source
photograph lives in exactly one split, and writes the corrected manifest with a
`source_photo_id` on every record.

This is the fix for the leakage documented in
`docs/audit/VISION_DETECTION_AUDIT_AND_RECOMMENDATIONS.md` §2 F1: the previous
harvester cycled `canonical_bases[i % 3]`, putting a photometric derivative of
the *same* source photograph into every split while labelling the rows with
disjoint-looking `(photographer, visit)` strings.

No network access is required — the already-downloaded images are reused.

    python ml/resplit_dataset.py                # re-split + report
    python ml/resplit_dataset.py --dry-run      # report only, do not write
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "ml" / "dataset"
MANIFEST = DATASET_DIR / "dataset_manifest.json"
WORK_DIR = ROOT / "ml" / "models" / "s0"

_spec = importlib.util.spec_from_file_location(
    "harvest", ROOT / "ml" / "harvest_training_dataset.py")
harvest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(harvest)


def _load_frozen_embeddings() -> dict:
    """The FROZEN backbone embeddings of the corpus, keyed by local path.

    They are produced once by the training pipeline and cached; the split uses
    them to measure how hard each series is, before any adapter is trained.
    """
    cache = WORK_DIR / "extracted_embeddings_512.npz"
    if not cache.is_file():
        return {}
    try:
        import numpy as np
        data = np.load(cache)
        return {k: data[k] for k in data.files}
    except Exception:
        return {}


def _place_difficulty_order(manifest: dict):
    """A function scoring a series by how PLACE-LIKE it is.

    For a positive class that is how distinctive the series is; for a negative
    class it is how confusable the series is with a place - which is exactly
    what makes a negative hard.
    """
    import numpy as np

    frozen = _load_frozen_embeddings()
    place_centroids = []
    for cid, node in manifest.get("pois", {}).items():
        if not _poi_spec(cid).get("vision_class", True):
            continue
        vecs = []
        for rec in node.get("records", []):
            v = frozen.get(rec.get("local_path", ""))
            if v is not None:
                vecs.append(np.asarray(v, dtype=np.float32))
        if vecs:
            m = np.mean(np.stack(vecs), axis=0)
            n = float(np.linalg.norm(m))
            if n > 0:
                place_centroids.append(m / n)
    if not place_centroids:
        return lambda recs: 0.0
    P = np.stack(place_centroids)

    def score(recs: list) -> float:
        vecs = [frozen.get(r.get("local_path", "")) for r in recs]
        vecs = [np.asarray(v, dtype=np.float32) for v in vecs if v is not None]
        if not vecs:
            return 0.0
        m = np.mean(np.stack(vecs), axis=0)
        n = float(np.linalg.norm(m))
        if n <= 0:
            return 0.0
        m = m / n
        return float(np.max(P @ m))
    return score


def subject_id_for(rec: dict) -> str:
    """The SUBJECT SERIES a photograph belongs to.

    Photographs of the same monument from the same visit are near-duplicates
    of each other, so the unit of independence for a statistical bound is the
    subject series, not the photograph.

    The series id is ALWAYS recomputed. The stored `source_subject_id` was
    previously trusted, which meant a record kept whatever id it was given
    when it was first admitted to the corpus - and after the normalisation
    improved, those stale ids kept the old (wrong) grouping alive forever.
    The canonical implementation lives in `harvest_training_dataset.py` so the
    splitter and the re-splitter can never drift apart again.
    """
    return harvest.subject_series_id(
        rec.get("photographer") or "", rec.get("title") or "") 


def source_photo_id_for(rec: dict) -> str:
    """Stable identity of the SOURCE photograph a record derives from.

    The Commons file title is the identity of the original upload; the
    `original_url` is the same identity expressed as a URL. Either is used.
    """
    title = (rec.get("title") or "").strip()
    if title:
        return "commons:" + hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]
    url = (rec.get("original_url") or rec.get("local_path") or "").strip()
    return "local:" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]



def _poi_spec(pid: str) -> Dict[str, object]:
    """The POI_SPECS entry for a place id (empty dict when unknown)."""
    for spec in harvest.POI_SPECS:
        if str(spec.get("place_id")) == pid:
            return spec
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-split the harvested corpus by source photograph")
    ap.add_argument("--dry-run", action="store_true", help="Report only; do not write the manifest")
    ap.add_argument("--keep-augmented", action="store_true",
                    help="Keep the previously generated augmented rows instead of regenerating them")
    ap.add_argument("--keep-orphans", action="store_true",
                    help="Do not delete image files that the new manifest no longer references")
    args = ap.parse_args()

    if not MANIFEST.is_file():
        print(f"manifest not found: {MANIFEST}", file=sys.stderr)
        return 2

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    photo_status = harvest.load_photo_status()
    review = harvest.load_verification_review()

    # ---------------------------------------------------------------- register
    # A negative category declared in the harvest spec but missing from the
    # manifest is REGISTERED here, empty. Without this a newly declared
    # category can never receive photographs: the promoter only promotes into a
    # class the manifest already knows, so a new hard-negative category would
    # be harvested, reviewed, approved - and then silently dropped.
    manifest.setdefault("negatives", {})
    for spec in harvest.NEGATIVE_SPECS:
        ncat = str(spec["neg_category"])
        if ncat not in manifest["negatives"]:
            manifest["negatives"][ncat] = {
                "label": str(spec.get("label", ncat)),
                "vision_class": False,
                "vision_note": str(spec.get("vision_note", "")),
                "records": [],
            }
            print(f"  ++ registered new negative category: {ncat}")

    # ---------------------------------------------------------------- purge
    # Remove every previously generated camera variation before re-splitting.
    # A variation is derived from a base photograph; if the base changed (it
    # was re-copied under a new name after a class change) the old variation is
    # a variation of the WRONG photograph, and because the embedding cache is
    # keyed by path it would silently poison the class centroid.
    import re as _re
    aug_pat = _re.compile(r"_[0-9a-f]{8}_(ref|calib|test)_\d{2}_m\d+\.")
    purged = 0
    for img in sorted((ROOT / "ml" / "dataset").rglob("*.jpg")):
        if "candidates" in img.parts:
            continue
        if aug_pat.search(img.name):
            img.unlink()
            purged += 1
    print(f"[resplit] purged {purged} stale camera variation(s)")

    # ---------------------------------------------------------------- collect
    # One "base" record per source photograph: the unaugmented download.
    def base_records(node: dict) -> list:
        seen: dict = {}
        for r in node.get("records", []):
            sid = source_photo_id_for(r)
            r["source_photo_id"] = sid
            if sid not in seen:
                seen[sid] = r
        return [seen[s] for s in sorted(seen.keys())]

    def reviewed(rec: dict) -> bool:
        verdict = str(review.get(rec.get("source_photo_id", ""), {}).get("verdict", "pending")).lower()
        rec["verification_status"] = verdict
        # ONLY an approved photograph may enter the corpus. A rejected one must
        # not, and a PENDING one - never reviewed - must not either: the review
        # file's own meaning is "pending: not yet reviewed; treated as unusable
        # for training". The previous check kept everything that was not
        # explicitly rejected, so an un-reviewed photograph stayed in the
        # corpus and was trained on.
        return verdict == "approved"

    # ---------------------------------------------------------------------
    # DIFFICULTY STRATIFICATION
    #
    # The split must give every split the same mix of HARD and EASY series.
    # At random, the calibration split ended up without the hardest example of
    # the hardest negative categories: its hardest negative had an open margin
    # of -0.26 while the test split's hardest was +0.13, and the threshold
    # fitted on the calibration split admitted 42 of 72 test series. A
    # threshold of 0.0 - which the calibration sample simply did not contain
    # evidence for - would have admitted 5 of 72.
    #
    # The difficulty of a series is measured with the FROZEN backbone, before
    # any adapter is trained: how close its photographs are to the PLACE
    # classes. A negative series that looks like a place is a hard negative; a
    # negative series that looks like nothing in the corpus is an easy one.
    # Dealing the series out hardest-first gives every split the same mix.
    # ---------------------------------------------------------------------
    # The split must be REPRODUCIBLE: the same corpus must always produce the
    # same split, or the benchmark is not a benchmark.
    #
    # An ordering by "how place-like is this series" was tried and rejected: it
    # is computed from the frozen backbone embeddings, and that cache is filled
    # INCREMENTALLY as the pipeline runs - so the same corpus produced a
    # different split on the next run, and the measured false-accept rate moved
    # between 2 and 10 failures with no change to the data at all. The split
    # is now ordered by the series size alone, which depends only on the
    # manifest.
    def series_order_for(section: str, kept: list) -> list:
        by_series: dict = {}
        for rec in kept:
            s = subject_id_for(rec)
            by_series.setdefault(s, []).append(rec)
        return sorted(by_series, key=lambda s: (-len(by_series[s]), s))

    report = []
    for section, counts, minimums in (
        ("pois", (4, 6, 10), (2, 2, 2)),
        ("negatives", (3, 6, 13), (2, 1, 2)),
    ):
        for cid, node in manifest.get(section, {}).items():
            bases = base_records(node)
            kept = [b for b in bases if reviewed(b)]
            dropped = len(bases) - len(kept)
            if not kept:
                # Every source photograph was rejected (or the class is not a
                # vision class). The vision_class flag is ALWAYS derived from
                # the POI_SPEC, never from a stale manifest, so a class that
                # becomes search-only cannot stay flagged as a vision class.
                spec0 = _poi_spec(cid)
                node["vision_class"] = bool(spec0.get("vision_class", True)) if spec0 else True
                node["vision_note"] = str(spec0.get("vision_note", "") or "") if spec0 else ""
                if not node["vision_class"]:
                    print(f"  -- {cid}: not a vision class (search-only / spotter item)")
                else:
                    print(f"  !! {cid}: every source photograph was rejected by review — class removed")
                node["records"] = []
                node["distinct_source_photos"] = 0
                node["total_split_count"] = 0
                continue
            recs = harvest.assign_photo_grouped_splits(
                kept, counts_per_split=counts, min_photos_per_split=minimums,
                series_order=series_order_for(section, kept))
            for r in recs:
                r["source_subject_id"] = subject_id_for(r)
            if section == "negatives":
                for r in recs:
                    r["neg_category"] = cid
                    r["label"] = node.get("label", "")
            node["records"] = recs
            # The vision_class flag comes from the POI SPEC (the source of
            # truth), not from whatever a previous manifest happened to say.
            spec = _poi_spec(cid)
            is_vision = bool(spec.get("vision_class", True)) if spec else True
            node["vision_class"] = is_vision
            node["vision_note"] = str(spec.get("vision_note", "") or "") if spec else ""
            if not is_vision:
                # A place that is not visually identifiable carries NO vision
                # reference: it is a spotter item on its parent's place card.
                # Its photographs are removed from the corpus entirely so they
                # can never be mistaken for a reference vector.
                node["records"] = []
                node["total_split_count"] = 0
                node["distinct_source_photos"] = 0
            node["distinct_source_photos"] = len({r["source_photo_id"] for r in recs})
            node["total_split_count"] = len(recs)
            node["photo_status"] = photo_status.get(cid, node.get("photo_status", "UNSPECIFIED"))
            node["rejected_source_photos"] = dropped
            by_split = defaultdict(set)
            for r in recs:
                by_split[r["split"]].add(r["source_photo_id"])
            report.append((section, cid, len(bases), len(kept),
                           {k: len(v) for k, v in sorted(by_split.items())}))

    # ---------------------------------------------------------------- integrity
    problems = []
    for section in ("pois", "negatives"):
        by_source = defaultdict(set)
        for cid, node in manifest.get(section, {}).items():
            for r in node.get("records", []):
                by_source[r["source_photo_id"]].add(r["split"])
        shared = {s: sorted(v) for s, v in by_source.items() if len(v) > 1}
        if shared:
            problems.append(f"{section}: {len(shared)} source photographs span >1 split")

    # cross-class content duplicates
    by_hash = defaultdict(set)
    for section in ("pois", "negatives"):
        for cid, node in manifest.get(section, {}).items():
            for r in node.get("records", []):
                by_hash[r.get("sha256", "")].add(f"{section}:{cid}")
    conflicts = {h: sorted(c) for h, c in by_hash.items() if len(c) > 1}
    if conflicts:
        problems.append(f"{len(conflicts)} content hashes claimed by more than one class")

    manifest["split_unit"] = "source_photo_id"
    manifest["split_unit_note"] = (
        "Splits are assigned by SOURCE PHOTOGRAPH. Every derivative of one source "
        "photograph lives in exactly one split, so the rows of a split are "
        "independent trials and the Clopper-Pearson bound on the false-accept "
        "rate is meaningful."
    )
    manifest.setdefault("summary", {})
    manifest["summary"]["resplit_at"] = None  # filled by caller if desired
    manifest["summary"]["distinct_source_photographs"] = len(
        {r["source_photo_id"] for s in ("pois", "negatives")
         for n in manifest.get(s, {}).values() for r in n.get("records", [])})

    print("=== RE-SPLIT REPORT ===")
    for section, cid, n_bases, n_kept, per_split in report:
        print(f"  {section:11s} {cid:42s} photos {n_bases:2d}->{n_kept:2d}  per-split {per_split}")
    print()
    if problems:
        print("=== INTEGRITY: FAIL ===")
        for p in problems:
            print("  ! " + p)
    else:
        print("=== INTEGRITY: PASS ===")
        print("  no source photograph spans more than one split; no cross-class content duplicates")

    if not args.dry_run:
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n-> wrote {MANIFEST}")
        if not args.keep_orphans:
            referenced = {r["local_path"] for s in ("pois", "negatives")
                          for n in manifest.get(s, {}).values() for r in n.get("records", [])}
            removed = 0
            # NEVER touch the quarantine: unreviewed candidates are not in the
            # manifest, and pruning them would destroy the pool the reviewer
            # has not yet worked through.
            quarantine = (DATASET_DIR / "candidates").resolve()
            for img in sorted((ROOT / "ml" / "dataset").rglob("*.jpg")):
                if quarantine in img.resolve().parents:
                    continue
                rel = str(img.relative_to(ROOT)).replace("\\", "/")
                if rel not in referenced:
                    img.unlink()
                    removed += 1
            print(f"-> pruned {removed} unreferenced image file(s) (quarantine untouched)")
    else:
        print("\n(dry run: manifest not written)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
