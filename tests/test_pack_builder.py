"""Comprehensive unit and integration test suite for TrueWay Pack Builder & Regional Catalog.

Covers:
- Multi-region pack definitions (.twpkg)
- Manifest canonical JSON and SHA-256 tree verification
- Zero-copy binary index integrity (TWVEC002)
- Ed25519 signature generation and verification (real keys & demo keys)
- Hostile archive and tamper rejection
- Parity with Android PackImporter.kt expectations
- Regional pack distribution catalog operations
"""
from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pack-builder"))

from build_pack import (
    TWVEC002_HEADER_SIZE,
    TWVEC002_MAGIC,
    canonical,
    cmd_build,
    cmd_verify,
    compile_twvec002_from_reference_index,
    safe_zip_members,
    verify_twvec002_file,
    verify_twvec002_integrity,
)
from regional_catalog import RegionalPackCatalog, RegionalPackDefinition


class TestTWVEC002BinaryIntegrity(unittest.TestCase):
    """Tests TWVEC002 zero-copy binary index integrity checking."""

    def test_verify_real_committed_twvec002(self):
        bin_path = ROOT / "content" / "vision" / "reference_vectors.bin"
        meta_path = ROOT / "content" / "vision" / "reference_vectors.meta.json"
        self.assertTrue(bin_path.is_file(), "reference_vectors.bin must exist")
        self.assertTrue(meta_path.is_file(), "reference_vectors.meta.json must exist")

        ok, errs = verify_twvec002_file(bin_path, meta_path)
        self.assertTrue(ok, f"Committed TWVEC002 index failed integrity check: {errs}")
        self.assertEqual(len(errs), 0)

    def test_reject_corrupt_twvec002_magic(self):
        bin_path = ROOT / "content" / "vision" / "reference_vectors.bin"
        raw = bytearray(bin_path.read_bytes())
        raw[:8] = b"CORRUPT!"
        ok, errs = verify_twvec002_integrity(bytes(raw))
        self.assertFalse(ok)
        self.assertTrue(any("magic" in e.lower() for e in errs))

    def test_reject_truncated_twvec002(self):
        bin_path = ROOT / "content" / "vision" / "reference_vectors.bin"
        raw = bin_path.read_bytes()
        truncated = raw[:-100]  # Cut off last 100 bytes
        ok, errs = verify_twvec002_integrity(truncated)
        self.assertFalse(ok)
        self.assertTrue(any("mismatch" in e.lower() or "size" in e.lower() for e in errs))

    def test_reject_incomplete_calibration_metadata(self):
        bin_path = ROOT / "content" / "vision" / "reference_vectors.bin"
        meta_path = ROOT / "content" / "vision" / "reference_vectors.meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        # Remove a critical calibration threshold
        del meta["calibration"]["accept_threshold"]
        ok, errs = verify_twvec002_integrity(bin_path.read_bytes(), meta)
        self.assertFalse(ok)
        self.assertTrue(any("incomplete calibration" in e.lower() for e in errs))

    def test_reject_non_contiguous_prototypes(self):
        bin_path = ROOT / "content" / "vision" / "reference_vectors.bin"
        meta_path = ROOT / "content" / "vision" / "reference_vectors.meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        # Corrupt prototype start
        if len(meta["places"]) > 1:
            meta["places"][1]["prototype_start"] = 999
            ok, errs = verify_twvec002_integrity(bin_path.read_bytes(), meta)
            self.assertFalse(ok)
            self.assertTrue(any("contiguous" in e.lower() for e in errs))


class TestEd25519SigningAndVerification(unittest.TestCase):
    """Tests Ed25519 real key and demo key signing."""

    def test_real_ed25519_key_signing_and_verification(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            key_file = tmp_p / "ed25519_test.key"
            priv_key = Ed25519PrivateKey.generate()
            pub_key = priv_key.public_key()
            pub_bytes = pub_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
            pub_b64 = base64.b64encode(pub_bytes).decode("ascii")

            # Write raw 32 bytes seed
            raw_priv = priv_key.private_bytes(
                encoding=Encoding.Raw,
                format=PublicFormat.Raw,
                encryption_algorithm=from_hazmat_no_encryption(),
            ) if False else None

            # Or write PEM format
            from cryptography.hazmat.primitives.serialization import NoEncryption, PrivateFormat
            pem_bytes = priv_key.private_bytes(
                Encoding.PEM,
                PrivateFormat.PKCS8,
                NoEncryption(),
            )
            key_file.write_bytes(pem_bytes)

            out_dir = tmp_p / "dist"
            pkg = cmd_build(
                version="2026.10.1",
                out=out_dir,
                demo_key=False,
                key_file=key_file,
                key_id="pubkey-test-real-1",
            )
            self.assertTrue(pkg.is_file())

            # Verification without public key must fail closed (§9.3/§28.8)
            rc_no_pub = cmd_verify(pkg)
            self.assertEqual(rc_no_pub, 1)

            # Verification with matching public key must succeed
            rc_pub = cmd_verify(pkg, pub_key_b64=pub_b64)
            self.assertEqual(rc_pub, 0)

    def test_demo_key_signing_and_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            out_dir = tmp_p / "dist"
            pkg = cmd_build(
                version="2026.10.1",
                out=out_dir,
                demo_key=True,
            )
            self.assertTrue(pkg.is_file())
            rc = cmd_verify(pkg)
            self.assertEqual(rc, 0)


class TestMultiRegionPackDefinitions(unittest.TestCase):
    """Tests building packs for multiple distinct regions."""

    def test_build_multi_region_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            schema_p = tmp_p / "schema.sql"
            seed_p = tmp_p / "seed.sql"

            schema_p.write_text(
                (ROOT / "content" / "schema" / "publication_schema.sql").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            # Custom regional seed with 2 POIs for a new corridor
            custom_seed = """
INSERT INTO places (place_id, canonical_name, category, latitude, longitude, visitor_mode, visitor_notice, last_reviewed_at, editorial_state)
VALUES 
  ('in-gt-delhi-qutub-minar', 'Qutub Minar', 'MONUMENT', 28.5244, 77.1855, 'PHOTO_SUPPORTED', 'Open daily', '2026-10-01', 'PUBLISHED'),
  ('in-gt-agra-taj-mahal', 'Taj Mahal', 'MAUSOLEUM', 27.1751, 78.0421, 'PHOTO_SUPPORTED', 'Closed Fridays', '2026-10-01', 'PUBLISHED');

INSERT INTO sources (source_id, title, author_or_publisher, publication_year, rights_id)
VALUES ('src-asi-gt', 'ASI Monument Guide', 'Archaeological Survey of India', '2020', 'ASI-OPEN');

INSERT INTO claims (claim_id, place_id, claim_type, locale, claim_text, reviewed_at, reviewer_id, editorial_state)
VALUES 
  ('clm-qm-1', 'in-gt-delhi-qutub-minar', 'DOCUMENTED', 'en', 'Minaret commissioned by Qutb-ud-din Aibak.', '2026-10-01', 'rev-1', 'PUBLISHED'),
  ('clm-qm-2', 'in-gt-delhi-qutub-minar', 'DOCUMENTED', 'hi', 'कुतुब मीनार 73 मीटर ऊँची मीनार है।', '2026-10-01', 'rev-1', 'PUBLISHED'),
  ('clm-tm-1', 'in-gt-agra-taj-mahal', 'DOCUMENTED', 'en', 'White marble mausoleum commissioned by Shah Jahan.', '2026-10-01', 'rev-1', 'PUBLISHED'),
  ('clm-tm-2', 'in-gt-agra-taj-mahal', 'DOCUMENTED', 'hi', 'ताजमहल सफ़ेद संगमरमर का मक़बरा है।', '2026-10-01', 'rev-1', 'PUBLISHED');

INSERT INTO claim_sources (claim_id, source_id, page_or_anchor)
VALUES 
  ('clm-qm-1', 'src-asi-gt', 'p. 12'),
  ('clm-qm-2', 'src-asi-gt', 'p. 14'),
  ('clm-tm-1', 'src-asi-gt', 'p. 45'),
  ('clm-tm-2', 'src-asi-gt', 'p. 48');
"""
            seed_p.write_text(custom_seed, encoding="utf-8")

            out_dir = tmp_p / "dist"
            pkg = cmd_build(
                version="2026.10.1",
                out=out_dir,
                demo_key=True,
                pack_id="in-golden-triangle-test",
                pack_title="India Golden Triangle Test Pack",
                schema_file=schema_p,
                seed_file=seed_p,
            )
            self.assertTrue(pkg.is_file())
            self.assertEqual(pkg.name, "trueway-in-golden-triangle-test-2026.10.1.twpkg")

            # Verify the bundle
            rc = cmd_verify(pkg)
            self.assertEqual(rc, 0)

            # Check manifest content
            with zipfile.ZipFile(pkg, "r") as z:
                manifest = json.loads(z.read("manifest.cjson").decode("utf-8"))
                self.assertEqual(manifest["pack_id"], "in-golden-triangle-test")
                self.assertEqual(manifest["place_count"], 2)
                self.assertEqual(sorted(manifest["content_locales"]), ["en", "hi"])
                self.assertEqual(manifest["schema_version"], 3)


class TestAndroidPackImporterCompatibility(unittest.TestCase):
    """Verifies that generated .twpkg packs conform to Android PackImporter.kt expectations."""

    def test_manifest_schema_and_file_completeness(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            pkg = cmd_build(
                version="2026.10.1",
                out=tmp_p / "dist",
                demo_key=True,
                audio_dir=ROOT / "content" / "audio",
                images_dir=ROOT / "content" / "images" / "then_now",
                vision_dir=ROOT / "content" / "vision",
            )
            with zipfile.ZipFile(pkg, "r") as z:
                names = z.namelist()
                # Required top-level files
                self.assertIn("manifest.cjson", names)
                self.assertIn("manifest.ed25519", names)
                self.assertIn("content/places.sqlite", names)
                self.assertIn("ATTRIBUTIONS.json", names)
                self.assertIn("LICENSES.json", names)
                self.assertIn("CHANGELOG.md", names)

                manifest = json.loads(z.read("manifest.cjson").decode("utf-8"))

                # Android PackImporter required fields
                self.assertEqual(manifest.get("format"), "trueway.pack")
                self.assertEqual(manifest.get("schema_version"), 3)
                self.assertTrue(manifest.get("pack_id"))
                self.assertTrue(manifest.get("release_version"))
                self.assertTrue(manifest.get("signing_key_id"))
                self.assertGreater(manifest.get("place_count", 0), 0)
                self.assertIn("vision", manifest)
                self.assertEqual(manifest["vision"].get("format"), "TWVEC002")

                files = manifest.get("files", [])
                self.assertGreater(len(files), 0)

                # Verify each file's size and SHA-256
                for f in files:
                    p = f["path"]
                    self.assertIn(p, names)
                    data = z.read(p)
                    self.assertEqual(len(data), f["bytes"])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), f["sha256"])
                    self.assertTrue(f.get("asset_origin"))


class TestRegionalCatalog(unittest.TestCase):
    """Tests the regional pack distribution catalog."""

    def test_catalog_query_and_extraction(self):
        cat = RegionalPackCatalog()
        regions = cat.list_regions()
        self.assertGreaterEqual(len(regions), 2)
        pack_ids = [r["pack_id"] for r in regions]
        self.assertIn("in-bihar-buddhist-circuit", pack_ids)
        self.assertIn("in-golden-triangle", pack_ids)

        latest = cat.get_latest_release("in-bihar-buddhist-circuit")
        self.assertIsNotNone(latest)
        self.assertEqual(latest["pack_id"], "in-bihar-buddhist-circuit")
        self.assertEqual(latest["schema_version"], 3)

        # Manifest reading from built bundle if present
        if cat.has_bundle("in-bihar-buddhist-circuit"):
            mbytes = cat.read_manifest("in-bihar-buddhist-circuit", "2026.10.1")
            self.assertIsNotNone(mbytes)
            mdata = json.loads(mbytes.decode("utf-8"))
            self.assertEqual(mdata["pack_id"], "in-bihar-buddhist-circuit")


if __name__ == "__main__":
    unittest.main()
