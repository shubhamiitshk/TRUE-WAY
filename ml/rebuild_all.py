"""The whole corpus + encoder + index rebuild, in the order that is correct.

    python ml/rebuild_all.py [--python <tf-interpreter>]

The order matters and getting it wrong produces a SILENTLY inconsistent
artefact rather than an error:

  1. sync the review file with the review tables
  2. promote the approved candidates into the corpus
  3. re-split by source subject series
  4. train the adapter and export the index (PyTorch)
  5. convert to ONNX and then to TFLite, MEASURING every variant
  6. extract the gallery WITH the chosen artefact
  7. re-export the index, the calibration and the benchmark from that gallery
  8. stage the artefact, export the parity vectors, build the pack

Step 5 needs the adapter from step 4 and step 6 needs the artefact from
step 5, so the artefact is always built from the adapter that is actually
shipped, and the gallery is always extracted with the artefact that is
actually shipped.

The TensorFlow steps are run as SEPARATE PROCESSES: the converter's peak
memory plus the training process exceeds the commit limit on a host with no
page file, and the process is killed outright (exit -1, no traceback).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TF_DEFAULT = str(Path.home() / "AppData/Local/Temp/opencode/tfenv/Scripts/python.exe")


def run(label: str, cmd: list, env: dict | None = None) -> None:
    print(f"\n=== {label}\n$ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=ROOT, env=env)
    if r.returncode != 0:
        raise SystemExit(f"step failed: {label} (exit {r.returncode})")


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild the corpus, the encoder and the index")
    ap.add_argument("--python", default=TF_DEFAULT, help="interpreter with tensorflow")
    args = ap.parse_args()
    tf = args.python
    if not Path(tf).is_file():
        raise SystemExit(f"no TensorFlow interpreter at {tf}; pass --python")

    import os
    env = dict(os.environ)
    env["HF_HUB_OFFLINE"] = "1"

    run("1. sync the review file with the review tables",
        [sys.executable, "ml/audit/sync_review_to_tables.py"])
    run("2. promote the approved candidates", [sys.executable, "ml/promote_candidates.py"])
    run("3. re-split by source subject series", [sys.executable, "ml/resplit_dataset.py"])
    run("4. train the adapter and export the index",
        [sys.executable, "ml/train_arcface_pipeline.py"])
    run("5a. export ONNX", [tf, "ml/convert_encoder.py", "--variant", "s0",
                            "--work", "ml/models/s0", "--steps", "fetch,onnx"], env)
    run("5b. convert to TFLite and measure the variants",
        [tf, "ml/convert_encoder.py", "--variant", "s0",
         "--work", "ml/models/s0", "--steps", "tflite,report"], env)

    log = json.loads((ROOT / "ml/models/s0/conversion_log.json").read_text(encoding="utf-8"))
    chosen = log["tflite"].get("chosen_file")
    if not chosen:
        raise SystemExit("conversion_log.json has no tflite.chosen_file")
    print(f"\nchosen artefact: {chosen}")

    run("6. extract the gallery with the chosen artefact",
        [tf, "ml/build_index_from_artifact.py", "--artifact", f"ml/models/s0/{chosen}"], env)
    # The artefact is STAGED before the final export: the export records the
    # digest of the encoder the reference vectors were built with, and the
    # device refuses a pack whose digest does not match its encoder. Staging
    # afterwards leaves the pack describing the PREVIOUS encoder.
    run("7a. stage the artefact", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                    "-File", str(ROOT / "android/fetch_vision_assets.ps1")])
    run("7b. re-export the index, the calibration and the benchmark",
        [sys.executable, "ml/train_arcface_pipeline.py"])
    # The index assets are staged AGAIN after the final export: the export
    # rewrites content/vision/reference_vectors.*, so an asset copy taken
    # before it describes the PREVIOUS index. The encoder is unchanged by
    # the export, so the digest guard stays satisfied.
    run("7c. stage the freshly exported index assets",
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(ROOT / "android/fetch_vision_assets.ps1")])
    run("8a. export the parity vectors", [sys.executable, "ml/export_parity_vectors.py"])
    run("8b. build the pack", [sys.executable, "pack-builder/build_pack.py",
                                "--version", "2026.10.1", "--out", "dist", "--demo-key",
                                "--audio-dir", "content/audio",
                                "--images-dir", "content/images/then_now",
                                "--vision-dir", "content/vision"])
    print("\nREBUILD OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
