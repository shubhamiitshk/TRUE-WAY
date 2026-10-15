"""Hostile pack fixtures — tests/fixtures/hostile (Gate 2, §29 / PROTOCOL.md).

Builds a valid demo pack, then derives the attack fixtures from §29.5:
  bad-signature.twpkg  — one flipped byte in manifest.ed25519
  unknown-key.twpkg    — signing_key_id rewritten to attacker-key-1
                         (signature no longer matches either)
  truncated-sqlite.twpkg — content/places.sqlite cut by 1 KB (digest mismatch)
  traversal.twpkg      — added ../../evil.txt entry (path rejection)
  downgrade.twpkg      — byte-identical valid pack, verified with
                         --min-safe ABOVE its version (replay policy)
  forged-prodkey.twpkg — signing_key_id = production-looking id WITH a
                         recomputed matching demo hash (key-id/sig-class binding)
  unlisted-entry.twpkg — extra safe-named file absent from the signed manifest
                         (signed file-set completeness)

Exit 0 iff the valid pack verifies OK and all hostile packs are REJECTED.
Fixtures are generated, never committed (reproducible via this script).

Usage: python tests/fixtures/hostile/make_hostile.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILD = ROOT / "pack-builder" / "build_pack.py"
OUT = Path(__file__).resolve().parent
VERSION = "2026.10.1"
DIST = OUT / "work"


def build_valid() -> Path:
    DIST.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(BUILD), "--version", VERSION,
                    "--out", str(DIST), "--demo-key"], check=True,
                   capture_output=True)
    return DIST / f"trueway-in-bihar-buddhist-circuit-{VERSION}.twpkg"


def rewrite(src: Path, dest: Path, mutate) -> None:
    with zipfile.ZipFile(src) as zin:
        items = {n: zin.read(n) for n in zin.namelist()}
    mutate(items)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
        for n, data in items.items():
            zout.writestr(n, data)


def verify(pkg: Path, extra: list[str] | None = None) -> tuple[int, str]:
    cmd = [sys.executable, str(BUILD), "--verify", str(pkg)] + (extra or [])
    p = subprocess.run(cmd, capture_output=True, text=True)
    lines = (p.stdout + p.stderr).strip().splitlines()
    return p.returncode, (lines[-1] if lines else "(no output)")


def main() -> int:
    valid = build_valid()
    rc, line = verify(valid)
    print(f"[valid] rc={rc} :: {line}")
    ok = rc == 0

    cases: list[tuple[str, list[str] | None]] = [
        ("bad-signature.twpkg", None),
        ("unknown-key.twpkg", None),
        ("truncated-sqlite.twpkg", None),
        ("traversal.twpkg", None),
        ("downgrade.twpkg", ["--min-safe", "2026.10.2"]),
        ("forged-prodkey.twpkg", None),
        ("unlisted-entry.twpkg", None),
    ]

    # bad-signature needs a real byte flip; redo cleanly (lambda above is opaque).
    def flip_sig(items):
        raw = bytearray(base64.b64decode(items["manifest.ed25519"]))
        raw[7] ^= 0xFF
        items["manifest.ed25519"] = base64.b64encode(bytes(raw))

    def attacker_key(items):
        m = json.loads(items["manifest.cjson"].decode())
        m["signing_key_id"] = "attacker-key-1"
        items["manifest.cjson"] = json.dumps(m).encode()

    def truncate_sqlite(items):
        items["content/places.sqlite"] = items["content/places.sqlite"][:-1024]

    def add_traversal(items):
        items["../../evil.txt"] = b"you are pwned"

    def forge_prodkey(items):
        # Production-looking key id WITH a recomputed matching demo hash: the
        # verifier must reject on key-id/signature-class binding, not accept.
        m = json.loads(items["manifest.cjson"].decode())
        m["signing_key_id"] = "pubkey-2026-q4"
        mb = json.dumps(m, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=False).encode("utf-8")
        items["manifest.cjson"] = mb
        items["manifest.ed25519"] = base64.b64encode(
            b"DEMO-SIGNATURE:" + hashlib.sha256(mb).digest())

    def add_unlisted(items):
        items["content/extra.json"] = b"{\"smuggled\": true}"

    mutators = {"bad-signature.twpkg": flip_sig,
                "unknown-key.twpkg": attacker_key,
                "truncated-sqlite.twpkg": truncate_sqlite,
                "traversal.twpkg": add_traversal,
                "downgrade.twpkg": None,
                "forged-prodkey.twpkg": forge_prodkey,
                "unlisted-entry.twpkg": add_unlisted}

    passed = 0
    for name, extra in cases:
        dest = OUT / name
        if mutators[name] is None:
            shutil.copy(valid, dest)  # downgrade: identical bytes, stricter policy
        else:
            rewrite(valid, dest, mutators[name])
        rc, line = verify(dest, extra)
        status = "REJECTED-ok" if rc != 0 else "ACCEPTED-BAD"
        print(f"[{name}] rc={rc} :: {line}  => {status}")
        ok = ok and rc != 0
        passed += 1 if rc != 0 else 0

    shutil.rmtree(DIST, ignore_errors=True)
    total = len(cases)
    print(f"\nHOSTILE SUITE " + (f"{passed}/{total} PASS" if ok else f"{passed}/{total} FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
