"""Workstation retrieval baseline & Gate 2 Calibration Evaluator — blueprint §7.6 / §18.2 / Gate G03.

Scores precomputed similarity rows; stdlib only. Evaluates top-1/top-3
recognition accuracy, open-set false-accept rate, exact Clopper-Pearson 95%
upper confidence bound on false accepts, and calibration sweeps.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def load(rows_path: Path) -> list[dict]:
    with rows_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clopper_pearson_upper_bound(k_errors: int, n_trials: int, alpha: float = 0.05) -> float:
    """Exact one-sided (1 - alpha) Clopper-Pearson upper bound on False Accept Rate."""
    if n_trials <= 0 or k_errors >= n_trials:
        return 1.0
    if k_errors == 0:
        return 1.0 - math.pow(alpha, 1.0 / n_trials)

    def cdf_le_k(p: float) -> float:
        return sum(
            math.comb(n_trials, i) * (p ** i) * ((1.0 - p) ** (n_trials - i))
            for i in range(k_errors + 1)
        )

    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if cdf_le_k(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def evaluate_gate2_metrics(
    known_top1_hits: int,
    known_top3_hits: int,
    total_known: int,
    false_accepts: int,
    total_negatives: int,
) -> Dict[str, object]:
    top1 = known_top1_hits / max(1, total_known)
    top3 = known_top3_hits / max(1, total_known)
    far_point = false_accepts / max(1, total_negatives)
    far_cp95_upper = clopper_pearson_upper_bound(false_accepts, total_negatives, alpha=0.05)
    passes_gate2 = (
        total_known >= 150
        and total_negatives >= 100
        and top1 >= 0.85
        and top3 >= 0.95
        and far_cp95_upper <= 0.05
    )
    return {
        "total_known": total_known,
        "total_negatives": total_negatives,
        "top1_accuracy": round(top1, 4),
        "top3_recall": round(top3, 4),
        "far_point": round(far_point, 4),
        "far_clopper_pearson_95_upper": round(far_cp95_upper, 4),
        "passes_gate2_statistical_bound": passes_gate2,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="CSV similarity rows (see ml/fixtures/).")
    ap.add_argument("--threshold", type=float, default=0.72, help="Accept iff score >= threshold (default 0.72).")
    args = ap.parse_args()

    rows = load(Path(args.input))
    test = [r for r in rows if r.get("split", "test") == "test"]
    known = [r for r in test if r.get("query_kind") == "known"]
    unknown = [r for r in test if r.get("query_kind") == "unknown"]
    if not known and not unknown:
        print("No test-split rows found; check the split column.", file=sys.stderr)
        return 2

    t = args.threshold
    top1_raw = sum(1 for r in known if r["place_id"] == r["correct_place_id"])
    top1_accepted = sum(1 for r in known
                        if r["place_id"] == r["correct_place_id"] and float(r["score"]) >= t)
    top3 = sum(1 for r in known if r.get("top3_hit", "0") == "1")
    accepted_known = sum(1 for r in known if float(r["score"]) >= t)
    fa = sum(1 for r in unknown if float(r["score"]) >= t)
    fa_upper = clopper_pearson_upper_bound(fa, len(unknown), alpha=0.05)

    def pct(a: int, b: int) -> str:
        return f"{100.0 * a / b:.1f}%" if b else "n/a"

    print(f"=== TrueWay Vision Evaluation (threshold={t:.3f}) ===")
    print(f"Sample: n_known={len(known)} n_unknown={len(unknown)}")
    print(f"top1_known(raw)       {top1_raw}/{len(known)} = {pct(top1_raw, len(known))}  (gate >=85% G03)")
    print(f"top1_known(accepted@t){top1_accepted}/{len(known)} = {pct(top1_accepted, len(known))}  (correct AND score>=t)")
    print(f"top3_known(raw)       {top3}/{len(known)} = {pct(top3, len(known))}  (gate >=95% G03)")
    print(f"false_accept@t        {fa}/{len(unknown)} = {pct(fa, len(unknown))}  (point FAR)")
    print(f"false_accept_95_upper {fa_upper*100:.2f}%  (one-sided 95% Clopper-Pearson upper bound; gate <=5.0%)")

    if len(unknown) < 59:
        print(f"  [NOTE] Sample size n={len(unknown)} < 59 mathematically cannot achieve <=5% upper bound even at 0 errors.")
        print(f"         Requires >=100 diverse hard negatives as practical benchmark target.")
    elif len(unknown) >= 100:
        gate2 = evaluate_gate2_metrics(top1_raw, top3, len(known), fa, len(unknown))
        status_label = "PASS" if gate2["passes_gate2_statistical_bound"] else "FAIL"
        print(f"\nGate 2 (G03) Statistical Verification: [{status_label}]")
        print(f"  Criteria: total_known>=150 ({len(known)}), total_negatives>=100 ({len(unknown)}),")
        print(f"            top1>=0.85 ({gate2['top1_accuracy']:.1%}), top3>=0.95 ({gate2['top3_recall']:.1%}),")
        print(f"            far_cp95_upper<=0.05 ({gate2['far_clopper_pearson_95_upper']:.2%})")

    print(f"\ncoverage              {accepted_known}/{len(known)} = {pct(accepted_known, len(known))}")
    print(f"abstention_known      {(len(known) - accepted_known)}/{len(known)} = "
          f"{pct(len(known) - accepted_known, len(known))}")

    # Confusion list: worst accepted errors first
    errors = [r for r in known
              if r["place_id"] != r["correct_place_id"] and float(r["score"]) >= t]
    errors.sort(key=lambda r: float(r["score"]), reverse=True)
    print(f"\naccepted-errors: {len(errors)} (worst first)")
    for r in errors[:10]:
        print(f"  {r['query_id']}: predicted={r['place_id']} "
              f"truth={r['correct_place_id']} score={r['score']} margin={r.get('margin', '?')}")

    # Calibration sweep on the calib split
    calib = [r for r in rows if r.get("split") == "calib"]
    if calib:
        ck = [r for r in calib if r.get("query_kind") == "known"]
        cu = [r for r in calib if r.get("query_kind") == "unknown"]
        print("\ncalibration sweep (accept iff score >= thr):")
        for thr in [round(x * 0.05, 2) for x in range(8, 20)]:
            cov = sum(1 for r in ck if float(r["score"]) >= thr) / max(len(ck), 1)
            far = sum(1 for r in cu if float(r["score"]) >= thr) / max(len(cu), 1)
            print(f"  thr={thr:.2f} coverage={cov:.2f} false_accept={far:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
