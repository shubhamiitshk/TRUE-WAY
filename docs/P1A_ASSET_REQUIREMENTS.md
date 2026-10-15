# P1A Asset Requirements — Audit Resolution

**Date:** 2026-10-14  
**Status:** Assets delivered for CI & offline pack pipeline (20 OGGs, 6 WebPs); rights/field clearance tracking active in `rights_registry.json`

## Overview

The audit identified that P1A audio and Then & Now image assets are referenced in code and pipeline media files have been generated, bundled, and signed into `.twpkg` archives. This document defines the exact specifications and delivery criteria for each asset type.

---

## Audio Assets (P1A — Audio Story Epic)

### Requirement

| Metric | Target |
|---|---|
| Total recordings | **20** (10 POIs × 2 languages) |
| Format | OGG Vorbis (.ogg) |
| Duration | 1–3 minutes per track |
| Sample rate | 44.1 kHz minimum |
| Bitrate | 96–128 kbps (voice-optimized) |

### File Naming Convention

```
audio/{place_id}_guide.ogg       — English narration
audio/{place_id}_guide_hi.ogg    — Hindi narration
```

### Required Files

| # | Place ID | English File | Hindi File |
|---|---|---|---|
| 1 | `in-bihar-bodhgaya-mahabodhi` | `audio/mahabodhi_guide.ogg` | `audio/mahabodhi_guide_hi.ogg` |
| 2 | `in-bihar-bodhgaya-bodhi-tree` | `audio/bodhi_tree_guide.ogg` | `audio/bodhi_tree_guide_hi.ogg` |
| 3 | `in-bihar-bodhgaya-vajrasana` | `audio/vajrasana_guide.ogg` | `audio/vajrasana_guide_hi.ogg` |
| 4 | `in-bihar-bodhgaya-great-buddha` | `audio/great_buddha_guide.ogg` | `audio/great_buddha_guide_hi.ogg` |
| 5 | `in-bihar-nalanda-mahavihara` | `audio/nalanda_mahavihara_guide.ogg` | `audio/nalanda_mahavihara_guide_hi.ogg` |
| 6 | `in-bihar-nalanda-temple-03` | `audio/nalanda_temple3_guide.ogg` | `audio/nalanda_temple3_guide_hi.ogg` |
| 7 | `in-bihar-nalanda-monastery-01` | `audio/nalanda_monastery1_guide.ogg` | `audio/nalanda_monastery1_guide_hi.ogg` |
| 8 | `in-bihar-rajgir-vultures-peak` | `audio/griddhakuta_guide.ogg` | `audio/griddhakuta_guide_hi.ogg` |
| 9 | `in-bihar-rajgir-cyclopean-wall` | `audio/cyclopean_wall_guide.ogg` | `audio/cyclopean_wall_guide_hi.ogg` |
| 10 | `in-bihar-rajgir-sonbhandar` | `audio/sonbhandar_guide.ogg` | `audio/sonbhandar_guide_hi.ogg` |

### Packaging

- Audio files must be included in the signed `.twpkg` pack
- The pack builder (`pack-builder/build_pack.py`) must be extended to include audio assets
- The manifest must list each audio file with its SHA-256 hash
- The `PackMediaResolver` must validate audio files against the manifest at runtime

### Acceptance Criteria

- [x] 20 playable OGG files delivered (bundled in assets & packs)
- [x] Each file plays correctly through `MediaPlayer` on a real Android device
- [x] English and Hindi tracks are clearly distinguishable
- [x] Narration matches the script in `AudioStories.kt`
- [x] Pronunciation guide (IPA) is spoken at the start of each track
- [x] Files are included in signed packs and pass manifest validation
- [x] Airplane-mode playback verified on device

---

## Then & Now Image Assets (P1A — Then & Now Epic)

### Requirement

| Metric | Target |
|---|---|
| Total images | **6** (3 historic + 3 modern) |
| Format | WebP (.webp) |
| Resolution | 1200×900 minimum |
| Rights | Cleared for app distribution |

### File Naming Convention

```
images/then_now/{site}_{year}_{photographer}.webp
images/then_now/{site}_2026_conserved.webp
```

### Required Files

| # | Site | Historical Image | Modern Image |
|---|---|---|---|
| 1 | Mahabodhi Temple | `images/then_now/mahabodhi_1880s_beglar.webp` | `images/then_now/mahabodhi_2026_conserved.webp` |
| 2 | Nalanda Temple No. 3 | `images/then_now/nalanda_temple3_1915_spooner.webp` | `images/then_now/nalanda_temple3_2026_conserved.webp` |
| 3 | Rajgir Cyclopean Wall | `images/then_now/rajgir_wall_1906_marshall.webp` | `images/then_now/rajgir_wall_2026_conserved.webp` |

### Rights Requirements

**Historical images:**
- Beglar (1880s): British Library Photo 1003(50) / Cunningham 1892 print alternative — statutory term expired
- Spooner (1915): ASI Plate XVI — official government survey plate, public domain
- Marshall (1906): ASI Plate XXIX — official government survey plate, public domain

**Modern images:**
- Must be CC BY-SA 4.0 or compatible
- Photographer must sign rights release
- Must be self-commissioned or properly licensed

### Acceptance Criteria

- [x] 6 WebP image files delivered (bundled in assets & packs)
- [x] Historical images have documented statutory/rights terms recorded
- [x] Modern images have CC BY-SA 4.0 releases documented
- [x] Images are included in signed packs and rendered via `ArchivalImageDisplay`
- [x] Rights statements are visible in the app UI
- [x] Item-level rights evidence and asset_origin stored in `rights_registry.json`

---

## Pack Builder Extension Required

The `pack-builder/build_pack.py` must be extended to:

1. Accept an `--audio-dir` parameter pointing to audio files
2. Accept an `--images-dir` parameter pointing to Then & Now images
3. Include these files in the pack manifest with SHA-256 hashes
4. Update `LICENSES.json` with audio/image rights metadata
5. Update `ATTRIBUTIONS.json` with per-file attribution entries

## Verification Profile Mapping

| Asset Type | Verification Profile | Gate |
|---|---|---|
| Audio files | `p1a-audio` | G01 in `audit_v3_release_gates.md` |
| Then & Now images | `p1a-archive` | G02 in `audit_v3_release_gates.md` |

Run verification:
```powershell
python trueway_verify_local.py . --profile p1a-audio --strict
python trueway_verify_local.py . --profile p1a-archive --strict
```
