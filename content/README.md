# content/ — typed claims, rights, bibliography, translations

Boundary per blueprint §8.4. This directory holds **editorial source material and schemas**, not application code.

## Schemas (blueprint §28)

| File | Purpose |
|---|---|
| `schema/publication_schema.sql` | Publisher knowledge base: places, aliases, claims, sources, claim↔source links, assets, reference embeddings, operational notices, touchpoints, pack releases, FTS5 search index (§28.3) |
| `schema/journal_schema.sql` | **Private, separate** database: journal entries, achievements, consent (§28.4). Separate file so deleting a region pack never deletes private notes. |

Both are executable SQLite DDL taken from the blueprint's reference contracts. They are *illustrative starter specification* (§28 preamble) — production needs migration discipline and generated fixtures.

## Publication rules (enforced at pack-build time)

1. **Do not export** `DRAFT`, rights-`PENDING` or rights-`REJECTED` content (§28.3).
2. Every claim row must carry a correct `place_id` and `reviewed_at`/`reviewer_id` (§10.2).
3. **Source ≠ licence.** Rights metadata lives at the asset level; a well-sourced fact may still be unshippable (§10.4).
4. Keep translation versions distinct from fact versions so a text fix never reverts corrected history (§9.2).
5. Romanized-Hindi aliases are stored explicitly; do not rely on FTS tokenization to transliterate Devanagari (§10.3).
6. Claim types (`DOCUMENTED`, `INTERPRETATION`, `TRADITION`, `CONTESTED`, `OPERATIONAL`, `HYPOTHESIS`) drive visible badges — never flatten tradition into documented fact (§10.4).

## Timestamps — do not confuse (§10.2)

`published_at` (source published) · `source_accessed_at` (editor read it) · `reviewed_at` (editor verified claim) · `effective_from/to` (rule applies) · `pack_built_at` (bundle compiled) · `installed_at` (user installed).

## Specifications & Tooling

| Path | Purpose |
|---|---|
| `DATASET_RESEARCH_AND_HARVESTING_SPECIFICATION.md` | Full dataset sourcing architecture: GLDv2 pretraining, Wikimedia Commons harvesting, Places365 negative sets, AI4Bharat IndicVoices ASR, and EGYPT-v1 / EgMM-Corpus structural benchmarks |
| `tools/harvest_monument_metadata.py` | Automated Wikidata SPARQL & Commons metadata harvester for Bihar monuments with offline fallback |
| `field/COLLECTION_PROTOCOL.md` | Physical on-site capture protocol, split integrity, privacy scrubbing, and Mahabodhi security compliance |
| `field/SCHOLAR_POI_WORKSHEET_TEMPLATE.yaml` | Structured editorial template for Magadh/Nalanda University scholar POI submissions (claims, citations, Before You Enter notices, word budgets) |
| `tools/validate_scholar_submission.py` | Automated linter verifying scholar POI submissions prior to honorarium payment approval |
| `vision/reference_index.json` | 512-dimensional canonical normalized reference embeddings & calibration thresholds for the 15 POIs |

## Status

- ✅ Schemas transcribed from §28.3 / §28.4
- ✅ Dataset acquisition specification and Wikidata SPARQL harvester operational
- ✅ 15 demonstrator POIs seeded (`seed_demo.sql`, validated via `validate_seed.py`)
- ✅ 20 bilingual audio guide recordings (10 POIs × EN/HI) generated in `content/audio/` and bundled in `.twpkg` and APK fallback
- ✅ 6 Then & Now comparison WebP plates (1200×900) generated in `content/images/then_now/`
- ✅ Rights registry operational in `content/seed/rights_registry.json` (26 registered assets: 20 TTS_PRELIMINARY, 3 PUBLIC_DOMAIN_ARCHIVAL, 3 FIELD_CLEARED_PRODUCTION; 0 SYNTHETIC_DEV)
- ✅ Scholar submission template and linter operational (`validate_scholar_submission.py` PASS)
- ✅ Zero-copy `TWVEC001` binary vector index generation operational in `pack-builder/build_pack.py`
- ✅ Security hardening & runtime wiring: manifest authentication + SHA-256 verification + publisher trust + safe pack swap eviction hooks (117/117 JVM tests PASS across 20 suites)
