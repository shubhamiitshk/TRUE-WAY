# ADR-0006: Ed25519 Cryptographic Pack Signing and Tamper Verification

- **Status:** Accepted (2026-10-11)
- **Source:** `docs/SYSTEM_ARCHITECTURE_SPECIFICATION.md` §6; Blueprint §9
- **Context:** TrueWay packs contain historical claims, visitor safety guidelines, and ML reference embeddings. Corrupted, outdated, or hostile packs must be rejected before activation to prevent misinformation, security vulnerabilities, or app crashes.

## Decision

1. Use **Ed25519 (RFC 8032)** for all pack manifest signatures.
2. The publisher compiles a deterministic, sorted, whitespace-minimized canonical JSON manifest (`manifest.cjson`, RFC 8785) and signs it, outputting a detached `manifest.ed25519` signature.
3. Every payload file within the `.twpkg` archive is indexed with its exact byte count and SHA-256 digest.
4. On the Android device, the verification state machine:
   - Verifies the detached Ed25519 signature against pinned publisher public keys **before** trusting any manifest data.
   - Verifies SHA-256 hashes of all components before unzipping.
   - Performs a security audit on zip members (rejects directory traversal `..`, symlinks, and executable files).
   - Any failure triggers immediate staging purge and preserves the previously active pack.

## Consequences

- Cryptographic guarantee that only reviewed and approved editorial content can activate on a user's device.
- Fulfills Gate 2 (100% rejection of hostile pack fixtures).
