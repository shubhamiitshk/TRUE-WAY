# TrueWay cross-document conflict register

Lead-dev audit of all 28 markdown files (2026-10-11). Each entry names the
contradiction, the evidence, and the recommended resolution with an owner.
Severity: **[B] blocking** (affects gates/safety) · **[M] major**
(affects architecture decisions) · **[m] minor** (naming/links).

**Governance rule applied throughout:** the Master Blueprint's evidence
labels hold — `[V]` verified fact beats `[R]` review suggestion beats `[D]`
design decision beats `[A]` planning assumption. Unmeasured numbers must
never be stated as architecture.

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
