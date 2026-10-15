# vision/ — P0 scanner on-device shell (blueprint §7–§8, ADR-0003)

| File | Role |
|---|---|
| `RetrievalEngine.kt` | Pure ranking + accept/abstain math (cosine, top-K, top-2-mean place aggregation, calibrated gate). Zero Android deps — JVM-tested. |
| `BinaryVectorIndex.kt` | Memory-mapped zero-copy `TWVEC001` binary vector index loader with INT8 quantization, prototype evaluations, and sibling calibration policy. |
| `ReferenceStore.kt` | Pack `reference_index.json` and `index.bin` loader: binary `TWVEC001` check with fallback to JSON Ready/Uncalibrated/Empty. |
| `ScanPipeline.kt` | `runScanBlocking`: active pack index → encoder → bounded EXIF-aware decode → embed → rank → decide, every failure an explicit state. |
| `MediaPipeEmbedder.kt` | Single-shot `ImageEmbedder` wrapper (`RunningMode.IMAGE`), GPU→CPU delegate ladder, encoder-agnostic asset `vision_encoder.tflite`, honest `NotInstalled` state. |
| `../../test/.../RetrievalEngineTest.kt` | 6/6: cosine, ranking, aggregation, accept/low/ambiguous/empty. |

## States

- No asset → `NotInstalled` → existing "recognition is not installed yet" UX.
- Asset present → `Ready` (CPU) or GPU attempt with CPU retry on `Failed`.
- Thresholds are learned (ml sweep on held-out visits), passed into
  `decide()` — no constants, no percentage UI until calibrated.

## Asset pipeline

`android/fetch_vision_assets.ps1` fetches the floor model (MediaPipe
MobileNetV3-small, ~4 MB, Apache-2.0 sample) into `app/src/main/assets/`
(gitignored). The MobileCLIP-S0 `.tflite` replaces it under the same
filename when conversion unblocks (`ml/models/CONVERSION_LOG.md`); pack
manifest `vision` records identity + dim for mismatch refusal (wired at
benchmark week with the dim check in this package).
