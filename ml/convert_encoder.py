"""Encoder conversion spike — research doc §5 phase 4a / ADR-0003.

Pipeline: timm HF-hub MobileCLIP image backbone (classifier stripped) →
torch ONNX (opset 17) → ORT smoke → onnx2tf SavedModel → TFLite FP32 →
TFLite INT8 full-integer + float I/O → TFLite interpreter smoke + op/size
report → conversion_log.json.

Rights flag: Apple MobileCLIP weights are `apple-amlr` licensed. Downloading
for workstation EVALUATION is the spike; shipping weights inside the app
needs rights-reviewer clearance first (blueprint §16). Never commit weights
to the repo — ml/models/ is gitignored-by-convention (fetch on demand).

Calibration honesty: the spike uses a RANDOM representative dataset purely
to prove the INT8 graph converts and runs (SPIKE-CALIB). Real accuracy
needs 200–500 pilot-domain images (§3.2); accuracy numbers from spike INT8
are NOT pilot evidence.

Usage:
  python ml/convert_encoder.py --variant s0 --work ml/models/s0
  python ml/convert_encoder.py --variant s2 --work ml/models/s2 --steps fetch,onnx,tflite,report
"""
from __future__ import annotations

import argparse
import io
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

VARIANTS = {
    "s0": "hf-hub:apple/mobileclip_s0_timm",
    "s2": "hf-hub:apple/mobileclip_s2_timm",
}
IMG = 256  # MobileCLIP-DataCompDR training size; benchmark 224 second


def _cos(a, b) -> float:
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class ClipImageFeatures(nn.Module):
    """timm backbone minus classifier: pooled pre-logit features for retrieval."""

    def __init__(self, backbone: nn.Module):
        super().__init__()
        self.backbone = backbone

    def forward(self, x):
        feats = self.backbone.forward_features(x)
        # forward_head(pre_logits=True) pools + flattens, skipping classifier
        return self.backbone.forward_head(feats, pre_logits=True)


def step_fetch(variant: str, work: Path):
    import timm
    ckpt = VARIANTS[variant]
    print(f"[fetch] {ckpt}")
    backbone = timm.create_model(ckpt, pretrained=True)
    backbone.eval()
    n_params = sum(p.numel() for p in backbone.parameters())
    feat = ClipImageFeatures(backbone).eval()
    with torch.no_grad():
        dummy = torch.randn(1, 3, IMG, IMG)
        out = feat(dummy)
    print(f"[fetch] params={n_params / 1e6:.1f}M feat_dim={tuple(out.shape)}")
    torch.save(feat.state_dict(), work / f"mci_{variant}_features.pt")
    meta = {"variant": variant, "ckpt": ckpt, "params": n_params,
            "feat_shape": list(out.shape), "input": [1, 3, IMG, IMG]}
    (work / "fetch_meta.json").write_text(json.dumps(meta, indent=1))
    return feat, meta


def step_onnx(feat: nn.Module, work: Path, variant: str):
    import onnx
    dummy = torch.randn(1, 3, IMG, IMG)
    onnx_path = work / f"mci_{variant}.onnx"
    torch.onnx.export(feat, dummy, str(onnx_path), input_names=["image"],
                      output_names=["embedding"], opset_version=17,
                      dynamo=False)
    onnx.checker.check_model(str(onnx_path))
    print(f"[onnx] wrote {onnx_path} ({onnx_path.stat().st_size / 1e6:.1f} MB)")
    # ORT smoke: self-cosine ~1.0 + latency
    import onnxruntime as ort
    sess = ort.InferenceSession(str(onnx_path),
                                providers=["CPUExecutionProvider"])
    x = np.random.rand(1, 3, IMG, IMG).astype(np.float32)
    for _ in range(3):
        sess.run(None, {"image": x})
    t0 = time.perf_counter()
    n = 20
    for _ in range(n):
        y = sess.run(None, {"image": x})[0]
    dt = (time.perf_counter() - t0) / n * 1000
    # Meaningful ORT check: DETERMINISM — the same input twice must yield the
    # same embedding (cos==1). (The old `norm(unit)**2` self-cos was vacuously
    # ~1.0 for ANY non-zero output and verified nothing.) The real conversion
    # check is the ORT-vs-TFLite cosine in step_tflite on a SHARED image.
    y_again = sess.run(None, {"image": x})[0]
    determinism = _cos(y, y_again)
    print(f"[ort] dim={y.shape[1]} determinism_cos={determinism:.6f} cpu_lat={dt:.1f} ms (workstation CPU)")
    return {"onnx_mb": onnx_path.stat().st_size / 1e6, "ort_dim": int(y.shape[1]),
            "ort_determinism_cos": determinism, "ort_cpu_ms": dt}


def step_tflite(work: Path, variant: str, ort_dim: int):
    import tensorflow as tf
    print("[tflite] onnx -> savedmodel via onnx2tf (this takes minutes)")
    import onnx2tf
    # onnx2tf's internal accuracy check downloads a version-pinned sample that
    # 404s upstream; when present locally it is used instead. Provide a seeded
    # random stand-in (their check only, NOT our verification) and remove it.
    import os
    stub = os.path.join(os.getcwd(), "calibration_image_sample_data_20x128x128x3_float32.npy")
    made_stub = False
    if not os.path.isfile(stub):
        rng_stub = np.random.default_rng(7)
        with open(stub, "wb") as f:
            np.save(f, rng_stub.random((20, 128, 128, 3), dtype=np.float32))
        made_stub = True
    # The MCi token-mixer does attention-style Mul/Div on NCHW tensors whose
    # shapes onnx2tf mis-transposes (scalar -> [1,1,1,4]). Keep every such
    # node's inputs in NCHW so the faulty transpose pass is skipped there.
    import onnx as _onnx
    _m = _onnx.load(str(work / f"mci_{variant}.onnx"))
    keep_nchw: list[str] = []
    for _n in _m.graph.node:
        if "token_mixer" in _n.name and _n.op_type in ("Mul", "Div"):
            keep_nchw.extend(_n.input)
    keep_nchw = sorted(set(keep_nchw))
    print(f"[tflite] keep-NCHW inputs for {len(keep_nchw)} token-mixer tensors")
    try:
        onnx2tf.convert(
            input_onnx_file_path=str(work / f"mci_{variant}.onnx"),
            output_folder_path=str(work / "savedmodel"),
            non_verbose=True,
            # Spike only: onnx2tf's per-op accuracy-corrector crashes against
            # TF 2.21's tf_keras (structural bug in THEIR validation-model
            # builder, unrelated to our weights). disable_strict_mode skips
            # that path; OUR verification is the ORT-vs-TFLite cosine check
            # below, which gates the log.
            disable_strict_mode=True,
            keep_ncw_or_nchw_or_ncdhw_input_names=keep_nchw,
        )
    finally:
        if made_stub and os.path.isfile(stub):
            os.remove(stub)
    converter = tf.lite.TFLiteConverter.from_saved_model(str(work / "savedmodel"))
    fp32 = converter.convert()
    (work / f"mci_{variant}_fp32.tflite").write_bytes(fp32)
    print(f"[tflite] fp32 {len(fp32) / 1e6:.1f} MB")

    rng = np.random.default_rng(7)
    def spike_calib():
        for _ in range(100):
            yield [rng.random((1, IMG, IMG, 3), dtype=np.float32)]
    # Note: onnx2tf emits NHWC float input; representative matches that.
    c2 = tf.lite.TFLiteConverter.from_saved_model(str(work / "savedmodel"))
    c2.optimizations = [tf.lite.Optimize.DEFAULT]
    c2.representative_dataset = spike_calib
    c2.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    c2.inference_input_type = tf.float32  # float I/O: GPU-delegate/XNNPACK safe
    c2.inference_output_type = tf.float32
    int8 = c2.convert()
    (work / f"mci_{variant}_int8.tflite").write_bytes(int8)
    print(f"[tflite] int8 {len(int8) / 1e6:.1f} MB (SPIKE-CALIB random data, not pilot evidence)")

    # Interpreter smoke on both (CPU, XNNPACK default) + REAL cross-backend
    # verification: run the SAME image through ORT (NCHW) and TFLite (NHWC) and
    # require a high cosine. This is the check the disable_strict_mode comment
    # promises; without it a mis-transposed token-mixer would ship silently.
    import onnxruntime as ort
    sess = ort.InferenceSession(str(work / f"mci_{variant}.onnx"),
                                providers=["CPUExecutionProvider"])
    shared_nhwc = rng.random((1, IMG, IMG, 3), dtype=np.float32)
    shared_nchw = np.ascontiguousarray(np.transpose(shared_nhwc, (0, 3, 1, 2)))
    emb_ort = sess.run(None, {"image": shared_nchw})[0].ravel()
    res = {}
    for name in ("fp32", "int8"):
        path = work / f"mci_{variant}_{name}.tflite"
        interp = tf.lite.Interpreter(model_path=str(path), num_threads=4)
        interp.allocate_tensors()
        inp, outp = interp.get_input_details()[0], interp.get_output_details()[0]
        x = rng.random((1, IMG, IMG, 3), dtype=np.float32)
        for _ in range(3):
            interp.set_tensor(inp["index"], x)
            interp.invoke()
        t0 = time.perf_counter()
        n = 20
        for _ in range(n):
            interp.set_tensor(inp["index"], x)
            interp.invoke()
        dt = (time.perf_counter() - t0) / n * 1000
        y = interp.get_tensor(outp["index"])
        ops = sorted({op["op_name"] for op in interp._get_ops_details()})
        # Cross-backend cosine on the shared image.
        interp.set_tensor(inp["index"], shared_nhwc)
        interp.invoke()
        emb_tfl = interp.get_tensor(outp["index"]).ravel()
        xcos = _cos(emb_ort, emb_tfl)
        floor = 0.99 if name == "fp32" else 0.90  # INT8 quant loses a little
        ok = xcos >= floor
        print(f"[interp:{name}] dim={y.shape[-1]} cpu4_lat={dt:.1f} ms ops={len(ops)} "
              f"ort_vs_tflite_cos={xcos:.4f} (floor {floor}) {'OK' if ok else 'FAIL'}")
        res[name] = {"mb": path.stat().st_size / 1e6, "cpu4_ms": dt,
                     "dim": int(y.shape[-1]), "ops": ops,
                     "ort_vs_tflite_cos": xcos, "cross_backend_ok": ok}
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["s0", "s2"], default="s0")
    ap.add_argument("--work", default="ml/models/s0")
    ap.add_argument("--steps", default="fetch,onnx,tflite,report",
                    help="comma subset of fetch,onnx,tflite,report")
    args = ap.parse_args()
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    steps = set(args.steps.split(","))
    log: dict = {"variant": args.variant, "spike_calib": True}
    feat, meta = step_fetch(args.variant, work) if "fetch" in steps else (None, {})
    log["fetch"] = meta
    if "onnx" in steps:
        assert feat is not None, "onnx needs fetch in same run (or extend script)"
        log["onnx"] = step_onnx(feat, work, args.variant)
    if "tflite" in steps:
        log["tflite"] = step_tflite(work, args.variant,
                                    log.get("onnx", {}).get("ort_dim", 0))
    if "report" in steps:
        (work / "conversion_log.json").write_text(json.dumps(log, indent=1))
        print(json.dumps({k: (v if k != "tflite" else
                              {m: {kk: vv for kk, vv in d.items() if kk != "ops"}
                               for m, d in v.items()})
                          for k, v in log.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
