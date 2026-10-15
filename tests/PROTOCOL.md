# tests/ — offline + hostile-pack regression protocol (blueprint §29)

## Radio states (record per run, §29 preamble)

- **RADIO-OFF**: mobile data + Wi-Fi + Bluetooth disabled. Core P0 suite.
- **NO-INTERNET/P2P**: Bluetooth/Wi-Fi enabled for Nearby, Internet
  isolated. Relay + QR-peer tests only.

## P0 core (scripted, all RADIO-OFF unless noted)

| ID | Scenario | Pass |
|---|---|---|
| OFF-001 | Supported search + sourced card, RADIO-OFF | Card + sources open, zero egress |
| OFF-002 | Manual lookup by Hindi alias, RADIO-OFF | Correct place resolves |
| OFF-003 | No GPS permission | Full list + search still work |
| TRUST-013 | Every material claim shows source + type chip | 22/22 seeded claims have anchors |
| SITE-018 | Mahabodhi card | Device-prohibition warning visible, no scan CTA |
| PACK-021/22/23 | Tampered pack fixtures (below) | Rejected, prior pack retained |
| PRIV-028 | One-shot scan | No off-device photo/EXIF/audio transmission |

## P0.5 & P1A verified experience protocol (v3.0 Execution Plan)

| ID | Scenario | Pass criteria |
|---|---|---|
| BRIEF-050 | "Before You Enter" briefing outside restricted boundary | Mahabodhi device prohibition highlighted; permitted perimeter bounded; screen-free observation targets rendered; no device instruction inside |
| DIAG-051 | 9-layer Truly-Ready offline self-test in Downloads tab | All 9 layers (Corpus, FTS, Vision, Essentials, Audio, Walks, Compliance, Sandbox, Geodesic Proximity) return PASSED with 0 network calls |
| AUDIO-052 | Pre-rendered bilingual audio story & pronunciation guide | Narrative script + phonetic IPA pronunciation + full text transcript accessible; zero live TTS network engine variance |
| WALK-053 | Curated heritage walking trail | Sequenced stop itinerary with terrain notes, heat advisories, and estimated duration labelled as estimate |
| PASSPORT-054 | Private offline heritage passport | Commemorative seal saved to private `user_journal.sqlite`; non-official commemorative disclaimer visible |
| ARCHIVE-055 | "Then & Now" archival comparisons | 19th/early-20th-century ASI photographic surveys with verified WebP plates, rights statements, and conservation status |
| EXPORT-056 | Public card sharing & private journal export | Public citation card shared via Android system share sheet; private journal exported as Plaintext, JSON, and PDF formats with automatic cache pruning |
| GEO-057 | Offline geodesic proximity & nearby places | Pure offline Haversine great-circle calculation, corridor hubs sorted by distance, meter/km formatting |
| PACK-058 | Dynamic active pack resolution & trust rotation | Regional reference embeddings index and touchpoint trust store dynamically resolved from active pack ahead of APK roots |

## Hostile pack fixtures (`tests/fixtures/hostile/`)

Generated (never committed) by `make_hostile.py` — exit 0 iff the valid
pack verifies OK and all attacks are rejected with named causes.
Workstation and on-device test suites: **7/7 PASS** (`HostilePackIntegrationTest.kt`).

| Fixture | Attack | Verifier verdict |
|---|---|---|
| `bad-signature.twpkg` | flipped byte in `manifest.ed25519` | REJECT invalid signature |
| `unknown-key.twpkg` | `signing_key_id: attacker-key-1` | REJECT signature mismatch |
| `truncated-sqlite.twpkg` | `places.sqlite` cut by 1 KB | REJECT digest/size mismatch |
| `traversal.twpkg` | added `../../evil.txt` entry | REJECT unsafe archive path |
| `downgrade.twpkg` | valid bytes, `--min-safe` above version | REJECT downgrade refused |

Both workstation Python verification and on-device Android `PackImporter` integration suites (7/7 tests) verify atomic activation, safe directory eviction, and complete rejection of hostile packs.

## P1/P2 (gated, NO-INTERNET/P2P where marked)

TOUCH-033…036 are **implemented** (`touchpoint/` + `QrScanScreen`, 7/7
crypto tests with real Ed25519) — field QR-plate deployment stays gated.
RELAY-037…042, VOICE-043…045, OCR-046/047 — run only when the gated
feature branch exists; never block the P0 beta on them (§23.4).
