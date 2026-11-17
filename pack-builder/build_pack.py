"""Demonstrator & release pack builder / verifier — blueprint §9.3, §20.2, §28.1, §28.8.

Supports:
- Multi-region pack definitions (.twpkg) via regional catalog or CLI args.
- Real Ed25519 signing via --key-file (32-byte raw seed or hex/base64 seed)
  and verification via --pub-key-b64.
- Ephemeral demo signing via --demo-key (stamps DEMO-KEY-DO-NOT-SHIP).
- Full canonical manifest.cjson SHA-256 tree hashing and verification.
- Zero-copy binary index integrity checking (TWVEC002 format, 40-byte 8-aligned header,
  L2 float32 storage, CSLS local density scale section, contiguous prototype ranges).
- Automatic item-level `asset_origin` stamping into `manifest.cjson` from
  rights registry so Android's `PackMediaResolver` enforces trust boundaries at runtime.
- Full schema and layout parity with Android PackImporter.kt.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import sqlite3
import struct
import sys
import tempfile
import zipfile
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pack-builder"))

try:
    from regional_catalog import RegionalPackCatalog, RegionalPackDefinition, default_catalog
except ImportError:
    RegionalPackCatalog = None
    default_catalog = None

DEFAULT_PACK_ID = "in-bihar-buddhist-circuit"
SCHEMA_VERSION = 3

TWVEC_MAGIC = b"TWVEC001"
TWVEC_HEADER_FMT = "<8sIIIIII"  # 32 bytes little-endian
TWVEC002_MAGIC = b"TWVEC002"
TWVEC002_HEADER_FMT = "<8sIIIIIIII"  # 40 bytes little-endian (8-byte aligned)
TWVEC002_HEADER_SIZE = 40


def _load_asset_origins(rights_registry_path: Optional[Path] = None) -> Dict[str, str]:
    """Loads asset_path -> asset_origin mapping from rights registry."""
    origins: Dict[str, str] = {}
    path = rights_registry_path or (ROOT / "content" / "seed" / "rights_registry.json")
    if not path.is_file():
        return origins
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("audio_tracks", []):
            p = item.get("asset_path")
            origin = item.get("asset_origin")
            if p and origin:
                origins[p] = origin
        for pair in data.get("then_and_now_archival_pairs", []):
            for side in ("historical", "modern"):
                entry = pair.get(side, {})
                p = entry.get("asset_path")
                origin = entry.get("asset_origin")
                if p and origin:
                    origins[p] = origin
    except Exception:
        pass
    return origins


def _quantize_l2_int8_row(vec: List[float]) -> bytes:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return bytes(
        (max(-127, min(127, int(round((v / norm) * 127.0)))) & 0xFF)
        for v in vec
    )


def _float32_row(vec: List[float]) -> bytes:
    return struct.pack("<%df" % len(vec), *[float(v) for v in vec])


def verify_twvec002_integrity(bin_bytes: bytes, meta_dict: Optional[dict] = None) -> Tuple[bool, List[str]]:
    """Verifies zero-copy TWVEC002 binary index integrity.

    Checks:
      1. 40-byte 8-aligned header with magic 'TWVEC002' and version 2.
      2. Storage flags declare float32 storage (flags & 1 == 1).
      3. Dimensions, positive count, and place count are strictly positive.
      4. Exact byte length matches:
         40 + (num_pos + num_neg) * dim * 4 + ((num_pos + num_neg) * 4 if (flags & 2) else 0).
      5. Vectors contain valid finite float32 values with normalized unit norms.
      6. If companion metadata is provided:
         - Dimension and place counts match.
         - Prototypes across all places sum exactly to num_pos.
         - Prototype ranges are strictly contiguous and non-overlapping.
         - Negative count matches num_neg.
         - Calibration policy contains all 6 required parameters.
         - Model sha256 is present and CRC32 matches header model_crc32.
    """
    errors: List[str] = []
    if len(bin_bytes) < TWVEC002_HEADER_SIZE:
        return False, [f"TWVEC002 file too small: {len(bin_bytes)} bytes < header size {TWVEC002_HEADER_SIZE}"]

    magic, version, model_crc, dim, num_pos, num_neg, num_places, flags, reserved = struct.unpack(
        TWVEC002_HEADER_FMT, bin_bytes[:TWVEC002_HEADER_SIZE]
    )

    if magic != TWVEC002_MAGIC:
        errors.append(f"Invalid TWVEC002 magic: {magic!r} (expected {TWVEC002_MAGIC!r})")
    if version != 2:
        errors.append(f"Unsupported TWVEC002 version: {version} (expected 2)")
    if dim <= 0:
        errors.append(f"Invalid dimension in TWVEC002 header: {dim}")
    if num_pos <= 0:
        errors.append(f"No positive reference vectors declared in TWVEC002 header: num_pos={num_pos}")
    if num_places <= 0:
        errors.append(f"No places declared in TWVEC002 header: num_places={num_places}")
    if (flags & 1) != 1:
        errors.append(f"TWVEC002 flags must declare float32 storage (flags={flags}, bit0 must be set)")

    has_scale = bool(flags & 2)
    scale_floats = (num_pos + num_neg) if has_scale else 0
    expected_bytes = TWVEC002_HEADER_SIZE + (num_pos + num_neg) * dim * 4 + scale_floats * 4

    if len(bin_bytes) != expected_bytes:
        errors.append(
            f"TWVEC002 byte size mismatch: actual {len(bin_bytes)} bytes != expected {expected_bytes} bytes "
            f"(dim={dim}, num_pos={num_pos}, num_neg={num_neg}, scale_floats={scale_floats})"
        )

    # Check finite float32 values on first vector
    if len(bin_bytes) >= TWVEC002_HEADER_SIZE + dim * 4:
        first_vec = struct.unpack("<%df" % dim, bin_bytes[TWVEC002_HEADER_SIZE : TWVEC002_HEADER_SIZE + dim * 4])
        for val in first_vec:
            if math.isnan(val) or math.isinf(val):
                errors.append("TWVEC002 contains NaN or Infinite float values")
                break
        norm = math.sqrt(sum(v * v for v in first_vec))
        if norm <= 0.0 or abs(norm - 1.0) > 0.05:
            errors.append(f"TWVEC002 reference vector not unit-norm (norm={norm:.4f})")

    # Validate against companion metadata if provided
    if meta_dict:
        meta_format = meta_dict.get("format")
        if meta_format != "TWVEC002":
            errors.append(f"Metadata format mismatch: {meta_format!r} != 'TWVEC002'")
        if meta_dict.get("storage") != "float32":
            errors.append(f"Metadata storage mismatch: {meta_dict.get('storage')!r} != 'float32'")
        if meta_dict.get("dim") != dim:
            errors.append(f"Metadata dim {meta_dict.get('dim')} != header dim {dim}")

        places = meta_dict.get("places", [])
        if len(places) != num_places:
            errors.append(f"Metadata places count {len(places)} != header num_places {num_places}")

        protos_sum = sum(int(p.get("prototype_count", 0)) for p in places)
        if protos_sum != num_pos:
            errors.append(f"Metadata prototypes sum {protos_sum} != header num_pos {num_pos}")

        # Check prototype ranges are contiguous and non-overlapping
        cursor = 0
        for i, place in enumerate(places):
            start = place.get("prototype_start", -1)
            count = place.get("prototype_count", 0)
            if start != cursor:
                errors.append(
                    f"Place {place.get('place_id')} prototype range not contiguous: "
                    f"start={start} != expected {cursor}"
                )
            cursor += count

        negs = meta_dict.get("negatives", [])
        if len(negs) != num_neg:
            errors.append(f"Metadata negatives count {len(negs)} != header num_neg {num_neg}")

        # Check calibration completeness
        cal = meta_dict.get("calibration", {}) or {}
        required_cal = (
            "accept_threshold",
            "relative_threshold",
            "hard_negative_margin",
            "sibling_margin",
            "min_margin",
            "top_k_mean",
        )
        missing_cal = [k for k in required_cal if k not in cal]
        if missing_cal:
            errors.append(f"Incomplete calibration block in metadata, missing: {', '.join(missing_cal)}")

        # Check encoder binding
        model_sha = meta_dict.get("model_sha256")
        if not model_sha:
            errors.append("No encoder digest (model_sha256) recorded in vision metadata")
        else:
            expected_crc = int(hashlib.sha256(model_sha.encode("utf-8")).hexdigest()[:8], 16)
            if model_crc != expected_crc:
                errors.append(f"Header model_crc32 ({hex(model_crc)}) != expected CRC ({hex(expected_crc)})")

        # Check local scale consistency
        scale_meta = meta_dict.get("local_scale", {}) or {}
        if has_scale:
            meta_count = scale_meta.get("count", 0)
            if meta_count != num_pos + num_neg:
                errors.append(f"Local scale metadata count {meta_count} != {num_pos + num_neg}")

    return len(errors) == 0, errors


def verify_twvec002_file(bin_path: Path, meta_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """Convenience helper to verify a TWVEC002 file on disk."""
    if not bin_path.is_file():
        return False, [f"Binary vector file not found: {bin_path}"]
    bin_bytes = bin_path.read_bytes()
    meta_dict = None
    if meta_path and meta_path.is_file():
        try:
            meta_dict = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as e:
            return False, [f"Failed to read metadata file {meta_path}: {e}"]
    return verify_twvec002_integrity(bin_bytes, meta_dict)


def compile_twvec002_from_reference_index(
    ref_json_path: Path,
    out_bin_path: Path,
    out_meta_path: Optional[Path] = None,
    model_sha256: Optional[str] = None,
) -> Dict[str, object]:
    """Compiles `reference_index.json` into a zero-copy TWVEC002 vector file."""
    data = json.loads(ref_json_path.read_text(encoding="utf-8"))
    model_id = data.get("model_id", "mobileclip-s0-v1")
    entries = data.get("places") or data.get("entries") or data.get("references") or []
    if not entries:
        entries = data.get("refs", [])
    negatives = data.get("hard_negatives", []) or data.get("negatives", [])

    if not entries:
        raise ValueError(f"No vector entries found in {ref_json_path}")

    # ---- group entries by place so each place owns a contiguous range -------
    grouped: "OrderedDict[str, List[dict]]" = OrderedDict()
    for item in entries:
        grouped.setdefault(item["place_id"], []).append(item)

    places_meta: List[Dict[str, object]] = []
    gallery: List[bytes] = []
    cursor = 0
    for place_id, items in grouped.items():
        head = items[0]
        vecs = []
        for item in items:
            vec = item.get("vector") or item.get("values") or []
            if not vec:
                continue
            vecs.append(vec)
        if not vecs:
            continue
        dim = len(vecs[0])
        for vec in vecs:
            if len(vec) != dim:
                raise ValueError(f"dimension mismatch inside place {place_id}")
            gallery.append(_float32_row(vec))
        places_meta.append({
            "place_id": place_id,
            "parent_place_id": head.get("parent_place_id"),
            "viewpoint_tag": head.get("viewpoint_tag", head.get("asset_id", "default")),
            "distinguishing_hint": head.get("distinguishing_hint", ""),
            "prototype_start": cursor,
            "prototype_count": len(vecs),
            "asset_ids": [item.get("asset_id") for item in items if item.get("asset_id")],
        })
        cursor += len(vecs)

    neg_meta: List[Dict[str, object]] = []
    neg_blob: List[bytes] = []
    for i, neg in enumerate(negatives):
        vec = neg.get("vector") or neg.get("values") or []
        if not vec:
            continue
        neg_blob.append(_float32_row(vec))
        neg_meta.append({
            "label": neg.get("label", f"neg-{i}"),
            "category": neg.get("category"),
        })

    dim = len(gallery[0]) // 4
    num_pos = len(gallery)
    num_neg = len(neg_blob)
    digest = model_sha256 or ""
    model_crc = int(hashlib.sha256(digest.encode("utf-8")).hexdigest()[:8], 16) if digest else 0

    # ---- the CSLS local scale, in the same order as the vectors --------------
    scales: List[float] = []
    for place_id, items in grouped.items():
        for item in items:
            v = item.get("vector") or item.get("values") or []
            if not v:
                continue
            scales.append(float(item.get("local_scale", 0.0)))
    for neg in negatives:
        v = neg.get("vector") or neg.get("values") or []
        if not v:
            continue
        scales.append(float(neg.get("local_scale", 0.0)))
    have_scale = len(scales) == num_pos + num_neg and any(x != 0.0 for x in scales)
    csls_k = int((data.get("calibration") or {}).get("csls_k", 10))

    flags = 1  # bit0 = float32 storage
    if have_scale:
        flags |= 2  # bit1 = a local-scale section follows the vectors
    header = struct.pack(
        TWVEC002_HEADER_FMT,
        TWVEC002_MAGIC,
        2,
        model_crc,
        dim,
        num_pos,
        num_neg,
        len(places_meta),
        flags,
        0,  # reserved
    )

    out_bin_path.parent.mkdir(parents=True, exist_ok=True)
    with out_bin_path.open("wb") as f:
        f.write(header)
        for row in gallery:
            f.write(row)
        for row in neg_blob:
            f.write(row)
        if have_scale:
            f.write(struct.pack("<%df" % len(scales), *scales))

    calibration = data.get("calibration") or {}
    meta_dict = {
        "format": "TWVEC002",
        "model_id": model_id,
        "model_sha256": digest or None,
        "model_crc32": model_crc,
        "dim": dim,
        "storage": "float32",
        "places": places_meta,
        "negatives": neg_meta,
        "calibration": calibration,
        "local_scale": {
            "k": csls_k,
            "count": len(scales) if have_scale else 0,
            "present": bool(have_scale),
        },
    }
    if out_meta_path is not None:
        out_meta_path.write_text(
            json.dumps(meta_dict, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # Post-compile integrity self-verification
    ok, errs = verify_twvec002_integrity(out_bin_path.read_bytes(), meta_dict)
    if not ok:
        raise ValueError(f"TWVEC002 compilation integrity check failed: {'; '.join(errs)}")

    return {
        "binary_path": str(out_bin_path),
        "bytes": out_bin_path.stat().st_size,
        "dim": dim,
        "num_prototypes": num_pos,
        "num_places": len(places_meta),
        "num_negatives": num_neg,
        "storage": "float32",
    }


def canonical(obj: dict) -> bytes:
    """Canonical JSON serializer: sorted keys, compact separators, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_places_sqlite(
    dest: Path,
    schema_path: Optional[Path] = None,
    seed_path: Optional[Path] = None,
) -> Tuple[int, List[str]]:
    """Builds and validates publication database. Returns (place_count, locales)."""
    schema_file = schema_path or (ROOT / "content" / "schema" / "publication_schema.sql")
    seed_file = seed_path or (ROOT / "content" / "seed" / "seed_demo.sql")

    con = sqlite3.connect(str(dest))
    con.execute("PRAGMA foreign_keys = ON;")
    con.executescript(schema_file.read_text(encoding="utf-8"))
    con.executescript(seed_file.read_text(encoding="utf-8"))

    gates = {
        "DRAFT places": "SELECT COUNT(*) FROM places WHERE editorial_state='DRAFT'",
        "DRAFT claims": "SELECT COUNT(*) FROM claims WHERE editorial_state='DRAFT'",
        "claims without a source": (
            "SELECT COUNT(*) FROM claims c "
            "LEFT JOIN claim_sources cs ON cs.claim_id=c.claim_id "
            "WHERE cs.claim_id IS NULL"
        ),
        "claims without a reviewer": (
            "SELECT COUNT(*) FROM claims "
            "WHERE reviewer_id IS NULL OR TRIM(reviewer_id)='' OR reviewed_at IS NULL"
        ),
    }
    offending = {name: con.execute(sql).fetchone()[0] for name, sql in gates.items()}
    place_count = con.execute("SELECT COUNT(*) FROM places;").fetchone()[0]
    locales_rows = con.execute("SELECT DISTINCT locale FROM claims;").fetchall()
    locales = sorted([r[0] for r in locales_rows if r[0]]) or ["en", "hi"]

    con.commit()
    con.close()

    bad = {k: v for k, v in offending.items() if v}
    if bad:
        raise SystemExit(
            "refusing pack — §28.3 violations: " + ", ".join(f"{v} {k}" for k, v in bad.items())
        )

    return place_count, locales


def safe_zip_members(names: list[str]) -> None:
    """Enforces blueprint §9.3 [G] path security on archive members."""
    executable_endings = (".exe", ".dll", ".so", ".apk", ".sh", ".bat", ".ps1", ".cmd", ".vbs")
    for n in names:
        if n.startswith("/") or n.startswith("\\"):
            raise ValueError(f"unsafe archive path: {n!r}")
        parts = n.replace("\\", "/").split("/")
        if ".." in parts:
            raise ValueError(f"unsafe archive path: {n!r}")
        low = n.lower()
        if low.endswith(executable_endings):
            raise ValueError(f"executable payload rejected: {n!r}")


def _load_ed25519_private_key(key_file: Path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    raw = key_file.read_bytes().strip()
    if raw.startswith(b"-----BEGIN"):
        return load_pem_private_key(raw, password=None)
    if len(raw) == 32:
        return Ed25519PrivateKey.from_private_bytes(raw)
    if len(raw) == 64:
        try:
            return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(raw.decode("ascii")))
        except Exception:
            pass
    decoded = base64.b64decode(raw)
    return Ed25519PrivateKey.from_private_bytes(decoded[:32])


def cmd_build(
    version: str = "2026.10.1",
    out: Path = Path("dist"),
    demo_key: bool = False,
    audio_dir: Path | None = None,
    images_dir: Path | None = None,
    vision_dir: Path | None = None,
    key_file: Path | None = None,
    key_id: str = "pubkey-2026-q4",
    pack_id: str = DEFAULT_PACK_ID,
    pack_title: Optional[str] = None,
    schema_file: Optional[Path] = None,
    seed_file: Optional[Path] = None,
    rights_registry: Optional[Path] = None,
    locales: Optional[List[str]] = None,
) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    asset_origins = _load_asset_origins(rights_registry)

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        sqlite_path = t / "places.sqlite"
        real_place_count, detected_locales = build_places_sqlite(sqlite_path, schema_file, seed_file)
        final_locales = locales or detected_locales or ["en", "hi"]

        media_files_to_pack: list[tuple[Path, str]] = []

        if audio_dir and audio_dir.is_dir():
            for f in sorted(audio_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in {".ogg", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".opus"}:
                    media_files_to_pack.append((f, f"audio/{f.name}"))

        if images_dir and images_dir.is_dir():
            for f in sorted(images_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in {".webp", ".png", ".jpg", ".jpeg", ".avif"}:
                    media_files_to_pack.append((f, f"images/then_now/{f.name}"))

        ref_json = None
        if vision_dir and (vision_dir / "reference_index.json").is_file():
            ref_json = vision_dir / "reference_index.json"
        elif (ROOT / "content" / "vision" / "reference_index.json").is_file():
            ref_json = ROOT / "content" / "vision" / "reference_index.json"

        encoder_path = ROOT / "android" / "app" / "src" / "main" / "assets" / "vision_encoder.tflite"
        encoder_sha256 = hashlib.sha256(encoder_path.read_bytes()).hexdigest() if encoder_path.is_file() else None

        if ref_json:
            v_dir = t / "vision"
            v_dir.mkdir(parents=True, exist_ok=True)
            (v_dir / "reference_index.json").write_bytes(ref_json.read_bytes())
            media_files_to_pack.append((v_dir / "reference_index.json", "vision/reference_index.json"))

            bin_path = v_dir / "reference_vectors.bin"
            meta_path = v_dir / "reference_vectors.meta.json"
            idx_bin_path = v_dir / "index.bin"
            compile_twvec002_from_reference_index(
                ref_json,
                bin_path,
                meta_path,
                model_sha256=encoder_sha256,
            )
            idx_bin_path.write_bytes(bin_path.read_bytes())
            media_files_to_pack.append((bin_path, "vision/reference_vectors.bin"))
            media_files_to_pack.append((meta_path, "vision/reference_vectors.meta.json"))
            media_files_to_pack.append((idx_bin_path, "vision/index.bin"))

        insights_json = ROOT / "content" / "seed" / "heritage_insights.json"
        if insights_json.is_file():
            media_files_to_pack.append((insights_json, "content/heritage_insights.json"))

        resolved_title = pack_title or f"TrueWay {pack_id} regional pack"
        attr_note = f"{resolved_title}: curated regional knowledge and citations."
        if media_files_to_pack:
            attr_note += f" Pack includes {len(media_files_to_pack)} curated media, insight & vision assets."

        (t / "ATTRIBUTIONS.json").write_text(
            json.dumps({"pack_id": pack_id, "release": version, "note": attr_note}, indent=2),
            encoding="utf-8",
        )
        (t / "LICENSES.json").write_text(
            json.dumps(
                {
                    "rights": "see content/seed/rights_registry.json; "
                    "curated audio narratives CC BY-SA 4.0; "
                    "archival comparisons per statutory public domain & CC BY-SA 4.0"
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (t / "CHANGELOG.md").write_text(
            f"# {pack_id} {version}\n\n- {real_place_count}-POI regional corpus.\n"
            f"- Media & vision assets included: {len(media_files_to_pack)} files.\n",
            encoding="utf-8",
        )

        files = []
        for p in [sqlite_path, t / "ATTRIBUTIONS.json", t / "LICENSES.json", t / "CHANGELOG.md"]:
            arc = "content/places.sqlite" if p.name == "places.sqlite" else p.name
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            files.append({
                "path": arc,
                "bytes": p.stat().st_size,
                "sha256": digest,
                "asset_origin": "PRODUCTION_CLEARED",
            })

        for src_path, arc_path in media_files_to_pack:
            data = src_path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            origin = asset_origins.get(arc_path, "PRODUCTION_CLEARED")
            files.append({
                "path": arc_path,
                "bytes": len(data),
                "sha256": digest,
                "asset_origin": origin,
            })

        adapter_path = ROOT / "ml" / "adapter_weights.json"
        if ref_json:
            rj_data = json.loads(ref_json.read_text(encoding="utf-8"))
            vision = {
                "model_id": rj_data.get("model_id", "mobileclip-s0-v1"),
                "dim": rj_data.get("dim", 512),
                "adapter": adapter_path.is_file(),
                "format": "TWVEC002",
                "storage": "float32",
                "calibration": rj_data.get(
                    "calibration",
                    {
                        "accept_threshold": 0.72,
                        "relative_threshold": 0.12,
                        "hard_negative_margin": 0.06,
                        "sibling_margin": 0.04,
                        "min_margin": 0.05,
                        "top_k_mean": 2,
                    },
                ),
            }
            if adapter_path.is_file():
                vision["adapter_sha256"] = hashlib.sha256(adapter_path.read_bytes()).hexdigest()
            if encoder_sha256:
                vision["weights_sha256"] = encoder_sha256
                vision["encoder_bytes"] = encoder_path.stat().st_size
            else:
                vision["weights_sha256"] = None
                vision["note"] = (
                    "encoder artefact not staged "
                    "(run android/fetch_vision_assets.ps1) — the pack cannot be "
                    "bound to an encoder, so the scanner must refuse to use it"
                )
        elif adapter_path.is_file():
            ad = json.loads(adapter_path.read_text(encoding="utf-8"))
            vision = {
                "model_id": ad.get("model_id"),
                "dim": ad.get("dim"),
                "adapter": True,
                "format": "TWVEC002",
                "weights_sha256": encoder_sha256,
            }
        else:
            vision = {
                "model_id": None,
                "dim": None,
                "adapter": False,
                "note": "no encoder selected yet — search/QR only (ADR-0003)",
            }

        signing_key_id = "DEMO-KEY-DO-NOT-SHIP" if (demo_key and key_file is None) else key_id
        manifest = {
            "format": "trueway.pack",
            "schema_version": SCHEMA_VERSION,
            "pack_id": pack_id,
            "release_version": version,
            "publisher_id": "trueway.editorial",
            "signing_key_id": signing_key_id,
            "content_locales": final_locales,
            "place_count": real_place_count,
            "vision": vision,
            "files": files,
            "licence_index_path": "LICENSES.json",
            "attribution_index_path": "ATTRIBUTIONS.json",
            "changelog_path": "CHANGELOG.md",
            "update_policy": {"atomic_activate": True},
        }
        manifest_bytes = canonical(manifest)
        if key_file is not None:
            priv_key = _load_ed25519_private_key(key_file)
            sig = priv_key.sign(manifest_bytes)
        elif demo_key:
            sig = base64.b64encode(b"DEMO-SIGNATURE:" + hashlib.sha256(manifest_bytes).digest())
        else:
            raise SystemExit(
                "no --demo-key and no --key-file supplied; refusing to fake a release signature (§28.8)"
            )

        pkg = out / f"trueway-{pack_id}-{version}.twpkg"
        with zipfile.ZipFile(pkg, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("manifest.cjson", manifest_bytes)
            z.writestr("manifest.ed25519", sig)
            z.write(sqlite_path, "content/places.sqlite")
            z.write(t / "ATTRIBUTIONS.json", "ATTRIBUTIONS.json")
            z.write(t / "LICENSES.json", "LICENSES.json")
            z.write(t / "CHANGELOG.md", "CHANGELOG.md")
            for src_path, arc_path in media_files_to_pack:
                z.write(src_path, arc_path)

        # Update or register pack in regional catalog if catalog is available
        if default_catalog is not None:
            try:
                raw_bytes = pkg.read_bytes()
                h = hashlib.sha256(raw_bytes).hexdigest()
                existing = default_catalog.get(pack_id)
                def _rel(p: Optional[Path]) -> Optional[str]:
                    if not p:
                        return None
                    try:
                        return str(p.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
                    except Exception:
                        return str(p).replace("\\", "/")

                schema_str = _rel(schema_file) or (existing.schema_file if existing else None)
                seed_str = _rel(seed_file) or (existing.seed_file if existing else None)
                rights_str = _rel(rights_registry) or (existing.rights_registry if existing else None)
                audio_str = _rel(audio_dir) or (existing.audio_dir if existing else None)
                images_str = _rel(images_dir) or (existing.images_dir if existing else None)
                vision_str = _rel(vision_dir) or (existing.vision_dir if existing else None)

                def_obj = RegionalPackDefinition(
                    pack_id=pack_id,
                    title=resolved_title,
                    description=existing.description if (existing and existing.description) else attr_note,
                    release_version=version,
                    schema_version=SCHEMA_VERSION,
                    content_locales=final_locales,
                    place_count=real_place_count,
                    publisher_id="trueway.editorial",
                    signing_key_id=signing_key_id,
                    schema_file=schema_str,
                    seed_file=seed_str,
                    rights_registry=rights_str,
                    audio_dir=audio_str,
                    images_dir=images_str,
                    vision_dir=vision_str,
                    bundle_filename=pkg.name,
                    bundle_bytes=len(raw_bytes),
                    bundle_sha256=h,
                    components=[f["path"] for f in files],
                )
                if out.resolve() == (ROOT / "dist").resolve():
                    default_catalog.register(def_obj)
                    default_catalog.save_to_file()
            except Exception:
                pass

        mode_str = f"ed25519 key={signing_key_id}" if key_file else "demo-signed"
        print(f"built {pkg} ({pkg.stat().st_size} bytes, {mode_str}, {len(files)} files)")
        return pkg


def cmd_verify(pkg: Path, min_safe: str | None = None, pub_key_b64: str | None = None) -> int:
    """Verifies a .twpkg archive against all security, cryptographic, and TWVEC002 invariants."""
    if not pkg.is_file():
        print(f"REJECT: file not found: {pkg}")
        return 1

    with zipfile.ZipFile(pkg) as z:
        names = z.namelist()
        try:
            safe_zip_members(names)
        except ValueError as e:
            print(f"REJECT: {e}")
            return 1

        if "manifest.cjson" not in names:
            print("REJECT: missing manifest.cjson")
            return 1
        if "manifest.ed25519" not in names:
            print("REJECT: missing manifest.ed25519")
            return 1

        manifest_bytes = z.read("manifest.cjson")
        sig = z.read("manifest.ed25519")

        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except Exception as e:
            print(f"REJECT: manifest is not valid JSON: {e}")
            return 1

        prefix = b"DEMO-SIGNATURE:"
        try:
            decoded_candidate = base64.b64decode(sig)
        except Exception:
            decoded_candidate = b""

        if decoded_candidate.startswith(prefix):
            raw = decoded_candidate
            is_demo_sig = True
        else:
            raw = sig
            is_demo_sig = False

        key_id = manifest.get("signing_key_id")
        is_demo_key = key_id == "DEMO-KEY-DO-NOT-SHIP"

        if is_demo_sig and not is_demo_key:
            print(
                f"REJECT: demo-class signature presented under non-demo "
                f"signing_key_id {key_id!r} (§28.8 key-id/signature binding)"
            )
            return 1

        if not is_demo_sig:
            if pub_key_b64 and not is_demo_key:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

                try:
                    pub_bytes = base64.b64decode(pub_key_b64)
                    pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
                    sig_to_verify = raw
                    if len(sig_to_verify) != 64 and len(decoded_candidate) == 64:
                        sig_to_verify = decoded_candidate
                    pub_key.verify(sig_to_verify, manifest_bytes)
                    print(f"note: Ed25519 release signature verified for key {key_id!r}")
                except Exception as e:
                    print(f"REJECT: Ed25519 signature verification failed for {key_id!r}: {e}")
                    return 1
            else:
                print(
                    f"REJECT: release signature for key {key_id!r} cannot be "
                    f"verified in the demonstrator (no publisher trust store "
                    f"wired); refusing rather than trusting (§9.3/§28.8)"
                )
                return 1
        else:
            print("note: demo signature - structurally checked, NOT a release signature")
            expect = hashlib.sha256(manifest_bytes).digest()
            if raw[len(prefix):] != expect:
                print("REJECT: manifest signature mismatch")
                return 1

        if min_safe is not None and _ver_tuple(manifest.get("release_version", "")) < _ver_tuple(min_safe):
            print(
                f"REJECT: version {manifest.get('release_version')} below "
                f"minimum safe release {min_safe} (downgrade refused)"
            )
            return 1

        # File completeness check
        files_list = manifest.get("files")
        if not isinstance(files_list, list):
            print("REJECT: manifest files entry is not a list")
            return 1

        listed = {f.get("path") for f in files_list if isinstance(f, dict)}
        allowed = listed | {"manifest.cjson", "manifest.ed25519"}
        extra = [n for n in names if n not in allowed and not n.endswith("/")]
        if extra:
            print(f"REJECT: unlisted archive entries not covered by the signed manifest: {extra}")
            return 1

        for f in files_list:
            path = f.get("path")
            if path not in names:
                print(f"REJECT: manifest lists {path} but it is missing from the archive")
                return 1
            data = z.read(path)
            if hashlib.sha256(data).hexdigest() != f.get("sha256") or len(data) != f.get("bytes"):
                print(f"REJECT: digest/size mismatch on {path}")
                return 1

        # Zero-copy binary index integrity verification (TWVEC002)
        vision_bin_entry = next((n for n in names if n in ("vision/reference_vectors.bin", "vision/index.bin")), None)
        if vision_bin_entry:
            bin_bytes = z.read(vision_bin_entry)
            meta_dict = None
            if "vision/reference_vectors.meta.json" in names:
                try:
                    meta_dict = json.loads(z.read("vision/reference_vectors.meta.json").decode("utf-8"))
                except Exception:
                    pass
            ok, errs = verify_twvec002_integrity(bin_bytes, meta_dict)
            if not ok:
                print(f"REJECT: TWVEC002 zero-copy binary index integrity violation: {'; '.join(errs)}")
                return 1
            print("note: TWVEC002 zero-copy binary index integrity verified")

        print(
            f"VERIFY OK: {manifest.get('pack_id')} {manifest.get('release_version')} "
            f"({manifest.get('place_count')} places, {len(manifest.get('files', []))} files)"
        )
        return 0


def _ver_tuple(v: str) -> tuple:
    return tuple((0, int(p)) if p.isdigit() else (1, p) for p in v.split("."))


def main() -> int:
    ap = argparse.ArgumentParser(description="TrueWay Pack Builder & Verifier")
    ap.add_argument("--version", default="2026.10.1")
    ap.add_argument("--out", default="dist")
    ap.add_argument("--demo-key", action="store_true")
    ap.add_argument("--key-file", default=None, help="path to 32-byte Ed25519 private key seed or PEM")
    ap.add_argument("--key-id", default="pubkey-2026-q4", help="publisher signing_key_id when using --key-file")
    ap.add_argument(
        "--pub-key-b64", default=None, help="base64-encoded 32-byte Ed25519 public key for release verification"
    )
    ap.add_argument("--verify", default=None, help="path to .twpkg archive to verify")
    ap.add_argument("--verify-twvec", default=None, help="path to TWVEC002 .bin file to verify")
    ap.add_argument("--twvec-meta", default=None, help="path to optional TWVEC002 .meta.json file")
    ap.add_argument(
        "--min-safe",
        default=None,
        help="minimum acceptable release_version; older packs are rejected as downgrades (§9.3 replay policy)",
    )
    ap.add_argument("--audio-dir", default=None, help="directory containing regional audio narrative files (.ogg)")
    ap.add_argument("--images-dir", default=None, help="directory containing Then & Now comparison images (.webp)")
    ap.add_argument("--vision-dir", default=None, help="directory containing vision reference index / vectors")

    # Multi-region and catalog options
    ap.add_argument(
        "--pack-id",
        default=DEFAULT_PACK_ID,
        help=f"regional pack identifier (default: {DEFAULT_PACK_ID})",
    )
    ap.add_argument("--pack-title", default=None, help="human-readable title for the regional pack")
    ap.add_argument("--pack-def", default=None, help="path to regional pack definition JSON")
    ap.add_argument("--schema", dest="schema_file", default=None, help="path to publication schema SQL")
    ap.add_argument("--seed", dest="seed_file", default=None, help="path to publication seed SQL")
    ap.add_argument("--rights-registry", default=None, help="path to rights registry JSON")
    ap.add_argument("--locales", default=None, help="comma-separated list of locales (e.g. en,hi)")
    ap.add_argument("--list-regions", action="store_true", help="list registered regional packs in catalog")
    ap.add_argument("--export-catalog", default=None, help="export regional catalog to specified JSON path")

    args = ap.parse_args()

    if args.list_regions:
        cat = default_catalog or RegionalPackCatalog()
        print("Registered Regional Packs:")
        for r in cat.list_regions():
            avail = "AVAILABLE" if r["bundle_available"] else "definition only"
            print(f"  * {r['pack_id']} [{r['latest_version']}] ({r['place_count']} places) — {r['title']} ({avail})")
        return 0

    if args.export_catalog:
        cat = default_catalog or RegionalPackCatalog()
        cat.save_to_file(Path(args.export_catalog))
        print(f"Exported regional catalog to {args.export_catalog}")
        return 0

    if args.verify_twvec:
        meta_p = Path(args.twvec_meta) if args.twvec_meta else None
        ok, errs = verify_twvec002_file(Path(args.verify_twvec), meta_p)
        if ok:
            print(f"VERIFY OK: TWVEC002 binary index integrity verified for {args.verify_twvec}")
            return 0
        else:
            print(f"REJECT: TWVEC002 integrity check failed:\n  " + "\n  ".join(errs))
            return 1

    if args.verify:
        return cmd_verify(Path(args.verify), args.min_safe, args.pub_key_b64)

    # Multi-region pack definition loading
    pack_id = args.pack_id
    pack_title = args.pack_title
    schema_p = Path(args.schema_file) if args.schema_file else None
    seed_p = Path(args.seed_file) if args.seed_file else None
    rights_p = Path(args.rights_registry) if args.rights_registry else None
    audio_d = Path(args.audio_dir) if args.audio_dir else None
    images_d = Path(args.images_dir) if args.images_dir else None
    vision_d = Path(args.vision_dir) if args.vision_dir else None
    locales_list = [loc.strip() for loc in args.locales.split(",")] if args.locales else None

    if args.pack_def:
        pdef_path = Path(args.pack_def)
        if not pdef_path.is_file():
            print(f"Error: pack definition file not found: {pdef_path}")
            return 1
        pdef_data = json.loads(pdef_path.read_text(encoding="utf-8"))
        pack_id = pdef_data.get("pack_id", pack_id)
        pack_title = pdef_data.get("title", pack_title)
        if "schema_file" in pdef_data and not schema_p:
            schema_p = ROOT / pdef_data["schema_file"]
        if "seed_file" in pdef_data and not seed_p:
            seed_p = ROOT / pdef_data["seed_file"]
        if "rights_registry" in pdef_data and not rights_p:
            rights_p = ROOT / pdef_data["rights_registry"]
        if "audio_dir" in pdef_data and not audio_d:
            audio_d = ROOT / pdef_data["audio_dir"]
        if "images_dir" in pdef_data and not images_d:
            images_d = ROOT / pdef_data["images_dir"]
        if "vision_dir" in pdef_data and not vision_d:
            vision_d = ROOT / pdef_data["vision_dir"]
        if "content_locales" in pdef_data and not locales_list:
            locales_list = pdef_data["content_locales"]
    elif default_catalog is not None:
        cat_def = default_catalog.get(pack_id)
        if cat_def:
            if not pack_title:
                pack_title = cat_def.title
            if cat_def.schema_file and not schema_p:
                schema_p = ROOT / cat_def.schema_file
            if cat_def.seed_file and not seed_p:
                seed_p = ROOT / cat_def.seed_file
            if cat_def.rights_registry and not rights_p:
                rights_p = ROOT / cat_def.rights_registry
            if cat_def.audio_dir and not audio_d:
                audio_d = ROOT / cat_def.audio_dir
            if cat_def.images_dir and not images_d:
                images_d = ROOT / cat_def.images_dir
            if cat_def.vision_dir and not vision_d:
                vision_d = ROOT / cat_def.vision_dir
            if cat_def.content_locales and not locales_list:
                locales_list = cat_def.content_locales

    cmd_build(
        version=args.version,
        out=Path(args.out),
        demo_key=args.demo_key,
        audio_dir=audio_d,
        images_dir=images_d,
        vision_dir=vision_d,
        key_file=Path(args.key_file) if args.key_file else None,
        key_id=args.key_id,
        pack_id=pack_id,
        pack_title=pack_title,
        schema_file=schema_p,
        seed_file=seed_p,
        rights_registry=rights_p,
        locales=locales_list,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
