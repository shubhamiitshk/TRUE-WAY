"""The TrueWay vision decision rule — the single source of truth.

This module implements EXACTLY the rule that
`android/app/src/main/java/com/trueway/app/vision/BinaryVectorIndex.kt`
implements on the device, so the workstation evaluation and the shipped
scanner cannot drift apart.

Decision rule (all thresholds LEARNED on the held-out calibration split):

    place_score(p)  = mean of the top-k similarities between the query and
                      p's reference vectors            (robust top-k mean, NOT a MAX)
    best_negative   = max similarity to any negative-bank vector
    open_margin     = place_score(winner) - best_negative
    place_margin    = place_score(winner) - place_score(runner-up place)

    ACCEPT  iff  place_score(winner) >= accept_threshold
           and  open_margin        >= relative_threshold
           and  place_margin       >= sibling_margin

    Otherwise ABSTAIN, with the first failing gate named.

Two SEPARATE margins, because they answer two different questions:

  * `open_margin` — "is this one of our places, or an unknown?" It compares the
    winner against the strongest NON-MATCHING exemplar (the hard-negative
    bank). This is the open-set gate, and it is the one that must be
    calibrated against the false-accept rate.
  * `place_margin` — "which of our places?" It compares the winner against the
    runner-up PLACE. This is the disambiguation gate: when two sibling
    structures look alike, the result is reported as an ambiguous pair rather
    than a forced identity.

They must NOT be merged into one `max(place, negative)` margin. Measured on the
verified corpus, the runner-up PLACE is a *different true class*, so folding
it into the open-set margin makes the gate penalise legitimate fine-grained
confusions: on the test split the positives' place margins run down to 0.004
while the negatives' run UP to 0.379, so a combined margin is anti-correlated
with the truth. The open margin, by contrast, separates cleanly
(positives >= +0.17 at the 10th percentile, negatives <= -0.05).

Why relative and not absolute: an absolute cosine moves with the encoder, the
quantisation, the input resolution and the number of prototypes. A relative
score does not (Miller et al., ECCV 2024, arXiv:2403.16528).

Why top-k mean and not MAX: a MAX over M references is a multiple-comparisons
statistic whose null distribution grows with M, which silently makes the
threshold depend on M (blueprint §7.5 asks for a "robust top-2 mean").
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Set

import numpy as np

# --------------------------------------------------------------------------------------
# calibration
# --------------------------------------------------------------------------------------


@dataclass
class Calibration:
    """Learned decision calibration. Every field comes from the calibration split."""

    accept_threshold: float
    relative_threshold: float
    hard_negative_margin: float
    sibling_margin: float
    min_margin: float
    top_k_mean: int = 2
    related_margin: float = 0.0
    # The CSLS neighbourhood size: the number of nearest neighbours used to
    # estimate the local density of a gallery vector. 10 is the value the
    # CSLS paper reports as insensitive.
    csls_k: int = 10
    calibrator: Optional[Dict[str, float]] = None
    source: str = "fitted"

    def to_json(self) -> Dict[str, object]:
        out: Dict[str, object] = {
            "accept_threshold": round(self.accept_threshold, 6),
            "relative_threshold": round(self.relative_threshold, 6),
            "hard_negative_margin": round(self.hard_negative_margin, 6),
            "sibling_margin": round(self.sibling_margin, 6),
            "min_margin": round(self.min_margin, 6),
            "top_k_mean": self.top_k_mean,
            "related_margin": round(self.related_margin, 6),
            "csls_k": self.csls_k,
        }
        if self.calibrator:
            out["calibrator"] = {k: round(float(v), 6) for k, v in self.calibrator.items()}
        return out

    @staticmethod
    def from_json(d: Dict[str, object]) -> "Calibration":
        return Calibration(
            accept_threshold=float(d.get("accept_threshold", 0.72)),
            relative_threshold=float(d.get("relative_threshold", 0.12)),
            hard_negative_margin=float(d.get("hard_negative_margin", 0.06)),
            sibling_margin=float(d.get("sibling_margin", 0.04)),
            min_margin=float(d.get("min_margin", 0.05)),
            top_k_mean=int(d.get("top_k_mean", 2)),
            related_margin=float(d.get("related_margin", 0.0)),
            csls_k=int(d.get("csls_k", 10)),
            calibrator=d.get("calibrator") or None,
            source=str(d.get("source", "pack")),
        )


# --------------------------------------------------------------------------------------
# index
# --------------------------------------------------------------------------------------


@dataclass
class PlacePrototypes:
    place_id: str
    parent_place_id: Optional[str]
    viewpoint_tag: str
    distinguishing_hint: str
    vectors: np.ndarray  # [n_refs, dim], each row L2-normalised
    asset_ids: List[str] = field(default_factory=list)
    # The SOURCE PHOTOGRAPH each vector derives from. Used to leave the query's
    # own photograph out when fitting the calibration — otherwise a calibration
    # query is scored against a gallery that contains itself, the fitted
    # threshold collapses, and the gate becomes far too permissive.
    source_ids: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.vectors.ndim == 1:
            self.vectors = self.vectors[None, :]


@dataclass
class Index:
    places: List[PlacePrototypes]
    negatives: np.ndarray  # [n_neg, dim], each row L2-normalised
    negative_labels: List[str]
    calibration: Calibration
    negative_source_ids: List[str] = field(default_factory=list)
    # The CSLS LOCAL SCALE of every gallery vector: r_k(v), the mean cosine of
    # v to its k nearest neighbours in the gallery. Order: the place
    # references (concatenated, in `places` order) then the negative bank.
    local_scale: List[float] = field(default_factory=list)

    def dim(self) -> int:
        return int(self.places[0].vectors.shape[1]) if self.places else 0

    def local_scale_of(self, place_index: int, vector_index: int) -> float:
        """r_k(v) for a place reference, or 0.0 when the index carries none."""
        if not self.local_scale:
            return 0.0
        off = 0
        for pi, p in enumerate(self.places):
            if pi == place_index:
                idx = off + vector_index
                return float(self.local_scale[idx]) if 0 <= idx < len(self.local_scale) else 0.0
            off += len(p.vectors)
        return 0.0

    def negative_scale_of(self, index: int) -> float:
        if not self.local_scale:
            return 0.0
        off = sum(len(p.vectors) for p in self.places)
        idx = off + index
        return float(self.local_scale[idx]) if 0 <= idx < len(self.local_scale) else 0.0


def l2_normalize(v: np.ndarray) -> np.ndarray:
    """L2-normalise EXACTLY as the device does.

    Sequential float64 accumulation of the squares, `sqrt`, then divide each
    element in float64 and round to float32 — the same order of operations as
    `BinaryVectorIndex.l2Normalize`. A numpy float32 norm uses a different
    summation order and can differ by 1 ULP, which flips a knife-edge
    decision; the cross-language parity test exists to catch exactly that.
    """
    acc = 0.0
    for x in v:
        acc += float(x) * float(x)
    n = math.sqrt(acc) if acc > 0.0 else 1.0
    if not math.isfinite(n) or n <= 0.0:
        return np.asarray(v, dtype=np.float32)
    return np.array([float(x) / n for x in v], dtype=np.float32)


# --------------------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------------------


@dataclass
class Scored:
    place_id: str
    score: float
    best_negative: float
    open_margin: float
    place_margin: float
    relative_score: float  # alias of open_margin (CSV column name)
    sibling_delta: float   # alias of place_margin (CSV column name)
    parent_place_id: Optional[str]
    distinguishing_hint: str


def _dot_f64(a, b) -> float:
    """Sequential float64 dot product.

    Matches the device EXACTLY: `BinaryVectorIndex.similarityTo` accumulates in
    double, sequentially, in index order. A numpy float32 matmul uses a
    different summation order, which flips knife-edge decisions — so the
    workstation must not use one.
    """
    acc = 0.0
    for i in range(len(a)):
        acc += float(a[i]) * float(b[i])
    return acc


def score_places(index: Index, query: np.ndarray, exclude_source: Optional[str] = None,
                 exclude_sources: Optional[Set[str]] = None) -> List[Scored]:
    """Scores every place in the index against the query, best first.

    [exclude_source] leaves out every gallery and negative vector that derives
    from the SAME source photograph as the query. The device never needs this
    (a visitor's photo is not in the gallery), but the CALIBRATION does: a
    calibration query is, by construction, a photograph the gallery was built
    from. Scoring it against itself makes its open margin artificially
    negative, which collapses the fitted threshold and leaves the shipped gate
    far too permissive.

    [exclude_sources] leaves out a whole SUBJECT SERIES - every photograph of
    the same monument from the same visit. This matters as much as excluding
    the photograph itself, and in the OPPOSITE direction: a calibration
    query's siblings are near-duplicates of it, so

      * they stay in the GALLERY, and the query scores higher against its own
        place than a photograph the gallery has never seen would; and
      * they stay in the NEGATIVE BANK, and the nearest negative looks closer
        than it will to a genuinely new negative.

    Both effects make the fitted threshold optimistic, and the optimism shows
    up as a false-accept rate on the test split that the calibration split
    never predicted. Measured on this corpus: the calibration split's hardest
    negative still had an open margin of -0.31, while the test split's hardest
    was +0.05 - a shift of more than a third of a cosine, and the whole
    difference between a 5 % and a 24 % measured false-accept rate.
    """
    q = l2_normalize(np.asarray(query, dtype=np.float32))
    q_list = [float(x) for x in q]
    # The query's own photograph is excluded from everywhere.
    # The query's whole SERIES is excluded from the NEGATIVE BANK only.
    #
    # The asymmetry is deliberate and it is the protocol:
    #  * The GALLERY keeps the query's siblings, because at inference the
    #    gallery does too - a visitor's photograph of the Mahabodhi is scored
    #    against every reference photograph of the Mahabodhi, including the
    #    ones from other visits. Removing the siblings here would make the
    #    calibration pessimistic about true matches.
    #  * The BANK drops the query's siblings, because a calibration negative
    #    IS a reference photograph of that monument and its siblings are
    #    near-identical to it. Scoring it against them measures the margin of a
    #    photograph that has a twin in the bank, not the margin of a NEW
    #    photograph of the same monument - which is what the device will
    #    ever see. That is the optimism that made the fitted threshold far
    #    too permissive: on this corpus the calibration split's hardest
    #    negative still had an open margin of -0.31 while the test split's
    #    hardest was +0.05.
    drop_bank: Set[str] = set(exclude_sources or ())
    drop_gallery: Set[str] = set()
    if exclude_source is not None:
        drop_bank.add(exclude_source)
        drop_gallery.add(exclude_source)

    # ---- CSLS: Cross-domain Similarity Local Scaling -------------------------
    #
    #   s'(q, v) = 2 s(q, v) - r_k(q) - r_k(v)
    #
    # with r_k(x) the mean cosine of x to its k nearest neighbours in the
    # gallery. It removes the HUBNESS of the embedding space: a small number of
    # gallery vectors are close to almost everything, and those vectors are
    # exactly what collapses the open margin (a lookalike that happens to be a
    # hub is scored as a confident match). Scaling them down by their local
    # density restores the separation.
    #
    # Measured on this corpus: Top-1 91.4 % -> 94.2 %, the median open margin
    # of a true match +0.335 -> +0.584, and the coverage at a 5 % false-accept
    # rate 79.9 % -> 91.4 %. Centering the embeddings (subtracting the corpus
    # mean) was measured too and made Top-1 WORSE, so it is not used.
    k = max(1, int(index.calibration.csls_k))
    use_csls = bool(index.local_scale)

    pos_sims: List[List[Tuple[int, float, float]]] = []   # (vector index, raw, scaled)
    neg_sims: List[Tuple[int, float, float]] = []
    pool_raw: List[float] = []
    for pi, p in enumerate(index.places):
        row: List[Tuple[int, float, float]] = []
        for i, v in enumerate(p.vectors):
            if i < len(p.source_ids) and p.source_ids[i] in drop_gallery:
                continue
            # The device accumulates the dot product in float64 and ROUNDS the
            # result to float32 before it compares anything. Rounding here
            # keeps the two implementations bit-identical.
            raw = float(np.float32(_dot_f64(v, q_list)))
            row.append((i, raw, 0.0))
            pool_raw.append(raw)
        pos_sims.append(row)
    for i, row in enumerate(index.negatives):
        if i < len(index.negative_source_ids) and index.negative_source_ids[i] in drop_bank:
            continue
        raw = float(np.float32(_dot_f64(row, q_list)))
        neg_sims.append((i, raw, 0.0))
        pool_raw.append(raw)

    if use_csls:
        kk = min(k, len(pool_raw))
        rq = float(sum(sorted(pool_raw, reverse=True)[:kk]) / kk) if kk > 0 else 0.0
        for pi, p in enumerate(index.places):
            for t, (i, raw, _z) in enumerate(pos_sims[pi]):
                sc = float(np.float32(2.0 * raw - rq - index.local_scale_of(pi, i)))
                pos_sims[pi][t] = (i, raw, sc)
        for t, (i, raw, _z) in enumerate(neg_sims):
            sc = float(np.float32(2.0 * raw - rq - index.negative_scale_of(i)))
            neg_sims[t] = (i, raw, sc)

    best_negative = -1.0
    for _i, _raw, sc in neg_sims:
        if sc > best_negative:
            best_negative = sc
    best_negative = float(np.float32(best_negative))

    scored: List[Scored] = []
    for pi, p in enumerate(index.places):
        sims: List[float] = [sc for (_i, _raw, sc) in pos_sims[pi]]
        if not sims:
            continue
        sims.sort(reverse=True)
        k = min(index.calibration.top_k_mean, len(sims))
        score = float(np.float32(sum(sims[:k]) / k))
        scored.append(Scored(
            place_id=p.place_id,
            score=score,
            best_negative=best_negative,
            open_margin=0.0,
            place_margin=0.0,
            relative_score=0.0,
            sibling_delta=0.0,
            parent_place_id=p.parent_place_id,
            distinguishing_hint=p.distinguishing_hint,
        ))
    scored.sort(key=lambda s: -s.score)
    for i, s in enumerate(scored):
        second = scored[i + 1].score if i + 1 < len(scored) else -1.0
        s.place_margin = s.score - second
        s.open_margin = s.score - s.best_negative
        s.sibling_delta = s.place_margin
        s.relative_score = s.open_margin
    return scored


@dataclass
class Decision:
    accepted: bool
    reason: str
    scored: List[Scored]
    top: Optional[Scored]
    runner_up: Optional[Scored]

    @property
    def place_id(self) -> Optional[str]:
        return self.top.place_id if self.top else None


def decide(index: Index, query: np.ndarray) -> Decision:
    """Applies the shipped decision rule. Mirrors BinaryVectorIndex.evaluate."""
    scored = score_places(index, query)
    if not scored:
        return Decision(False, "NO_CANDIDATES", scored, None, None)
    top = scored[0]
    runner_up = scored[1] if len(scored) > 1 else None
    cal = index.calibration

    if top.score < cal.accept_threshold:
        return Decision(False, "BELOW_ABSOLUTE_THRESHOLD", scored, top, runner_up)
    if top.open_margin < cal.relative_threshold:
        return Decision(False, "BELOW_RELATIVE_THRESHOLD", scored, top, runner_up)
    if runner_up is not None and top.place_margin < cal.sibling_margin:
        if _related(top.place_id, runner_up.place_id, index):
            return Decision(False, "AMBIGUOUS_SIBLING_PAIR", scored, top, runner_up)
        return Decision(False, "AMBIGUOUS_NON_SIBLING_MARGIN", scored, top, runner_up)
    if runner_up is not None and top.place_margin < cal.related_margin \
            and _related(top.place_id, runner_up.place_id, index):
        # A parent site and its child (or two siblings) that are visually close:
        # report the PAIR rather than forcing one of them (blueprint §7.2).
        return Decision(False, "AMBIGUOUS_SIBLING_PAIR", scored, top, runner_up)
    return Decision(True, "ACCEPTED", scored, top, runner_up)


def _related(place_a: str, place_b: str, index: Index) -> bool:
    """Are two places the same site (siblings, or a parent and its child)?

    Blueprint §7.2: "Separate parent sites from visually identifiable child
    structures, to prevent inflated 'accuracy' from generic large-site names."
    The device must therefore treat a parent and its child as AMBIGUOUS when
    they are visually close — a photograph of the Nalanda site as a whole is
    genuinely not separable from a photograph of Nalanda Monastery 1.
    """
    pa = next((p.parent_place_id for p in index.places if p.place_id == place_a), None)
    pb = next((p.parent_place_id for p in index.places if p.place_id == place_b), None)
    if pa is not None and pa == pb:
        return True                      # siblings
    if pa == place_b or pb == place_a:
        return True                      # parent and child
    return False


# --------------------------------------------------------------------------------------
# calibration fitting
# --------------------------------------------------------------------------------------


def clopper_pearson_upper(k: int, n: int, alpha: float = 0.05) -> float:
    if n <= 0:
        return 1.0
    if k >= n:
        return 1.0
    if k == 0:
        return 1.0 - alpha ** (1.0 / n)

    def cdf_le_k(p: float) -> float:
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))

    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if cdf_le_k(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def fit_calibration(
    index: Index,
    calib_known: Sequence[Tuple[np.ndarray, str, str, Sequence[str]]],
    calib_unknown: Sequence[Tuple[np.ndarray, str, Sequence[str]]],
    target_far: float = 0.05,
    top_k_mean: int = 2,
    min_coverage: float = 0.30,
) -> Tuple[Calibration, Dict[str, object]]:
    """Fits the decision thresholds on the CALIBRATION split only.

    The threshold sweep picks the MOST PERMISSIVE relative threshold whose
    Clopper-Pearson 95% upper bound on the false-accept rate — computed at the
    EFFECTIVE sample size (distinct source photographs), not the row count —
    stays at or below [target_far]. Never touches the test split.
    """
    base = index.calibration
    # The working index MUST carry the negative source ids. Without them the
    # leave-one-series-out exclusion cannot remove anything from the negative
    # bank, and the calibration is fitted against a bank that still contains
    # the query's own near-duplicate siblings - which is exactly the optimism
    # that made the fitted threshold far too permissive.
    work = Index(index.places, index.negatives, index.negative_labels,
                 Calibration(base.accept_threshold, base.relative_threshold,
                             base.hard_negative_margin, base.sibling_margin,
                             base.min_margin, top_k_mean),
                 index.negative_source_ids)

    known_scores: List[Tuple[float, float, float]] = []  # (place, place_margin, open_margin)
    for q, src, truth_id, series in calib_known:
        scored = score_places(work, q, exclude_source=src, exclude_sources=set(series))
        if not scored:
            continue
        # The score of the TRUE place (not the top-scoring one): a calibration
        # query is a photograph of a place we know, so the quantity we need is
        # "how well does its own place score", and "how far above the runner-up
        # place does it sit".
        mine = next((s for s in scored if s.place_id == truth_id), None)
        if mine is None:
            continue
        others = [s.score for s in scored if s.place_id != truth_id]
        best_other = max(others) if others else -1.0
        known_scores.append((mine.score, mine.score - best_other, mine.open_margin))

    unknown_scores: List[Tuple[float, float]] = []  # (place, open_margin)
    for q, src, series in calib_unknown:
        scored = score_places(work, q, exclude_source=src, exclude_sources=set(series))
        if not scored:
            continue
        top = scored[0]
        unknown_scores.append((top.score, top.open_margin))

    # Effective N for the bound: distinct SUBJECT SERIES, not rows and not
    # photographs. A series "passes" if ANY of its photographs would be
    # accepted - that is one independent trial, and it is the trial that can
    # produce a false accept.
    #
    # This used to count SOURCE PHOTOGRAPHS, which overstates the evidence:
    # a series of fifteen near-duplicate photographs was counted as fifteen
    # independent trials, and the Clopper-Pearson bound was computed against
    # an n several times too large. The bound it produced was therefore too
    # OPTIMISTIC - the opposite of the direction the protocol requires.
    def _passing_photos(unknown_rows: Sequence[Tuple[float, float, str]],
                        threshold: float) -> int:
        passing = set()
        for _score, open_margin, src in unknown_rows:
            if open_margin >= threshold:
                passing.add(src)
        return len(passing)

    unknown_rows: List[Tuple[float, float, str]] = []
    for (q, src, series), (_score, open_margin) in zip(calib_unknown, unknown_scores):
        # the SERIES identity is the trial identity
        unknown_rows.append((_score, open_margin, series[0] if series else src))
    eff_n = len({s for _sc, _r, s in unknown_rows}) or len(unknown_rows)

    best = None
    certifiable = False
    # Prefer a threshold whose Clopper-Pearson bound over INDEPENDENT trials
    # certifies the target FAR.
    for step in range(-100, 101):
        rel_thr = round(step * 0.01, 2)
        fa = _passing_photos(unknown_rows, rel_thr)
        bound = clopper_pearson_upper(fa, eff_n)
        cov = sum(1 for _s, _pm, om in known_scores if om >= rel_thr) / max(1, len(known_scores))
        if bound <= target_far and cov >= min_coverage:
            best = (rel_thr, fa, bound, cov)
            certifiable = True
            break

    if best is None:
        # The bound CANNOT be certified at this effective N: with `eff_n`
        # independent negatives, a PERFECT run already has an upper bound of
        # 1 - 0.05^(1/eff_n), which exceeds the target when eff_n < 59.
        #
        # The operating point is then chosen to TARGET the false-accept rate
        # rather than to forbid every failure. "Admit no calibration negative
        # at all" is the most conservative rule the sample supports, and it is
        # far more conservative than the target: with 24 independent
        # calibration negatives it produced a 58 % abstention rate on true
        # matches to hold a measured false-accept rate of 1.1 %. The target
        # is a RATE, so the rule is: the most permissive threshold whose
        # ESTIMATED rate on the calibration sample is at or below the target
        # and which keeps the coverage the protocol requires.
        #
        # The number the team reports is still a bound and not a claim: the
        # calibration sample is small, and the evaluator computes the
        # Clopper-Pearson bound at the TEST split's effective n.
        allowed = max(0, int(target_far * eff_n))
        candidates = []
        # Swept from the STRICTEST threshold downwards, so the first candidate
        # that meets the target is the MOST PERMISSIVE one that does. (The
        # rule is "accept if open_margin >= threshold", so a LOWER threshold
        # is the more permissive one.)
        for step in range(100, -101, -1):
            rel_thr = round(step * 0.01, 2)
            fa = _passing_photos(unknown_rows, rel_thr)
            if fa > allowed:
                continue
            cov = sum(1 for _s, _pm, om in known_scores if om >= rel_thr) / max(1, len(known_scores))
            if cov < min_coverage:
                continue
            candidates.append((rel_thr, fa, clopper_pearson_upper(fa, eff_n), cov))
            break
        if not candidates:
            # even one failure is over the target: fall back to the strictest
            # rule the sample supports
            strict = 0.0
            for step in range(-100, 101):
                rel_thr = round(step * 0.01, 2)
                if _passing_photos(unknown_rows, rel_thr) == 0:
                    strict = rel_thr
                    break
            candidates = []
            for step in range(-100, 101):
                rel_thr = round(step * 0.01, 2)
                if _passing_photos(unknown_rows, rel_thr) == 0:
                    cov = sum(1 for _s, _pm, om in known_scores if om >= rel_thr) / max(1, len(known_scores))
                    candidates.append((rel_thr, 0, clopper_pearson_upper(0, eff_n), cov))
        if candidates:
            # the most permissive threshold that still meets the target
            best = candidates[0]
        else:
            best = (strict, 0, clopper_pearson_upper(0, eff_n),
                    sum(1 for _s, _pm, om in known_scores if om >= strict) / max(1, len(known_scores)))

    rel_thr, fa, bound, cov = best

    # Absolute floor: a sanity gate on the embedding, not a tuned operating
    # point. Set well below the calibration positives so it only rejects a
    # broken embedding — the open margin does the real work.
    abs_thr = 0.0
    if known_scores:
        vals = sorted(s for s, _pm, _om in known_scores)
        abs_thr = max(0.0, vals[max(0, int(0.02 * len(vals)) - 1)] - 0.15)

    # Hard-negative margin: LEGACY name of the open-set gate. The open-set gate
    # is `relative_threshold`; this is kept at 0 in newly fitted calibrations so
    # the two cannot contradict each other. Older packs that shipped a
    # non-zero value keep their old behaviour (the device takes the max of the
    # two), so an existing pack never becomes MORE permissive on upgrade.
    hard_margin = 0.0

    # Sibling margin: a DISAMBIGUATION gate, not the open-set gate. It must only
    # reject genuinely ambiguous pairs, so it is taken from the low tail of the
    # calibration positives' place margins and capped: a 10th-percentile rule
    # would reject a tenth of every true match by construction.
    sibling_margin = 0.04
    pms = sorted(pm for _s, pm, _om in known_scores)
    if pms:
        sibling_margin = max(0.0, min(0.06, pms[max(0, int(0.05 * len(pms)) - 1)]))

    # Related-pair margin: a PARENT site and its child (or two siblings) that
    # look alike must be reported as a PAIR, not forced onto one of them
    # (blueprint §7.2). The margin is fitted from the observed distribution of
    # margins between a place and its closest RELATED place.
    related_margins: List[float] = []
    for q, src, truth_id, _series in calib_known:
        scored = score_places(work, q, exclude_source=src)
        mine = next((s for s in scored if s.place_id == truth_id), None)
        if mine is None:
            continue
        rel = [s for s in scored if s.place_id != truth_id and _related(truth_id, s.place_id, work)]
        if rel:
            related_margins.append(mine.score - max(s.score for s in rel))
    related_margin = 0.0
    if related_margins:
        rel_sorted = sorted(related_margins)
        # the median observed related-pair margin: below it, abstain
        related_margin = max(0.0, rel_sorted[len(rel_sorted) // 2])

    # Platt calibrator on the open margin (QA provenance only).
    calibrator = _fit_platt(known_scores, unknown_scores)

    cal = Calibration(
        accept_threshold=abs_thr,
        relative_threshold=rel_thr,
        hard_negative_margin=hard_margin,
        sibling_margin=sibling_margin,
        min_margin=0.0,
        top_k_mean=top_k_mean,
        related_margin=related_margin,
        calibrator=calibrator,
        source="fitted",
    )
    report = {
        "target_far": target_far,
        "calib_known_rows": len(known_scores),
        "calib_unknown_rows": len(unknown_scores),
        "calib_effective_n_unknown": eff_n,
        "certifiable_at_target_far": certifiable,
        "minimum_effective_n_to_certify": 59,
        "selected_relative_threshold": rel_thr,
        "calib_false_accepts_at_threshold": fa,
        "calib_far_point_at_threshold": round(fa / max(1, len(unknown_scores)), 6),
        "calib_far_cp95_upper_at_effective_n": round(bound, 6),
        "calib_coverage_at_threshold": round(cov, 4),
        "accept_threshold": round(abs_thr, 6),
        "hard_negative_margin": round(hard_margin, 6),
        "sibling_margin": round(sibling_margin, 6),
        "related_margin": round(related_margin, 6),
    }
    if not certifiable:
        report["note"] = (
            f"The <= {target_far:.0%} false-accept gate CANNOT be certified at "
            f"N={eff_n} independent negatives (a perfect run already bounds at "
            f"{clopper_pearson_upper(0, eff_n):.1%}). The threshold below is the "
            f"point-FAR operating point; collect >= 59 independent hard negatives."
        )
    return cal, report


def _fit_platt(
    known_scores: Sequence[Tuple[float, float, float]],
    unknown_scores: Sequence[Tuple[float, float]],
) -> Optional[Dict[str, float]]:
    """One-dimensional logistic fit of relative score -> P(correct).

    Newton-Raphson on the Bernoulli log-likelihood. Returns None when there is
    not enough signal to fit (e.g. every calibration point has the same label).
    """
    xs: List[float] = [om for _s, _pm, om in known_scores] + [om for _s, om in unknown_scores]
    ys: List[float] = [1.0] * len(known_scores) + [0.0] * len(unknown_scores)
    if len(set(ys)) < 2 or len(xs) < 10:
        return None
    a, b = 8.0, -4.0
    for _ in range(60):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for x, y in zip(xs, ys):
            z = a * x + b
            p = 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, z))))
            w = max(p * (1.0 - p), 1e-9)
            r = y - p
            g0 += r * x
            g1 += r
            h00 += w * x * x
            h01 += w * x
            h11 += w
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            return None
        da = (h11 * g0 - h01 * g1) / det
        db = (-h01 * g0 + h00 * g1) / det
        a += da
        b += db
        if abs(da) < 1e-9 and abs(db) < 1e-9:
            break
    if a <= 0:
        return None
    return {"a": a, "b": b}
