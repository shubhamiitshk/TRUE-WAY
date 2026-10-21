"""Rebuild the encoder, the gallery and the index - in the order that works.

    python ml/rebuild_encoder.py

WHY A SCRIPT AND NOT A README PARAGRAPH
---------------------------------------
The order is not obvious and getting it wrong produces a **silently wrong
pack** rather than an error:

  1. train the adapter                      (PyTorch; the gallery's source of truth)
  2. convert to ONNX                        (the exported graph)
  3. convert to TFLite and MEASURE          (five variants; the fastest wins)
  4. extract the gallery WITH the winner     (the vectors the device will score against)
  5. stage the winner into the APK assets    (the file the device will load)
  6. re-export the index + calibration      (from the artefact's own embeddings)

Steps 2-3 and step 6 run as SEPARATE PROCESSES on purpose: the TFLite
converter's peak memory plus the training process exceeds the commit limit on
a machine with no page file, and the process is killed outright (exit -1, no
traceback, buffered stdout lost). One step per process keeps each peak small.

Steps 4 and 5 must both happen BEFORE step 6: the index records the digest of
the encoder that produced the reference vectors, and the device refuses a pack
whose digest does not match the encoder it ships.

    --python   the interpreter to use for the TensorFlow steps. It must have
               tensorflow, onnx, onnx2tf, onnxruntime, torch and timm.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "ml" / "models" / "s0"


def run(label: str, cmd: list) -> None:
    print(f"\n=== {label}\n$ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(f"step failed: {label} (exit {r.returncode})")


def tf_python(explicit: str | None) -> str:
    """The interpreter for the TensorFlow steps."""
    if explicit:
        return explicit
    try:
        import tensorflow  # noqa: F401
        return sys.executable
    except ImportError:
        pass
    for candidate in (
        Path.home() / "AppData/Local/Temp/opencode/tfenv/Scripts/python.exe",
        ROOT / ".venv-tf/Scripts/python.exe",
    ):
        if candidate.is_file():
            return str(candidate)
    raise SystemExit(
        "no TensorFlow-capable interpreter found. Install one (python 3.11 + "
        "tensorflow-cpu, onnx, onnxruntime, onnx2tf, torch, timm) and pass it "
        "with --python.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild the encoder, gallery and index")
    ap.add_argument("--python", default=None, help="interpreter with tensorflow")
    ap.add_argument("--skip-train", action="store_true",
                    help="reuse the existing adapter (step 1)")
    args = ap.parse_args()

    tf = tf_python(args.python)
    print(f"tensorflow interpreter: {tf}")
    print(f"work directory        : {WORK}")

    if not args.skip_train:
        run("1/6 train the adapter", [sys.executable, "ml/train_arcface_pipeline.py"])

    run("2/6 export ONNX", [tf, "ml/convert_encoder.py", "--variant", "s0",
                            "--work", "ml/models/s0", "--steps", "fetch,onnx"])
    run("3/6 convert to TFLite and measure the variants",
        [tf, "ml/convert_encoder.py", "--variant", "s0",
         "--work", "ml/models/s0", "--steps", "tflite,report"])

    log = json.loads((WORK / "conversion_log.json").read_text(encoding="utf-8"))
    chosen = log["tflite"].get("chosen_file")
    if not chosen:
        raise SystemExit("conversion_log.json has no tflite.chosen_file")
    print(f"\nchosen artefact: {chosen}")

    run("4/6 extract the gallery WITH the chosen artefact",
        [tf, "ml/build_index_from_artifact.py", "--artifact", f"ml/models/s0/{chosen}"])

    ps = shutil.which("pwsh") or shutil.which("powershell")
    if not ps:
        raise SystemExit("no PowerShell found; run android/fetch_vision_assets.ps1 by hand")
    run("5/6 stage the chosen artefact into the APK assets",
        [ps, "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(ROOT / "android" / "fetch_vision_assets.ps1")])

    run("6/6 re-export the index, the calibration and the benchmark",
        [sys.executable, "ml/train_arcface_pipeline.py"])

    print("\nREBUILD OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
