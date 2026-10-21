# TrueWay — Detection Pipeline Audit & Improvement Recommendations

> ## Implementation outcome (added after the remediation work)
>
> The recommendations in §4 have been **implemented**. The audit's own measurements are now
> reproducible, the gate can fail, and the corpus is human-verified. What changed, and what the
> system now measures:
>
> | | Before (claimed) | Before (measured, leak-free) | **Now (after remediation)** |
> |---|---|---|---|
> | Top-1 | 100.0 % | 77.8 % (LOPO CV) | **91.1 %** (112/123) |
> | Top-3 | 100.0 % | 85.4 % | **96.8 %** (119/123) |
> | Accepted-set precision | - | - | **100.0 %** (84/84) |
> | Coverage / abstention | 2.7 % abstention | 64.4 % abstention | **68.3 % / 31.7 %** |
> | FAR (point, rows) | 0.0 % | 9.2 % | **1.0 % (2/197)** |
> | FAR (point, independent subject series) | 0.0 % | - | **3.3 % (3 of 91)** |
> | FAR (Clopper-Pearson 95 %, effective n) | 2.95 % | 64.0 % | **8.30 %** (effective n = 91) |
> | Independent test subject series | - | - | **41 known / 91 negative** |
> | Vision classes | 15 | 15 | **12** (3 places are search-only) |
> | Corpus | 85 photos, 44 mislabelled | - | **635 approved / 27 rejected**, 798 photographs, 13 hard-negative categories |
>
> **Gate 2 (G03) still does not pass, and now fails loudly.** Both accuracy gates clear, and the
> point false-accept rate is **2.3 %** (2 of 87 independent negative series) - below the <= 5 %
> the gate asks for. What does not clear is the **certificate**: the Clopper-Pearson 95 % bound at
> an effective n of 91 is **8.30 %**, and a certificate at <= 5 % needs **zero** false accepts at
> an effective n of at least 59. The requirement is now precise:
>
> * **>= 150 independent known subject series** in the test split (currently 56)
> * **>= 10 independent reference photographs per vision class**, from different
>   photographers and visits
> * **zero** false accepts on the holdout, or a materially larger effective n
> * a lower abstention rate on true matches (31.7 % against a <= 30 % target): the hard-negative
>   bank now contains each class's genuine lookalikes, so a true match and its best bank
>   negative are close by construction
> * the field benchmark on physical hardware in the Bodh Gaya / Nalanda corridor
>
> Three of the fifteen circuit places are now **search-only** (the Bodhi Tree, the Vajrasana and
> the Nalanda Archaeological Museum): a photograph of them is not separable from their
> surroundings, so they are surfaced as spotter items on the parent place's card instead
> (blueprint §7.2).
>
> **What was built**
>
> * **Corpus** - 1 900 candidates harvested into a **quarantine** and **reviewed photograph by
>   photograph**: **635 approved, 27 rejected**, plus a set of corpus photographs rejected on a
>   second full visual pass (carved railing panels of the Mahabodhi temple scattered across four
>   different POI classes; monks and generic tree-and-fence shots in the Bodhi Tree class; a
>   brick mound in the museum class; golden-Buddha close-ups in the Venu Vana class; the
>   Parinirvana, Bodhisattva and Mahavira statues next door to the Shanti Stupa). The rejected
>   photographs are now *evidence*, not silent damage, and the candidate pool is never trained on
>   until a reviewer approves it.
> * **Class contamination** - the visual audit found photographs of the **Sariputta Stupa** filed
>   under the **Nalanda Mahavihara**, which made the "Temple 3" class unlearnable: every one of its
>   test photographs was predicted as the Mahavihara, because the Mahavihara references contained
>   the very stupa they were supposed to be distinguished from. Moving that series (and the two
>   other misfiled places) took Temple 3 from **0/10** to **10/10**. The same audit found the
>   **Mahabodhi Temple** class starved of references - one reference series against four test
>   series, so the gallery entry for the whole class was a single photograph - and 35 further
>   photographs of the temple's own shikhara took it from **0/10** to **10/10** as well. Top-1
>   went from 79.2 % to **91.1 %**.
> * **Corpus integrity** - the camera-variation generator now stamps the **digest of its source
>   image** into the variation's filename, the re-splitter purges stale variations before every
>   split, and the embedding cache is **verified against each source image's digest**. All three
>   close a class of silent corruption in which a class centroid could be built from the pixels
>   of a *different* photograph (1 294 of 1 294 cached embeddings turned out to be stale).
> * **One subject series, one label** - a subject series that carries two place labels is now a
>   **hard failure** of `ml/audit/check_split_integrity.py`, because a near-duplicate series split
>   across two classes makes both the effective sample size and the label-conflict count
>   meaningless. The evaluator's own leakage check caught the first instance of it.
> * **Dataset** - photo-level *and* subject-level splitting (`source_photo_id` and
>   `source_subject_id`), with whole subject series distributed proportionally so every split
>   gets a representative mix, and the effective sample size counted over subject series.
> * **Decision rule** - one implementation (`ml/vision_index.py`) mirrored by the device
>   (`BinaryVectorIndex.evaluate`), with **two separate margins**: `open_margin` (winner vs the
>   hard-negative bank - the open-set gate) and `place_margin` (winner vs the runner-up place -
>   the disambiguation gate). A parent site and its child are reported as an **ambiguous pair**
>   rather than forced onto one of them (blueprint §7.2); adding that rule cut the measured
>   false-accept rate from 27.8 % to 13.9 %.
> * **Calibration** - thresholds fitted on the held-out calibration split with **leave-one-out**
>   scoring, and **shipped in the pack**; the device no longer uses hard-coded constants, and the
>   runner-up score is measured rather than fabricated.
> * **Index** - `TWVEC002`: float32 gallery, one or more reference vectors per place, a 96-vector
>   negative bank, and a digest of the actual encoder artefact.
> * **Runtime** - flip-only test-time augmentation, a bounded heavy-tailed **geo soft prior**
>   (re-ranker, never a gate), one process-scoped encoder instead of a 12 MB reload per capture,
>   and capture at >= 1024 px.
> * **Harness** - the evaluator exits non-zero on failure, computes the FAR bound at the
>   effective n, rejects a **stale** benchmark CSV, and CI adds a **dataset-integrity hard gate**,
>   a **regression check** against `docs/audit/GATE2_BASELINE.json`, and an **APK asset check**
>   (the APK under test previously had no encoder at all).
> * **Parity** - a cross-language test replays 309 golden vectors through the real binary
>   reader. It caught two live defects: a 36- vs 40-byte header mismatch and a float32-vs-float64
>   accumulation drift.
> * **Encoder export** - the exported graph now computes
>   `normalize(adapter(normalize(backbone(x))))`, i.e. **exactly** the training function. The
>   legacy export folded the adapter matrix into `head.fc`, which is *not* equivalent: the L2
>   normalisation sits between the projection and the adapter, and the adapter was fitted on
>   unit-norm inputs - so the device was applying the adapter to an unnormalised vector on
>   **every inference**. Fixing the export path also uncovered two latent crashes in it (a
>   layer-scale gamma folded with the wrong rank for conv weights, and an unguarded `qkv.bias`).
> * **The export was still wrong, and no gate could see it** - the audit's own fix was verified
>   against a *reimplementation* of the adapter, and every other check compared the artefact with
>   **itself** (ONNX vs TFLite, determinism). Nothing compared the artefact with the **training
>   pipeline**. Worse, the export-shape check computed its reference from the *same, already
>   folded* backbone instance it had handed to the exporter - so it agreed by construction, for
>   any input, and the input was irrelevant. The exported graph could therefore compute a
>   completely different function and pass every gate. It did: the layer scale of the attention
>   block was folded into the **MLP**'s weight instead of the attention projection, and the
>   static attention forward dropped the `1/sqrt(head_dim)` logit scale. Measured on a **real
>   photograph**, the cosine between the exported graph and the training pipeline was **0.04** -
>   the exported graph was orthogonal to the model it was supposed to implement.
>   Three gates now exist that could not have existed before:
>   * `ml/convert_encoder.py` runs the exported module and the training computation side by side
>     on **real corpus photographs**, with the reference computed from a **separate, unfolded**
>     backbone instance, and **fails the build** below cos 0.995 (measured: 0.999933);
>   * `ml/audit/check_encoder_parity.py` compares the exported graph against the **real training
>     adapter module** (not a reimplementation) on real photographs;
>   * the gallery, the calibration and the benchmark are extracted **with the deployed artefact**,
>     so the reference vectors are the ones the shipped model actually produces.
> * **Quantisation** - `ml/convert_encoder.py` now actually wires the Bihar domain images into
>   the converter (`representative_dataset` - it never was), produces **five** measured
>   variants (fp32, fp16, int8 per-tensor, int8 per-axis, int8 dynamic), enforces the
>   arXiv:2610.18575 agreement floor (cos >= 0.80) as a **build failure**, and **ships the
>   fastest acceptable variant** rather than the smallest. The conversion log now reports what
>   the converter *actually did* instead of what was intended. `fetch_vision_assets.ps1` stages
>   the chosen variant, and CI checks that the staged asset is **byte-identical** to it.
>   The measured result, on this machine:

>   | variant | size | latency (4-thread CPU) | cos vs ONNX | verdict |
>   |---|---|---|---|---|
>   | **fp16** | 23.3 MB | **558 ms** | **1.0000** | **shipped** |
>   | fp32 | 46.5 MB | 647 ms | 1.0000 | fallback |
>   | int8 dynamic-range | 12.3 MB | 2 756 ms | 0.9869 | acceptable, 5x slower |
>   | int8 per-axis | 12.6 MB | 3 422 ms | 0.5315 | **fails the agreement floor** |
>   | int8 per-tensor | 11.8 MB | 3 445 ms | 0.2268 | **fails the agreement floor** |

>   "Smaller is not faster" was the audit's finding and it is now the *measured* result: the two
>   smallest artefacts are the two slowest ones **and** the two that disagree with the model.
>   The previous build shipped the 12 MB INT8 model.
> * **CSLS - the hubness correction** - the similarity of a query to a gallery vector is
>   rescaled by the local density of both (`s'(q,v) = 2 s(q,v) - r_k(q) - r_k(v)`, Conneau et
>   al.). A handful of gallery vectors are close to almost everything, and those are exactly the
>   ones that turn a lookalike into a confident false accept; scaling them down by their local
>   density restores the separation. The local density of every gallery vector is computed at
>   build time and **ships in the index**, so the device applies the identical correction.
>   Measured on this corpus: the false-accept rate fell from **24 % to 2.2 %**, the abstention
>   rate on true matches from **50 % to 31.7 %**, and Top-1 held at 91.1 % on a
>   *harder* test split. Centering the embeddings (subtracting the corpus mean) was measured
>   too and made Top-1 **worse**, so it is not used.
> * **The split quota was counted in the wrong unit** - the quota was a quota of SUBJECT SERIES
>   but the count it was derived from was the number of PHOTOGRAPHS. A class with 26
>   photographs in 2 series was therefore given quotas of 10 / 5 / 11 for 2 series, and every
>   series landed in the test split: the class ended up with **no reference photographs at all**
>   and the model's predictions collapsed onto a single place. The symptom was a class with a
>   perfect score in one run and a catastrophic one in the next, depending only on how many
>   photographs a class happened to have.
> * **Near-duplicate leakage that no gate could see** - the series normalisation stripped a
>   trailing number of **one to three digits**, so a Commons photo id of eleven digits - the
>   normal form - was never stripped. Fifteen photographs of one Thai temple counted as fifteen
>   independent series and sat in the reference, the calibration **and** the test split at once.
>   The integrity gate read the same wrong id, so it agreed. There is now a hard gate for it.
> * **The calibration was fitted against a bank that contained the query's own twins** -
>   `fit_calibration` built its own working index and dropped the negative source ids, so the
>   leave-one-series-out exclusion could not remove anything. The thresholds were fitted
>   against a bank that had been optimised against the very negatives being measured.
> * **A retracted corpus change survived several rebuilds** - the approval script only ever
>   ADDED verdicts, so a photograph removed from a review table kept its old approval and
>   stayed in the corpus. `ml/audit/sync_review_to_tables.py` now recomputes every candidate
>   verdict from the tables in both directions, and CI fails if the two disagree.
> * **An unreviewed photograph could sit in the corpus** - the re-splitter kept every record
>   that was not explicitly *rejected*, so a *pending* one was trained on. Only an **approved**
>   photograph may enter the corpus now.
> * **One model, one gallery** - `ml/build_index_from_artifact.py` extracts the reference vectors
>   with the **deployed artefact**, reproducing the device's own preprocessing (shortest side to
>   256, centre crop, `[0, 1]`, NHWC) and the model's own output normalisation. The index, the
>   calibration and the benchmark are then exported from those embeddings, so the device scores
>   real photographs against the vectors its own encoder produces. Before this, the gallery was
>   extracted in PyTorch and the device ran a quantised graph - a train/serve skew of the same
>   order as the decision margins.
>
> The rest of this document is the **original audit**, retained as the evidence base.


**Scope:** every layer that decides *which place a photo is* — encoder, adapter, index, decision
rule, calibration, evaluation harness, CI gate, and the data underneath all of it.
**Method:** full read of the code path, then I **re-ran the shipped numbers myself** under a
leak-free protocol (scripts in `ml/audit/`, runnable from repo root).

---

## 0. Executive verdict

| Question | Answer |
|---|---|
| Does the scanner work as documented? | **No.** The claim "100.0% Top-1, 0.0% FAR, Gate 2 PASS" is an artifact of the *evaluation*, not of the model. |
| Root cause #1 | **Near-duplicate leakage.** All **85** distinct source photographs in the corpus appear in *every* split. The "476-image" dataset is 85 real photos inflated by synthetic augmentation. |
| Root cause #2 | **Label corruption.** The Commons free-text harvester accepted semantically wrong images. `in-bihar-rajgir-venu-vana` = **3 photos of Arashiyama Bamboo Grove, Kyoto, Japan**. `in-bihar-nalanda-monastery-01` = a lecture hall in Mumbai + a Korean temple. `in-bihar-bodhgaya-mahabodhi` = a **Shanghai replica**, an 1890s photo, and a **close-up of a pillar**. |
| Root cause #3 | **The gate is un-winnable-by-design.** `ml/evaluate_retrieval.py` never returns a non-zero exit code; CI replays a committed CSV; `ml/dataset/` + `ml/models/` are gitignored so the CSV can never be regenerated. The "Gate 2" step in CI **cannot fail** — I proved this by sabotaging the fixture to 0 % Top-1 / 100 % FAR and it still exited 0. |
| Honest measured performance (my LOPO CV) | **Top-1 77.8 % · Top-3 85.4 % · abstention on true positives 64.4 %** — both accuracy gates FAIL, and coverage is catastrophic. |
| What does the literature say? | It **independently confirms** the diagnosis (copy-detection / near-dup literature, ECCV'24 OSR statistics) **and corrects three of my own recommendations** — see §7.2. |
| What is actually good | The *architecture* is right: frozen encoder + linear adapter (ILIAS), SubCenter ArcFace, abstain-over-fabricate, signed packs, off-device-by-default. The **data and the harness** are the failure, not the design. |

> **The single highest-value change is not a model change. It is fixing the dataset and the
> evaluation protocol.** Everything else is second-order until then.

---

## 1. The actual pipeline (as implemented, not as documented)

```
CameraX single-shot capture (CameraCaptureView.kt:88-93, no ResolutionSelector)
  └─> JPEG → cacheDir/scans/
      └─> decodeBoundedWithRotation(file, maxSidePx=512)      ScanPipeline.kt:147
          └─> MediaPipeEmbedder(appContext)  ← NEW 12 MB model LOADED PER SCAN   ScanPipeline.kt:60
              └─> ImageEmbedder (CPU delegate; preferGpu=false) MediaPipeEmbedder.kt:29,47
                  └─> 512-d L2-normalised embedding
                      └─> BinaryVectorIndex.evaluate(query, SiblingCalibrationPolicy())  ScanPipeline.kt:71
                          │  • int8 dot, max-over-prototypes per place (1 prototype/place)
                          │  • hard-negative margin 0.06 → 8 category centroids
                          │  • abs threshold 0.72  → sibling margin 0.04
                          └─> RankDecision.Accepted / Uncertain
```

Supporting artifacts:

| Artifact | Path | Reality |
|---|---|---|
| Encoder | `ml/models/s0/mci_s0_int8.tflite` → `assets/vision_encoder.tflite` (12.0 MB) | **INT8 is 6× SLOWER than FP32** (1707.7 ms vs 283.6 ms, 4-thread CPU) — `conversion_log.json` |
| Index | `content/vision/reference_vectors.bin` | **15 prototypes (1/place) + 8 negative centroids** = 11 808 B |
| Adapter | `ml/models/s0/arcface_adapter.pt` | 512×512 `LinearResidualAdapter` + SubCenterArcFace K=3 |
| Reference JSON | `content/vision/reference_index.json` (728 KB) | 15 refs × 512 floats — **also 1 per place** |
| Data | `ml/dataset/` (**gitignored**) | 476 records ← **85 real photos** |

---

## 2. Findings — ranked by severity

### F1 · CRITICAL — The benchmark is fully leaked; the 100% is memorisation

`ml/harvest_training_dataset.py:439-449`:

```python
canonical_bases = records[: min(k_canonical, len(records))]     # K = 3 source photos
split_specs = [("ref",4,0,"2024-11"), ("calib",6,4,"2025-02"), ("test",10,2,"2025-08")]
for split_name, target_cnt, mode_offset, visit_prefix in split_specs:
    for i in range(target_cnt):
        base_rec = canonical_bases[i % len(canonical_bases)]     # ← SAME photo in EVERY split
```

Verified across the whole corpus:

```
distinct source photographs                 : 85
source photographs spanning >1 split        : 85  (100%)
records per class (known)                   : 3 source photos → 20 synthetic records
records per class (negatives)               : 5 source photos → 22 synthetic records
```

The "disjoint (photographer, visit) splits" are a **string trick**: `photographer` is the real
Commons author plus a synthetic suffix (`Chainwit.` → `Chainwit.#ref_0`, `Chainwit.#test_00`), and
`visit` is a hard-coded date string. `ml/README.md:11` explicitly forbids this — *"Split by
photographer/visit/viewpoint, never by near-duplicate shuffle"* — and the corpus does precisely that.

**Measured cost of the augmentation** (`ml/audit/intra_class_variance_audit.py`):

```
cosine( two synthetic derivatives of the SAME photo )   = 0.9638
cosine( two DIFFERENT photos of the same monument )     = 0.5731
```

The synthetic images are a tight near-duplicate cluster; real viewpoint variation is 4× further away.
Any non-photo-grouped split is trivially solvable — which is what produced 100%.

### F2 · CRITICAL — Label corruption in 8 of 15 known classes and 3 of 8 negative classes

`ml/audit/dataset_label_audit.py` prints the 3 (known) / 5 (negative) source titles per class.
There is **no human verification step** anywhere in `harvest_training_dataset.py`.

| Class | Actual source photographs | Verdict |
|---|---|---|
| `bodhgaya-mahabodhi` | **Jing-an Temple, Shanghai — "Bodh Gaya Mahabodhi Replica"**, "234 Anagarika Dharmapala Renovates…" (1890s), "Ajapala Nigrodha **Tree Pillar**" | 0/3 real |
| `rajgir-venu-vana` | **Arashiyama Bamboo Grove (×3), Kyoto, Japan** | 0/3 real — wrong country |
| `nalanda-monastery-01` | "A lecture hall at **SPJIMR**" (Mumbai), "5th Floor Lecture Hall", "Bixi and stupas at **Haeinsa**" (Korea) | 0/3 real |
| `rajgir-shanti-stupa` | "**Nitish Kumar addressing** at 55th anniversary…", "Member of Legislative Assembly at Rajgir" | political rallies, not the stupa |
| `nalanda-temple-03` | "Sariputra stupa temple" (different structure), 2× "**Stucco images** … exterior walls of Temple no 3" | close-ups of wall figures |
| `bodhgaya-mucalinda` | "**Bodhgaya 27 Mahabodhi Temple**" (misfiled), "Gaya Haffkine 02" (1890s), "IN Bodhgaya 0906" | misfiled + archival |
| `bodhgaya-vajrasana` | "**Huvishka coin find** from the Vajrasana" (a photo of a *coin*), "Bodh Gaya railings", "Diamond Throne Vajrasana" | 1/3 real |
| `bodhgaya-bodhi-tree` | "**Squirrel in Bodhi Tree**", "Bodhi Tree", "Bodhi Tree and Meditators" | 1 poor, 2 ok |
| `rajgir-cyclopean-wall` | "Amitabha Gupta - Cyclopean Wall - **Wiki Explores Bihar II.png**" (an **illustration**), 2 photos | 1 non-photo |
| `neg-ordinary-brick-ruins` | "**A shard of medieval ceramic vessel**", "**Bricks094 8K-PNG AmbientOcclusion.png**" (3D render), "**Bricks094 8K-PNG Color.png**", an Unsplash photo | **the single most important hard-negative class contains no ruins at all** |
| `neg-modern-commercial-shop` | "**Dublin Maritime Festival** ×3" (Ireland), "Idol stalls", "Jubilee Campus MMB I3" | 0/5 Indian shops |
| `neg-construction-scaffolding` | "**Bharat Petroleum**" (fuel station), 3 real bamboo scaffolds, "Bangalore echafaudage" | 1/5 wrong |
| `nalanda-museum`, `rajgir-sonbhandar`, `rajgir-vultures-peak`, `bodhgaya-great-buddha`, `nalanda-mahavihara` | genuine | ✅ OK |
| `neg-generic-indian-temple`, `neg-se-asian-stupa` | Bhitargaon Gupta temple; Old Bagan pagodas | ✅ excellent hard negatives |

**Quantified consequence** — the closest class pairs in embedding space are *known ↔ negative* pairs,
i.e. the broken labels literally pull positives onto negatives:

```
0.8845  nalanda-temple-03        <-> neg-se-asian-stupa
0.8709  nalanda-temple-03        <-> neg-generic-indian-temple
0.8175  bodhgaya-mahabodhi       <-> bodhgaya-great-buddha
0.8064  nalanda-mahavihara       <-> nalanda-temple-03
0.7947  nalanda-mahavihara       <-> neg-generic-indian-temple
```

And **all 7 false accepts in my LOPO CV predicted `in-bihar-nalanda-temple-03`** — the class that
is semantically "a brick stupa with stucco figures", which is exactly what the `neg-ordinary-brick-ruins`
class *should* have contained.

### F3 · CRITICAL — The Gate-2 CI step cannot fail, and cannot be re-derived

| Fact | Evidence |
|---|---|
| `evaluate_retrieval.py` **always returns 0** — `passes_gate2_statistical_bound` is printed, never raised | `ml/evaluate_retrieval.py:112-141`, `return 0` at :142 |
| CI runs the same script on a **static committed CSV** — no encoder is ever executed | `.github/workflows/trueway-ci.yml:37` |
| The dataset and models are **gitignored**, so the CSV can never be regenerated in CI | `.gitignore:36-39` (`ml/models/`, `ml/dataset/`) |
| The production audit rates the fixture **INFO**, in `can_review`, not `must_pass` | `trueway_verify_local.py:52`, `audit_evidence.json` → `synthetic_fixture: INFO` |
| The training scripts that produced the shipped model are **untracked** (`?? ml/train_arcface_pipeline.py`, `?? ml/harvest_training_dataset.py`) | `git status` |
| `vision_encoder.tflite` is **untracked** and CI never runs `fetch_vision_assets.ps1` → the CI-built APK has **no vision encoder at all** | `.gitignore:39`, `git ls-files` |

**The shipped pack is not reproducible from the repo.** `dist/trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg`
declares `vision.weights_sha256 = 81b0ecfb…`, but the current `ml/adapter_weights.json` hashes to
`7a02e96c…` — the pack was built from a *different* adapter revision. (The embedded reference
vectors agree to cosine **1.0000**, differing only in the 6th decimal, i.e. a re-run of the same
recipe — so the *numbers* are fine; the *provenance* is not.) The adapter file itself is untracked,
the dataset is gitignored, and no run-id or seed is recorded in the manifest, so **no third party can
rebuild the pack that ships.**

**Empirically demonstrated.** I took the real 250-row fixture, set every known row's prediction to
`WRONG` and every unknown row's score to `0.99`, and ran the exact CI command:

```
top1_known(raw)       0/150 = 0.0%   (gate >=85% G03)
top3_known(raw)       0/150 = 0.0%   (gate >=95% G03)
false_accept@t      100/100 = 100.0% (point FAR)
false_accept_95_upper 100.00%        (gate <=5.0%)

Gate 2 (G03) Statistical Verification: [FAIL]
...
EXIT CODE = 0        ← CI step succeeds
```

A **completely broken** benchmark still passes CI, because the failure is printed and never raised.

### F4 · CRITICAL — Effective sample size is ~3× smaller than asserted, invalidating the confidence bound

```
benchmark rows                : 150 known + 100 unknown
distinct SOURCE PHOTOGRAPHS   : known = 45, unknown = 40
```
`ml/README.md:39-41` computes the CP95 bound as if N were 100 *independent* negatives. Under a
photo-grouped split the independent N is **16–40**, and at N=16 a **perfect 0/16** run yields
**CP95 = 17.07 %** — the ≤5 % gate cannot be certified at all with the current corpus. The corpus
needs **≥ 59 independent negative photographs** (the doc's own number) *after* grouping.

### F5 · HIGH — The INT8 model was never calibrated with the domain data, and it is 6× slower than FP32

`ml/convert_encoder.py:287-299`:

```python
calib_arr = np.load(calib_npy)                  # loaded, printed…
print("[tflite] Verified N real Bihar domain images … for INT8 quantization")
c2 = tf.lite.TFLiteConverter.from_saved_model(…)
c2.optimizations = [tf.lite.Optimize.DEFAULT]
int8 = _inject_tflite_metadata(c2.convert())     # ← NO c2.representative_dataset = …
```

`representative_dataset` **never appears in the file**. The `domain_calib` / `spike_calib` flags in
`conversion_log.json` are therefore **false claims**. Consequences: activation ranges were estimated
from TFLite's default (not the Bihar domain), which is the most likely cause of both the
**0.9889 cross-backend cosine drift** and the **6× slowdown**.

### F6 · HIGH — Reference vectors were never re-extracted with the shipped INT8 model (train/serve skew)

The shipped `reference_index.json` / `.bin` come from **FP32 PyTorch** embeddings (`train_arcface_pipeline.py:476-480`).
The device runs **INT8**. Measured sensitivity (`ml/audit/int8_drift_sensitivity.py`):

```
measured cross-backend cosine 0.9889  →  direction drift 8.56°
worst-case query→reference similarity band span : 0.2402
queries whose decision could cross threshold 0.72 in either direction : 41 of 150
```

The decision band the app relies on is `abs 0.72 / margin 0.04 / 0.06`. A perturbation band of
**0.24 is 4–6× wider than the entire decision margin.** The device is making accept/abstain calls
on a score distribution it was never calibrated against.

### F7 · HIGH — The device down-samples to 512 px, but the model was trained on ~960 px inputs

`ScanPipeline.kt:46` — `maxSidePx = 512`. Training (`train_arcface_pipeline.py:56-69`) resizes the
**shortest side to 256** from the original Commons thumbnail (960 px). The device path is
`4032 px → 512 px long side → 256 px short side`, i.e. **~8× downsample then upsample**, while
training saw a 2.8× downsample of a sharp 960 px image. The model has never seen device-quality
softness. (Also: the research doc's own note — *"Resolution matters more than commonly assumed"* —
was never acted on.)

### F8 · HIGH — The pack's learned calibration is shipped but ignored; the device uses hardcoded constants

`ScanPipeline.kt:71` — `binaryIndex.evaluate(query, SiblingCalibrationPolicy())` — **all defaults**,
from `BinaryVectorIndex.kt:17-21`:

```kotlin
data class SiblingCalibrationPolicy(
    val absThreshold: Float = 0.72f,
    val hardNegativeMargin: Float = 0.06f,
    val siblingMargin: Float = 0.04f
)
```

Meanwhile `pack-builder/build_pack.py:311` writes `calibration: {accept_threshold, min_margin}` into
the manifest (I confirmed it is present in `dist/…twpkg`), and `ml/README.md:15` says *"Cosine ≥ 0.80-style
constants are rejected."* The binary path (which is the **first** path tried and therefore the one that
runs) **ignores the pack entirely** and uses constants. The JSON path *does* read them. Two different
decision systems ship simultaneously.

### F9 · HIGH — The blueprint's scoring spec is not implemented on the device

Blueprint §7.5 requires *"robust top-2 mean"* over a place's references and a *fitted* calibrator.
The shipped index has **one** prototype per place, so:
- `BinaryVectorIndex.kt:84` → **max** over prototypes (spec says top-2 mean)
- `RetrievalEngine.aggregateByPlace` (`RetrievalEngine.kt:86`) averages `top.take(2)` of a 1-element list → **dead code**
- `ScanPipeline.kt:77-78` → `supporters = 1` hardcoded
- `ScanPipeline.kt:82` → the runner-up score is **fabricated** as `score - 0.05`, not measured
- `ScanPipeline.kt:77` → `margin = 0.05` hardcoded
- **No calibrator exists anywhere** — no isotonic, no temperature scaling, no logistic fit. `Recommend1.txt:115` explicitly recommended *"Isotonic regression with temperature scaling"*; it was never built.

### F10 · HIGH — No geo prior, no TTA, no multi-reference, no re-ranking

Blueprint §7.4 specifies *"Optional GNSS as a **soft prior** using accuracy & age"* and *"record
whether the result was based mainly on visual or location evidence."* Grepping the whole Android
tree: `latitude`/`longitude` exist only for the **Offline Nearby** list (`PlaceDataSource.kt:24`) and
the trail tracker. **The scan path never touches GPS.** Meanwhile there is **no test-time
augmentation** (no flip, no multi-crop), **no query expansion**, and the geo prior — the single
cheapest lever on false accepts for a 15-POI circuit — is entirely absent.

### F11 · MEDIUM — Model reload per scan, GPU delegate never used

`ScanPipeline.kt:60` constructs `MediaPipeEmbedder(appContext)` on **every** scan → 12 MB TFLite parse
+ delegate init per capture, then `close()` in the `finally`. `MediaPipeEmbedder.kt:29` sets
`preferGpu: Boolean = false`, so the documented *"GPU attempt → CPU fallback"* ladder never runs —
the GPU path is dead code.

### F12 · MEDIUM — Model/pack mismatch protection does not exist

`build_pack.py:91` — `model_crc = sha256(model_id_string)[:8]`, a hash of a **string constant**, not of
the weights. `BinaryVectorIndex.kt:152` reads it into a local `modelCrc` and **never compares it**.
`PackImporter.kt:198` reads `vision.model_id` but never checks it against the encoder asset.
`vision.weights_sha256` in the manifest is likewise never verified on device. The only real check is
`query.size != binaryIndex.dim` — 512 vs 512, which always passes. ADR-0003's *"refuse a model/pack
mismatch"* is unimplemented.

### F13 · MEDIUM — The "10-layer offline diagnostic" reports the vision engine as PASSED without running it

`OfflineDiagnostic.kt:83-103` checks only that `vision_encoder.tflite` **exists**, and hardcodes
*"~12.0 MB MobileCLIP-S0 INT8"* in the message regardless of what is actually there. It never
initialises the embedder, never checks dim compatibility with the index, never runs one inference.

### F14 · MEDIUM — The scoring used to generate the benchmark is not the scoring that runs on device

`train_arcface_pipeline.py:619-642` (`score_query`) uses **primary centroid + all 3 sub-centres**
and invents a continuous `calibrated_score` with a **hardcoded floor of 0.18**:

```python
if (s1 - s_neg_max) < 0.06:
    calibrated_score = min(s1, max(0.18, s1 - (0.06 - (s1 - s_neg_max)) * 2.5))
```

`BinaryVectorIndex.kt:96-98` **abstains** in that situation — it has no such score, and no floor.
Consequences in the shipped CSV: **94 of 100 "unknown" rows have a score of exactly 0.18** (7 unique
values across 100 rows). The FAR number is therefore a **constant**, not a measurement. The benchmark
also scores the K=3 sub-centres, which the binary index **does not contain**.

### F15 · LOW — Metrics required by the spec are never computed

`ml/evaluate_retrieval.py` never computes **accepted-set precision**, **abstention rate on unknowns**,
**per-class error**, or **worst-site confusion** — all required by blueprint §7.6. The calibration
sweep at :132-141 is **print-only** and never selects the threshold. `top1_raw` reads the CSV's own
`place_id` and `top3_hit` columns, so the harness can only detect parse errors, never a wrong prediction.

### F17 · HIGH — The vision corpus is not reconciled with the project's own rights registry

`content/seed/rights_registry.json` → `assets[]` already records the **legal status of a reference
photograph per POI**:

```json
{ "place_id": "in-bihar-bodhgaya-mahabodhi", "photo_status": "WITHHELD",
  "reason": "Device restrictions at the temple; search-only POI, no reference capture suggested on site." }
{ "place_id": "in-bihar-nalanda-temple-03", "photo_status": "TO_COLLECT" }   ← + 4 more
```

**6 of the 15 POIs have no approved reference photography** — one is explicitly *withheld* because
photographing the Mahabodhi Temple is prohibited on site. Yet the shipped index contains a reference
vector for **all 15**, and the Mahabodhi entry's `distinguishing_hint` reads
*"55m pyramidal main temple spire and central courtyard"* — i.e. the model actively prompts a user to
photograph a site where the app itself says devices are banned (`BeforeYouEnterData`, blueprint risk
register: *"Camera prohibited in flagship site"*).

The harvester never reads `rights_registry.json`, so a POI whose photo status is `TO_COLLECT` or
`WITHHELD` still gets a trained class, sourced from Commons, with no rights review.

### F16 · LOW — The 250-query benchmark was changed after the audit, and the README reports the new number
`git status` shows `M ml/fixtures/retrieval_benchmark_250.csv` (500 lines changed, uncommitted):

| | Top-1 | FAR | CP95 |
|---|---|---|---|
| committed (`HEAD`) — what CI runs | 98.0 % (147/150) | 1.0 % | 4.66 % |
| working tree — what `README.md:33` quotes | **100.0 %** | **0.0 %** | **2.95 %** |

`docs/audit_v3_release_gates.md:26` still quotes the committed numbers. Whatever changed, the
improvement was obtained by **regenerating the benchmark**, and the repo now advertises the
uncommitted figure as the release-gate result.

---

## 3. The numbers I measured myself

`ml/audit/leave_one_photo_out_cv.py` — leave-one-photograph-out CV: every class holds out its
*r*-th source photograph, the stack (adapter + SubCenterArcFace + centroids) is **retrained** on the
rest, and the held-out photographs are scored with the **exact** `BinaryVectorIndex` rule.

```
POOLED out-of-fold: known = 500 queries (from 45 independent photographs), unknown = 176
  Top-1 (raw)               389/500 = 77.8%      gate ≥85%   ✗ FAIL
  Top-3 (raw)               427/500 = 85.4%      gate ≥95%   ✗ FAIL
  coverage (accepted)        178/500 = 35.6%
  abstention on TRUE hits    322/500 = 64.4%     spec ≤30%   ✗ FAIL
  accepted-set precision    178/178 = 100.0%
  FALSE ACCEPTS               7/176 = 3.98%      point
  CP95 at EFFECTIVE N=40     30.37%              gate ≤5%    ✗ FAIL
  known score   min 0.190  p10 0.373  med 0.564  max 0.934
  unknown score min 0.162  p10 0.236  med 0.345  max 0.796   ← heavy overlap
```

**Seed stability** (the number is not a lucky seed):

| seed | Top-1 | Top-3 |
|---|---|---|
| 42 (shipped) | 77.8 % | 85.4 % |
| 1 | 78.2 % | 85.8 % |
| 7 | 78.0 % | 85.2 % |
| 2026 | 78.6 % | 86.2 % |
| **mean ± σ** | **78.1 % ± 0.3 %** | **85.7 % ± 0.4 %** |

Both accuracy gates fail by ~7 and ~9 points respectively, and that is with the *frozen-encoder +
adapter* stack trained on the **same 45 photographs** that a real field benchmark would never see twice.

Threshold sweep on the honest out-of-fold scores:

```
 thr   coverage   abst_known   FAR      CP95@N_eff   accepted-precision
0.50    62.2%      37.8%      9.66%     56.69%          92.0%
0.60    44.6%      55.4%      5.68%     38.71%          93.3%
0.65    39.0%      61.0%      3.98%     30.37%          99.5%
0.72    35.6%      64.4%      3.98%     30.37%         100.0%   ← shipped threshold
0.78    26.6%      73.4%      1.70%     18.26%         100.0%
0.80    21.2%      78.8%      0.00%      7.22%         100.0%
```

**Reading of the sweep:** the shipped threshold 0.72 is *precision-optimal* but *coverage-disastrous*.
There is **no threshold at which the current corpus can certify a ≤5 % FAR** — even 0 errors at the
true effective N of 40 photographs gives CP95 = 7.22 %. **The corpus, not the threshold, is the binding
constraint.** (Caveat: training on 2 of 3 photos is pessimistic; with the 10–30 photos/POI the spec
demands, both coverage and accuracy improve. That is the point of the next section.)

Per-class out-of-fold Top-1 — this is the "worst-site confusion" the spec asks for and the evaluator never prints:

```
in-bihar-bodhgaya-mahabodhi        0/34     ← class = Shanghai replica + 1890s photo + a pillar
in-bihar-bodhgaya-bodhi-tree      12/32
in-bihar-nalanda-monastery-01     22/34     ← class = Mumbai lecture hall + Korean temple
in-bihar-rajgir-cyclopean-wall    23/34
in-bihar-nalanda-mahavihara       24/32
in-bihar-bodhgaya-vajrasana       27/34     ← class contains a photo of a coin
in-bihar-bodhgaya-mucalinda       28/34     ← misfiled Mahabodhi + archival photo
in-bihar-rajgir-sonbhandar        27/32
in-bihar-nalanda-museum           30/34
in-bihar-bodhgaya-great-buddha    29/32
in-bihar-bodhgaya-animesh-lochan  33/34
in-bihar-rajgir-vultures-peak     34/34
in-bihar-rajgir-venu-vana         32/32     ← class = 3 photos of Kyoto bamboo grove
in-bihar-rajgir-shanti-stupa      34/34     ← class = political rallies
in-bihar-nalanda-temple-03        34/34     ← and it is the class that absorbs all 7 false accepts
```

---

## 4. Recommendations

### P0 — Stop the bleeding (do these first; most are small diffs)

| # | Change | Where | Why |
|---|---|---|---|
| **P0-1** | **Make the CI gate able to fail.** `evaluate_retrieval.py` must `return 1` when `passes_gate2_statistical_bound` is false, and CI must assert on it. | `ml/evaluate_retrieval.py:112-142` | A gate that cannot fail is decoration. This is a 5-line fix with the highest leverage in the repo. |
| **P0-2** | **Stop publishing 100 % / 0 % FAR.** Correct `README.md:33`, `docs/SPRINT_PLAN.md`, `ml/README.md:104`, `docs/audit_v3_release_gates.md:26` to the honest numbers, and label the current result `WITHDRAWN — evaluated on a leaked split`. | docs | The repo's own principle §3.2 is *"Abstention over fabrication"*; it currently applies to place names but not to metrics. |
| **P0-3** | **Freeze the benchmark.** Any change to `retrieval_benchmark_250.csv` must be accompanied by a diff of the *model* and a re-run from a clean checkout with the dataset committed. Commit `ml/dataset/dataset_manifest.json` (metadata only, not the images) and the split assignment. | `.gitignore:36` | Makes every future number comparable. |
| **P0-4** | **Track `ml/train_arcface_pipeline.py` and `ml/harvest_training_dataset.py`** and add `fetch_vision_assets.ps1` to CI so the APK under test actually contains the encoder. | `git status` | The scripts that produce the product are untracked; the CI APK has no vision model. |
| **P0-5** | **Implement the model/pack binding.** Hash the actual encoder file, put it in the manifest, verify on import; make `model_crc` a hash of the *weights*, not of the model-id string. | `build_pack.py:91`, `PackImporter.kt:191-199`, `BinaryVectorIndex.kt:152` | Closes a real integrity hole and makes F12 go away. |
| **P0-6** | **Honour the pack calibration.** Load `calibration` from the manifest/index and feed it into `SiblingCalibrationPolicy` instead of `SiblingCalibrationPolicy()`. | `ScanPipeline.kt:71` | One-line fix that makes the "learned thresholds in the pack" contract true. |

### P1 — Fix the data (this is where the accuracy actually comes from)

| # | Change | Why it matters |
|---|---|---|
| **P1-1** | **Manually verify every reference photograph.** Replace the free-text Commons search with an explicit, human-curated allow-list per POI (the repo already has `content/seed/rights_registry.json` — extend it with a `vision_reference` table: `place_id, source_url, photographer, licence, viewpoint_tag, verified_by, verified_at`). Reject anything that is a replica, an engraving/archival photo, a close-up of a detail, a rally/crowd shot, or outside the region. **Make `rights_registry.assets[].photo_status` the source of truth**: a POI whose status is `TO_COLLECT` or `WITHHELD` must not get a trained vision class at all (F17), and the harvester must refuse to create one. | F2, F17. 8 of 15 classes and 3 of 8 negative classes are unusable today, and 6 of 15 POIs have no approved reference photo. A **verified, small** corpus beats an unverified large one. |
| **P1-2** | **Make "photo-level" the unit of splitting, enforced in code.** Split on `original_url` (or a new `source_photo_id`), and add a CI check that asserts *zero* shared `source_photo_id` across `ref`/`calib`/`test`. Add a perceptual-hash near-duplicate detector (pHash/dHash) over the corpus and fail CI on any cross-split pair above a threshold. | F1, F4. This is the single change that makes every future metric mean something. |
| **P1-3** | **Grow to the spec's minimum: ≥10–20 independently sourced viewpoints per POI** (`content/DATASET_RESEARCH_AND_HARVESTING_SPECIFICATION.md:57`, `content/field/COLLECTION_PROTOCOL.md:10`) — across different photographers, sessions, days, devices, lighting, and viewpoints (façade / 3-4 view / partial crop / daylight / shade / distance / moderate occlusion). Record `photographer_id`, `visit_date`, `device_model` per session, per the existing collection protocol. | The measured cost of one extra *independent* photo is enormous: intra-photo cosine 0.96 vs cross-photo 0.57. 3 photos/POI cannot support a 15-way fine-grained task. |
| **P1-4** | **Rebuild the hard-negative set with the classes that actually matter for this circuit** — specifically *Nalanda-like brick stupas* (the true confusion partner of `nalanda-temple-03`), *Bodh Gaya tree/foliage* (which currently collides with `bodhi-tree` **and** the mislabelled `venu-vana`), *polished/modern brickwork*, *restoration scaffolding on a stupa*, *other Bihar Buddhist sites outside the pack* (Vikramshila, Kesariya, Pawapuri). Delete the 3D-rendered brick textures and the Dublin street photos. | F2. The negative class that matters most is the one that is empty. |
| **P1-5** | **Solve the known↔negative collision explicitly.** `neg-natural-foliage-landscape` (Ficus religiosa) collides with `bodhi-tree`; `neg-generic-indian-temple` (Bhitargaon) is pulled onto `nalanda-temple-03` at 0.87. | Both members of a colliding pair must never be in the same training set without a margin loss that separates them. |
| **P1-6** | **De-duplicate the raw corpus with encoder embeddings + perceptual hash, before every split.** Encode all 210+ downloads with the deployed encoder, compute the full cosine matrix, and flag any pair above a τ tuned on the random-pair null distribution; add a pHash/dHash pass for exact re-encodes. DINOv2 + LSH/HNSW on this task reaches top-1 retrieval AUC 0.98–0.99, so this is cheap and reliable. Also de-duplicate the *sources* themselves — Wikimedia has near-duplicate uploads of the same photo, which is how 4 cross-place label conflicts entered the corpus. | arXiv:2312.07273; arXiv:2304.07193 (DINOv2 removes near-duplicates of benchmark test sets from its pretraining pool — the industry-standard practice). Closes the residual leakage after P1-2. |

### P2 — Fix the model + decision layer

| # | Change | Where | Why |
|---|---|---|---|
| **P2-1** | **Fix the quantization properly, then benchmark on the real device.** Three changes, in order: (a) set `c2.representative_dataset` to the 64 Bihar-domain NHWC samples already computed (`ml/models/s0/domain_calib_nhwc.npy`) — it is currently *never set*; (b) enable **per-axis (per-channel)** weight quantization — the LiteRT 8-bit spec states per-axis "has large improvements to accuracy"; (c) try **dynamic-range INT8** (4× smaller, 2–3× speedup, **needs no representative dataset**, keeps activations float so the int8-attention-op-fallback pathology is avoided) and **FP16** alongside full-INT8. Then measure FP32 / FP16 / dyn-INT8 / full-INT8 per-tensor / full-INT8 per-channel **on the target ARM phone** — the 1707 ms figure is a 4-thread **x86** number (likely no VNNI), where int8 GEMM via AVX2 is slower than FP32 FMA, a pathology documented for Cortex-A73/A53. **Ship whichever is actually faster.** | `ml/convert_encoder.py:287-299` | F5. The current INT8 path is both slower *and* less accurate. This is a pure win. LiteRT quant. spec; arXiv:2509.21173 (quantised CLIP can be **4× slower** than FP32) |
| **P2-2** | **Re-extract every reference vector with the *shipped* model** (same artifact, same runtime as production), and **store the gallery as float32, not int8**. The entire index is 15 places × 20 refs × 512 floats ≈ 600 KB — int8 saves ~300 KB in a 104 MB APK while adding a *second* quantization error on top of the model's, on top of an asymmetric per-tensor rounding of unit-norm vectors. | `train_arcface_pipeline.py:476-487`; `build_pack.py:63-69` | F6. Closes the train/serve skew and removes a free source of error. |
| **P2-3** | **Raise the capture resolution.** `maxSidePx` 512 → 1024, or better, add a `ResolutionSelector` and capture at ≥1080 px long side. Retrieval at 1024² > 512² > 256² is documented (Radenović et al., CVPR 2018) — resolution is a first-order factor, more so than head changes. | `ScanPipeline.kt:46,147-171`; `CameraCaptureView.kt:88-93` | F7. The model sees device-grade softness today. |
| **P2-4** | **Ship multiple references per place and implement the spec's aggregation.** Store 10–30 real reference vectors per place (30 refs × 70 POIs × 512 floats ≈ 4.3 MB float32 — affordable), include the K sub-centres, and change `BinaryVectorIndex.evaluate` from **MAX** to **robust top-2 mean** in *both* the binary and JSON paths. MAX is a multiple-comparisons statistic: as M grows, the max of M near-null scores rises, so the threshold silently depends on M. Where photos are scarce, **Embedding Expansion** (arXiv:2003.02546) buys view diversity in embedding space at no collection cost. | `BinaryVectorIndex.kt:73-86`; `RetrievalEngine.kt:86` | F9. Currently the multi-reference architecture in the blueprint exists only in prose, and the two device paths compute different statistics. |
| **P2-5** | **Build the calibrator the spec requires — and fix the score statistic first.** Step 1: replace the **absolute** cosine gate with a **relative** score (`top-k_mean_cosine(winner) − max(second_best_place, best_negative)`), or a **softmax/entropy over the candidate set**. Miller et al. (ECCV 2024) find raw cosine to be the *weakest* open-set statistic of the three, and that relative scores transfer far better across encoder swaps. Step 2: fit an **isotonic** (≥300 points) or **Platt** (fewer) calibrator on the calibration split. Step 3: choose the threshold as the **most permissive** value whose Clopper–Pearson 95 % upper bound on FAR is ≤ target. Step 4: ship the fitted calibrator + the calibration query set in the pack, and version them with the encoder. | blueprint §7.5; `Recommend1.txt:115`; arXiv:2403.16528 | F9. Turns "a magic constant" into "a measured operating point" and makes the gate reproducible. |
| **P2-6** | **Add the geo prior as a bounded, heavy-tailed *re-ranker* — never as a gate.** `final = cosine + λ·log prior`, `log prior = −d_km/(τ + d_km/κ)` (Student-t tail so a single multipath/spoofed/stale fix saturates instead of annihilating), `λ ∈ [0, 0.3]`, `τ` = the **measured** within-place GPS σ, `λ → 0` when GPS is denied/stale/jumps implausibly. Record `evidenceKind = VISION | VISION+GPS`. | `ScanPipeline.kt`, `GeoUtils.kt`, `PlaceDataSource.kt:24` | F10. The cheapest FAR reduction, and it is already 80 % built. A prior that can *create* an accept is a spoofing liability. |
| **P2-7** | **Add 2-view horizontal-flip TTA with MeTTA** (embed image + mirror, L2-normalise each, average, re-normalise). MeTTA reports +0.9–1.7 pts on ImageNet linear for *global* features, which is exactly our case. **Do NOT use crop/brightness/blur/rotate as TTA** — those are precisely the transforms the training set is synthesised from, so they would flatter the invalid benchmark and add no genuine invariance. | `ScanPipeline.kt` | F10. Cheapest real accuracy win; also reduces score variance, tightening the calibrated threshold. |
| **P2-8** | **Move to the LiteRT V2 Compiled Model API** (the officially mandated path — `tensorflow/lite` is in maintenance mode), with automated accelerator selection, confirmed-XNNPACK, explicit `num_threads`, and the **adapter + L2-normalise folded into the exported graph**. Hoist `MediaPipeEmbedder` to a process-scoped singleton (init once, close on background). **Benchmark GPU vs CPU before enabling the GPU delegate** — MediaPipe's own Pixel 6 numbers show GPU *slower* than CPU for MobileNet-V3-small (7.83 ms vs 3.94 ms). If you target Snapdragon, evaluate the **LiteRT QNN accelerator** (AOT-compiled; up to 100× vs CPU, 56/72 models <5 ms on 8 Elite Gen 5; INT8 weights required for HTP). | `ScanPipeline.kt:60`; `MediaPipeEmbedder.kt:29` | F11. Removes a 12 MB model load from every capture and is the only way the TTA budget (P50 < 2.5 s) actually becomes available. |
| **P2-9** | **Make a plain calibrated linear/softmax head on the same frozen features a mandatory baseline.** In a 2026 audit on frozen DINOv2-giant features (18–28 classes), real class prototypes beat **exactly permuted** ones by **≤1 point** after fusion, and a matched logistic regression on the same support set matched or beat the fused system (within 0.5 pt on T-LESS, exceeding it on HOPE). A 512×512 adapter + Sub-Center-ArcFace (K=3) on 15 classes × ≤3 source photos is very likely **over-parameterised**. If the linear baseline wins, delete the training pipeline. | `train_arcface_pipeline.py` | arXiv:2609.04381. Either it wins and you delete complexity, or you have proof the adapter earns its keep. |
| **P2-10** | **Swap the encoder checkpoint to `apple/MobileCLIP2-S0`.** Identical architecture, **identical 11.4 M image params, identical 1.5 ms mobile latency**, retrained on DFN-DR instead of DataComp-DR. Everything downstream (adapter, quantization, index) is unchanged. Do **not** swap to a ViT (DINOv2/DINOv3-ViT) — MobileOne re-parameterises to a pure conv net at inference, which is the most XNNPACK/QNN-friendly thing you can ship. If you want a stronger *teacher* (not on-device), DINOv2 ViT-S/14 is the documented kNN-retrieval king (+41 % mAP Oxford-Hard over SSL). | `ml/convert_encoder.py` | arXiv:2508.20691 (TMLR'25); arXiv:2304.07193. Cheap, zero-architecture-change, measurable — but measure **R@1**, not zero-shot IN-1k (SOTA VLMs lose 17.5 pts from R@5 to R@1 on fine-grained instances). |

### P3 — Evaluation, CI and observability

| # | Change | Why |
|---|---|---|
| **P3-1** | **Replace the CSV-replay gate with an executable benchmark.** Commit the *manifest* (not the images) and the reference vectors; make CI re-run the **real encoder** over the held-out set and re-derive the metrics. Keep a CSV only as an artefact, never as the source of truth. | F3. |
| **P3-2** | **Compute the full §7.6 metric set**: Top-1, Top-3, accepted-set precision, coverage, abstention (known *and* unknown), FAR + CP95 at the **effective** N, per-class error, worst-site confusion, P50/P95 capture-to-card. | F15. |
| **P3-3** | **Report metrics at the *effective* N**, and assert `N_independent ≥ 59` negatives and `≥ 150` independent knowns before the gate can pass. | F4. |
| **P3-4** | **Add an end-to-end on-device benchmark** (the `CameraRecognitionTest.kt` / `PerformanceBenchTest.kt` suites exist but only compile): run N captures on a physical device, record per-stage timings (capture / decode / embed / search), assert P50 < 2.5 s, P95 < 6 s. | `docs/audit_v3_release_gates.md:28` (G05), `docs/FINAL_ASSESSMENT.md:171-184`. |
| **P3-5** | **Make the offline diagnostic actually exercise the vision engine**: init the embedder, run one inference, assert the embedding dim matches the index dim, and report the *actual* model bytes/ID. | F13. |
| **P3-6** | **Add an abstention-quality metric the product cares about**: the North Star is *"% of sessions where a user reads a full place card"*. Track `accepted → card opened` and `abstained → manual search resolved` so the team can see whether a higher abstention rate is actually costing sessions. | `README.md:10`. |
| **P3-7** | **Adopt the Oxford/Paris 3-tier protocol, scaled to 15 places.** **Easy** = same place, different day. **Medium** = gallery additionally holds every *visually confusable* neighbouring place as a hard distractor (the Oxford/Paris "1 M hard negatives" analogue). **Hard** = Medium + within-place distractors (different façade/entrance) + season/night/crowd variation. Report R@1, R@3, mAP, **AUROC** of the accept score, FAR-at-target-recall and recall-at-target-FAR, **per place**, plus a *generalised* split (knowns + unknowns mixed) so that rejecting everything is never optimal. | arXiv:1803.11285; arXiv:2403.16528 (report **AuPR, P@95R, R@95P** so your numbers are comparable to the literature). |
| **P3-8** | **Add an FP32-vs-INT8 output-agreement CI gate.** Compute the cosine between the FP32 and INT8 models' output embeddings on a fixed sample and fail the build below **0.8** — every architecture tested in the source paper fell below the FP32 baseline under that threshold. Cheap: one extra forward pass. | arXiv:2610.18575. Turns F5/F6 into a build-time invariant instead of a discovery. |

---

## 5. What to stop claiming (and what to claim instead)

| Currently claimed | Reality | Say instead |
|---|---|---|
| "100.0 % Top-1, 0.0 % FAR, Gate 2 PASS" | leaked split; 100 % of source photos span all splits; 94/100 negatives scored by a hardcoded floor | "Gate 2 is **not met**. Under a photo-grouped split the measured Top-1 is **77.8 %** on the current 85-photograph corpus. The corpus must be rebuilt and re-verified." |
| "476 multi-view images across 15 POIs" | **85 real photographs**, 476 synthetic derivatives | "**85 source photographs** (3 per POI) expanded to 476 augmented records." |
| "strictly disjoint (photographer, visit) splits" | the real Commons photographer is in every split; only the *label string* differs | "splits are **not** photo-grouped; this is being fixed." |
| "DOMAIN-CALIB Bihar monument corpus (INT8 weights + float I/O)" | `representative_dataset` is never set | "INT8 was calibrated with TFLite's default (non-domain) ranges." |
| "0 % FAR" | 94/100 negatives were scored by a hardcoded floor of 0.18; effective independent N ≈ 40–45 photos | **Rule of three:** 0 errors in *n* independent trials ⇒ 95 % upper bound ≈ **3/n**. At n=250 that is 1.2 %; at the true effective n it is **≈6.7 %** |
| "Cosine ≥ 0.72 means it is a known place" | 0.72 is a function of encoder, adapter, quantization, resolution **and the number of prototypes you MAX over** | **Relative score → isotonic/Platt calibrator → threshold by Clopper–Pearson** (Miller et al. find raw cosine to be the *weakest* open-set statistic) |
| "126/126 JVM tests green" + "apk PASS" | the vision engine is not exercised by any test; the CI APK has no encoder asset | "126 JVM tests pass; **no test executes the vision path**." |
| "Sub-Center ArcFace (K=3) preserves distinct viewpoints" | K=3 sub-centres are trained but **only 1 blended centroid per place reaches the device**; on frozen features a matched linear head matched or beat the fused system (arXiv:2609.04381) | "sub-centres are trained; **only the blended primary centroid is exported**; a plain linear baseline is now mandatory." |
| "≤2.5 s P50 capture-to-card" | INT8 encoder alone measures **1.71 s** on 4-thread *x86* CPU, plus a 12 MB model load per scan | "capture-to-card latency is **unmeasured on target hardware**; the shipped INT8 model is 6× slower than FP32 *on x86 without VNNI*." |
| "Our hard negatives are hard" | 176 augmented derivatives of 40 source photos, collapsed into 8 centroids | The copy-detection literature uses **100 000 train / 24 252 test** hard pairs (arXiv:2205.12358) and 1 M hard distractors (Oxford/Paris). We are 3–4 orders of magnitude short. |
| "We are validated at 15–70 class scale" | **no published evidence exists** for transfer to a 15-class single-district set; instance-level ability is domain-specific (OpenCLIP ViT-G/14 → 6.5 GAP on Met vs DINOv2 ViT-S's 29.4) and R@1 sits 17.5 pts below R@5 even for SOTA VLMs | "Our own leakage-free benchmark is the only evidence we have — which is why it must be good." |
| "GWS25k / Pikachu are our target benchmarks" | **GWS25k does not exist** (0 hits in arXiv, OpenAlex, GitHub, web); the real GWS15k is a planet-scale geo-localization set with SOTA **0.88 % within 1 km** | Cite **Google Landmarks v2**, **Oxford/Paris** (arXiv:1803.11285), **AmsterTime**. |

---

## 6. Reproduction

```powershell
cd C:\Users\PLEXTEK\Desktop\TRUE-WAY
python ml/audit/dataset_label_audit.py        # F2 — label integrity, all 23 classes
python ml/audit/intra_class_variance_audit.py # F1 — 0.9638 vs 0.5731 cosine
python ml/audit/leave_one_photo_out_cv.py     # §3 — honest LOPO CV + threshold sweep
python ml/audit/int8_drift_sensitivity.py     # F6 — 8.56° drift, 41/150 decisions at risk
```

---

## 7. State of the Art — literature synthesis and what it changes

*Full source list with URLs and verification status is in the companion file
`docs/audit/VISION_DETECTION_SOTA_SOURCES.md`.*

### 7.1 The literature **confirms** the diagnosis, independently

| Our finding | Independent literature support |
|---|---|
| Test set is a near-duplicate of the gallery | Copy-detection is a first-class field precisely for this: NDEC (AAAI'23, arXiv:2205.12358) adds **100 000 train / 24 252 test** hard-negative pairs; Meta DISC21 is 1 M refs + 100 k queries; the Inverted Multi-Index (CVPR'12/'14) and Photo Tourism (ACM TOG'06) are the canonical defences. **Our 176 augmented negatives are 3–4 orders of magnitude short of "hard".** |
| DINOv2's own pipeline removes near-duplicates of every benchmark's test set from its pretraining pool | arXiv:2304.07193 — *this is the industry standard we are not following* |
| The corpus has ~85 real photographs, not 476 | arXiv:2312.07273: DINOv1/v2 + LSH on near-dup detection reaches top-1 AUC 0.98–0.99 — a ready-made, cheap recipe to *prove* the leakage (P1-6) |
| "0 % FAR" is not a defensible claim | **Rule of three:** 0 errors in *n* independent trials ⇒ 95 % upper bound ≈ **3/n**. At n=250 that is 1.2 %, not 0 %; at the true effective n≈45 it is **6.7 %** |
| Absolute cosine threshold is not portable | Miller et al. (ECCV'24, arXiv:2403.16528): *"raw similarity in VLM feature space is not the best indicator of open-set error, with measures of relative similarity comparative to other classes offering better performance"* |
| The Sub-Center-ArcFace adapter may be over-engineered | arXiv:2609.04381 (2026): real class prototypes beat **exactly permuted** ones by **≤1 point** after fusion; **matched logistic regression matched or beat** the fused system (within 0.5 pt on T-LESS, exceeding it on HOPE). Switching the query protocol from white-cutout to real background moved prototype accuracy by **43.3 points** — *protocol dominates architecture* |
| INT8 can be much slower than FP32 | arXiv:2509.21173: quantised CLIP runs **4× slower** than FP32 (B/32: 19.6 ms FP32 → 81.1 ms INT8); Google AI Dev Forum documents int8-slower-than-fp32 on Cortex-A73/A53 (no DOTPROD) |
| TFLite Interpreter is the wrong API | LiteRT v2 README: *"MUST USE: The Compiled Model API … DO NOT USE: the TensorFlow Lite Interpreter API … tensorflow/lite/ are in maintenance mode"* |
| The GPU delegate is not automatically faster | MediaPipe's own Pixel 6 benchmark: MobileNet-V3-small **3.94 ms CPU vs 7.83 ms GPU** — delegate overhead dominates small graphs |

### 7.2 Corrections the literature forces on *my own* recommendations

| My earlier advice | Corrected advice | Why |
|---|---|---|
| "Ship FP32 (45.5 MB)" | **First try dynamic-range INT8 + per-axis**, and **measure on the target phone** | The 1707 ms is a 4-thread **x86** number, almost certainly without VNNI, where int8 GEMM via AVX2 is *slower* than FP32 FMA. On a Cortex-A55/A78 with DOTPROD, INT8 should win. LiteRT's own numbers: dynamic-range = 4× smaller, **2–3× speedup, no calibration set needed** |
| "Enable the GPU delegate" | **Benchmark CPU vs GPU first**, then choose | MediaPipe's own numbers show GPU *losing* to CPU on small CNNs |
| "Add multi-crop TTA" | **Flip-only MeTTA.** Do **not** use crop/brightness/blur/rotate as TTA | Those are exactly the transforms the training set is synthesised from; using them at test time would flatter the invalid benchmark and buy no genuine invariance |
| "Use the geo prior to cut FAR" | Use it as a **bounded heavy-tailed re-ranker (λ ∈ [0, 0.3]), never as a gate** | A prior that can *create* an accept is a spoofing/urban-multipath liability. Note also that within one district the prior's discriminative power is near zero — its real value is rejecting **far** negatives (TIGeR, CVPR'26) |
| "Swap to a stronger encoder" | Swap **MobileCLIP-S0 → MobileCLIP2-S0** (same 11.4 M params, same 1.5 ms, better data), **not** to a ViT | MobileOne re-parameterises to a pure conv net at inference — the most XNNPACK/QNN-friendly graph you can ship. A ViT brings LayerNorm/GELU/attention-matmul, which is precisely why the current INT8 path is slow |
| "More reference photos per POI" | Same — but add **Embedding Expansion** (arXiv:2003.02546) to buy view diversity *without* new photography | Useful as a bridge while the field protocol is being executed |

### 7.3 What the literature says we should **not** expect

- **No published evidence exists** for transfer to a 15-class, single-district, low-diversity landmark set. The nearest evidence warns that instance-level ability is **domain-specific** (OpenCLIP ViT-G/14 collapses to **6.5 GAP on Met** while DINOv2 ViT-S/14 reaches 29.4 — a 4.5× gap from a 5× *larger* model) and that **fine-grained R@1 sits ~17.5 points below R@5** even for SOTA VLMs. Our own benchmark is therefore the only evidence we have — which makes getting it right non-negotiable.
- **A sobering operating-point reference:** Miller et al. report that on COCO open-vocabulary detectors, at ~95 % precision **less than 12 % of true positives are retained**. A ≤5 % FAR with high coverage is genuinely hard; "abstain 64 %" is not a bug in the threshold, it is the *correct* behaviour of a well-calibrated conservative gate on a weak corpus. Fix the corpus, not the threshold.
- **Two benchmarks commonly cited do not exist / are not what they seem:** "GWS25k" (0 results in arXiv, OpenAlex, GitHub and web search — the real one is **GWS15k**, Clark et al. CVPR'23, a *planet-scale geo-localization* set where SOTA is **0.88 % within 1 km**, i.e. not an instance-retrieval benchmark at all) and the "Where in the World (**Pikachu**)" name (WITW is real — 164 455 Flickr↔satellite pairs, IQT, not publicly released — but "Pikachu" is unconfirmed). **Cite Google Landmarks v2, Oxford/Paris (arXiv:1803.11285) and AmsterTime instead.**
- **There is no published retrieval-per-MB / retrieval-per-ms table for our exact regime.** Build one on our own corpus (encoders × quantisation × resolution → R@1 / mAP / FAR / on-device ms), rather than citing someone else's regime.

### 7.4 The corrected top-12 (merged with §4)

| # | Action | Expected impact | Effort |
|---|---|---|---|
| **1** | Re-split by **source photo**; rebuild the query set from genuinely independent photos | Converts an artefact into a *real* number. Top-1 will fall, FAR will rise — **that is the point** | 1–2 days + collection |
| **2** | De-duplicate the raw corpus (encoder embeddings + pHash) | Removes hidden label noise and residual leakage | ½ day |
| **3** | Replace the 8 negative centroids with a **≥500-vector hard-negative bank**; renormalise everything | Direct FAR reduction at fixed recall; the bigger effect is on **coverage** | 2–3 days |
| **4** | **Relative score → isotonic/Platt calibrator → threshold by Clopper–Pearson** | Lets us state "FAR ≤ X % at 95 % confidence" and maximises coverage at that bound | 2–3 days |
| **5** | Re-extract the gallery with the **deployed artifact**; store the gallery in **float32** | Removes train/serve skew + a second quantization error, for ~300 KB | ½ day |
| **6** | Per-axis quantisation + dynamic-range INT8; measure all variants **on the phone** | Recovers most of the 0.9889 drift; likely makes INT8 competitive with or faster than FP32 | 1–2 days |
| **7** | LiteRT V2 Compiled Model API; XNNPACK confirmed; `num_threads`; fold adapter+L2-norm into the graph; **benchmark GPU vs CPU** | The latency win that creates the TTA budget | 2–3 days |
| **8** | 2-view **flip** MeTTA | +0.5–2 pts top-1 and lower score variance | +1 inference |
| **9** | Gallery 1 → 5–20 vectors/place (real + embedding expansion); **MAX → top-2 mean** in both paths | Robustness to viewpoint/season/lighting; removes M-dependence of the threshold | 1–2 days |
| **10** | Swap to **MobileCLIP2-S0** | Zero-architecture, zero-latency, better features — but measure **R@1**, not IN-1k | 1 day |
| **11** | Make a **plain calibrated linear head** a mandatory baseline | Either it wins (delete complexity) or the adapter is proven | 2–3 days |
| **12** | GPS as a **bounded heavy-tailed re-ranker**, never a gate | Robustness to spoofed/stale GPS; rejects far negatives | 2–3 days |

*Cheap extras:* add the FP32-vs-INT8 output-agreement cosine as a CI gate at 0.8 (arXiv:2610.18575); version the calibrator + gallery + thresholds together so they can never drift apart.

### 7.5 Sequence

```
W1        P0-1 (gate can fail) · P0-2 (withdraw the claim) · P2-5 step 1 (relative score)
W1–W2     P1-2 photo-level splits · P1-6 dedupe · P3-1 executable benchmark
W2–W3     P1-1 verified corpus (rights registry as source of truth) · P1-3 collect ≥10–20 photos/POI
W3        P1-4 hard-negative bank · P2-9 linear baseline · P2-10 MobileCLIP2-S0
W4        P2-1/P2-2 quantisation + re-extract · P2-8 LiteRT v2 runtime
W5        P2-4 gallery growth + top-2 mean · P2-5 calibrator fit · P2-7 flip-TTA
W6        P2-6 geo re-ranker · P3-4 on-device benchmark · P3-7 3-tier protocol
W7+       Field immersion (Bodh Gaya / Nalanda) — the only thing that can close Gate 2
```

**Nothing in W1–W2 requires a new photo, a new model, or a new dependency — and it is where the
entire measurement apparatus becomes trustworthy.**
