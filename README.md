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

**Feasibility demonstrator with v3.0 P0.5 Hardening and P1A Experience Epics complete.**
- Scan: capture → embed → rank → calibrated accept/unknown with on-device `vision_encoder.tflite` (~4.1 MB MobileCLIP-S0)
- Search: bilingual Latin & Devanagari transliteration quick-pills, category filtering, and offline FTS index
- Sourced History: factual claims classified as `DOCUMENTED`, `INTERPRETATION`, `TRADITION`, `CONTESTED` with verifiable bibliography citations
- Site Compliance: P0.5 "Before You Enter" briefings for restricted sites (Mahabodhi device ban, Nalanda ruins, Griddhakuta ascent)
- Audio & Pronunciation: P1A bilingual audio story narratives (F101+F110, 20 OGG recordings generated for 10 POIs × EN/HI, bundled in APK & signed pack), accessible text transcripts, and phonetic IPA guides
- Curated Trails: 3 authored heritage walking trails (F105+F112) with terrain caveats, heat warnings, and sequenced stops
- Heritage Passport: private commemorative stamp collection (F107) in local `user_journal.sqlite` (separate from read-only `places.sqlite`)
- Then & Now: curatorial 1880s–1915 ASI survey photographic comparisons (F108, 6 WebP plates generated at 1200x900) with rights statements, inline image rendering, and conservation notes
- Offline Nearby: F005/F008 geodesic proximity ranking using on-device Haversine math with zero network tracking
- Sharing & Export: F114+F117 Android system place card sharing with citations and private journal export in Plaintext, JSON, and PDF formats
- Offline Diagnostics: 10-layer on-device self-test (including Geodesic Proximity Engine and Phonetic Search & Media Trust Boundary) verifying zero-network readiness
- Binary Vector Packs: Zero-copy `TWVEC001` binary vector index (`vision/reference_vectors.bin` and `vision/index.bin`) emitted by `build_pack.py` with SHA-256 tree verification in `manifest.cjson`
- CI Pipeline: Automated GitHub Actions workflow (`.github/workflows/trueway-ci.yml`) verifying SQL seed, scholar template, Gate 2 250-query benchmark, 117 JVM tests, androidTest compilation, and strict production verification on every commit
- **Test suite: 117/117 JVM unit tests green across 20 test suites, `assembleDebug` and `compileDebugAndroidTestKotlin` build cleanly, all 4 audit profiles PASS (`trueway_verify_local.py`), and Gate 2 (G03) 250-query statistical evaluation PASSES (Clopper-Pearson 95% upper bound = 4.66% $\le$ 5.0%).** See [docs/SPRINT_PLAN.md](docs/SPRINT_PLAN.md) and [docs/CONFLICT_REGISTER.md](docs/CONFLICT_REGISTER.md).

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
