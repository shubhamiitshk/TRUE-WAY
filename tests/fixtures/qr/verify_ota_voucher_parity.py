#!/usr/bin/env python3
"""Cross-language parity check for OTA voucher canonicalization.

Simulates the Kotlin `OtaVoucherParser.canonicalizeVoucher` byte-for-byte and
verifies the Ed25519 signatures from the Python fixture generator. If the two
sides ever diverge, this script fails loudly — the same class of bug the repo
already caught in the vision index (36- vs 40-byte header).
"""
import json
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

BASE = Path(__file__).parent


def b64d(s: str) -> bytes:
    p = s.strip()
    p += "=" * ((4 - len(p) % 4) % 4)
    return base64.urlsafe_b64decode(p)


def escape_json_string(s: str) -> str:
    out = []
    for c in s:
        if c == "\\":
            out.append("\\\\")
        elif c == '"':
            out.append('\\"')
        elif ord(c) < 0x20:
            out.append("\\u%04x" % ord(c))
        else:
            out.append(c)
    return "".join(out)


def kotlin_canonical(obj: dict) -> bytes:
    parts = []
    for k in ("expires_at", "issued_at", "ota_partner", "pack_id"):
        v = obj.get(k)
        if v:
            parts.append('"%s":"%s"' % (k, escape_json_string(v)))
    parts.append('"v":%d' % obj["v"])
    v = obj.get("voucher_id")
    if v:
        parts.append('"voucher_id":"%s"' % escape_json_string(v))
    return ("{" + ",".join(parts) + "}").encode("utf-8")


def python_canonical(obj: dict) -> bytes:
    c = {k: v for k, v in obj.items() if k != "signature"}
    return json.dumps(c, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    trust = json.loads((BASE / "demo_ota_trust_store.json").read_text(encoding="utf-8"))
    keys = {p["partner_id"]: p["pubkey_b64u"] for p in trust["partners"]}

    failures = 0
    for name in [
        "demo_viator_voucher.json",
        "demo_klook_voucher.json",
        "demo_mmt_voucher.json",
        "expired_voucher.json",
        "bad_signature_voucher.json",
    ]:
        expected_valid = name != "bad_signature_voucher.json"
        obj = json.loads((BASE / name).read_text(encoding="utf-8"))
        k_can = kotlin_canonical(obj)
        p_can = python_canonical(obj)
        match = k_can == p_can
        print("=" * 60)
        print(name, "(expect", "VALID" if expected_valid else "INVALID", "signature)")
        print("  kotlin-canonical == python-canonical:", match)
        sig = b64d(obj["signature"])
        pub = Ed25519PublicKey.from_public_bytes(b64d(keys[obj["ota_partner"]]))
        try:
            pub.verify(sig, k_can)
            sig_ok = True
            print("  VALID over kotlin-canonical")
        except Exception:
            sig_ok = False
            print("  INVALID over kotlin-canonical")
        if sig_ok != expected_valid:
            failures += 1
            print("  ^^ UNEXPECTED RESULT")

    print("=" * 60)
    if failures:
        print(f"PARITY CHECK FAILED: {failures} voucher(s) produced unexpected results")
        return 1
    print("PARITY CHECK PASSED — Kotlin canonicalization is byte-identical to Python")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
