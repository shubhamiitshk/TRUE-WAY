"""Exports golden decision vectors for the CROSS-LANGUAGE PARITY TEST.

The workstation evaluator (`ml/vision_index.py`) and the Android device
(`BinaryVectorIndex.evaluate`) must make the SAME decision for the SAME
embedding. They are two implementations of one rule, and the rule is the
product. This script freezes a set of queries and the decisions both sides
must produce, so CI catches a drift the moment either side changes.

    python ml/export_parity_vectors.py

Writes `android/app/src/test/resources/decision_parity.json`.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml"))
from vision_index import Calibration, Index, PlacePrototypes, decide  # noqa: E402


def load_index() -> Index:
    spec = importlib.util.spec_from_file_location("vi", ROOT / "ml" / "vision_index.py")
    vi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vi)
    data = json.loads((ROOT / "content" / "vision" / "reference_index.json").read_text(encoding="utf-8"))
    cal = vi.Calibration.from_json(data.get("calibration", {}))

    grouped: dict = {}
    for e in data.get("places") or data.get("entries") or data.get("refs") or []:
        grouped.setdefault(e["place_id"], []).append(e)
    places = []
    for pid, items in grouped.items():
        head = items[0]
        M = np.stack([np.array(i.get("vector") or i.get("values"), dtype=np.float32) for i in items])
        M = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-8)
        places.append(vi.PlacePrototypes(
            place_id=pid,
            parent_place_id=head.get("parent_place_id"),
            viewpoint_tag=str(head.get("viewpoint_tag", "")),
            distinguishing_hint=str(head.get("distinguishing_hint", "")),
            vectors=M,
            source_ids=[str(i.get("source_photo_id") or "") for i in items],
        ))
    negs = []
    labels = []
    neg_sources = []
    neg_scales = []
    for n in data.get("hard_negatives", []) or []:
        v = n.get("vector") or n.get("values") or []
        if not v:
            continue
        negs.append(np.array(v, dtype=np.float32))
        labels.append(str(n.get("label", "")))
        neg_sources.append(str(n.get("source_photo_id") or ""))
        neg_scales.append(float(n.get("local_scale", 0.0)))
    NEG = np.stack(negs) if negs else np.zeros((0, 512), np.float32)
    NEG = NEG / (np.linalg.norm(NEG, axis=1, keepdims=True) + 1e-8)
    # The CSLS local scale, in the same order as the gallery: the place
    # references first, then the negative bank. Without it the index would
    # score on the RAW cosine while the calibration in the pack was fitted on
    # the CORRECTED scale - and every case would abstain.
    local_scale = [float(e.get("local_scale", 0.0)) for e in
                   (data.get("places") or data.get("entries") or [])] + neg_scales
    return vi.Index(places, NEG, labels, cal, neg_sources, local_scale)


def main() -> int:
    index = load_index()
    manifest = json.loads((ROOT / "ml" / "dataset" / "dataset_manifest.json").read_text(encoding="utf-8"))
    emb = np.load(ROOT / "ml" / "models" / "s0" / "extracted_embeddings_512.npz")

    ck_path = ROOT / "ml" / "models" / "s0" / "arcface_adapter.pt"
    if not ck_path.is_file():
        print("arcface_adapter.pt missing — run ml/train_arcface_pipeline.py first", file=sys.stderr)
        return 2
    import torch
    spec = importlib.util.spec_from_file_location("tap", ROOT / "ml" / "train_arcface_pipeline.py")
    tap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tap)
    ck = torch.load(ck_path, map_location="cpu", weights_only=False)
    ad = tap.LinearResidualAdapter(dim=512, alpha_init=0.35)
    ad.load_state_dict(ck["adapter_state_dict"])
    ad.eval()

    def src(rec):
        return rec.get("source_photo_id") or rec.get("original_url") or rec.get("local_path")

    cases = []
    # a spread of knowns and unknowns from the held-out test split
    for section, kind in (("pois", "known"), ("negatives", "unknown")):
        for cid, node in manifest.get(section, {}).items():
            for rec in node.get("records", []):
                if rec.get("split") != "test":
                    continue
                path = rec.get("local_path")
                if path not in emb.files:
                    continue
                with torch.no_grad():
                    z = ad(torch.from_numpy(emb[path][None, :])).detach().numpy()[0]
                # Round the query to the precision the fixture stores, and
                # decide on THAT value, so both sides see identical inputs.
                z = np.array([round(float(x), 6) for x in z], dtype=np.float32)
                d = decide(index, z)
                top = d.top
                cases.append({
                    "id": f"{kind}:{cid}:{src(rec)[:24]}",
                    "kind": kind,
                    "truth": cid if kind == "known" else None,
                    "query": [round(float(x), 6) for x in z],
                    "expected": {
                        "accepted": d.accepted,
                        "reason": d.reason,
                        "place_id": top.place_id if top else None,
                        "score": round(top.score, 5) if top else None,
                        "open_margin": round(top.open_margin, 5) if top else None,
                        "place_margin": round(top.place_margin, 5) if top else None,
                        "best_negative": round(top.best_negative, 5) if top else None,
                    },
                })

    payload = {
        "note": ("Golden decision vectors. The Python evaluator (ml/vision_index.py) and the "
                 "Android device (BinaryVectorIndex.evaluate) must agree on every case. "
                 "Generated by ml/export_parity_vectors.py."),
        "calibration": index.calibration.to_json(),
        "cases": cases,
    }
    out = ROOT / "android" / "app" / "src" / "test" / "resources" / "decision_parity.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    accepted = sum(1 for c in cases if c["expected"]["accepted"])
    print(f"-> wrote {out}")
    print(f"   {len(cases)} cases ({accepted} accepted, {len(cases)-accepted} abstained)")
    print(f"   size: {out.stat().st_size/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
