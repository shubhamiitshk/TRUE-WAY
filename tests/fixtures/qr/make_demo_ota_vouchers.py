#!/usr/bin/env python3
"""
Generate test OTA voucher fixtures for TrueWay.
These are used in CI/CD to test the OTA voucher verification pipeline.

Usage:
    python tests/fixtures/qr/make_demo_ota_vouchers.py

This creates:
    - tests/fixtures/qr/demo_viator_voucher.json
    - tests/fixtures/qr/demo_klook_voucher.json
    - tests/fixtures/qr/demo_mmt_voucher.json
    - tests/fixtures/qr/expired_voucher.json
    - tests/fixtures/qr/bad_signature_voucher.json
"""

import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("ERROR: cryptography package required. Install with: pip install cryptography")
    exit(1)

# Demo partner private keys (in production, these would be held by OTA partners)
DEMO_VIATOR_PRIVATE_KEY = Ed25519PrivateKey.generate()
DEMO_KLOOK_PRIVATE_KEY = Ed25519PrivateKey.generate()
DEMO_MMT_PRIVATE_KEY = Ed25519PrivateKey.generate()

# Demo partner public keys (these would be in the trust store)
DEMO_VIATOR_PUBLIC_KEY = DEMO_VIATOR_PRIVATE_KEY.public_key()
DEMO_KLOOK_PUBLIC_KEY = DEMO_KLOOK_PRIVATE_KEY.public_key()
DEMO_MMT_PUBLIC_KEY = DEMO_MMT_PRIVATE_KEY.public_key()


def b64u(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def generate_voucher(
    partner: str,
    private_key: Ed25519PrivateKey,
    voucher_id: str,
    pack_id: str,
    expires_at: datetime,
    issued_at: datetime = None,
) -> dict:
    """Generate a signed OTA voucher."""
    if issued_at is None:
        issued_at = datetime.now(timezone.utc)

    # Canonical payload (without signature)
    canonical = {
        "v": 1,
        "voucher_id": voucher_id,
        "ota_partner": partner,
        "pack_id": pack_id,
        "expires_at": expires_at.isoformat(),
        "issued_at": issued_at.isoformat(),
    }

    # Sign the canonical JSON
    canonical_bytes = json.dumps(canonical, separators=(',', ':'), sort_keys=True).encode('utf-8')
    signature = private_key.sign(canonical_bytes)

    # Add signature to voucher
    voucher = dict(canonical)
    voucher["signature"] = b64u(signature)

    return voucher


def write_voucher(voucher: dict, path: Path):
    """Write voucher to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(voucher, f, indent=2)
    print(f"Generated: {path}")


def main():
    base_dir = Path(__file__).parent

    # Valid vouchers (expires in 30 days)
    expires_future = datetime.now(timezone.utc) + timedelta(days=30)

    viator_voucher = generate_voucher(
        partner="viator",
        private_key=DEMO_VIATOR_PRIVATE_KEY,
        voucher_id="VIATOR-2026-11-001",
        pack_id="in-bihar-buddhist-circuit",
        expires_at=expires_future,
    )
    write_voucher(viator_voucher, base_dir / "demo_viator_voucher.json")

    klook_voucher = generate_voucher(
        partner="klook",
        private_key=DEMO_KLOOK_PRIVATE_KEY,
        voucher_id="KLOOK-2026-11-001",
        pack_id="in-golden-triangle",
        expires_at=expires_future,
    )
    write_voucher(klook_voucher, base_dir / "demo_klook_voucher.json")

    mmt_voucher = generate_voucher(
        partner="makemytrip",
        private_key=DEMO_MMT_PRIVATE_KEY,
        voucher_id="MMT-2026-11-001",
        pack_id="in-bihar-buddhist-circuit",
        expires_at=expires_future,
    )
    write_voucher(mmt_voucher, base_dir / "demo_mmt_voucher.json")

    # Expired voucher (expired 1 day ago)
    expires_past = datetime.now(timezone.utc) - timedelta(days=1)
    expired_voucher = generate_voucher(
        partner="viator",
        private_key=DEMO_VIATOR_PRIVATE_KEY,
        voucher_id="VIATOR-2026-11-EXPIRED",
        pack_id="in-bihar-buddhist-circuit",
        expires_at=expires_past,
    )
    write_voucher(expired_voucher, base_dir / "expired_voucher.json")

    # Bad signature voucher (tampered)
    bad_sig_voucher = dict(viator_voucher)
    bad_sig_voucher["signature"] = b64u(b"invalid_signature_64_bytes_long_padding_padding_padding_padding")
    write_voucher(bad_sig_voucher, base_dir / "bad_signature_voucher.json")

    # Write trust store for testing
    trust_store = {
        "partners": [
            {
                "partner_id": "viator",
                "key_id": "viator-prod-2026",
                "pubkey_b64u": b64u(DEMO_VIATOR_PUBLIC_KEY.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )),
            },
            {
                "partner_id": "klook",
                "key_id": "klook-prod-2026",
                "pubkey_b64u": b64u(DEMO_KLOOK_PUBLIC_KEY.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )),
            },
            {
                "partner_id": "makemytrip",
                "key_id": "mmt-prod-2026",
                "pubkey_b64u": b64u(DEMO_MMT_PUBLIC_KEY.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )),
            },
        ]
    }
    write_voucher(trust_store, base_dir / "demo_ota_trust_store.json")

    print("\n=== OTA Voucher Test Fixtures Generated ===")
    print(f"Valid vouchers: 3")
    print(f"Expired voucher: 1")
    print(f"Bad signature voucher: 1")
    print(f"Trust store: 1")
    print("\nThese fixtures are used in CI/CD to test the OTA voucher verification pipeline.")
    print("In production, real partner public keys would be used instead of demo keys.")


if __name__ == "__main__":
    main()