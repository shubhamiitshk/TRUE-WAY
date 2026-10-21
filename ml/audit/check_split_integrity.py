"""Hard CI gate for dataset integrity. Stdlib only. Exits non-zero on failure.

Checks
------
1. **No source photograph spans more than one split.** Rows derived from one
   photograph are not independent trials, so a split that mixes them cannot
   certify a false-accept rate (ml/README.md §Protocol; blueprint §7.2).
2. **No content hash is claimed by more than one class.** The same photograph
   under two place labels is a label conflict, not a hard negative.
3. **Every photograph in the corpus is human-verified.** A photograph with no
   verdict, or with a `pending` verdict, must not be in the corpus.
4. **The effective sample size is reported** and compared against the minimum
   needed to certify the release gate (>= 59 independent negatives, per the
   Clopper-Pearson rule-of-three: 1 - 0.05^(1/N) <= 0.05).

    python ml/audit/check_split_integrity.py
    python ml/audit/check_split_integrity.py --manifest ml/dataset/dataset_manifest.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_MANIFEST = ROOT / "ml" / "dataset" / "dataset_manifest.json"
DEFAULT_REVIEW = ROOT / "ml" / "dataset" / "verification_review.json"

MIN_INDEPENDENT_NEGATIVES = 59  # 1 - 0.05^(1/59) = 4.95% <= 5%


def main() -> int:
    ap = argparse.ArgumentParser(description="Dataset integrity gate (CI)")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--review", default=str(DEFAULT_REVIEW))
    ap.add_argument("--min-negatives", type=int, default=MIN_INDEPENDENT_NEGATIVES)
    ap.add_argument("--warn-only", action="store_true",
                    help="Report the effective-N shortfall without failing (for corpora "
                         "that are still being collected)")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    review = {}
    review_path = Path(args.review)
    if review_path.is_file():
        review = json.loads(review_path.read_text(encoding="utf-8")).get("reviews", {})

    errors: list[str] = []
    warnings: list[str] = []

    # ---------------------------------------------------------------- 1 + 2
    by_source_splits = defaultdict(set)
    by_source_places = defaultdict(set)
    by_hash_owners = defaultdict(set)
    by_series_splits = defaultdict(set)
    for section in ("pois", "negatives"):
        for cid, node in manifest.get(section, {}).items():
            for r in node.get("records", []):
                sid = r.get("source_photo_id") or r.get("original_url") or r.get("local_path")
                by_source_splits[sid].add(r.get("split", "?"))
                by_source_places[sid].add(f"{section}:{cid}")
                series = r.get("source_subject_id") or sid
                by_series_splits[series].add(r.get("split", "?"))
                sha = r.get("sha256")
                if sha:
                    by_hash_owners[sha].add(f"{section}:{cid}")

    shared = {s: sorted(v) for s, v in by_source_splits.items() if len(v) > 1}
    if shared:
        errors.append(
            f"{len(shared)} source photograph(s) span more than one split "
            f"(near-duplicate leakage). Examples: {list(shared.items())[:3]}"
        )

    # The SERIES is the unit that must not straddle a split: several
    # photographs of one monument from one visit are near-duplicates of each
    # other, so a series that appears in the reference set AND in the test
    # split is the same failure as a photograph that does - only harder to see.
    # This check was missing, and it was blind to a real leak: fifteen
    # photographs of one Thai temple (whose Commons titles carry an ELEVEN-digit
    # photo id that the old normalisation did not strip) sat in the reference,
    # the calibration and the test split at once.
    series_shared = {s: sorted(v) for s, v in by_series_splits.items() if len(v) > 1}
    if series_shared:
        errors.append(
            f"{len(series_shared)} subject series span more than one split "
            f"(near-duplicate leakage between photographs of the same monument "
            f"from the same visit). Examples: {list(series_shared.items())[:3]}"
        )

    conflicts = {h: sorted(c) for h, c in by_hash_owners.items() if len(c) > 1}
    if conflicts:
        errors.append(
            f"{len(conflicts)} content hash(es) claimed by more than one class "
            f"(label conflict). Examples: {list(conflicts.items())[:3]}"
        )

    # ---------------------------------------------------------------- 3
    unverified = []
    for section in ("pois", "negatives"):
        for cid, node in manifest.get(section, {}).items():
            for r in node.get("records", []):
                sid = r.get("source_photo_id") or ""
                verdict = str(review.get(sid, {}).get("verdict", "pending")).lower()
                if verdict != "approved":
                    unverified.append(f"{section}:{cid}:{sid}:{verdict}")
    if unverified:
        errors.append(
            f"{len(unverified)} corpus photograph(s) are NOT human-verified as usable. "
            f"Examples: {unverified[:3]}"
        )

    # ---------------------------------------------------------------- 4
    def _series(r):
        return r.get("source_subject_id") or r.get("source_photo_id")

    # ---------------------------------------------------------------- 3b
    # A SUBJECT SERIES must not carry two place labels.
    #
    # The subject series is the unit of independence for every statistical
    # bound in this project: photographs of the same monument from the same
    # visit are near-duplicates of each other. If one series contributes
    # photographs to two different places, the series is simultaneously a
    # training signal for one place and a test trial for another, and the
    # effective sample size and the label-conflict count both become
    # meaningless. This is not hypothetical: the "Nalanda ruins and
    # archaeological site" series was filed under the Nalanda Mahavihara while
    # its partner photograph was filed under the Sariputta Stupa (Temple 3),
    # and the evaluator's label-conflict check caught it.
    series_labels: dict = {}
    for section in ("pois", "negatives"):
        for cid, node in manifest.get(section, {}).items():
            for r in node.get("records", []):
                s = _series(r)
                if not s:
                    continue
                series_labels.setdefault(s, set()).add(f"{section}:{cid}")
    cross_class = {s: sorted(v) for s, v in series_labels.items() if len(v) > 1}
    if cross_class:
        errors.append(
            f"{len(cross_class)} subject series carry MORE THAN ONE place label "
            f"(a near-duplicate series split across two classes). Examples: "
            f"{list(cross_class.items())[:3]}"
        )

    test_neg_series = {
        _series(r)
        for node in manifest.get("negatives", {}).values()
        for r in node.get("records", []) if r.get("split") == "test"
    }
    test_known_series = {
        _series(r)
        for node in manifest.get("pois", {}).values()
        for r in node.get("records", []) if r.get("split") == "test"
    }
    test_neg_photos = {
        r.get("source_photo_id")
        for node in manifest.get("negatives", {}).values()
        for r in node.get("records", []) if r.get("split") == "test"
    }
    test_known_photos = {
        r.get("source_photo_id")
        for node in manifest.get("pois", {}).values()
        for r in node.get("records", []) if r.get("split") == "test"
    }
    n_neg = len([s for s in test_neg_series if s])
    n_known = len([s for s in test_known_series if s])
    if n_neg < args.min_negatives:
        msg = (f"effective independent negatives in the test split = {n_neg}; "
               f"{args.min_negatives} are needed to certify a <=5% false-accept rate "
               f"(1 - 0.05^(1/N) <= 0.05). Collect ~{args.min_negatives - n_neg} more "
               f"INDEPENDENT hard-negative photographs.")
        (warnings if args.warn_only else errors).append(msg)

    # ---------------------------------------------------------------- 5
    # The benchmark CSV must be DERIVED FROM THIS MANIFEST. A stale CSV would
    # silently report a different experiment (a stale subject id once made the
    # whole negative test set look like a single subject series).
    bench = ROOT / "tests" / "fixtures" / "retrieval_benchmark_250.csv"
    if bench.is_file():
        import csv as _csv
        rows = list(_csv.DictReader(bench.open("r", encoding="utf-8-sig", newline="")))
        index: dict = {}
        for section in ("pois", "negatives"):
            for cid, node in manifest.get(section, {}).items():
                for r in node.get("records", []):
                    index[r.get("source_photo_id")] = (r.get("split"), r.get("source_subject_id"))
        unknown_photos = [r.get("source_photo_id") for r in rows
                          if r.get("query_kind") == "unknown"]
        missing = sorted({p for p in unknown_photos if p not in index})
        if missing:
            errors.append(
                f"{len(missing)} benchmark row(s) reference a photograph that is not in the "
                f"manifest — the benchmark CSV is STALE. Re-run ml/train_arcface_pipeline.py. "
                f"Examples: {missing[:3]}"
            )
        mismatch = [
            r.get("source_photo_id") for r in rows
            if r.get("query_kind") == "unknown"
            and r.get("source_photo_id") in index
            and index[r.get("source_photo_id")][0] != r.get("split")
        ]
        if mismatch:
            errors.append(
                f"{len(mismatch)} benchmark row(s) have a split that disagrees with the "
                f"manifest — the benchmark CSV is STALE."
            )
        subj_mismatch = [
            r.get("source_photo_id") for r in rows
            if r.get("query_kind") == "unknown"
            and r.get("source_photo_id") in index
            and index[r.get("source_photo_id")][1] != r.get("source_subject_id")
        ]
        if subj_mismatch:
            errors.append(
                f"{len(subj_mismatch)} benchmark row(s) carry a subject id that disagrees with "
                f"the manifest — the benchmark CSV is STALE."
            )

    # ---------------------------------------------------------------- report
    print("=== DATASET INTEGRITY GATE ===")
    print(f"  corpus photographs          : "
          f"{len({s for s in by_source_splits})}")
    print(f"  independent test SUBJECT SERIES: known={n_known}  negative={n_neg}")
    print(f"  (from {len(test_known_photos)} known / {len(test_neg_photos)} negative photographs)")
    print(f"  (a false-accept rate can only be certified at the EFFECTIVE n)")
    if errors:
        print("  RESULT: FAIL")
        for e in errors:
            print("   ! " + e)
    else:
        print("  RESULT: PASS")
    for w in warnings:
        print("   ~ " + w)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
