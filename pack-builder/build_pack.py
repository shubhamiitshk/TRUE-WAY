"""Demonstrator pack builder / verifier — blueprint §9.3, §28.1, §28.8.

Stdlib only. Real Ed25519 signing plugs in via --key-file (raw 32-byte
seed read from a protected signing environment, never committed); without
it, --demo-key stamps DEMO-KEY-DO-NOT-SHIP so output is unshippable.
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
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "content" / "schema" / "publication_schema.sql"
SEED = ROOT / "content" / "seed" / "seed_demo.sql"

PACK_ID = "in-bihar-buddhist-circuit"
SCHEMA_VERSION = 3

TWVEC_MAGIC = b"TWVEC001"
TWVEC_HEADER_FMT = "<8sIIIIII"  # 32 bytes little-endian


def _quantize_l2_int8_row(vec: List[float]) -> bytes:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return bytes(
        (max(-127, min(127, int(round((v / norm) * 127.0)))) & 0xFF)
        for v in vec
    )


def compile_twvec01_from_reference_json(
    ref_json_path: Path,
    out_bin_path: Path,
    out_meta_path: Optional[Path] = None,
) -> Dict[str, object]:
    """Compiles `reference_index.json` into a zero-copy TWVEC001 binary file."""
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
    # Publication rules: the shippable pack carries REVIEWED/PUBLISHED, fully
    # sourced + reviewed content only (§28.3). Mirror content/seed/validate_seed.py
    # so the artifact builder is as strict as the CI gate — not weaker.
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


def cmd_build(
    version: str,
    out: Path,
    demo_key: bool,
    audio_dir: Path | None = None,
    images_dir: Path | None = None,
    vision_dir: Path | None = None,
) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        sqlite_path = t / "places.sqlite"
        build_places_sqlite(sqlite_path)

        media_files_to_pack: list[tuple[Path, str]] = []

        # Collect audio assets if directory specified
        if audio_dir and audio_dir.is_dir():
            for f in sorted(audio_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in {".ogg", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".opus"}:
                    media_files_to_pack.append((f, f"audio/{f.name}"))

        # Collect Then & Now images if directory specified
        if images_dir and images_dir.is_dir():
            for f in sorted(images_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in {".webp", ".png", ".jpg", ".jpeg", ".avif"}:
                    media_files_to_pack.append((f, f"images/then_now/{f.name}"))

        # Collect vision assets and compile TWVEC001 binary index
        ref_json = None
        if vision_dir and (vision_dir / "reference_index.json").is_file():
            ref_json = vision_dir / "reference_index.json"
        elif (ROOT / "content" / "vision" / "reference_index.json").is_file():
            ref_json = ROOT / "content" / "vision" / "reference_index.json"

        if ref_json:
            v_dir = t / "vision"
            v_dir.mkdir(parents=True, exist_ok=True)
            (v_dir / "reference_index.json").write_bytes(ref_json.read_bytes())
            media_files_to_pack.append((v_dir / "reference_index.json", "vision/reference_index.json"))

            bin_path = v_dir / "reference_vectors.bin"
            meta_path = v_dir / "reference_vectors.meta.json"
            idx_bin_path = v_dir / "index.bin"
            compile_twvec01_from_reference_json(
                ref_json,
                bin_path,
                meta_path,
            )
            idx_bin_path.write_bytes(bin_path.read_bytes())
            media_files_to_pack.append((bin_path, "vision/reference_vectors.bin"))
            media_files_to_pack.append((meta_path, "vision/reference_vectors.meta.json"))
            media_files_to_pack.append((idx_bin_path, "vision/index.bin"))

        attr_note = "Demonstrator: UNESCO/Bihar-Tourism/Wikidata anchors."
        if media_files_to_pack:
            attr_note += f" Pack includes {len(media_files_to_pack)} curated media & vision assets."

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
            files.append({"path": arc, "bytes": p.stat().st_size, "sha256": digest})

        for src_path, arc_path in media_files_to_pack:
            data = src_path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            files.append({"path": arc_path, "bytes": len(data), "sha256": digest})

        # Vision contract (ADR-0003): encoder identity + adapted dim travel WITH
        # the pack so the app can refuse a mismatched model instead of
        # mis-scoring.
        adapter_path = ROOT / "ml" / "adapter_weights.json"
        if ref_json:
            rj_data = json.loads(ref_json.read_text(encoding="utf-8"))
            vision = {
                "model_id": rj_data.get("model_id", "mobileclip-s0-v1"),
                "dim": rj_data.get("dim", 512),
                "adapter": adapter_path.is_file(),
                "format": "TWVEC001",
                "calibration": rj_data.get("calibration", {"accept_threshold": 0.72, "min_margin": 0.05}),
            }
            if adapter_path.is_file():
                vision["weights_sha256"] = hashlib.sha256(adapter_path.read_bytes()).hexdigest()
        elif adapter_path.is_file():
            ad = json.loads(adapter_path.read_text(encoding="utf-8"))
            vision = {"model_id": ad.get("model_id"), "dim": ad.get("dim"),
                      "adapter": True,
                      "weights_sha256": hashlib.sha256(
                          adapter_path.read_bytes()).hexdigest()}
        else:
            vision = {"model_id": None, "dim": None, "adapter": False,
                      "note": "no encoder selected yet — search/QR only (ADR-0003)"}

        manifest = {
            "format": "trueway.pack",
            "schema_version": SCHEMA_VERSION,
            "pack_id": PACK_ID,
            "release_version": version,
            "publisher_id": "trueway.editorial",
            "signing_key_id": "DEMO-KEY-DO-NOT-SHIP" if demo_key else "pubkey-2026-q4",
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
        if demo_key:
            sig = base64.b64encode(b"DEMO-SIGNATURE:" + hashlib.sha256(manifest_bytes).digest())
        else:
            raise SystemExit("no --demo-key and no HSM wiring in the demonstrator; "
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
        print(f"built {pkg} ({pkg.stat().st_size} bytes, demo-signed, {len(files)} files)")
        return pkg


def cmd_verify(pkg: Path, min_safe: str | None = None) -> int:
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
        raw = base64.b64decode(sig)
        prefix = b"DEMO-SIGNATURE:"
        is_demo_sig = raw.startswith(prefix)
        key_id = manifest.get("signing_key_id")
        is_demo_key = key_id == "DEMO-KEY-DO-NOT-SHIP"
        # Bind key-id class to signature class BEFORE trusting anything (§28.8).
        # A demo-class signature is only acceptable under the demo key id; a
        # production key id demands a real Ed25519 signature verified against a
        # pinned publisher trust store, which the demonstrator does not wire —
        # so such a pack must fail closed, never pass on the keyless demo hash.
        if is_demo_sig and not is_demo_key:
            print(f"REJECT: demo-class signature presented under non-demo "
                  f"signing_key_id {key_id!r} (§28.8 key-id/signature binding)")
            return 1
        if not is_demo_sig:
            print(f"REJECT: release signature for key {key_id!r} cannot be "
                  f"verified in the demonstrator (no publisher trust store "
                  f"wired); refusing rather than trusting (§9.3/§28.8)")
            return 1
        # demo-class signature under the demo key id: structural check only.
        print("note: demo signature - structurally checked, NOT a release signature")
        expect = hashlib.sha256(manifest_bytes).digest()
        if raw[len(prefix):] != expect:
            print("REJECT: manifest signature mismatch")
            return 1
        if min_safe is not None and _ver_tuple(manifest.get("release_version", "")) < _ver_tuple(min_safe):
            print(f"REJECT: version {manifest.get('release_version')} below "
                  f"minimum safe release {min_safe} (downgrade refused)")
            return 1
        # The signature commits to the manifest, and the manifest must commit to
        # the EXACT file set: reject any archive entry not listed in `files`
        # (besides the two manifest parts), so a signed pack cannot smuggle extra
        # unsigned content that would extract into the live pack dir.
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
    # (0,int) for numeric, (1,str) for non-numeric segments so comparison never
    # mixes int and str (e.g. "2026.10.1-rc1") and raises TypeError.
    return tuple((0, int(p)) if p.isdigit() else (1, p) for p in v.split("."))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="2026.10.1")
    ap.add_argument("--out", default="dist")
    ap.add_argument("--demo-key", action="store_true")
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
        return cmd_verify(Path(args.verify), args.min_safe)
    cmd_build(
        args.version,
        Path(args.out),
        args.demo_key,
        Path(args.audio_dir) if args.audio_dir else None,
        Path(args.images_dir) if args.images_dir else None,
        Path(args.vision_dir) if args.vision_dir else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
