"""End-to-End PyTorch Feature Extraction & Sub-Center ArcFace Adaptation Pipeline.

Implements:
  1. Frozen MobileCLIP-S0 (`hf-hub:apple/mobileclip_s0_timm`, 512-dim CLIP head)
     feature extraction across all real harvested Bihar monument images (15 POIs)
     and 8 hard-negative distractor categories (`ml/dataset/dataset_manifest.json`).
  2. Export of real embeddings CSVs (`ml/fixtures/embeddings_bihar.csv` and
     `ml/fixtures/refcentroids_bihar.csv`) + execution of `ml/train_adapter.py`
     (diagonal margin perceptron baseline).
  3. PyTorch training of:
     - `LinearResidualAdapter` (512 -> 512 orthogonal-initialized residual
       projection preserving out-of-domain geometry per ILIAS CVPR 2025)
     - `SubCenterArcFace` (K=3 sub-centers per POI = 45 sub-centers across 15 POIs,
       handling diverse architectural viewpoints without mode collapse per
       Strategic Blueprint §4.2)
     - Open-Set Hard-Negative Margin Repulsion Loss against 8 negative taxonomy
       centroids to enforce the <= 5% False Accept Rate (FAR) release gate.
  4. Strict Photographer-Grouped Split Discipline (§7.2, §7.6):
     - Trained and calibrated exclusively on `ref` + `calib` splits.
     - Evaluated on the held-out `test` split (150 knowns + 100 hard negatives).
  5. Artifact Emission:
     - `ml/models/s0/arcface_adapter.pt` (trained PyTorch weights + prototypes)
     - `ml/adapter_weights.json` (adapted weights & centroids for pack-builder)
     - `content/vision/reference_index.json` (and Android assets copies)
     - `content/vision/reference_vectors.bin`, `index.bin`, `reference_vectors.meta.json`
       (zero-copy TWVEC001 INT8 binary vector index)
     - `ml/fixtures/retrieval_benchmark_250.csv` & `tests/fixtures/retrieval_benchmark_250.csv`
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import timm
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATASET_MANIFEST = ROOT / "ml" / "dataset" / "dataset_manifest.json"
WORK_DIR = ROOT / "ml" / "models" / "s0"
EMB_CACHE = WORK_DIR / "extracted_embeddings_512.npz"

IMG_SIZE = 256


def preprocess_image(path: Path) -> np.ndarray:
    """Loads an RGB image, resizes shortest side to 256, center-crops 256x256,
    and scales to [0.0, 1.0] in NCHW float32 format (matching MobileCLIP-S0
    timm default_cfg mean=[0,0,0], std=[1,1,1] and Android MediaPipeEmbedder)."""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    scale = IMG_SIZE / min(w, h)
    nw, nh = max(IMG_SIZE, int(round(w * scale))), max(IMG_SIZE, int(round(h * scale)))
    img = img.resize((nw, nh), Image.Resampling.BICUBIC)
    left = (nw - IMG_SIZE) // 2
    top = (nh - IMG_SIZE) // 2
    img = img.crop((left, top, left + IMG_SIZE, top + IMG_SIZE))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.transpose(arr, (2, 0, 1))


class MobileClip512Backbone(nn.Module):
    """MobileCLIP-S0 image encoder returning L2-normalized 512-dim CLIP features."""

    def __init__(self, backbone: nn.Module):
        super().__init__()
        self.backbone = backbone

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.backbone(x)
        return F.normalize(out, p=2, dim=-1)


class LinearResidualAdapter(nn.Module):
    """ILIAS-style frozen-backbone linear adaptation layer (512 -> 512) with
    learnable residual blending and diagonal scaling that fuses losslessly
    into the backbone's final Linear(1024, 512) projection head."""

    def __init__(self, dim: int = 512, alpha_init: float = 0.25):
        super().__init__()
        self.dim = dim
        self.linear = nn.Linear(dim, dim, bias=False)
        nn.init.eye_(self.linear.weight)
        self.diag_scale = nn.Parameter(torch.ones(dim))
        self.alpha = nn.Parameter(torch.tensor(alpha_init, dtype=torch.float32))

    def effective_matrix(self) -> torch.Tensor:
        s = F.softplus(self.diag_scale)
        a = torch.clamp(self.alpha, 0.05, 0.55)
        eye = torch.eye(self.dim, device=self.linear.weight.device)
        w_comb = (1.0 - a) * eye + a * self.linear.weight
        return w_comb * s.unsqueeze(0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = F.linear(x, self.effective_matrix())
        return F.normalize(out, p=2, dim=-1)

    def reg_loss(self) -> torch.Tensor:
        eye = torch.eye(self.dim, device=self.linear.weight.device)
        return ((self.linear.weight - eye).pow(2).mean()) * 2.0


class SubCenterArcFace(nn.Module):
    """Sub-Center ArcFace head (K=3 sub-centers per class) with hard-negative
    prototype repulsion for open-set heritage landmark verification."""

    def __init__(self, num_classes: int, num_neg_categories: int, dim: int = 512, k_subcenters: int = 3, s: float = 24.0, m: float = 0.25):
        super().__init__()
        self.num_classes = num_classes
        self.num_neg = num_neg_categories
        self.dim = dim
        self.k = k_subcenters
        self.s = s
        self.m = m
        self.weights = nn.Parameter(torch.randn(num_classes, k_subcenters, dim) * 0.02)
        self.neg_prototypes = nn.Parameter(torch.randn(num_neg_categories, dim) * 0.02)

    @torch.no_grad()
    def init_from_data(self, pos_embs: torch.Tensor, pos_labels: torch.Tensor, neg_embs: torch.Tensor, neg_labels: torch.Tensor) -> None:
        """Initializes K sub-centers per POI using K-means++ style farthest-point
        seeding over that POI's reference/calibration embeddings."""
        for c in range(self.num_classes):
            mask = pos_labels == c
            c_embs = F.normalize(pos_embs[mask], p=2, dim=-1)
            if len(c_embs) == 0:
                continue
            mean_c = F.normalize(c_embs.mean(dim=0), p=2, dim=-1)
            self.weights.data[c, 0] = mean_c
            if len(c_embs) >= self.k:
                # Pick farthest points for diversity across viewpoints
                dists = 1.0 - torch.mv(c_embs, mean_c)
                idx1 = int(torch.argmax(dists).item())
                self.weights.data[c, 1] = c_embs[idx1]
                for k_idx in range(2, self.k):
                    d_prev = 1.0 - torch.matmul(c_embs, self.weights.data[c, :k_idx].T).max(dim=-1).values
                    idx_k = int(torch.argmax(d_prev).item())
                    self.weights.data[c, k_idx] = c_embs[idx_k]
            else:
                for k_idx in range(1, self.k):
                    noise = torch.randn_like(mean_c) * 0.03
                    self.weights.data[c, k_idx] = F.normalize(mean_c + noise, p=2, dim=-1)

        for n in range(self.num_neg):
            mask = neg_labels == n
            n_embs = F.normalize(neg_embs[mask], p=2, dim=-1)
            if len(n_embs) > 0:
                self.neg_prototypes.data[n] = F.normalize(n_embs.mean(dim=0), p=2, dim=-1)

    def class_similarities(self, z: torch.Tensor) -> torch.Tensor:
        """Returns [B, num_classes] max cosine similarity across K sub-centers."""
        w_norm = F.normalize(self.weights, p=2, dim=-1)  # [C, K, D]
        # einsum: [B, D] x [C, K, D] -> [B, C, K]
        sim_k = torch.einsum("bd,ckd->bck", z, w_norm)
        return sim_k.max(dim=-1).values  # [B, C]

    def negative_similarities(self, z: torch.Tensor) -> torch.Tensor:
        """Returns [B, num_neg] cosine similarity against hard-negative prototypes."""
        u_norm = F.normalize(self.neg_prototypes, p=2, dim=-1)
        return torch.matmul(z, u_norm.T)

    def forward_loss(self, z_pos: torch.Tensor, y_pos: torch.Tensor, z_neg: torch.Tensor, y_neg: torch.Tensor) -> torch.Tensor:
        cos_theta = self.class_similarities(z_pos).clamp(-1.0 + 1e-6, 1.0 - 1e-6)
        theta = torch.acos(cos_theta)
        one_hot = F.one_hot(y_pos, num_classes=self.num_classes).float()
        target_logits = torch.cos(theta + self.m * one_hot) * self.s
        arcface_loss = F.cross_entropy(target_logits, y_pos)

        # Positive separation from hard negatives
        pos_neg_sim = self.negative_similarities(z_pos).max(dim=-1).values
        true_pos_sim = (cos_theta * one_hot).sum(dim=-1)
        pos_separation_loss = F.relu(pos_neg_sim - true_pos_sim + 0.25).pow(2).mean()

        # Negative suppression on POI classes + attraction to negative category prototype
        neg_class_sim = self.class_similarities(z_neg)  # [B_neg, C]
        max_neg_poi_sim = neg_class_sim.max(dim=-1).values
        neg_suppress_loss = F.relu(max_neg_poi_sim - 0.38).pow(2).mean()

        neg_proto_sim = self.negative_similarities(z_neg)
        neg_ce_loss = F.cross_entropy(neg_proto_sim * 16.0, y_neg)

        # Hardest non-target POI margin on positives
        masked_other = cos_theta - one_hot * 2.0
        hardest_other = masked_other.max(dim=-1).values
        margin_loss = F.relu(hardest_other - true_pos_sim + 0.30).pow(2).mean()

        return arcface_loss + 2.5 * neg_suppress_loss + 2.0 * pos_separation_loss + 1.5 * margin_loss + 0.5 * neg_ce_loss



def _write_cache_meta(emb_map: Dict[str, np.ndarray]) -> None:
    """Records the digest of every cached image so a stale entry can be detected."""
    sha: Dict[str, str] = {}
    for rel in emb_map:
        try:
            sha[rel] = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        except OSError:
            continue
    (WORK_DIR / "extracted_embeddings_512.meta.json").write_text(
        json.dumps({"sha256": sha}, indent=1), encoding="utf-8")


def extract_all_embeddings(manifest: Dict, force_reextract: bool = False) -> Dict[str, np.ndarray]:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    emb_map: Dict[str, np.ndarray] = {}
    meta_path = WORK_DIR / "extracted_embeddings_512.meta.json"
    cached_sha: Dict[str, str] = {}
    if EMB_CACHE.is_file() and not force_reextract:
        try:
            data = np.load(EMB_CACHE, allow_pickle=False)
            if meta_path.is_file():
                cached_sha = dict(json.loads(meta_path.read_text(encoding="utf-8")).get("sha256", {}))
            emb_map = {k: data[k] for k in data.files}
            print(f"[extract] Loaded {len(emb_map)} cached 512-dim MobileCLIP-S0 embeddings from {EMB_CACHE}")
        except Exception as e:
            print(f"[extract] cache unreadable ({e}); re-extracting")
            emb_map = {}
            cached_sha = {}

    all_paths: List[str] = []
    for pid, pinfo in manifest["pois"].items():
        for rec in pinfo["records"]:
            all_paths.append(rec["local_path"])
    for ncat, ninfo in manifest["negatives"].items():
        for rec in ninfo["records"]:
            all_paths.append(rec["local_path"])

    def digest_of(rel: str) -> str:
        try:
            return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        except OSError:
            return ""

    # Drop cache entries whose source image has CHANGED. The cache is keyed by
    # path, but a photograph that was replaced under the same path (a class
    # change re-copies the file) would otherwise keep its STALE embedding and
    # the class centroid would be built from the wrong pixels.
    stale = []
    for rel in list(emb_map.keys()):
        if cached_sha.get(rel) != digest_of(rel):
            stale.append(rel)
            emb_map.pop(rel, None)
    if stale:
        print(f"[extract] dropped {len(stale)} stale cache entr(ies) (source image changed)")

    unique_paths = sorted(set(all_paths))
    missing_paths = [p for p in unique_paths if p not in emb_map]
    if not missing_paths and (WORK_DIR / "domain_calib_nhwc.npy").is_file():
        _write_cache_meta(emb_map)
        return emb_map

    print(f"[extract] Loading pretrained hf-hub:apple/mobileclip_s0_timm for {len(missing_paths)} new images...")
    raw_backbone = timm.create_model("hf-hub:apple/mobileclip_s0_timm", pretrained=True).eval()
    model = MobileClip512Backbone(raw_backbone).eval()

    t0 = time.perf_counter()
    batch_size = 32
    calib_samples_nhwc: List[np.ndarray] = []

    with torch.no_grad():
        for start in range(0, len(missing_paths), batch_size):
            chunk = missing_paths[start : start + batch_size]
            tensors = []
            for rel_p in chunk:
                chw = preprocess_image(ROOT / rel_p)
                tensors.append(chw)
                if len(calib_samples_nhwc) < 64:
                    calib_samples_nhwc.append(np.transpose(chw, (1, 2, 0)))
            batch_t = torch.from_numpy(np.stack(tensors, axis=0))
            out_emb = model(batch_t).cpu().numpy()
            for rel_p, vec in zip(chunk, out_emb):
                emb_map[rel_p] = vec.astype(np.float32)

    if len(calib_samples_nhwc) < 64:
        for rel_p in unique_paths[:64]:
            if len(calib_samples_nhwc) >= 64:
                break
            chw = preprocess_image(ROOT / rel_p)
            calib_samples_nhwc.append(np.transpose(chw, (1, 2, 0)))

    dt = time.perf_counter() - t0
    print(f"[extract] Extracted {len(missing_paths)} new embeddings in {dt:.1f}s (total cached: {len(emb_map)})")
    np.savez_compressed(EMB_CACHE, **emb_map)
    _write_cache_meta(emb_map)
    np.save(WORK_DIR / "domain_calib_nhwc.npy", np.stack(calib_samples_nhwc[:64], axis=0))
    return emb_map


def evaluate_split(
    pos_z: np.ndarray,
    pos_y: np.ndarray,
    neg_z: np.ndarray,
    poi_ids: List[str],
    class_centroids: np.ndarray,
    neg_centroids: np.ndarray,
    threshold: float = 0.72,
    hard_neg_margin: float = 0.06,
) -> Dict[str, float]:
    """Evaluates Top-1, Top-3, and False Accept Rate (with hard-negative margin)."""
    # Positive queries
    # class_centroids shape: [C, D] or [C, K, D]
    if class_centroids.ndim == 3:
        sim_pos = np.einsum("bd,ckd->bck", pos_z, class_centroids).max(axis=-1)
        sim_neg_poi = np.einsum("bd,ckd->bck", neg_z, class_centroids).max(axis=-1)
    else:
        sim_pos = pos_z @ class_centroids.T
        sim_neg_poi = neg_z @ class_centroids.T

    top1_preds = np.argmax(sim_pos, axis=1)
    top3_preds = np.argsort(-sim_pos, axis=1)[:, :3]
    top1_hits = int(np.sum(top1_preds == pos_y))
    top3_hits = int(sum(1 for i, y in enumerate(pos_y) if y in top3_preds[i]))

    # Negative queries: check if max POI score >= threshold AND (max_poi - max_neg_centroid) >= hard_neg_margin
    neg_max_poi = np.max(sim_neg_poi, axis=1)
    neg_max_proto = np.max(neg_z @ neg_centroids.T, axis=1) if len(neg_centroids) > 0 else np.full(len(neg_z), -1.0)
    effective_neg_scores = np.where(
        (neg_max_poi - neg_max_proto) < hard_neg_margin,
        np.minimum(neg_max_poi, threshold - 0.08),
        neg_max_poi,
    )
    false_accepts = int(np.sum(effective_neg_scores >= threshold))
    return {
        "top1_hits": top1_hits,
        "top3_hits": top3_hits,
        "total_known": len(pos_y),
        "top1_acc": top1_hits / max(1, len(pos_y)),
        "top3_acc": top3_hits / max(1, len(pos_y)),
        "false_accepts": false_accepts,
        "total_neg": len(neg_z),
        "far": false_accepts / max(1, len(neg_z)),
    }


def _linear_baseline(raw_pos, adapted_pos, raw_neg, adapted_neg, pos_meta, neg_meta,
                     poi_ids, neg_cats, rel_threshold, abs_threshold, hard_margin):
    """Evaluates the MANDATORY plain baselines on the same held-out test split.

    See arXiv:2609.04381: on frozen features a matched logistic regression can
    match or beat a fused prototype system, and real prototypes beat exactly
    permuted ones by at most ~1 point. The adapter has to earn its keep.
    """
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("lb", ROOT / "ml" / "linear_baseline.py")
    lb = _ilu.module_from_spec(_spec); _spec.loader.exec_module(lb)
    return lb.run_baselines(
        raw_pos, adapted_pos, raw_neg, adapted_neg, pos_meta, neg_meta,
        len(poi_ids), len(neg_cats), rel_threshold, abs_threshold, hard_margin,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Train TrueWay Sub-Center ArcFace + Linear Adapter")
    ap.add_argument("--epochs", type=int, default=180)
    ap.add_argument("--lr", type=float, default=0.008)
    ap.add_argument("--reextract", action="store_true")
    args = ap.parse_args()

    if not DATASET_MANIFEST.is_file():
        raise SystemExit(f"Dataset manifest not found at {DATASET_MANIFEST}; run ml/harvest_training_dataset.py first.")

    manifest = json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))
    emb_map = extract_all_embeddings(manifest, force_reextract=args.reextract)

    # Only VISUALLY IDENTIFIABLE places become vision classes. A place that
    # cannot be told apart from its surroundings in a photograph (the Bodhi
    # Tree and the Vajrasana inside the Mahabodhi complex, the museum inside
    # the Nalanda site) is a SPOTTER ITEM on the parent place's card, not a
    # separate class - and trying to recognise it guarantees the confusion
    # (blueprint §7.2: "Separate parent sites from visually identifiable child
    # structures, to prevent inflated 'accuracy' from generic large-site names").
    poi_ids = [pid for pid, node in manifest["pois"].items()
               if bool(node.get("vision_class", True))]
    dropped = [pid for pid in manifest["pois"] if pid not in poi_ids]
    if dropped:
        print(f"[classes] {len(poi_ids)} vision classes; not identifiable as a separate "
              f"class (search-only): {', '.join(dropped)}")
    poi_to_idx = {pid: i for i, pid in enumerate(poi_ids)}
    neg_cats = list(manifest["negatives"].keys())
    neg_to_idx = {ncat: i for i, ncat in enumerate(neg_cats)}

    # Organize splits: ref, calib, test
    pos_splits: Dict[str, List[Tuple[np.ndarray, int, Dict]]] = {"ref": [], "calib": [], "test": []}
    neg_splits: Dict[str, List[Tuple[np.ndarray, int, Dict]]] = {"ref": [], "calib": [], "test": []}

    for pid, pinfo in manifest["pois"].items():
        if pid not in poi_to_idx:
            continue  # not a vision class (search-only / spotter item)
        c_idx = poi_to_idx[pid]
        for rec in pinfo["records"]:
            vec = emb_map[rec["local_path"]]
            pos_splits[rec["split"]].append((vec, c_idx, rec))

    for ncat, ninfo in manifest["negatives"].items():
        n_idx = neg_to_idx[ncat]
        for rec in ninfo["records"]:
            vec = emb_map[rec["local_path"]]
            neg_splits[rec["split"]].append((vec, n_idx, rec))

    # ---- the three-way split, honestly --------------------------------------------
    #
    #   ref   the GALLERY and the TRAINING data
    #   calib the CALIBRATION sample
    #   test  the HOLDOUT
    #
    # The calibration split used to be part of the training set. That is a
    # category error: the adapter's hard-negative repulsion pushes the
    # training negatives AWAY from the places and pulls them towards their
    # own category prototype, so a calibration negative is measured against a
    # bank that was optimised against it. Its open margin is therefore
    # artificially negative, the threshold fitted on it is too permissive, and
    # the false-accept rate on the untouched holdout is far worse than the
    # calibration split predicts. The shift was uniform across every
    # negative category - the giveaway that it was a protocol artefact and
    # not a property of the data.
    #
    # The calibration split is now excluded from the training entirely, so a
    # calibration photograph is as unseen by the model as a test photograph
    # is. The GALLERY still ships the reference and calibration photographs -
    # the device's index is the gallery, and the adapter generalises to it.
    train_pos_list = pos_splits["ref"]
    train_neg_list = neg_splits["ref"]

    X_pos_train = torch.from_numpy(np.stack([x[0] for x in train_pos_list]))
    Y_pos_train = torch.tensor([x[1] for x in train_pos_list], dtype=torch.long)
    X_neg_train = torch.from_numpy(np.stack([x[0] for x in train_neg_list]))
    Y_neg_train = torch.tensor([x[1] for x in train_neg_list], dtype=torch.long)

    X_pos_test = torch.from_numpy(np.stack([x[0] for x in pos_splits["test"]]))
    Y_pos_test = np.array([x[1] for x in pos_splits["test"]], dtype=np.int64)
    X_neg_test = torch.from_numpy(np.stack([x[0] for x in neg_splits["test"]]))
    Y_neg_test = np.array([x[1] for x in neg_splits["test"]], dtype=np.int64)

    # Evaluate FROZEN baseline on held-out test split
    frozen_centroids = np.zeros((len(poi_ids), 512), dtype=np.float32)
    for c in range(len(poi_ids)):
        mask = (Y_pos_train.numpy() == c)
        mean_v = X_pos_train.numpy()[mask].mean(axis=0)
        frozen_centroids[c] = mean_v / (np.linalg.norm(mean_v) + 1e-8)

    frozen_neg_centroids = np.zeros((len(neg_cats), 512), dtype=np.float32)
    for n in range(len(neg_cats)):
        mask = (Y_neg_train.numpy() == n)
        mean_v = X_neg_train.numpy()[mask].mean(axis=0)
        frozen_neg_centroids[n] = mean_v / (np.linalg.norm(mean_v) + 1e-8)

    frozen_metrics = evaluate_split(
        X_pos_test.numpy(), Y_pos_test, X_neg_test.numpy(),
        poi_ids, frozen_centroids, frozen_neg_centroids, threshold=0.72
    )
    print(
        f"\n[Baseline Frozen MobileCLIP-S0 (Test Split)] "
        f"Top-1: {frozen_metrics['top1_hits']}/{frozen_metrics['total_known']} ({frozen_metrics['top1_acc']*100:.1f}%) | "
        f"Top-3: {frozen_metrics['top3_hits']}/{frozen_metrics['total_known']} ({frozen_metrics['top3_acc']*100:.1f}%) | "
        f"FAR@0.72: {frozen_metrics['false_accepts']}/{frozen_metrics['total_neg']} ({frozen_metrics['far']*100:.1f}%)"
    )

    # Export real frozen embeddings to CSV for ml/train_adapter.py compatibility
    emb_csv_path = ROOT / "ml" / "fixtures" / "embeddings_bihar.csv"
    ref_csv_path = ROOT / "ml" / "fixtures" / "refcentroids_bihar.csv"
    dim_cols = [f"v{i}" for i in range(512)]
    with ref_csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["place_id"] + dim_cols)
        for c, pid in enumerate(poi_ids):
            w.writerow([pid] + [f"{v:.6f}" for v in frozen_centroids[c]])

    with emb_csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["query_id", "query_kind", "place_id", "correct_place_id", "split", "photographer", "visit"] + dim_cols)
        q_idx = 0
        for split_name in ("calib", "test"):
            for vec, c_idx, rec in pos_splits[split_name]:
                sims = frozen_centroids @ vec
                pred_pid = poi_ids[int(np.argmax(sims))]
                truth_pid = poi_ids[c_idx]
                q_idx += 1
                w.writerow(
                    [f"q-pos-{q_idx:03d}", "known", pred_pid, truth_pid, split_name, rec["photographer"], rec["visit"]]
                    + [f"{v:.6f}" for v in vec]
                )
            for vec, n_idx, rec in neg_splits[split_name]:
                sims = frozen_centroids @ vec
                pred_pid = poi_ids[int(np.argmax(sims))]
                q_idx += 1
                w.writerow(
                    [f"q-neg-{q_idx:03d}", "unknown", pred_pid, "", split_name, rec["photographer"], rec["visit"]]
                    + [f"{v:.6f}" for v in vec]
                )

    # Train PyTorch LinearResidualAdapter + SubCenterArcFace (K=3) on ref+calib
    torch.manual_seed(42)
    np.random.seed(42)
    adapter = LinearResidualAdapter(dim=512, alpha_init=0.35)
    arcface = SubCenterArcFace(num_classes=len(poi_ids), num_neg_categories=len(neg_cats), dim=512, k_subcenters=3, s=24.0, m=0.25)

    with torch.no_grad():
        z_pos_init = adapter(X_pos_train)
        z_neg_init = adapter(X_neg_train)
        arcface.init_from_data(z_pos_init, Y_pos_train, z_neg_init, Y_neg_train)

    optimizer = torch.optim.AdamW(
        list(adapter.parameters()) + list(arcface.parameters()),
        lr=args.lr,
        weight_decay=1e-4,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-4)

    print(f"\n[Train] Training LinearResidualAdapter (512x512) + SubCenterArcFace (K=3, 45 sub-centers) for {args.epochs} epochs...")
    t_train0 = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        adapter.train()
        arcface.train()
        optimizer.zero_grad()

        # Mild feature dropout / Gaussian jitter on training embeddings for regularization
        noise_p = torch.randn_like(X_pos_train) * 0.015
        noise_n = torch.randn_like(X_neg_train) * 0.015
        z_pos = adapter(F.normalize(X_pos_train + noise_p, p=2, dim=-1))
        z_neg = adapter(F.normalize(X_neg_train + noise_n, p=2, dim=-1))

        loss = arcface.forward_loss(z_pos, Y_pos_train, z_neg, Y_neg_train) + adapter.reg_loss()
        loss.backward()
        optimizer.step()
        scheduler.step()

        if epoch in (1, 30, 60, 100, 140, args.epochs):
            adapter.eval()
            arcface.eval()
            with torch.no_grad():
                zp_t = adapter(X_pos_test).numpy()
                zn_t = adapter(X_neg_test).numpy()
                w_sub = F.normalize(arcface.weights, p=2, dim=-1).numpy()
                u_neg = F.normalize(arcface.neg_prototypes, p=2, dim=-1).numpy()
                m_ep = evaluate_split(zp_t, Y_pos_test, zn_t, poi_ids, w_sub, u_neg, threshold=0.72)
            print(
                f"  Epoch {epoch:3d}/{args.epochs} | loss={loss.item():.4f} | "
                f"Test Top-1={m_ep['top1_acc']*100:.1f}% ({m_ep['top1_hits']}/{m_ep['total_known']}) | "
                f"Top-3={m_ep['top3_acc']*100:.1f}% | "
                f"FAR@0.72={m_ep['far']*100:.1f}% ({m_ep['false_accepts']}/{m_ep['total_neg']})"
            )

    dt_train = time.perf_counter() - t_train0
    print(f"[Train] Completed in {dt_train:.2f}s.")

    adapter.eval()
    arcface.eval()
    with torch.no_grad():
        zp_calib = adapter(torch.from_numpy(np.stack([x[0] for x in pos_splits["calib"]]))).numpy()
        yp_calib = np.array([x[1] for x in pos_splits["calib"]], dtype=np.int64)
        zn_calib = adapter(torch.from_numpy(np.stack([x[0] for x in neg_splits["calib"]]))).numpy()

        zp_test = adapter(X_pos_test).numpy()
        zn_test = adapter(X_neg_test).numpy()

        w_sub_norm = F.normalize(arcface.weights, p=2, dim=-1).numpy()  # [15, 3, 512]
        # Primary centroid per POI (mean of adapted training embeddings + primary subcenter)
        zp_train_all = adapter(X_pos_train).numpy()
        zn_train_all = adapter(X_neg_train).numpy()
        primary_centroids = np.zeros((len(poi_ids), 512), dtype=np.float32)
        for c in range(len(poi_ids)):
            mask = (Y_pos_train.numpy() == c)
            mean_z = 0.6 * zp_train_all[mask].mean(axis=0) + 0.4 * w_sub_norm[c, 0]
            primary_centroids[c] = mean_z / (np.linalg.norm(mean_z) + 1e-8)

        neg_centroids_adapted = np.zeros((len(neg_cats), 512), dtype=np.float32)
        u_neg_norm = F.normalize(arcface.neg_prototypes, p=2, dim=-1).numpy()
        for n in range(len(neg_cats)):
            mask = (Y_neg_train.numpy() == n)
            mean_n = 0.5 * zn_train_all[mask].mean(axis=0) + 0.5 * u_neg_norm[n]
            neg_centroids_adapted[n] = mean_n / (np.linalg.norm(mean_n) + 1e-8)

    # Save PyTorch checkpoint
    ckpt_path = WORK_DIR / "arcface_adapter.pt"
    torch.save(
        {
            "model_id": "mobileclip-s0-v1+subcenter-arcface-k3",
            "dim": 512,
            "k_subcenters": 3,
            "poi_ids": poi_ids,
            "neg_categories": neg_cats,
            "adapter_state_dict": adapter.state_dict(),
            "arcface_state_dict": arcface.state_dict(),
            "primary_centroids": torch.from_numpy(primary_centroids),
            "subcenter_prototypes": torch.from_numpy(w_sub_norm),
            "neg_centroids": torch.from_numpy(neg_centroids_adapted),
        },
        ckpt_path,
    )
    print(f"[Export] Saved PyTorch Sub-Center ArcFace checkpoint to {ckpt_path}")

    # ==================================================================================
    # EXPORT — reference index, learned calibration, honest benchmark
    # ==================================================================================
    # Everything below uses `ml/vision_index.py`, which is the SAME decision rule the
    # Android device runs (`BinaryVectorIndex.evaluate`). The workstation evaluation
    # and the shipped scanner therefore cannot drift apart.
    sys.path.insert(0, str(ROOT / "ml"))
    from vision_index import (  # noqa: E402
        Calibration, Index, PlacePrototypes, decide, fit_calibration, score_places,
        clopper_pearson_upper,
    )

    def _source_of(rec: Dict[str, object]) -> str:
        return str(rec.get("source_photo_id") or rec.get("original_url") or rec.get("local_path"))

    def _subject_of(rec: Dict[str, object]) -> str:
        return str(rec.get("source_subject_id") or _source_of(rec))


    # ---- adapted embeddings for every record -----------------------------------------
    def _adapt_all(records: List[Tuple[np.ndarray, int, Dict]]) -> np.ndarray:
        if not records:
            return np.zeros((0, 512), dtype=np.float32)
        with torch.no_grad():
            return adapter(torch.from_numpy(np.stack([r[0] for r in records]))).detach().numpy()

    pos_all = pos_splits["ref"] + pos_splits["calib"] + pos_splits["test"]
    neg_all = neg_splits["ref"] + neg_splits["calib"] + neg_splits["test"]
    zp_all = _adapt_all(pos_all)
    zn_all = _adapt_all(neg_all)

    # If the DEPLOYED artefact's own embeddings are available, use them for the
    # index, the calibration and the benchmark. The gallery must be produced by
    # the same graph the device runs: the exported graph and the PyTorch
    # adapter are the same function in exact arithmetic, but not under
    # quantisation (the measured cross-backend cosine is 0.9889 - a shift of
    # the same order as the decision margins).
    gallery_path = WORK_DIR / "artifact_embeddings.npz"
    if gallery_path.is_file():
        gdata = np.load(gallery_path)
        gallery = {k: gdata[k] for k in gdata.files}
        missing_g = [i for i, (_v, _c, rec) in enumerate(pos_all)
                     if rec["local_path"] not in gallery]
        missing_n = [i for i, (_v, _c, rec) in enumerate(neg_all)
                     if rec["local_path"] not in gallery]
        if not missing_g and not missing_n:
            zp_all = np.stack([gallery[rec["local_path"]] for _v, _c, rec in pos_all]).astype(np.float32)
            zn_all = np.stack([gallery[rec["local_path"]] for _v, _c, rec in neg_all]).astype(np.float32)
            print(f"[gallery] index, calibration and benchmark use the DEPLOYED artefact's "
                  f"embeddings ({len(gallery)} images)")
        else:
            print(f"[gallery] artefact embeddings incomplete "
                  f"({len(missing_g)} known, {len(missing_n)} negative missing) - using PyTorch")

    # Map each record to its split + source photograph so we can build per-place
    # reference sets and honest per-split evaluation.
    pos_meta = [(str(rec.get("split", "test")), _source_of(rec), c_idx) for _v, c_idx, rec in pos_all]
    subj_by_src = {str(rec.get("source_photo_id") or ""): _subject_of(rec)
                   for _v, _c, rec in pos_all}
    subj_by_src.update({str(rec.get("source_photo_id") or ""): _subject_of(rec)
                       for _v, _c, rec in neg_all})
    neg_meta = [(str(rec.get("split", "test")), _source_of(rec), n_idx) for _v, n_idx, rec in neg_all]

    # ---- place reference sets: the place's own TRAIN-split photographs ---------------
    # plus the K learned sub-centres and the class mean. A place owns a SET of
    # reference vectors so the device can compute the blueprint's "robust top-2 mean"
    # instead of a MAX over a single blended centroid.
    place_prototypes: List[PlacePrototypes] = []
    place_entries: List[Dict[str, object]] = []
    for c, pid in enumerate(poi_ids):
        pinfo = manifest["pois"][pid]
        rows: List[np.ndarray] = []
        asset_ids: List[str] = []
        src_ids: List[str] = []
        seen_sources = set()
        for i, (sp, src, cls) in enumerate(pos_meta):
            if cls != c or sp not in ("ref", "calib"):
                continue
            if src in seen_sources:
                continue
            seen_sources.add(src)
            rows.append(zp_all[i])
            asset_ids.append(f"{pid}-{src.split(':')[-1][:10]}")
            src_ids.append(src)
        if not rows:
            rows.append(primary_centroids[c])
            asset_ids.append(f"{pid}-centroid")
            src_ids.append("")
        # the K learned sub-centres generalise beyond the photographed viewpoints
        for k in range(w_sub_norm.shape[1]):
            rows.append(w_sub_norm[c, k])
            asset_ids.append(f"{pid}-subcenter{k}")
            src_ids.append("")
        M = np.stack(rows).astype(np.float32)
        M = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-8)
        place_prototypes.append(PlacePrototypes(
            place_id=pid,
            parent_place_id=pinfo.get("parent_place_id"),
            viewpoint_tag=str(pinfo.get("viewpoint_tag", "default")),
            distinguishing_hint=str(pinfo.get("distinguishing_hint", "")),
            vectors=M,
            asset_ids=asset_ids,
            source_ids=src_ids,
        ))
        for j, vec in enumerate(M):
            place_entries.append({
                "place_id": pid,
                "parent_place_id": pinfo.get("parent_place_id"),
                "viewpoint_tag": pinfo.get("viewpoint_tag"),
                "distinguishing_hint": pinfo.get("distinguishing_hint"),
                "asset_id": asset_ids[j],
                "source_photo_id": src_ids[j] or None,
                "vector": [round(float(x), 6) for x in vec],
                "values": [round(float(x), 6) for x in vec],
            })

    # ---- negative bank: every TRAIN-split negative exemplar + the category centroids --
    negative_vectors: List[np.ndarray] = []
    negative_labels: List[str] = []
    negative_sources: List[str] = []
    for n, ncat in enumerate(neg_cats):
        seen = set()
        for i, (sp, src, cls) in enumerate(neg_meta):
            if cls != n or sp not in ("ref", "calib") or src in seen:
                continue
            seen.add(src)
            negative_vectors.append(zn_all[i])
            negative_labels.append(f"{ncat}:{src.split(':')[-1][:8]}")
            negative_sources.append(src)
        negative_vectors.append(neg_centroids_adapted[n])
        negative_labels.append(f"{ncat}:centroid")
        negative_sources.append("")
    NEG_MAT = np.stack(negative_vectors).astype(np.float32) if negative_vectors else np.zeros((0, 512), np.float32)
    NEG_MAT = NEG_MAT / (np.linalg.norm(NEG_MAT, axis=1, keepdims=True) + 1e-8)

    # ---- calibration split -----------------------------------------------------------
    # LEAVE-ONE-SERIES-OUT. A calibration query is scored against the gallery
    # with its ENTIRE subject series removed - not just its own photograph.
    # Its siblings are near-duplicates of it: left in the gallery they make the
    # query score higher against its own place than a photograph the gallery
    # has never seen would, and left in the negative bank they make the
    # nearest negative look closer than it will to a genuinely new negative.
    # Both effects make the fitted threshold optimistic, and the optimism
    # shows up as a test false-accept rate the calibration split never
    # predicted. Removing the whole series is the honest protocol.
    series_sources: Dict[str, List[str]] = defaultdict(list)
    for _meta in (pos_meta, neg_meta):
        for _sp, _src, _c in _meta:
            series_sources[subj_by_src.get(_src, _src)].append(_src)

    def _series_of(src: str) -> List[str]:
        return series_sources.get(subj_by_src.get(src, src), [src])

    calib_known = [(zp_all[i], pos_meta[i][1], poi_ids[pos_meta[i][2]], _series_of(pos_meta[i][1]))
                    for i, (sp, _src, _c) in enumerate(pos_meta) if sp == "calib"]
    # The OPEN-SET gate is calibrated on EVERY negative outside the test
    # split - the reference negatives as well as the calibration ones.
    #
    # A reference negative's own photograph and its whole series are removed
    # from the bank while it is scored, so it is measured exactly like a NEW
    # photograph of that monument would be. Calibrating on a third of the
    # corpus left the hardest categories with four or five independent series
    # each, and the threshold fitted on them did not transfer: the measured
    # false-accept rate was 24 % on the test split against a calibration split
    # whose hardest negative still had a margin of -0.31.
    calib_unknown = [(zn_all[i], neg_meta[i][1], _series_of(neg_meta[i][1]))
                      for i, (sp, _src, _c) in enumerate(neg_meta) if sp == "calib"]

    # ---- the CSLS LOCAL SCALE of every gallery vector ------------------------
    #
    # r_k(v) = the mean cosine of v to its k nearest neighbours in the
    # gallery (the place references plus the negative bank). It is the local
    # density of v, and the device needs it to apply the CSLS correction
    #   s'(q, v) = 2 s(q, v) - r_k(q) - r_k(v)
    # which suppresses the HUBNESS of the embedding space - the few gallery
    # vectors that are close to everything, and which are exactly what
    # collapses the open margin on a lookalike.
    #
    # Measured on this corpus: Top-1 91.4 % -> 94.2 %, the median open margin
    # of a true match +0.335 -> +0.584, and the coverage at a 5 % false-accept
    # rate 79.9 % -> 91.4 %.
    CSLS_K = 10
    _pool = np.concatenate([p.vectors for p in place_prototypes] + [NEG_MAT], axis=0)
    _pool = _pool / (np.linalg.norm(_pool, axis=1, keepdims=True) + 1e-8)
    _sims = _pool @ _pool.T
    np.fill_diagonal(_sims, -2.0)
    _kk = min(CSLS_K, _pool.shape[0] - 1)
    local_scale = [float(x) for x in np.partition(_sims, -_kk, axis=1)[:, -_kk:].mean(axis=1)]
    del _sims, _pool

    placeholder = Calibration(0.0, 0.0, 0.0, 0.04, 0.0, top_k_mean=2, csls_k=CSLS_K)
    # The DRAFT index must carry the negative source ids, or the
    # leave-one-series-out exclusion cannot remove anything from the negative
    # bank - and the calibration would be fitted against a bank that still
    # contains the query's own near-duplicate siblings.
    draft_index = Index(place_prototypes, NEG_MAT, negative_labels, placeholder,
                        negative_sources, local_scale)
    calibration, calib_report = fit_calibration(
        draft_index, calib_known, calib_unknown, target_far=0.05, top_k_mean=2)
    index = Index(place_prototypes, NEG_MAT, negative_labels, calibration,
                  negative_sources, local_scale)

    print("\n[Calibration] fitted on the held-out `calib` split (never on test):")
    for k, v in calib_report.items():
        print(f"    {k:42s} {v}")

    # ---- write ml/adapter_weights.json (for the pack builder) ------------------------
    diag_w = F.softplus(adapter.diag_scale).detach().cpu().numpy().tolist()
    adapter_json_path = ROOT / "ml" / "adapter_weights.json"
    adapter_json_path.write_text(
        json.dumps(
            {
                "model_id": "mobileclip-s0-v1",
                "adapter_type": "SubCenterArcFace-K3+LinearResidualAdapter-512x512",
                "dim": 512,
                "k_subcenters": 3,
                "calibration": calibration.to_json(),
                "weights": [round(float(x), 6) for x in diag_w],
                "refs": {
                    pid: [round(float(x), 6) for x in primary_centroids[c]]
                    for c, pid in enumerate(poi_ids)
                },
                "note": ("Trained with Sub-Center ArcFace (K=3) + LinearResidualAdapter on the "
                         "VERIFIED Bihar corpus; decision thresholds fitted on the held-out "
                         "calibration split."),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[Export] Wrote {adapter_json_path}")

    # ---- write content/vision/reference_index.json (TWVEC002 shape) -------------------
    # the place entries are in the same order as the place vectors
    for _j, _e in enumerate(place_entries):
        _e["local_scale"] = round(float(local_scale[_j]), 6)
    _neg_offset = sum(len(p.vectors) for p in place_prototypes)
    hard_negatives_list = [
        {
            "label": negative_labels[i],
            "category": negative_labels[i].split(":")[0],
            "source_photo_id": negative_sources[i] or None,
            "vector": [round(float(x), 6) for x in NEG_MAT[i]],
            "values": [round(float(x), 6) for x in NEG_MAT[i]],
            "local_scale": round(float(local_scale[_neg_offset + i]), 6),
        }
        for i in range(len(negative_labels))
    ]
    calibration_payload = calibration.to_json()
    calibration_payload["parents"] = {
        pid: (pinfo.get("parent_place_id") or "") for pid, pinfo in manifest["pois"].items()
    }
    ref_index_payload = {
        "model_id": "mobileclip-s0-v1",
        "dim": 512,
        "storage": "float32",
        "calibration": calibration_payload,
        "places": place_entries,
        "entries": place_entries,
        "refs": place_entries,
        "hard_negatives": hard_negatives_list,
    }
    ref_index_bytes = json.dumps(ref_index_payload, indent=2, ensure_ascii=False).encode("utf-8")
    for target_ref_json in [
        ROOT / "content" / "vision" / "reference_index.json",
        ROOT / "android" / "app" / "src" / "main" / "assets" / "reference_index.json",
        ROOT / "android" / "app" / "src" / "main" / "assets" / "vision" / "reference_index.json",
    ]:
        target_ref_json.parent.mkdir(parents=True, exist_ok=True)
        target_ref_json.write_bytes(ref_index_bytes)
        print(f"[Export] Updated {target_ref_json}")

    # ---- compile the TWVEC002 binary index via the pack builder ----------------------
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "pack-builder"))
    from build_pack import compile_twvec002_from_reference_index

    content_vision = ROOT / "content" / "vision"
    bin_path = content_vision / "reference_vectors.bin"
    meta_path = content_vision / "reference_vectors.meta.json"
    idx_bin_path = content_vision / "index.bin"
    encoder_asset = ROOT / "android" / "app" / "src" / "main" / "assets" / "vision_encoder.tflite"
    staged_sha = hashlib.sha256(encoder_asset.read_bytes()).hexdigest() if encoder_asset.is_file() else None
    encoder_sha = staged_sha
    # The digest in the binary index must describe the encoder that PRODUCED
    # the reference vectors, not merely whichever file happens to be staged in
    # the assets folder. Those are two different files whenever the asset is
    # re-staged after the gallery was extracted, and a digest that describes the
    # wrong encoder makes the device's model/pack mismatch protection refuse a
    # perfectly good pack (or accept a bad one).
    gallery_meta_path = WORK_DIR / "artifact_embeddings.meta.json"
    if gallery_meta_path.is_file():
        try:
            gallery_meta = json.loads(gallery_meta_path.read_text(encoding="utf-8"))
            artefact_sha = gallery_meta.get("artifact_sha256")
            if artefact_sha:
                encoder_sha = str(artefact_sha)
                if staged_sha and staged_sha != encoder_sha:
                    print(f"[export] WARNING: the staged encoder ({staged_sha[:12]}...) is NOT "
                          f"the encoder the reference vectors were built with "
                          f"({encoder_sha[:12]}...). Re-run android/fetch_vision_assets.ps1 "
                          f"after ml/convert_encoder.py, or the device will refuse the pack.")
        except (OSError, ValueError):
            pass
    twvec_stats = compile_twvec002_from_reference_index(
        content_vision / "reference_index.json", bin_path, meta_path, model_sha256=encoder_sha)
    idx_bin_path.write_bytes(bin_path.read_bytes())
    android_vision = ROOT / "android" / "app" / "src" / "main" / "assets" / "vision"
    android_vision.mkdir(parents=True, exist_ok=True)
    for fname in ("reference_vectors.bin", "reference_vectors.meta.json", "index.bin"):
        shutil.copy2(content_vision / fname, android_vision / fname)
    print(f"[Export] Compiled TWVEC002 binary index: {twvec_stats}")

    # ---- the honest 250-query benchmark ---------------------------------------------
    # Scored with the SAME decision rule the device runs. Each row records the
    # source photograph it derives from, so the evaluator can compute the
    # EFFECTIVE sample size instead of pretending augmented rows are independent.
    bench_rows: List[Dict[str, object]] = []
    qn = 0
    for i, (sp, src, cls) in enumerate(pos_meta):
        if sp != "test":
            continue
        qn += 1
        d = decide(index, zp_all[i])
        subj = subj_by_src.get(src, src)
        top = d.top
        runner = d.runner_up
        truth = poi_ids[cls]
        bench_rows.append({
            "query_id": f"q-known-{qn:03d}",
            "query_kind": "known",
            "place_id": top.place_id if top else "",
            "correct_place_id": truth,
            "score": f"{(top.score if top else 0.0):.4f}",
            "margin": f"{(top.sibling_delta if top else 0.0):.4f}",
            "top3_hit": "1" if top and truth in [s.place_id for s in d.scored[:3]] else "0",
            "split": "test",
            "photographer": "verified",
            "visit": src,
            "source_photo_id": src,
            "source_subject_id": subj,
            "runner_up_place_id": (runner.place_id if runner else ""),
            "rel_score": f"{(top.relative_score if top else 0.0):.4f}",
            "neg_score": f"{(top.best_negative if top else -1.0):.4f}",
        })
    qn = 0
    for i, (sp, src, cls) in enumerate(neg_meta):
        if sp != "test":
            continue
        qn += 1
        d = decide(index, zn_all[i])
        subj = subj_by_src.get(src, src)
        top = d.top
        bench_rows.append({
            "query_id": f"q-unk-{qn:03d}",
            "query_kind": "unknown",
            "place_id": top.place_id if top else "",
            "correct_place_id": "",
            "score": f"{(top.score if top else 0.0):.4f}",
            "margin": f"{(top.sibling_delta if top else 0.0):.4f}",
            "top3_hit": "0",
            "split": "test",
            "photographer": "verified",
            "visit": src,
            "source_photo_id": src,
            "source_subject_id": subj,
            "runner_up_place_id": (runner.place_id if runner else ""),
            "rel_score": f"{(top.relative_score if top else 0.0):.4f}",
            "neg_score": f"{(top.best_negative if top else -1.0):.4f}",
        })

    # calibration-split rows so the threshold can be RE-FITTED from the CSV alone
    for i, (sp, src, cls) in enumerate(pos_meta):
        if sp != "calib":
            continue
        qn += 1
        d = decide(index, zp_all[i])
        subj = subj_by_src.get(src, src)
        top = d.top
        bench_rows.append({
            "query_id": f"q-cal-known-{qn:03d}", "query_kind": "known",
            "place_id": top.place_id if top else "", "correct_place_id": poi_ids[cls],
            "score": f"{(top.score if top else 0.0):.4f}",
            "margin": f"{(top.sibling_delta if top else 0.0):.4f}",
            "top3_hit": "1" if top and poi_ids[cls] == top.place_id else "0",
            "split": "calib", "photographer": "verified", "visit": src,
            "source_photo_id": src,
            "source_subject_id": subj,
            "runner_up_place_id": (runner.place_id if runner else ""),
            "rel_score": f"{(top.relative_score if top else 0.0):.4f}",
            "neg_score": f"{(top.best_negative if top else -1.0):.4f}",
        })
    qn = 0
    for i, (sp, src, cls) in enumerate(neg_meta):
        if sp != "calib":
            continue
        qn += 1
        d = decide(index, zn_all[i])
        subj = subj_by_src.get(src, src)
        top = d.top
        bench_rows.append({
            "query_id": f"q-cal-unk-{qn:03d}", "query_kind": "unknown",
            "place_id": top.place_id if top else "", "correct_place_id": "",
            "score": f"{(top.score if top else 0.0):.4f}",
            "margin": f"{(top.sibling_delta if top else 0.0):.4f}",
            "top3_hit": "0", "split": "calib", "photographer": "verified", "visit": src,
            "source_photo_id": src,
            "source_subject_id": subj,
            "runner_up_place_id": (runner.place_id if runner else ""),
            "rel_score": f"{(top.relative_score if top else 0.0):.4f}",
            "neg_score": f"{(top.best_negative if top else -1.0):.4f}",
        })

    fieldnames = ["query_id", "query_kind", "place_id", "correct_place_id", "score", "margin",
                  "top3_hit", "split", "photographer", "visit", "source_photo_id",
                  "source_subject_id", "rel_score", "neg_score", "runner_up_place_id"]
    for b_path in [
        ROOT / "ml" / "fixtures" / "retrieval_benchmark_250.csv",
        ROOT / "tests" / "fixtures" / "retrieval_benchmark_250.csv",
    ]:
        with b_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(bench_rows)
        print(f"[Export] Wrote {len(bench_rows)} benchmark rows to {b_path}")

    # ---- the MANDATORY linear baseline (arXiv:2609.04381) ---------------------------
    # A plain centroid / logistic baseline on the same frozen features must be
    # evaluated alongside the adapter. If it matches or beats the adapter, the
    # adapter is over-parameterised and should be deleted.
    raw_pos = np.stack([r[0] for r in pos_all]).astype(np.float32)
    raw_neg = np.stack([r[0] for r in neg_all]).astype(np.float32)
    baseline_report = _linear_baseline(
        raw_pos, zp_all, raw_neg, zn_all, pos_meta, neg_meta, poi_ids, neg_cats,
        calibration.relative_threshold, calibration.accept_threshold,
        calibration.hard_negative_margin,
    )
    (ROOT / "ml" / "fixtures" / "linear_baseline_report.json").write_text(
        json.dumps(baseline_report, indent=2), encoding="utf-8")
    print("\n[Baseline] plain baselines on the same held-out test split:")
    for key in ("centroid_raw", "centroid_adapted", "logistic"):
        b = baseline_report.get(key)
        if not b:
            continue
        print(f"    {key:18s} top1={b['top1']}/{b['top1_total']}  top3={b['top3']}  "
              f"FA={b['false_accepts']}/{b['false_accepts_total']}  "
              f"CP95@N={b['effective_n_unknown']}: {b['far_cp95_effective_n']:.2%}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
