# pack-builder/ — signed regional pack pipeline (blueprint §9, §20.2, §28.1)

Builds the `in-bihar-buddhist-circuit` demonstrator pack from
`content/schema/` + `content/seed/`: canonical manifest → SHA-256 per
file → detached Ed25519 signature → hostile-archive validation.

## Layout of a built pack (§9.4)

```text
trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg  (zip)
  manifest.cjson        # canonical JSON — THE signed bytes
  manifest.ed25519      # detached base64 signature (never inside manifest.cjson)
  content/places.sqlite # publication_schema.sql + seed_demo.sql, PUBLISHED/REVIEWED only
  ATTRIBUTIONS.json / LICENSES.json / CHANGELOG.md
  content/audio/        # P1A: 20 bilingual OGG tracks (10 POIs × EN/HI)
  content/images/       # P1A: 6 WebP images (3 historic + 3 modern)
```

## Commands (stdlib + `cryptography` or `PyNaCl` for real keys)

```powershell
python pack-builder\build_pack.py --version 2026.10.1 --out dist
python pack-builder\build_pack.py --verify dist\trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg
```

### With media assets (P1A)

```powershell
python pack-builder\build_pack.py --version 2026.10.1 --out dist --audio-dir path/to/audio --images-dir path/to/images
python pack-builder\build_pack.py --verify dist\trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg
```

The `--demo-key` flag signs with an ephemeral key and stamps
`DEMO-KEY-DO-NOT-SHIP` as `signing_key_id` so a demo signature can
never be mistaken for a release signature (§28.8: private keys live in
a protected signing environment, never in the repo).

## Invariants enforced (§9.3 [G])

- `bytes_free` storage check inputs recorded in the manifest.
- No absolute paths, no `..`, no symlinks, no executables in the zip.
- Receiver verifies detached signature **before** trusting any digest.
- Failed verification keeps the previous pack; nothing half-activates.
