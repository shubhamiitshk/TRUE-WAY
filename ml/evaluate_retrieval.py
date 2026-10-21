"""Workstation retrieval evaluator & Gate 2 (G03) verifier — blueprint §7.6 / §18.2.

Stdlib only. Evaluates an open-set retrieval benchmark CSV and:

  * computes the FULL §7.6 metric set (Top-1, Top-3, accepted-set precision,
    coverage, abstention split known/unknown, hard-negative FAR with an exact
    one-sided Clopper-Pearson 95% upper bound, per-class error, worst-site
    confusion);
  * computes the FAR bound at the **EFFECTIVE** sample size — the number of
    distinct *source photographs* behind the rows, not the number of rows.
    Rows that are synthetic derivatives of one photograph are NOT independent
    trials (ml/README.md §Protocol: "Split by photographer/visit/viewpoint,
    never by near-duplicate shuffle");
  * FAILS on cross-split source-photo sharing (near-duplicate leakage) and on
    cross-place duplicate rows (label conflicts);
  * uses the PACK's LEARNED calibration when one is supplied — the same
    thresholds the device runs — instead of a hand-written constant;
  * can compare the result against a recorded BASELINE so CI blocks on a
    REGRESSION even while the absolute release gate is still outstanding;
  * **exits non-zero when the gate fails**, so CI can actually block.

CSV contract
------------
Required columns:
    query_id, query_kind[known|unknown], place_id, correct_place_id, score, split
Optional columns:
    margin, top3_hit, source_photo_id, rel_score, neg_score

`score` is the visual similarity of the predicted place. When `rel_score` is
present it is the GATE score: the relative score
(winner - max(second-best place, best hard negative)) is far more stable than
an absolute cosine across encoder / quantisation / gallery-size changes
(Miller et al., ECCV 2024, arXiv:2403.16528).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------------------
# calibration
# --------------------------------------------------------------------------------------


class GateCalibration:
    """The learned decision calibration. Mirrors the device."""

    def __init__(
        self,
        accept_threshold: float = 0.72,
        relative_threshold: float = 0.12,
        hard_negative_margin: float = 0.06,
        sibling_margin: float = 0.04,
        min_margin: float = 0.05,
        top_k_mean: int = 2,
        related_margin: float = 0.0,
        parents: Optional[dict] = None,
        source: str = "default",
    ) -> None:
        self.accept_threshold = accept_threshold
        self.relative_threshold = relative_threshold
        self.hard_negative_margin = hard_negative_margin
        self.sibling_margin = sibling_margin
        self.min_margin = min_margin
        self.top_k_mean = top_k_mean
        self.related_margin = related_margin
        self.parents = parents or {}
        self.source = source

    @staticmethod
    def load(path: Optional[str]) -> "GateCalibration":
        if not path:
            return GateCalibration()
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        block = raw.get("vision", {}).get("calibration") if "vision" in raw else raw.get("calibration", raw)
        if not isinstance(block, dict) or not block:
            return GateCalibration()
        def num(key: str, default: float) -> float:
            v = block.get(key, default)
            try:
                return float(v)
            except (TypeError, ValueError):
                return default
        return GateCalibration(
            accept_threshold=num("accept_threshold", 0.72),
            relative_threshold=num("relative_threshold", 0.12),
            hard_negative_margin=num("hard_negative_margin", 0.06),
            sibling_margin=num("sibling_margin", 0.04),
            min_margin=num("min_margin", 0.05),
            top_k_mean=int(block.get("top_k_mean", 2)),
            related_margin=num("related_margin", 0.0),
            parents=block.get("parents") or {},
            source=str(block.get("source", "pack")),
        )

    def describe(self) -> str:
        return (f"accept>={self.accept_threshold:.4f} relative>={self.relative_threshold:.4f} "
                f"hardneg>={self.hard_negative_margin:.4f} sibling>={self.sibling_margin:.4f} "
                f"(source={self.source})")


# --------------------------------------------------------------------------------------
# statistical helpers
# --------------------------------------------------------------------------------------


def clopper_pearson_upper_bound(k_errors: int, n_trials: int, alpha: float = 0.05) -> float:
    """Exact one-sided (1 - alpha) Clopper-Pearson upper bound on a rate."""
    if n_trials <= 0:
        return 1.0
    if k_errors >= n_trials:
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


# --------------------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------------------

REQUIRED_COLUMNS = ("query_id", "query_kind", "place_id", "correct_place_id", "score", "split")


def load(rows_path: Path) -> List[dict]:
    with rows_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(
                f"benchmark CSV is missing required column(s): {', '.join(missing)} "
                f"(found: {', '.join(reader.fieldnames or [])})"
            )
        return list(reader)


def source_key(row: dict) -> str:
    """Grouping unit for independence.

    The unit is the SOURCE SUBJECT SERIES, not the individual photograph:
    several photographs of the same monument from the same visit are
    near-duplicates of each other, so counting them as independent trials
    overstates the evidence. The photograph id is used as a fallback.
    """
    sid = (row.get("source_subject_id") or "").strip()
    if sid:
        return sid
    sid = (row.get("source_photo_id") or "").strip()
    if sid:
        return sid
    return f"{row.get('photographer', '')}|{row.get('visit', '')}"


def _num(row: dict, key: str) -> Optional[float]:
    v = row.get(key)
    if v is None or str(v).strip() == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def is_accepted(row: dict, cal: GateCalibration) -> bool:
    """Reproduces the shipped decision rule (BinaryVectorIndex.evaluate).

    Two margins:
      open_margin  = place score - best hard negative  ("is it one of ours?")
      place_margin = place score - runner-up place    ("which one of ours?")
    """
    visual = float(row["score"])
    neg = _num(row, "neg_score")
    rel = _num(row, "rel_score")
    open_margin = rel if rel is not None else (visual - neg if neg is not None else visual)
    if visual < cal.accept_threshold:
        return False
    # `hard_negative_margin` is the legacy name of the open-set gate. A legacy
    # pack shipped a POSITIVE margin there; a newly fitted calibration sets it
    # to 0 meaning "not used". Treat 0 as absent so a fitted threshold of
    # e.g. -0.44 is not silently tightened to 0.0.
    open_gate = (max(cal.relative_threshold, cal.hard_negative_margin)
                 if cal.hard_negative_margin > 0 else cal.relative_threshold)
    if open_margin < open_gate:
        return False
    margin = _num(row, "margin")
    if margin is not None and margin < cal.sibling_margin:
        return False
    # A parent site and its child (or two siblings) that look alike must be
    # reported as a PAIR, not forced onto one of them (blueprint §7.2).
    if margin is not None and cal.related_margin > 0 and margin < cal.related_margin:
        runner = (row.get("runner_up_place_id") or "").strip()
        if runner and _related(row.get("place_id", ""), runner, cal.parents):
            return False
    return True


def _related(place_a: str, place_b: str, parents: dict) -> bool:
    pa = parents.get(place_a) or None
    pb = parents.get(place_b) or None
    if pa and pa == pb:
        return True
    if pa == place_b or pb == place_a:
        return True
    return False


# --------------------------------------------------------------------------------------
# leakage / integrity checks
# --------------------------------------------------------------------------------------


def check_source_disjointness(rows: Sequence[dict]) -> List[str]:
    """Returns a list of leakage problems. Empty list == clean."""
    problems: List[str] = []
    by_source: Dict[str, set] = defaultdict(set)
    for r in rows:
        by_source[source_key(r)].add(r.get("split", ""))
    shared = {s: sorted(v) for s, v in by_source.items() if len(v) > 1}
    if shared:
        problems.append(
            f"{len(shared)} source photograph(s) appear in MORE THAN ONE split "
            f"(near-duplicate leakage). Examples: {list(shared.items())[:5]}"
        )

    by_place_source: Dict[str, set] = defaultdict(set)
    for r in rows:
        if r.get("query_kind") == "known":
            by_place_source[source_key(r)].add(r.get("correct_place_id", ""))
    conflicts = {s: sorted(p) for s, p in by_place_source.items() if len(p) > 1}
    if conflicts:
        problems.append(
            f"{len(conflicts)} source photograph(s) carry MORE THAN ONE place label "
            f"(label conflict). Examples: {list(conflicts.items())[:5]}"
        )
    return problems


def effective_sample_size(rows: Sequence[dict], kind: str) -> int:
    """Number of INDEPENDENT trials behind `rows` of the given kind."""
    return len({source_key(r) for r in rows if r.get("query_kind") == kind})


# --------------------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------------------


def compute_metrics(known: Sequence[dict], unknown: Sequence[dict], cal: GateCalibration) -> dict:
    n_known, n_unknown = len(known), len(unknown)

    top1 = sum(1 for r in known if r["place_id"] == r.get("correct_place_id"))
    top3 = 0
    for r in known:
        hit = r.get("top3_hit")
        if hit not in (None, ""):
            top3 += 1 if hit == "1" else 0
        else:
            top3 += 1 if r["place_id"] == r.get("correct_place_id") else 0

    accepted_known = [r for r in known if is_accepted(r, cal)]
    accepted_correct = sum(1 for r in accepted_known if r["place_id"] == r.get("correct_place_id"))
    coverage = len(accepted_known) / max(1, n_known)
    abstention_known = (n_known - len(accepted_known)) / max(1, n_known)

    false_accepts = sum(1 for r in unknown if is_accepted(r, cal))
    abstention_unknown = (n_unknown - false_accepts) / max(1, n_unknown)

    n_eff_unknown = effective_sample_size(unknown, "unknown") or n_unknown
    n_eff_known = effective_sample_size(known, "known") or n_known
    # The false-accept bound is over INDEPENDENT trials: distinct source
    # PHOTOGRAPHS, not rows. Six augmented rows derived from one photograph are
    # ONE failed trial; counting them as six would inflate the numerator and
    # understate the bound.
    failing_photos = {source_key(r) for r in unknown if is_accepted(r, cal)}
    false_accept_photos = len(failing_photos)

    per_class: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "correct": 0, "accepted": 0})
    for r in known:
        c = r.get("correct_place_id") or "?"
        per_class[c]["total"] += 1
        if r["place_id"] == c:
            per_class[c]["correct"] += 1
        if is_accepted(r, cal):
            per_class[c]["accepted"] += 1

    confusion: Counter = Counter()
    for r in known:
        if r["place_id"] != r.get("correct_place_id"):
            confusion[f"{r.get('correct_place_id')} -> {r['place_id']}"] += 1

    accepted_precision = accepted_correct / len(accepted_known) if accepted_known else 0.0

    return {
        "calibration": {
            "accept_threshold": cal.accept_threshold,
            "relative_threshold": cal.relative_threshold,
            "hard_negative_margin": cal.hard_negative_margin,
            "sibling_margin": cal.sibling_margin,
            "source": cal.source,
        },
        "total_known": n_known,
        "total_unknown": n_unknown,
        "effective_n_known": n_eff_known,
        "effective_n_unknown": n_eff_unknown,
        "top1_hits": top1,
        "top3_hits": top3,
        "top1_accuracy": round(top1 / max(1, n_known), 4),
        "top3_recall": round(top3 / max(1, n_known), 4),
        "coverage": round(coverage, 4),
        "abstention_known": round(abstention_known, 4),
        "abstention_unknown": round(abstention_unknown, 4),
        "accepted_count": len(accepted_known),
        "accepted_correct": accepted_correct,
        "accepted_set_precision": round(accepted_precision, 4),
        "false_accepts": false_accepts,
        "false_accept_photographs": false_accept_photos,
        "far_point": round(false_accepts / max(1, n_unknown), 4),
        "far_photo_point": round(false_accept_photos / max(1, n_eff_unknown), 4),
        "far_clopper_pearson_95_upper": round(clopper_pearson_upper_bound(false_accepts, n_unknown), 4),
        "far_cp95_upper_at_effective_n": round(clopper_pearson_upper_bound(false_accept_photos, n_eff_unknown), 4),
        "per_class": {k: dict(v) for k, v in sorted(per_class.items())},
        "worst_class_confusions": confusion.most_common(10),
    }


def evaluate_gate2(metrics: dict, min_known: int, min_unknown: int, min_top1: float,
                   min_top3: float, max_far_cp95: float) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    if metrics["total_known"] < min_known:
        reasons.append(f"known queries {metrics['total_known']} < {min_known}")
    if metrics["total_unknown"] < min_unknown:
        reasons.append(f"negatives {metrics['total_unknown']} < {min_unknown}")
    if metrics["top1_accuracy"] < min_top1:
        reasons.append(f"top1 {metrics['top1_accuracy']:.1%} < {min_top1:.0%}")
    if metrics["top3_recall"] < min_top3:
        reasons.append(f"top3 {metrics['top3_recall']:.1%} < {min_top3:.0%}")
    if metrics["far_cp95_upper_at_effective_n"] > max_far_cp95:
        reasons.append(
            f"far CP95 at effective N={metrics['effective_n_unknown']} "
            f"{metrics['far_cp95_upper_at_effective_n']:.2%} > {max_far_cp95:.1%}"
        )
    return (not reasons), reasons


def compare_to_baseline(metrics: dict, baseline: dict) -> Tuple[bool, List[str]]:
    """Regression check: CI blocks when a metric gets WORSE than the recorded
    baseline, even while the absolute release gate is still outstanding."""
    reasons: List[str] = []
    def num(d: dict, key: str) -> Optional[float]:
        v = d.get(key)
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
    for key, direction in (("top1_accuracy", "up"), ("top3_recall", "up"),
                           ("accepted_set_precision", "up"), ("coverage", "up")):
        cur, base = num(metrics, key), num(baseline, key)
        if cur is None or base is None:
            continue
        if direction == "up" and cur < base - 1e-9:
            reasons.append(f"{key} regressed: {cur:.4f} < baseline {base:.4f}")
    for key in ("far_cp95_upper_at_effective_n", "abstention_known"):
        cur, base = num(metrics, key), num(baseline, key)
        if cur is None or base is None:
            continue
        if cur > base + 1e-9:
            reasons.append(f"{key} regressed: {cur:.4f} > baseline {base:.4f}")
    return (not reasons), reasons


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="TrueWay Vision benchmark evaluator / Gate 2 verifier")
    ap.add_argument("--input", required=True, help="CSV similarity rows (see ml/fixtures/).")
    ap.add_argument("--calibration", help="Pack calibration JSON (manifest.cjson or a bare "
                                          "calibration block). Uses the LEARNED thresholds.")
    ap.add_argument("--threshold", type=float, default=None,
                    help="Override the relative accept threshold (default: the pack's).")
    ap.add_argument("--baseline", help="Recorded baseline JSON; CI fails on a regression.")
    ap.add_argument("--min-known", type=int, default=150)
    ap.add_argument("--min-unknown", type=int, default=100)
    ap.add_argument("--min-top1", type=float, default=0.85)
    ap.add_argument("--min-top3", type=float, default=0.95)
    ap.add_argument("--max-far-cp95", type=float, default=0.05)
    ap.add_argument("--json-out", help="Write the full metric JSON here.")
    ap.add_argument("--allow-leakage", action="store_true",
                    help="Do not fail on cross-split source-photo sharing (diagnostics only).")
    ap.add_argument("--no-gate", action="store_true",
                    help="Report only; never fail (diagnostics only).")
    ap.add_argument("--regression-only", action="store_true",
                    help="Fail ONLY on a regression against the recorded baseline. The absolute "
                         "release gate is reported but does not block, because it is an "
                         "acknowledged collection debt with a tracked owner.")
    args = ap.parse_args()

    try:
        rows = load(Path(args.input))
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2

    if not rows:
        print("benchmark CSV is empty", file=sys.stderr)
        return 2

    cal = GateCalibration.load(args.calibration)
    if args.threshold is not None:
        cal.relative_threshold = args.threshold

    # ---------------------------------------------------------------- leakage gate
    leakage = check_source_disjointness(rows)
    if leakage:
        print("\n=== LEAKAGE / INTEGRITY CHECK: FAIL ===")
        for p in leakage:
            print("  ! " + p)
        if not args.allow_leakage:
            print("\n  The benchmark is not a valid open-set evaluation. "
                  "Rows derived from the same source photograph are NOT independent trials.")
            return 1
        print("  (--allow-leakage set: continuing for diagnostics only)")
    else:
        print("=== LEAKAGE / INTEGRITY CHECK: PASS ===")
        print("  no source photograph spans more than one split; no cross-place label conflicts")

    test = [r for r in rows if r.get("split", "test") == "test"]
    known = [r for r in test if r.get("query_kind") == "known"]
    unknown = [r for r in test if r.get("query_kind") == "unknown"]
    if not known and not unknown:
        print("No test-split rows found; check the split column.", file=sys.stderr)
        return 2

    m = compute_metrics(known, unknown, cal)

    def pct(a: int, b: int) -> str:
        return f"{100.0 * a / b:.1f}%" if b else "n/a"

    print(f"\n=== TrueWay Vision Evaluation ===")
    print(f"calibration: {cal.describe()}")
    print(f"rows: known={m['total_known']} unknown={m['total_unknown']} "
          f"| EFFECTIVE (distinct source SUBJECT SERIES): known={m['effective_n_known']} "
          f"unknown={m['effective_n_unknown']}")
    print(f"top1_known(raw)       {m['top1_hits']}/{m['total_known']} = {pct(m['top1_hits'], m['total_known'])}  (gate >={args.min_top1:.0%})")
    print(f"top3_known(raw)       {m['top3_hits']}/{m['total_known']} = {pct(m['top3_hits'], m['total_known'])}  (gate >={args.min_top3:.0%})")
    print(f"coverage(accepted)    {m['accepted_count']}/{m['total_known']} = {pct(m['accepted_count'], m['total_known'])}")
    print(f"abstention_known      {m['abstention_known']:.1%}")
    print(f"abstention_unknown    {m['abstention_unknown']:.1%}")
    print(f"accepted-set precision{m['accepted_correct']}/{m['accepted_count']} = {m['accepted_set_precision']:.1%}")
    print(f"false_accept@t        {m['false_accepts']}/{m['total_unknown']} = {m['far_point']:.1%}  (point FAR over rows)")
    print(f"false_accept_series   {m['false_accept_photographs']}/{m['effective_n_unknown']} = {m['far_photo_point']:.1%}  (point FAR over INDEPENDENT subject series)")
    print(f"false_accept_95_upper {m['far_clopper_pearson_95_upper']:.2%}  (row count N={m['total_unknown']})")
    print(f"false_accept_95_upper {m['far_cp95_upper_at_effective_n']:.2%}  "
          f"(EFFECTIVE N={m['effective_n_unknown']}, {m['false_accept_photographs']} failing "
          f"PHOTOGRAPH(S) <- the one the gate uses)")

    if m["effective_n_unknown"] < m["total_unknown"]:
        print(f"  [NOTE] {m['total_unknown']} rows descend from only {m['effective_n_unknown']} independent "
              f"SUBJECT SERIES (photographs of the same monument from the same visit are "
              f"near-duplicates of each other). The row-count bound overstates the evidence.")

    passed, reasons = evaluate_gate2(m, args.min_known, args.min_unknown, args.min_top1,
                                     args.min_top3, args.max_far_cp95)
    print(f"\nGate 2 (G03) Statistical Verification: [{'PASS' if passed else 'FAIL'}]")
    print(f"  Criteria: total_known>={args.min_known} ({m['total_known']}), "
          f"total_negatives>={args.min_unknown} ({m['total_unknown']}),")
    print(f"            top1>={args.min_top1:.0%} ({m['top1_accuracy']:.1%}), "
          f"top3>={args.min_top3:.0%} ({m['top3_recall']:.1%}),")
    print(f"            far_cp95(effective N)<={args.max_far_cp95:.1%} "
          f"({m['far_cp95_upper_at_effective_n']:.2%})")
    for r in reasons:
        print(f"    - FAIL: {r}")

    print("\nper-class top-1 (worst first):")
    for c, s in sorted(m["per_class"].items(), key=lambda kv: (kv[1]["correct"] / max(1, kv[1]["total"]), kv[0])):
        print(f"  {c:45s} {s['correct']}/{s['total']} top1   accepted {s['accepted']}/{s['total']}")
    if m["worst_class_confusions"]:
        print("\nworst-site confusions:")
        for pair, n in m["worst_class_confusions"]:
            print(f"  {pair}  x{n}")

    accepted_errors = [
        r for r in known
        if r["place_id"] != r.get("correct_place_id") and is_accepted(r, cal)
    ]
    accepted_errors.sort(key=lambda r: float(r["score"]), reverse=True)
    print(f"\naccepted-errors: {len(accepted_errors)} (worst first)")
    for r in accepted_errors[:10]:
        print(f"  {r['query_id']}: predicted={r['place_id']} "
              f"truth={r.get('correct_place_id')} score={r['score']}")

    # ---------------------------------------------------------------- regression gate
    regressed = False
    if args.baseline:
        base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        ok, b_reasons = compare_to_baseline(m, base.get("metrics", base))
        print(f"\n=== BASELINE REGRESSION CHECK: [{'PASS' if ok else 'FAIL'}] ===")
        for r in b_reasons:
            print(f"  ! {r}")
        regressed = not ok

    if args.json_out:
        payload = dict(m)
        payload["gate_passed"] = passed
        payload["gate_failures"] = reasons
        payload["leakage_problems"] = leakage
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\n-> wrote {args.json_out}")

    if args.no_gate:
        return 0
    if regressed:
        print("\nREGRESSION AGAINST THE RECORDED BASELINE — exiting non-zero so CI blocks.",
              file=sys.stderr)
        return 1
    if args.regression_only:
        print("\nNo regression. (The absolute Gate 2 verdict above is reported but does not "
              "block in --regression-only mode: it is a tracked collection debt.)")
        return 0
    if not passed:
        print("\nGATE 2 FAILED — exiting non-zero so CI blocks.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
