"""Unit tests for ml/harvest_global_corridors.py.

Verifies:
1. POI and corridor specifications (Bihar Circuit, India Golden Triangle, Global Icons)
2. Reject pattern title filtering and subject exemptions
3. Sharpness calculation and perceptual dHash deduplication
4. Photographer-grouped and video-series-grouped split discipline
5. Mock corridor harvesting, candidate manifest generation, and quarantine isolation
"""
import copy
import io
import json
import sys
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ml.harvest_global_corridors as hgc


class TestHarvestGlobalCorridors(unittest.TestCase):

    def test_corridor_specifications_completeness(self):
        """Verifies presence and schema of all mandatory corridors and flagship POIs."""
        corridors = hgc.CORRIDORS
        self.assertIn("bihar-buddhist-circuit", corridors)
        self.assertIn("india-golden-triangle", corridors)
        self.assertIn("global-icons-tier1", corridors)

        # 1. Bihar Buddhist Circuit (15 POIs)
        bihar = corridors["bihar-buddhist-circuit"]
        self.assertEqual(len(bihar["pois"]), 15)
        bihar_ids = {p["place_id"] for p in bihar["pois"]}
        self.assertIn("in-bihar-bodhgaya-mahabodhi", bihar_ids)
        self.assertIn("in-bihar-nalanda-mahavihara", bihar_ids)
        self.assertIn("in-bihar-rajgir-shanti-stupa", bihar_ids)

        # 2. India Golden Triangle
        gt = corridors["india-golden-triangle"]
        gt_ids = {p["place_id"] for p in gt["pois"]}
        mandatory_gt = [
            "in-agra-taj-mahal",
            "in-delhi-qutub-minar",
            "in-delhi-red-fort",
            "in-jaipur-hawa-mahal",
            "in-jaipur-amer-fort",
            "in-agra-agra-fort",
            "in-agra-fatehpur-sikri",
            "in-delhi-humayuns-tomb",
            "in-jaipur-city-palace",
        ]
        for mid in mandatory_gt:
            self.assertIn(mid, gt_ids)

        # 3. Global Icons Tier-1
        global_icons = corridors["global-icons-tier1"]
        global_ids = {p["place_id"] for p in global_icons["pois"]}
        mandatory_global = [
            "fr-paris-eiffel-tower",
            "it-rome-colosseum",
            "eg-giza-pyramids",
            "kh-siem-reap-angkor-wat",
            "pe-cusco-machu-picchu",
            "us-nyc-statue-of-liberty",
        ]
        for gid in mandatory_global:
            self.assertIn(gid, global_ids)

        # Schema checks
        for cid, cdata in corridors.items():
            self.assertIn("pack_id", cdata)
            self.assertIn("name", cdata)
            for p in cdata["pois"]:
                self.assertIn("place_id", p)
                self.assertIn("viewpoint_tag", p)
                self.assertIn("categories", p)
                self.assertIn("queries", p)

    def test_title_rejection_and_exemptions(self):
        """Verifies candidate title filtering against non-photographs while respecting domain exemptions."""
        # Obvious rejects
        self.assertTrue(hgc.is_rejected_title("A miniature model of Taj Mahal in museum"))
        self.assertTrue(hgc.is_rejected_title("Drawing of Qutub Minar 1856 sketch"))
        self.assertTrue(hgc.is_rejected_title("Commemorative coin of Red Fort 1980"))
        self.assertTrue(hgc.is_rejected_title("Early photograph of Hawa Mahal 1885 archival"))
        self.assertTrue(hgc.is_rejected_title("Information signboard board at Amer Fort"))
        self.assertTrue(hgc.is_rejected_title("Colosseum elevation architectural plan"))

        # Valid field photo titles
        self.assertFalse(hgc.is_rejected_title("Taj Mahal south facade reflection pool 2024"))
        self.assertFalse(hgc.is_rejected_title("Qutub Minar fluted balcony view Delhi"))
        self.assertFalse(hgc.is_rejected_title("Red Fort Lahori Gate main ramparts"))

        # Exemption handling (e.g. Great Buddha statue or Sonbhandar caves)
        self.assertTrue(hgc.is_rejected_title("Great Buddha statue in garden"))
        self.assertFalse(hgc.is_rejected_title("Great Buddha statue in garden", exempt=[r"\bstatue\b"]))

    def test_quality_and_deduplication_metrics(self):
        """Verifies edge variance sharpness and dHash Hamming distance calculation."""
        # 1. Blank image (low edge variance)
        blank = Image.new("RGB", (200, 200), color=(128, 128, 128))
        sharp_blank = hgc.compute_sharpness(blank)
        self.assertLess(sharp_blank, 500.0)

        # 2. High contrast pattern image (high sharpness)
        pattern = Image.new("RGB", (200, 200), color=(255, 255, 255))
        draw = ImageDraw.Draw(pattern)
        for i in range(0, 200, 10):
            draw.line([(i, 0), (i, 200)], fill=(0, 0, 0), width=2)
        sharp_pattern = hgc.compute_sharpness(pattern)
        self.assertGreater(sharp_pattern, 5000.0)
        self.assertGreater(sharp_pattern, sharp_blank * 10)

        # 3. dHash and Hamming distance
        h1 = hgc.compute_dhash(pattern)
        pattern_clone = pattern.copy()
        h2 = hgc.compute_dhash(pattern_clone)
        self.assertEqual(hgc.hamming_distance(h1, h2), 0)

        inverted = Image.new("RGB", (200, 200), color=(0, 0, 0))
        h3 = hgc.compute_dhash(inverted)
        self.assertGreaterEqual(hgc.hamming_distance(h1, h3), 0)

    def test_photographer_grouped_split_discipline(self):
        """Tests that assign_photo_grouped_splits guarantees disjoint splits."""
        records = [
            # Photographer Alice (Series 1: Taj Mahal)
            {
                "local_path": "ml/dataset/candidates/place/taj_01.jpg",
                "source_photo_id": "photo_a1",
                "photographer": "Alice",
                "title": "Taj Mahal south view (1)",
            },
            {
                "local_path": "ml/dataset/candidates/place/taj_02.jpg",
                "source_photo_id": "photo_a2",
                "photographer": "Alice",
                "title": "Taj Mahal south view (2)",
            },
            # Photographer Bob (Series 2: Taj Mahal)
            {
                "local_path": "ml/dataset/candidates/place/taj_03.jpg",
                "source_photo_id": "photo_b1",
                "photographer": "Bob",
                "title": "Taj Mahal minarets sunrise",
            },
            # Photographer Charlie (Series 3: Taj Mahal)
            {
                "local_path": "ml/dataset/candidates/place/taj_04.jpg",
                "source_photo_id": "photo_c1",
                "photographer": "Charlie",
                "title": "Taj Mahal garden charbagh",
            },
            # Video Series (Video Tour 1)
            {
                "local_path": "ml/dataset/candidates/place/taj_05.jpg",
                "source_photo_id": "video:tour01:001",
                "source_subject_id": "video:tour01",
                "photographer": "channel:Prowalk",
                "title": "VideoFrame:tour01:001",
            },
            {
                "local_path": "ml/dataset/candidates/place/taj_06.jpg",
                "source_photo_id": "video:tour01:002",
                "source_subject_id": "video:tour01",
                "photographer": "channel:Prowalk",
                "title": "VideoFrame:tour01:002",
            },
        ]

        split_recs = hgc.assign_photo_grouped_splits(records, counts_per_split=(2, 2, 4))
        valid, errors = hgc.verify_split_discipline(split_recs)
        self.assertTrue(valid, f"Split discipline failed: {errors}")

        # Check Alice's series didn't leak across multiple splits
        alice_splits = {r["split"] for r in split_recs if r["photographer"] == "Alice"}
        self.assertEqual(len(alice_splits), 1)

        # Check video series didn't leak across multiple splits
        video_splits = {r["split"] for r in split_recs if r.get("source_subject_id") == "video:tour01"}
        self.assertEqual(len(video_splits), 1)

        # Test intentional leakage detection
        leaked_recs = copy.deepcopy(split_recs)
        leaked_recs[0]["split"] = "ref"
        leaked_recs[1]["split"] = "test"
        valid_leaked, leak_errors = hgc.verify_split_discipline(leaked_recs)
        self.assertFalse(valid_leaked)
        self.assertTrue(any("leakage" in e.lower() for e in leak_errors))

    def test_mock_harvest_manifest_generation(self):
        """Runs mock harvest on Golden Triangle POI and verifies quarantine manifest output."""
        test_dir = ROOT / "ml" / "dataset" / "candidates" / "test_unit_quarantine"
        manifest_file = test_dir / "test_unit_manifest.json"

        try:
            manifest = hgc.harvest_corridor(
                corridor_key="india-golden-triangle",
                target_dir=test_dir,
                manifest_path=manifest_file,
                source_mode="both",
                per_class_target=6,
                mock_mode=True,
                poi_filter=["in-agra-taj-mahal", "in-delhi-qutub-minar"],
            )

            self.assertTrue(manifest_file.is_file())
            self.assertEqual(manifest["corridor_id"], "india-golden-triangle")
            self.assertIn("in-agra-taj-mahal", manifest["classes"])
            self.assertIn("in-delhi-qutub-minar", manifest["classes"])

            # Verify quarantine isolation: all records must have status='pending'
            for cid, cinfo in manifest["classes"].items():
                for rec in cinfo["records"]:
                    self.assertEqual(rec["status"], "pending")
                    self.assertEqual(rec["verification_status"], "pending")
                    self.assertIn(rec["split"], ("ref", "calib", "test"))

            self.assertTrue(manifest["summary"]["split_integrity_verified"])

        finally:
            if manifest_file.exists():
                manifest_file.unlink()
            if test_dir.exists():
                import shutil
                shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
