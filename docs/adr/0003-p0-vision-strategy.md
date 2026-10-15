# ADR-0003: P0 vision encoder strategy (research-backed, benchmark-gated)

- **Status:** Accepted (2026-10-11)
- **Source:** `docs/research/ONDEVICE_VISION_2026.md`; blueprint §7.3 (baselines to benchmark, not pre-select)
- **Context:** Blueprint lists MobileNet/EfficientNet, EmbeddingGemma-440M,
  geometric verifier and Gemma-4-QA as variants. Oct-2026 external evidence
  (MobileCLIP2/TMLR-2025, EmbeddingGemma-2 launch, ILIAS/CVPR-2025, LiteRT
  NPU/GPU docs, NNAPI deprecation) sharpens the benchmark matrix without
  pre-selecting a winner.

## Decision

1. Benchmark matrix (Week 4–7), in order: **MobileCLIP-S0 image encoder
   (v1 converted; v2 = `apple/ml-mobileclip` re-measurement candidate, never
   assumed) (INT8, new P0 favorite) → MobileCLIP-S2 (promotion iff S0 fails the
   false-accept gate) → MobileNetV3-small/EfficientNet-Lite0 (cheap floor) →
   EmbeddingGemma-2 Text-Vision 440M (Tier-F optional experiment only)**.
2. Training procedure is **frozen encoder + learned linear adaptation layer**
   on pilot data (ILIAS finding), never full fine-tuning on 15–70 POIs.
   Prototype: `ml/train_adapter.py` (diagonal form, stdlib-only);
   full-matrix ArcFace version trains on workstation with torch.
3. Runtime is **LiteRT via Play Services + GPU delegate, CPU+XNNPACK
   fallback**. No direct NNAPI code (deprecated Android 15). QNN/NPU is a
   flagship experiment, not a P0 dependency. Integration surface:
   MediaPipe `ImageEmbedder` (`RunningMode.IMAGE`).
4. Index stays **flat brute-force + scalar-quantized refs** at pilot scale
   (~1 MB for 70×30×512 INT8). No HNSW until measured P95 pressure.

## Consequences

- Adds a model-conversion spike (ONNX→TFLite INT8 + float I/O, on-device
  load check incl. the ARM `ConvInteger` crash fallback) before adaptation
  training.
- Gates unchanged (§18.2): ≥85% top-1 / ≥95% top-3 / ≤5% FA, FA binding.
