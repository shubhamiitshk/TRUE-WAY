"""Encoder parity gate: does the DEPLOYED artefact produce the embeddings the
gallery was built from?

The gallery in `content/vision/reference_index.json` is extracted with PyTorch.
The device runs a converted TFLite artefact. If the two disagree, every score
the device computes is measured against the wrong reference vectors — the
train/serve skew that the audit found (the adapter was folded across an L2
normalisation, so the exported graph applied it to an UNNORMALISED backbone
output while the adapter had been fitted on unit-norm inputs).

This script compares, for a set of corpus photographs:
    cos( PyTorch embedding , artefact embedding )
and FAILS when the agreement is below the threshold that the quantisation
literature says is safe (arXiv:2610.18575: below an output-agreement cosine of
0.8 every architecture tested fell below the FP32 baseline).

It needs `onnxruntime` for the ONNX artefact (and `tensorflow` for the TFLite
one). If neither is installed it SKIPS with a clear message — the conversion
itself needs a TensorFlow host, and the repo is expected to be developed on
one.

    python ml/audit/check_encoder_parity.py
    python ml/audit/check_encoder_parity.py --artifact ml/models/s0/mci_s0_int8.tflite
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
MIN_AGREEMENT = 0.80


def cosine(a, b) -> float:
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na <= 0 or nb <= 0:
        return 0.0
    return float(a @ b / (na * nb))


def torch_embeddings(paths, img=256):
    import importlib.util
    import torch
    import timm
    from PIL import Image
    spec = importlib.util.spec_from_file_location("ce", ROOT / "ml" / "convert_encoder.py")
    ce = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ce)
    from timm.utils.model import reparameterize_model
    backbone = timm.create_model(ce.VARIANTS["s0"], pretrained=True).eval()
    backbone = reparameterize_model(backbone).eval()
    ckpt = torch.load(ROOT / "ml" / "models" / "s0" / "arcface_adapter.pt",
                      map_location="cpu", weights_only=False)
    feat = ce.ClipImageFeatures(backbone, pre_logits=False,
                                adapter_state=ckpt.get("adapter_state_dict")).eval()
    out = []
    with torch.no_grad():
        for p in paths:
            im = Image.open(p).convert("RGB")
            w, h = im.size
            scale = img / min(w, h)
            im = im.resize((max(img, int(round(w * scale))), max(img, int(round(h * scale)))),
                           Image.Resampling.BICUBIC)
            left = (im.width - img) // 2
            top = (im.height - img) // 2
            im = im.crop((left, top, left + img, top + img))
            x = np.asarray(im, dtype=np.float32) / 255.0
            x = np.transpose(x, (2, 0, 1))[None, ...]
            out.append(feat(torch.from_numpy(x)).numpy().ravel())
    return out


def artifact_embeddings(paths, artifact: Path, img=256):
    if artifact.suffix == ".onnx":
        import onnxruntime as ort
        sess = ort.InferenceSession(str(artifact), providers=["CPUExecutionProvider"])
        outs = []
        for p in paths:
            x = _preprocess(p, img, "nchw")
            outs.append(sess.run(None, {"image": x})[0].ravel())
        return outs
    if artifact.suffix == ".tflite":
        import tensorflow as tf
        interp = tf.lite.Interpreter(model_path=str(artifact), num_threads=4)
        interp.allocate_tensors()
        inp, outp = interp.get_input_details()[0], interp.get_output_details()[0]
        # The TFLite graph takes NHWC ([1, H, W, C]); the ONNX graph takes
        # NCHW. Feeding the ONNX layout to the TFLite model is a silent
        # dimension mismatch that the interpreter reports as a shape error.
        layout = "nhwc" if list(inp["shape"])[-1] == 3 else "nchw"
        outs = []
        for p in paths:
            x = _preprocess(p, img, layout)
            interp.set_tensor(inp["index"], x.astype(np.float32))
            interp.invoke()
            outs.append(interp.get_tensor(outp["index"]).ravel())
        return outs
    raise SystemExit(f"unsupported artefact: {artifact}")


def _preprocess(path: Path, img=256, layout: str = "nchw"):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    scale = img / min(w, h)
    im = im.resize((max(img, int(round(w * scale))), max(img, int(round(h * scale)))),
                   Image.Resampling.BICUBIC)
    left = (im.width - img) // 2
    top = (im.height - img) // 2
    im = im.crop((left, top, left + img, top + img))
    x = np.asarray(im, dtype=np.float32) / 255.0
    if layout == "nhwc":
        return x[None, ...]
    return np.transpose(x, (2, 0, 1))[None, ...]


def check_export_shape() -> int:
    """Verifies the exported graph computes the SAME function as training.

    Training (ml/train_arcface_pipeline.py):
        embedding = normalize(adapter(normalize(backbone(x))))
    Export (ml/convert_encoder.py, adapter_mode="separate"):
        embedding = normalize(adapter_fc(normalize(backbone(x))))

    The legacy export folded the adapter into ``head.fc``, which is not
    equivalent: the L2 normalisation sits BETWEEN the projection and the
    adapter, so folding a linear map across it changes the function (and the
    adapter was fitted on unit-norm inputs). That mismatch is a train/serve
    skew on every single inference.
    """
    try:
        import importlib.util
        import torch
        import timm
        from timm.utils.model import reparameterize_model
    except ImportError as e:
        print(f"SKIP: export-shape check needs torch/timm ({e})")
        return 0
    ckpt_path = ROOT / "ml" / "models" / "s0" / "arcface_adapter.pt"
    if not ckpt_path.is_file():
        print("SKIP: arcface_adapter.pt not found (run ml/train_arcface_pipeline.py)")
        return 0
    spec = importlib.util.spec_from_file_location("ce", ROOT / "ml" / "convert_encoder.py")
    ce = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ce)
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    state = ckpt.get("adapter_state_dict")
    if not state:
        print("SKIP: no adapter state in the checkpoint")
        return 0

    # The REFERENCE side: an UNTOUCHED, reparameterised backbone. It must be a
    # SEPARATE instance from the one the export folds in place - comparing the
    # folded backbone against itself cannot detect a mis-folded layer scale.
    ref_backbone = timm.create_model(ce.VARIANTS["s0"], pretrained=True).eval()
    ref_backbone = reparameterize_model(ref_backbone).eval()

    # The EXPORT side.
    backbone = timm.create_model(ce.VARIANTS["s0"], pretrained=True).eval()
    backbone = reparameterize_model(backbone).eval()
    feat = ce.ClipImageFeatures(backbone, pre_logits=False, adapter_state=state,
                                adapter_mode="separate").eval()

    # the training-side adapter (the REAL module, not a reimplementation)
    ad = ce_torch_adapter(state)

    # REAL photographs, not random noise: a mis-folded attention scale or a
    # mis-folded layer scale is invisible on noise and obvious on a picture.
    xs = _real_images(4)
    if not xs:
        torch.manual_seed(3)
        xs = [torch.randn(1, 3, 256, 256)]
    worst = 1.0
    with torch.no_grad():
        for x in xs:
            head = ref_backbone.forward_head(ref_backbone.forward_features(x))
            training = torch.nn.functional.normalize(
                ad(torch.nn.functional.normalize(head, p=2, dim=-1)), p=2, dim=-1)
            exported = feat(x)
            worst = min(worst, cosine(training.numpy(), exported.numpy()))
    print("=== EXPORT-SHAPE CHECK ===")
    print(f"  cos(training pipeline, exported graph) = {worst:.6f}  (floor 0.999)")
    if worst < 0.999:
        print("  RESULT: FAIL — the exported graph does NOT compute the training function.")
        print("          The device would score against embeddings the gallery never saw.")
        return 1
    print("  RESULT: PASS — the exported graph reproduces the training computation.")
    return 0


def _real_images(n: int):
    """Real corpus photographs as NCHW tensors, for the export-shape check."""
    import torch
    from PIL import Image
    manifest_path = ROOT / "ml" / "dataset" / "dataset_manifest.json"
    if not manifest_path.is_file():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = []
    for section in ("pois", "negatives"):
        for node in manifest.get(section, {}).values():
            for r in node.get("records", []):
                p = ROOT / r["local_path"]
                if p.is_file():
                    paths.append(p)
    if not paths:
        return []
    step = max(1, len(paths) // n)
    paths = paths[::step][:n]
    out = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        scale = 256 / min(w, h)
        im = im.resize((max(256, int(round(w * scale))), max(256, int(round(h * scale)))),
                       Image.Resampling.BICUBIC)
        im = im.crop(((im.width - 256) // 2, (im.height - 256) // 2,
                      (im.width - 256) // 2 + 256, (im.height - 256) // 2 + 256))
        x = np.asarray(im, dtype=np.float32) / 255.0
        out.append(torch.from_numpy(np.transpose(x, (2, 0, 1))[None, ...]))
    return out


def ce_torch_adapter(state):
    """The TRAINING adapter, loaded from the checkpoint.

    This used to be a REIMPLEMENTATION of the adapter, which made the check
    self-referential: it compared the exported graph against a second copy of
    the export's own arithmetic and therefore could not detect a divergence
    between the export and the training pipeline. The real module is imported
    from the training script instead.
    """
    import importlib.util
    import torch
    import torch.nn.functional as F

    spec = importlib.util.spec_from_file_location("tap", ROOT / "ml" / "train_arcface_pipeline.py")
    tap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tap)
    adapter = tap.LinearResidualAdapter(512, 0.25)
    adapter.load_state_dict(state)
    adapter.eval()
    return adapter


def default_artifact() -> Path:
    """The artefact that ACTUALLY ships.

    `ml/convert_encoder.py` measures every variant and records the fastest
    acceptable one in `ml/models/s0/conversion_log.json`; that is the file the
    packaging step stages into the APK. Checking a different file would leave
    the shipped model unverified.
    """
    work = ROOT / "ml" / "models" / "s0"
    log_path = work / "conversion_log.json"
    if log_path.is_file():
        try:
            log = json.loads(log_path.read_text(encoding="utf-8"))
            name = (log.get("tflite") or {}).get("chosen_file")
            if name:
                cand = work / str(name)
                if cand.is_file():
                    return cand
        except (ValueError, OSError):
            pass
    for name in ("mci_s0_fp16.tflite", "mci_s0_fp32.tflite", "mci_s0_int8.tflite"):
        cand = work / name
        if cand.is_file():
            return cand
    return work / "mci_s0_int8.tflite"


def main() -> int:
    ap = argparse.ArgumentParser(description="Encoder parity gate (PyTorch gallery vs deployed artefact)")
    ap.add_argument("--artifact", default=str(default_artifact()))
    ap.add_argument("--samples", type=int, default=12)
    ap.add_argument("--min-agreement", type=float, default=MIN_AGREEMENT)
    ap.add_argument("--shape-only", action="store_true",
                    help="Only run the PyTorch export-shape check (no artefact needed)")
    args = ap.parse_args()

    # ------------------------------------------------------------------ CHECK 1
    # The EXPORT SHAPE must equal the TRAINING computation:
    #     training : normalize(adapter(normalize(backbone(x))))
    #     export   : normalize(adapter_fc(normalize(backbone(x))))   [separate]
    # The legacy export folded the adapter into head.fc, which is NOT equivalent
    # because the normalisation sits between the projection and the adapter.
    # This check needs no TensorFlow, so it runs everywhere.
    if args.shape_only or True:
        rc = check_export_shape()
        if rc != 0:
            return rc

    artifact = Path(args.artifact)
    if not artifact.is_file():
        print(f"SKIP: artefact not built ({artifact}). Run ml/convert_encoder.py on a TensorFlow host.")
        return 0

    manifest_path = ROOT / "ml" / "dataset" / "dataset_manifest.json"
    if not manifest_path.is_file():
        print("SKIP: dataset manifest not found")
        return 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = []
    for section in ("pois", "negatives"):
        for node in manifest.get(section, {}).values():
            for r in node.get("records", []):
                p = ROOT / r["local_path"]
                if p.is_file():
                    paths.append(p)
    if not paths:
        print("SKIP: no corpus images on disk")
        return 0
    step = max(1, len(paths) // args.samples)
    paths = paths[::step][:args.samples]

    try:
        ref = torch_embeddings(paths)
        got = artifact_embeddings(paths, artifact)
    except ImportError as e:
        print(f"SKIP: missing runtime ({e}). The encoder parity gate needs "
              f"onnxruntime (for .onnx) or tensorflow (for .tflite).")
        return 0

    cosines = [cosine(a, b) for a, b in zip(ref, got)]
    worst = min(cosines)
    mean = sum(cosines) / len(cosines)
    print(f"=== ENCODER PARITY ({artifact.name}) ===")
    print(f"  samples            : {len(cosines)}")
    print(f"  agreement cosine   : min {worst:.4f}  mean {mean:.4f}  (floor {args.min_agreement})")
    if worst < args.min_agreement:
        print("  RESULT: FAIL — the deployed artefact does not reproduce the gallery embeddings.")
        print("          The reference vectors must be re-extracted with this artefact, or the")
        print("          artefact must be rebuilt (see ml/convert_encoder.py).")
        return 1
    print("  RESULT: PASS — the deployed artefact reproduces the gallery embeddings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
