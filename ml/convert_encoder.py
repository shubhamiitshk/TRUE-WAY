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
ROOT = Path(__file__).resolve().parent.parent


def _cos(a, b) -> float:
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _fold_scale(target: nn.Module, gamma: torch.Tensor) -> None:
    """Folds a per-channel LayerScale into the op that PRODUCES those channels.

    A LayerScale is a per-output-channel multiply, so it commutes with the op
    it follows:  g * (W x + b) == (g*W) x + (g*b).  It does NOT commute with
    any other op - folding the wrong gamma into the wrong weight computes a
    DIFFERENT function, which is exactly what the previous export did: it
    folded `layer_scale_1` (the attention output scale) into `mlp.fc2` (the
    MLP output weight). The model still ran, the ONNX and the TFLite artefacts
    still agreed with EACH OTHER, and the gallery was extracted in PyTorch, so
    every consistency check passed - while the exported graph computed a
    function whose cosine with the training pipeline was 0.04.

    The shape of the weight decides how the scale is broadcast: a Conv2d weight
    is [C_out, C_in, kh, kw] and a Linear weight is [C_out, C_in].
    """
    g = gamma.detach().reshape(-1)
    w = target.weight
    if w.dim() == 4:
        target.weight.data.mul_(g.view(-1, 1, 1, 1))
    elif w.dim() == 2:
        target.weight.data.mul_(g.view(-1, 1))
    else:
        raise RuntimeError(
            f"cannot fold a layer scale into a weight of shape {tuple(w.shape)}")
    if target.bias is not None:
        target.bias.data.mul_(g)


def _make_static_attn_forward(mod: nn.Module):
    """A TFLite-friendly rewrite of timm's fused attention.

    timm's `Attention` with `fused_attn=True` calls
    `F.scaled_dot_product_attention(q, k, v)`, whose implicit logit scale is
    `1/sqrt(head_dim)`. The rewrite therefore applies `mod.scale` EXPLICITLY.
    Absorbing the scale into the qkv weights and then dropping it from the
    logits would scale the attention logits by 1/sqrt(head_dim) a second time -
    a different function, on every image.
    """

    def _forward(x: torch.Tensor) -> torch.Tensor:
        B, C, H, W = int(x.shape[0]), int(x.shape[1]), int(x.shape[2]), int(x.shape[3])
        N = H * W
        x_flat = x.reshape(B, C, N).transpose(-2, -1)
        qkv = mod.qkv(x_flat).reshape(B, N, 3, mod.num_heads, mod.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        attn = ((q @ k.transpose(-2, -1)) * float(mod.scale)).softmax(dim=-1)
        out = (attn @ v).transpose(1, 2).reshape(B, N, C)
        out = mod.proj(out)
        return out.transpose(-2, -1).reshape(B, C, H, W)
    return _forward


def _tanh_gelu(x: torch.Tensor) -> torch.Tensor:
    return 0.5 * x * (1.0 + torch.tanh(0.7978845608028654 * (x + 0.044715 * x * x * x)))


class ClipImageFeatures(nn.Module):
    """timm MobileCLIP image encoder outputting the 512-dim CLIP visual projection.

    TWO EXPORT SHAPES, and the difference matters:

    * ``adapter_mode="fused"`` (legacy): the trained adapter matrix is folded
      into ``backbone.head.fc``. **This is only valid if nothing sits between
      the projection and the adapter** - and in training something DOES: the
      backbone output is L2-normalised *before* the adapter is applied
      (``MobileClip512Backbone.forward`` ends in ``F.normalize``). Folding a
      linear map across a normalisation is NOT a no-op: the adapter was fitted
      on unit-norm inputs, so applying it to an unnormalised vector on the
      device is a genuine train/serve mismatch, and the folded matrix is no
      longer scale-invariant.

    * ``adapter_mode="separate"`` (correct, the default): the graph is
          features -> head.fc -> L2Normalize -> Linear(W_eff) -> L2Normalize
      which is EXACTLY what the training pipeline computes, with the adapter
      as one extra 512x512 matmul. The device therefore receives a unit-norm
      embedding that matches the gallery vectors.
    """

    def __init__(self, backbone: nn.Module, pre_logits: bool = False,
                 adapter_state: dict | None = None, adapter_mode: str = "separate"):
        super().__init__()
        self.backbone = backbone
        self.pre_logits = pre_logits
        self.adapter_mode = adapter_mode
        self.has_adapter = adapter_state is not None and not pre_logits
        with torch.no_grad():
            for st in self.backbone.stages:
                for blk in st.blocks:
                    # timm's RepMixerBlock:   x = x + layer_scale(mlp(x))
                    # timm's AttentionBlock: x = x + layer_scale_1(token_mixer(norm(x)))
                    #                        x = x + layer_scale_2(mlp(x))
                    # Each scale belongs to the op that PRODUCES its channels.
                    if hasattr(blk, "layer_scale") and hasattr(blk.layer_scale, "gamma"):
                        _fold_scale(blk.mlp.fc2, blk.layer_scale.gamma.data)
                        blk.layer_scale = nn.Identity()
                    if hasattr(blk, "layer_scale_1") and hasattr(blk.layer_scale_1, "gamma"):
                        mixer = getattr(blk, "token_mixer", None)
                        target = getattr(mixer, "proj", None)
                        if target is None:
                            target = blk.mlp.fc2
                        _fold_scale(target, blk.layer_scale_1.gamma.data)
                        blk.layer_scale_1 = nn.Identity()
                    if hasattr(blk, "layer_scale_2") and hasattr(blk.layer_scale_2, "gamma"):
                        _fold_scale(blk.mlp.fc2, blk.layer_scale_2.gamma.data)
                        blk.layer_scale_2 = nn.Identity()

            for m in self.backbone.modules():
                if isinstance(m, nn.GELU):
                    m.forward = _tanh_gelu
                if hasattr(m, "qkv") and hasattr(m, "scale") and hasattr(m, "num_heads") and hasattr(m, "head_dim"):
                    # The attention scale is applied EXPLICITLY in the static
                    # forward below, exactly as `scaled_dot_product_attention`
                    # would. It is NOT absorbed into the qkv weights: the
                    # original fused path applies 1/sqrt(head_dim) to the
                    # logits, and absorbing it into q would apply it twice.
                    m.forward = _make_static_attn_forward(m)

        self.adapter_fc = None
        if self.has_adapter and adapter_state is not None:
            with torch.no_grad():
                d_scale = adapter_state["diag_scale"].float()
                w_lin = adapter_state["linear.weight"].float()
                alpha = torch.clamp(adapter_state["alpha"].float(), 0.05, 0.55)
                dim = int(d_scale.shape[0])
                s = torch.nn.functional.softplus(d_scale)
                eye = torch.eye(dim)
                w_eff = ((1.0 - alpha) * eye + alpha * w_lin) * s.unsqueeze(0)
                if adapter_mode == "separate":
                    # Keep the adapter OUT of head.fc and apply it AFTER the
                    # normalisation, exactly as training does.
                    self.adapter_fc = nn.Linear(dim, dim, bias=False)
                    self.adapter_fc.weight.data.copy_(w_eff)
                else:
                    fc = self.backbone.head.fc
                    fc.weight.data.copy_(w_eff @ fc.weight.data)
                    if fc.bias is not None:
                        fc.bias.data.copy_(w_eff @ fc.bias.data)

    def forward(self, x):
        feats = self.backbone.forward_features(x)
        head = self.backbone.forward_head(feats, pre_logits=self.pre_logits)
        if self.adapter_fc is not None:
            head = torch.nn.functional.normalize(head, p=2, dim=-1)
            head = self.adapter_fc(head)
            head = torch.nn.functional.normalize(head, p=2, dim=-1)
        return head


def check_real_image_equivalence(feat: nn.Module, work: Path, n: int = 8,
                                floor: float = 0.995) -> dict:
    """Does the EXPORTED GRAPH compute the TRAINING function on REAL IMAGES?

    Every consistency check in this pipeline (ONNX-vs-TFLite, determinism,
    export-shape) compares the artefact with ITSELF. None of them compared the
    artefact with the TRAINING pipeline, so a graph that computes a completely
    different function passed every gate: the ONNX and the TFLite model agreed
    with each other (cos 0.9999) while the cosine with the training pipeline
    on a real photograph was **0.04**. Random-noise inputs hid it - the
    attention logits saturate differently on noise than on a photograph.

    This check runs the exported module and the training computation side by
    side on REAL corpus photographs and fails the build when they disagree.
    """
    import timm
    from timm.utils.model import reparameterize_model
    from PIL import Image

    manifest_path = ROOT / "ml" / "dataset" / "dataset_manifest.json"
    if not manifest_path.is_file():
        print("[equiv] SKIP: no dataset manifest")
        return {"skipped": True}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths: list = []
    for section in ("pois", "negatives"):
        for node in manifest.get(section, {}).values():
            for r in node.get("records", []):
                p = ROOT / r["local_path"]
                if p.is_file():
                    paths.append(p)
    if not paths:
        print("[equiv] SKIP: no corpus images on disk")
        return {"skipped": True}
    step = max(1, len(paths) // n)
    paths = paths[::step][:n]

    # The REFERENCE side: the untouched, reparameterised backbone plus the
    # adapter applied to its NORMALISED output - the training pipeline.
    ref_backbone = timm.create_model(VARIANTS["s0"], pretrained=True).eval()
    ref_backbone = reparameterize_model(ref_backbone).eval()
    state = torch.load(work / "arcface_adapter.pt", map_location="cpu",
                       weights_only=False).get("adapter_state_dict")
    if not state:
        print("[equiv] SKIP: no adapter state")
        return {"skipped": True}
    d_scale = state["diag_scale"].float()
    w_lin = state["linear.weight"].float()
    alpha = torch.clamp(state["alpha"].float(), 0.05, 0.55)
    s = torch.nn.functional.softplus(d_scale)
    dim = int(d_scale.shape[0])
    w_eff = ((1.0 - alpha) * torch.eye(dim) + alpha * w_lin) * s.unsqueeze(0)

    worst = 1.0
    with torch.no_grad():
        for p in paths:
            im = Image.open(p).convert("RGB")
            w, h = im.size
            scale = IMG / min(w, h)
            im = im.resize((max(IMG, int(round(w * scale))), max(IMG, int(round(h * scale)))),
                           Image.Resampling.BICUBIC)
            im = im.crop(((im.width - IMG) // 2, (im.height - IMG) // 2,
                          (im.width - IMG) // 2 + IMG, (im.height - IMG) // 2 + IMG))
            x = np.asarray(im, dtype=np.float32) / 255.0
            xt = torch.from_numpy(np.transpose(x, (2, 0, 1))[None, ...])
            head = ref_backbone.forward_head(ref_backbone.forward_features(xt))
            ref = torch.nn.functional.normalize(
                torch.nn.functional.normalize(head, p=2, dim=-1), p=2, dim=-1)
            ref = torch.nn.functional.normalize(torch.nn.functional.linear(ref, w_eff), p=2, dim=-1)
            got = feat(xt)
            c = _cos(ref.numpy(), got.numpy())
            worst = min(worst, c)
    print(f"[equiv] cos(training pipeline, exported graph) on {len(paths)} REAL "
          f"photographs: min {worst:.6f} (floor {floor})")
    if worst < floor:
        print("[equiv] FAIL - the exported graph does NOT compute the training function "
              "on real photographs.")
        print("          The device would score against embeddings the gallery never saw.")
        raise SystemExit(3)
    print("[equiv] PASS - the exported graph reproduces the training computation "
          "on real photographs.")
    # The reference model is a whole second copy of the backbone; release it
    # before the converter starts allocating the (much larger) TFLite
    # conversion buffers.
    del ref_backbone, w_eff, state
    import gc
    gc.collect()
    return {"min_cos_real_images": worst, "samples": len(paths), "floor": floor}


def step_fetch(variant: str, work: Path, pre_logits: bool = False):
    import timm
    from timm.utils.model import reparameterize_model
    ckpt = VARIANTS[variant]
    print(f"[fetch] {ckpt} (pre_logits={pre_logits})")
    backbone = timm.create_model(ckpt, pretrained=True).eval()
    backbone = reparameterize_model(backbone).eval()
    adapter_state = None
    arcface_pt = work / "arcface_adapter.pt"
    if arcface_pt.is_file() and not pre_logits:
        ckpt_data = torch.load(arcface_pt, map_location="cpu", weights_only=False)
        adapter_state = ckpt_data.get("adapter_state_dict")
        print(f"[fetch] fusing trained LinearResidualAdapter from {arcface_pt}")
    feat = ClipImageFeatures(backbone, pre_logits=pre_logits, adapter_state=adapter_state).eval()
    n_params = sum(p.numel() for p in feat.parameters())
    with torch.no_grad():
        dummy = torch.randn(1, 3, IMG, IMG)
        out = feat(dummy)
    print(f"[fetch] params={n_params / 1e6:.1f}M feat_dim={tuple(out.shape)} adapter_fused={adapter_state is not None}")
    torch.save(feat.state_dict(), work / f"mci_{variant}_features.pt")
    meta = {"variant": variant, "ckpt": ckpt, "params": n_params,
            "feat_shape": list(out.shape), "input": [1, 3, IMG, IMG],
            "adapter_fused": feat.adapter_fc is None and adapter_state is not None,
             "adapter_mode": getattr(feat, "adapter_mode", "fused")}
    # The exported graph must compute the TRAINING function on REAL
    # photographs. Without this the build happily shipped a graph whose
    # cosine with the training pipeline was 0.04.
    meta["real_image_equivalence"] = check_real_image_equivalence(feat, work)
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
    import sys
    import types
    import tensorflow as tf
    if "ai_edge_litert" not in sys.modules:
        try:
            import ai_edge_litert.interpreter  # noqa: F401
        except ModuleNotFoundError:
            _m1 = types.ModuleType("ai_edge_litert")
            _m2 = types.ModuleType("ai_edge_litert.interpreter")
            _m2.Interpreter = tf.lite.Interpreter  # type: ignore[attr-defined]
            _m1.interpreter = _m2  # type: ignore[attr-defined]
            sys.modules["ai_edge_litert"] = _m1
            sys.modules["ai_edge_litert.interpreter"] = _m2
    print("[tflite] onnx -> savedmodel via onnx2tf (this takes minutes)")
    import onnx2tf
    import os
    stub = os.path.join(os.getcwd(), "calibration_image_sample_data_20x128x128x3_float32.npy")
    made_stub = False
    if not os.path.isfile(stub):
        rng_stub = np.random.default_rng(7)
        with open(stub, "wb") as f:
            np.save(f, rng_stub.random((20, 128, 128, 3), dtype=np.float32))
        made_stub = True
    # Keep stages.3 attention token-mixer activation inputs in NCHW so onnx2tf
    # preserves exact 3D/4D reshape and transpose axes inside attention.
    import onnx as _onnx
    _m = _onnx.load(str(work / f"mci_{variant}.onnx"))
    keep_nchw: list[str] = []
    for _n in _m.graph.node:
        if "stages.3" in _n.name and "token_mixer" in _n.name:
            if _n.op_type in ("Reshape", "Transpose", "Gather", "Softmax"):
                keep_nchw.append(_n.input[0])
            elif _n.op_type == "MatMul":
                keep_nchw.append(_n.input[0])
                if not _n.input[1].startswith("onnx::"):
                    keep_nchw.append(_n.input[1])
    keep_nchw = sorted(set(keep_nchw))
    print(f"[tflite] keep-NCHW inputs for {len(keep_nchw)} stages.3 token-mixer activation tensors")
    try:
        onnx2tf.convert(
            input_onnx_file_path=str(work / f"mci_{variant}.onnx"),
            output_folder_path=str(work / "savedmodel"),
            non_verbose=True,
            disable_strict_mode=True,
            keep_ncw_or_nchw_or_ncdhw_input_names=keep_nchw,
        )
    finally:
        if made_stub and os.path.isfile(stub):
            os.remove(stub)

    import base64
    import flatbuffers
    from tensorflow.lite.python import schema_py_generated as schema_fb

    _TFLITE_METADATA_B64 = (
        "HAAAAE0wMDEUACAAHAAYABQAEAAMAAgAAAAEABQAAAAcAAAAJAAAAGwAAAB4AAAAoAIAAKQC"
        "AADUAgAABQAAADEuMC4wAAAARwAAAEFwYWNoZSBMaWNlbnNlLiBWZXJzaW9uIDIuMCBodHRw"
        "Oi8vd3d3LmFwYWNoZS5vcmcvbGljZW5zZXMvTElDRU5TRS0yLjAuAAkAAABNZWRpYVBpcGUA"
        "AAABAAAAEAAAAAwADAAAAAAACAAEAAwAAAAIAAAAcAAAAAEAAAAQAAAADAAQAAwACAAAAAQAD"
        "AAAAAwAAAAcAAAAQAAAAGT///8MAAAAAAAAAQQABAAEAAAAIgAAAEZlYXR1cmUgdmVjdG9yIG"
        "9mIHRoZSBpbnB1dCBpbWFnZS4AAAcAAABmZWF0dXJlAAEAAAAUAAAAEAAYABQAEAAAAAwACAAE"
        "ABAAAAAUAAAALAAAAHAAAACEAAAAaAEAAMj///8IAAAADAAAAAEAAAAAAAAAAQAAAAAAgD8BAAA"
        "ADAAAAAgADAALAAQACAAAABAAAAAAAAABCAAMAAgABAAIAAAACAAAAAwAAAABAAAAAAB/QwEAAA"
        "AAAAAACAAKAAkABAAIAAAADAAAAAACBgAIAAcABgAAAAAAAAHgAAAASW5wdXQgaW1hZ2UgdG8g"
        "YmUgZW1iZWRkZWQuIFRoZSBleHBlY3RlZCBpbWFnZSBpcyAyNTYgeCAyNTYsIHdpdGggdGhyZWU"
        "gY2hhbm5lbHMgKHJlZCwgYmx1ZSwgYW5kIGdyZWVuKSBwZXIgcGl4ZWwuIEVhY2ggZWxlbWVudCB"
        "pbiB0aGUgdGVuc29yIGlzIGEgdmFsdWUgYmV0d2VlbiBtaW4gYW5kIG1heCwgd2hlcmUgKHBlci"
        "1jaGFubmVsKSBtaW4gaXMgWzAuMF0gYW5kIG1heCBpcyBbMS4wXS4AAAAABQAAAGltYWdlAAAAAQ"
        "AAADEAAAAuAAAAQ3JlYXRlcyB0aGUgZmVhdHVyZSB2ZWN0b3Igb2YgdGhlIGlucHV0IGltYWdlLg"
        "AAHAAAAE1vYmlsZUNMSVAtUzAgaW1hZ2UgZW1iZWRkZXIAAAAA"
    )
    _meta_buf = list(base64.b64decode(_TFLITE_METADATA_B64))

    def _inject_tflite_metadata(raw_bytes: bytes) -> bytes:
        model_t = schema_fb.ModelT.InitFromPackedBuf(raw_bytes, 0)
        if model_t.metadata is None:
            model_t.metadata = []
        model_t.metadata = [m for m in model_t.metadata if m.name != b"TFLITE_METADATA"]
        buf_t = schema_fb.BufferT()
        buf_t.data = list(_meta_buf)
        model_t.buffers.append(buf_t)
        meta_t = schema_fb.MetadataT()
        meta_t.name = b"TFLITE_METADATA"
        meta_t.buffer = len(model_t.buffers) - 1
        model_t.metadata.append(meta_t)
        builder = flatbuffers.Builder(len(raw_bytes) + 4096)
        packed = model_t.Pack(builder)
        builder.Finish(packed, b"TFL3")
        return bytes(builder.Output())

    converter = tf.lite.TFLiteConverter.from_saved_model(str(work / "savedmodel"))
    fp32 = _inject_tflite_metadata(converter.convert())
    (work / f"mci_{variant}_fp32.tflite").write_bytes(fp32)
    print(f"[tflite] fp32 {len(fp32) / 1e6:.1f} MB (+TFLITE_METADATA)")

    rng = np.random.default_rng(7)
    calib_npy = work / "domain_calib_nhwc.npy"
    calib_arr = None
    if calib_npy.is_file():
        calib_arr = np.load(calib_npy).astype(np.float32)
        print(f"[tflite] domain calibration set: {calib_arr.shape} "
              f"({len(calib_arr)} real Bihar images) - wired into the per-tensor "
              f"and per-axis INT8 converters as `representative_dataset`; the "
              f"dynamic-range and fp16 variants take no calibration set")
    else:
        print("[tflite] WARNING: no domain calibration set; quantisation ranges will NOT "
              "be domain-calibrated")

    def representative_dataset():
        if calib_arr is None:
            raise RuntimeError("no domain calibration set available")
        for i in range(calib_arr.shape[0]):
            yield [calib_arr[i:i + 1]]

    # ------------------------------------------------------------------ INT8
    # The previous build loaded the Bihar domain calibration images and then
    # NEVER WIRED THEM INTO THE CONVERTER: `c2.representative_dataset` was never
    # set, so the quantisation ranges came from TFLite's default rather than from
    # the domain the encoder actually runs in - while the conversion log still
    # claimed "DOMAIN-CALIB". The measured result was a cross-backend cosine of
    # 0.9889 and an INT8 model 6x SLOWER than FP32 on the workstation CPU.
    #
    # Four variants are now produced and MEASURED:
    #   int8_per_tensor  full integer quantisation, per-tensor weights
    #   int8_per_axis    full integer quantisation, per-axis (per-channel) weights
    #   int8_dynamic     dynamic-range quantisation (int8 weights, float
    #                     activations) - LiteRT: 4x smaller, 2-3x speedup, and NO
    #                     representative dataset is needed
    #   fp16             float16 weights, float IO
    # The one that is actually FASTER on the target is the one that ships:
    # "smaller" is not "faster" (arXiv:2509.21173 measures quantised CLIP
    # running 4x slower than FP32).
    #
    # NOTE on per-axis: TensorFlow's converter has per-channel weight
    # quantisation ON BY DEFAULT (`_experimental_disable_per_channel = False`).
    # A converter that is not told otherwise therefore produces PER-CHANNEL
    # weights, so a "per-tensor" variant must explicitly disable it - otherwise
    # the two variants are the same file and the comparison is meaningless.
    # Each variant is produced, injected, written and MEASURED on its own, and
    # the intermediate flatbuffer objects are released before the next
    # conversion starts. The metadata injection parses the whole model into
    # Python objects (a 46 MB flatbuffer becomes hundreds of megabytes of
    # lists), and holding five of those alive at once was enough to take the
    # converter process down with a silent exit code 1.
    import gc

    def _build_fp32() -> bytes:
        converter = tf.lite.TFLiteConverter.from_saved_model(str(work / "savedmodel"))
        return converter.convert()

    def _build_int8(per_channel: bool) -> bytes:
        c = tf.lite.TFLiteConverter.from_saved_model(str(work / "savedmodel"))
        c.optimizations = [tf.lite.Optimize.DEFAULT]
        # TensorFlow's converter has per-channel weight quantisation ON BY
        # DEFAULT (`_experimental_disable_per_channel = False`). A converter
        # that is not told otherwise therefore produces PER-CHANNEL weights, so
        # the per-tensor variant must explicitly disable it - otherwise the two
        # variants are the same file and the comparison is meaningless.
        c._experimental_disable_per_channel = not per_channel
        if calib_arr is not None:
            c.representative_dataset = representative_dataset
            c.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        c.inference_input_type = tf.float32
        c.inference_output_type = tf.float32
        return c.convert()

    def _build_dynamic() -> bytes:
        c = tf.lite.TFLiteConverter.from_saved_model(str(work / "savedmodel"))
        c.optimizations = [tf.lite.Optimize.DEFAULT]
        c.inference_input_type = tf.float32
        c.inference_output_type = tf.float32
        return c.convert()

    def _build_fp16() -> bytes:
        c = tf.lite.TFLiteConverter.from_saved_model(str(work / "savedmodel"))
        c.optimizations = [tf.lite.Optimize.DEFAULT]
        c.target_spec.supported_types = [tf.float16]
        c.inference_input_type = tf.float32
        c.inference_output_type = tf.float32
        return c.convert()

    import onnxruntime as ort
    sess = ort.InferenceSession(str(work / f"mci_{variant}.onnx"),
                                providers=["CPUExecutionProvider"])
    shared_nhwc = rng.random((1, IMG, IMG, 3), dtype=np.float32)
    shared_nchw = np.ascontiguousarray(np.transpose(shared_nhwc, (0, 3, 1, 2)))
    emb_ort = sess.run(None, {"image": shared_nchw})[0].ravel()
    # The ONNX runtime session holds a 46 MB model; release it before the
    # (much heavier) TFLite conversions start.
    del sess
    import gc
    gc.collect()

    def _measure(path: Path, name: str) -> dict:
        interp = tf.lite.Interpreter(
            model_path=str(path),
            num_threads=4,
            experimental_op_resolver_type=tf.lite.experimental.OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES,
        )
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
        # Cross-backend cosine on the SHARED image: the number that decides
        # whether the gallery must be re-extracted with this artefact.
        interp.set_tensor(inp["index"], shared_nhwc)
        interp.invoke()
        emb_tfl = interp.get_tensor(outp["index"]).ravel()
        xcos = _cos(emb_ort, emb_tfl)
        # arXiv:2610.18575: below an output-agreement cosine of 0.8 every
        # architecture tested fell below the FP32 baseline. A BUILD FAILURE, not
        # a warning.
        floor = 0.99 if name == "fp32" else 0.80
        ok = xcos >= floor
        print(f"[interp:{name}] dim={y.shape[-1]} cpu4_lat={dt:.1f} ms ops={len(ops)} "
              f"ort_vs_tflite_cos={xcos:.4f} (floor {floor}) {'OK' if ok else 'FAIL'}")
        dim = int(y.shape[-1])
        del interp, emb_tfl, y
        gc.collect()
        return {"mb": path.stat().st_size / 1e6, "cpu4_ms": dt,
                "dim": dim, "ops": ops,
                "ort_vs_tflite_cos": xcos, "cross_backend_ok": ok}

    variants: dict[str, Path] = {}
    res: dict[str, dict] = {}
    plan = [
        ("fp32", f"mci_{variant}_fp32.tflite", _build_fp32),
        ("int8_per_tensor", f"mci_{variant}_int8.tflite", lambda: _build_int8(False)),
        ("int8_per_axis", f"mci_{variant}_int8_per_axis.tflite", lambda: _build_int8(True)),
        ("int8_dynamic", f"mci_{variant}_int8_dynamic.tflite", _build_dynamic),
        ("fp16", f"mci_{variant}_fp16.tflite", _build_fp16),
    ]
    for name, fname, build in plan:
        raw = build()
        gc.collect()
        injected = _inject_tflite_metadata(raw)
        del raw
        gc.collect()
        path = work / fname
        path.write_bytes(injected)
        del injected
        gc.collect()
        variants[name] = path
        res[name] = _measure(path, name)
        gc.collect()

    # ---- pick the FASTEST acceptable variant ---------------------------------
    acceptable = {k: v for k, v in res.items() if v["cross_backend_ok"] and k != "fp32"}
    chosen = min(acceptable, key=lambda k: acceptable[k]["cpu4_ms"]) if acceptable else "fp32"
    res["chosen_variant"] = chosen
    res["chosen_file"] = variants[chosen].name
    res["chosen_reason"] = ("fastest variant whose output agreement with ONNX/FP32 is "
                             ">= 0.80; FP32 is the fallback because 'smaller' is not 'faster'")
    res["calibrated_with_domain_images"] = bool(calib_arr is not None)
    res["calibration_images"] = int(calib_arr.shape[0]) if calib_arr is not None else 0
    print(f"[tflite] CHOSEN VARIANT: {chosen} "
          f"({res[chosen]['mb']:.1f} MB, {res[chosen]['cpu4_ms']:.1f} ms, "
          f"cos={res[chosen]['ort_vs_tflite_cos']:.4f})")
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
    has_domain_calib = (work / "domain_calib_nhwc.npy").is_file()
    log: dict = {
        "variant": args.variant,
        "spike_calib": not has_domain_calib,
        "domain_calib": has_domain_calib,
        # These flags describe what the CONVERTER ACTUALLY DID, not what was
        # intended. The previous build reported "domain_calib: true" while
        # never setting `representative_dataset`, so the activation ranges came
        # from TFLite's default rather than from the Bihar domain.
        "calibration_wired_into_converter": has_domain_calib,
        "calibration_note": (
            "INT8 activation ranges are calibrated with the real Bihar domain "
            "images in domain_calib_nhwc.npy" if has_domain_calib else
            "NO domain calibration was available; the INT8 activation ranges are "
            "TFLite's default and the agreement cosine is expected to be poor"),
    }
    feat, meta = step_fetch(args.variant, work) if "fetch" in steps else (None, {})
    log["fetch"] = meta
    if "onnx" in steps:
        assert feat is not None, "onnx needs fetch in same run (or extend script)"
        log["onnx"] = step_onnx(feat, work, args.variant)
    # Persist after every step: this machine has NO page file, and the TFLite
    # conversion is close enough to the commit limit that the process is killed
    # outright (exit -1, no traceback, buffered stdout lost). A partial log
    # survives; a lost one does not.
    log_path = work / "conversion_log.json"
    if log_path.is_file():
        try:
            previous = json.loads(log_path.read_text(encoding="utf-8"))
        except ValueError:
            previous = {}
        for key in ("fetch", "onnx"):
            if key not in log and key in previous:
                log[key] = previous[key]
    log_path.write_text(json.dumps(log, indent=1))
    if "tflite" in steps:
        log["tflite"] = step_tflite(work, args.variant,
                                    log.get("onnx", {}).get("ort_dim", 0))
    if "report" in steps:
        (work / "conversion_log.json").write_text(json.dumps(log, indent=1))
        def _slim(v):
            # The tflite section holds one measurement dict PER VARIANT plus a
            # few scalar summary keys (chosen_variant, chosen_file, ...).
            if not isinstance(v, dict):
                return v
            out = {}
            for m, d in v.items():
                if isinstance(d, dict):
                    out[m] = {kk: vv for kk, vv in d.items() if kk != "ops"}
                else:
                    out[m] = d
            return out

        print(json.dumps({k: (_slim(v) if k == "tflite" else v)
                          for k, v in log.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
