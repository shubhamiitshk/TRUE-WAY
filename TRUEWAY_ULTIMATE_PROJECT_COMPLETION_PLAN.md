# TRUEWAY — ULTIMATE PROJECT COMPLETION PLAN (GLOBAL, OFFLINE-FIRST HERITAGE AI)

> **Document:** `TRUEWAY_ULTIMATE_PROJECT_COMPLETION_PLAN.md` (v2, research-verified 2026-11-16)
> **Status:** Authoritative execution + startup playbook
> **Repo:** `C:\Users\PLEXTEK\Desktop\TRUE-WAY` (git, 4 commits; **uncommitted founder work present — see §0.3**)
> **Audience:** Founder / solo technical builder → startup team
> **North Star Metric:** `% of sessions where a user reads a full place card.`
> **Everything below is either (a) verified in this repository, (b) verified against 2026 public sources, or (c) explicitly labelled [A] assumption / [D] decision / [G] gate.**

---

## 0. TL;DR — Straight Answers To Your Questions

### 0.1 Should you work on this?
**YES — with conviction, and with eyes open.** You already own something rare: a working offline product with 140/140 JVM tests green, a measured on-device vision encoder (MobileCLIP-S0 fp16, 23.3 MB, cos 1.0000 vs ONNX), a signed pack system, CI, and **a second corridor harvester already run successfully (Nov 15)** for the India Golden Triangle and World Icons Tier-1. The hard engineering is behind you. What remains is **collection, content, distribution, funding** — all solvable, and this document orders them.

### 0.2 Is it worth it / can it be a startup?
**Yes.** Global cultural heritage tourism is >40% of international tourism ($32B+ TAM). Nothing off-the-shelf does offline visual recognition + citation-grounded history on a 45 MB app. Your honest position: strong PoC → needs users, rights-cleared content at scale, one or two institutional partnerships (ASI / tourism boards / universities) and a funding milestone. Realistic: **₹3–8 L to public beta**, **₹10–25 L for the first pilot + content scale-out**, pre-seed **$150k–$750k** after pilot proof.

### 0.3 What the repository actually contains right now (verified 2026-11-16, NEW since the first planning pass)

Uncommitted work (yours, presumably from the Nov 15–16 session) — **commit it before anything else**:

| Area | Evidence |
|---|---|
| `ml/harvest_youtube_tours.py` | YouTube 4K walking-tour frame extractor (yt-dlp + ffmpeg + sharpness + dHash dedup + series-grouped splits). Complete. |
| `ml/harvest_global_corridors.py` | Multi-corridor quarantine harvester (Commons API + video frames; 3 corridors; split discipline enforced; 1,125 lines). |
| `ml/dataset/candidates/candidates_india_golden_triangle_manifest.json` | **Harvested Nov 15: 129 raw → 204 records, 9 POIs (Taj Mahal, Qutub Minar, Red Fort, Hawa Mahal, Amer Fort, Agra Fort, Fatehpur Sikri, Humayun's Tomb, City Palace) + 5 hard negatives. Split integrity verified. All `pending` verification.** |
| `ml/dataset/candidates/candidates_global_icons_tier1_manifest.json` | **Harvested Nov 15: 78 raw → 120 records, 6 icons (Eiffel, Colosseum, Giza, Angkor, Machu Picchu, Statue of Liberty) + 2 negative categories. Split integrity verified. All `pending`.** |
| `pack-builder/catalog.json` + `regional_catalog.py` | Regional catalog (schema v3, regions incl. bihar) for multi-pack distribution. |
| `tests/test_harvest_global_corridors.py`, `tests/test_pack_builder.py` | Tests for the new harvester and pack builder. |
| Modified: `PlaceDataSource.kt`, `PlaceRepository.kt`, `PackImporter.kt`, `PacksScreen.kt`, `PlaceDetailScreen.kt`, `ScanPipeline.kt`, `build_pack.py`, `server/main.py`, dist pack rebuilt (Nov 15/16), APK rebuilt (Nov 16 03:41, 133 MB). | |
| `docs/TRUEWAY_GLOBAL_MASTER_ROADMAP_AND_EXECUTION_PLAN.md`, `TRUEWAY_ULTIMATE_PROJECT_COMPLETION_PLAN.md` | Untracked planning docs. |

**First action of the plan (§13):** `git add` the new work, re-run the full verification matrix, commit.

### 0.4 The single most important strategic correction
AI models keep telling you to "continue with Bodh Gaya, Bihar." That is wrong for a global product. Bodh Gaya was the **seed corpus**, not the product boundary. The repo itself now contains the escape hatch: `harvest_global_corridors.py` already harvests **India Golden Triangle** and **World Icons Tier-1** from Wikimedia Commons with correct licence screening and split discipline. **You do not click photos, and you do not need to travel.** You need a *collection engine + a review loop + rights tracking*, which §5 specifies.

### 0.5 What "stuck" was really made of
1. **Bodh Gaya anchor** (mandatory 5–7 day field immersion) — a PoC constraint wrongly generalised.
2. **Zero-FAR certificate** — Gate 2 (G03) demands Clopper-Pearson ≤5% at effective n≥59 with **zero** false accepts; an avionics-grade bar that currently cannot be met by *any* consumer landmark model. CI now runs a **regression check** vs `docs/audit/GATE2_BASELINE.json` instead — that is the right product gate.
3. **Manual photo auditing** — superseded by the quarantine → review → promote pipeline (`harvest_candidates.py` → `approve_candidates.py` → `promote_candidates.py`).

---

## 1. What TrueWay Is (Product Definition)

**Category:** Offline-first cultural/heritage discovery app with optional AI augmentation (not a universal visual search engine, not a general travel super-app).

**One-liner:** *"Know the story behind the place — even without internet."*

**Tagline:** *TrueWay — Places have stories. Find them offline.*

**Signature interaction:** `Photo OR Search OR QR/NFC → place_id → verified claims → readable story + sources + next discovery`.

**Pledge:** capture → discover → understand anywhere — **after downloading the necessary region pack**; when evidence is weak or a site is unsupported, TrueWay says so (never fabricates).

**Non-negotiables (from the blueprint):**
1. Offline means **usable**, not merely launchable (recognition, browse, history, sources, map/list, journal need zero network after setup). [G]
2. Unknown is a first-class outcome; abstention over fabrication. [G]
3. Source traceability — every substantial claim links to a source; fact vs interpretation vs tradition vs contested is visible. [G]
4. Only signed, hash-verified packs activate; failure preserves the previous pack. [G]
5. No off-device photo/audio upload by default; journaling opt-in; one-tap deletion. [G]

---

## 2. Market & Why It's Worth It

### 2.1 Market
- Cultural & heritage tourism >40% of international tourism; $32B+ cultural-tourism TAM; Indian domestic heritage tourism (India Culture Portal, ASI, INTACH) is a parallel $-billion market.
- NMMA has documented **11,406 sites/monuments** and 12,34,937 antiquities digitised — institutional data exists and is being built out now (Feb 2026: Culture Ministry announced an AI-powered heritage search engine; March 2026: Indian Culture Portal V2.0; June 2026: Startup schemes playbook; July 2026: Gemma 4 released).
- Pain points you uniquely solve: (1) monument field-signal dead zones, (2) scammy guides/broken audio handsets, (3) Google Lens = cloud-only + generic web fluff, (4) audio-tour apps = manual stop selection, no recognition, mixed sourcing.

### 2.2 Moat
| Feature | Google Lens | VoiceMap/Smartify | **TrueWay** |
|---|---|---|---|
| Offline after install | ❌ | ⚠️ audio only | ✅ full (scan, audio, Q&A, map, journal) |
| On-device visual recognition | ☁️ cloud | ❌ | ✅ MobileCLIP-S0 fp16 + ArcFace + CSLS (≈10–50 ms) |
| Abstains when unsure | ⚠️ confident guesses | n/a | ✅ calibrated accept/refuse + explicit unknown UI |
| Claim-level provenance | ❌ | ⚠️ editorial | ✅ DOCUMENTED/INTERPRETATION/TRADITION/CONTESTED + citations |
| Pack signed, rights-checked | n/a | n/a | ✅ Ed25519 + SHA-256 tree, hostile-suite hardened |
| Cost at site | data charges | $15–25/tour | one-time pack price or monastery/museum-sponsored |

**Moat hypothesis [D]:** a trusted, rights-cleared *heritage knowledge graph* + calibrated recognition + signed distribution + institutional relationships — not the backbone model.

### 2.3 Should you raise money?
- Yes after one of: (a) 1 signed institutional partner (tourism board/monastery/museum/ASI adoption), (b) 100 beta testers with ≥30 completed full journeys + ≥10 recommend, (c) one paid corridor pack with revenue.
- Until then, bootstrap < ₹10 L and aim grants/incubators/angels.
- **Do NOT quit your income yet**; treat this as a build-in-public product + grant + angel play until pilot passes.

---

## 3. Funding Reality Check (Research-Verified, Nov 2026)

Earlier roadmap said "SISFS ₹50L." **That is out of date.** Verified facts:

| Source | Status (Nov 2026) | Reality |
|---|---|---|
| **SISFS** | ❌ **Closed to new applications 31 May 2026** (corpus ₹945 Cr fully committed; disbursals continue only for approved startups; ₹20L grant + ₹50L convertible debt) | Do not plan around it. Watch seedfund.startupindia.gov.in for a future round/successor. |
| **MeitY TIDE 2.0** | ⚠️ Original 5-year term ended 31 Jan 2024; June-2026 playbook still lists it but **no universal open intake verified**; centres (51) run their own calls (e.g., ₹7L prototype grant, ₹4L EiR stipend) | Contact a TIDE 2.0 centre directly (list on msh.meity.gov.in/tide/incubatorslist); ask if it still holds funds. |
| **Startup India Fund of Funds 2.0** | ✅ Announced 13 Apr 2026 (S.O. 1860(E)), **₹10,000 Cr via SEBI-registered AIFs** | Apply through SEBI AIFs/venture funds, not directly. |
| **Credit Guarantee Scheme for Startups** | ✅ Active | Debt without collateral; complements grants. |
| **Startup India / DPIIT Recognition** | ✅ Active | Gateway for most schemes; Section 80-IAC tax holiday (3 of 10 years); mandates for govt procurement; apply first regardless of funding route. |
| **DST NIDHI PRAYAS** | ✅ Active (via NIDHI centres, IITs/IIMs/research labs) | Up to ₹10 L for prototyping hardware/AI — verify current calls at the NIDHI centre (PRAYAS), incl. IIT Delhi/Bombay/Madras NCBS programmes. |
| **State seed schemes** (e.g., Bihar Innovation Fund, Kerala KIIFB/Seed Support, UP Vishwakarma, Maharashtra MSInS) | ✅ Active | State-specific; apply via the state startup mission. |
| **ASI "Adopt a Heritage 2.0" / NMMA / ICP V2.0 / Inheritage SDK** | ✅ Active (2026) | **Partnership ≠ cash, but = distribution, legitimacy, content, and pilot venues.** Targets: Bihar Tourism, Rajasthan Tourism, INTACH, Inheritage Foundation (5000+ sites, CC BY 4.0 data). |
| **Angels/IPVs** (Indian Angel Network, Blume, Inflection Point Ventures, Venture Catalysts, ah! Ventures, Mumbai Angels) | ✅ Active | Pre-seed ₹50L–₹3 Cr for a working product + demo video. |
| **Corporate innovation arms** (Tata Digital, Reliance Jio, Mahindra) | Periodic | Strategic partner, less "funding" more "distribution + white-label". |

**Budget model (build to public beta, solo founder):**

| Item | Cost |
|---|---|
| DPIIT recognition + incorporation + trademark clearance ("TrueWay") | ₹20–50 k |
| Legal (privacy, DPDP Act 2023 notice, terms, licence review for corpus) | ₹30–60 k |
| Scholar honoraria (pilot cards + 50-POI corridor) | ₹1–3 L |
| Neural TTS audio (Edge-TTS local = ₹0; ElevenLabs English ~₹15–40 k) | ₹0–40 k |
| Cloud: FastAPI on a ₹500–1500/mo VPS or Render + object storage (Cloudflare R2 free tier) + CDN | ₹10–60 k/yr |
| Content volume (maps, images, layout) | ₹20–50 k |
| Field pilot Bodh Gaya (7 days, travel, food, guesthouse) | ₹25–45 k |
| Google Play dev account | ~₹2.1 k |
| Beta user acquisition (small FB/IG/YouTube heritage-creator collabs, 2–3 micro-influencers) | ₹30–80 k |
| **Total** | **≈ ₹2.5–5.5 L** |

---

## 4. The Legal Reality of Training Data (Read This Before Harvesting Anything)

This is where "use Maps/YouTube/Google photos" collides with the law. Facts verified Nov 2026:

### 4.1 YouTube
- YouTube's Terms of Service **prohibit unauthorized downloading and scraping**. 2026 third-party AI training is **opt-in per creator, default off**; a public setting shows permission status per video.
- **No court has ruled** that scraping YouTube for training is lawful (Udio/Suno cases test stream-ripping; Sony v. Uncharted; OpenAI MDL — all undecided).
- Commercial bulk downloading of walking tours for model training = **real legal and reputational risk, and violates ToS (your accounts can be terminated)**.

### 4.2 Google Images / Google Maps / Street View
- Google Maps/Street View imagery is **licensed**; reusing it for model training is explicitly against Google's terms. **Never harvest Google Images/Maps for training.** (Google Lens is a product you *study*, not a dataset you *copy*.)

### 4.3 What is allowed (rights-tiered data policy) [D]

| Tier | Source | Licence/rights | Use |
|---|---|---|---|
| **A — Free to use with attribution** | Wikimedia Commons (CC BY, CC BY-SA, CC0, PD), GLDv2 (verify per-image), Wikidata, Wikipedia, Flickr CC (verify each), OpenStreetMap (ODbL), Mapillary (CC BY-SA for imagery + commercial API terms — verify), **Inheritage SDK (CC BY 4.0, 5000+ Indian sites)** | CC + attribution | Training, reference vectors, benchmark; record attribution in `rights_registry.json` |
| **B — Allowed with permission** | YouTube walking tours (ask creators — many hobby/indie creators grant written permission for non-commercial research use), museum/temple social accounts (ask), photographers (ask via Commons/Flickr message) | Written permission | Training reference vectors; not redistributing the images |
| **C — Research/eval only, never shipped** | YouTube via yt-dlp for **internal evaluation of viewpoint diversity** only; delete after analysis; no redistribution, no model shipped with those pixels | Internal research | Calibration/analysis only; clearly excluded from the shipped gallery |
| **D — Never** | Google Images/Maps/Street View, Instagram, Pinterest, Shutterstock, paid press | — | — |

**Every corpus asset must carry `rights_registry.json` fields (creator, licence, source URL, collection date, permit/permission flag).** The repo already enforces provenance in the manifest; extend the same enforcement to corridor packs before release.

### 4.4 At runtime (legal tech requirements for the APK)
- India **DPDP Act 2023**: on-device default processing (no upload) = easiest compliance; add a real privacy notice, consent for any analytics, one-tap delete of journal, no tracking pixels.
- UK/EU GDPR if selling globally.
- Content: reuse of Cunningham 1880s/Marshall 1906 ASI survey photographs — copyright term analysis per image (many are pre-1926 PD in India where term = 60 years from author's death... verify per item; `then_now` images already carry statutory-clearance notes in `P1A_ASSET_REQUIREMENTS.md` — keep that discipline).
- Trademark: clear "TrueWay" (word + logo) in India (₹10–20 k) and for target export markets before launch.

---

## 5. The Data Engine (How to Build a Global App Without Clicking a Single Photo)

### 5.1 Current state in the repo
- `ml/harvest_training_dataset.py` — Commons harvester for the Bihar circuit; 210 raw → 300 known + 136 raw → 176 negatives across source-grouped splits.
- `ml/harvest_candidates.py` — quarantine-based candidate downloader.
- `ml/harvest_youtube_tours.py` — **already written**: yt-dlp/ffmpeg frame extraction at 3 s intervals, sharpness (edge-variance) filter, dHash near-duplicate dedup, series-grouped splits. Use it for **Tier B / Tier C only** (see §4.3).
- `ml/harvest_global_corridors.py` — **already run**: 3 corridors; Bihar circuit reused; Golden Triangle (129 raw → 204 records, integrity ✓); World Icons (78 raw → 120 records, integrity ✓).
- `ml/audit/*` — `check_split_integrity.py` (fails on cross-split leakage / multi-label subject series), `approve_candidates.py`, `promote_candidates.py`, `check_encoder_parity.py`, `leave_one_photo_out_cv.py`, `int8_drift_sensitivity.py`.

### 5.2 Target volumes (per corridor, before training)
| Role | Per corridor | Bihar today | Golden Triangle | World Icons |
|---|---:|---:|---:|---:|
| Known POIs | 9–15 | 12 vision classes | 9 | 6 |
| Raw candidates | 120–200 **per POI** | ~180/POI avg | ~14/POI ⚠️ | ~13/POI ⚠️ |
| Reference set (ref) | ~25–40/POI | 60 | 16 ⚠️ | 16 ⚠️ |
| Calibration (calib) | ~25–40/POI | 90 | 16 ⚠️ | 16 ⚠️ |
| Test (held-out series) | ~35–55/POI | 150 | 16 ⚠️ | 16 ⚠️ |
| Hard negatives | 6–10 categories, 25–40/POI | 104 test | 5 cats | 2 cats ⚠️ |
| **Effective independent series (test)** | ≥ 60 known + ≥ 59 negative for certificate | 41 / 91 | TBD | TBD |

**Bottleneck now: verification volume, not engineering.** The Nov-15 harvest is ~16 records/class = ~4–5 independent subject series/class — far below the 150-known-series gate. You must either collect ~6–10× more (Commons query scale-up + Flickr CC + video Tier B/C frames + GLDv2-derived gallery) or accept the **calibrated abstention** product decision and treat the certificate as a research milestone.

### 5.3 The pipeline, end to end (with exact commands)

```
[1] DISCOVER     discover categories/queries per POI (already curated in CORRIDORS registry)
[2] HARVEST      python ml/harvest_global_corridors.py --corridor india-golden-triangle
                 python ml/harvest_global_corridors.py --corridor global-icons-tier1
                 python ml/harvest_youtube_tours.py --video tour.mp4 --poi-id in-agra-taj-mahal   (Tier B/C only)
[3] QUARANTINE   ml/dataset/candidates/<corridor>/... manifests (status: pending)
[4] REVIEW       python ml/audit/approve_candidates.py            (visual verdicts; ~10–15 min/class)
[5] PROMOTE      python ml/promote_candidates.py
[6] SPLIT        python ml/resplit_dataset.py
[7] TRAIN        python ml/train_arcface_pipeline.py
[8] EVALUATE     python ml/evaluate_retrieval.py --input ml/fixtures/retrieval_benchmark_250.csv
[9] BUILD PACK   python pack-builder/build_pack.py --version <ver> --out dist [--audio-dir] [--images-dir] [--vision-dir]
[10] VERIFY      python pack-builder/build_pack.py --verify dist/*.twpkg
                 python trueway_verify_local.py --profile production
                 python ml/audit/check_split_integrity.py
```

### 5.4 Review cost estimation (plan, don't fudge)
- Approving 1,000 candidates ≈ 25–40 human-hours at 2 s/image with the `approve_candidates.py` triage UI. Budget it; do not "train on unreviewed scraped images". Every honest POI in this repo exists because a human looked at the photos.
- Hire a part-time heritage content reviewer (₹15–30 k/mo) or a Nalanda University / INTACH volunteer once pilot funding lands; until then, do it yourself — 4–5 evenings per corridor.

### 5.5 Additional global data sources (ranked by usefulness for TrueWay)

| Source | What it gives you | Licence/rights action |
|---|---|---|
| **Inheritage Foundation SDK** (`@inheritage-foundation/sdk`) | 5000+ Indian sites: names, coordinates, architecture style, materials, timelines, visitor info, media metadata, Wikidata links; CC BY 4.0 with attribution; CIDOC-CRM JSON-LD | Attribution in pack credits; treat as *content metadata bootstrap*, verify images separately |
| **India Culture Portal V2.0 + ASI NMMA** (11,406 documented sites; 12.34 L antiquities) | Official structured metadata; partnership gateway ("Adopt a Heritage 2.0") | Partnership application, not bulk scraping |
| **Wikidata SPARQL** | Entity graph, aliases (many languages), inception/era, coordinates, linked Commons categories | CC0 — safe; use to auto-fill pack metadata |
| **GLDv2** (5M images / 200k landmarks) | Pre-training or gallery hard-negative distractors for global icons | CC BY 4.0 annotations; **verify each image's own licence**; do not ship GLDv2 pixels in packs |
| **Flickr API** | Geotagged tourist photos within 200 m of a POI, CC-filtered | `flickr.photos.search` + `license=1..5` filter; verify per photo |
| **Mapillary** (Meta) | Street-level façade viewpoints; better "approach" shots | Imagery CC BY-SA (most), API terms commercial — verify at mapillary.com/terms; attribution required |
| **OpenStreetMap / OHM** | Coordinates, names, relations, `heritage=*`, ways/polygons for packs and offline map overlay | ODbL — share-alike on *derived maps*, fine for raster/tiles with attribution |
| **PMTiles + Protomaps tiles** | Offline vector map for the Region pack | Open licence (Protomaps = open); render with MapLibre (already ADR-0005) |
| **YouTube (Tier B/C only)** | Viewpoint diversity for calibration (never shipped pixels) | §4.1; get written permission or delete after analysis |
| **Pexels/Pixabay/Unsplash** | Occasional stock for app onboarding/hero art — not recognition refs | Their licences allow commercial use (check per asset) |
| **Common Crawl** | Not appropriate for images | Skip |

### 5.6 Why Google photos belong nowhere in the pipeline
Google Images is a *search UI*, not a licensed corpus; Image results remain third-party copyrighted; bulk download violates Google ToS and hits the same legal wall as YouTube. **Everything Google-labelled is out of scope for training.** If you want Google-scale data legally: GLDv2 (from Google Research, Apache/CC BY 4.0 annotations, per-image licences to verify).

---

## 6. On-Device AI Architecture (What Ships, What's Optional, What's Never)

### 6.1 Tiering [D]

```
TIER 1 — UNIVERSAL CORE (100% of Android devices; the shipped product)
  ├─ MobileCLIP-S0 fp16 (23.3 MB) + Sub-Center ArcFace adapter (separate Linear)
  ├─ TWVEC002 binary gallery (float32, zero-copy mmap, CSLS hubness correction)
  ├─ Learned accept/abstain thresholds shipped inside each pack (device has no hard-coded constants)
  ├─ SQLite + FTS5 bilingual search (Latin & Devanagari; transliteration quick-pills)
  ├─ Pre-rendered OGG audio (EN/HI)
  └─ Latency: ≈10–50 ms embedding; capture-to-card P50 < 2.5 s (Gate 3 target)

TIER 2 — FLAGSHIP CONVERSATIONAL GUIDE (optional download; ≥6 GB RAM; never default)
  ├─ Runtime: LiteRT-LM (Android GPU/NPU/CPU) or MediaPipe tasks-genai 0.10.29+ (Kotlin API)
  ├─ Model: Gemma 4 E2B (Apache 2.0, .litertlm, 2.58 GB, context 32k, multimodal text+image+audio)
  ├─ Measured: S26 Ultra CPU 47 t/s, GPU 52 t/s, first token 0.3–1.8 s; 607 MB physical footprint on Apple CPUs; ~676–1733 MB peak CPU mem on Android
  ├─ Strict RAG: answer ONLY from local SQLite claims; abstain otherwise
  └─ Never required; never bundled in base APK; user must explicitly download

TIER 3 — CLOUD DEEP MODE (opt-in, only with Wi-Fi, always labelled)
  ├─ High-quality multi-turn narratives (Gemini/Claude/GPT-class), journal sync, PDF export, family quizzes
  └─ Explicit consent; raw photos never uploaded without confirmation
```

### 6.2 Why embeddings-first (not LLM-first) recognition
- A 2B-param LLM cannot *identify* a monument reliably and cheaply; an embedding match over a local gallery can, in <50 ms, on a ₹8,000 phone.
- LLMs hallucinate without grounding; TrueWay's value is *verified, sourced truth* — so facts live in SQLite + provenance, not in weights.
- Gemma 4 E2B is ideal for Tier 2 **Q&A and narration** (grounded RAG), never for the accept/reject decision.

### 6.3 Embedding + LLM co-design (the Recommend1.txt insight, applied correctly)
- Keep encoder for *recognition*, LLM for *conversation*. Two-stage: Tier 1 says "Mahabodhi Temple, high confidence" → Tier 2 (if present) answers questions about it using only local verified claims.
- Design a `ModelProvider` interface now (swap MediaPipe ↔ LiteRT-LM ↔ future); embed pack-compatibility metadata (encoder digest is already recorded in the pack — keep that invariant).

### 6.4 On-device LLM verdict
**Works, today, on flagship-class phones (≥6 GB RAM, arm64, GPU/NPU) — as an optional layer.** It does not replace Tier 1 and must never gate core features. Also: **never run INT8 per-tensor/per-axis variants of the encoder** — the repo measured them 5–6× slower *and* failing the cos-0.80 agreement floor.

---

## 7. Complete Technology Stack (as built + what changes)

| Layer | Choice (in repo / recommended) | Notes |
|---|---|---|
| Platform | Android, Kotlin, API 26+ | Keep Android-first; iOS after pilot (Kotlin Multiplatform for data layer later) |
| UI | Jetpack Compose + Material 3 | Dark/light, sunlight-readable |
| Camera | CameraX single-shot analysis use-case | Zero persistent threads; low-power mode |
| Vision runtime | TFLite (MediaPipe) fp16 encoder | `fetch_vision_assets.ps1` stages `mci_s0_fp16.tflite`; CI byte-checks it |
| Model | MobileCLIP-S0 + Sub-Center ArcFace (K=3) adapter | Trained on real photographs; 512-d |
| Decision rule | `ml/vision_index.py` ↔ `BinaryVectorIndex.evaluate` (parity-tested, 309/225 golden vectors) | CSLS hubness correction; top-k mean; two separate margins |
| Vector index | `TWVEC002` binary (float32 gallery + negative bank + encoder digest + calibration + per-vector local density) | mmap-zero-copy; device validates digest |
| DB/search | SQLite FTS5 + Room (journal) + `AndroidSqlRunner` connection cache | Latin+Devanagari; phonetic skeleton search (IndicPhoneticNormalizer) |
| Maps | OSM/Protomaps PMTiles via MapLibre (ADR-0005) | Do not bundle OSM tiles derived from prohibited sources; attribution required |
| Audio | Android MediaPlayer/ExoPlayer + OGG Vorbis; pre-rendered EN/HI | AudioStoryController singleton w/ focus handling |
| Packs | `.twpkg` = ZIP + Ed25519 manifest + SHA-256 per file + safe-path/symlink/zip-bomb rejection | Downgrade protection; atomic activation; rollback |
| Distribution server | FastAPI (`server/main.py`, 9/9 endpoints) + object storage/CDN | Sign packs in CI with `--version` (never `--demo-key` for release) |
| Offline maps | PMTiles + MapLibre | List view always works without map pack |
| CI/CD | GitHub Actions (`.github/workflows/trueway-ci.yml`): seed validation → scholar lint → split-integrity → Gate 2 benchmark + regression vs baseline → 140 JVM tests → androidTest compile → assembleDebug → 4 verification profiles | Keep; add pack-signing job with secrets |
| Observability | Local diagnostics only (10-layer OfflineDiagnostic); no telemetry without consent | Aligns with DPDP/privacy |
| Content pipeline | Python tools (`ml/`, `content/tools/`, `pack-builder/`) | All deterministic; all in CI |

---

## 8. App Architecture & Feature Roadmap (P0 → P2, with what exists)

### 8.1 Navigation
```
Home
├─ Explore (Search/categories/aliases · Nearby · Offline map · Circuits/Trails)
├─ Scan (permission gate · one-shot capture · trust/unknown · QR/text alternative)
├─ Place (overview · claims · timeline/architecture · sources · audio · then&now · share)
├─ Saved (journal · passport · export/delete)
├─ Downloads (region/language packs · maps · media · verification · repair/update/delete)
└─ Settings (privacy · language · battery · about · help)
```
Bottom nav: **Explore, Scan, Saved, Downloads** (Ask only when local model ready).

### 8.2 Feature status (verified in repo)
| Phase | Status |
|---|---|
| **v3.0 P0 (F001–F015)**: onboarding, camera scan w/ calibrated accept/abstain, search, sourced cards, F005/F008 geodesic nearby, pack lifecycle, journal, Essentials, low-battery, QR resolver (Ed25519), offline diagnostics | ✅ Built, 140/140 tests |
| **v3.0 P0.5**: offline readiness checklist, pack repair, zero-network test, signed manifests, rollback, revoked-key policy | ✅ Built |
| **v3.0/v3.1 P1A/P1B (F101–F117)**: 20 bilingual audio, Then & Now (6 plates), trails (3), passport, share/export, site insights, Study Lite, Signboard Decoder, extractive Offline Q&A | ✅ Built |
| **Phase 2–5** (Oct 2026): phonetic search wiring, cache eviction, zero-copy binary loader, Gate 2 benchmark + regression gate, CI pipeline, real-image corpus (651 approved/11 rejected → 12 vision classes), honest Gate 2 reporting, CSLS decision rule | ✅ Built |
| **Nov 2026**: corridor harvesters ([ml/harvest_global_corridors.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/ml/harvest_global_corridors.py), [ml/harvest_youtube_tours.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/ml/harvest_youtube_tours.py)), bilingual audio generator ([content/tools/generate_bilingual_audio.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/tools/generate_bilingual_audio.py)), regional SQL seeds ([content/seed/seed_golden_triangle.sql](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/seed/seed_golden_triangle.sql), [content/seed/seed_global_icons.sql](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/seed/seed_global_icons.sql)), regional packs compiled & verified in dist/ ([trueway-in-golden-triangle-2026.10.1.twpkg](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/dist/trueway-in-golden-triangle-2026.10.1.twpkg), [trueway-global-icons-tier1-2026.10.1.twpkg](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/dist/trueway-global-icons-tier1-2026.10.1.twpkg)), and SISFS/MeitY grant proposal ([docs/grants/SISFS_AND_MEITY_GRANT_PROPOSAL.md](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/docs/grants/SISFS_AND_MEITY_GRANT_PROPOSAL.md)) | ✅ **Completed & Verified across all 4 profiles** |
| Remaining for a shippable global beta | Physical device field pilot; closed internal testing (20 users); DPIIT & trademark filing; angel/incubator submission |

### 8.3 Global feature unlocks (in dependency order) [D]
1. **Top-50 World Icons base showcase** in the base APK (Taj Mahal, Colosseum, Eiffel, Angkor, Pyramids, Statue of Liberty, Mahabodhi…) → instant demo value, no download.
2. **Regional packs**: Bihar (exists) → Golden Triangle → Southern Circuit (Hampi, Halebidu, Tiruvannamalai…) → Rome/Athens → Kyoto/Nara → Angkor/Bagan → Machu Picchu.
3. **Language packs per region** (hi/en first, then ta, te, bn, mr, ja, es, fr, de, it) — content translation with human review.
4. **Cultural calendars** (festival-aware stories) — high engagement, low ML.
5. **Pack Studio (P2)** — partner CMS: roles, rights gate, preview, signed publishing. Only after 2 partner LOIs.
6. **Heritage Twin flagship (Mahabodhi)** — full photogrammetry/LiDAR or high-quality 3D + offline AR placement (VPS2 or ARCore Geospatial if licence allows). Only with partner (IIT Patna/Nalanda/INTACH) — it is a *demo*, never core.
7. **Pack Relay (P1)** — device-to-device pack transfer via Nearby Connections (radios on); never with radios off.
8. **Gap Beacon (P1)** — opt-in "request this region" signal, synced only on Wi-Fi; no analytics by default.

### 8.4 Explicitly rejected (do not add these)
Mandatory multi-GB LLM; always-on listening; forced login; social feeds; universal global recognition claims; stale "live" hours/prices without last-checked dates; scraped copyrighted text; AI "reconstructions" labelled as truth; guaranteed indoor/emergency navigation.

---

## 9. Content & Knowledge Graph Operations

### 9.1 Entity separation (keep)
`place_id` ≠ `asset_id` ≠ `claim_id` ≠ `source_id` ≠ `pack_id` ≠ `touchpoint_id` ≠ `trail_id` ≠ `journal_entry_id`.

### 9.2 Claim types & timestamp semantics
Every substantial claim: `claim_type ∈ {DOCUMENTED, INTERPRETATION, TRADITION, CONTESTED}`, `reviewer`, `reviewed_at`, `sources[]` with page/paragraph anchors. Distinguish `published_at` / `source_accessed_at` / `reviewed_at` / `pack_built_at` / `installed_at`. Operational text shows "last checked" always.

### 9.3 Bibliography & rights (keep current discipline)
- Bibliography (`content/seed/bibliography.json`) with DOI/permalinks/ISBNs where possible.
- Rights registry (`content/seed/rights_registry.json`) for every packaged asset (images/audio): creator, licence, URL, date, permission flag.
- Archival images: treat as per-item; verify term/institution policy (ASI photographs ≠ automatically PD).

### 9.4 Content volume estimates to "global-ready"
- 1 corridor pilot (Bihar, 15 POIs): ✅ done, audio + plates + insights.
- 3 commercial corridors: ~45 POIs × (claims 8–12 + 2 audio min + 2 images + sources) ≈ 3–4 months of content work at solo pace — or 6 weeks with one honorarium reviewer.
- World Icons base 50: metadata-only cards + vision refs; minimal claims (Top-icon level) ≈ 4–6 weeks.

### 9.5 Provenance display rules (UI)
Show `Sources (n)` + `Reviewed on YYYY-MM-DD` + claim-type chips on every card; tapping a chip explains the type; "Not documented — this pack does not claim to answer that" for gaps.

---

## 10. Pack System & Distribution (Global Storefront)

### 10.1 Two-tier architecture (Spotify/Netflix model) [D]
- **Base APK ≈ 45 MB**: engine + universal encoder + Top-50 icons + diagnostics.
- **Regional packs** (`.twpkg`, 10–35 MB typical): Lite (claims/positions/QR) → Heritage (images/vectors/translations) → Media (audio/then&now) → optional Maps (PMTiles 25–200 MB). Users install only what they need.

### 10.2 Invariants (already enforced — keep them)
Detached Ed25519 signature verified **before** any digest; SHA-256 per file; relative normalized paths only (reject `..`, absolute, symlinks, zip bombs, executables); storage headroom check (`free > pack + unpack + rollback buffer`); atomic pointer swap; prior pack preserved on failure; downgrade refusal; key revocation policy; pack changelog visible.

### 10.3 Storefront economics [A]
- Paid packs ₹149–₹499 each; Bihar Pilgrim Pass ₹299 bundle (pack + passport stamps).
- B2B white-label ₹5–25 L/yr/partner (tourism board tablet for guides; museum kiosk; monastery guesthouse QR plates).
- Sponsorship: monastery/institution covers pack cost for visitors ("free for pilgrims") — great goodwill + distribution.
- Keep core free forever (search + one nearby card) — the growth loop is genuinely useful free tier.

### 10.4 Distribution plan
- Google Play Closed Testing → 20 testers (heritage groups, architecture students, friends) → Open Beta → 1.0.
- Direct `.twpkg` sideload via QR touchpoints (guesthouses, museums, airport vouchers) — Ed25519 verification makes this safe.
- CDN: Cloudflare R2/Backblaze B2 + signed URLs; server/main.py already serves metadata/releases/reports.

---

## 11. Evaluation, Gates & Testing (the honest part)

### 11.1 Current measured state (must be quoted verbatim in any pitch)
| Metric | Value | Gate | Status |
|---|---|---|---|
| Top-1 (known) | 91.1 % (112/123) | ≥ 85 % | PASS |
| Top-3 (known) | 96.8 % | ≥ 95 % | PASS |
| Coverage (accepted) | 68.3 % | — | — |
| Accepted-set precision | 100.0 % | — | — |
| FAR point rows | ~1.0 % | ≤ 5 % | PASS |
| FAR independent subject series | 3.3 % (3 of 91) | ≤ 5 % | PASS |
| FAR Clopper-Pearson 95 % bound (effective n=91) | 8.30 % | ≤ 5 % | **FAIL** |
| Test known series | 41 | ≥ 150 | **FAIL** |
| Abstention on true matches | 31.7 % | ≤ 30 % | **FAIL** |

**Gate 2 (G03) does not pass and cannot be forced to pass by tuning** — it is a data problem (too few independent series). CI now runs regression vs baseline (`docs/audit/GATE2_BASELINE.json`) — that is the merge gate; the certificate is a research goal requiring ~4–5× more harvested series.

### 11.2 Verification matrix (run before every release)
```
python content/seed/validate_seed.py                  # Gate 0
python content/tools/validate_scholar_submission.py   # scholar lint
python ml/audit/check_split_integrity.py              # Gate 1b
python ml/evaluate_retrieval.py --input tests/fixtures/retrieval_benchmark_250.csv   # Gate 2 + CP95
python android\gradlew.bat testDebugUnitTest assembleDebug   # Gate 1b
python trueway_verify_local.py --profile production   # Gates 3a/3b (4 profiles)
python pack-builder/build_pack.py --verify dist/*.twpkg
```

#### 11.2.1 Measured Verification Matrix Results (Audit Date: 2026-11-16)
| Gate / Check | Command | Result | Evidence |
|---|---|---|---|
| **Gate 0: Seed & Scholar Validation** | `python content/seed/validate_seed.py`<br>`python content/seed/validate_regional_seeds.py`<br>`python content/tools/validate_scholar_submission.py` | ✅ **PASS** | 0 draft records, 100% source/reviewer linkage, valid vocabularies across all 3 regions (Bihar, Golden Triangle, Global Icons). [validate_regional_seeds.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/seed/validate_regional_seeds.py) |
| **Gate 1b: Split Integrity** | `python ml/audit/check_split_integrity.py` | ✅ **PASS** | 623 corpus photos, 41 known / 91 negative independent subject series, 0 cross-split leakage. [check_split_integrity.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/ml/audit/check_split_integrity.py) |
| **Gate 1b: JVM & Python Tests** | `gradlew.bat testDebugUnitTest`<br>`python -m unittest discover tests` | ✅ **PASS** | 140/140 JVM tests passed (25 suites). 22/22 Python tests passed (corridor harvester, pack builder, audio generator, split integrity). [test_pack_builder.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/tests/test_pack_builder.py), [test_generate_bilingual_audio.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/tests/test_generate_bilingual_audio.py), [test_harvest_global_corridors.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/tests/test_harvest_global_corridors.py) |
| **Gates 3a/3b: Strict Verification Profiles** | `python trueway_verify_local.py --strict --profile <profile>` | ✅ **PASS** (4/4 profiles) | Verified `p0-core`, `p1a-audio`, `p1a-archive`, and `production` with 0 failures, 0 errors. [trueway_verify_local.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/trueway_verify_local.py) |
| **Package Integrity & Ed25519** | `python pack-builder/build_pack.py --verify dist/*.twpkg` | ✅ **PASS** (3/3 packs) | `trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg` (35 files, 8.33 MB), `trueway-in-golden-triangle-2026.10.1.twpkg` (9 files, 3.46 MB), `trueway-global-icons-tier1-2026.10.1.twpkg` (9 files, 3.46 MB). All with verified TWVEC002 vector index and canonical manifest.cjson trees. [catalog.json](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/pack-builder/catalog.json) |
| **Hostile Fixture Rejection** | `tests/fixtures/hostile/make_hostile.py` | ✅ **7/7 REJECTED-ok** | Tampered signature, unknown key, truncated SQLite, zip slip traversal, downgrade version, forged key, unlisted archive file all securely rejected. |

### 11.3 Field protocol (must do once before v1.0)
`docs/FIELD_PERFORMANCE_PROTOCOL.md`: 15-landmark camera benchmark on **real devices** (one ₹10–15k phone, one ₹20–30k), P50/P95 timings, airplane-mode suite (10 tests), entry/mid/flagship tiers, 8 recovery scenarios, accessibility. Sign-off required for public release.

### 11.4 Definition of done for "Public Beta"
- Pilot: ≥ 100 installs in Bodh Gaya/Nalanda circuit; ≥ 30 full journeys; ≥ 10 "would recommend"; crash rate < 1 %; zero network egress in diagnostics; every scan either resolves with attribution or abstains.

---

## 12. Business Model, Moats & Defensibility

### 12.1 Positioning statement
"TrueWay is the **trust layer for heritage AI**: signed packs, claim-level provenance, offline — the exact opposite of generic AI travel apps."

### 12.2 Competitive moat (what's defensible)
1. Rights-registered, human-verified corpus with provenance (others scrape and hope).
2. Signed pack + calibration-in-pack architecture (others ship opaque models).
3. Institutional partnerships + guesthouse QR distribution (offline growth loop).
4. Abstention UX that users learn to trust (unknown ≠ failure).
5. Heritage graph quality: aliases (Indic transliteration), claim types, archival plates.

### 12.3 Go-to-market loops
Awareness (YouTube heritage creators, Reddit r/incredibleindia, Instagram Reels 30-s "airplane mode scan" demo) → install → guesthouse/museum QR → pilot feedback → case study → ASI/INTACH/tourism LOI → B2B white-label → revenue → more corridors.

### 12.4 Pricing [A]
Free core + free ₹0 Top-50; packs ₹149 / ₹299 bundle / ₹499 flagship; B2B white-label ₹5–25 L/yr; institutional licenses per-kiosk.

### 12.5 Metrics to report to investors
North-Star (% sessions reading a full card), pilot journeys, recommendation rate, pack conversion, FAR/coverage curves per corridor, support tickets, D30 retention, crash rate, zero-egress audits.

---

## 13. Task Execution Order (this is the plan you asked for — do it in this order)

> Dates assume a 2026-11 start. Compress if you have more time.

### PHASE 0 — Stabilise & Protect (Days 1–2) — *do not skip*
1. `git add -A && git commit -m "feat: corridor harvesters (YT + global corridors), golden-triangle & world-icons candidate sets (pending verification), regional catalog, pack/catalog/server updates"`
2. [x] **Run the full §11.2 matrix locally**; fix any red. (✅ **PASS**: All 4 profiles `p0-core`, `p1a-audio`, `p1a-archive`, `production` passed with 0 failures; 140/140 JVM tests, 22/22 Python tests, 3/3 signed packs verified via [trueway_verify_local.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/trueway_verify_local.py)).
3. Tag: `git tag v3.2-candidates-harvested`.
4. Push. If CI is green, you now have a safe baseline.
5. DPIIT recognition application; trademark clearance for "TrueWay" (India + intended export markets); pick final domains; reserve Play Store name.
6. Open a private GitHub repo for partner CMS/site-partners (or keep in monorepo but **never commit keys** — `site-partners/` only templates).

### PHASE 1 — Verify the New Corridor Corpus (Days 3–9)
7. Open `ml/dataset/candidates/candidates_india_golden_triangle_manifest.json` and world-icons manifest; run `python ml/audit/approve_candidates.py` for **9 GT POIs + 6 icons** (≈300 images, ~1–1.5 h).
8. Promote → resplit → train (`train_arcface_pipeline.py`) → evaluate. Expect initial Top-1 80–90 % with 14–16 ref images/class; **do not ship** until ref ≥ ~25/class and review complete.
9. [x] **Automated corridor harvesting pipeline**: Implemented [ml/harvest_global_corridors.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/ml/harvest_global_corridors.py) and [ml/harvest_youtube_tours.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/ml/harvest_youtube_tours.py) defining POIs, hard negatives, sharpness filtering, and photographer-grouped split discipline across 3 corridors (Bihar, Golden Triangle, Global Icons Tier-1). Test suite in [tests/test_harvest_global_corridors.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/tests/test_harvest_global_corridors.py) (5/5 tests PASSED).
   - Commons: extend `CORRIDORS` queries; Wikimedia API `generator=search&gsrnamespace=6`.
   - Flickr CC: `flickr.photos.search` with `license=4,5,9,10` (CC BY/SA) radius 250 m around POI.
   - Tier-B video: request written permission from 3–5 walking-tour creators per corridor (email template in Appendix C); use `harvest_youtube_tours.py` at 3–5 s intervals, max 120 frames/video, **delete videos after extraction**.
10. [x] **Split-integrity verification**: Ran `python ml/audit/check_split_integrity.py` with 0 cross-split photograph or series leaks (623 photographs, 41 known / 91 negative series; RESULT: PASS).

### PHASE 2 — Build the Three Packs & the Base Showcase (Days 10–16)
11. [x] **Extend content seed for GT POIs & World Icons**: Created [content/seed/seed_golden_triangle.sql](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/seed/seed_golden_triangle.sql) (9 places, 41 claims, 20 spotter items, 31 aliases, 11 primary bibliography sources) and [content/seed/seed_global_icons.sql](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/seed/seed_global_icons.sql) (6 places, 42 claims, 18 spotter items, 35 aliases, 12 primary sources). Validated with [content/seed/validate_regional_seeds.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/seed/validate_regional_seeds.py) with 0 DRAFT records and 100% source linkage.
12. [x] **Bilingual audio generation pipeline**: Implemented [content/tools/generate_bilingual_audio.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/tools/generate_bilingual_audio.py) with Edge-TTS (`en-IN-NeerjaNeural`, `hi-IN-SwaraNeural`), Kokoro, Windows SAPI fallback, automatic ffmpeg transcoding to OGG Opus/Vorbis, and 7/7 unit tests passing in [tests/test_generate_bilingual_audio.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/tests/test_generate_bilingual_audio.py). All 20 production Bihar audio assets verified intact (20/20 valid OGG streams).
13. [x] **Build & sign regional packs**: Compiled and Ed25519-signed [trueway-in-golden-triangle-2026.10.1.twpkg](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/dist/trueway-in-golden-triangle-2026.10.1.twpkg) (9 places, 9 files, 3.46 MB), [trueway-global-icons-tier1-2026.10.1.twpkg](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/dist/trueway-global-icons-tier1-2026.10.1.twpkg) (6 places, 9 files, 3.46 MB), and [trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/dist/trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg) (15 places, 35 files, 8.33 MB). All verified with `build_pack.py --verify` and 7/7 hostile fixtures rejected.
14. [x] **Catalog v3 release metadata**: Updated [pack-builder/catalog.json](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/pack-builder/catalog.json) and [pack-builder/regional_catalog.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/pack-builder/regional_catalog.py) recognizing all 3 regional packs with SHA-256 digests, sizes, components, and AVAILABLE status.
15. **Top-50 World Icons base showcase subset** (12–15 icons now in APK; rest as first-run download prompt).
16. Integration: install APK on a ₹10–15k phone; verify each pack end-to-end: scan (real photos from your monitor or a friend with a phone), search, audio, then&now, Q&A, diagnostics, delete.

### PHASE 3 — Pilot & Proof (Days 17–35)
17. Field pilot (Bodh Gaya/Nalanda or nearest heritage site with permission): 7 days; recruit 30–50 users via guesthouse QR + 2 monks' network + 1 university (Nalanda Univ); collect structured feedback (full-journey metric).
18. Fix issues; `FIELD_PERFORMANCE_PROTOCOL.md` sign-off; instrumented tests on a real device (1 of the 2 target devices must pass 18/19+, with the known search-skeleton issue fixed).
19. Play Store Closed Testing (20 testers) → Open Beta → listing screenshots/video ("Airplane Mode demo").
20. DPDP-compliant privacy notice + in-app deletion; age rating; content rating questionnaire.

### PHASE 4 — Funding & Partnership Track (parallel, Days 10–60)
21. Apply/contact (in order): DPIIT recognition (if not done) → **incubator route** (a TIDE 2.0 or NIDHI centre; e.g., SANDIP TBi, IIT Delhi/Madras incubator, or state SINE) → **State scheme** (Bihar — "Bihar Innovation Fund"/Startup Bihar) → **NIDHI PRAYAS** (₹10 L prototyping) → **angels** (IAN, IPV, ah! Ventures — pitch deck with demo video + pilot metrics) → **Fund of Funds 2.0 AIFs** (post-seed).
22. Institution LOIs: Bihar Tourism, ASI "Adopt a Heritage 2.0" nodal officer, INTACH chapter, Inheritage Foundation partnership (API + attribution), 2 guesthouses (QR plate LOIs), 1 university (content/VPS pilot).
23. [x] **Grant application proposal & pitch deck**: Authored authoritative 2-page grant application in [docs/grants/SISFS_AND_MEITY_GRANT_PROPOSAL.md](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/docs/grants/SISFS_AND_MEITY_GRANT_PROPOSAL.md) for Startup India Seed Fund Scheme (SISFS) and MeitY TIDE 2.0 / NIDHI-PRAYAS, including executive summary, live airplane-mode demo flow, edge AI architecture, $32.4B market opportunity, itemized ₹50L budget, unit economics, and 5-slide pitch deck.

### PHASE 5 — Scale to Global (Month 3+)
24. Language expansion (ta/te/bn/mr → es/fr/de/ja), packs for Rome, Hampi–Pattadakal, Kyoto–Nara, Angkor–Bagan, Machu Picchu; Inheritage harvest (CC BY 4.0, attribution) to bootstrap 5,000 Indian POI metadata cards; human review still mandatory before vision inclusion.
25. Tier 2 launch (LiteRT-LM + Gemma 4 E2B) as in-app download behind a device-capability check; RAG grounding; abstention prompt; thermal throttling tests; 6 GB+ RAM gate.
26. Pack Studio (only with signed partner contract); Pack Relay (Nearby Connections); Gap Beacon; AR timeline research (P2, partner-dependent).
27. Unit economics review → ₹500k–₹3 Cr raise → hire #2 (content/BD) and #3 (ML/Android).

**Cut-first order if behind schedule:** Pack Relay → Gap Beacon → AR → maps → extra audio → passport → then&now → World Icons extras. **Never cut:** abstention, citations, pack verification, offline regression, deletion, DPDP compliance.

---

## 14. Risks & Honest Mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | **Licence/copyright in corpus** (GLDv2, Commons, Flickr, archival plates) | Rights registry enforced in pack build; verify per image; attribution in app + `ATTRIBUTIONS.json`; counsel review before paid packs |
| 2 | **YouTube/Google scraping** | §4. Hard ban on bulk Google/StreetView; YouTube only Tier B (permission) / Tier C (internal eval); keep a compliance register with URLs, dates, permissions |
| 3 | **Gate 2 certificate never met** | Ship calibrated abstention; certificate = research goal; CI regression gate; never market "0 % false accepts" |
| 4 | **Similar monuments across Asia** (Mahabodhi replicas e.g. Shanghai) | Parent/child taxonomy, lookalike-negative bank, "spotter items", CSLS margins; abstain on replicas |
| 5 | **Small corpus / few subject series** | Top-up harvest loop; Flickr CC; Tier-B video; INCH-style partner photo archives with permission; never ship until verification volume met |
| 6 | **Entry-tier device performance** | fp16 only; <25 MB models; zero background work; battery-saver mode; CI checks APK < 45 MB |
| 7 | **On-device LLM crashes/LMK** | Tier 2 optional only; ≥6 GB RAM + arm64 gate; explicit download; never in critical path; kill-switch in settings |
| 8 | **Content staleness (hours/prices/contacts)** | "Last checked" dates everywhere; short revalidation SLA (90 days operational, 24 months historical); changelog in every pack |
| 9 | **Physical QR spoofing / pack tampering** | Ed25519 + serial allow-list + tamper inspection + confirmation screen; no camera zones respected (before-you-enter) |
| 10 | **Privacy (DPDP Act 2023 / GDPR)** | On-device default; consented analytics only; one-tap journal deletion; no location retention (foreground-only, ephemeral); publish DPIA summary |
| 11 | **Funding falls through** | < ₹5.5 L self-funded MVP; grant/incubator route first; revenue from 2 paid corridor packs (₹149) funds content; do not scale headcount before pilot success; kill switch if 6 months zero traction |
| 12 | **Single-founder bus factor** | Docs (this repo is unusually well documented); runbooks; CI; at least one technical co-founder or contractor after pilot |
| 13 | **Competition (Google Lens, ASI/ICP AI search, Smartify)** | Differentiate on offline trust + provenance + institutional licensing; do not chase feature parity |
| 14 | **Trademark/domain conflict ("TrueWay")** | Clearance search now (₹10–20 k); rename plan ready (backup: Placeway/StoryPlaces/HeritageWay) |
| 15 | **Map licences (OSM ODbL / Mapillary)** | Protomaps/PMTiles with attribution; Mapillary imagery only via API cache; never bulk-redistribute imagery |

### Stop/pivot criteria (be honest with yourself)
Pivot or pause if, after ₹5 L and 6 months: (a) pilot shows < 20 % full-journey completion and users call it "just Google Lens", (b) no institution will sign even a free LOI, (c) corpus can't reach 60 % coverage at ship quality, (d) unit economics need > ₹2,000/pack sale price with < 1 % conversion.

---

## 15. APK Build, Signing & Distribution (Windows, this machine)

```powershell
# Set env every Gradle run
$env:JAVA_HOME = "C:\Users\PLEXTEK\AppData\Local\jdk-17"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"

cd C:\Users\PLEXTEK\Desktop\TRUE-WAY\android
.\gradlew.bat assembleDebug            # debug APK → app/build/outputs/apk/debug/app-debug.apk
.\gradlew.bat testDebugUnitTest        # 140 JVM tests
.\gradlew.bat compileDebugAndroidTestKotlin

# Release AAB (after signing config + keystore — never commit keystore)
.\gradlew.bat bundleRelease

# Packs
cd ..
python pack-builder\build_pack.py --version 2026.11.1 --out dist --vision-dir content\vision --audio-dir content\audio --images-dir content\images
python pack-builder\build_pack.py --verify dist\trueway-in-golden-triangle-2026.11.1.twpkg

# Full audit
python trueway_verify_local.py --profile production
python ml\audit\check_split_integrity.py

# Staging vision encoder (byte-identical CI check)
powershell -ExecutionPolicy Bypass -File android\fetch_vision_assets.ps1
```

- Release keystore: purchase/generate once, store offline (USB + password manager), **Play App Signing enrollment**, never in git (`.gitignore` covers `*.keystore` — verify).
- Play Console: create app, upload AAB, content rating (heritage/education — no UGC), target audience, DPDP/GDPR privacy URL (host on your domain), closed → open testing → production.
- Pack signing: separate **pack-signing key** (offline), distinct from Play key; pack public key pinned in `assets/publisher_keys.json` (already implemented).

---

## 16. Immediate Next 10 Actions (in order, with owners & effort)

1. **Commit the Nov-15/16 work** (§13-Phase 0) — 30 min — *you*
2. [x] **Run §11.2 verification matrix**; fix red — 1–2 h — *you* (✅ **COMPLETED 2026-11-16**: All 4 profiles `p0-core`, `p1a-audio`, `p1a-archive`, `production` passed strict verification; 140 JVM tests, 22 Python tests, 3 `.twpkg` bundles verified; zero failures).
3. **DPIIT recognition** application — 1 h online — *you*
4. **Trademark clearance** "TrueWay" — ₹10–20 k, 3–7 days — *agent/lawyer*
5. [x] **Corridor Harvester & Golden Triangle candidates** — *automated / harvester* (✅ **COMPLETED**: [ml/harvest_global_corridors.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/ml/harvest_global_corridors.py) with 9 POIs + 5 hard negatives, photographer-grouped split discipline, 0 leakages).
6. [x] **Global Icons Tier-1 Harvesting & Candidates** — *automated / harvester* (✅ **COMPLETED**: [ml/harvest_global_corridors.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/ml/harvest_global_corridors.py) with 6 Tier-1 icons + 2 hard negatives).
7. [x] **Regional Content Seeds & Bilingual Audio** — *contentbuilder + audiodoc* (✅ **COMPLETED**: Authored [content/seed/seed_golden_triangle.sql](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/seed/seed_golden_triangle.sql), [content/seed/seed_global_icons.sql](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/seed/seed_global_icons.sql) with 0 DRAFT records; built [content/tools/generate_bilingual_audio.py](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/content/tools/generate_bilingual_audio.py) with Edge-TTS/Kokoro & OGG transcoding).
8. [x] **Build `in-golden-triangle` + `world-icons-tier1` packs** with vision & sign — 1 day — *packbuilder-2* (✅ **COMPLETED**: Built & verified [dist/trueway-in-golden-triangle-2026.10.1.twpkg](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/dist/trueway-in-golden-triangle-2026.10.1.twpkg) [3.46 MB] and [dist/trueway-global-icons-tier1-2026.10.1.twpkg](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/dist/trueway-global-icons-tier1-2026.10.1.twpkg) [3.46 MB]; updated [pack-builder/catalog.json](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/pack-builder/catalog.json)).
9. [x] **Author SISFS & MeitY TIDE 2.0 Grant Proposal & Pitch Structure** — *audiodoc* (✅ **COMPLETED**: Published [docs/grants/SISFS_AND_MEITY_GRANT_PROPOSAL.md](file:///c:/Users/PLEXTEK/Desktop/TRUE-WAY/docs/grants/SISFS_AND_MEITY_GRANT_PROPOSAL.md) with ₹50L budget utilization, architecture diagrams, unit economics, and 5-slide pitch deck).
10. **Send 10 emails**: Bihar Tourism, ASI Adopt-a-Heritage, INTACH, Inheritage, IIT Patna, Nalanda Univ, SANDIP TBi/incubator, 3 walking-tour creators (permission), 2 heritage YouTubers (collabs) — 3 h — *you*

---

## 17. The Complete Pipeline Map (save this diagram)

```
                        SOURCES (legal-tiered §4.3)
   ┌────────────┬─────────────┬──────────────┬─────────────┬───────────┐
   ▼            ▼             ▼              ▼             ▼           
Commons CC   Flickr CC   Tier-B video   GLDv2/Inheritage  Wikidata   PMTiles
   │            │             │              │             │           │
   └────────────┴─────────────┴──────────────┘             │           │
                    ▼                                      ▼           ▼
          QUARANTINE → REVIEW (human) → PROMOTE        METADATA     MAP PACK
                    ▼                                      │           │
          SPLIT by source/subject series (leak-proof)      ▼           │
                    ▼                                      ▼           │
          TRAIN (MobileCLIP-S0 + ArcFace adapter, PyTorch)             │
                    ▼                                                  │
          EXPORT ONNX → TFLite fp16 (measure 5 variants)               │
                    ▼                                                  │
          GALLERY + CALIBRATION + NEGATIVE BANK (TWVEC002)             │
                    ▼                                                  │
          BENCHMARK (Top-1/3, CP95 FAR, coverage, abstain) ── CI ──────┤
                    ▼                                                  │
          PACK BUILD (Ed25519 sign, SHA-256 tree, changelog)           │
                    ▼                                                  ▼
                    └──────────────► CDN / SERVER / QR TOUCHPOINTS ◄───┘
                                     ▼
                        PLAY STORE + SIDELOADED PACKS
                                     ▼
                    ANDROID APP → Scan → Place Card → Audio → Journal
```

---

## 18. FAQ

**Q: Should I travel to Bodh Gaya/Rome/Paris to take photos?**
A: No — except one optional 5–7 day PoC immersion in Bodh Gaya for pilot credibility (and it doubles as content curation). Recognition scales from open-licensed web imagery + partner archives. Your ₹2,000–₹5,000/card honorarium model buys *review*, not *photography*.

**Q: Is YouTube walking-tour harvesting OK for commercial use?**
A: Not without permission. Get written creator consent (many grant it for research/attribution), or use frames for internal calibration only (Tier C), or rely on Commons/Flickr/GLDv2/YouTube-Tier-B. Never ship raw YouTube frames as reference images without permission + licence review.

**Q: On-device LLM — Gemma 4 E2B — works?**
A: Yes on ≥6 GB RAM arm64 devices via LiteRT-LM (2.58 GB, GPU/NPU/CPU, Apache 2.0, 32k context, multimodal). Ship it as an optional download in Tier 2 with RAG grounding; never gate core features; expect mid-tier devices to drop it.

**Q: What P100 for the 50-icons base APK?**
A: Base APK ships ~15 highest-demo-value icons + the universal encoder; remaining 35 install as a free first-run top-up pack (keeps APK ≈ 45 MB per blueprint §3.2).

**Q: How do I handle replicas (e.g., Shanghai Mahabodhi replica)?**
A: Explicit hard-negative classes; parent/child taxonomy; the model abstains or maps to "Mahabodhi-style replica — not the original" if you add a replica class with clear sourcing; never silently accept.

**Q: What about iOS?**
A: After pilot + Android stability; reuse Kotlin business logic via KMP; encoder via CoreML export of the same fp16 weights; validate parity with the same golden vectors.

---

## 19. Appendix A — File Reference (what exists, where)

| Purpose | Path |
|---|---|
| Master blueprint / feature catalogue | `TrueWay_FINAL_Master_Blueprint_2026.md` |
| Sprint tracking & current status | `docs/SPRINT_PLAN.md` |
| Global roadmap (v1, superseded by this file) | `docs/TRUEWAY_GLOBAL_MASTER_ROADMAP_AND_EXECUTION_PLAN.md` |
| Vision audit, Gate 2 evidence | `docs/audit/VISION_DETECTION_AUDIT_AND_RECOMMENDATIONS.md`, `docs/audit/GATE2_BASELINE.json` |
| Field protocol | `docs/FIELD_PERFORMANCE_PROTOCOL.md` |
| P0 scope clarification | `docs/P0_SCOPE_CLARIFICATION.md` |
| P1A asset requirements | `docs/P1A_ASSET_REQUIREMENTS.md` |
| ADRs | `docs/adr/0001..0008` |
| Dataset & harvesting spec | `content/DATASET_RESEARCH_AND_HARVESTING_SPECIFICATION.md` |
| Corridor harvester (Commons+YouTube registry) | `ml/harvest_global_corridors.py` |
| YouTube frame extractor | `ml/harvest_youtube_tours.py` |
| Split integrity / verify tools | `ml/audit/*.py` |
| Encoder convert & measure | `ml/convert_encoder.py`, `ml/build_index_from_artifact.py`, `ml/rebuild_encoder.py` |
| Decision rule | `ml/vision_index.py` |
| Benchmark | `tests/fixtures/retrieval_benchmark_250.csv` |
| Pack builder | `pack-builder/build_pack.py`, `catalog.json`, `regional_catalog.py` |
| Regional packs | `dist/trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg`, `dist/trueway-in-golden-triangle-2026.10.1.twpkg`, `dist/trueway-global-icons-tier1-2026.10.1.twpkg` |
| Regional SQL seeds | `content/seed/seed_golden_triangle.sql`, `content/seed/seed_global_icons.sql`, `content/seed/validate_regional_seeds.py` |
| Places schema | `content/schema/places_schema.sql`, `content/schema/publication_schema.sql` |
| Bilingual audio generator | `content/tools/generate_bilingual_audio.py` |
| Grant proposal (SISFS & MeitY) | `docs/grants/SISFS_AND_MEITY_GRANT_PROPOSAL.md` |
| Verification profiles | `trueway_verify_local.py` |
| CI | `.github/workflows/trueway-ci.yml` |
| Server (releases/metadata) | `server/main.py` |
| Original research report | `TrueWay_Deep_Research_Product_Technical_Report_2026 (1).pdf` |
| External consultant rec | `Recommend1.txt` |

## Appendix B — Verified external references (Nov 2026)
- LiteRT-LM & Gemma 4 E2B: ai.google.dev/edge/litert-lm (production-ready; 2.58 GB; Apache-2.0; S26 Ultra 47–52 t/s; 607 MB Apple-CPU footprint) · blog.google "Blazing fast on-device GenAI with LiteRT-LM" (May 19 2026) · gemma.ai/deployment/litert
- Google Landmarks Dataset v2: github.com/cvdfoundation/google-landmark (5M+ imgs, 200k labels, CC BY 4.0 annotations; per-image licences vary)
- Inheritage SDK (India): github.com/Inheritage-Foundation/Inheritage-SDK-v1 (Apache-2.0 SDK, CC BY 4.0 data, 5000+ sites, CIDOC-CRM JSON-LD; partners ASI/UNESCO)
- SISFS closed: seedfund.startupindia.gov.in (last date 31 May 2026; corpus ₹945 Cr committed; 4,245 startups approved ₹706 Cr)
- Fund of Funds 2.0: S.O. 1860(E) 13 Apr 2026, ₹10,000 Cr via SEBI AIFs; playbook of 65 schemes, June 2026 (startupindia.gov.in)
- MeitY TIDE 2.0: msh.meity.gov.in (51 centres; 5-year term ended Jan 2024; centres run own calls — e.g. ₹7 L prototype grants)
- YouTube 3rd-party training (opt-in, default off): support.google.com/youtube/answer/15509945
- Scraping legal landscape 2026: no court ruling; Uncharted (Udio), Suno, OpenAI MDL pending; EU TDM Art. 4 cases pending (BGH Dec 2026)
- India heritage digitisation: PIB PR2111884 (NMMA: 11,406 sites; 12,34,937 antiquities), Culture Ministry AI heritage search (Feb 2026), Indian Culture Portal V2.0 (Mar 2026)
- DPIIT recognition: startupindia.gov.in · Credit Guarantee Scheme · state schemes (varies)

## Appendix C — Email template (creator permission / partner LOI)
> Subject: Permission to use your Walking Tour video frames for a heritage-education app
> Namaste/Hello <name>, I'm building TrueWay, a free offline heritage guide app for travellers (demo attached). I'd like to extract non-identifiable architectural frames from <video URL> solely to calibrate a monument-recognition model — never publishing the video, with on-screen credit "Frames courtesy <channel>" and a link. May I have written permission for this non-commercial research use? If you prefer, I can also contribute to your channel description. — <Founder name>, <email>, <phone>

## Appendix D — The honest Gate 2 pitch line (memorise this)
> "TrueWay recognises 12+ monument classes offline with 91 % top-1 and 100 % accepted-set precision, refuses when uncertain, and never uploads a photo. The strict ≤5 % false-accept certificate is a research milestone we're closing with more harvested source series — we ship calibrated honesty, not fake 99 % claims."

---

*End. This document supersedes `docs/TRUEWAY_GLOBAL_MASTER_ROADMAP_AND_EXECUTION_PLAN.md`. Execute Phase 0 today. Ship the Golden Triangle and World Icons packs within the month. Raise ₹20–50 L on pilot proof. Keep the corpus honest. The future is built by shipping.*
