# P0 Scope Clarification — v3.0 Audit Resolution

**Date:** 2026-10-13  
**Auditor:** ChatGPT (external review)  
**Resolution:** Accepted — scope definitions corrected and separated

## Background

The audit identified that the latest report described a "text-first P0 beta" focusing on offline search, verified claims, advisories, and Heritage Passport. This did not match the approved v3.0 strategy, where **camera recognition (F002)** is a P0 feature and **Heritage Passport (F107)** is P1A.

## Approved v3.0 Scope Definitions

### Full P0 Beta (F001–F015)

| ID | Feature | Priority |
|---|---|---|
| F001 | Region onboarding | P0 |
| F002 | **Camera capture/landmark ranking** | **P0** |
| F003 | Search and category lookup | P0 |
| F004 | Sourced historical card | P0 |
| F005 | Optional GPS location | P0 |
| F006 | Pack lifecycle (download → verify → index → atomic activate) | P0 |
| F007 | Lite journal/bookmarks | P0 |
| F008 | Offline nearby/list | P0 |
| F009 | Camera/device restrictions | P0 |
| F010 | Trust/unknown UI | P0 |
| F011 | Basic essentials strip | P0 |
| F012 | Resource & low-battery controls | P0 |
| F013 | Pack content changelog | P0 |
| F014 | Signed QR resolver | P0 |
| F015 | Help, accessibility, offline badge | P0 |

**P0 Exit Criteria:**
- All F001–F015 features functional
- Camera recognition: Top-1 ≥85%, Top-3 ≥95%, FAR ≤5%
- All core flows work with Internet off + radios off
- Malicious pack rejection verified

### Search-First Beta (Reduced Scope Option)

A narrower beta that ships **before** camera benchmarks succeed, provided:

1. Scanning is explicitly marked as **experimental** or **unavailable**
2. Release scope is officially changed and documented
3. Users are **not promised** reliable visual recognition
4. All other P0 features (search, sourced cards, packs, journal, QR, essentials) are functional

**Search-First Beta ≠ Full P0 Completion.** This distinction must be clearly communicated in all release notes and marketing materials.

### P1A Experience Epics (Post-P0)

| Epic | Features | Status |
|---|---|---|
| Audio Story | F101+F110+F106 | Implemented (20/20 audio files bundled & verified) |
| Curated Walks | F105+F112 | Implemented (3 trails) |
| Heritage Passport | F107 | Implemented (6 stamps) |
| Then & Now | F108 | Implemented (6/6 WebP plates bundled & verified) |
| Share & Export | F114+F117 | Implemented (JSON, Plaintext & PDF export with cache pruning) |

## Release Path Decision

Two release paths are available:

- **Path A: Full P0 Beta** — Ship when camera benchmarks pass Gate 2 (Top-1 ≥85%, FAR ≤5%). Includes all F001–F015.
- **Path B: Search-First Beta** — Ship when offline content + security gates pass. Camera scanning explicitly experimental/unavailable. Must not be described as "P0 complete."

## Action Items

- [x] Scope definitions corrected in this document
- [ ] Release notes must explicitly state which path is taken
- [ ] If Path B, UI must show scanning as "Experimental" or "Coming Soon"
- [ ] If Path B, release title must not include "P0" without qualification
