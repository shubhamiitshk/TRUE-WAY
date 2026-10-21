"""Synchronises the candidate verdicts in `verification_review.json` with the
review tables in `ml/audit/approve_candidates.py`.

    python ml/audit/sync_review_to_tables.py            # reconcile
    python ml/audit/sync_review_to_tables.py --check    # CI gate: fail on drift

The tables are the single source of truth for the CANDIDATE pool. This tool
recomputes every candidate's verdict from them by running the approval step's
OWN logic against a temporary copy of the review file, so the two can never
disagree about the rules.

Why it exists: the approval script only ever ADDED verdicts, so a photograph
removed from a table kept its old "approved" verdict and stayed in the corpus.
A retracted corpus change therefore survived several rebuilds. This tool makes
the tables authoritative in both directions.

The verdicts for photographs that are already IN the corpus and are not
candidates are left untouched: they were decided by the original visual pass.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
REVIEW = ROOT / "ml" / "dataset" / "verification_review.json"
CANDS = ROOT / "ml" / "dataset" / "candidates_manifest.json"

spec = importlib.util.spec_from_file_location("ac", ROOT / "ml" / "audit" / "approve_candidates.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)


def candidate_sids() -> set:
    cands = json.loads(CANDS.read_text(encoding="utf-8"))
    out = set()
    for node in cands.get("classes", {}).values():
        for rec in node.get("records", []):
            out.add(rec["source_photo_id"])
    return out


def expected_reviews() -> dict:
    """The verdicts the approval step would write, computed on a copy."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "verification_review.json"
        shutil.copy2(REVIEW, copy)
        original = ac.REVIEW
        ac.REVIEW = copy
        try:
            ac.main()
        finally:
            ac.REVIEW = original
        return json.loads(copy.read_text(encoding="utf-8"))["reviews"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync the candidate verdicts with the review tables")
    ap.add_argument("--check", action="store_true",
                    help="Exit non-zero if the review file and the tables disagree")
    args = ap.parse_args()

    current = json.loads(REVIEW.read_text(encoding="utf-8"))["reviews"]
    wanted = expected_reviews()
    cands = candidate_sids()

    diffs = []
    for sid in sorted(cands):
        a = current.get(sid, {})
        b = wanted.get(sid, {})
        if a.get("verdict") != b.get("verdict") or \
                (a.get("place_id") or a.get("neg_category")) != (b.get("place_id") or b.get("neg_category")):
            diffs.append((sid, a.get("verdict"), b.get("verdict")))

    print(f"candidate verdicts: {len(cands)} candidates, {len(diffs)} disagreement(s)")
    for sid, was, now in diffs[:5]:
        print(f"    {sid}: {was} -> {now}")
    if args.check:
        if diffs:
            print("FAIL: the review file and the review tables disagree. Run "
                  "python ml/audit/sync_review_to_tables.py to reconcile them.")
            return 1
        print("PASS: the review file and the review tables agree.")
        return 0
    if not diffs:
        print("already in sync")
        return 0
    payload = json.loads(REVIEW.read_text(encoding="utf-8"))
    for sid, _was, _now in diffs:
        if sid in wanted:
            payload["reviews"][sid] = wanted[sid]
    REVIEW.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    n_app = sum(1 for v in payload["reviews"].values() if v.get("verdict") == "approved")
    n_rej = sum(1 for v in payload["reviews"].values() if v.get("verdict") == "rejected")
    print(f"-> wrote {REVIEW}  ({n_app} approved, {n_rej} rejected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
