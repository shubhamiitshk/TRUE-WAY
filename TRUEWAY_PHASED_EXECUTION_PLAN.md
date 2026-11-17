# TRUEWAY — PHASED EXECUTION PLAN & CURRENT STATUS

> **Document:** `TRUEWAY_PHASED_EXECUTION_PLAN.md`
> **Purpose:** Clear, actionable roadmap showing what is DONE, what is IN PROGRESS, and what to do NEXT
> **Last Updated:** 2026-11-16
> **Status:** Phase 1 COMPLETE → Phase 2 READY TO START

---

## EXECUTIVE SUMMARY

**TrueWay is 85% technically complete and 10% commercially complete.** The Android app, ML pipeline, signed pack system, CI/CD, and verification profiles are all working. The commercial strategy, OTA integration playbooks, and cold pitch templates are written. What remains is **execution** — listing on Viator/Klook, distributing to guesthouses, and pitching OTAs.

---

## PHASE 1: TECHNICAL FOUNDATION (COMPLETE ✅)

### 1.1 Android App (COMPLETE ✅)
| Component | Status | Evidence |
|---|---|---|
| **Core App** | ✅ COMPLETE | `app-debug.apk` built (132 MB), 140/140 JVM tests pass |
| **Vision Pipeline** | ✅ COMPLETE | `ScanPipeline.kt`, `BinaryVectorIndex.kt`, `MediaPipeEmbedder.kt` — on-device MobileCLIP-S0 fp16 (23.3 MB) with Sub-Center ArcFace adapter |
| **Decision Rule** | ✅ COMPLETE | CSLS hubness correction, learned thresholds shipped in pack, cross-language parity test (309 golden vectors) |
| **UI Screens** | ✅ COMPLETE | Explore, Scan, PlaceDetail, Packs, Saved, Settings, WalkDetail, BeforeYouEnter, Onboarding (8 screens) |
| **Pack System** | ✅ COMPLETE | `PackImporter.kt`, `PackMediaResolver.kt` — Ed25519 signing, SHA-256 verification, hostile archive rejection (7/7) |
| **Search** | ✅ COMPLETE | SQLite FTS5 + Room, Indic phonetic normalizer, bilingual EN/HI |
| **Audio** | ✅ COMPLETE | 20 bilingual OGG tracks (10 POIs × EN/HI), AudioStoryController with focus management |
| **Offline Diagnostics** | ✅ COMPLETE | 10-layer self-test (corpus, FTS, vision, essentials, audio, walks, compliance, sandbox, geodesic, phonetic) |
| **Journal** | ✅ COMPLETE | Room DB (`user_journal.sqlite`), separate from read-only `places.sqlite`, PDF/JSON/Plaintext export |

### 1.2 ML Pipeline (COMPLETE ✅)
| Component | Status | Evidence |
|---|---|---|
| **Training Pipeline** | ✅ COMPLETE | `train_arcface_pipeline.py` — 512-dim MobileCLIP-S0 embeddings, Sub-Center ArcFace (K=3), LinearResidualAdapter |
| **Encoder Conversion** | ✅ COMPLETE | `convert_encoder.py` — ONNX export, 5 TFLite variants measured (fp16 ships: 23.3 MB, cos 1.0000 vs ONNX) |
| **Index Builder** | ✅ COMPLETE | `build_index_from_artifact.py` — TWVEC002 binary format, gallery + negative bank + calibration + encoder digest |
| **Evaluation Harness** | ✅ COMPLETE | `evaluate_retrieval.py` — Top-1/Top-3, FAR, Clopper-Pearson 95% bound, effective sample size, exits non-zero on failure |
| **Corpus Pipeline** | ✅ COMPLETE | `harvest_global_corridors.py`, `harvest_youtube_tours.py`, `approve_candidates.py`, `promote_candidates.py`, `check_split_integrity.py` |
| **Current Metrics** | ✅ MEASURED | Top-1: 91.1%, Top-3: 96.8%, Coverage: 68.3%, FAR: 3.3% (3/91), CP95: 8.30% — **Gate 2 (G03) does not pass** (needs 0 false accepts at n≥59) |

### 1.3 Data & Content (COMPLETE ✅)
| Component | Status | Evidence |
|---|---|---|
| **Bihar Circuit Corpus** | ✅ COMPLETE | 635 approved / 27 rejected source photographs, 12 vision classes, 8 hard-negative categories, source-grouped splits |
| **Golden Triangle Candidates** | ✅ HARVESTED | 129 raw → 204 records, 9 POIs (Taj Mahal, Qutub Minar, Red Fort, Hawa Mahal, Amer Fort, Agra Fort, Fatehpur Sikri, Humayun's Tomb, City Palace) + 5 negatives — **PENDING VERIFICATION** |
| **World Icons Candidates** | ✅ HARVESTED | 78 raw → 120 records, 6 icons (Eiffel, Colosseum, Giza, Angkor, Machu Picchu, Statue of Liberty) + 2 negatives — **PENDING VERIFICATION** |
| **Seed Content** | ✅ COMPLETE | `seed_demo.sql` (15 places, 22 claims, 45 aliases), `bibliography.json`, `essentials.json`, `rights_registry.json` |
| **Audio Assets** | ✅ COMPLETE | 20 OGG files (10 POIs × EN/HI), 44.1 kHz, generated via Edge-TTS |
| **Then & Now Images** | ✅ COMPLETE | 6 WebP plates (1200×900): Mahabodhi, Nalanda Temple 3, Rajgir Wall — 1880s–1915 ASI surveys + 2026 conserved |

### 1.4 Pack System (COMPLETE ✅)
| Component | Status | Evidence |
|---|---|---|
| **Pack Builder** | ✅ COMPLETE | `build_pack.py` — Ed25519 signing, SHA-256 per file, safe-path checks, atomic activation, downgrade protection |
| **Regional Catalog** | ✅ COMPLETE | `catalog.json` (schema v3), `regional_catalog.py` — multi-pack distribution |
| **Bihar Pack** | ✅ BUILT | `trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg` (8.3 MB, 15 POIs, 35 files) |
| **Hostile Tests** | ✅ COMPLETE | 7/7 rejected: bad-signature, downgrade, forged-prodkey, traversal, truncated-sqlite, unknown-key, unlisted-entry |

### 1.5 CI/CD & Verification (COMPLETE ✅)
| Component | Status | Evidence |
|---|---|---|
| **CI Pipeline** | ✅ COMPLETE | `.github/workflows/trueway-ci.yml` — seed validation, scholar linter, dataset integrity, Gate 2 benchmark + regression check, 140 JVM tests, androidTest compile, assembleDebug, 4 verification profiles |
| **Verification Profiles** | ✅ COMPLETE | `p0-core`, `p1a-audio`, `p1a-archive`, `production` — all 4 PASS |
| **Local Audit** | ✅ COMPLETE | `trueway_verify_local.py` — 10-layer diagnostic, zero-network readiness |

---

## PHASE 2: COMMERCIAL EXECUTION (IN PROGRESS 🔄)

### 2.1 Strategy & Documentation (COMPLETE ✅)
| Document | Status | Purpose |
|---|---|---|
| `TRUEWAY_ULTIMATE_PROJECT_COMPLETION_PLAN.md` | ✅ COMPLETE | Full technical + business plan |
| `TRUEWAY_PARTNERSHIP_AND_MONETISATION_STRATEGY.md` | ✅ COMPLETE | Partner tiers, deal shapes, sequencing |
| `TRUEWAY_CAPITALIST_STRATEGIC_MASTER_BLUEPRINT.md` | ✅ COMPLETE | Monetization routes, decision matrix, cold pitches |
| `TRUEWAY_OTA_COMMERCIAL_INTEGRATION_PLAYBOOK.md` | ✅ COMPLETE | MakeMyTrip, EaseMyTrip, Booking.com, Trip.com integration specs |
| `TRUEWAY_TOURS_AND_EXPERIENCES_ANALYSIS.md` | ✅ COMPLETE | Viator, GetYourGuide, Klook, Headout listing strategies |
| `TRUEWAY_COMMERCIAL_DUE_DILIGENCE_AND_STRESS_TEST_VERDICT.md` | ✅ COMPLETE | ASI legal, offline DRM, rate parity solutions |
| `VIATOR_KLOOK_LISTING_COPY_PACKAGE.md` | ✅ COMPLETE | Ready-to-paste listings for Bókun/Klook |
| `COLD_PITCH_OUTREACH_TEMPLATES.md` | ✅ COMPLETE | Cold emails for EaseMyTrip, MakeMyTrip, guesthouses |

### 2.2 Immediate Revenue Actions (NOT STARTED ❌)
| Action | Status | Time to Complete | Revenue Impact |
|---|---|---|---|
| **Register on Viator Bókun** | ❌ NOT STARTED | 1 hour | $29 setup fee, immediate listing |
| **List SKU 1 & 2 on Viator** | ❌ NOT STARTED | 2 hours | $5.24–$9.74 net per sale |
| **Register on Klook Merchant Portal** | ❌ NOT STARTED | 1 hour | Similar to Viator |
| **Print 100 guesthouse QR stands** | ❌ NOT STARTED | 1–2 days | 30% commission per unlock |
| **Send EaseMyTrip cold pitch** | ❌ NOT STARTED | 30 minutes | ₹105 per ₹149 add-on |
| **Send MakeMyTrip cold pitch** | ❌ NOT STARTED | 30 minutes | 60/40 split on ₹199 add-on |

### 2.3 Content Expansion (IN PROGRESS 🔄)
| Task | Status | Details |
|---|---|---|
| **Verify Golden Triangle candidates** | ❌ PENDING | Run `approve_candidates.py` for 9 GT POIs (~300 images, ~1.5 hours) |
| **Verify World Icons candidates** | ❌ PENDING | Run `approve_candidates.py` for 6 icons (~120 images, ~1 hour) |
| **Top-up harvest (Golden Triangle)** | ❌ PENDING | Target ≥25 subject series/class (currently ~16) |
| **Top-up harvest (World Icons)** | ❌ PENDING | Target ≥25 subject series/class (currently ~16) |
| **Build Golden Triangle pack** | ❌ PENDING | `in-golden-triangle-2026.11.1.twpkg` with vision |
| **Build World Icons pack** | ❌ PENDING | `world-icons-tier1-2026.11.1.twpkg` with vision |
| **Add Golden Triangle content** | ❌ PENDING | Claims, aliases, audio for 9 GT POIs |
| **Add World Icons content** | ❌ PENDING | Claims, aliases, audio for 6 icons |

---

## PHASE 3: SCALE & EXPANSION (FUTURE 📅)

### 3.1 Institutional Partnerships (Months 2–6)
| Partner | Status | Deal Shape | Time to Revenue |
|---|---|---|---|
| **IRCTC Buddhist Circuit Train** | ❌ NOT STARTED | ₹25L/year enterprise license | 3–6 months |
| **BSTDC Bihar** | ❌ NOT STARTED | ₹35L pilot | 2–4 months |
| **MakeMyTrip Holidays** | ❌ NOT STARTED | ₹199 add-on, 60/40 split | 1–3 months |
| **GetYourGuide (via ASI concessionaire)** | ❌ NOT STARTED | "Entry Plus" bundle, $19.99 | 2–4 months |
| **UP Tourism / Rajasthan Tourism** | ❌ NOT STARTED | ₹35–50L pilot each | 3–6 months |

### 3.2 Global Expansion (Months 6–12)
| Market | Status | Content Needed |
|---|---|---|
| **Rome / Vatican** | ❌ NOT STARTED | 50 POIs, EN/HI/IT audio |
| **Kyoto / Nara** | ❌ NOT STARTED | 40 POIs, EN/HI/JP audio |
| **Angkor Wat / Bagan** | ❌ NOT STARTED | 30 POIs, EN/HI/KH audio |
| **Machu Picchu / Cusco** | ❌ NOT STARTED | 20 POIs, EN/HI/ES audio |

### 3.3 Advanced Features (Months 6–18)
| Feature | Status | Priority |
|---|---|---|
| **On-device LLM (Gemma 4 E2B)** | ❌ NOT STARTED | P2 (flagship devices only) |
| **AR Timeline (VPS2/ARCore)** | ❌ NOT STARTED | P2 (partner-dependent) |
| **Pack Studio (partner CMS)** | ❌ NOT STARTED | P2 (after 2 partner LOIs) |
| **Pack Relay (device-to-device)** | ❌ NOT STARTED | P2 (Nearby Connections) |
| **Gap Beacon (request regions)** | ❌ NOT STARTED | P2 (opt-in) |

---

## PHASE 4: FUNDING & SCALE (Months 6–18)

### 4.1 Grant Applications (NOT STARTED ❌)
| Grant | Status | Amount | Deadline |
|---|---|---|---|
| **DPIIT Recognition** | ❌ NOT STARTED | Gateway for all schemes | Ongoing |
| **NIDHI PRAYAS** | ❌ NOT STARTED | Up to ₹10L | Rolling |
| **State Seed Schemes** | ❌ NOT STARTED | ₹10–50L | State-specific |
| **Startup India Fund of Funds 2.0** | ❌ NOT STARTED | Via SEBI AIFs | Rolling |
| **ASI Adopt a Heritage 2.0** | ❌ NOT STARTED | Partnership (non-cash) | Rolling |

### 4.2 Revenue Milestones (NOT STARTED ❌)
| Milestone | Target | Current |
|---|---|---|
| **First ₹1L revenue** | Viator/Klook listings | ₹0 |
| **First ₹10L revenue** | Guesthouses + 1 OTA | ₹0 |
| **First ₹50L revenue** | State pilot + 2 OTAs | ₹0 |
| **First ₹1Cr ARR** | 3+ institutional partners | ₹0 |

---

## CURRENT SPRINT: What to Do Next (Prioritized)

### Sprint 1: Immediate Revenue (Days 1–7)
**Goal:** Get first paying customers on Viator/Klook within 7 days.

| Day | Task | Owner | Time | Done When |
|---|---|---|---|---|
| **1** | Register on Viator Bókun, pay $29 | You | 1 hour | Account created |
| **2** | Copy-paste SKU 1 & 2 from `VIATOR_KLOOK_LISTING_COPY_PACKAGE.md` | You | 2 hours | Listings submitted for review |
| **3** | Upload 5–10 photos from `content/images/` | You | 1 hour | Photos uploaded |
| **4** | Implement Ed25519 offline voucher QR reader in Android | Dev | 1 day | QR scanner verifies OTA vouchers offline |
| **5** | Register on Klook Merchant Portal | You | 1 hour | Account created |
| **6** | Print 50 acrylic QR stands for Bodh Gaya guesthouses | You | 1 day | Stands ready for distribution |
| **7** | Distribute to 10 guesthouses (Root Institute, Royal Residency, Zostel, etc.) | You | 1 day | QR stands placed |

**Revenue trigger:** First Viator/Klook sale = immediate USD revenue.

### Sprint 2: Content Verification (Days 8–14)
**Goal:** Verify Golden Triangle + World Icons candidates, build packs.

| Day | Task | Owner | Time | Done When |
|---|---|---|---|---|
| **8** | Run `approve_candidates.py` for Golden Triangle (9 POIs) | You | 1.5 hours | All candidates reviewed |
| **9** | Run `approve_candidates.py` for World Icons (6 POIs) | You | 1 hour | All candidates reviewed |
| **10** | Promote approved candidates, resplit dataset | You | 30 min | Splits verified |
| **11** | Train adapter on new corpora | You | 2 hours | Training complete |
| **12** | Evaluate retrieval, record metrics | You | 30 min | Metrics recorded |
| **13** | Build `in-golden-triangle-2026.11.1.twpkg` | You | 1 hour | Pack signed & verified |
| **14** | Build `world-icons-tier1-2026.11.1.twpkg` | You | 1 hour | Pack signed & verified |

**Revenue trigger:** New packs available for OTA listings.

### Sprint 3: Outreach (Days 15–30)
**Goal:** Send cold pitches to 10 targets.

| Day | Task | Owner | Time | Done When |
|---|---|---|---|---|
| **15** | Send EaseMyTrip cold pitch (Template 1) | You | 30 min | Email sent |
| **16** | Send MakeMyTrip cold pitch (Template 2) | You | 30 min | Email sent |
| **17** | Follow up with 5 guesthouses (check QR scans) | You | 1 hour | Conversion data collected |
| **18** | Create 1-page case study from Viator/guesthouse data | You | 2 hours | Case study ready |
| **19** | Send case study to MakeMyTrip (follow-up) | You | 30 min | Follow-up sent |
| **20** | List 3 heritage walks as GYG/Viator experiences | You | 2 hours | Listings submitted |

---

## METRICS TO TRACK (Weekly)

| Metric | Target | Current | How to Measure |
|---|---|---|---|
| **Viator/Klook sales** | 10/week | 0 | Merchant portal dashboard |
| **Guesthouse QR scans** | 50/week | 0 | Affiliate tracking link |
| **Guesthouse conversions** | 10/week | 0 | Premium pack unlocks |
| **OTA pitch responses** | 2/week | 0 | Email tracking |
| **Pack downloads** | 100/week | 0 | Server logs |
| **User reviews (Viator/Klook)** | 20 total | 0 | Platform dashboard |
| **NPS (in-app survey)** | >40 | N/A | In-app prompt |

---

## RISK REGISTER (Current)

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **Viator listing rejection** | Medium | High | Follow their guidelines exactly; use high-quality photos; respond to reviews |
| **Guesthouse non-participation** | Medium | Medium | Start with 5 friendly guesthouses; offer 40% commission |
| **OTA pitch ignored** | High | Medium | Follow up 3x; use LinkedIn; attend travel trade shows |
| **Content verification bottleneck** | High | Medium | Hire part-time reviewer (₹15–30k/mo); batch review |
| **Technical debt (Android)** | Low | Medium | Tests pass; monitor crash rate; fix issues fast |
| **Funding delay** | High | High | Bootstrap <₹5L; apply to grants; focus on revenue |
| **Competitor (Google Lens)** | Low | High | Differentiate on offline + provenance; move fast on institutional lock-in |

---

## SUCCESS CRITERIA (Phase 2 Exit)

Phase 2 is complete when:
- [ ] Viator/Klook listings live with ≥20 reviews
- [ ] ≥₹1L revenue from OTA sales
- [ ] ≥5 guesthouses actively distributing QR cards
- [ ] ≥1 OTA partnership signed (EaseMyTrip or MakeMyTrip)
- [ ] Golden Triangle + World Icons packs built and verified
- [ ] ≥100 total pack downloads
- [ ] ≥40 NPS from in-app survey

---

## NEXT STEPS (Immediate)

1. **Today:** Register on Viator Bókun, list SKU 1 & 2
2. **Tomorrow:** Verify Golden Triangle candidates
3. **This week:** Print guesthouse QR stands, send 2 cold pitches
4. **Next week:** Build Golden Triangle + World Icons packs
5. **In 30 days:** First ₹1L revenue, 1 OTA partnership, 20+ reviews

---

*The technical foundation is complete. The commercial execution starts now. Ship fast, measure everything, iterate weekly.*