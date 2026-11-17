# pack-builder/ — signed regional pack pipeline (blueprint §9, §20.2, §28.1)

Builds and verifies cryptographically signed regional packs (`.twpkg`) from
schema and seed SQL, canonical JSON manifests, SHA-256 hash trees, zero-copy
TWVEC002 binary vision indexes, and detached Ed25519 signatures.

## Layout of a built pack (§9.4)

```text
trueway-<pack_id>-<version>.twpkg  (zip)
  manifest.cjson               # canonical JSON — THE signed bytes
  manifest.ed25519             # detached signature (never inside manifest.cjson)
  content/places.sqlite        # publication schema + seed SQL (PUBLISHED/REVIEWED only)
  ATTRIBUTIONS.json            # attributions and sources
  LICENSES.json                # statutory rights & CC BY-SA 4.0 licences
  CHANGELOG.md                 # plain-language release notes
  content/audio/               # optional regional audio tracks (.ogg)
  content/images/then_now/     # optional comparison plates (.webp)
  vision/                      # optional zero-copy TWVEC002 vector index
    reference_index.json       # reference index source
    reference_vectors.bin      # 40-byte 8-aligned header + float32 vectors + CSLS local scale
    reference_vectors.meta.json# metadata with learned calibration gate & encoder digest
    index.bin                  # binary index copy
```

## Regional Pack Distribution Catalog (§20.1, §20.5)

`regional_catalog.py` manages registered corridors, release metadata, and pack bundles:
- `in-bihar-buddhist-circuit`: Bodh Gaya, Nalanda, Rajgir flagship demonstrator (15 POIs).
- `in-golden-triangle`: Delhi, Agra, Jaipur cultural corridor (Taj Mahal, Qutub Minar, Red Fort, Hawa Mahal, Amer Fort, Fatehpur Sikri).
- Dynamic discovery of `.twpkg` archives in `dist/`.

List available regional packs:
```powershell
python pack-builder\build_pack.py --list-regions
```

## Build Commands

### 1. Demonstrator Pack (Default)
```powershell
python pack-builder\build_pack.py --version 2026.10.1 --out dist --demo-key --audio-dir content/audio --images-dir content/images/then_now --vision-dir content/vision
```

### 2. Custom Regional Pack
```powershell
python pack-builder\build_pack.py --pack-id in-golden-triangle --pack-title "India Golden Triangle Corridor" --version 2026.10.1 --out dist --seed path/to/seed.sql --demo-key
```

### 3. Release Signing with Real Ed25519 Key (§28.8)
```powershell
python pack-builder\build_pack.py --version 2026.10.1 --out dist --key-file path/to/ed25519.key --key-id pubkey-2026-q4
```

## Verification Commands

### 1. Verify Archive Bundle (.twpkg)
```powershell
python pack-builder\build_pack.py --verify dist\trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg
```

With release Ed25519 public key and downgrade guard:
```powershell
python pack-builder\build_pack.py --verify dist\trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg --pub-key-b64 <base64_pub_key> --min-safe 2026.10.1
```

### 2. Verify Zero-Copy TWVEC002 Binary Index
```powershell
python pack-builder\build_pack.py --verify-twvec content\vision\reference_vectors.bin --twvec-meta content\vision\reference_vectors.meta.json
```

## Invariants Enforced (§9.3 [G], Android `PackImporter.kt` Parity)

- **Archive Path Security:** No absolute paths, no `..` path segments, no executables (.exe, .dll, .so, .apk, .sh, .bat, .ps1, .cmd).
- **Cryptographic Trust:** Detached Ed25519 signature verified **before** trusting any hash.
- **Key-ID / Signature Binding:** Demo signatures rejected unless `signing_key_id` is explicitly `DEMO-KEY-DO-NOT-SHIP`.
- **SHA-256 Tree Completeness:** Every file in the archive must be listed in `manifest.cjson`; no unlisted smuggled files.
- **Digest & Size Verification:** Exact uncompressed byte size and SHA-256 checked for each file.
- **Zero-Copy TWVEC002 Integrity:** Header length 40 bytes (8-byte aligned), magic `TWVEC002`, version 2, float32 storage, CSLS local scale section, exact byte count formula, finite non-NaN vectors, contiguous prototype ranges, complete 6-parameter calibration gate, and encoder binding (`model_sha256` CRC32).
- **Atomic Activation & Rollback Support:** Replay/downgrade protection against `min_safe` release version.

## Tests

Run comprehensive pack-builder and hostile test suites:
```powershell
python -m unittest tests/test_pack_builder.py
python tests/fixtures/hostile/make_hostile.py
```
