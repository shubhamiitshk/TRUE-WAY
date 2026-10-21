# TrueWay cross-document conflict register

Lead-dev audit of all 28 markdown files (2026-10-11). Each entry names the
contradiction, the evidence, and the recommended resolution with an owner.
Severity: **[B] blocking** (affects gates/safety) · **[M] major**
(affects architecture decisions) · **[m] minor** (naming/links).

**Governance rule applied throughout:** the Master Blueprint's evidence
labels hold — `[V]` verified fact beats `[R]` review suggestion beats `[D]`
design decision beats `[A]` planning assumption. Unmeasured numbers must
never be stated as architecture.


## Resolved in the Oct 2026 vision audit

| ID | Conflict | Resolution |
|---|---|---|
| **V1** | The Gate 2 benchmark was scored on a **near-duplicate split** while `ml/README.md` §Protocol explicitly forbade it, and the harness **always exited 0** so CI could not block. | Splits are now grouped by **source subject series**; `ml/audit/check_split_integrity.py` is a hard CI gate; `ml/evaluate_retrieval.py` exits non-zero when the gate fails; CI additionally runs a **regression check** against `docs/audit/GATE2_BASELINE.json`. |
| **V2** | The reported "100 % Top-1 / 0 % FAR" was quoted as a release-gate PASS in `README.md`, `ml/README.md`, `docs/SPRINT_PLAN.md` and `docs/audit_v3_release_gates.md`. | **Withdrawn.** The benchmark was rebuilt on a human-verified, source-disjoint corpus. Current measured state: Top-1 **91.1 %**, Top-3 **96.8 %**, coverage **68.3 %**, accepted-set precision **100.0 %**, abstention **31.7 %**, point FAR **1.5 % (3/196)** of rows / **3.3 % (3 of 91)** of independent subject series (Clopper-Pearson 95 % bound **8.30 %** at an effective n of 91). Both accuracy gates clear and the point false-accept rate is below the target; **Gate 2 (G03) still FAILS** on the certificate (it needs zero false accepts at an effective n of at least 59) and on the number of independent known test series (41 against 150). |
| **V3** | The false-accept bound was computed over **rows**, so augmented derivatives of one photograph counted as independent trials (and the claim "0 % FAR" was really "the floor value 0.18"). | The bound is now computed at the **effective** sample size — distinct **subject series**. A photograph of the same monument from the same visit is a near-duplicate, not an independent trial. |
| **V4** | The device used three **hard-coded Kotlin constants** while the pack shipped a `calibration` block that was silently ignored; the runner-up score was **fabricated** as `score − 0.05`. | The gate reads the pack's learned calibration; the runner-up score is a measured value. `SiblingCalibrationPolicy` is derived from `VisionCalibration`, and an incomplete calibration makes the scanner report UNCALIBRATED rather than present a name. |
| **V5** | The decision rule lived only in Kotlin, so the workstation evaluation and the shipped scanner could drift without anyone noticing. | `ml/vision_index.py` is the single source of truth and the device mirrors it. A **cross-language parity test** replays 146 golden vectors through the real binary reader. It already caught a 36- vs 40-byte header mismatch and a float32-vs-float64 accumulation drift. |
| **V6** | The INT8 encoder was converted **without** `representative_dataset` (the domain calibration file was loaded and printed but never wired), the log claimed `domain_calib`, and INT8 measured **6× slower** than FP32 (1707 ms vs 284 ms). | `ml/convert_encoder.py` now wires the domain images in, produces five measured variants (fp32 / fp16 / int8 per-tensor / int8 per-axis / int8 dynamic), enforces the arXiv:2610.18575 agreement floor (cos ≥ 0.80) as a build failure, and ships the **fastest acceptable** variant. The conversion log reports what the converter *actually did*. **Done and measured:** fp16 (23.3 MB, cos 1.0000) is the variant that ships; fp32 is 647 ms; int8 dynamic-range is 2 756 ms; int8 per-axis (3 422 ms) and int8 per-tensor (3 445 ms) fail the agreement floor outright (cos 0.38 / 0.17). The two smallest artefacts are the two slowest ones. |
| **V7** | The pack's `model_crc` hashed the **model-id string** (a constant), so it could never detect a model/pack mismatch; `weights_sha256` hashed the adapter file and was never verified on device. | `TWVEC002` carries a digest of the **actual encoder artefact**; the pack manifest records it and the app refuses an unbound pack. |
| **V8** | The CI workflow built the APK **without staging the gitignored vision encoder**, so the APK under test had no encoder at all — and the audit still reported the APK as PASS. | CI stages the encoder and asserts that the built APK carries `vision_encoder.tflite`, `reference_vectors.bin` and `reference_vectors.meta.json`. |
| **V9** | The vision corpus ignored `content/seed/rights_registry.json`, which records Mahabodhi as `WITHHELD` (photography prohibited on site) while the model shipped a reference vector inviting users to photograph the spire. | The rights registry is the **source of truth** for the reference-photo policy and is surfaced in the dataset manifest and the pack. |
| **V10** | The exported TFLite graph folded the trained adapter matrix into `backbone.head.fc`, but the training pipeline L2-normalises the backbone output **before** the adapter. Folding a linear map across a normalisation is not a no-op, so the device applied the adapter to an unnormalised vector on **every inference** — a train/serve skew on 100 % of queries. | The export now computes `normalize(adapter(normalize(backbone(x))))` — the adapter is a separate `Linear` after the normalisation. **Still not enough.** Every check compared the artefact with *itself* (ONNX vs TFLite) or with a *reimplementation* of the adapter, so the exported graph could compute a completely different function and pass every gate. It did: the attention block's layer scale was folded into the **MLP's** weight instead of the attention projection, and the static attention forward dropped the `1/sqrt(head_dim)` logit scale. Measured on a **real photograph**, the cosine between the exported graph and the training pipeline was **0.04**. Now: the adapter is a separate `Linear` after the normalisation, each layer scale is folded into the op that produces its channels, the logit scale is applied explicitly, `ml/convert_encoder.py` **fails the build** if the exported graph does not reproduce the training computation on real photographs (cos >= 0.995; measured **0.999933**), `ml/audit/check_encoder_parity.py` compares against the **real** training adapter module, and the gallery, the calibration and the benchmark are extracted **with the deployed artefact** (`ml/build_index_from_artifact.py`). |
| **V11** | The corpus split was assigned by source-photo id (a hash), which LOOKS random but is not: a class harvested in one sitting ended up with 2 of its 24 visually confusable photographs in the calibration split and 10 in the test split, so the fitted threshold did not transfer and the measured false-accept rate was 3× higher on test than on calibration. | Splits are assigned by **subject series** (photographs of the same monument from the same visit), distributed proportionally so every split gets a representative mix. `source_subject_id` is carried on every record and the effective sample size is counted over subject series, not rows. |
| **V12** | A parent site and its child structure (the Nalanda site and Nalanda Monastery 1; the Mahabodhi complex and the Animesh Lochan chaitya) were separate vision classes with no rule to separate them, so the child or the parent won arbitrarily — exactly the failure blueprint §7.2 warns about. | A **related-pair margin** was added: a parent and its child (or two siblings) that look alike are reported as an **ambiguous pair** rather than one of them forced. Adding it cut the measured false-accept rate from 27.8 % to 13.9 %. |
| **V13** | The split quota was a quota of **subject series**, but the count it was derived from was the number of **photographs**. A class with 26 photographs in 2 series was therefore given quotas of 10 / 5 / 11 for 2 series, and every series landed in the test split: the class ended up with **no reference photographs at all** and the model's predictions collapsed onto a single place. The symptom was a class scoring perfectly in one run and catastrophically in the next, depending only on how many photographs that class happened to have. | The quota is derived from the number of **series** (`assign_photo_grouped_splits`). Every class now holds series in all three splits, and `ml/audit/check_split_integrity.py` fails when a class has an empty gallery. |
| **V14** | The split was ordered by "how place-like is this series", computed from the frozen backbone embeddings - and that cache is filled **incrementally** as the pipeline runs. The same corpus therefore produced a **different split** on the next run, and the measured false-accept rate moved between 2 and 10 failures with no change to the data at all. A benchmark whose split moves is not a benchmark. | The split is ordered by the series size alone, which depends only on the manifest. Verified: two consecutive re-splits produce **0 differences** in the split assignment. |
| **V15** | The approval script only ever **added** verdicts, so a photograph removed from a review table kept its old "approved" verdict and stayed in the corpus: a retracted corpus change survived several rebuilds. Separately, the re-splitter kept every record that was not explicitly *rejected*, so a **pending** (never reviewed) photograph was trained on. | `ml/audit/sync_review_to_tables.py` recomputes every candidate verdict from the review tables in **both directions** and CI fails if the two disagree; the re-splitter admits **only approved** photographs to the corpus. |

## [B1] "MobileCLIP2-S0" naming — RESOLVED
- **Status:** RESOLVED (Oct 14).
- **Resolution:** Reconciled `docs/STRATEGIC_TECHNOLOGY_BLUEPRINT_2026_2027.md` and `docs/SYSTEM_ARCHITECTURE_SPECIFICATION.md` to reflect the actual shipped v1 `MobileCLIP-S0` TFLite model (~4.1 MB, 512-dim embedding) executed via MediaPipe `ImageEmbedder` with CPU/GPU delegates (per ADR-0003), preventing inadvertent removal of `MediaPipeEmbedder`.

## [B2] Unmeasured performance numbers stated as architecture

- **Where:** Strategic §3.1 ("~12-18ms", "18ms total", "500 keypoints <15ms",
  "RANSAC <10ms", "Inliers >= 25", "Margin >= 0.08"), §3.4 ("~35 MB/s"),
  Gate 3 ("<4% battery"); ADR-0007 ("30+ MB/s"); System §X ("<15%/hr" —
  contradicts Strategic's <4%/hr); ADR-0004 (128-dim, RRF constants).
- **Evidence:** no benchmark on target phones exists (CONVERSION_LOG: only
  workstation ORT CPU 32/79 ms). Blueprint §2.3.11 + §18 explicitly class
  these as hypotheses, and §11.4 forbids promising relay rates.
- **Fix:** relabel every such number `[A]`/hypothesis with "to be measured
  Week 4–7" or delete. Latency target is formally defined per v3.0 Gate 3:
  capture-to-card P50 < 2.5s and P95 < 6s on reference hardware (replacing
  any model-only sub-500ms claims). Battery: single envelope "set after baselines"
  (blueprint §18.2). **Owner:** doc authors; enforced at PR review.

## [M1] Index strategy: ADR-0003 flat vs ADR-0004 sqlite-vec — both "Accepted"

- **Where:** ADR-0003 + `docs/research/ONDEVICE_VISION_2026.md` §4 (flat
  brute-force, 256-dim floor, HNSW only on measured pressure) vs ADR-0004 +
  Strategic §3.2 + System §IV (mandatory `vec0`, 128-dim MRL, RRF hybrid).
- **Evidence:** pilot arithmetic (§4: 70×30×512 INT8 ≈ 1 MB) needs no index;
  research shows 128-dim drops multimodal recall (256-dim keeps ~95%).
- **Fix (recommended):** flat brute-force + full/256-dim now; sqlite-vec
  becomes a *gated* upgrade ADR with trigger criteria (P95 pressure or
  >10k vectors). Downgrade ADR-0004 status to "Proposed / gated".
  **Owner:** founder + ML engineer at benchmark review.

## [M2] P2P transport: Nearby (ADR-0007/System) vs Wi-Fi Aware NAN (Strategic §3.4)

- **Evidence:** blueprint §11.4 specifies Nearby Connections (P1 gated) with
  measured-capability warnings; Strategic §3.4 draws a NAN flow at "~35 MB/s".
- **Fix:** Nearby Connections is the specified path; NAN is a research
  alternative — record as such, move NAN diagram behind a gate.
  **Owner:** founder.

## [M3] Threshold soup: KT-001/G1 (70%/10%) vs release gates (85/95/5%)

- **Where:** CTO §III G1 + KT-001 exit vs blueprint §18.2 vs Strategic Gate 1.
- **Fix:** keep both but label explicitly: 70/10 = **kill-test pre-gate**
  (camera stays only if met); 85/95/5 = **release gate**, false-accept binding.
  Unlabeled, teams will ship to the weaker number. **Owner:** founder.

## [M4] "Supersedes Master Blueprint §7 & §14" vs blueprint-as-source-of-truth

- **Where:** Strategic line 9 vs `docs/SPRINT_PLAN.md` line 3 ("Source of
  truth: Master Blueprint…").
- **Fix:** no document supersedes the blueprint until its gates are measured.
  Reword to "proposes revisions to … pending benchmark evidence", decided via
  ADR. **Owner:** doc author + founder.

## [M5] XFeat presented as decided P0/P1 component

- **Where:** Strategic §3.1/§4.1 (INT8, ~3.8MB, inlier thresholds), System
  §V/§IX, CTO R-01 ("two-stage XFeat cascade").
- **Evidence:** XFeat appears in zero benchmarks, conversions, or the
  research doc; blueprint variant C is a *candidate* P1 verifier.
- **Fix:** demote to "P1 geometric-verifier candidate (backends: XFeat /
  MediaPipe / classical, to be benchmarked)". **Owner:** ML engineer.

## [M6] "Mathematically impossible" GBNF claim

- **Where:** Strategic §2.2 ("mathematically impossible … without citing").
- **Evidence:** grammar constrains citation *format*, not truth — a model can
  emit a well-formed citation to a wrong claim.
- **Fix:** "grammar-constrained decoding *reduces* unsupported citations;
  factual support still requires the extractive validator (§14.1)."
  **Owner:** doc author.

## [m1] Journal filename — FIXED this pass

- CTO + ADR-0008 specify `user_journal.sqlite`; code used `trueway_journal.db`.
  Renamed in `JournalGraph` (no users yet, zero migration cost).

## [m2] External claims needing verification or "lead" labels

- Ministry of Culture "AI Heritage Search Engine (Feb 2026)", "ICP v2.0
  (Mar 2026)", "Inheritage SDK 5,000+ sites", "EGYPT-v1 99.13%",
  "EgMM-Corpus (Oct 2025)", "AI4Bharat 12,000 hrs / 208 districts",
  "Indic DiarBench (Aug 2026)", "228K WLM 2025 images", "ASI 3,679
  monuments", "sherpa-onnx ~200MB", "Gemma 4 E2B ~2GB".
- **Fix:** spot-check each before it enters any user-facing or partner text;
  until then they are research leads, not facts. **Owner:** content/research.

## [m3] Scope drift in lists

- KT-001/CTO content table add **Barabar Caves, Vaishali, Patna** beyond the
  blueprint's Bodh Gaya–Rajgir–Nalanda corridor; System §2.2 multi-module
  split, Coil 3.x, Hilt, DataStore, safe-args presented as current stack.
- **Fix:** corridor changes via explicit scope decision; target architecture
  labeled *target*, current single-module + manual DI labeled *current*.

## [m4] Machine-specific `file:///` links — RESOLVED
- **Status:** RESOLVED (Oct 14).
- **Resolution:** All machine-specific `file:///c:/Users/sumit/...` links in `docs/STRATEGIC_TECHNOLOGY_BLUEPRINT_2026_2027.md` and `docs/CTO_PROJECT_PLAN_AND_MULTI_AGENT_STRATEGY.md` replaced with relative repository links (`../tests/PROTOCOL.md`, `SPRINT_PLAN.md`).

## Resolved by this audit (no further action)

- Root README status (Day 1–2 → current P0 state). PROTOCOL.md TOUCH +
  hostile sections (TOUCH implemented; hostile 5/5 suite operational).
  Sprint plan stale rows (F001/F003/F009/F010 paths, Days 9–12 numbers).
  Pack downgrade policy (`--min-safe` implemented + fixture).
- v3.0 Execution Plan (P0.5 & P1A): Site etiquette/prohibitions (Mahabodhi device ban)
  resolved via "Before You Enter" outside-gate briefings (`BeforeYouEnterData.kt`,
  `BeforeYouEnterScreen.kt`). Privacy invariants preserved: passport seals and travel
  notes remain strictly in local `user_journal.sqlite` (zero remote egress). Audio stories,
  pronunciation guides, walking trails, Then & Now archival comparisons, and the 8-layer
  offline self-test fully integrated and verified (89/89 JVM tests PASS).
- **Security hardening (Oct 13):** 9 new resolver tests for manifest authentication + hash verification + staging/backup rejection + attacker scenario; publisher trust loading from assets (PacksScreen); SQLite connection cache (AndroidSqlRunner); search debounce (ExploreScreen); typo fix `ACCENT_SAFETY_HAZARD` → `ASCENT_SAFETY_HAZARD` (BeforeYouEnterData, BeforeYouEnterScreen, BeforeYouEnterTest); thread-safe manifest cache (ConcurrentHashMap); PDF export timestamp fix (JournalExporter); operator precedence fix (PlaceDetailScreen).
- **Active Pack Overrides, Asset Rendering & Diagnostic Hardening (Oct 14):**
  - `[m5]` FULLY RESOLVED: Replaced `AssetFileDescriptor` in `PackMediaResolver` with domain `ResolvedMedia` sealed interface (`VerifiedPackFile`, `BundledApkAsset`, `Rejected`) and a `(canonicalPath, length, lastModified, sha256)` stamp cache. Completely eliminated `sun.misc.Unsafe`, `ReflectionFactory`, and reflection mock hacks from `PackMediaResolverTest.kt`, ensuring clean, forward-compatible execution on standard JVMs.
  - `[m6]` RESOLVED: `ReferenceStore.load(context, assetName, packDir, packId)` queries active packs in `PrefsActivePackStore` for regional `reference_index.json` before falling back to bundled assets, populating scan provenance `packId`.
  - `[m7]` RESOLVED: `TouchpointVerifier.loadTrustStore(context, packDir)` queries active packs in `PrefsActivePackStore` for regional `touch_issuers.json`, dynamically rotating and augmenting trusted issuers ahead of bundled APK roots; wired into `QrScanScreen`.
  - `PlaceDetailScreen.kt`: `AudioStorySection` dynamically resolves active regional pack from `PrefsActivePackStore`; `ThenAndNowSection` renders archival and modern WebP plates using `ArchivalImageDisplay` and `PackMediaResolver`.
  - Layer 9 Geodesic Proximity Engine integrated into `OfflineDiagnostic` (F005 / F008 Haversine great-circle calculation and nearby places sorting); 115/115 JVM tests green across 20 suites.
- **Phase 2 Runtime Wiring & Gate 2 Calibration Integration (Oct 14–15):**
  - **Indic Phonetic Skeleton Search:** Connected `IndicPhoneticNormalizer.toSkeleton()` to live search paths (`DemoCorpusSource` and `SqlitePackSource` in `PlaceDataSource.kt`) resolving Romanized transliteration queries without breaking exact search parity; added `searchResolvesPhoneticSpellingVariants` in `PlaceRepositoryTest.kt`.
  - **Pack Lifecycle Cache Eviction Hooks:** Synchronous directory cache eviction wired before pack rename, rollback, and deletion via `AndroidSqlRunner.evictPackDirectory()` and `PackMediaResolver.evictPackCache()` in `PackImporter.kt` and `PacksScreen.kt`.
  - **Zero-Copy Binary Index Loader:** Wired `ReferenceStore.loadBinaryIfPresent` and `ScanPipeline.runScanBlocking` for direct memory-mapped `TWVEC001` format loading with JSON index fallback; added `loadsBinaryVectorsWhenPresentInPackDir` in `ReferenceStoreTest.kt`.
  - **Gate 2 (G03) Statistical Verification:** Upgraded `ml/evaluate_retrieval.py` with exact Clopper-Pearson 95% False Accept Rate upper bound calculations and evaluated 250-query benchmark fixture (`retrieval_benchmark_250.csv`): 147/150 top-1 (98.0%), 150/150 top-3 (100.0%), 1/100 false accept (1.0%), Clopper-Pearson 95% upper bound = 4.66% $\le$ 5.0% (Gate 2 G03 PASS).
  - **Audio Story Lifecycle Controller:** Hoisted `MediaPlayer` out of Composable UI scope via `AudioStoryController` singleton with speed adjustment and audio focus management in `PlaceDetailScreen.kt`.
  - **Test Suite Status:** 117/117 JVM tests pass across 20 test suites; `compileDebugAndroidTestKotlin` succeeds cleanly; all 4 audit profiles (`p0-core`, `p1a-audio`, `p1a-archive`, `production`) PASS with zero failures (`trueway_verify_local.py`).
- **Phase 3 Pack-Builder Binary Emission, Layer 10 Diagnostic & CI Pipeline (Oct 15):**
  - **Pack-Builder Binary Index Emission:** Integrated `compile_twvec01_from_reference_json()` into `pack-builder/build_pack.py`. Pack generation automatically quantizes 512-dim L2 float vectors to int8, packaging `vision/reference_vectors.bin`, `vision/reference_vectors.meta.json`, `vision/index.bin`, and `vision/reference_index.json` with SHA-256 registered in `manifest.cjson`. Hostile test suite continues to pass 7/7 on derived attack fixtures.
  - **Layer 10 Diagnostic Gate:** Added Layer 10 (`Phonetic Search & Media Trust Boundary`) to `OfflineDiagnostic.kt` and `OfflineDiagnosticTest.kt`. Verifies live Indic phonetic normalizer skeleton equivalences and `PackMediaResolver` SHA-256 stamp cache readiness offline.
  - **CI Workflow Automation:** Added `.github/workflows/trueway-ci.yml` running validation of SQL seed, scholar submission linter, 250-query Gate 2 benchmark, 117 JVM unit tests, `compileDebugAndroidTestKotlin`, `assembleDebug`, and strict verification of all 4 profiles on every push and pull request.

## Newly tracked (not blocking)

- [m8] Server stub has no persistence, auth, TLS, or rate limiting — by design for v3.0.
