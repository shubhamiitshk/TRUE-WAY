# ADR-0002: Demonstrator knowledge layer without Room (Days 3–4)

- **Status:** Accepted (2026-10-11)
- **Source:** Blueprint §10.3 (SQLite + FTS5), §28.3 (publication DDL); sprint DoD Days 3–4.
- **Context:** The DoD needs `place_id`/`claim_id`/`source_id` joins plus
  local source UI today; adding Room + KSP + FTS wiring in one step risks
  breaking the green Day 1–2 build on a machine with a pinned offline
  Gradle cache.

## Decision

- Canonical data lives in `content/schema/*.sql` + `content/seed/seed_demo.sql`
  (real SQLite, validated by `validate_seed.py` — including the FTS5 index).
- The app mirrors that seed in `data/DemoCorpus.kt` + `data/PlaceRepository.kt`
  (pure Kotlin, JVM-tested) and renders it in `PlaceDetailScreen`.
- Room + FTS5 on-device + pack-import DB lands with Days 8–11
  (pack lifecycle F006); the repository interface is kept narrow so the
  swap is mechanical.

## Consequences

- Two copies of the corpus exist until the Room migration; any seed edit
  must update `DemoCorpus.kt` + `PlaceRepositoryTest` in the same commit.
- `validate_seed.py` is the join-truth gate; JVM tests mirror it.
