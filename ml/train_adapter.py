"""Linear adaptation prototype — research doc §2 finding 2 / §5 phase 4b.

Procedure (ILIAS-backed): FREEZE the encoder, learn a cheap LINEAR layer on
pilot embeddings, export the weights into the pack. Full-matrix version
(d×d, ArcFace) trains on workstation with torch; this stdlib-only script
implements the diagonal form (per-dimension weights, Rocchio-flavoured
margin perceptron) so the *protocol* — photographer-grouped splits,
calib-learned / test-measured, FA-gated — is executable today.

Input contract (embeddings CSV, one row per query photo):
  query_id,query_kind[known|unknown],place_id,correct_place_id,split,photographer,visit,v0..vN
  place_id         = top-1 predicted place under the FROZEN encoder
  correct_place_id = ground truth (empty for unknown)
  v0..vN           = L2-normalized query embedding (reference centroids are
                     computed from known rows per split — see --refs)
  --refs CSV: place_id,v0..vN  reference centroid per place (adapted space
                     is learned jointly; centroids recomputed after weighting)

Usage:
  python ml/train_adapter.py --queries ml/fixtures/embeddings_demo.csv \
      --refs ml/fixtures/refcentroids_demo.csv
  python ml/train_adapter.py --selftest   # plumbing check on SYNTHETIC data only

Output: prints frozen vs adapted top-1 / false-accept on the TEST split and
writes weights JSON (place centroids in adapted space + dim weights) for the
pack builder. Calib split is used for learning; test split is never touched
during training (§7.6 split discipline).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from pathlib import Path


def l2(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def dot(a: list[float], b: list[float], w: list[float]) -> float:
    return sum((ai * bi) * wi for ai, bi, wi in zip(a, b, w))


def wcosine(a: list[float], b: list[float], w: list[float]) -> float:
    """Weighted cosine = cosine in the sqrt(w)-scaled space. Bounded to
    [-1,1] so scores share the SAME scale as evaluate_retrieval.py's cosine
    sweep — the diagonal weights must not silently rescale the operating point.
    """
    num = sum(wi * ai * bi for ai, bi, wi in zip(a, b, w))
    na = math.sqrt(sum(wi * ai * ai for ai, wi in zip(a, w)))
    nb = math.sqrt(sum(wi * bi * bi for bi, wi in zip(b, w)))
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return num / (na * nb)


def load_queries(p: Path):
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    dims = [c for c in rows[0].keys() if c.startswith("v")]
    out = []
    for r in rows:
        out.append({
            "id": r["query_id"], "kind": r["query_kind"],
            "pred": r["place_id"], "truth": r.get("correct_place_id", ""),
            "split": r.get("split", "test"), "photog": r.get("photographer", "?"),
            "vec": l2([float(r[c]) for c in dims]),
        })
    return out, len(dims)


def load_refs(p: Path):
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    dims = [c for c in rows[0].keys() if c.startswith("v")]
    return {r["place_id"]: l2([float(r[c]) for c in dims]) for r in rows}, len(dims)


def predict(vec, refs, w):
    best, best_s = None, -1e18
    for pid, c in refs.items():
        s = wcosine(vec, c, w)  # bounded cosine scale, not an unbounded dot
        if s > best_s:
            best, best_s = pid, s
    return best, best_s


def evaluate(queries, refs, w, split="test", accept=0.5):
    known = [q for q in queries if q["split"] == split and q["kind"] == "known"]
    unknown = [q for q in queries if q["split"] == split and q["kind"] == "unknown"]
    top1 = sum(1 for q in known if predict(q["vec"], refs, w)[0] == q["truth"])
    # False accept: an UNKNOWN query whose best adapted score clears `accept`.
    # Indicative at this threshold; the binding gate is the calib sweep in
    # evaluate_retrieval.py. Scores are cosine-scale (wcosine) so `accept` means
    # the same thing here as there.
    fa = sum(1 for q in unknown if predict(q["vec"], refs, w)[1] >= accept)
    return known, unknown, top1, fa


def train(queries, refs, dim, iters=50, lr=0.5, margin=0.05):
    """Margin perceptron on diagonal weights, calib split only."""
    w = [1.0] * dim
    calib = [q for q in queries if q["split"] == "calib" and q["kind"] == "known"]
    # Group by photographer: never learn visit-specific quirks silently —
    # iterate groups round-robin so no single shoot dominates.
    groups: dict[str, list] = {}
    for q in calib:
        groups.setdefault(q["photog"], []).append(q)
    order = list(groups)
    for _ in range(iters):
        for g in order:
            for q in groups[g]:
                if q["truth"] not in refs:
                    continue
                s_true = wcosine(q["vec"], refs[q["truth"]], w)
                # hardest negative place
                neg, s_neg = None, -1e18
                for pid, c in refs.items():
                    if pid == q["truth"]:
                        continue
                    s = wcosine(q["vec"], c, w)
                    if s > s_neg:
                        neg, s_neg = pid, s
                if s_true < s_neg + margin:
                    for i in range(dim):
                        v, ct, cn = q["vec"][i], refs[q["truth"]][i], refs[neg][i]
                        w[i] = max(0.05, w[i] + lr * (v * ct - v * cn))
    # Diagonal weights define a sqrt(w)-scaled space; scoring uses wcosine()
    # so adapted scores stay on the cosine scale the calibrator expects.
    return w


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", default=None)
    ap.add_argument("--refs", default=None)
    ap.add_argument("--out", default="ml/adapter_weights.json")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--iters", type=int, default=50)
    args = ap.parse_args()

    if args.selftest:
        random.seed(7)
        dim = 16
        refs = {"place-a": l2([1.0] * 8 + [0.0] * 8),
                "place-b": l2([0.0] * 8 + [1.0] * 8)}
        queries = []
        for i in range(40):
            truth = "place-a" if i % 2 == 0 else "place-b"
            base = refs[truth]
            vec = l2([x + random.gauss(0, 0.6) for x in base])
            queries.append({"id": f"q{i}", "kind": "known", "pred": "",
                            "truth": truth, "split": "calib" if i < 20 else "test",
                            "photog": f"p{i % 3}", "vec": vec})
        w0 = [1.0] * dim
        _, _, t0, _ = evaluate(queries, refs, w0)
        w = train(queries, refs, dim, iters=args.iters)
        known, _, t1, _ = evaluate(queries, refs, w)
        print(f"[SELFTEST synthetic plumbing only] frozen top1={t0}/{len(known)} "
              f"adapted top1={t1}/{len(known)} dim={dim}")
        return 0

    if not args.queries or not args.refs:
        print("need --queries and --refs (or --selftest)", file=sys.stderr)
        return 2
    queries, dq = load_queries(Path(args.queries))
    refs, dr = load_refs(Path(args.refs))
    assert dq == dr, f"dim mismatch queries={dq} refs={dr}"
    known, unknown, t0, fa0 = evaluate(queries, refs, [1.0] * dq)
    w = train(queries, refs, dq, iters=args.iters)
    _, _, t1, fa1 = evaluate(queries, refs, w)
    print(f"frozen top1(test)  = {t0}/{len(known)}  false_accept@0.5 = {fa0}/{len(unknown)}")
    print(f"adapted top1(test) = {t1}/{len(known)}  false_accept@0.5 = {fa1}/{len(unknown)}  "
          f"(calib-learned, photographer-grouped)")
    print(f"(binding FA gate is the calib sweep in evaluate_retrieval.py)")
    Path(args.out).write_text(json.dumps(
        {"model_id": "mobileclip-s0+diag-adapter", "dim": dq, "weights": w,
         "refs": refs,
         "note": "diagonal adaptation; full-matrix ArcFace version trains with torch on workstation"},
        indent=1), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
