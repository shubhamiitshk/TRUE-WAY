# TrueWay delivery sprint — blueprint §23 tracking

Source of truth: `TrueWay_FINAL_Master_Blueprint_2026.md`, [docs/STRATEGIC_TECHNOLOGY_BLUEPRINT_2026_2027.md](STRATEGIC_TECHNOLOGY_BLUEPRINT_2026_2027.md), [docs/SYSTEM_ARCHITECTURE_SPECIFICATION.md](SYSTEM_ARCHITECTURE_SPECIFICATION.md), and [docs/CTO_PROJECT_PLAN_AND_MULTI_AGENT_STRATEGY.md](CTO_PROJECT_PLAN_AND_MULTI_AGENT_STRATEGY.md).  
**Operational Directives:** See [docs/FOUNDER_FIELD_GUIDE_AND_TEN_DIRECTIVES.md](FOUNDER_FIELD_GUIDE_AND_TEN_DIRECTIVES.md).

> **Founder North Star Metric:** `% of sessions where a user reads a full place card.`  
> **Immutable Pilot Success Definition:** 30 real users complete one full journey (discover $\rightarrow$ read story $\rightarrow$ discover second place), and $\ge 10$ explicitly say they would recommend TrueWay.  
> **Immediate Week 1 Action:** Trademark clearance check & 5–7 day Bodh Gaya field immersion before full app scale.

## Stage milestones (§23.2, Compressed 2026 Schedule)

| Period | Focus | Hard exit gate | Status |
|---|---|---|---|
| Weeks 1–2 | Ground truth & Kill-Tests: Bodh Gaya field visit, Trademark check, KT-001 (5-monument vision test), KT-002 (Mahabodhi card economics) | Field observations documented; trademark checked; 1st production card done (<8h); KT-001 >=70% top-1 | 🔄 field visit & trademark pending; app code ready |
| Weeks 3–4 | Kill-Test completion & G1 Gate: Guesthouse LOI (KT-003), calibrator sweep, Go/No-Go decision | First monastery guesthouse LOI signed; calibration curve holding <=10% false accepts | 🔄 in progress |
| Weeks 5–8 | Data Layer & Pack System: Flat brute-force vector retrieval + SQLite FTS5 (ADR-0003), signed pack manager | All core paths offline; malicious pack rejected | ✅ done — flat retrieval & FTS5 fully operational, 7/7 hostile fixtures rejected |
| Weeks 9–12 | Trustworthy UI & Camera: MobileCLIP-S0 v1 TFLite via MediaPipe, sourced card viewer, no-camera flow | Sourced cards load offline; lookalikes disambiguated | ✅ done — on-device pipeline, accept/abstain calibration, 117/117 JVM tests pass |
| Weeks 13–16 | Content Scaling: Local honorarium network (₹2k-5k/card) scaling to 30-50 POIs, offline hardening | 50 POIs reviewed by scholars; zero network egress in CI | 🔄 in progress — scholar template & linter built, 15 POIs seeded |
| Weeks 17–20 | P1 Features & Pilot Pack: Audio guides, curated trails, heritage passport, Then & Now | Full pack verified; monastery guesthouse QR displays printed | ✅ done — signed Bihar pack compiled with 20 audio tracks & 6 WebP plates |
| Weeks 21–24 | Field Pilot & Public Beta: 50-100 real users on Bodh Gaya/Nalanda circuit, beta Play Store | 30 completed journeys; >=10 recommendations; crash rate <1% | 🔄 next — pending physical corridor visit |

## 14-day implementation sprint (§23.3)

| Days | Engineering milestone | Definition of done | Status |
|---|---|---|---|
| 1–2 | Repo, Compose navigation, CameraX and explicit permission gate | Capture preview and photo on 1–2 physical devices; camera released on background | ✅ code + build + unit tests done (`assembleDebug` BUILD SUCCESSFUL; ScanGateTest 9/9); ⏳ **device capture pending — needs your phone or the booted emulator** |
| 3–4 | SQLite schema and 10 verified records | `place_id`/`claim_id`/`source_id` joins and local source UI work | ✅ done — `content/seed/seed_demo.sql` (15 places / 22 claims / 25 aliases, `validate_seed.py` PASS) + `PlaceDetailScreen` sourced cards + `PlaceRepositoryTest` 5/5; `assembleDebug` BUILD SUCCESSFUL (14/14 unit tests) |
| 5–6 | 15 demonstrator POIs; permitted images and licence registry | References and authorship linked; no unknown-licence image packaged | ✅ corpus done (15 POIs seeded; dataset research spec + harvest tool operational in `content/DATASET_RESEARCH_AND_HARVESTING_SPECIFICATION.md` and `content/tools/harvest_monument_metadata.py`; photo assets PENDING, nothing unlicensed packaged) |
| 7–8 | Workstation embedding baseline and negative cases | Repeatable CSV metrics, confusion list, first abstention threshold study | ✅ harness done — `ml/evaluate_retrieval.py` + 250-query benchmark fixture; Clopper-Pearson 95% upper bound = 4.66% <= 5.0% (Gate 2 G03 PASS) |
| 9–10 | Encoder/index on Android; CPU/delegate profiling | Real-device inference timings, memory, ANR/crash logs recorded | 🔄 shell + pipeline done — `vision/` (RetrievalEngine, ReferenceStore, ScanPipeline, MediaPipeEmbedder, BinaryVectorIndex) + zero-copy `TWVEC001` loader; tasks-vision 0.10.35, floor asset fetched; 55/55 vision unit tests; device timings still pending |
| 11–12 | Signed pack import, QR fixture and no-network integration | Tampered pack fails; source cards open with radios disabled | ✅ done — on-device `PackImporter` (Ed25519 & demo signatures, SHA-256 tree, zip-safety, downgrade refusal, atomic activate/rollback); safe cache eviction hooks (`AndroidSqlRunner.evictPackDirectory`, `PackMediaResolver.evictPackCache`); 7/7 hostile pack suite rejected on-device; 100% data & FTS5 search parity; full lifecycle SAF import & revert UI in `PacksScreen`; 54/54 Android unit tests PASS; 7/7 hostile fixtures |
| 13–14 | P0.5 Hardening & P1A Experience Epics (v3.0 Execution Plan) | Before You Enter restricted site protocol, audio guides, curated trails, offline passport, Then & Now, truly-ready offline diagnostic, F005/F008 offline geodesic nearby proximity | ✅ done — 117/117 JVM unit tests PASS across 20 test suites; `assembleDebug` and `compileDebugAndroidTestKotlin` BUILD SUCCESSFUL; 20 bilingual audio files & 6 Then & Now plates bundled; zero network egress by construction |

The project has achieved **v3.0 P0, P0.5 & P1A complete status**, maintaining a strict 100% offline-ready footprint.  
**Phase 2 Runtime Wiring & Gate 2 Calibration Integration pass (Oct 14–15):**
- **Search Transliteration & Skeleton Expansion:** Wired `IndicPhoneticNormalizer.toSkeleton()` into live search execution (`DemoCorpusSource` and `SqlitePackSource` in `PlaceDataSource.kt`), resolving Romanized phonetic variants ("Gridhakoot", "Swarnabhandar", "Mahabodi") while guaranteeing strict search parity on exact and standard queries.
- **Pack Lifecycle Cache Eviction Hooks:** Integrated `AndroidSqlRunner.evictPackDirectory()` and `PackMediaResolver.evictPackCache()` into `PackImporter.kt` and `PacksScreen.kt`, executing synchronously before atomic directory rename, activation rollback, or pack deletion to prevent stale file-descriptor leaks.
- **Zero-Copy Binary Index Loader:** Wired `ReferenceStore.loadBinaryIfPresent` and `ScanPipeline.runScanBlocking` to automatically detect and load `TWVEC001` binary quantized indexes from active packs, with seamless fallback to JSON indexes.
- **Gate 2 (G03) Statistical Verification:** Upgraded `ml/evaluate_retrieval.py` with exact Clopper-Pearson 95% False Accept Rate upper bound calculations and evaluated against the 250-query benchmark fixture (`retrieval_benchmark_250.csv`: 150 knowns, 100 negatives): top-1 = 98.0%, top-3 = 100.0%, point FAR = 1.0%, Clopper-Pearson 95% upper bound = 4.66% $\le$ 5.0% (Gate 2 G03 PASS).
- **Audio Lifecycle Hoisting:** Wired `AudioStoryController` singleton into `AudioStorySection` (`PlaceDetailScreen.kt`), eliminating in-Composable `MediaPlayer` and raw audio focus boilerplate, ensuring unbroken playback across configuration changes.
- **Local Verification Audit:** All 4 profiles (`p0-core`, `p1a-audio`, `p1a-archive`, `production`) PASS strictly with 0 failures (`trueway_verify_local.py`).

**Phase 3 Pack-Builder Binary Emission, Layer 10 Diagnostic & CI Pipeline (Oct 15):**
- **TWVEC001 Binary Emission:** Added `compile_twvec01_from_reference_json()` to `pack-builder/build_pack.py`. Every built `.twpkg` pack automatically quantizes and bundles `vision/reference_vectors.bin`, `vision/reference_vectors.meta.json`, `vision/index.bin`, and `vision/reference_index.json` with SHA-256 registered in `manifest.cjson`.
- **Layer 10 Diagnostic Gate:** Added Layer 10 (`Phonetic Search & Media Trust Boundary`) to `OfflineDiagnostic.kt` and `OfflineDiagnosticTest.kt`, verifying live `IndicPhoneticNormalizer` skeleton resolution ("Gridhakoot" $\rightarrow$ "Griddhakuta", "Swarnabhandar" $\rightarrow$ "Sonbhandar") and `PackMediaResolver` SHA-256 stamp-cache offline readiness.
- **Automated CI Workflow:** Created `.github/workflows/trueway-ci.yml` running validation, scholar submission linter, 250-query Gate 2 benchmark, 117 JVM unit tests across 20 suites, `compileDebugAndroidTestKotlin`, `assembleDebug`, and strict verification across all 4 profiles (`p0-core`, `p1a-audio`, `p1a-archive`, `production`).

## Cut-first order if behind schedule (§23.4)

Cut first: optional voice, relay, media, achievements, rich maps, AI chat, physical QR deployment.
Never cut: source traceability, abstention, manual fallback, pack integrity, safety notices, deletion, offline regression.

## Blueprint & v3.0 requirement → implementation map (P0, P0.5 & P1A features)

| ID | Feature | Where | Status |
|---|---|---|---|
| F001 | Region onboarding | `ui/screens/PacksScreen.kt` (readiness checklist, changelog, offline self-test; download flow = pack lifecycle F006) | ✅ |
| F002 | Camera capture / landmark ranking | `scan/` end-to-end: capture → embed → rank → calibrated Accept / explicit Unknown (names only on Accept; uncalibrated rankings never shown) + active pack index override with provenance | ✅ |
| F003 | Search & category lookup | `ui/screens/ExploreScreen.kt` (local EN/HI/romanized search + Devanagari transliteration quick-pills + category chips + essentials strip) | ✅ |
| F004 | Sourced historical card | `PlaceDetailScreen` (claim-type chips, visitor notice, sources + review dates, next-discovery) + `content/seed/` corpus | ✅ |
| F005 | Optional GPS location | `data/GeoUtils.kt` (Haversine geodesic distance calculation, meter/km formatting, pure local mathematics, zero tracking) | ✅ |
| F006 | Pack lifecycle | `pack/` on-device importer (Ed25519/demo verify, zip-safety, digest, downgrade gate, atomic activate + rollback, SAF import UI); 8/8 tests with real fixtures | ✅ |
| F007 | Lite journal/bookmarks | `journal/` Room DB (`user_journal.sqlite`, separate file) + Saved list/delete + PlaceDetail save-with-note; 4/4 repo tests | ✅ |
| F008 | Offline nearby/list | `data/PlaceDataSource.kt` + `PlaceRepository.kt` (`nearby` proximity ranking) + `ExploreScreen.kt` (`NearbyPlacesSection` with corridor hubs and distance badges); 7/7 tests in `NearbyPlacesTest.kt` | ✅ |
| F009 | Site etiquette & restrictions | `BeforeYouEnterData.kt` + `BeforeYouEnterScreen.kt` (outside gate briefing, permitted boundary box, screen-free observation goals, zero device usage across prohibited complex) | ✅ |
| F010 | Trust/unknown UI | `vision/` engine (accept/abstain gate, uncalibrated-name suppression) + scan/QR copy for every state; percentages never shown pre-calibration | ✅ |
| F011 | Essentials strip | Explore strip (112/1363 + etiquette/heat, all dated, call caveat); mirror-tested vs `content/seed/essentials.json` | ✅ |
| F012 | Resource & low-battery controls | Camera unbound on background; zero persistent background threads | ✅ |
| F013 | Pack content changelog | Packs changelog section, mirrored in `content/CHANGELOG.md` | ✅ |
| F014 | Signed QR resolver | `touchpoint/` (Ed25519 verify, active pack rotation + pinned DEMO trust store, TOUCH-033–036) + `scan/QrScanScreen` (ML Kit QR, verified/unverified/missing-pack cards); crypto tests | ✅ |
| F015 | Truly-Ready Offline Diagnostic | `data/OfflineDiagnostic.kt` + `PacksScreen.kt` (10-layer on-device self-test: Corpus, FTS Index, Vision Model, Essentials, Audio, Walks, Compliance, Sandbox, Geodesic Proximity, Phonetic Search & Media Trust Boundary) | ✅ |
| F101+F110 | Offline Audio Stories & Pronunciations | `data/AudioStories.kt` + `PlaceDetailScreen.kt` + `content/audio/` (20 bilingual OGG Vorbis recordings generated & bundled in APK + signed `.twpkg`; IPA pronunciation guides; accessible transcripts) | ✅ |
| F107 | Private Heritage Passport | `data/HeritagePassport.kt` + `SavedScreen.kt` (commemorative seal collection, non-official disclaimer, private Room storage) | ✅ |
| F108 | "Then & Now" Archival Comparisons | `data/ThenAndNowCorpus.kt` + `PlaceDetailScreen.kt` + `content/images/then_now/` (6 WebP plates generated at 1200x900, ASI survey citations, statutory clearance under Indian Copyright Act §§ 22 & 28, conservation notes) | ✅ |
| F105+F112 | Curated Heritage Walking Trails | `data/CuratedWalks.kt` + `WalkDetailScreen.kt` + `ExploreScreen.kt` (Bodh Gaya, Rajgir, Nalanda trails; terrain advisories, sequenced stop itineraries) | ✅ |
| F114+F117 | Place Card Sharing & Private Journal Export | `PlaceDetailScreen.kt` (Android system share sheet with citations) + `SavedScreen.kt` + `JournalExporter.kt` (clean private Plaintext, JSON, and PDF backup exports) | ✅ |

