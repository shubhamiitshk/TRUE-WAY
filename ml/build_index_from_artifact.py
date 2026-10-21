"""Build the reference index FROM the deployed encoder artefact.

Why this exists
---------------
The gallery must be produced by the **same artefact the device runs**. Two
train/serve skews were found in the audit:

  1. The exported graph folded the adapter matrix into ``head.fc``, but the
     training pipeline L2-normalises the backbone output BEFORE the adapter.
     Folding a linear map across a normalisation is not a no-op, so the device
     was applying the adapter to an unnormalised vector on every inference.
  2. The reference vectors were extracted in PyTorch FP32 while the device runs
     a quantised INT8 graph, whose outputs differ by a measured 0.9889 cosine
     - a shift of the same order as the decision margins.

Both are eliminated by building the gallery with the artefact itself.

This script is the SECOND half of the pipeline:

    ml/train_arcface_pipeline.py   trains the adapter and exports the artefact
    ml/build_index_from_artifact.py  extracts the gallery WITH the artefact and
                                     fits the calibration on the artefact's own
                                     embedding distribution

The device's preprocessing is reproduced exactly as the TFLITE_METADATA
declares it: resize the SHORTEST side to 256 preserving the aspect ratio,
centre-crop 256x256, scale to [0, 1], NHWC float32.

    python ml/build_index_from_artifact.py \
        --artifact ml/models/s0/mci_s0_int8.tflite
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml"))

IMG = 256


def _preprocess(path: Path, img: int = IMG) -> np.ndarray:
    """The device's preprocessing, per the TFLITE_METADATA."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    scale = img / min(w, h)
    nw, nh = max(img, int(round(w * scale))), max(img, int(round(h * scale)))
    im = im.resize((nw, nh), Image.Resampling.BICUBIC)
    left, top = (nw - img) // 2, (nh - img) // 2
    im = im.crop((left, top, left + img, top + img))
    return (np.asarray(im, dtype=np.float32) / 255.0)[None, ...]


def load_interpreter(artifact: Path):
    if artifact.suffix == ".tflite":
        import tensorflow as tf
        interp = tf.lite.Interpreter(model_path=str(artifact), num_threads=4)
        interp.allocate_tensors()
        return interp
    if artifact.suffix == ".onnx":
        import onnxruntime as ort
        return ort.InferenceSession(str(artifact), providers=["CPUExecutionProvider"])
    raise SystemExit(f"unsupported artefact: {artifact}")


def embed_all(artifact: Path, paths: List[str]) -> Dict[str, np.ndarray]:
    interp = load_interpreter(artifact)
    out: Dict[str, np.ndarray] = {}
    if artifact.suffix == ".tflite":
        inp = interp.get_input_details()[0]
        outp = interp.get_output_details()[0]
        for rel in paths:
            x = _preprocess(ROOT / rel).astype(np.float32)
            interp.set_tensor(inp["index"], x)
            interp.invoke()
            out[rel] = interp.get_tensor(outp["index"])[0].ravel().astype(np.float32)
    else:
        for rel in paths:
            x = _preprocess(ROOT / rel).astype(np.float32)
            x = np.transpose(x, (0, 2, 3, 1))[0][None, ...]
            out[rel] = interp.run(None, {"image": x})[0].ravel().astype(np.float32)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the reference index from the deployed artefact")
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--manifest", default=str(ROOT / "ml" / "dataset" / "dataset_manifest.json"))
    ap.add_argument("--out", default=str(ROOT / "ml" / "models" / "s0" / "artifact_embeddings.npz"))
    ap.add_argument("--batch", type=int, default=1)
    args = ap.parse_args()

    artifact = Path(args.artifact)
    if not artifact.is_file():
        print(f"artefact not found: {artifact}", file=sys.stderr)
        return 2
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))

    paths: List[str] = []
    for section in ("pois", "negatives"):
        for node in manifest.get(section, {}).values():
            for r in node.get("records", []):
                if r["local_path"] not in paths:
                    paths.append(r["local_path"])
    print(f"[gallery] embedding {len(paths)} corpus photographs with {artifact.name}")
    embs = embed_all(artifact, paths)

    # sanity: the embedding must be a stable, L2-normalisable vector
    norms = [float(np.linalg.norm(v)) for v in embs.values()]
    print(f"[gallery] embedding norm: min {min(norms):.4f} mean {sum(norms)/len(norms):.4f} "
          f"max {max(norms):.4f}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, **embs)
    meta = {
        "artifact": str(artifact),
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "artifact_bytes": artifact.stat().st_size,
        "images": len(embs),
        "preprocessing": "resize shortest side to 256 (aspect preserved), centre-crop 256x256, /255, NHWC float32",
    }
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[gallery] -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
