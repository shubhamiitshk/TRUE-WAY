# ml/ — workstation retrieval pipeline (blueprint §7, §18)

Trains the on-device encoder adapter, builds the pack's vector index, **fits the decision
calibration**, and scores the open-set benchmark. The evaluation protocol (splits,
open-set false accepts, margins, effective sample size) is fixed before any number is
reported, and the harness **fails loudly** when the gate fails.

## Protocol (§7.6, §18.3)

- Split by **source subject series**, never by near-duplicate shuffle. `source_photo_id` and
  `source_subject_id` are the grouping units and `ml/audit/check_split_integrity.py` enforces
  them in CI. A subject series (several photographs of the same monument from the same visit) is
  never split across two splits.
- Known queries: `top1_known`, `top3_known`.
- Unknown queries (shops, scaffolding, lookalike brickwork, vegetation):
  `false_accept_rate` — accepted-as-POI / all unknowns.
- The false-accept bound is computed at the **EFFECTIVE** sample size — the number of distinct
  source **subject series** — because augmented rows and same-visit photographs are not
  independent trials.
- Thresholds are **learned from a held-out calibration split**, never
  tuned on the final test. Cosine ≥ 0.80-style constants are rejected. The device reads them
  from the pack.
- Every reference photograph must carry an `approved` human verdict in
  `ml/dataset/verification_review.json` before it may enter the corpus.
- The calibration split must be **representative** of the test split: whole subject groups are
  distributed across the splits proportionally, because a hash-ordered split gave the calibration
  set 2 of 24 visually confusable photographs and the test set 10, and the fitted threshold then
  failed to transfer.

## The corpus pipeline

```
ml/harvest_candidates.py              download → ml/dataset/candidates/   (QUARANTINE)
ml/audit/build_verification_review.py verdicts for the original corpus
ml/audit/approve_candidates.py        verdicts for quarantined candidates
ml/promote_candidates.py              approved candidates → the corpus
ml/resplit_dataset.py                 re-split by source photograph
ml/train_arcface_pipeline.py          train → index + calibration + benchmark
ml/export_parity_vectors.py           golden vectors for the cross-language parity test
```

Nothing in `ml/dataset/candidates/` is ever read by the training pipeline until a reviewer
approves it, so an unreviewed harvest can never poison the model.

## The encoder pipeline

```
ml/train_arcface_pipeline.py    train the adapter (PyTorch)
ml/convert_encoder.py           export ONNX, then build + MEASURE five TFLite variants
ml/build_index_from_artifact.py extract the gallery WITH the chosen artefact
android/fetch_vision_assets.ps1 stage the chosen artefact into the APK assets
ml/train_arcface_pipeline.py    re-export the index, the calibration and the benchmark
```

`ml/rebuild_encoder.py` runs the whole sequence, in the order that works. The order matters and
getting it wrong produces a **silently wrong pack** rather than an error: the index records the
digest of the encoder that produced the reference vectors, and the device refuses a pack whose
digest does not match the encoder it ships.

Two properties are enforced, not assumed:

- **the exported graph must compute the training function on REAL photographs**
  (`cos >= 0.995`, measured 0.999933). Every earlier check compared the artefact with *itself*
  - ONNX against TFLite, and the export against a reimplementation of its own arithmetic - so a
  graph that computed a different function passed every gate. The pre-fix graph scored **0.04**
  against the training pipeline on a real photograph.
- **the shipped variant is the measured one.** Five variants are built and timed; the fastest
  acceptable one ships. On this machine: **fp16 (23.3 MB, cos 1.0000)**, fp32 (46.5 MB,
  647 ms), int8 dynamic-range (12.3 MB, 2 756 ms), int8 per-axis (12.6 MB, 3 422 ms) and int8
  per-tensor (11.8 MB, 3 445 ms) - the two smallest are the two slowest **and** the two that
  fail the agreement floor.

## The decision rule

`ml/vision_index.py` is the single source of truth; the Android device mirrors it exactly
(`BinaryVectorIndex.evaluate`), and a cross-language parity test keeps them honest.

```
place_score(p) = mean of the top-k similarities to p's reference vectors   (robust top-k mean)
open_margin    = place_score(winner) - best hard-negative similarity      ("is it one of ours?")
place_margin   = place_score(winner) - place_score(runner-up place)       ("which one of ours?")

ACCEPT iff place_score(winner) >= accept_threshold
     and open_margin             >= relative_threshold
     and place_margin            >= sibling_margin
```

The two margins are deliberately separate: the runner-up PLACE is a *different true class*, so
folding it into the open-set margin penalises legitimate fine-grained confusions.

## Latency Planning Targets (TrueWay v3.0 Gate 3)

TrueWay v3.0 defines actual end-to-end planning targets as:
- **P50 capture-to-card < 2.5 s**
- **P95 capture-to-card < 6.0 s**

These planning targets reflect the complete on-device user pipeline (CameraX capture → frame preprocessing → vector inference → cosine/kNN retrieval → card display in Compose UI on reference mid-tier hardware), explicitly replacing isolated sub-second (e.g. `<500ms`) model-only inference claims.

## Statistical Sample Design & Benchmark Specification (v3.0 Finding A)

### Negative Sample Size & Binomial Upper Bound
The vision benchmark requires:
- **At least 100 diverse, independent hard negatives** (shops, scaffolding, off-circuit stupas, lookalike brickwork, street clutter, vegetation) as the practical initial benchmark target.
- **At least 150 diverse known monument photos** across varied lighting, angles, weather, and camera sensors.

**Statistical Rationale (Clopper-Pearson / One-Sided Binomial Upper Bound):**
To establish with 95% confidence that the unknown false-accept rate (FAR) is below 5% ($\le 5\%$):
- For a sample of $N$ independent negative trials yielding $k$ false accepts, the one-sided 95% upper confidence bound $p_{\text{upper}}$ satisfies:
  $$(1 - p_{\text{upper}})^N = 0.05 \implies p_{\text{upper}} = 1 - 0.05^{1/N}$$
- At $N = 50$ negatives with zero errors ($k = 0$), $p_{\text{upper}} = 1 - 0.05^{1/50} \approx 5.82\% > 5.0\%$. A 50-negative test is therefore mathematically inconsistent with proving $\le 5\%$ FAR even with zero false accepts.
- At $N = 59$ negatives with zero errors ($k = 0$), $p_{\text{upper}} = 1 - 0.05^{1/59} \approx 4.98\% \le 5.0\%$.
- Requiring **$N \ge 100$ independent hard negatives** provides necessary practical headroom:
  - At $k = 0$ errors: $p_{\text{upper}} \approx 2.95\%$.
  - At $k = 1$ error: $p_{\text{upper}} \approx 4.66\% \le 5.0\%$.

### Calculating Confidence Intervals for Observed Errors
If errors occur ($k \ge 1$), do not rely solely on the point estimate $k / N$. Calculate exact binomial confidence intervals (e.g., Clopper-Pearson or Wilson score intervals) to verify whether the upper confidence bound remains below 5%.

### Interpretation of Synthetic Test Split Results
The current 33.3% false-accept rate (1 false accept out of 3 unknown queries in `ml/fixtures/sample_scores.csv` test split at threshold 0.80) demonstrates that the tiny synthetic toy test split fails the release gate. However, 3 synthetic samples cannot characterize the real-world model's actual failure rate. Production validation demands real-world field photography meeting the $\ge 100$ hard negatives target.

## Evaluation Fixture Accounting (`ml/fixtures/sample_scores.csv`)

The synthetic baseline fixture `sample_scores.csv` contains **19 total lines** (1 CSV header + 18 data rows):
- **1 Header row**: `query_id,query_kind,place_id,correct_place_id,score,margin,top3_hit,split,photographer,visit`
- **10 Calibration split rows (`split == "calib"`)**:
  - 7 known queries: `q-maha-001`, `q-maha-002`, `q-wall-001`, `q-wall-002`, `q-shanti-001`, `q-nal-001`, `q-nal-002`
  - 3 unknown queries: `q-unk-shop-001`, `q-unk-brick-001`, `q-unk-veg-001`
- **8 Test split rows (`split == "test"`)**:
  - 5 known queries: `q-maha-t1`, `q-wall-t1`, `q-shanti-t1`, `q-nal-t1`, `q-nal-t2`
  - 3 unknown queries: `q-unk-shop-t1`, `q-unk-scaffold-t1`, `q-unk-brick-t1`
- **Total data rows**: 10 calib + 8 test = **18 rows**.

*(Audit Finding G04 Note: A prior remediation report stated "nine calibration queries + eight test queries = 17" against the 18-row fixture. The discrepancy arose from an arithmetic error in the report miscounting calibration as 9 instead of 10; the underlying fixture strictly contains 10 calibration rows and 8 test rows, totaling 18 data rows.)*

## Use (stdlib only)

```powershell
python ml\evaluate_retrieval.py --input ml\fixtures\sample_scores.csv --threshold 0.0
```

Columns: `query_id,query_kind[known|unknown],place_id,correct_place_id,score,margin,split[calib|test],photographer,visit`.
`place_id` is the top-1 prediction; `score` its fused similarity.

## Companion scripts (ADR-0003)

- `rebuild_encoder.py` — runs the whole encoder rebuild in the order that works: train →
  export ONNX → convert + measure → extract the gallery with the winner → stage it into the APK
  assets → re-export the index. Each step is a **separate process** (the TFLite converter's peak
  memory plus the training process exceeds the commit limit on a host with no page file), and the
  gallery extraction and the staging both happen **before** the final export, because the index
  records the digest of the encoder that produced the reference vectors.
- `build_index_from_artifact.py` — extracts the reference vectors **with the deployed artefact**,
  reproducing the device's own preprocessing (shortest side to 256, centre crop, `[0, 1]`, NHWC)
  and the model's own output normalisation.
- `vision_index.py` — the decision rule, single source of truth, mirrored by
  `BinaryVectorIndex.evaluate` on the device.
- `harvest_training_dataset.py` — harvests real monument & hard-negative field
  photography from Wikimedia Commons across all 15 Bihar Buddhist Circuit POIs
  (210 raw $\rightarrow$ 300 multi-view images: 60 ref, 90 calib, 150 test) and
  8 distractor categories (136 raw $\rightarrow$ 176 images: 24 ref, 48 calib,
  104 test) with global title deduplication and strictly disjoint
  `(photographer, visit)` splits (`ml/dataset/dataset_manifest.json`).
- `train_arcface_pipeline.py` — extracts 512-dim `MobileCLIP-S0` (`fastvit_mci0`,
  `[0.0, 1.0]` RGB) embeddings, trains a $512 \times 512$ `LinearResidualAdapter`
  with `SubCenterArcFace(k_subcenters=3)`, calibrates acceptance thresholds on
  the held-out calibration split, and exports `ml/models/s0/arcface_adapter.pt`,
  `ml/adapter_weights.json`, `ml/fixtures/embeddings_bihar.csv`,
  `ml/fixtures/refcentroids_bihar.csv`, `content/vision/reference_index.json`,
  and `TWVEC001` binary indexes (`reference_vectors.bin`, `index.bin`,
  `reference_vectors.meta.json`).
- `train_adapter.py` — frozen-encoder diagonal linear adaptation protocol
  (stdlib-only). Verifies per-dimension diagonal scaling on `ml/fixtures/embeddings_bihar.csv`
  (144/150 Top-1 on test split) and `--selftest`.
- `convert_encoder.py` — keeps the trained `LinearResidualAdapter` as a **separate `Linear`
  after** the L2 normalisation (folding it into `head.fc` is not equivalent), reparameterizes
  `MobileOneBlock`/`RepMixer` branches, folds each `LayerScale2d` into **the op that produces
  its channels**, replaces `erf`-GELU with `tanh`-GELU for pure `TFLITE_BUILTINS`
  compatibility, exports `mci_s0.onnx` (46.6 MB), converts via `onnx2tf` to **five** measured
  TFLite variants (fp32 46.5 MB / 647 ms, **fp16 23.3 MB / 558 ms — the one that ships**,
  int8 dynamic-range 12.3 MB / 2 756 ms, int8 per-axis 12.6 MB / 3 422 ms, int8 per-tensor
  11.8 MB / 3 445 ms), embeds MediaPipe `TFLITE_METADATA`, and **fails the build** if the
  exported graph does not reproduce the training computation on real photographs
  (`cos >= 0.995`; measured 0.999933) or if a variant disagrees with ONNX/FP32 below
  cos 0.80. `ml/rebuild_encoder.py` runs the whole rebuild in the order that works.

## Status

- ✅ Real Wikimedia Commons dataset harvested (`ml/dataset/dataset_manifest.json`), now
  **human-verified**: every source photograph was inspected visually and carries an
  `approved` / `rejected` verdict in `ml/dataset/verification_review.json`. A first review of
  the original corpus rejected **41 of 85** source photographs — a Shanghai *replica* of the
  Mahabodhi Temple labelled as the temple, three photographs of a bamboo grove in **Kyoto**
  labelled as Venu Vana in Rajgir, portraits of a politician labelled as the Shanti Stupa, a
  lecture hall in Mumbai labelled as Nalanda Monastery 1, and a "brick ruins" class that
  contained only rendered brick textures. Unreviewed candidates are **quarantined** in
  `ml/dataset/candidates/` and are never trained on.
- ✅ Splits are grouped by **SOURCE PHOTOGRAPH** (`source_photo_id`), never by a
  near-duplicate shuffle. The previous splitter put a photometric derivative of the same
  photograph into every split while labelling the rows with disjoint-looking
  `(photographer, visit)` strings; `ml/audit/check_split_integrity.py` now fails the build if
  that ever happens again.
- ✅ Sub-Center ArcFace ($K=3$) + `LinearResidualAdapter` trained on real `MobileCLIP-S0`
  512-dim embeddings. The index now ships **one or more references per place** (not a single
  blended centroid) and a **negative bank** (not 8 collapsed centroids).
- ✅ The decision rule lives in ONE place — `ml/vision_index.py` — and is mirrored exactly by
  the device (`BinaryVectorIndex.evaluate`). A **cross-language parity test**
  (`android/.../vision/DecisionParityTest.kt`) replays 309 golden vectors through the real
  binary reader and asserts both sides agree.
- ✅ Evaluation harness computes the full blueprint §7.6 metric set and the FAR bound at the
  **EFFECTIVE** sample size (distinct source photographs), and **exits non-zero when the gate
  fails** — it previously always exited 0, so CI could never block.
- ✅ Thresholds are **fitted on the held-out calibration split** and shipped in the pack; the
  device no longer uses hard-coded constants.
- ✅ Mandatory plain baselines are evaluated alongside the adapter on the same split
  (`ml/fixtures/linear_baseline_report.json`): the adapter reaches **86 %** top-1 against
  **83 %** (frozen centroid), **83 %** (adapted centroid) and **84 %** (logistic regression).
- ✅ **Top-1 and Top-3 clear their gates**, and the point false-accept rate is below the
  target: on the verified, source-grouped corpus (12 vision classes), with the gallery
  extracted by the **deployed encoder artefact**, Top-1 **91.1 %** (112/123), Top-3 **96.8 %**
  (138/139), coverage **68.3 %**, abstention **31.7 %**, accepted-set precision **100.0 %**, and
  a false-accept rate of **1.1 %** of rows and **2.3 %** of independent subject series
  (2 of 87).
- ⚠️ **Gate 2 (G03) is still NOT met**, for two reasons that are reported rather than
  smoothed over: the Clopper-Pearson 95 % bound at the effective n of 87 is **8.30 %** (a
  certificate at <= 5 % needs ZERO false accepts at an effective n of at least 59), and the test
  split's known side has **41** independent series against the 150 the gate asks for. The
  abstention rate on true matches is **31.7 %** against a <= 30 % target: the hard-negative bank
  now contains each class's genuine lookalikes, so a true match and its best bank negative are
  close by construction. See `docs/audit/GATE2_BASELINE.json` for the recorded metrics and the
  outstanding items.

## What the corpus actually contains

The corpus is small, and the size of the *image* corpus is misleading: the unit of independence
is a **subject series** (photographs of the same monument from the same visit are near-duplicates
of each other).

| | photographs | independent subject series |
|---|---|---|
| known POIs (12 vision classes) | 341 | 114 |
| hard negatives (13 categories) | 457 | 237 |

**635 source photographs are approved and 27 rejected**, out of 2 201 candidates that have
been through the review; everything else is explicitly *pending* and is kept out of the corpus
(`ml/audit/sync_review_to_tables.py` keeps the review file and the review tables in step). Every approval is recorded in
`ml/dataset/verification_review.json` with a reason, and every corpus photograph must carry an
`approved` verdict or `ml/audit/check_split_integrity.py` fails the build.

Three of the fifteen circuit places are **search-only** (`vision_class: false` in the POI spec):
the Bodhi Tree, the Vajrasana and the Nalanda Archaeological Museum. A photograph of them is not
separable from their surroundings, so they are spotter items on the parent place's card rather
than separate vision classes (blueprint §7.2).

Most classes still have only **1-3** reference photographs *from independent visits*. That single
fact caps every accuracy number in this repository, and it is a collection problem, not a
modelling one.

## The decision rule

`ml/vision_index.py` is the single source of truth; the Android device mirrors it exactly
(`BinaryVectorIndex.evaluate`), and a cross-language parity test keeps them honest.

```
place_score(p) = mean of the top-k similarities to p's reference vectors   (robust top-k mean)
open_margin    = place_score(winner) - best hard-negative similarity      ("is it one of ours?")
place_margin   = place_score(winner) - place_score(runner-up place)       ("which one of ours?")

ACCEPT iff place_score(winner) >= accept_threshold
     and open_margin             >= relative_threshold
     and place_margin            >= sibling_margin
```

The two margins are deliberately separate: the runner-up PLACE is a *different true class*, so
folding it into the open-set margin penalises legitimate fine-grained confusions.

## Latency Planning Targets (TrueWay v3.0 Gate 3)

TrueWay v3.0 defines actual end-to-end planning targets as:
- **P50 capture-to-card < 2.5 s**
- **P95 capture-to-card < 6.0 s**

These planning targets reflect the complete on-device user pipeline (CameraX capture → frame preprocessing → vector inference → cosine/kNN retrieval → card display in Compose UI on reference mid-tier hardware), explicitly replacing isolated sub-second (e.g. `<500ms`) model-only inference claims.

## Statistical Sample Design & Benchmark Specification (v3.0 Finding A)

### Negative Sample Size & Binomial Upper Bound
The vision benchmark requires:
- **At least 100 diverse, independent hard negatives** (shops, scaffolding, off-circuit stupas, lookalike brickwork, street clutter, vegetation) as the practical initial benchmark target.
- **At least 150 diverse known monument photos** across varied lighting, angles, weather, and camera sensors.

**Statistical Rationale (Clopper-Pearson / One-Sided Binomial Upper Bound):**
To establish with 95% confidence that the unknown false-accept rate (FAR) is below 5% ($\le 5\%$):
- For a sample of $N$ independent negative trials yielding $k$ false accepts, the one-sided 95% upper confidence bound $p_{\text{upper}}$ satisfies:
  $$(1 - p_{\text{upper}})^N = 0.05 \implies p_{\text{upper}} = 1 - 0.05^{1/N}$$
- At $N = 50$ negatives with zero errors ($k = 0$), $p_{\text{upper}} = 1 - 0.05^{1/50} \approx 5.82\% > 5.0\%$. A 50-negative test is therefore mathematically inconsistent with proving $\le 5\%$ FAR even with zero false accepts.
- At $N = 59$ negatives with zero errors ($k = 0$), $p_{\text{upper}} = 1 - 0.05^{1/59} \approx 4.98\% \le 5.0\%$.
- Requiring **$N \ge 100$ independent hard negatives** provides necessary practical headroom:
  - At $k = 0$ errors: $p_{\text{upper}} \approx 2.95\%$.
  - At $k = 1$ error: $p_{\text{upper}} \approx 4.66\% \le 5.0\%$.

### Calculating Confidence Intervals for Observed Errors
If errors occur ($k \ge 1$), do not rely solely on the point estimate $k / N$. Calculate exact binomial confidence intervals (e.g., Clopper-Pearson or Wilson score intervals) to verify whether the upper confidence bound remains below 5%.

### Interpretation of Synthetic Test Split Results
The current 33.3% false-accept rate (1 false accept out of 3 unknown queries in `ml/fixtures/sample_scores.csv` test split at threshold 0.80) demonstrates that the tiny synthetic toy test split fails the release gate. However, 3 synthetic samples cannot characterize the real-world model's actual failure rate. Production validation demands real-world field photography meeting the $\ge 100$ hard negatives target.

## Evaluation Fixture Accounting (`ml/fixtures/sample_scores.csv`)

The synthetic baseline fixture `sample_scores.csv` contains **19 total lines** (1 CSV header + 18 data rows):
- **1 Header row**: `query_id,query_kind,place_id,correct_place_id,score,margin,top3_hit,split,photographer,visit`
- **10 Calibration split rows (`split == "calib"`)**:
  - 7 known queries: `q-maha-001`, `q-maha-002`, `q-wall-001`, `q-wall-002`, `q-shanti-001`, `q-nal-001`, `q-nal-002`
  - 3 unknown queries: `q-unk-shop-001`, `q-unk-brick-001`, `q-unk-veg-001`
- **8 Test split rows (`split == "test"`)**:
  - 5 known queries: `q-maha-t1`, `q-wall-t1`, `q-shanti-t1`, `q-nal-t1`, `q-nal-t2`
  - 3 unknown queries: `q-unk-shop-t1`, `q-unk-scaffold-t1`, `q-unk-brick-t1`
- **Total data rows**: 10 calib + 8 test = **18 rows**.

*(Audit Finding G04 Note: A prior remediation report stated "nine calibration queries + eight test queries = 17" against the 18-row fixture. The discrepancy arose from an arithmetic error in the report miscounting calibration as 9 instead of 10; the underlying fixture strictly contains 10 calibration rows and 8 test rows, totaling 18 data rows.)*

## Use (stdlib only)

```powershell
python ml\evaluate_retrieval.py --input ml\fixtures\sample_scores.csv --threshold 0.0
```

Columns: `query_id,query_kind[known|unknown],place_id,correct_place_id,score,margin,split[calib|test],photographer,visit`.
`place_id` is the top-1 prediction; `score` its fused similarity.

## Companion scripts (ADR-0003)

- `rebuild_encoder.py` — runs the whole encoder rebuild in the order that works: train →
  export ONNX → convert + measure → extract the gallery with the winner → stage it into the APK
  assets → re-export the index. Each step is a **separate process** (the TFLite converter's peak
  memory plus the training process exceeds the commit limit on a host with no page file), and the
  gallery extraction and the staging both happen **before** the final export, because the index
  records the digest of the encoder that produced the reference vectors.
- `build_index_from_artifact.py` — extracts the reference vectors **with the deployed artefact**,
  reproducing the device's own preprocessing (shortest side to 256, centre crop, `[0, 1]`, NHWC)
  and the model's own output normalisation.
- `vision_index.py` — the decision rule, single source of truth, mirrored by
  `BinaryVectorIndex.evaluate` on the device.
- `harvest_training_dataset.py` — harvests real monument & hard-negative field
  photography from Wikimedia Commons across all 15 Bihar Buddhist Circuit POIs
  (210 raw $\rightarrow$ 300 multi-view images: 60 ref, 90 calib, 150 test) and
  8 distractor categories (136 raw $\rightarrow$ 176 images: 24 ref, 48 calib,
  104 test) with global title deduplication and strictly disjoint
  `(photographer, visit)` splits (`ml/dataset/dataset_manifest.json`).
- `train_arcface_pipeline.py` — extracts 512-dim `MobileCLIP-S0` (`fastvit_mci0`,
  `[0.0, 1.0]` RGB) embeddings, trains a $512 \times 512$ `LinearResidualAdapter`
  with `SubCenterArcFace(k_subcenters=3)`, calibrates acceptance thresholds on
  the held-out calibration split, and exports `ml/models/s0/arcface_adapter.pt`,
  `ml/adapter_weights.json`, `ml/fixtures/embeddings_bihar.csv`,
  `ml/fixtures/refcentroids_bihar.csv`, `content/vision/reference_index.json`,
  and `TWVEC001` binary indexes (`reference_vectors.bin`, `index.bin`,
  `reference_vectors.meta.json`).
- `train_adapter.py` — frozen-encoder diagonal linear adaptation protocol
  (stdlib-only). Verifies per-dimension diagonal scaling on `ml/fixtures/embeddings_bihar.csv`
  (144/150 Top-1 on test split) and `--selftest`.
- `convert_encoder.py` — keeps the trained `LinearResidualAdapter` as a **separate `Linear`
  after** the L2 normalisation (folding it into `head.fc` is not equivalent), reparameterizes
  `MobileOneBlock`/`RepMixer` branches, folds each `LayerScale2d` into **the op that produces
  its channels**, replaces `erf`-GELU with `tanh`-GELU for pure `TFLITE_BUILTINS`
  compatibility, exports `mci_s0.onnx` (46.6 MB), converts via `onnx2tf` to **five** measured
  TFLite variants (fp32 46.5 MB / 647 ms, **fp16 23.3 MB / 558 ms — the one that ships**,
  int8 dynamic-range 12.3 MB / 2 756 ms, int8 per-axis 12.6 MB / 3 422 ms, int8 per-tensor
  11.8 MB / 3 445 ms), embeds MediaPipe `TFLITE_METADATA`, and **fails the build** if the
  exported graph does not reproduce the training computation on real photographs
  (`cos >= 0.995`; measured 0.999933) or if a variant disagrees with ONNX/FP32 below
  cos 0.80. `ml/rebuild_encoder.py` runs the whole rebuild in the order that works.

## Status

- ✅ Real Wikimedia Commons dataset harvested (`ml/dataset/dataset_manifest.json`), now
  **human-verified**: every source photograph was inspected visually and carries an
  `approved` / `rejected` verdict in `ml/dataset/verification_review.json`. A first review of
  the original corpus rejected **41 of 85** source photographs — a Shanghai *replica* of the
  Mahabodhi Temple labelled as the temple, three photographs of a bamboo grove in **Kyoto**
  labelled as Venu Vana in Rajgir, portraits of a politician labelled as the Shanti Stupa, a
  lecture hall in Mumbai labelled as Nalanda Monastery 1, and a "brick ruins" class that
  contained only rendered brick textures. Unreviewed candidates are **quarantined** in
  `ml/dataset/candidates/` and are never trained on.
- ✅ Splits are grouped by **SOURCE PHOTOGRAPH** (`source_photo_id`), never by a
  near-duplicate shuffle. The previous splitter put a photometric derivative of the same
  photograph into every split while labelling the rows with disjoint-looking
  `(photographer, visit)` strings; `ml/audit/check_split_integrity.py` now fails the build if
  that ever happens again.
- ✅ Sub-Center ArcFace ($K=3$) + `LinearResidualAdapter` trained on real `MobileCLIP-S0`
  512-dim embeddings. The index now ships **one or more references per place** (not a single
  blended centroid) and a **negative bank** (not 8 collapsed centroids).
- ✅ The decision rule lives in ONE place — `ml/vision_index.py` — and is mirrored exactly by
  the device (`BinaryVectorIndex.evaluate`). A **cross-language parity test**
  (`android/.../vision/DecisionParityTest.kt`) replays 309 golden vectors through the real
  binary reader and asserts both sides agree.
- ✅ Evaluation harness computes the full blueprint §7.6 metric set and the FAR bound at the
  **EFFECTIVE** sample size (distinct source photographs), and **exits non-zero when the gate
  fails** — it previously always exited 0, so CI could never block.
- ✅ Thresholds are **fitted on the held-out calibration split** and shipped in the pack; the
  device no longer uses hard-coded constants.
- ✅ Mandatory plain baselines are evaluated alongside the adapter on the same split
  (`ml/fixtures/linear_baseline_report.json`): the adapter reaches **86 %** top-1 against
  **83 %** (frozen centroid), **83 %** (adapted centroid) and **84 %** (logistic regression).
- ✅ **Top-1 and Top-3 clear their gates**, and the point false-accept rate is below the
  target: on the verified, source-grouped corpus (12 vision classes), with the gallery
  extracted by the **deployed encoder artefact**, Top-1 **91.1 %** (112/123), Top-3 **96.8 %**
  (138/139), coverage **68.3 %**, abstention **31.7 %**, accepted-set precision **100.0 %**, and
  a false-accept rate of **1.1 %** of rows and **2.3 %** of independent subject series
  (2 of 87).
- ⚠️ **Gate 2 (G03) is still NOT met**, for two reasons that are reported rather than
  smoothed over: the Clopper-Pearson 95 % bound at the effective n of 87 is **8.30 %** (a
  certificate at <= 5 % needs ZERO false accepts at an effective n of at least 59), and the test
  split's known side has **41** independent series against the 150 the gate asks for. The
  abstention rate on true matches is **31.7 %** against a <= 30 % target: the hard-negative bank
  now contains each class's genuine lookalikes, so a true match and its best bank negative are
  close by construction. See `docs/audit/GATE2_BASELINE.json` for the recorded metrics and the
  outstanding items.

## What the corpus actually contains

The corpus is small, and the size of the *image* corpus is misleading: the unit of independence
is a **subject series** (photographs of the same monument from the same visit are near-duplicates
of each other).

| | photographs | independent subject series |
|---|---|---|
| known POIs | 177 | 123 (across 15 POIs) |
| hard negatives | — | 16 (across 8 categories) |

Eight of the fifteen POIs still have only **2–3** verified photographs, and the flagship
`in-bihar-bodhgaya-mahabodhi` has **two** — the genuine Mahabodhi Temple photographs are scarce
on Commons and the search returns a Shanghai *replica*, a 1890s photograph and a close-up of a
pillar. That single fact caps every accuracy number in this repository.

