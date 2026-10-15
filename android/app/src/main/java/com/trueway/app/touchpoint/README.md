# touchpoint/ — signed site-code resolver (blueprint §11, F014)

P0 = in-app resolver. P1 = partner plate deployment (not this package).

| File | Role |
|---|---|
| `Touchpoint.kt` | `TouchpointParser` (only `tw://place/v1/<c>.<s>` + `{"v":1,"c","s"}`; URLs never touched) + `TouchpointVerifier` (pinned-issuer Ed25519, expiry, installed-corpus resolution). Pure + BC: JVM-tested with real crypto. |
| `../scan/QrScanScreen.kt` | ML Kit QR + CameraX analysis, result routing: Valid→verified card (issuer, label, plate serial, mismatch route), ValidUnknownPlace→honest missing-pack, Invalid→unverified warning + search. |
| `../../test/.../TouchpointTest.kt` | 7/7 with real Ed25519: Python-signed demo/expired/forged/unknown-issuer fixtures + JVM-signed unknown-place round-trip; URLs/WiFi tags rejected. |

## Security notes (§15.3)

- No WebView, no `ACTION_VIEW`, no fetch: scanned text is data, matched
  against one scheme. A pasted malicious QR with a valid signature for a
  *different* place still opens only the local card for its signed
  `place_id`, with serial + mismatch report — spoofing a location requires
  the issuer's private key or physical plate swap, both handled by
  revocation + on-screen context, not by trust in the sticker.
- Trust store (`assets/touch_issuers.json`, DEMO key) moves to signed
  trust-store updates at release (§9.3); release signing keys never enter
  the repo (fixtures use ephemeral keys, `make_demo_touchpoint.py`).
