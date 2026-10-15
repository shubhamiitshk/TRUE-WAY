# ADR-0008: Database Isolation for User-Private Data and Journaling

- **Status:** Accepted (2026-10-11)
- **Source:** `docs/SYSTEM_ARCHITECTURE_SPECIFICATION.md` §4.1; Blueprint §28.4
- **Context:** TrueWay features travel journaling, personal notes, bookmarks, and visit history. Regional packs (`places.sqlite`) are publisher-owned, downloaded, updated, and replaced as new scholarship or corrections emerge. If user data and pack data coexisted in a single database, pack updates or rollbacks could corrupt or erase personal memories.

## Decision

1. Completely separate the storage architecture into two independent database files:
   - **Publisher Database (`places.sqlite`):** Extracted from `.twpkg` packs, read-only to user interactions, atomically replaced upon pack updates.
   - **User Private Database (`user_journal.sqlite`):** Governed by `content/schema/journal_schema.sql` and managed via Room, strictly isolated from pack lifecycles.
2. User preferences, consent records, and telemetry flags are stored in Jetpack DataStore, never in pack databases.
3. One-tap deletion: The user can purge their private database at any time without affecting installed regional knowledge packs.

## Consequences

- Pack downloads, upgrades, and rollbacks are 100% safe for personal travel data.
- Guarantees DPDP Act 2023 (India) and GDPR compliance with clean data isolation and instant erasure capabilities.
