# ADR-0005: PMTiles for Offline Vector Map Storage and MapLibre Native Rendering

- **Status:** Accepted (2026-10-11)
- **Source:** `docs/SYSTEM_ARCHITECTURE_SPECIFICATION.md` §7; Blueprint §12
- **Context:** Heritage exploration requires rendering offline vector maps for monuments, walking trails, and terrain. Running a local HTTP tile server or unpacking millions of raster/vector tile files causes filesystem bloat, slow installation, and high battery consumption.

## Decision

1. Adopt **PMTiles** (Protomaps single-file archive format) for regional offline vector map storage.
2. Render maps using **MapLibre Native Android** with direct `pmtiles://` file URL custom source integration.
3. Package map files as optional regional components (e.g. `map-bihar.pmtiles`, 25–100MB) inside regional `.twpkg` archives or as modular downloads.
4. Fallback behavior: If map tiles are not downloaded, the app displays a structured offline POI list and directional compass without failing.

## Consequences

- Entire regional map lives in a single, seekable archive file with zero HTTP tile server overhead.
- Rapid pack installation and instant deletion without leaving fragmented tile caches on the user's device.
