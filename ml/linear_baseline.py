"""The mandatory baseline comparison.

arXiv:2609.04381 (2026) audited class prototypes on frozen foundation
features and found that REAL prototypes beat EXACTLY PERMUTED ones by at most
~1 point after fusion, and that a MATCHED logistic regression on the same
labelled support set matched or beat the fused prototype system (within 0.5 pt
on T-LESS, exceeding it on HOPE and on self-collected parts).

Applied here: a 512x512 adapter + Sub-Center-ArcFace on a small corpus is
very likely over-parameterised. Until the adapter is shown to beat a plain
baseline on the SAME held-out split, it is an unearned complication.

Three baselines are evaluated, all on the same test split and with the same
decision rule:

  centroid_raw        class mean of the FROZEN encoder features (no adapter)
  centroid_adapted    class mean of the ADAPTED features (what the old
                      single-vector index effectively shipped)
  logistic            multinomial logistic regression on the frozen features

`ml/train_arcface_pipeline.py` writes the result to
`ml/fixtures/linear_baseline_report.json`.
"""
from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

import numpy as np


def _l2(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-8)


def _cp_upper(k: int, n: int, alpha: float = 0.05) -> float:
    if n <= 0:
        return 1.0
    if k >= n:
        return 1.0
    if k == 0:
        return 1.0 - alpha ** (1.0 / n)

    def cdf(p: float) -> float:
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))

    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _centroids(features: np.ndarray, labels: np.ndarray, n_classes: int) -> np.ndarray:
    out = np.zeros((n_classes, features.shape[1]), dtype=np.float32)
    for c in range(n_classes):
        m = labels == c
        if m.any():
            out[c] = features[m].mean(axis=0)
    return _l2(out)


def _evaluate(
    centroids: np.ndarray,
    neg_vecs: np.ndarray,
    known_feats: np.ndarray,
    known_truth: np.ndarray,
    known_sources: Sequence[str],
    unknown_feats: np.ndarray,
    unknown_sources: Sequence[str],
    rel_threshold: float,
    abs_threshold: float,
    hard_margin: float,
    n_classes: int,
) -> Dict[str, object]:
    negs = _l2(neg_vecs) if neg_vecs.size else np.zeros((0, centroids.shape[1]), np.float32)
    q = _l2(known_feats)
    sims = q @ centroids.T
    order = np.argsort(-sims, axis=1)
    top1 = int((order[:, 0] == known_truth).sum())
    top3 = int(sum(1 for i in range(q.shape[0]) if known_truth[i] in order[i, :3]))
    rel: List[float] = []
    second: List[float] = []
    for i in range(q.shape[0]):
        s1 = float(sims[i, order[i, 0]])
        s2 = float(sims[i, order[i, 1]]) if n_classes > 1 else -1.0
        sn = float(np.max(negs @ q[i])) if negs.size else -1.0
        second.append(s2)
        rel.append(s1 - max(s2, sn))
    accepted = [i for i in range(q.shape[0])
                if rel[i] >= rel_threshold and sims[i, order[i, 0]] >= abs_threshold]
    fa = 0
    if negs.size:
        qu = _l2(unknown_feats)
        su = qu @ centroids.T
        for i in range(qu.shape[0]):
            o = np.argsort(-su[i])
            s1 = float(su[i, o[0]])
            s2 = float(su[i, o[1]]) if n_classes > 1 else -1.0
            sn = float(np.max(negs @ qu[i]))
            if (s1 - sn) >= hard_margin and (s1 - max(s2, sn)) >= rel_threshold and s1 >= abs_threshold:
                fa += 1
    eff_n = len(set(unknown_sources)) or len(unknown_sources)
    return {
        "top1": top1, "top1_total": len(known_truth),
        "top3": top3,
        "coverage": len(accepted), "coverage_total": len(known_truth),
        "false_accepts": fa, "false_accepts_total": len(unknown_sources),
        "far_cp95_effective_n": round(_cp_upper(fa, eff_n), 6),
        "effective_n_unknown": eff_n,
        "effective_n_known": len(set(known_sources)),
    }


def _logistic_fit(
    x: np.ndarray, y: np.ndarray, n_classes: int, epochs: int = 400, lr: float = 0.5
) -> Tuple[np.ndarray, np.ndarray]:
    """Multinomial logistic regression (softmax) by gradient descent."""
    dim = x.shape[1]
    w = np.zeros((n_classes, dim), dtype=np.float64)
    b = np.zeros(n_classes, dtype=np.float64)
    for _ in range(epochs):
        z = x @ w.T + b
        z -= z.max(axis=1, keepdims=True)
        e = np.exp(z)
        p = e / e.sum(axis=1, keepdims=True)
        onehot = np.zeros_like(p)
        onehot[np.arange(len(y)), y] = 1.0
        g = (p - onehot) / max(1, len(y))
        w -= lr * (g.T @ x)
        b -= lr * g.sum(axis=0)
    return w, b


def run_baselines(
    raw_pos: np.ndarray,
    adapted_pos: np.ndarray,
    raw_neg: np.ndarray,
    adapted_neg: np.ndarray,
    pos_meta: Sequence[Tuple[str, str, int]],
    neg_meta: Sequence[Tuple[str, str, int]],
    n_classes: int,
    n_neg_classes: int,
    rel_threshold: float,
    abs_threshold: float,
    hard_margin: float,
) -> Dict[str, object]:
    """Evaluates the baselines on the test split. Returns a JSON-ready report."""
    known_idx = [i for i, m in enumerate(pos_meta) if m[0] == "test"]
    neg_idx = [i for i, m in enumerate(neg_meta) if m[0] == "test"]
    train_idx = [i for i, m in enumerate(pos_meta) if m[0] in ("ref", "calib")]
    neg_train_idx = [i for i, m in enumerate(neg_meta) if m[0] in ("ref", "calib")]

    known_truth = np.array([pos_meta[i][2] for i in known_idx], dtype=np.int64)
    known_sources = [pos_meta[i][1] for i in known_idx]
    unknown_sources = [neg_meta[i][1] for i in neg_idx]

    report: Dict[str, object] = {
        "note": ("Baselines evaluated on the SAME held-out test split with the SAME "
                 "relative-score decision rule. See arXiv:2609.04381."),
        "thresholds": {
            "relative_threshold": rel_threshold,
            "accept_threshold": abs_threshold,
            "hard_negative_margin": hard_margin,
        },
    }

    for name, pos_feats, neg_feats in (
        ("centroid_raw", raw_pos, raw_neg),
        ("centroid_adapted", adapted_pos, adapted_neg),
    ):
        cents = _centroids(pos_feats[train_idx],
                           np.array([pos_meta[i][2] for i in train_idx], dtype=np.int64),
                           n_classes)
        negs = neg_feats[neg_train_idx]
        # The UNKNOWN features come from the NEGATIVE feature array. This
        # used to read `pos_feats[neg_idx]` - the positive array indexed with
        # the negative split's indices. It did not raise while the negative
        # split was smaller than the positive one; it silently scored the
        # false-accept rate against the WRONG photographs, and it started
        # raising as soon as the corpus grew.
        report[name] = _evaluate(cents, negs, pos_feats[known_idx], known_truth, known_sources,
                                 neg_feats[neg_idx], unknown_sources,
                                 rel_threshold, abs_threshold, hard_margin, n_classes)

    # ---- multinomial logistic regression on the frozen features ---------------------
    xtr = _l2(raw_pos[train_idx].astype(np.float64))
    ytr = np.array([pos_meta[i][2] for i in train_idx], dtype=np.int64)
    w, b = _logistic_fit(xtr, ytr, n_classes)
    q = _l2(raw_pos[known_idx].astype(np.float64))
    logits = q @ w.T + b
    order = np.argsort(-logits, axis=1)
    top1 = int((order[:, 0] == known_truth).sum())
    top3 = int(sum(1 for i in range(len(known_truth)) if known_truth[i] in order[i, :3]))
    qu = _l2(raw_neg[neg_idx].astype(np.float64))
    lu = qu @ w.T + b
    o = np.argsort(-lu, axis=1)
    # relative score for the logistic head = margin between the top-1 and top-2 logits
    rel_u = lu[np.arange(len(lu)), o[:, 0]] - lu[np.arange(len(lu)), o[:, 1]] if n_classes > 1 else lu[:, 0]
    fa = int((rel_u >= rel_threshold).sum())
    eff_n = len(set(unknown_sources)) or len(unknown_sources)
    report["logistic"] = {
        "top1": top1, "top1_total": len(known_truth),
        "top3": top3,
        "coverage": 0, "coverage_total": len(known_truth),
        "false_accepts": fa, "false_accepts_total": len(unknown_sources),
        "far_cp95_effective_n": round(_cp_upper(fa, eff_n), 6),
        "effective_n_unknown": eff_n,
        "effective_n_known": len(set(known_sources)),
        "note": "logit margin threshold is on a different scale than the cosine relative score; "
                "the FAR figure is indicative only",
    }
    return report
