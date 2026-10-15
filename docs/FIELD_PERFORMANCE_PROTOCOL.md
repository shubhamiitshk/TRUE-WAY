# Field Performance Protocol — TrueWay v3.0

**Date:** 2026-10-13  
**Purpose:** Define the field testing protocol required before public beta approval

## Overview

The audit identified that no instrumented Android tests, live-camera measurements, or device testing evidence exist. This document defines the field performance protocol that must be completed before the public beta can be approved.

---

## 1. Camera Recognition Benchmarks (Gate 2)

### 1.1 Test Dataset

| Requirement | Minimum | Target |
|---|---|---|
| Supported landmarks (PHOTO_SUPPORTED) | 15 | 15+ |
| Diverse hard negatives | 100 | 150+ |
| Photographers (distinct) | 5 | 8+ |
| Visit sessions (distinct days/times) | 10 | 15+ |
| Viewpoints per landmark | 3 | 5+ |

### 1.2 Capture Protocol

For each supported landmark:
1. Capture from **3+ distinct viewpoints** (front, side, detail, wide)
2. Capture at **3+ lighting conditions** (morning, midday, afternoon/shade)
3. Include **10+ hard negatives** per session (other monuments, signs, trees, people, animals)
4. Each photo taken by a **different photographer** where possible
5. Record GPS coordinates, timestamp, and device model for each capture

### 1.3 Performance Metrics

| Metric | Gate | Measurement |
|---|---|---|
| Top-1 accuracy | ≥85% | Correct place identified as top result |
| Top-3 accuracy | ≥95% | Correct place in top 3 results |
| False Accept Rate (FAR) | ≤5% | Unsupported place incorrectly accepted |
| P50 latency | <2.5s | Median time from capture to result |
| P95 latency | <6.0s | 95th percentile time from capture to result |
| Abstention rate | ≤30% | Percentage of queries that abstain |

### 1.4 Statistical Rigor

- **Clopper-Pearson 95% upper confidence bound** must be ≤5% for FAR
- With 100 independent negatives: 0 errors → 2.95% upper bound; 1 error → 4.66%; 2 errors → 6.16% (FAILS)
- Results must be reported with confidence intervals, not just point estimates
- The calibration split must be held out from training

### 1.5 Test Environment

- **Airplane mode** for all offline testing
- **Radios off**: mobile data, Wi-Fi, Bluetooth disabled
- Test on **3 device tiers**: Entry (<4GB RAM), Mid (4–6GB), Flagship (≥6GB)
- Test in **real outdoor conditions** at actual heritage sites

---

## 2. Offline Operation Verification

### 2.1 Airplane Mode Test

| ID | Test | Pass Criteria |
|---|---|---|
| AIR-001 | Fresh install, airplane mode on | App launches successfully |
| AIR-002 | Search for known place | Results returned within 2s |
| AIR-003 | Open place detail | Full content loads with sources |
| AIR-004 | Scan a supported landmark | Recognition result within 6s |
| AIR-005 | Scan an unsupported object | Abstention message displayed |
| AIR-006 | Browse curated walks | Trail details load |
| AIR-007 | View Heritage Passport | Stamps load |
| AIR-008 | Play audio story | Narration plays (if assets present) |
| AIR-009 | Add journal entry | Entry saved locally |
| AIR-010 | Install offline pack | Pack verifies and activates |

### 2.2 Network Isolation Verification

Use Android's `tcpdump` or similar to verify zero network egress during all P0 operations.

---

## 3. Device Tier Testing

### 3.1 Tier E (Entry, <4GB RAM)

- App installs and launches
- Search works with FTS
- QR scanning works
- Compact vision model functions
- Journal operations work
- No crashes during 30-minute session

### 3.2 Tier M (Mid, 4–6GB RAM)

- All Tier E features work
- Audio playback works
- Optional OCR/translation works
- Trails render correctly

### 3.3 Tier F (Flagship, ≥6GB RAM)

- All Tier M features work
- Optional LLM features work (if enabled)
- Richer media renders correctly

---

## 4. Recovery and Resilience

| ID | Scenario | Pass Criteria |
|---|---|---|
| REC-001 | Pack download interrupted | Partial pack deleted, retry succeeds |
| REC-002 | Pack install fails mid-extraction | Previous pack retained, no corruption |
| REC-003 | Pack tampered after install | File rejected by manifest validation |
| REC-004 | Storage full during pack install | Graceful error, no data loss |
| REC-005 | App killed during audio playback | No crash on resume |
| REC-006 | Camera permission denied | Search fallback works |
| REC-007 | Low battery (<10%) | App suggests power-saving mode |
| REC-008 | Device rotation during scan | Scan completes correctly |

---

## 5. Accessibility Testing

| ID | Test | Pass Criteria |
|---|---|---|
| ACC-001 | TalkBack navigation | All interactive elements reachable |
| ACC-002 | Font size adjustment | Text scales to 200% without truncation |
| ACC-003 | High contrast mode | UI elements distinguishable |
| ACC-004 | Screen reader labels | All buttons have content descriptions |

---

## 6. Instrumented Android Tests (Required)

The 5 instrumented test suites have been implemented in `android/app/src/androidTest/com/trueway/app/` and compile cleanly with `./gradlew.bat compileDebugAndroidTestKotlin`:

| Test Suite | Framework | What It Verifies |
|---|---|---|
| `CameraRecognitionTest.kt` | CameraX + real camera | End-to-end scan pipeline execution |
| `AudioPlaybackTest.kt` | MediaPlayer on device | Actual audio file playback and focus |
| `PackLifecycleTest.kt` | Real filesystem | Install/verify/activate/delete on device |
| `OfflineModeTest.kt` | Airplane mode toggle | Zero network egress assertion |
| `PerformanceBenchTest.kt` | System timer | P50/P95 latency measurements |

---

## 7. Sign-Off Requirements

Status toward public beta approval:

- [ ] Camera benchmarks pass Gate 2 on 3 physical hardware device tiers (field immersion)
- [x] 100+ independent negative test queries assembled (`tests/fixtures/retrieval_benchmark_250.csv`)
- [x] FAR upper confidence bound $\le$ 5% at 95% confidence verified in CI (Clopper-Pearson upper bound = 4.66% $\le$ 5.0%)
- [ ] All airplane mode tests pass on physical devices in Bodh Gaya / Nalanda
- [ ] All recovery tests pass on physical hardware
- [ ] All accessibility tests pass on physical hardware
- [x] Instrumented Android test suites written, compiling, and packaging cleanly (`compileDebugAndroidTestKotlin` & `assembleDebugAndroidTest` PASS $\rightarrow$ `app-debug-androidTest.apk`)
- [ ] Field test report signed off by engineering lead
- [x] Content rights registered in `content/seed/rights_registry.json` (26 assets, 0 synthetic)
