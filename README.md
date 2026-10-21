# TrueWay — Offline-first AI Heritage & Travel Companion

**Product promise:** _Capture. Discover. Understand. Anywhere._

TrueWay helps travellers identify a **supported** place, discover historically sourced explanations and explore curated local heritage **after downloading the necessary region pack**, even when internet access disappears. When evidence is weak or a site is not supported, TrueWay says so rather than fabricating a name or history.

> This repository is the **implementation** of `TrueWay_FINAL_Master_Blueprint_2026.md`, the strategic [docs/STRATEGIC_TECHNOLOGY_BLUEPRINT_2026_2027.md](docs/STRATEGIC_TECHNOLOGY_BLUEPRINT_2026_2027.md), the system architecture [docs/SYSTEM_ARCHITECTURE_SPECIFICATION.md](docs/SYSTEM_ARCHITECTURE_SPECIFICATION.md), and the [docs/CTO_PROJECT_PLAN_AND_MULTI_AGENT_STRATEGY.md](docs/CTO_PROJECT_PLAN_AND_MULTI_AGENT_STRATEGY.md). See [docs/SPRINT_PLAN.md](docs/SPRINT_PLAN.md) for delivery tracking.
>
> 🧭 **Founder Directives ([docs/FOUNDER_FIELD_GUIDE_AND_TEN_DIRECTIVES.md](docs/FOUNDER_FIELD_GUIDE_AND_TEN_DIRECTIVES.md)):**
> - **North Star Metric:** `% of sessions where a user reads a full place card.`
> - **Pilot Success Definition:** 30 real users complete a full journey (discover $\rightarrow$ read story $\rightarrow$ discover 2nd place), and $\ge 10$ recommend TrueWay.
> - **Immediate Action:** Trademark clearance check (₹10–20k) & 5–7 day Bodh Gaya field immersion before full app scale.
> - **Guesthouse Hack:** Partner with Bodh Gaya international monastery guesthouses for reception QR displays (solves the pre-trip offline download dilemma).

## Status

**Feasibility demonstrator with v3.0 P0.5 Hardening, P1A Experience Epics, and P1B Offline Heritage Insights & Q&A complete.**
- Scan: capture → embed → rank → calibrated accept/unknown with on-device `vision_encoder.tflite` (a 23.3 MB MobileCLIP-S0 **fp16** encoder — the variant `ml/convert_encoder.py` *measured* as fastest, with the Sub-Center ArcFace adapter as a separate `Linear` after the L2 normalisation; the reference vectors are extracted with that same file). The gate is **relative** (the winner must beat the strongest hard-negative exemplar) and the thresholds are **learned on the held-out calibration split and shipped in the pack** — the device no longer uses hard-coded constants. Flip-only test-time augmentation, a bounded heavy-tailed **geo soft prior** (re-ranker, never a gate), one process-scoped encoder instead of a per-capture reload, and measured (not fabricated) margins.
- Search: bilingual Latin & Devanagari transliteration quick-pills, category filtering, and offline FTS index
- Sourced History: factual claims classified as `DOCUMENTED`, `INTERPRETATION`, `TRADITION`, `CONTESTED` with verifiable bibliography citations
- Offline Site Insights, Study Lite & Q&A: P1B multi-depth explanations (F104+F109+F116) across all 15 POIs with `Traveller Guide` (EN/HI), `What to Spot On-Site` architectural spotter checklists, `Scholar Lens` chronological timelines, interactive **Study Lite** epistemic self-checks (`F116`), circuit-wide offline topic/Q&A search on `ExploreScreen`, and deterministic citation-grounded **Offline Q&A** with honest abstention
- On-Site Signboard & Plaque Decoder: P1B `F103` bilingual (`EN`/`हिं`) decoder for official visitor/safety signs and ASI architectural/iconographic terms with explicit epigraphy boundaries (`SignboardGlossary.kt`)
- Site Compliance: P0.5 "Before You Enter" briefings for restricted sites (Mahabodhi device ban, Nalanda ruins, Griddhakuta ascent) with bilingual takeaway & architectural spotter memory cards
- Audio & Pronunciation: P1A bilingual audio story narratives (F101+F110, 20 OGG recordings generated for 10 POIs × EN/HI, bundled in APK & signed pack), accessible text transcripts, and phonetic IPA guides
- Curated Trails & Foreground Stop Tracker: 3 authored heritage walking trails (F105+F106+F112) with terrain caveats, heat warnings, foreground geodesic stop-to-stop distances, visited-stop checklist, and inline EN/HI audio story playback
- Heritage Passport: private commemorative stamp collection (F107) in local `user_journal.sqlite` (separate from read-only `places.sqlite`)
- Then & Now: curatorial 1880s–1915 ASI survey photographic comparisons (F108, 6 WebP plates generated at 1200x900) with rights statements, inline image rendering, and conservation notes
- Offline Nearby: F005/F008 geodesic proximity ranking using on-device Haversine math with zero network tracking
- Sharing & Export: F114+F117 Android system place card sharing with citations and private journal export in Plaintext, JSON, and PDF formats
- Offline Diagnostics: 10-layer on-device self-test (including Geodesic Proximity Engine and Phonetic Search & Media Trust Boundary) verifying zero-network readiness
- Binary Vector & Insight Packs: Zero-copy `TWVEC002` binary vector index (`vision/reference_vectors.bin`, `vision/index.bin`) — **float32** gallery, one or more references per place, the pack's learned calibration, and a digest of the actual encoder artefact — plus `content/heritage_insights.json`, emitted by `build_pack.py` with SHA-256 tree verification in `manifest.cjson`
- CI Pipeline: Automated GitHub Actions workflow (`.github/workflows/trueway-ci.yml`) verifying SQL seed, scholar template, **dataset integrity (source-photo-grouped splits, no near-duplicate leakage, every reference human-verified)**, the open-set benchmark against the pack's learned calibration with a **regression check against a recorded baseline**, staging the vision encoder into the APK, 140 JVM tests, androidTest compilation, and strict production verification on every commit

### Vision detection — current measured state

The scanner is measured on a **human-verified corpus** whose splits are grouped by **source
subject series** (photographs of the same monument from the same visit are near-duplicates of each
other and are *not* independent trials).

| Metric | Value | Gate | Status |
|---|---|---|---|
| Top-1 (known) | **91.1 %** (112/123) | >= 85 % | **PASS** |
| Top-3 (known) | **96.8 %** (119/123) | >= 95 % | **PASS** |
| Coverage (accepted) | **68.3 %** | - | - |
| Abstention on true matches | **31.7 %** | <= 30 % | FAIL |
| Accepted-set precision | **100.0 %** (84/84) | - | - |
| False-accept rate (point, rows) | **1.0 % (2/197)** | <= 5 % | **PASS** |
| False-accept rate (independent subject series) | **3.3 % (3 of 91)** | <= 5 % | **PASS** |
| FAR, Clopper-Pearson 95 % at the **effective** n = 91 | **8.30 %** | <= 5 % | FAIL - a certificate needs zero failures |
| Independent test **subject series** | 41 known / 91 negative | 150 / 59 | **FAIL** (the negative half is met) |

**Gate 2 (G03) still does not pass, and now fails loudly.** Both accuracy gates and the
point false-accept rate (**3.3 % (3 of 91)**) are met, but the Clopper-Pearson 95 % bound is
**8.30 %**: a certificate at the <= 5 % the gate asks for needs **zero** false accepts at an
effective n of at least 59. The corpus is still the binding
constraint - **651 approved / 11 rejected** source photographs across 12 vision classes and 13
hard-negative categories, but most classes still have only **1-3** reference photographs from
independent visits, and the test split's known series (41) is under a third of the 150 the
gate asks for.

**The shipped encoder is the measured one.** `ml/convert_encoder.py` builds five variants and
*measures* each: **fp16 (23.3 MB, cos 1.0000 vs ONNX)**, fp32 (46.5 MB), int8 dynamic-range
(12.3 MB, cos 0.987), and int8 per-tensor / per-axis, which are **5-6x slower than FP32 and
fail the agreement floor outright** (cos 0.23 / 0.53). "Smaller is not faster" - the smallest
artefact was the worst one. The gallery, the calibration and the benchmark are extracted **with
that same artefact**, so the reference vectors the device scores against are the reference vectors
the shipped model produces.

The decision rule applies the **CSLS hubness correction** (Conneau et al.): the similarity of a
query to a gallery vector is rescaled by the local density of both, which suppresses the handful
of gallery vectors that are close to everything - and those are exactly the ones that turn a
lookalike into a confident false accept. The local density of every gallery vector ships in the
index. Measured here: the false-accept rate fell from 24 % to **3.3 %** and the abstention rate
on true matches from 50 % to **31.7 %**.

**Taxonomy.** Three of the fifteen circuit places are **search-only**: the Bodhi Tree, the Vajrasana
and the Nalanda Archaeological Museum. A photograph of them is not separable from their
surroundings, so claiming to have "recognised" them would produce a wrong answer; they are surfaced
as **spotter items on the parent place's card** instead (blueprint §7.2: *"Separate parent sites
from visually identifiable child structures, to prevent inflated 'accuracy' from generic large-site
names"*).

The previous "100 % Top-1 / 0 % FAR" figure was an artefact: every test query was a synthetic
augmentation of a photograph that was also in the reference set, and the CI gate could not fail.
Both are fixed. See
[docs/audit/VISION_DETECTION_AUDIT_AND_RECOMMENDATIONS.md](docs/audit/VISION_DETECTION_AUDIT_AND_RECOMMENDATIONS.md)
for the full audit, the measured evidence, and the collection plan.

**Test suite: 140/140 JVM unit tests green across 24 test suites** (including a cross-language
parity test that replays 225 golden decision vectors through the real binary reader and asserts
the device reaches the same decision the workstation evaluator does), `assembleDebug` and
`compileDebugAndroidTestKotlin` build cleanly, and all 4 audit profiles PASS
(`trueway_verify_local.py`). See [docs/SPRINT_PLAN.md](docs/SPRINT_PLAN.md) and
[docs/CONFLICT_REGISTER.md](docs/CONFLICT_REGISTER.md).

## Repository layout (blueprint §8.4)

| Directory | Boundary |
|---|---|
| `android/` | Kotlin app: Compose UI, camera, services, persistence, tests |
| `ml/` | Feature extraction, quantization, evaluation harness |
| `content/` | Typed claims, rights registry, bibliography, translations, SQLite schemas |
| `pack-builder/` | Canonical signed manifest, compression, signing |
| `server/` | Distribution, release metadata, opt-in reports |
| `site-partners/` | Contracts/templates only — **no credentials committed** |
| `tests/` | Golden queries, known/unknown images, offline regression protocol |
| `docs/` | ADRs, sprint plan, privacy/content policies, release checklists |

## Building the app

```powershell
cd android
.\gradlew.bat assembleDebug          # debug APK → app/build/outputs/apk/debug/
.\gradlew.bat testDebugUnitTest      # JVM unit tests
```

Requirements: JDK 17, Android SDK with platform 35 and build-tools 35.x, `ANDROID_HOME` set (or `local.properties` with `sdk.dir`).

> **Note on this machine:** `services.gradle.org` / `downloads.gradle.org` are unreachable, so the Gradle wrapper points at `gradle-8.13-bin.zip`, which is already present in the local wrapper cache (`%USERPROFILE%\.gradle\wrapper\dists`). Dependency resolution uses `google()` and `mavenCentral()`, both verified reachable.

## Principles that constrain every contribution (blueprint §3)

1. **Offline means usable, not merely launchable** — after setup, core paths must not need the network.
2. **Abstention over fabrication** — never force a landmark name; unknown is a first-class state.
3. **Source traceability** — every published claim links to a source; fact vs. interpretation vs. tradition is visible.
4. **Pack integrity** — only signed, hash-verified packs activate; failure preserves the previous pack.
5. **Privacy** — no off-device photo/audio uploads; no hidden account; one-tap deletion.

## Legal notice

Speculative product in development. Not legal, safety, or archaeological certification. "TrueWay" is a working title pending trademark/domain clearance (blueprint §1.2).
