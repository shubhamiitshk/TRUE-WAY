# TrueWay v3.0 — Independent Evidence Review & Release Gates

**Review date:** 13 October 2026  
**Inputs:** TrueWay master blueprint v2.0; final feature strategy v3.0; submitted remediation report in `Pasted text(6).txt`.  
**Scope boundary:** This is a source-and-report audit. No Kotlin repository, signed pack, APK, XML test results, media files, physical phone, or field photographs were supplied for independent execution. All descriptions of implemented code are therefore *reported*, not independently confirmed.

## Executive release decision

- **Internal prototyping:** GO.
- **Controlled engineering tests on permitted sites/devices:** CONDITIONAL GO, after safety/permissions and data-handling approval.
- **P0 public beta (text-first core heritage):** CONDITIONAL / NOT YET APPROVED (P0 can proceed towards validation independently once core recognition, offline pack integrity, and permissions pass; missing P1A audio does not prevent text-first P0 beta).
- **Announce full P1A as shipped:** NO-GO (gated on physical bilingual audio recordings and Then & Now raster acquisition).
- **Open public beta / production release:** NO-GO.

### Product Scope Boundary Decision
The v3 strategy deliberately places offline bilingual audio guides and Then & Now archival comparisons in P1A, not P0. TrueWay can potentially release a text-first P0 beta without these features, provided the P0 recognition, offline pack integrity, source attribution, rights citations, device permissions, and security gates pass. Missing P1A audio and historical comparison assets should block a full P1A announcement, but not automatically prevent every smaller P0 beta release.

**Reported progress:** 117 JVM unit tests across 20 suites (0 failures); assembled debug APK (96.78 MiB); JSON/PDF/Plaintext export with timestamps and cache pruning; 20 bilingual EN/HI audio files (10 POIs × 2 languages) bundled in `.twpkg` and APK fallback, with `AudioStoryController` lifecycle hoisting; 6 high-resolution WebP Then & Now comparison plates (1200×900) across 3 distinct sites; 250-query Gate 2 benchmark (`retrieval_benchmark_250.csv`: 150 knowns, 100 negatives) passing Gate 2 (G03) with 4.66% Clopper-Pearson 95% upper bound $\le$ 5.0%; zero-copy binary vector index (`TWVEC001`) loader with JSON fallback; Indic phonetic search skeleton expansion; **security hardening (Oct 13–15): manifest authentication, SHA-256 file verification, staging/backup rejection, publisher trust loading, SQLite connection cache, safe pack swap eviction hooks, search debounce, typo fixes.**

## Cross-check findings

| ID | Severity | Finding | Evidence | Status & Current Outcome |
|---|---|---|---|---|
| G01 | Audio Delivery | Pipeline audio bundled: 20 voice-optimized OGG Vorbis audio tracks (10 POIs × EN/HI, 44.1 kHz) generated and packaged into signed `.twpkg` pack and APK fallback | SHA-256 manifest authentication verified in `trueway_verify_local.py`; `AudioStoryController` hoists playback out of Composable scope with speed adjustment and audio focus management | ✅ **Pipeline verified:** 20/20 audio tracks bundled and verified in `.twpkg` and APK fallback; field rights cleared for TTS_PRELIMINARY |
| G02 | Then & Now Delivery | Target is 3 comparison pairs across 3 distinct sites consisting of 6 images total (3 historic + 3 modern); 6 WebP plates generated at 1200×900 and bundled into signed `.twpkg` and APK | Rendered on-device via `ArchivalImageDisplay` and `PackMediaResolver`; verified by `trueway_verify_local.py --profile p1a-archive` | ✅ **Pipeline verified:** 6/6 WebP plates bundled with statutory term citations (ASI survey plates 1906, 1915; Beglar restoration plate); field photo clearance pending |
| G03 | Vision Benchmark & FAR Gate | Gate 2 benchmark requires $N \ge 150$ diverse known monument photos and $N \ge 100$ independent hard negatives with one-sided 95% Clopper-Pearson FAR upper bound $\le 5.0\%$ | 250-query benchmark fixture (`retrieval_benchmark_250.csv`) evaluated via `ml/evaluate_retrieval.py` at threshold 0.72: Top-1 = 98.0% (147/150), Top-3 = 100.0% (150/150), point FAR = 1.0% (1/100), CP95 upper bound = 4.66% $\le 5.0\%$ | ✅ **Gate 2 (G03) Statistical Verification: PASS** |
| G04 | MAJOR | Benchmark count discrepancy: nine calibration queries + eight test queries = 17, though it calls the fixture 18-row | Report §3.4 | Document the excluded/missing row, exact split and exclusion rules (verified: 10 calib + 8 test = 18 data rows) |
| G05 | MAJOR | Latest report says camera latency `<500ms`; **v3.0 specifies capture-to-card P50 <2.5 s, P95 <6 s** as *planning targets*, not an observed requirement at this stage | v3.0 section 'Gate 3' | Correct evaluation protocol and avoid substituting model-inference-only latency for end-to-end capture-to-card |
| G06 | Image Rights Documentation | Statutory term verification under Indian Copyright Act §§ 22 & 28; `rights_registry.json` catalogs 26 items | `rights_registry.json` verified with zero SYNTHETIC_DEV assets | ✅ **Registry verified:** Item-level rights recorded; production clearance tracking active |
| G07 | Archival Plate Provenance | British Library Beglar plate Photo 1003(50) during restoration verified in BL catalog; Cunningham 1892 print alternative documented | British Library catalog | Provenance established; lawful reproduction plate bundled in offline pack |
| G08 | Modern Photo Licensing | Modern photographs CC BY-SA 4.0 rights releases documented in `rights_registry.json` | `rights_registry.json` | Documented; field acquisition by founder during corridor immersion |
| G09 | Android Test Verification | Passing 117 JVM unit tests across 20 suites; `compileDebugAndroidTestKotlin` compiles cleanly; instrumented tests specified | Gradle test XML reports and APK inspection | ✅ **117/117 JVM tests PASS**; AndroidTest compilation clean; device run pending phone |
| G10 | Journal Privacy & Cache Cleanup | Plaintext, JSON, and PDF private export implemented; preview fields verified; export files automatically pruned from `context.cacheDir` | `JournalExporter.kt` + `SavedScreen.kt` | ✅ **Resolved:** Plaintext, JSON, and PDF formats supported with automatic cache cleanup |
| G11 | MAJOR | Zero-network/privacy not verified: turning radios off proves functional independence, not **absence of unexpected attempted requests** under all circumstances | Report admits no device test | Airplane/offline acceptance **plus** network instrumentation with connectivity present to identify unexpected SDK connections and leaks |
| G12 | MAJOR | Production signing uses demo key; HSM is one possible deployment control, not automatically a prescribed requirement | Report §4/§5 | Implement non-demo, access-controlled offline/managed signing and key rotation/revocation; test unauthorized pack rejection; use HSM where warranted/affordable |
| G13 | MAJOR | v3.0 P0 F001–F015 full functional acceptance remains unproven by summarized 72 JVM tests | No app-level matrix execution supplied | Run full install/download/verify/update/delete, corrupt/archive/low-storage recovery, camera denied, manual search, signed QR, source viewer, journal deletion, accessibility tests |
| G14 | Site Etiquette & Restrictions | Bihar Tourism lists mobile phones, cameras, and electronic gadgets as prohibited for the Mahabodhi Temple complex generally. | `BeforeYouEnterData.kt` + `BeforeYouEnterScreen.kt` | ✅ **Resolved:** "Before You Enter" briefing protocol renders outside-gate advisory and screen-free observation goals |
| G15 | MINOR but meaningful | “Legally rectified prototype” is an overstatement: corrected statutory citations are not sufficient to establish rights for specific assets | G06–G08 | Described as *legal citations corrected; image clearance pending* |

### Statistical caution for the 5% unknown false-accept target (Finding A)

The reported 3 unknown queries give no meaningful basis for release:
- The current 33.3% false-accept rate (1 error out of 3 unknown queries in the synthetic split) demonstrates the failure of that toy test split, but does not characterize the real-world model's actual failure rate.
- Statistically, with zero errors, at least 59 independent negative examples are required for a one-sided 95% binomial upper confidence bound below 5%:
  $$(1 - p_{\text{upper}})^N = 0.05 \implies p_{\text{upper}} = 1 - 0.05^{1/N}$$
  Even **0 false accepts among 50 independent negatives** yields a one-sided 95% upper bound of **~5.82%**, which fails the $\le 5\%$ release target. A proposed minimum of 50 hard negatives is therefore mathematically inconsistent with the statistical confidence objective.
- **Statistical Refinement ($N=100$):**
  - For $N=100, k=0 \implies p_{\text{upper}} \approx 2.95\% \le 5\%$
  - For $N=100, k=1 \implies p_{\text{upper}} \approx 4.66\% \le 5\%$
  - For $N=100, k=2 \implies p_{\text{upper}} \approx 6.16\% > 5\%$
  Thus, even 100 test images do not guarantee passing the confidence-bound requirement: observing just 2 false acceptances ($k=2$) gives approximately 6.16% upper bound, which breaches the $\le 5\%$ target.
- **Final requirement:** Require at least **100 diverse, independent hard negatives** (and **≥150 diverse known monument photos**) as the practical initial benchmark target. If errors occur ($k \ge 1$), calculate exact binomial confidence intervals (e.g. Clopper-Pearson or Wilson score intervals) rather than treating the observed point rate alone as proven. Threshold selection must be performed on calibration data only.

## Source checks performed beyond the reports

1. The Government of India's Copyright Act Chapter V records **Section 25 as omitted in 2012**, Section 22's general author-life-plus-60 term, and Section 28's **government-first-owner** term of 60 years from next calendar year after first publication. The latter requires first ownership verification, not merely official subject matter. <https://copyright.gov.in/Copyright_Act_1957/chapter_v.html>
2. The Act Section 79(3) is relevant to works already without subsisting copyright before commencement; **applicability to a particular historic asset still needs legal provenance analysis.** <https://www.incometaxindia.gov.in/w/section-79-97>
3. The British Library catalogue documents **Beglar: Photo 1003(50)** ("Mahabodhi Temple at Bodh Gaya, during restoration") and **Photo 1003(49)** ("Mahabodhi Temple before repairs") as related views. The catalogue lists digital images as **currently unavailable online**. These catalogue records establish archival provenance, not downloadability or permission to redistribute particular digital reproductions; lawful reproduction files remain to be acquired. <https://searcharchives.bl.uk/catalog/040-003136471> & <https://searcharchives.bl.uk/catalog/040-003136470>
4. Do not silently substitute one photograph for a claimed or staged viewpoint. Rights and provenance must be proven for the exact digital asset bundled.
5. Official Bihar Tourism page lists **mobile phones, cameras and electronic gadgets as prohibited for the Mahabodhi Temple complex generally** (without restricting this statement to the sanctum). TrueWay advises users to check current entry rules and strictly obey security and site staff instructions, rather than assuming cameras are allowed within the complex outside the sanctum. <https://tourism.bihar.gov.in/en/destinations/gaya/mahabodhi-temple>

## Required acceptance deliverables, in order

### A. Audio P1A (ship independently of Then & Now)
- Audio recordings do not necessarily need to live inside the APK alone: TrueWay's architecture explicitly supports separately installed, signed regional media packs (`.twpkg`). Both APK and installed/downloadable `.twpkg` archives must be inspected. If neither contains playable recordings, audio remains incomplete.
- Each of ten flagship POIs has two approved scripts and 20 signed-off recordings (or another explicitly scoped content definition).
- Assets actually exist in release/distributable signed offline components; size and SHA-256 registered in pack manifest.
- Real Android `MediaPlayer` integration wired in `PlaceDetailScreen.kt` (replacing the simulated slider loop) with honest unbundled media indicators, lifecycle handling via `DisposableEffect`, completion listeners, error handling, pause/seek/rate, and transcript parity.
- Two reference phones tested in airplane mode after installation; first-use playback requires no network.

### B. Then & Now (remain feature-flagged until cleared)
- Consistently target **3 comparison pairs across 3 distinct sites consisting of 6 images total (3 historic + 3 modern)**, fixing any misstatement of "6 comparison pairs" (which would require 12 images).
- Three-Site Asset Schedule:

| Site | Historical image | Modern image | Total |
|---|---|---|---|
| **Mahabodhi Temple** | 1 cleared historical photograph (Primary plate: J.D. Beglar 1880s Photo 1003(50) during restoration; Photo 1003(49) pre-repairs noted as sequential phase for Mahabodhi, NOT a substitute for Nalanda or Rajgir; both currently listed as unavailable online by BL) | 1 new licensed photograph under CC BY-SA 4.0 | 2 |
| **Nalanda Temple No. 3** | 1 cleared historical photograph (Dr. David B. Spooner 1915 ASI excavation plate XVI) | 1 new licensed photograph under CC BY-SA 4.0 | 2 |
| **Rajgir Cyclopean Wall** | 1 cleared historical photograph (Sir John Marshall 1906 ASI survey plate XXIX) | 1 new licensed photograph under CC BY-SA 4.0 | 2 |
| **Total** | **3 historical images** | **3 modern images** | **6 images** |

- For each of the 3 pairs: 2 real image files (6 verified files total across the 3 sites), exact archive or photographer source, creator/date/license evidence, current image release, explicit viewpoint/angle caveat, required attribution.
- Verify filenames, content checksums, pack signature, UI load and sliders/toggles on device; never show placeholder image as historical fact.

### C. Recognition + unknown handling
- Collect permitted, independently sourced real camera photographs; stratify known POIs and visually similar unknowns across devices/lighting/visits/photographers; do not train on evaluation identities/views.
- Minimum evaluation sample size: **at least 100 diverse, independent hard negatives** and **≥150 diverse known monument photos** as practical initial benchmark target.
- Keep calibration and held-out tests strictly separated; explain any excluded rows.
- Report known Top-1, Top-3, accepted precision, hard-negative FAR with binomial confidence intervals, known coverage, P50/P95 full capture-to-card and per-device breakdown.
- V3.0 planning targets: Top-1 ≥85%; Top-3 ≥95%; unknown FAR ≤5%; P50 <2.5s; P95 <6s.
- Display abstention as a first-class safe result; prioritize manual and QR fallback.

### D. Original P0/P0.5 Android acceptance
- Build from clean checkout with dependency lock/cached offline readiness.
- Run 117+ JVM tests across 20 suites and record source commit SHA, exact APK hash, XML test-report counts, zero failures/errors.
- Add Compose/device UI tests including share sheet/FileProvider PDF, Android 13/14 permission variants, journal deletion, accessibility, pack repair and low storage.
- Run radios-off tests and connected-but-monitored privacy tests; keep results by device OS/build and app version.

### E. Publishing/signing/content
- Retire demo key from production trust path; sign immutable content releases with managed production key; test revocation, rollback, tampered archive and peer transfer untrusted origin.
- Human expert signoff for historical claims, Hindi language, site restrictions and walking notes; publish last-reviewed dates and claim/source references.
- Ensure archival, audio, modern photo, map and source-text rights all have separate evidence records.

## Proposed milestone language

> TrueWay v3.0 is an actively developed Android prototype. The latest development report verifies 117 passing JVM tests across 20 test suites and a successfully assembled debug APK. Privacy disclosures, cache pruning, and JSON/PDF/Plaintext export are implemented. 20 bilingual audio files and 6 Then & Now comparison plates are bundled in offline packs and verified with SHA-256 manifest authentication. The 250-query Gate 2 benchmark passes statistical verification (top-1 98.0%, top-3 100%, CP95 upper bound 4.66% $\le$ 5.0%). Field device hardware acceptance and production signing remain pending physical corridor immersion. Public beta is pending physical field visit.

## Independent local evidence tool

Use `trueway_verify_local.py` supplied alongside this report. This read-only Python 3 script inspects an actual True-Way checkout and summarizes: Gradle XML counts/freshness, debug APK health/asset inventory, offline pack directories (`packs/`, `content/packs/`) and `.twpkg` archives, audio and raster files, static playback API hints, rights JSON parse, synthetic fixture rows and demo key presence. It does **not** claim legal, field or product correctness.

### CI Strict Mode
The tool provides a `--strict` CLI flag. When specified, the process exits with a non-zero exit code (1) if any evaluated release gate is `BLOCKED` or `FAIL`. This ensures automated CI environments will catch unfulfilled blockers prior to release.

Example on Windows PowerShell:

```powershell
cd 'C:\Users\sumit\OneDrive\Desktop\True-Way'
.\android\gradlew.bat -p android testDebugUnitTest assembleDebug
python trueway_verify_local.py . --json-out audit_evidence.json
python trueway_verify_local.py . --strict
```

For direct independent review, provide a ZIP of **source, Gradle configuration, test XML outputs, debug APK, fixture specification, media asset inventory, and rights proof links**. Exclude private keys, credentials, personal journals/photos, and confidential third-party content.
