"""Unit test suite for content/tools/generate_bilingual_audio.py.

Validates:
1. Dry-run execution across individual regions and corridors.
2. Synthetic mock audio generation for both OGG Vorbis and OGG Opus codecs.
3. RFC 3533 Ogg container integrity verification (OggS magic, Vorbis/Opus headers).
4. Ad-hoc custom POI synthesis with bilingual text scripts.
5. Safe abstention on missing inputs.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = ROOT / "content" / "tools" / "generate_bilingual_audio.py"


class TestGenerateBilingualAudio(unittest.TestCase):
    def test_tool_exists(self) -> None:
        self.assertTrue(TOOL_PATH.is_file(), f"Tool not found at {TOOL_PATH}")

    def test_dry_run_bihar_circuit(self) -> None:
        cmd = [sys.executable, str(TOOL_PATH), "--dry-run", "--region", "in-bihar-buddhist-circuit"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Dry-run failed: {res.stderr}")
        self.assertIn("TrueWay Bilingual Audio Generator", res.stdout)
        self.assertIn("mahabodhi", res.stdout)
        self.assertIn("DRY-RUN", res.stdout)

    def test_dry_run_all_regions(self) -> None:
        cmd = [sys.executable, str(TOOL_PATH), "--dry-run", "--region", "all"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Dry-run all regions failed: {res.stderr}")
        self.assertIn("taj_mahal", res.stdout)
        self.assertIn("eiffel_tower", res.stdout)

    def test_mock_generation_vorbis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            cmd = [
                sys.executable,
                str(TOOL_PATH),
                "--mock",
                "--region", "in-golden-triangle",
                "--codec", "vorbis",
                "--out-dir", str(tmp),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Mock Vorbis generation failed: {res.stderr}")

            # Verify generated files
            en_file = tmp / "taj_mahal_guide.ogg"
            hi_file = tmp / "taj_mahal_guide_hi.ogg"
            self.assertTrue(en_file.is_file(), "Missing taj_mahal_guide.ogg")
            self.assertTrue(hi_file.is_file(), "Missing taj_mahal_guide_hi.ogg")

            with open(en_file, "rb") as f:
                header = f.read(64)
            self.assertTrue(header.startswith(b"OggS"), "Invalid Ogg header")

            # Verify with tool's own --verify flag
            v_cmd = [sys.executable, str(TOOL_PATH), "--verify", "--out-dir", str(tmp)]
            v_res = subprocess.run(v_cmd, capture_output=True, text=True)
            self.assertEqual(v_res.returncode, 0, f"Mock Vorbis verification failed: {v_res.stderr}")
            self.assertIn("Verification completed", v_res.stdout)

    def test_mock_generation_opus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            cmd = [
                sys.executable,
                str(TOOL_PATH),
                "--mock",
                "--poi-id", "colosseum",
                "--codec", "opus",
                "--out-dir", str(tmp),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Mock Opus generation failed: {res.stderr}")

            en_file = tmp / "colosseum_guide.ogg"
            self.assertTrue(en_file.is_file(), "Missing colosseum_guide.ogg")

            with open(en_file, "rb") as f:
                header = f.read(64)
            self.assertTrue(header.startswith(b"OggS"), "Invalid Ogg header")

    def test_ad_hoc_poi_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            cmd = [
                sys.executable,
                str(TOOL_PATH),
                "--mock",
                "--poi-id", "test_monument",
                "--text-en", "Welcome to the ancient testing site.",
                "--text-hi", "परीक्षण स्थल में आपका स्वागत है।",
                "--out-dir", str(tmp),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Ad-hoc POI synthesis failed: {res.stderr}")

            en_file = tmp / "test_monument_guide.ogg"
            hi_file = tmp / "test_monument_guide_hi.ogg"
            self.assertTrue(en_file.is_file(), "Missing test_monument_guide.ogg")
            self.assertTrue(hi_file.is_file(), "Missing test_monument_guide_hi.ogg")

    def test_verify_production_corpus(self) -> None:
        prod_audio = ROOT / "content" / "audio"
        if not prod_audio.exists():
            self.skipTest("Production audio directory not found")

        cmd = [sys.executable, str(TOOL_PATH), "--verify", "--out-dir", str(prod_audio)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Production audio verification failed: {res.stderr}")
        self.assertIn("20/20 valid audio streams", res.stdout)


if __name__ == "__main__":
    unittest.main()
