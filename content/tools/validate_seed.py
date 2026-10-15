"""Forwarding stub for content/seed/validate_seed.py."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "seed" / "validate_seed.py"

if __name__ == "__main__":
    import subprocess
    cmd = [sys.executable, str(TARGET)] + sys.argv[1:]
    sys.exit(subprocess.run(cmd).returncode)
