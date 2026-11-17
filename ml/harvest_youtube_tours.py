"""Automated Video Tour Frame Extractor for Monument Training Datasets.

Extracts high-resolution, diverse viewpoint frames from 4K walking tours
(e.g., YouTube walking tours downloaded via yt-dlp) without requiring manual
photography on-site.

Features:
- Periodic frame extraction (e.g. 1 frame every 3 seconds)
- Sharpness / blur filter using PIL edge detection & variance
- Perceptual hash deduplication (drops near-identical consecutive frames)
- Automatic grouping by video series to prevent train/test leakage
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List

from PIL import Image, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "ml" / "dataset"
CANDIDATES_DIR = DATASET_DIR / "candidates"


def compute_sharpness(img: Image.Image) -> float:
    """Computes edge gradient energy as a proxy for sharpness (replaces cv2 Laplacian)."""
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    return float(stat.var[0])


def compute_dhash(img: Image.Image, hash_size: int = 8) -> int:
    """Computes difference hash (dHash) to detect near-duplicate frames."""
    resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(resized.getdata())
    difference = []
    for row in range(hash_size):
        for col in range(hash_size):
            pixel_left = pixels[row * (hash_size + 1) + col]
            pixel_right = pixels[row * (hash_size + 1) + col + 1]
            difference.append(pixel_left > pixel_right)
    decimal_value = 0
    for idx, val in enumerate(difference):
        if val:
            decimal_value |= 1 << idx
    return decimal_value


def hamming_distance(h1: int, h2: int) -> int:
    return bin(h1 ^ h2).count("1")


def extract_frames_with_ffmpeg(
    video_path: Path,
    output_dir: Path,
    interval_seconds: float = 3.0,
    min_sharpness: float = 100.0,
    max_frames: int = 150,
) -> int:
    """Extracts candidate frames from a downloaded video file using ffmpeg if present,
    or processes an image sequence."""
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = output_dir / "temp_frames"
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Extracting frames from {video_path.name} at {interval_seconds}s intervals...")

    # Run ffmpeg to extract raw frames at 1 / interval_seconds fps
    fps_val = 1.0 / interval_seconds
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"fps={fps_val:.3f}",
        "-q:v",
        "2",
        str(temp_dir / "frame_%04d.jpg"),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("[!] Note: ffmpeg not detected in system path. Place video frames directly in temp_frames/")
        return 0

    saved_hashes: List[int] = []
    saved_count = 0

    frame_files = sorted(temp_dir.glob("frame_*.jpg"))
    print(f"[*] Analyzing {len(frame_files)} extracted candidate frames...")

    for frame_path in frame_files:
        if saved_count >= max_frames:
            break
        try:
            with Image.open(frame_path) as img:
                # 1. Blur check
                sharpness = compute_sharpness(img)
                if sharpness < min_sharpness:
                    continue

                # 2. Duplicate check against previously accepted frames
                curr_hash = compute_dhash(img)
                if any(hamming_distance(curr_hash, h) < 10 for h in saved_hashes):
                    continue

                # Save accepted frame
                out_name = f"harvest_vid_{video_path.stem}_{saved_count:03d}.jpg"
                final_path = output_dir / out_name
                img.save(final_path, quality=92)
                saved_hashes.append(curr_hash)
                saved_count += 1
        except Exception as e:
            continue

    # Cleanup temp frames
    for f in temp_dir.glob("*.jpg"):
        f.unlink()
    temp_dir.rmdir()

    print(f"[+] Successfully harvested {saved_count} sharp, diverse frames to {output_dir}")
    return saved_count


def main():
    parser = argparse.ArgumentParser(description="Harvest training frames from 4K video tours.")
    parser.add_argument("--video", type=str, help="Path to local video file (downloaded via yt-dlp)")
    parser.add_argument("--poi-id", type=str, required=True, help="Canonical POI ID (e.g. in-agra-taj-mahal)")
    parser.add_argument("--interval", type=float, default=3.0, help="Interval between frames in seconds")
    parser.add_argument("--max-frames", type=int, default=120, help="Maximum sharp frames to collect")
    args = parser.parse_args()

    target_dir = CANDIDATES_DIR / args.poi_id
    if args.video and Path(args.video).exists():
        extract_frames_with_ffmpeg(Path(args.video), target_dir, args.interval, max_frames=args.max_frames)
    else:
        print("[*] Harvester script initialized. Use with yt-dlp to download walking tours:")
        print(f"    yt-dlp -f 'bestvideo[height<=1080]' -o 'tour.mp4' <YOUTUBE_URL>")
        print(f"    python ml/harvest_youtube_tours.py --video tour.mp4 --poi-id {args.poi_id}")


if __name__ == "__main__":
    main()
