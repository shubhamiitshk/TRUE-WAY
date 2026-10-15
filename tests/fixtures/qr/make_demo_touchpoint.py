"""Demo touchpoint issuer — tests/fixtures/qr (TOUCH-033..036).

Generates an EPHEMERAL Ed25519 issuer key (never committed), signs the demo
touchpoint payload, and writes:
  demo_touchpoint_envelope.json  {"v":1,"c":"<b64u canonical>","s":"<b64u sig>"}
  demo_touchpoint_qr.txt         tw://place/v1/<c>.<s>   (QR-printable form)
  expired_touchpoint_envelope.json / forged_touchpoint_envelope.json /
  unknownissuer_touchpoint_envelope.json   (negative fixtures)
  trust_store.json               {"issuers":[{issuer_id,key_id,pubkey_b64u,status:DEMO}]}
Copy trust_store.json -> android/app/src/main/assets/touch_issuers.json
(canonical bytes are identical, so fixtures validate against the app store).

Canonical form (MUST match TouchpointParser.kt byte-for-byte):
  json.dumps(payload, sort_keys=True, separators=(",", ":"))  # ASCII labels
Transports carry (c, s) opaquely — verifiers never re-serialize.

Usage: python tests/fixtures/qr/make_demo_touchpoint.py
Requires: cryptography (pip install cryptography)
"""
from __future__ import annotations

import base64
import datetime as dt
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

HERE = Path(__file__).resolve().parent
FAR_FUTURE = "2030-01-01T00:00:00Z"
PAST = "2020-01-01T00:00:00Z"


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def envelope(payload: dict, priv: Ed25519PrivateKey) -> dict:
    c = canonical(payload)
    return {"v": 1, "c": b64u(c), "s": b64u(priv.sign(c))}


def base_payload(**over) -> dict:
    p = {
        "issuer_id": "trueway.editorial",
        "key_id": "touch-issuer-demo-1",
        "touchpoint_id": "demo-nalanda-museum-entry",
        "place_id": "in-bihar-nalanda-museum",
        "pack_id": "in-bihar-buddhist-circuit",
        "issued_at": "2026-10-10T00:00:00Z",
        "expires_at": FAR_FUTURE,
        "site_serial": "DEMO-PLATE-001",
        "human_label": "Nalanda Archaeological Museum - entry (DEMO)",
    }
    p.update(over)
    return p


def main() -> None:
    priv = Ed25519PrivateKey.generate()
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    pub = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    forged_priv = Ed25519PrivateKey.generate()  # valid key, NOT in trust store

    good = envelope(base_payload(), priv)
    (HERE / "demo_touchpoint_envelope.json").write_text(json.dumps(good, indent=1))
    (HERE / "demo_touchpoint_qr.txt").write_text(
        f"tw://place/v1/{good['c']}.{good['s']}")
    (HERE / "expired_touchpoint_envelope.json").write_text(json.dumps(
        envelope(base_payload(expires_at=PAST), priv), indent=1))
    # Forged: valid envelope bytes whose signature is corrupted.
    forged = dict(good)
    sig = bytearray(base64.urlsafe_b64decode(good["s"] + "=="))
    sig[7] ^= 0xFF
    forged["s"] = b64u(bytes(sig))
    (HERE / "forged_touchpoint_envelope.json").write_text(json.dumps(forged, indent=1))
    (HERE / "unknownissuer_touchpoint_envelope.json").write_text(json.dumps(
        envelope(base_payload(key_id="attacker-key-1"), forged_priv), indent=1))
    (HERE / "trust_store.json").write_text(json.dumps({
        "note": "DEMO trust store. Release keys are pinned via signed trust-store update (§9.3).",
        "issuers": [{
            "issuer_id": "trueway.editorial",
            "key_id": "touch-issuer-demo-1",
            "pubkey_b64u": b64u(pub),
            "status": "DEMO",
        }],
    }, indent=1))
    # Automatically sync trust_store.json and fixtures to Android assets & test resources
    root_dir = HERE.parent.parent.parent
    app_assets_trust = root_dir / "android/app/src/main/assets/touch_issuers.json"
    if app_assets_trust.parent.is_dir():
        app_assets_trust.write_text((HERE / "trust_store.json").read_text(encoding="utf-8"), encoding="utf-8")
    test_res_qr = root_dir / "android/app/src/test/resources/qr"
    if test_res_qr.is_dir():
        for fn in (
            "demo_touchpoint_envelope.json",
            "demo_touchpoint_qr.txt",
            "expired_touchpoint_envelope.json",
            "forged_touchpoint_envelope.json",
            "unknownissuer_touchpoint_envelope.json",
            "trust_store.json",
        ):
            (test_res_qr / fn).write_text((HERE / fn).read_text(encoding="utf-8"), encoding="utf-8")
    print("wrote demo + expired + forged + unknown-issuer envelopes and synced trust_store.json to Android assets & test resources")
    print("DO NOT commit any private key — none was written (ephemeral, in-memory only).")


if __name__ == "__main__":
    main()
