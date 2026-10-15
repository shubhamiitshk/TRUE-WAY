---
title: "TrueWay — Final Feature Strategy & Execution Plan"
subtitle: "Decision-controlled revision to TrueWay Master Blueprint v2.0"
version: "3.0 — Founder decision edition"
date: "2026-10-12"
status: "Proposed build decision; conditional on research, permissions and field gates"
initial_market: "Bodh Gaya–Rajgir–Nalanda, Bihar, India"
source_documents:
  - "TrueWay_FINAL_Master_Blueprint_2026(1).md — v2.0"
  - "Pasted text(3).txt — Deep Evaluation: TrueWay Extra Features"
---

# TRUEWAY — FINAL FEATURE STRATEGY & EXECUTION PLAN

**Capture. Discover. Understand. Anywhere.**  
**Proposed positioning:** *An offline heritage companion that identifies supported places and brings their verified stories to life.*

> **FINAL PRODUCT DECISION** — Build the **trusted offline discovery core** first, then an **audio-led heritage experience layer**. Treat rich AI, radio peer distribution, AR and partner tooling as hypotheses, not mandatory product features. Preserve source transparency, unknown/abstain behaviour, visitor rights, user privacy and site restrictions across every release.

**Reading convention:** **[B]** = derived from the 10 October 2026 master blueprint; **[R]** = suggestion from supplied Deep Evaluation; **[D]** = final proposed design choice; **[A]** = an unverified target/assumption; **[G]** = blocking release gate; **[X]** = external primary-source support (linked in section 17). Neither the original blueprint nor this decision document represents an implemented/validated application.

**Document precedence:** This v3 feature decision **supersedes the conflicting scope, relative priorities and corresponding timing statements** in v2.0, especially §§2.2, 5.3–5.5, 6.7, 14 (voice/assistant priority), 23.2–23.4, 24 (P1 epics), 26 (P1 gate) and 30.3. The remaining v2.0 architecture, data contracts, source policy, privacy/security, historic content procedures and test suite remain engineering reference requirements unless explicitly amended here. Preserve both files for traceability.

---

## 1. Decision in one page

### Product definition

TrueWay is **not** universal AI visual search, a booking service, a generic maps replacement or a generative history chatbot. It is an offline, curated and verifiable way to find heritage sites and understand them in permitted contexts. Its promise starts **after the relevant pack and required models have been successfully installed**.

**Pillar 1 — Discover (P0):** photo-based supported landmark matching, manual/alias search, nearby/list/map as installed, authenticated local QR lookup, and a visible *unknown* outcome.

**Pillar 2 — Trust (P0):** claim-level evidence, bibliography, published/reviewed dates, tradition versus scholarly interpretation, media rights, site restrictions and pack changes.

**Pillar 3 — Experience (P1):** reviewed offline audio, curated walks, visual then-and-now comparisons, local heritage passport and explicit sharing/export.

**Pillar 4 — Extend (P2/research):** radio-based pack relay, voice input after user evidence, venue integrations, rich scholar tooling, optional local LLM demonstrations and research AR/BLE.

### Five decisions that settle the reviews

1. **Keep the complete P0 contract** (15 existing F001–F015 features), with P0.5 hardening. Do not trade trust/security for splashy audio. [B/D]
2. **Audio is the leading P1 investment**, but **not** a prerequisite for a viable P0 pilot. Pre-render source-reviewed English/Hindi clips when rights permit, with matching transcripts and caption-equivalent text. [R/D]
3. **Curated, authored content beats unbounded generation in the initial release.** Store claim-linked FAQs as reviewed records; answer unsupported questions with a clear limitation. Move production on-device LLM and ASR **out of the near-term committed roadmap**, not out of the research backlog forever. [R/D]
4. **Merge related feature tracks** to reduce coordination: route+terrain; audio+pronunciation+playlist; share+export; scholar lens+architectural annotations. [R/D]
5. **Make site compliance a product interaction.** A “Before You Enter” experience belongs in P0.5; it is used outside sites/areas where electronics are prohibited and never instructs visitors to use a device inside the prohibited zone. [R/D/G]

### Default go/no-go

**GO** on a 15-supported-landmark technical demonstrator → conditional 50–70-POI source-backed Bihar pilot. **NO GO** on mandatory large language models, global landmark ID, unlicensed historical photography, live traffic/weather/hours from static packs, AR reconstruction described as archaeological truth, forced login, always-on listening or hidden media upload.

---

## 2. Assessment of the second AI review — accept, correct, reject

| Review assertion | Decision | Necessary correction |
|---|---|---|
| Audio should organize P1 | **Accept** | Audio is a priority **after** P0; user demand and paid conversion are hypotheses, not established Bihar results. |
| Pre-rendered media avoids inconsistent phone TTS | **Accept as preferred P1 implementation** | Server rendering, narration/editorial quality, language review, vendor voice rights, distribution size and withdrawal must be managed. |
| Voice OUTPUT is more valuable than voice INPUT | **Accept for initial sequencing** | Claims that voice input presumes literacy are not generally true: combined voice input **and** spoken output may help accessibility. Re-test if field interviews identify this need. |
| Extractive FAQ answers effectively every realistic question with zero hallucination | **Reject the absolute claim; accept the architecture choice** | Curated FAQ has bounded coverage and can still present erroneous or stale source material. It must provide coverage limits, source citations and an “answer not available” route. |
| Local LLM should be cut from the actual initial product | **Accept** | Keep only research/optional non-blocking demo; do not make a multi-GB model, continuous assistant or LLM dependence an install requirement. |
| Then & Now slider is trivial to build | **Partially accept** | Slider UI is small; perspective pairing, factual captions, conservation context and item-level commercial rights are substantial work. |
| International visitor nationalities are dominant and imply exact language order | **Unverified** | Pilot **English/Hindi** per v2.0. Choose further languages from actual field interviews, tourism audience evidence, partner requests and content rights—not an unsupported ranking. |
| Heritage Passport is nearly free with no ML | **Accept relative simplicity** | Avoid pretending a self-recorded stamp is a verified physical visit. Local DB, UX, accessibility, privacy and correct labels still require testing. |
| Curated terrain notes are low-risk safety guidance | **Accept with gate** | Mark as dated information; not live heat/weather/hazard assessment or certified route safety. |
| Share cards inherently create WhatsApp virality | **Treat as hypothesis** | The user chooses whether and where to share; no automatic private journal, precise location, third-party app or unlicensed media inclusion. |
| Pack Relay should move to P2 | **Accept as default** | Fast-track if 15–25 interviews and field logs demonstrate inability to obtain downloads and repeated genuine group-sharing need. Radios and app permissions still required. |
| Gap Beacon should be cut | **Accept from immediate scope** | Anonymous demand signals are not a launch blocker; optional consent-based feature after a real prioritization process exists. |
| Partner CMS needs six months of use | **Accept principle, reject fixed time as gate** | Build institutional Pack Studio only after multiple actual controlled editorial/release cycles, rights audits and demonstrated partner commitment. |
| All P1 items have “zero trust risk” | **Reject** | Provenance, narration errors, mobile sharing, route claims and image licences all generate risks; require feature-specific release gates. |

### Strategic nuance

The most valuable differentiation is **a reusable, evidence-aware heritage content pipeline**, not audio *alone*. Audio extends the same claims; routes combine the same place IDs; then-and-now depends on rights-cleared assets; source-backed share cards distribute trust. This makes the long-term product more defensible than a one-off audio app or a flashy camera demo.

---

## 3. Final authoritative priority structure

### P0 — Must ship for a meaningful private field pilot

Keep **F001–F015** from v2.0:

| Epic | Committed functions | Why mandatory |
|---|---|---|
| OFFLINE | Region onboarding; signed, validated install/update/rollback/delete; component manifest; changelog; readiness indicator | Offline is the user promise, not a marketing label. |
| FIND | Camera single-shot for supported classes, top candidates, conservative abstention; text/categorical/alias search; offline nearby/list; optional GPS | Does not fail when scan is unavailable or uncertain. |
| EXPLAIN | Human-reviewed history/architecture/timeline; source links locally inspectable; FACT / INTERPRETATION / TRADITION / CONTESTED labelling | The epistemic differentiator. |
| RESPECT | Device/site restrictions, last-checked operational advice, offline emergency *reference* strip with connectivity warning | Prevents inappropriate or false-safety claims. |
| KEEP | Local private bookmarks/journal, export/deletion readiness, no account; source-aware QR resolver (without partner plate rollout) | Basic return and deterministic access. |
| PERFORM | Battery-conscious capture, graceful degradation, error states, accessibility and Hindi/English content | Works on actual target devices. |

**Boundary:** 50–70 pilot POIs are **content records**, not 50–70 independently recognizable camera classes. Mark each as `PHOTO_SUPPORTED`, `SEARCH_ONLY`, `TEXT_REFERENCE_ONLY`, `TRAIL_STOP` and/or authorised `QR_PARTNER`. Begin the visual study with **15 clearly defined and lawful scan targets**. [B/D]

### P0.5 — Must harden before any public beta

1. **Before You Enter:** pre-visit summary, prohibited-item/device etiquette, offline saved story, text first; optional downloadable audio only when P1 media exists. Make the permitted-use boundary explicit.
2. **Transliteration and multilingual search polish:** Hindi names in Devanagari and Roman aliases, common spelling variants, icon-based categories, offline fuzzy/ranked search where tested. Important: this is a SEARCH improvement, not a new speech pipeline.
3. **Truly ready offline badge:** explicit per-layer check (content, images, vision model, map, media/language) with dry-run support; no runtime surprise download.
4. **Reliability/security:** corrupt archive rejection, key rotation/revocation strategy, rollback, low-storage behavior, no unexpected egress and device-resource regression.
5. **Operational provenance:** last-checked dates, where official current on-site notices supersede downloaded guidance, accessibility/legal/rights review.

### P1A — Five experience epics, *conditionally sequenced*, not all required for P0

| Order | Unified epic | Included original IDs | Smallest legitimate slice | Primary release gate |
|---:|---|---|---|---|
| 1 | **AUDIO STORY** | F101 + F110 + manual F106 | 1–3 minute pre-rendered Hindi/English reviewed clips for 10 flagship POIs, text transcript, play/pause/seek, pronunciation where verified; manual stop playlist | Accurate content and captions; media licence; offline playback, accessible controls and device/storage tests |
| 2 | **CURATED WALKS** | F105 + F112 | 2–3 authored routes with selectable stops, duration **estimates labelled as estimates**, route/terrain/heat caveats and last-checked date; no algorithmic route optimizer | Route validation, on-site permissions, permitted paths, mobility caveats, no “live safety” implication |
| 3 | **HERITAGE PASSPORT** | F107 | Private, offline place collection with self-recorded visits, optional commemorative stamps, no GPS proof requirement | Never imply official accreditation, authenticated attendance or mandatory tracking |
| 4 | **THEN & NOW** | F108 | 3 rigorously rights-cleared and context-matched image pairs first; target 5–10 only if cleared; creator, dates, uncertainty and alignment caveat visible | Item-level image rights, accurate location/time descriptions, source/editor signoff |
| 5 | **SHARE & EXPORT** | F114 + F117 | One tap to select a **public, licensed place card** and separately export selected **private journal entries** as JSON/PDF; no implicit GPS or EXIF | Explicit selection, legal media reuse, clean offline export, downstream privacy warning |

**Sequencing rule:** One epic may be incomplete or removed from a release while the other qualifying epics ship. In particular, inability to clear archival image rights must **not** delay P0 or the audio/walk experience. This is a priority order for staffing, not a guarantee of completion dates. [D/G]

### P1B — Later refinements after observed user need

| Epic | Original IDs | Scope and limits | Why not Wave 1 |
|---|---|---|---|
| **Modern-sign OCR** | F103 | Optional offline Devanagari/Latin text extraction, correction UI, original source visible; translation only with available reviewed/preinstalled language assets | Adds camera and script QA; helps at permitted signs only; cannot decipher ancient epigraphy |
| **Audience lenses / Scholar annotations** | F109 + F104 | Start with two reviewed variants (family and scholar) and annotated diagrams for ~10 POIs; retain canonical claims/IDs | Editorial capacity, translation quality and content reuse need proof |
| **Study Lite** | F116 | Claim-linked quizzes and chronology cards for pilot education partner | Schools/academic demand is not yet validated |
| **Location-aware playback** | remaining F106 | Optional foreground guided-walk triggers, never background tracking without explicit consent; easy manual playback | Battery, GNSS reliability, accessibility and venue-use constraints |
| **Partner QR installation** | F014 extension | Authorized, maintained signed plates with serial/site register; permitted device use only | Requires explicit permissions, physical audit and operations owner |

### P2 — Conditioned research / partner platform

- **Pack Relay (F111):** controlled devices/permissions, signed receiver-side validation; only after evidence of distribution bottleneck and measured mixed-phone usability.
- **Push-to-talk Hindi/Hinglish queries (F102):** revisit if visitor interviews identify low-literacy accessibility needs not met by icon browsing + spoken output. Transcript is editable and reply may be spoken; measure noisy field recognition on target handsets. No always-on capture.
- **Opt-in Gap Beacon (F115):** publish a privacy and consent design only once capacity to act on requests exists.
- **Commercial Pack Studio, community media/guide voices, institutional dashboards:** partner-authorisation, commercial rights, moderation, revocation and repeatable in-house editorial process are prerequisites.
- **AR historical reconstruction, BLE museum positioning, advanced epigraphy OCR, SfM/relocalisation, scholar comparison, international marketplace:** independent research/rights/venue/device gates.
- **Local generative QA (F113):** **non-production research sandbox by default**, never a product dependency. Future promotion requires an observed unsolved user need, on-device resource/thermal fit, measurable retrieval/evidence quality and audited abstention; static FAQs remain functional without it.

### Explicit exclusions for all initial releases

No global arbitrary-building recognizer, AI-created history presented as fact, mandatory multi-GB LLM, scraped restricted map tiles, unapproved photographic capture, guaranteed indoor route precision, live status from static downloads, automatic audio/photo uploads, guaranteed emergency response, compulsory accounts, persistent microphone or location tracking, open user-content feed or forced viral/share loops.

---

## 4. Final ranked list — the actual top ten *after* P0

| Rank | Feature | Release slot | Concrete output |
|---:|---|---|---|
| 1 | Reviewed offline audio + pronunciation | P1A | 10 POI clips in Hindi/English, scripts and locally playable files |
| 2 | Authored heritage walks + dated trail notes | P1A | 2–3 offline stop lists with practical constraints |
| 3 | Private Heritage Passport | P1A | Personal stamps and saved history, clearly non-official |
| 4 | Then & Now | P1A rights-gated | 3 first, expand to 5–10 approved historic/current pairs |
| 5 | Explicit public share cards + private journal exports | P1A | Shareable licensed fact card; separate selected PDF/JSON export |
| 6 | Modern signboard OCR | P1B | Optional Devanagari/Latin recognition; offline model present |
| 7 | Family/scholar lenses with curated architecture annotations | P1B | 10 POIs, two authored content variants |
| 8 | Educational Study Lite | P1B conditional | Quizzes linked to citations if academic partner exists |
| 9 | Pack Relay | P2 conditional | Tested offline transfer via radios, with signature verification |
| 10 | Voice input and advanced assistant research | P2 research | Controlled low-vision/language experiment, no production promise |

**Important:** *Before You Enter, transliteration, icon/category browse, safe QR resolver, low-power scan and pack changelog are P0/P0.5*, so they should not be misleadingly ranked as optional P1 extras.

---

## 5. The complete customer experience

### A. Ordinary permitted outdoor discovery

```
Choose Bihar circuit → download verified region pack → see OFFLINE READY
    ↓
Explore (name/alias/category) ─ OR ─ Scan (if camera permitted) ─ OR ─ QR (if authorized)
    ↓
Recognized candidate / manual selected place / explicit UNKNOWN
    ↓
Source-backed overview → Architecture / Timeline / Tradition / References
    ↓
P1 when installed: listen → next curated stop → personal passport → licensed share card
```

If camera matching cannot confidently identify a supported POI, say **“No reliable match in your downloaded places.”** Suggest an offline search or nearest listed POIs without falsely implying visual recognition.

### B. Mahabodhi or another restricted-device context

```
Outside restricted area and only where devices are permitted
    ↓
View current official rules → Before You Enter → read/listen/save itinerary
    ↓
Put device away; comply with on-site operator instructions
    ↓
Explore saved reflections later outside restricted area
```

**No in-restricted-zone QR, scanning, narrated walking mode or electronic passport checkpoint.** Bihar Tourism currently lists mobile phones, cameras and electronic gadgets as prohibited at Mahabodhi Temple; actual entry restrictions and on-site instructions are authoritative and can change. [X1]

### C. Budget visitor with a low-end handset

Install the text-first Lite pack, search in Hindi/Romanized Hindi, use category icons, read or listen to an optional preinstalled brief audio clip, see static source-linked facts, save visits locally. No high-end AI accelerator, paid content or large audio/language models required to understand the core facts. If media missing, display the transcript/text, not a disabled mystery button.

### D. Student and architectural fieldwork

Search or select a precisely defined `place_id`, read claims and chronology, see annotated architectural elements when Scholar lens exists, inspect citations, save original notes and export selected fieldwork. Never claim that a generic image recognizer has established a period or construction technology from visual style alone.

### E. Group leader

Until Pack Relay passes a dedicated gate, provide straightforward download instructions, visible pack size, QR/safe installation link information when connected, and a human-readable region pack name. Never market radio-free peer transfer.

---

## 6. Proposed app navigation and page-level requirements

**Bottom navigation:** **Explore · Scan · Saved · Downloads**. No permanent Ask/AI tab unless a supported, independently validated answering mode is installed and its limitations are visible.

| Area | Release | Required state and interactions |
|---|---|---|
| **Onboarding / Destination** | P0 | Choose circuit, languages, package sizes, assets, rights/attribution summary; download and verify. |
| **Home / Explore** | P0 | Search field with Hindi/Roman aliases; categories; nearby optional; saved routes when available; offline-ready/status strip. |
| **Scan** | P0 | Site rule gate; permission request in context; single shot; optional blur hint; candidates vs unknown; manual fallback; QR lookup where permitted. |
| **Place Detail** | P0 + P1 | Source-backed story, timeline, architecture, claim-type badges, local citations, last reviewed; conditional Listen/Then & Now. |
| **Before You Enter** | P0.5 | Dated official-use notice; short offline briefing; permitted-use boundary; prepared text; optional audio only outside restricted area. |
| **Walks** | P1A | Authored named trails, stops, static route/mobility notes, estimated time caveat, manual audio playlist. |
| **Passport / Saved** | P0 + P1A | Bookmarks, private notes and optional user-created stamp; private data never mixed into a public verified card. |
| **Share / Export** | P1A | Choose public vs private content; preview attribution and locations; choose format; open Android system share target manually. |
| **Downloads** | P0 | Verify/install/repair/update/delete; release changes, active pack, model/library readiness, size and component dependencies. |
| **Settings** | P0 | Language, text size, TalkBack support, privacy, separate deletions for packs and journal, battery/download policies, publisher/source credits. |

**Content UX invariants:** Every substantial historical assertion maps to locally retrievable claim/source IDs; operational notices have freshness dates; expired or contested claims never silently become facts; absence of optional media never blocks history; translation does not alter claim classification.

---

## 7. Recommended technical architecture (bounded, not speculative)

### On-device P0 critical path

```
Android Compose UI
    ├─ CameraX single-shot → small evaluated image encoder → local embedding similarity
    │                                   └─ calibrated ACCEPT / ABSTAIN
    ├─ FTS5 SQLite → place/alias/category search
    ├─ SQLite claims → evidence/local source viewer
    ├─ signed QR payload → trusted issuer check → local place_id
    ├─ POI list / optional predownloaded licensed map component
    ├─ local journal (separate private DB)
    └─ signed pack lifecycle → staging → validation → atomic activation
```

**No call to a backend is allowed to be necessary for a successful scan, search, history read, QR local resolution, journal read or map/list lookup after complete setup.** The backend builds, signs and distributes packages and never secretly answers heritage questions in the offline path. [B/D/G]

### P1 extension

- **Audio:** `claim_ids + language + reviewed narrative script + voice asset right + waveform + transcript + pronunciation quality checks + release date`; produce static compressed clips before publishing. No forced on-device TTS/ASR. Local playback and foreground controls.
- **Walk:** `trail_id + ordered place_ids + validated permitted pathways + segment_notes + estimated_duration_source + verified_at + mobility_limitations + seasonal_snapshot`. Offline map optional, textual stop list mandatory.
- **Then & Now:** `pair_id + historic_asset_id + current_asset_id + creator/license/rights evidence + approximate date + viewpoint correspondence + historical caption + reviewer`. Do not imply an exact georegistration unless measured.
- **Passport:** local `visit_id`, `place_id`, `saved_at`, `user_marked`, `verified_visit=false` by default. Avoid raw passive location histories.
- **Share:** generated readable place card from a public/redistributable claims/media allowlist; personal export separate and opt-in; size/provenance warnings when receiver lacks the pack.
- **FAQ:** exact authored question variants → reviewed answer/claim IDs; show citations, age and “not in this pack.” Even deterministic output is audited for misleading retrieval/claim selection.

### Distribution/security invariants

Keep the v2.0 pinned publisher keys and signature architecture: Ed25519 signing of canonical manifests, detached signatures, SHA-256 asset checks, schema and licence validation, normalized path extraction, rollback, versioned changelog. Peer relay, if eventually built, **must apply precisely the same receiver-side signature and rights verification** as internet download. A signed QR validates issuer-signed data, **not** physical placement/plate authenticity.

### Technical research choices kept open

Vision encoder, exact index type, model quantization, PMTiles packaging/MapLibre Android version, audio codec/bitrates and phone RAM/API floor must be determined by actual measured performance and licensing. No arbitrary embedding threshold, latency or archive size is presented as observed data.

---

## 8. Content, rights and editorial work — the real foundation

**For every POI:** stable place ID, canonical/local names, aliases, exact parent/child identity, whether photo recognition is lawful/sensible, sourced facts, tradition vs interpretation, architectural notes, current-source reference, last-reviewed timestamps, translation state, rights for each photo/audio asset and published notice timestamp.

**Minimum editor workflow:**

1. Research bibliography and independently trace each material historical claim to authoritative evidence.
2. Classify `DOCUMENTED`, `INTERPRETATION`, `TRADITION`, `CONTESTED`, `OPERATIONAL` and `HYPOTHESIS`; do not collapse tradition into archaeological proof.
3. Inspect media rights **per item**: creator, chain of rights, licence, commercial reproduction, required attribution and alterations.
4. Human-review Hindi/English summaries and audio scripts. Do not translate an uncertain statement into a confident one.
5. Complete site/device/use restrictions review from primary authority and record its freshness.
6. Validate pack references/claims, test source viewer offline, build/sign/verify, publish change notes.
7. Maintain corrections/withdrawal workflow. Offline-copied content cannot be centrally erased instantly; include remediation in next update and acknowledge limits.

**Then & Now gate:** Identical/similar viewpoint is a desirable **curatorial** property, not proof of a digitally exact match. Record year as approximate if uncertain; explain whether structures or restorations changed and cite sources. Do not assume “19th-century photograph = public domain.”

**Audio gate:** Review factual claims, pronunciation and rhythm, subtitle parity, volume/playback accessibility, clear identity of human/AI voices, TTS-service license and voice/performer consent. Avoid cloning voices without explicit consent. Media must be legally redistributable as pack assets.

**Trail gate:** Validate permissioned walking routes on site; disclose uneven terrain, climb/water/rest availability only when grounded, and warn that downloaded advice is not live. Never infer a route's safety from a stale DEM snapshot.

---

## 9. Evidence-first product discovery before writing more AI code

### Research plan (15–25 interviews proposed [A])

Sample domestic visitors, Hindi-first users, international pilgrims (do not assume preferred language), architecture/history students, guides and site staff. Seek representative low-end Android devices and permissioned field settings. Ask users to demonstrate their actual visit tasks, not to rate futuristic feature names.

**Questions that can change priority:**

- Do users actually have trouble reading sourced cards, and would downloadable audio fix it?
- Which segment pays for a themed audio walk, if any? Are users willing to tolerate larger download sizes?
- Do groups routinely travel without reliable pretrip Wi-Fi, and could a signed offline pack transfer materially help?
- Do permitted viewpoint restrictions prevent photo matching for most relevant sites?
- Which language(s) beyond English/Hindi are asked for, with how many requests?
- Does the learner segment want architecture annotations or only credible sources/field note export?
- What can museum/site operators authorize: references, audio, QR plates, archival image rights or none?
- Do travellers understand “self-recorded passport stamp” and “not official proof of visiting”?

**Decision triggers:** If audio is not used during field tasks, do not expand from ten flagship clips to full-circuit coverage. If users lack installation connectivity, investigate better smaller packs and distribution before committing to peer transfer. If scanner recognition fails on hard unknowns or is mostly illegal/unpermitted at key sites, emphasize search/QR and **remove camera-first marketing** until the cause is resolved.

---

## 10. Release roadmap — 24-week P0 pilot plus conditional expansion

**This is a proposed sequence, not a guarantee that staffing, licenses, permits or dataset availability exist.** The original ₹25.76-lakh staffed baseline is an **illustrative P0 pilot**, not an all-feature contract.

| Window | Priority work | Deliverable / exit criterion |
|---|---|---|
| **Weeks 1–3** | Source/right register, 15 eligible scan targets, taxonomy, Kotlin shell, source schema, device matrix, first user interviews | Reproducible permitted dataset plan; complete editorial record for demo set |
| **Weeks 4–7** | Camera baseline, positive/negative data, held-out photographer/visit splits, calibration, unknown-state UX | Open-set report, error list and actual device timing, not demo-only top-1 |
| **Weeks 8–11** | Signed packs, offline SQLite/FTS, QR resolver, changelog, lite journal, offline list and readiness | App works without internet after setup; malicious/corrupt pack rejected |
| **Weeks 12–15** | Hindi/Roman aliases, source viewer, P0.5 Before You Enter, restrictions, a11y, accessibility, rights audit, POI expansion as cleared | Edited 50–70 content records **if achievable**; 15 targets need not become 70 scan classes |
| **Weeks 16–20** | Permissioned Bihar field testing, hard negatives, low-tier device thermal, no-GPS/no-camera and user comprehension testing | Recorded pilot gate; content/support coverage and trust complaints audited |
| **Weeks 21–24** | P0 security/privacy/rights regression and conditional restricted beta | **GO** only if release gates pass; otherwise narrower beta with clear missing capability |
| **Post-P0, Wave 1** | Audio → walks → passport → rights-cleared Then & Now → share/export | Independent P1A release gates and field adoption data; no fixed date imposed |
| **Post-P1A, Wave 2** | Optional OCR; family/scholar variants; education test; triggered narration/authorized venue touchpoints | Only if measured demand and partner/rights gates justify it |
| **Research/partner track** | Relay, voice-input accessibility, generative demo, AR/BLE, Pack Studio | Separate written business case; not promised to first paying traveller |

**Scope-compression order if schedule slips:** optional map art, richer photography, P1 sample audio, achievements, then any other optional media. **Never** cut pack integrity, traceable material historical claims, lawful content, camera-ban compliance, conservative unknown behavior, manual search, privacy controls or offline core tests.

---

## 11. Acceptance gates — cannot be bypassed by product demos

### Gate 0 — Data and source legitimacy [G]

- Every published material historical claim has a locally inspectable source anchor and appropriate fact-type classification.
- Every embedded image/narration asset has documented reproduction permission appropriate for use and distribution.
- All promoted sites/recognition viewpoints have checked camera/device rules and no encouragement to violate them.
- Hindi/English content has designated editorial and linguistic reviewers.

### Gate 1 — Useful offline P0 [G]

- All scripted core flows function with **Internet unavailable and local radios off** after installs, with no unexpected external data traffic.
- Supported photo recognition, manual name/alias, verified QR, source viewer, journal and list all work offline subject to their installed prerequisites.
- Unknown/out-of-pack scenes do not become forced confident labels. If scanner quality gate fails, ship **search-first** and mark scan experimental or remove its public claim.
- On each low-end supported phone, no repeated-scan crash, runaway resource usage or unacceptable performance after a defined test.
- Signed update rejection, tamper detection, low-storage rollback and safe delete pass attack and recovery tests.

### Gate 2 — Model performance [A/G]

Use v2.0's **provisional** starting targets, not claims of present achievement: known-set Top-1 ≥85%, Top-3 ≥95%, hard unknown false-accept ≤5% (stricter where risk warrants), P50 capture-to-card <2.5 s, P95 <6 s on a specified reference phone. Evaluate by held-out visit and photographer, with failure modes published internally. Calibrate thresholds from measured examples; do not show invented user-facing percent confidence.

### Gate 3 — P1 media/content [G]

- **Audio:** full offline playback, text/transcript available, language is correct, content editor passed, permissions/rights documented, battery and media sizes measured, playback behavior accessible.
- **Walks:** all listed stops have permitted routes, verified context, last-checked notes and non-live disclaimers. Manual list works without GPS or map.
- **Passport:** stamped places are user-recorded unless independently verified; no automatic location proof or implied institutional recognition.
- **Then & Now:** both image rights independently cleared, archival dating/creator context and preservation caveats visible, no synthetic “historical truth” layering.
- **Share/export:** public card contains only distributable content; any personal data and coordinates require explicit user selection; PDF/JSON output locally correct and deletable.

### Gate 4 — Field desirability & economics [A/G]

Evaluate completion and comprehension in actual moderated trials. v2.0's ≥80% unassisted task completion is an initial planning target, not evidence. Measure audio starts/completions, route task success, repeated saves, source inspection and user-reported relevance with a privacy-preserving method. Validate hypothetical traveller prices (v2.0 proposes ₹99–299 optional circuit) and institutional fees **through observed willingness-to-pay/partner commitments**, not competitor inference.

**Hard stop:** No official approval, no licence, no allowed scan context, no acceptable false-accept control or no offline completion → do not publicly market that feature as available.

---

## 12. Product metrics and privacy-respecting experimentation

**North-star hypothesis:** successful **source-backed offline discovery sessions** per travel day. A valid discovery includes an accepted supported visual match or a user-selected/verified local place card with a meaningful history view. Never count “AI claimed to identify unknown site” as success.

**Secondary measures:** install-to-ready ratio; first useful fact; known vs unknown recognition correctness; wrong-match complaints; source clicks/understanding; search failure by aliases; audio listening with text alternative; route completion self-report; optional licensed share actions; pack repair failures; entry-tier crashes; consent withdrawals.

**Data collection rule:** by default collect **locally** for QA; no raw camera frames, precise travel paths, audio or journal export transmitted automatically. Any optional telemetry needs separate informed consent, strict minimization/retention and a verified legal basis. Offline-first does not justify concealed tracking or a promise of formal anonymity without a privacy analysis.

---

## 13. Business model — hypotheses, not proven revenue

### Free foundation [D]

Keep installation of a basic destination pack, text-first canonical facts, source inspection, manual lookup, conservative camera use where supported and essential accessibility settings available without compulsory payment/account. The trusted core creates adoption and avoids putting historical truth behind a paywall.

### Optional paid traveller experiences [A]

Test **professionally edited premium narrated circuits** or richer thematic media after content and payment demand evidence. The earlier draft's **₹99–299 per enhanced circuit** is a test hypothesis, not a validated price. Avoid charging for basic source notes, emergency reference details, uncertainty disclaimers or critical site restrictions.

### Institution-first opportunities [A]

Investigate commissioned, rights-cleared guided circuits, permitted QR touchpoints, audited multilingual interpretation and eventually rights-controlled content publishing. Do not promise B2B revenue because tourist footfall is high. Require a named buying authority, content/licence responsibility, maintenance schedule, measurable benefit and real pilot agreement.

### Revenue risks

High-quality bilingual audio and archival photo rights are **not free content**. Per-POI editorial labor, narration rights, future corrections, new languages and update egress may dominate startup economics. Build a cost-per-cleared-POI and per-minute-of-approved-audio ledger before promising the number of paying circuits.

---

## 14. Budget and resource focus

The existing v2.0 estimate provides an **illustrative ₹25.76 lakh / 24-week staffed pilot**, using ₹22.40 lakh cost subtotal plus 15% contingency. It should **not** be labeled an observed quote or a guarantee of a 50–70 POI published app. The founder/demo band in v2.0 of **₹1.5–5 lakh plus unpaid time** is likewise a planning scenario.

**Suggested scarce-resources allocation order (not percentages or purchase orders):**

1. Evidence/rights/editorial and permitted image corpus.
2. Android offline stack + signing/recovery and test devices.
3. Reliable recognition/open-set testing and manual fallback.
4. User research/field permissions and multilingual quality.
5. After P0 success, low-risk narrated content and routes; budget narration and archival licences separately.

Reforecast after the 15-target feasibility gate. Collect at least one source-specific content acquisition quote, one user audio demand signal and actual phone benchmarks **before** making the full P1A investment decision.

---

## 15. Changes to make in the existing v2.0 backlog (editorial patch map)

| v2.0 location | Required v3 correction |
|---|---|
| §2.2 Integration decisions | Audio P1 leading; voice-input P2 conditional; production local LLM P2 research; relay P2 conditional; gap P2; Then & Now early rights-gated. |
| §5.1 P0 | **Retain F001–F015** unchanged in substance. |
| §5.2 P0.5 | Add *Before You Enter* and strong Hindi/Roman name/alias search with category icons. |
| §5.3 P1 | Reorganize into five **P1A** epics and smaller **P1B** refinements; keep original IDs as cross-reference. |
| §5.4 P2 | Move F102/F111/F113/F115 to conditional experiments; keep AR/BLE/Pack Studio/community gated. |
| §6.7 Screens | Add Before You Enter, walks/audio playlist, passport, explicit share/export; Ask hidden unless justified and installed. |
| §14 Assistant | Curated text/FAQ primary; local model not production commitment; pre-rendered reviewed narration preferred; Hindi ASR experimental. |
| §21 Budget | Note P0 baseline does not fund guaranteed P1A. Add narration/rights cost ledger and separate estimates only after pilot. |
| §22 Business | Mark audio monetization as demand hypothesis; avoid promising “proven in exact Bihar market.” |
| §23 Delivery | 24 weeks reserved for P0/P0.5 conditional beta; P1A after core gate or on non-blocking isolated branch. |
| §24 Epics | Merge `TRAIL+TERRAIN`, `AUDIO+PRONUNCIATION+PLAYLIST`, `SHARE+EXPORT`, `SCHOLAR+DETECTIVE`; voice and relay research-only. |
| §§26/29 Gates | Introduce P1 item-specific rights/narration/trail/passport/share tests; separate radio-off vs peer-radio-on conditions. |
| §30 Priorities | Replace earlier post-core order with P1A/P1B/P2 ladder in this document. |
| Final one-page handoff | Use Section 1's decision and Section 16's signed-off release commitments. |

**Existing P0 contract reference:** F001–F015 should continue to use v2.0's machine-readable pack/QR/SQL/security examples and original acceptance IDs. This file is a **scope and execution decision**, not a replacement for the technical schemas or legal review.

---

## 16. Practical next actions / final sign-off

### First 14 days (founder build sprint)

- **Days 1–2:** Freeze the exact 15 demo site identities and the `PHOTO_SUPPORTED` versus `SEARCH_ONLY` distinction; set up Kotlin/Compose and content schema.
- **Days 3–4:** Populate 10 source-backed records with EN/HI aliases, fact-type fields, source links and rights metadata; exercise search with camera denied.
- **Days 5–6:** Obtain only permitted, rights-tracked images; plan hard unknown/lookalike test set; identify restricted use contexts.
- **Days 7–8:** Run baseline retrieval/abstention experiment with photographer/visit separation; record accepted errors, not only accuracy.
- **Days 9–10:** Port a candidate model to intended Android handset; record actual memory, time, battery/thermal conditions and app shutdown behavior.
- **Days 11–12:** Implement signed-pack fixture and QR resolver; load claims/citations with all network access disabled; tamper-test archive.
- **Days 13–14:** Conduct a small moderated task test, including “no-camera” and “Before You Enter”; decide next gate from observed failures.

### Release contract to the team

**Must work without network:** search, supported scan where permitted, correct uncertainty, local references, downloaded place and trail records, QR lookup, private saves and pack repair behavior, with required assets already installed.

**Must never be fabricated:** a recognition identity; a scholarly citation; a photo licence; site operating status; time-to-destination; safe indoor route; location precision; emergency-service connectivity; audio/visitor adoption; or a partner agreement.

**Not in the critical release path:** voice-input model, generative LLM, AR, BLE, global image recognition, peer relay and public submissions.

### Final recommendation

> **Ship the smallest trustworthy offline heritage companion; make its first expansion an exceptional *listening and walking* experience; use rights-cleared historic comparisons, visitor memory and safe share cards as support. Build heavy AI and institutional platform tools only after someone has clearly demonstrated the need and the gates can be met.**

**Status:** Final proposed feature and sequencing decision **for founder sign-off**. Target numbers and market claims require field validation. No app, training dataset, content licence, device benchmark or partner permit is implied to exist merely because it appears in this plan.

---

## 17. External verification links (primary-source support for factual gates)

The supplied master blueprint's source index remains the broader bibliography. These links are additional direct checks for consequential points, accessed/reviewed 12 October 2026:

1. **[X1] Bihar Tourism — Mahabodhi Temple.** Current published visitor information lists mobile phones, cameras and electronic gadgets as prohibited. This supports *Before You Enter*; check newer local signage/official orders: <https://tourism.bihar.gov.in/en/destinations/gaya/mahabodhi-temple>.
2. **[X2] Google ML Kit — Text Recognition v2.** Latin and Devanagari are supported, which does **not** establish ancient inscription reading accuracy: <https://developers.google.com/ml-kit/vision/text-recognition/v2>.
3. **[X3] Google ML Kit Android text recognition install choices.** Bundled and unbundled models have different offline-readiness implications: <https://developers.google.com/ml-kit/vision/text-recognition/v2/android>.
4. **[X4] Google Nearby Connections Android.** Peer data transfer can work without Internet, but device radios, permissions and user acceptance are required: <https://developers.google.com/nearby/connections/android/get-started>.
5. **[X5] VoiceMap official help.** Downloaded audio tours work offline; this validates *technical and category viability*, not TrueWay's own potential market share or paid conversion in Bihar: <https://support.voicemap.me/can-i-use-voicemap-offline/>.

*Research integrity note:* No external claim has been inferred merely from another AI's confident tone. Evidence-backed platform/site facts, proposed product choices, sample budgets, market hypotheses and tested benchmarks have been separated throughout.

**END — TrueWay Final Feature Strategy & Execution Plan v3.0**
