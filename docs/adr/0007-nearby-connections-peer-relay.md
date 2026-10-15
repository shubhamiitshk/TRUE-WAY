# ADR-0007: Google Nearby Connections for Offline Peer Pack Relay

- **Status:** Accepted (2026-10-11)
- **Source:** `docs/SYSTEM_ARCHITECTURE_SPECIFICATION.md` §8.2; Blueprint §11
- **Context:** Heritage travelers frequently explore remote rural or mountainous sites (e.g. Nalanda ruins, Gridhrakuta Peak in Rajgir) where cellular connectivity is absent. Users who need regional packs should be able to receive them directly from nearby travelers without an internet gateway.

## Decision

1. Adopt **Google Nearby Connections API** (P2P Cluster strategy) using Wi-Fi Direct and Bluetooth Low Energy (BLE) for high-speed device-to-device pack transfer.
2. Receiver verification rule: The receiving device must independently verify the Ed25519 signature and SHA-256 hash tree of the transferred `.twpkg` archive before staging or activating it. Peer transfer confers **zero trust bypass**.
3. UI privacy gating: Pack sharing is strictly user-initiated. Advertising and discovery require explicit user consent and are automatically terminated upon transfer completion or screen exit.

## Consequences

- Enables offline data transfer of regional packs between travelers in zero-internet zones over local P2P channels (Nearby Connections specified P1 path; Wi-Fi Aware NAN is an exploratory research alternative). Measured throughput to be established during field testing on reference hardware.
- Enforces strict security: peer-shared packs must be authentic publisher-signed binaries.
