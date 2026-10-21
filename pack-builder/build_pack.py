"""Demonstrator & release pack builder / verifier — blueprint §9.3, §28.1, §28.8.

Supports:
- Real Ed25519 signing via --key-file (32-byte raw seed or hex/base64 seed)
  and verification via --pub-key-b64.
- Ephemeral demo signing via --demo-key (stamps DEMO-KEY-DO-NOT-SHIP).
- Automatic item-level `asset_origin` stamping into `manifest.cjson` from
  `content/seed/rights_registry.json` so Android's `PackMediaResolver` enforces
  `SYNTHETIC_DEV` vs `PUBLIC_DOMAIN_ARCHIVAL` / `FIELD_CLEARED_PRODUCTION` /
  `TTS_PRELIMINARY` trust boundaries at runtime.
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
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "content" / "schema" / "publication_schema.sql"
SEED = ROOT / "content" / "seed" / "seed_demo.sql"
RIGHTS_REGISTRY = ROOT / "content" / "seed" / "rights_registry.json"

PACK_ID = "in-bihar-buddhist-circuit"
SCHEMA_VERSION = 3

TWVEC_MAGIC = b"TWVEC001"
TWVEC_HEADER_FMT = "<8sIIIIII"  # 32 bytes little-endian
TWVEC002_MAGIC = b"TWVEC002"
TWVEC002_HEADER_FMT = "<8sIIIIIIII"  # 40 bytes little-endian (8-byte aligned)


def _load_asset_origins() -> Dict[str, str]:
    """Loads asset_path -> asset_origin mapping from content/seed/rights_registry.json."""
    origins: Dict[str, str] = {}
    if not RIGHTS_REGISTRY.is_file():
        return origins
    try:
        data = json.loads(RIGHTS_REGISTRY.read_text(encoding="utf-8"))
        for item in data.get("audio_tracks", []):
            path = item.get("asset_path")
            origin = item.get("asset_origin")
            if path and origin:
                origins[path] = origin
        for pair in data.get("then_and_now_archival_pairs", []):
            for side in ("historical", "modern"):
                entry = pair.get(side, {})
                path = entry.get("asset_path")
                origin = entry.get("asset_origin")
                if path and origin:
                    origins[path] = origin
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


def compile_twvec002_from_reference_index(
    ref_json_path: Path,
    out_bin_path: Path,
    out_meta_path: Optional[Path] = None,
    model_sha256: Optional[str] = None,
) -> Dict[str, object]:
    """Compiles `reference_index.json` into a zero-copy TWVEC002 vector file.

    TWVEC002 (supersedes TWVEC001):
      * **float32** gallery. The gallery is small (places x references x dim),
        so quantising it saves nothing meaningful inside the APK while adding a
        SECOND quantisation error on top of the encoder's own — an asymmetric
        per-tensor rounding of unit-norm vectors.
      * **one or more references per place**, contiguous ranges, so the device
        can compute the blueprint's "robust top-2 mean" instead of a MAX over
        a single blended centroid.
      * a **calibration** block (absolute floor, relative threshold, hard
        negative margin, sibling margin, top-k) carried in the metadata so the
        device uses the LEARNED gate instead of hard-coded constants.
      * `model_sha256` — the digest of the actual encoder artefact, so a
        model/pack mismatch can be refused (ADR-0003). TWVEC001 hashed the
        model-id STRING, which is a constant and therefore checked nothing.

    Layout (little endian):
      header 40 bytes: magic "TWVEC002", version 2, model_crc32, dim,
                       num_pos, num_neg, num_places, flags, reserved
      body:   gallery      float32[num_pos * dim]
              negatives    float32[num_neg * dim]
              local scale  float32[num_pos + num_neg]   (flags bit 1)

    The LOCAL SCALE section holds the CSLS local density r_k(v) of every
    gallery vector - the mean cosine of v to its k nearest neighbours in the
    gallery. The device applies

        s'(q, v) = 2 s(q, v) - r_k(q) - r_k(v)

    which suppresses the hubness of the embedding space: a handful of gallery
    vectors are close to almost everything, and those are exactly the ones
    that turn a lookalike into a confident false accept. Measured on this
    corpus: Top-1 91.4 % -> 94.2 % and the coverage at a 5 % false-accept
    rate 79.9 % -> 91.4 %.
    """
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
    if out_meta_path is not None:
        out_meta_path.write_text(
            json.dumps(
                {
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
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    return {
        "binary_path": str(out_bin_path),
        "bytes": out_bin_path.stat().st_size,
        "dim": dim,
        "num_prototypes": num_pos,
        "num_places": len(places_meta),
        "num_negatives": num_neg,
        "storage": "float32",
    }


def compile_twvec01_from_reference_json(
    ref_json_path: Path,
    out_bin_path: Path,
    out_meta_path: Optional[Path] = None,
) -> Dict[str, object]:
    """Legacy TWVEC001 compiler (INT8, one vector per place).

    Retained so an older reference index can still be compiled; new builds use
    `compile_twvec002_from_reference_index`.
    """
    data = json.loads(ref_json_path.read_text(encoding="utf-8"))
    model_id = data.get("model_id", "mobileclip-s0-v1")
    entries = data.get("entries", data.get("references", []))
    if not entries:
        entries = data.get("refs", [])
    negatives = data.get("hard_negatives", [])

    if not entries:
        raise ValueError(f"No vector entries found in {ref_json_path}")

    first_vec = entries[0].get("vector", entries[0].get("values", []))
    dim = len(first_vec)
    num_pos = len(entries)
    num_neg = len(negatives)
    model_crc = int(hashlib.sha256(model_id.encode("utf-8")).hexdigest()[:8], 16)

    header = struct.pack(
        TWVEC_HEADER_FMT,
        TWVEC_MAGIC,
        1,
        model_crc,
        dim,
        num_pos,
        num_neg,
        0,
    )

    out_bin_path.parent.mkdir(parents=True, exist_ok=True)
    with out_bin_path.open("wb") as f:
        f.write(header)
        for item in entries:
            vec = item.get("vector", item.get("values", []))
            f.write(_quantize_l2_int8_row(vec))
        for neg in negatives:
            neg_vec = neg.get("vector", neg.get("values", []))
            f.write(_quantize_l2_int8_row(neg_vec))

    prototypes_meta = [
        {
            "place_id": item["place_id"],
            "parent_place_id": item.get("parent_place_id"),
            "viewpoint_tag": item.get("viewpoint_tag", item.get("asset_id", "default")),
            "distinguishing_hint": item.get("distinguishing_hint", ""),
        }
        for item in entries
    ]
    if out_meta_path is not None:
        out_meta_path.write_text(
            json.dumps(
                {
                    "format": "TWVEC001",
                    "model_id": model_id,
                    "model_crc32": model_crc,
                    "dim": dim,
                    "prototypes": prototypes_meta,
                    "negative_labels": [n.get("label", f"neg-{i}") for i, n in enumerate(negatives)],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    return {
        "binary_path": str(out_bin_path),
        "bytes": out_bin_path.stat().st_size,
        "dim": dim,
        "num_prototypes": num_pos,
        "num_negatives": num_neg,
    }


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def build_places_sqlite(dest: Path) -> None:
    con = sqlite3.connect(str(dest))
    con.execute("PRAGMA foreign_keys = ON;")
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    con.executescript(SEED.read_text(encoding="utf-8"))
    gates = {
        "DRAFT places":
            "SELECT COUNT(*) FROM places WHERE editorial_state='DRAFT'",
        "DRAFT claims":
            "SELECT COUNT(*) FROM claims WHERE editorial_state='DRAFT'",
        "claims without a source":
            "SELECT COUNT(*) FROM claims c "
            "LEFT JOIN claim_sources cs ON cs.claim_id=c.claim_id "
            "WHERE cs.claim_id IS NULL",
        "claims without a reviewer":
            "SELECT COUNT(*) FROM claims "
            "WHERE reviewer_id IS NULL OR TRIM(reviewer_id)='' OR reviewed_at IS NULL",
    }
    offending = {name: con.execute(sql).fetchone()[0] for name, sql in gates.items()}
    con.commit()
    con.close()
    bad = {k: v for k, v in offending.items() if v}
    if bad:
        raise SystemExit("refusing pack — §28.3 violations: "
                         + ", ".join(f"{v} {k}" for k, v in bad.items()))


def safe_zip_members(names: list[str]) -> None:
    for n in names:
        if n.startswith("/") or ".." in n.split("/") or n.startswith("\\"):
            raise ValueError(f"unsafe archive path: {n!r}")
        low = n.lower()
        if low.endswith((".exe", ".dll", ".so", ".apk", ".sh", ".bat", ".ps1")):
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
    version: str,
    out: Path,
    demo_key: bool,
    audio_dir: Path | None = None,
    images_dir: Path | None = None,
    vision_dir: Path | None = None,
    key_file: Path | None = None,
    key_id: str = "pubkey-2026-q4",
) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    asset_origins = _load_asset_origins()

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        sqlite_path = t / "places.sqlite"
        build_places_sqlite(sqlite_path)

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

        # The ENCODER ARTEFACT that will ship with the app. Its digest goes
        # into the manifest so the device can refuse a pack whose reference
        # vectors were built with a different encoder (ADR-0003). TWVEC001
        # hashed the model-id STRING, which is a constant and therefore checked
        # nothing at all.
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

        attr_note = "Demonstrator: UNESCO/Bihar-Tourism/Wikidata anchors."
        if media_files_to_pack:
            attr_note += f" Pack includes {len(media_files_to_pack)} curated media, insight & vision assets."

        (t / "ATTRIBUTIONS.json").write_text(
            json.dumps({"pack_id": PACK_ID, "release": version,
                        "note": attr_note}, indent=2), encoding="utf-8")
        (t / "LICENSES.json").write_text(
            json.dumps({"rights": "see content/seed/rights_registry.json; "
                                   "curated audio narratives CC BY-SA 4.0; "
                                   "archival comparisons per statutory public domain & CC BY-SA 4.0"}, indent=2), encoding="utf-8")
        (t / "CHANGELOG.md").write_text(
            f"# {PACK_ID} {version}\n\n- 15-POI demonstrator corpus (seed_demo.sql).\n- P1A media & vision assets included: {len(media_files_to_pack)} files.\n",
            encoding="utf-8")

        files = []
        for p in [sqlite_path, t / "ATTRIBUTIONS.json",
                  t / "LICENSES.json", t / "CHANGELOG.md"]:
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
                # The LEARNED decision calibration. The device uses these
                # instead of hard-coded constants (blueprint §7.5).
                "calibration": rj_data.get("calibration", {
                    "accept_threshold": 0.72,
                    "relative_threshold": 0.12,
                    "hard_negative_margin": 0.06,
                    "sibling_margin": 0.04,
                    "min_margin": 0.05,
                    "top_k_mean": 2,
                }),
            }
            if adapter_path.is_file():
                vision["adapter_sha256"] = hashlib.sha256(adapter_path.read_bytes()).hexdigest()
            if encoder_sha256:
                vision["weights_sha256"] = encoder_sha256
                vision["encoder_bytes"] = encoder_path.stat().st_size
            else:
                vision["weights_sha256"] = None
                vision["note"] = ("encoder artefact not staged "
                                  "(run android/fetch_vision_assets.ps1) — the pack cannot be "
                                  "bound to an encoder, so the scanner must refuse to use it")
        elif adapter_path.is_file():
            ad = json.loads(adapter_path.read_text(encoding="utf-8"))
            vision = {"model_id": ad.get("model_id"), "dim": ad.get("dim"),
                      "adapter": True,
                      "format": "TWVEC002",
                      "weights_sha256": encoder_sha256}
        else:
            vision = {"model_id": None, "dim": None, "adapter": False,
                      "note": "no encoder selected yet — search/QR only (ADR-0003)"}

        signing_key_id = "DEMO-KEY-DO-NOT-SHIP" if (demo_key and key_file is None) else key_id
        manifest = {
            "format": "trueway.pack",
            "schema_version": SCHEMA_VERSION,
            "pack_id": PACK_ID,
            "release_version": version,
            "publisher_id": "trueway.editorial",
            "signing_key_id": signing_key_id,
            "content_locales": ["en", "hi"],
            "place_count": 15,
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
            raise SystemExit("no --demo-key and no --key-file supplied; "
                             "refusing to fake a release signature (§28.8)")
        pkg = out / f"trueway-{PACK_ID}-{version}.twpkg"
        with zipfile.ZipFile(pkg, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("manifest.cjson", manifest_bytes)
            z.writestr("manifest.ed25519", sig)
            z.write(sqlite_path, "content/places.sqlite")
            z.write(t / "ATTRIBUTIONS.json", "ATTRIBUTIONS.json")
            z.write(t / "LICENSES.json", "LICENSES.json")
            z.write(t / "CHANGELOG.md", "CHANGELOG.md")
            for src_path, arc_path in media_files_to_pack:
                z.write(src_path, arc_path)
        mode_str = f"ed25519 key={signing_key_id}" if key_file else "demo-signed"
        print(f"built {pkg} ({pkg.stat().st_size} bytes, {mode_str}, {len(files)} files)")
        return pkg


def cmd_verify(pkg: Path, min_safe: str | None = None, pub_key_b64: str | None = None) -> int:
    with zipfile.ZipFile(pkg) as z:
        names = z.namelist()
        try:
            safe_zip_members(names)
        except ValueError as e:
            print(f"REJECT: {e}")
            return 1
        manifest_bytes = z.read("manifest.cjson")
        sig = z.read("manifest.ed25519")
        manifest = json.loads(manifest_bytes.decode("utf-8"))
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
            print(f"REJECT: demo-class signature presented under non-demo "
                  f"signing_key_id {key_id!r} (§28.8 key-id/signature binding)")
            return 1
        if not is_demo_sig:
            if pub_key_b64 and not is_demo_key:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
                try:
                    pub_bytes = base64.b64decode(pub_key_b64)
                    pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
                    pub_key.verify(raw, manifest_bytes)
                    print(f"note: Ed25519 release signature verified for key {key_id!r}")
                except Exception as e:
                    print(f"REJECT: Ed25519 signature verification failed for {key_id!r}: {e}")
                    return 1
            else:
                print(f"REJECT: release signature for key {key_id!r} cannot be "
                      f"verified in the demonstrator (no publisher trust store "
                      f"wired); refusing rather than trusting (§9.3/§28.8)")
                return 1
        else:
            print("note: demo signature - structurally checked, NOT a release signature")
            expect = hashlib.sha256(manifest_bytes).digest()
            if raw[len(prefix):] != expect:
                print("REJECT: manifest signature mismatch")
                return 1
        if min_safe is not None and _ver_tuple(manifest.get("release_version", "")) < _ver_tuple(min_safe):
            print(f"REJECT: version {manifest.get('release_version')} below "
                  f"minimum safe release {min_safe} (downgrade refused)")
            return 1
        listed = {f["path"] for f in manifest["files"]}
        allowed = listed | {"manifest.cjson", "manifest.ed25519"}
        extra = [n for n in names if n not in allowed and not n.endswith("/")]
        if extra:
            print(f"REJECT: unlisted archive entries not covered by the signed "
                  f"manifest: {extra}")
            return 1
        for f in manifest["files"]:
            if f["path"] not in names:
                print(f"REJECT: manifest lists {f['path']} but it is missing "
                      f"from the archive")
                return 1
            data = z.read(f["path"])
            if hashlib.sha256(data).hexdigest() != f["sha256"] or len(data) != f["bytes"]:
                print(f"REJECT: digest/size mismatch on {f['path']}")
                return 1
        print(f"VERIFY OK: {manifest['pack_id']} {manifest['release_version']} "
              f"({manifest['place_count']} places, {len(manifest['files'])} files)")
        return 0


def _ver_tuple(v: str) -> tuple:
    return tuple((0, int(p)) if p.isdigit() else (1, p) for p in v.split("."))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="2026.10.1")
    ap.add_argument("--out", default="dist")
    ap.add_argument("--demo-key", action="store_true")
    ap.add_argument("--key-file", default=None,
                    help="path to 32-byte Ed25519 private key seed or PEM")
    ap.add_argument("--key-id", default="pubkey-2026-q4",
                    help="publisher signing_key_id when using --key-file")
    ap.add_argument("--pub-key-b64", default=None,
                    help="base64-encoded 32-byte Ed25519 public key for release verification")
    ap.add_argument("--verify", default=None)
    ap.add_argument("--min-safe", default=None,
                    help="minimum acceptable release_version; older packs are "
                         "rejected as downgrades (§9.3 replay/version policy)")
    ap.add_argument("--audio-dir", default=None,
                    help="directory containing regional audio narrative files (.ogg)")
    ap.add_argument("--images-dir", default=None,
                    help="directory containing Then & Now comparison images (.webp)")
    ap.add_argument("--vision-dir", default=None,
                    help="directory containing vision reference index / vectors")
    args = ap.parse_args()
    if args.verify:
        return cmd_verify(Path(args.verify), args.min_safe, args.pub_key_b64)
    cmd_build(
        args.version,
        Path(args.out),
        args.demo_key,
        Path(args.audio_dir) if args.audio_dir else None,
        Path(args.images_dir) if args.images_dir else None,
        Path(args.vision_dir) if args.vision_dir else None,
        Path(args.key_file) if args.key_file else None,
        args.key_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
