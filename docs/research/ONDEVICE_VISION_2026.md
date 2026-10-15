# On-device vision for TrueWay — research synthesis (Oct 2026)

Lead-developer research backing blueprint §7 (recognition science) and §8
(reference architecture). Question answered: **which encoder + runtime +
index ships the P0 scanner on entry-tier Android, and what is the measured
upgrade path?** All external numbers are cited; nothing here replaces the
Week 4–7 benchmark on our own corpus (§7.6, §18.2).

## 0. Bottom line (read this only)

1. **P0 baseline: MobileCLIP-S0 image encoder (v1, converted and verified),
   INT8, LiteRT, CPU+XNNPACK with GPU-delegate upgrade path, flat
   brute-force index.** Image encoder is ~11M params (~45 MB FP32, ~12 MB
   INT8) at ~1.5 ms iPhone-class latency — 30× smaller and an order of
   magnitude faster than the 388 MB EmbeddingGemma Text-Vision option, and
   it leaves the entry-tier budget intact. (MobileCLIP2 weights are the
   promotion candidate — re-measure, don't assume.)
2. **Correctness comes from a frozen encoder + learned linear adaptation
   layer trained on pilot data, not from a bigger model.** ILIAS (CVPR 2025)
   shows linear adaptation is the single most effective cheap boost for
   image-to-image retrieval with VLMs, and that domain-fine-tuned models
   win in-domain but collapse out-of-domain — so we adapt, we don't
   full-fine-tune.
3. **Semantic embedding ≠ instance identity.** No frozen encoder separates
   Nalanda Temple 3 from Monastery 1 out of the box. The place-level
   aggregation + calibration gate + abstention (blueprint §7.4–7.5) is the
   product; the encoder is one input to it. Geometric verification stays P1.
4. **Runtime: LiteRT, never NNAPI directly** (deprecated in Android 15 —
   migrate to LiteRT Play Services + GPU delegate). NPU (Qualcomm QNN) is a
   measured flagship upgrade, not a P0 dependency.
5. **Index: flat brute-force + scalar-quantized embeddings at pilot scale.**
   HNSW only if latency proves necessary. A 70-POI × 30-ref × 512-dim
   INT8 index is ~1 MB — there is nothing to optimize yet.

---

## 1. Encoder landscape (measured numbers, Oct 2026)

| Encoder (image side only) | Image params | FP32 size | INT8 size | Latency ref | Zero-shot signal |
|---|---|---|---|---|---|
| **MobileCLIP-S0 (v1, CONVERTED — `apple/mobileclip_s0_timm`)** | 11.4M | ~45 MB (43.7 MB ONNX measured) | **~12 MB** | **1.5 ms** img (iPhone 12 Pro Max, CoreML) | IN-1k **67.8%**, 38-set avg 58.1 |
| **MobileCLIP-S2 (v1, CONVERTED)** | 35.7M | ~140 MB (141 MB ONNX measured) | ~35 MB | 3.6 ms img | IN-1k 74.4%, avg 63.7 |
| MobileCLIP2-S0/S2 (v2, NOT converted — promotion candidate) | same arches | same | same | same | v2-S0 IN-1k 71.5%, v2-S2 77.2% — re-measure on pilot before promoting |
| MobileCLIP-B (v1, reference only) | 86.3M | ~345 MB | ~86 MB | 10.4 ms img | IN-1k 76.8% |
| **EmbeddingGemma 2 Text-Vision** (Oct 2026) | 440M total (170M vision) | — | **388 MB** download | 49 ms img+text (Pixel 11 Pro TPU); 119–191 ms (S26 Ultra) | MIEB-lite 64.6, MMEB-img 57.3 |
| MobileNetV3-small (MediaPipe default) | ~2.5M | ~10 MB | ~3 MB | single-digit ms CPU | classification backbone, weak retrieval semantics |
| EfficientNet-Lite0 | ~4.7M | ~19 MB | ~5 MB | single-digit ms CPU | same class as above |

Sources: Apple ml-mobileclip repo + CVPR'24 paper + MobileCLIP2 arXiv
2508.20691 (latencies = image+text split as reported, iPhone 12 Pro Max);
Google EmbeddingGemma 2 model card + LiteRT-LM latency table via
GenAI Magazine Oct 2026 (Pixel 11 Pro TPU 8.3 ms text / 49 ms text+image,
S26 Ultra GPU 119 ms); MediaPipe Image Embedder docs (MobileNetV3 pair).

### 1.1 Reading the table as a lead dev

- **S0 vs S2 is the real P0 decision, not S0 vs EmbeddingGemma.**
  EmbeddingGemma-TextVision is disqualified as *mandatory* (blueprint
  already says this): 388 MB download, ~191 MB text-only / ~567 MB full
  active RAM on a Pixel 11 Pro, 49 ms only on flagship TPU. It is a valid
  **Tier-F optional experiment** (multimodal text+image queries, MRL
  truncation 768→256 keeps ~95% quality at 1/3 storage) — never the floor.
- **S0→S2 buys +5.7 pts IN-1k for +24M params / +2 ms.** Whether that moves
  *our* open-set false-accept rate is unknowable without the pilot corpus —
  that is exactly the Week 4–7 benchmark. Default to S0 for the entry tier,
  promote to S2 iff the false-accept gate fails on S0 with adaptation.
- **MobileNetV3/EfficientNet-Lite stay as the "cheap floor" candidate**
  (blueprint variant A): smallest install, fastest CPU, weakest semantics.
  Keep one in the benchmark matrix so "small model can't do it" is a
  measurement, not an assumption.
- **DINOv2 note (ILIAS finding):** DINOv2-B/L is competitive on
  architecture/sculpture categories specifically — plausibly the closest
  public backbone bias to heritage stone. Too heavy for P0 on-device, but a
  strong **teacher for distillation / adaptation-target** on workstation.

## 2. The instance-vs-semantic gap (why the pipeline matters more than the model)

ILIAS (CVPR 2025, 1k instances / 100M distractors) is the closest public
proxy to our problem, and its four findings map 1:1 onto blueprint §7:

1. **Domain-tuned models excel in-domain, fail out-of-domain.** Do NOT
   full-fine-tune the encoder on 15–70 Bihar POIs and declare victory — it
   will memorize the pilot and collapse on the next circuit. (This is why
   blueprint §7.2 demands photographer/visit/day splits.)
2. **Linear adaptation on frozen features is the cheap universal win.**
   A learned linear layer on multi-domain supervision improves most models,
   most strongly for VLMs — because image-to-image relations are *not*
   optimized during VLM pretraining. **This is our P0 training procedure:**
   freeze encoder → train linear projection (contrastive/ArcFace on pilot
   + lookalike pairs) → export projection as a second tiny matmul.
   Cost: minutes on workstation, kilobytes on device.
3. **Local-descriptor re-ranking still matters under clutter** — validates
   blueprint variant C (geometric verifier) as P1, not P0.
4. **i2i and t2i retrieval are weakly correlated; ensembling gains +6.1.**
   Future lever only: average visual similarity with text-alias similarity
   (our FTS rank) at decision time. Record both scores from day one so the
   ensemble is a future offline experiment, not a rewrite.
5. **Resolution matters more than commonly assumed** (SigLIP small-highres
   beats larger-lowres). Benchmark 224 vs 320 input on-device; extra pixels
   are cheaper than extra parameters if the delegate holds latency.

**GLDv2 lesson for our eval design:** 99% out-of-domain test images, long
tail, high intra-class variance. Our unknown set (shops, scaffolding,
generic brickwork, neighboring lookalikes) must *outnumber and out-diversify*
the known set — otherwise top-1 looks good and false-accepts kill us in
the field. The 85%/95%/≤5% gates stand, with false-accept as the binding one.

## 3. Android inference stack (what to actually ship)

### 3.1 Runtime decision: LiteRT (Play Services path first)

- **NNAPI is deprecated (Android 15).** Google's migration guide points to
  LiteRT-in-Play-Services + GPU delegate. Never call NNAPI directly in new
  code. (Our `minSdk 26` + Play-Services runtime keeps entry devices covered;
  standalone `litert` bundling only if the no-Google-services market is
  declared — it currently is not.)
- **Delegate priority per device tier:**
  1. **CPU + XNNPACK (INT8)** — universal fallback, zero compat risk.
     Independent benchmark: TFLite INT8 MobileNetV2 ~40–80 ms on Pi-4 class
     CPU; modern entry phones do substantially better — measure, don't infer.
  2. **GPU delegate (FP16 / float-view INT8)** — the standard upgrade. INT8
     models run through a float view (weights dequantized once into GPU
     memory; I/O quant ops on CPU). Keep float input/output tensors.
     Startup check via `CompatibilityList` / `TfLiteGpu.isGpuDelegateAvailable`,
     CPU fallback on unsupported ops. GPU delegate **must init and invoke on
     the same thread**; RGBA input avoids an RGB→RGBX copy; reshape-heavy
     graphs are disproportionately slow on GPU — prefer conv-heavy encoders
     (another point for MCi-style CNN-hybrid image encoders over pure ViT).
  3. **Qualcomm QNN / NPU delegate** — flagship-only experiment. Measured
     MobileNetV2: NPU 0.3–0.6 ms vs GPU 1.8–2.7 ms vs CPU 2.8–4.1 ms
     (S23–S25). Real but narrow for a retrieval encoder; revisit for the
     optional LLM/ASR tiers, not the P0 scanner.
- **MediaPipe ImageEmbedder task** is the recommended integration surface:
  `RunningMode.IMAGE` (single-shot — matches our no-continuous-scan policy),
  built-in preprocess/resize/normalize, `cosineSimilarity()` helper,
  `quantize=true` scalar quantization for stored reference vectors, CPU/GPU
  delegate switch in ~10 lines (`ImageEmbedderHelper.kt` pattern). For the
  future index-attached option, Task Library `ImageSearcher` (embedder +
  ScaNN index in TFLite metadata) exists — evaluate only if flat search
  fails latency.

### 3.2 Quantization rules that survive contact with real phones

- **Ship INT8 with float I/O** (post-training full-integer or QAT) for the
  retrieval encoder; XNNPACK handles INT8 CPU, GPU delegate takes the float
  view. This is the one config with support on every path.
- **Known crash vector:** full-INT8 graphs with integer-arithmetic ops
  (`ConvInteger`/`MatMulInteger`) can fail on mobile ARM CPU exec providers
  while passing on x86 desktop. If a converted MobileCLIP encoder crashes
  on-device but passes workstation checks, fall back to **INT8 weight-only +
  DequantizeLinear** (storage win, FP32 compute, universally supported) or
  FP16 — and log it as a conversion bug, not a product decision. Validate
  **on the physical entry phone**, never only on emulator/x86.
- **Calibration discipline:** 200–500 *pilot-domain* images (our permitted
  viewpoints + lookalikes), not generic ImageNet samples. Domain calibration
  is where the last point of retrieval accuracy lives.
- **Embedding storage:** scalar-quantize reference vectors to INT8
  (~4× smaller, negligible cosine-similarity loss); keep the query path FP
  until measured. MRL-style truncation (512/256-dim) is the second lever if
  pack bytes bite — validate recall delta on our corpus first.

### 3.3 Preprocessing is a latency line item

CameraX YUV → RGB → resize → normalize on the **same native path** (avoid
`Bitmap` alloc churn; ~3 ms vs ~18 ms reported for the Bitmap path on Pixel
8). Single-shot capture (already our policy) keeps thermal behavior trivial
vs streaming. Record per-stage timings (capture / preprocess / encode /
search) in the benchmark template — when P95 blows the 6 s gate, the fix is
usually preprocess or delegate fallback, not the model.

## 4. Index + decision math at pilot scale (do the arithmetic)

- 70 POIs × 30 refs × 512-dim INT8 ≈ **~1 MB**. 768-dim FP32 ≈ ~6.5 MB.
  Either is noise next to images/audio. **Flat brute-force cosine is the
  correct P0 index** — exact, zero dependency, debuggable. HNSW/ScaNN/ObjectBox
  answers a question we do not have (sub-ms over millions). Revisit at
  10k+ vectors or measured P95 pressure, not before.
- Place-level score = robust top-2 mean over that place's refs (+ soft geo
  prior), then the **calibration gate learned on held-out visits** decides
  accept/abstain. Threshold is an output of `ml/evaluate_retrieval.py`'s
  sweep on *our* data, not a constant from a paper. Until calibrated: no
  percentage confidences in UI (likely/possible/unknown wording stands).

## 5. Phased execution plan (maps to sprint)

| Phase | Work | Exit artifact |
|---|---|---|
| **4a. Conversion spike (days)** | Export MobileCLIP-S0 + S2 image encoders (v1; v2 on re-measurement) → ONNX → TFLite (INT8 + float I/O); MobileNetV3-small as floor; record which conversions survive on-device load | `ml/models/` conversion log: size, load OK/FAIL per phone |
| **4b. Adaptation training (workstation)** | Freeze encoder → train linear projection (ArcFace/contrastive) on pilot lawful images + lookalike negatives, photographer-split; export projection weights into pack | `reference-vectors.bin` built from *adapted* embeddings; top-1/top-3/FA numbers on held-out visits |
| **4c. On-device benchmark** | LiteRT benchmark tool: CPU-XNNPACK vs GPU delegate per encoder; per-stage timings; PSS/RSS, thermal, battery drain on entry + mid phones | Benchmark sheet per §29.3 template; delegate-selection table in code |
| **4d. Gate review** | ≥85% top-1 / ≥95% top-3 / ≤5% FA on pre-registered set; 100% tampered-pack rejection; all-radio-off suite | Go/no-go for scanner in beta (§26.1); S0 vs S2 promotion decision |
| Later (P1, only on pass) | Geometric verifier on confusing pairs; i2i+t2i ensemble logging; QNN/NPU experiment; EmbeddingGemma-440M Tier-F experiment | Separate feature-gated branches |

Non-goals restated: no global ID, no continuous background scan, no
percentage confidence before calibration, no HNSW, no mandatory LLM.

## 6. Sources (verification snapshot Oct 2026)

- S-A1 Apple ml-mobileclip repo (MobileCLIP2-S4 matches SigLIP-SO400M/14 at
  2× fewer params; S0 67.8→71.5 IN-1k across v1→v2) + CVPR'24 paper + arXiv
  2508.20691.
- S-A2 Google EmbeddingGemma 2 model card (740M; 270/440/570/740 modular;
  MRL 768→256 ~95% quality) + LiteRT-LM latency table (Pixel 11 Pro TPU
  8.3 ms text / 49 ms text+image; S26 Ultra 119 ms GPU) + HF model page.
- S-A3 LiteRT GPU/delegates docs (op support, float-view INT8, same-thread
  rule, RGBA fast path) + NNAPI migration guide (deprecated, Android 15) +
  Qualcomm QNN delegate (S25: NPU 0.3 / GPU 1.8 / CPU 2.8 ms MobileNetV2).
- S-A4 MediaPipe ImageEmbedder + Task Library ImageSearcher/Embedder docs
  (RunningMode.IMAGE, quantize flag, ScaNN-attached searcher model).
- S-A5 ILIAS CVPR'25 (linear adaptation boost; domain-tuning brittleness;
  local re-rank value; i2i+t2i ensemble +6.1) + GLDv2 paper (99%
  out-of-domain test, long tail) + CLIP-vs-DINO controlled study (language
  supervision aids fine-grained distinctions).
- S-A6 ONNX-mobile quantization field report (ConvInteger ARM crash →
  weight-only INT8+DequantizeLinear ships at 75% smaller, identical quality)
  + ORT quantization docs (S8S8/QDQ guidance) + edge TFLite/ORT/PyTorchMobile
  benchmark (TFLite INT8 leads on ARM via XNNPACK).
- S-A7 LEANN / MicroNN / MobileRAG-EcoVector / ObjectBox (why HNSW-on-phone
  exists — and why our 1 MB index doesn't need it yet).
