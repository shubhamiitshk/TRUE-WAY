# ADR-0004: SQLite + `sqlite-vec` Hybrid Vector & Full-Text Search

- **Status:** Proposed / Gated (Deferred to P1 per ADR-0003 & CONFLICT_REGISTER [M1])
- **Source:** `docs/SYSTEM_ARCHITECTURE_SPECIFICATION.md` §4; `docs/STRATEGIC_TECHNOLOGY_BLUEPRINT_2026_2027.md` §3.2
- **Context:** TrueWay requires semantic query understanding and image embedding nearest-neighbor retrieval on-device with zero internet. At a pilot scale of 15–70 POIs (with 10–30 reference vectors each), in-memory flat brute-force retrieval (ADR-0003) via `TWVEC001` zero-copy binary indexes executes in $<1\text{ ms}$, requiring zero native `.so` extension overhead. However, as the corpus expands beyond 10,000 vectors across multiple states, an in-process indexed vector table is desirable.

## Current v1 Status vs. Gated P1 Roadmap
- **Shipped v1 Architecture:** In-memory flat brute-force cosine retrieval (via `TWVEC001` memory-mapped binary vector files or in-memory arrays) paired with SQLite FTS5 for text search.
- **Gated Upgrade Trigger:** `sqlite-vec` will be benchmarked and activated when corpus size exceeds 10,000 vectors or when P95 retrieval latency exceeds 50ms on entry-tier devices.

## Decision

1. Adopt **`sqlite-vec`** as the in-process vector search engine, loaded as a runtime SQLite extension via `vec0` virtual tables directly into `places.sqlite`.
2. Implement **Hybrid Search with Reciprocal Rank Fusion (RRF)**:
   - Sparse lexical branch: SQLite FTS5 (BM25 ranking on canonical names, aliases, and claim text).
   - Dense semantic branch: `sqlite-vec` cosine distance matching on 128-dim MRL embeddings.
   - Combined score: $\text{RRF} = \frac{1}{60 + \text{BM25\_rank}} + (1.0 - \text{cosine\_distance})$.
3. On Android, bundle `androidx.sqlite:sqlite-bundled` with precompiled native libraries for `arm64-v8a` and `armeabi-v7a`. Maintain an exact Kotlin in-memory scalar dot-product fallback if OEM security policies restrict extension loading.

## Consequences

- Keeps the entire knowledge base, full-text index, and vector embeddings in a single atomic SQLite file (`content/places.sqlite`) inside the signed pack.
- Zero network dependencies, zero separate database processes, and single-digit millisecond latency.
