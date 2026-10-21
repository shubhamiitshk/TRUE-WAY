# vision/ — P0 scanner on-device shell (blueprint §7–§8, ADR-0003)

| File | Role |
|---|---|
| `RetrievalEngine.kt` | Pure ranking + accept/abstain math (cosine, top-K, top-2-mean place aggregation, calibrated gate). Zero Android deps — JVM-tested. |
| `BinaryVectorIndex.kt` | Memory-mapped zero-copy **`TWVEC002`** binary vector index: **float32** gallery, one or more reference vectors per place, a negative bank, and the two-margin decision rule. |
| `VisionCalibration.kt` | The pack's **learned** calibration: absolute floor, relative (open-set) threshold, hard-negative margin, sibling margin, related-pair margin, and a Platt calibrator. An incomplete calibration is REFUSED, not defaulted. |
| `GeoPrior.kt` | Bounded, heavy-tailed geographic **soft prior** — a re-ranker, never a gate. |
| `DeviceLocationProvider.kt` | Optional coarse, last-known location. No tracking, no listener; absence is normal. |
| `ReferenceStore.kt` | Pack `reference_index.json` and `vision/reference_vectors.bin` loader: `TWVEC002` metadata parsing with `TWVEC001` fallback. |
| `ScanPipeline.kt` | `runScanBlocking`: active pack index → encoder → bounded EXIF-aware decode → embed (flip TTA) → rank → decide, every failure an explicit state. |
| `MediaPipeEmbedder.kt` | Single-shot `ImageEmbedder` wrapper (`RunningMode.IMAGE`) plus a process-scoped `VisionEncoder` holder (one encoder, one dedicated thread). |
| `../../test/.../DecisionParityTest.kt` | **Cross-language parity**: replays 146 golden vectors through the real binary reader and asserts the device reaches the same decision the workstation evaluator does. |
| `../../test/.../VisionCalibrationTest.kt` | Calibration parsing, the pack-vs-default provenance, and the geo prior's bounds. |
| `../../test/.../BinaryVectorIndexTest.kt` | The decision rule: top-k mean, open margin, sibling/related ambiguity, geo re-ranking. |

## The decision rule

```
place_score(p) = mean of the top-k similarities to p's reference vectors   (robust top-k mean)
open_margin    = place_score(winner) - best hard-negative similarity      ("is it one of ours?")
place_margin   = place_score(winner) - place_score(runner-up place)       ("which one of ours?")

ACCEPT iff place_score(winner) >= accept_threshold
     and open_margin             >= relative_threshold
     and place_margin            >= sibling_margin      (related pairs use related_margin)
```

The two margins are deliberately **separate**: the runner-up PLACE is a *different true class*, so
folding it into the open-set margin penalises legitimate fine-grained confusions. A parent site and
its child (or two siblings) that look alike are reported as an **ambiguous pair** rather than forced
onto one of them (blueprint §7.2).

The same rule is implemented on the workstation in `ml/vision_index.py`; the parity test keeps the
two honest.

## States

- No asset → `NotInstalled` → existing "recognition is not installed yet" UX.
- Asset present → `Ready` (CPU) or GPU attempt with CPU retry on `Failed`.
- Pack present but **no complete calibration** → `Uncalibrated`: the scanner ranks for diagnostics
  and shows **no names** (§3 principle 2 — abstention over fabrication).
- Thresholds come from the **pack**, learned on the held-out calibration split — no constants, no
  percentage UI until the calibrated probabilities are validated in the field.

## Asset pipeline

`android/fetch_vision_assets.ps1` stages the locally converted MobileCLIP-S0 model
(`ml/models/s0/mci_s0_fp16.tflite`, 23.3 MB, 512-dim with the Sub-Center ArcFace adapter as a
separate `Linear` after the L2 normalisation, and MediaPipe `TFLITE_METADATA`) into
`app/src/main/assets/vision_encoder.tflite` (gitignored), falling back to the 4.1 MB MediaPipe
MobileNetV3-small sample only if no local artefact exists. **Which variant ships is decided by
measurement, not by file size**: `ml/convert_encoder.py` builds five variants and times them, and
records the fastest acceptable one in `ml/models/s0/conversion_log.json`. On the development
machine that is fp16 (239 ms, cos 1.0000 vs ONNX) - the two *smallest* variants are the two
slowest ones (1 726 ms and 2 607 ms) **and** the two that fail the agreement floor.

The pack manifest `vision` section records the
**digest of the actual encoder artefact** so a model/pack mismatch can be refused, together with
the full learned calibration. The digest is the one of the encoder that produced the reference
vectors, and CI checks that the APK's encoder and the APK's vector index agree.
