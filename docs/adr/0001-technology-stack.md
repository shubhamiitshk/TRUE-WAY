# ADR-0001: Reference technology stack

- **Status:** Accepted (2026-10-10)
- **Source:** Blueprint §8.2 "Proposed stack" [D] (design decision, subject to benchmark-driven change)
- **Context:** TrueWay must run recognition, history reading, search and journaling with **zero network** after setup (§3), on Android-first devices from entry to flagship tiers (§8.3).

## Decision

| Layer | Choice | Notes |
|---|---|---|
| Platform | Kotlin, Android-first | Flutter/React Native only if native camera/AI constraints demand it |
| UI | Jetpack Compose + Material 3 | TalkBack and contrast requirements are release gates (§19.1) |
| Camera | CameraX, lifecycle-bound, **single-shot** default | No continuous recognition loop unless benchmarked (§19.1) |
| Navigation | bottom nav: Explore · Scan · Saved · Downloads; Settings from top bar (§6.7) | `Ask` tab only when a local model is actually ready |
| Data | SQLite (Room) + FTS5 | Flat vector matrix first; R-Tree only when spatial needs merit it (§10.3) |
| AI runtime | LiteRT / benchmarked runtime | ONNX Runtime Mobile and TFLite are benchmark candidates (§8.2) |
| Maps | MapLibre + already-downloaded local PMTiles | Never render a blank "offline" map (§6.4) |
| OCR | ML Kit Text Recognition v2 (bundled models) | Supported scripts only (§8.2) |
| Speech | Optional Vosk / sherpa-onnx | Gated P1; typed fallback mandatory (§5.3 F102) |
| Pack server | Python + FastAPI + build workers | Publishing path only; never in the scan/read path (§8.1) |
| CI/CD | GitHub Actions or analogous, reproducible builds | Separate data and code quality gates |
| Observability | Local debug metrics; strict opt-in aggregation | Never upload raw photos/audio by default |

## Consequences

- JVM unit tests only for Day 1–2 (no instrumented test runner wired yet); Robolectric/instrumented tests come with schema work.
- Distribution URLs must be pinned; this machine cannot reach `gradle.org`, so the wrapper uses the cached `gradle-8.13-bin` distribution.
- Version choices live in `android/gradle/libs.versions.toml` so a benchmark can change them in one place.

## Alternatives considered (deferred, not rejected)

- ONNX Runtime Mobile vs LiteRT — decided by Day 9–10 profiling (§23.3).
- Flutter/RN — rejected for v1 because CameraX + on-device ML integrations are the core risk (§8.2).
