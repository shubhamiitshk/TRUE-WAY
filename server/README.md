# server/ — pack distribution stub (blueprint §20.1, §20.5)

Online-only publishing path; **never in the scan/read path** (§8.1).
Serves release metadata + immutable pack bytes built by
`pack-builder/build_pack.py`, plus explicit opt-in feedback queues.

```powershell
pip install fastapi uvicorn
uvicorn main:app --reload --port 8080
```

Endpoints (§20.5 planning contract):

- `GET /v1/regions?lang=en`
- `GET /v1/regions/in-bihar-buddhist-circuit/releases/latest`
- `GET /v1/packs/{pack_id}/{version}/manifest.cjson`
- `GET /v1/packs/{pack_id}/{version}/{component}`
- `GET /v1/keys/publishers` (signed trust-store response only)
- `POST /v1/feedback/coverage` (explicit opt-in; no raw photo)
- `POST /v1/feedback/correction` (moderation queue)

## Current State (v3.0)

**Stub implementation** — all endpoints return notice strings.
- No database persistence
- No authentication / rate limiting
- No TLS configuration
- No actual pack file serving (returns notice string instead of bytes)

## Production Requirements

- [ ] Object storage / CDN integration for pack component serving
- [ ] Database for release metadata + version tracking
- [ ] mTLS or API key authentication for `/v1/keys/publishers`
- [ ] Rate limiting on feedback endpoints
- [ ] TLS termination
- [ ] Request logging for audit
- [ ] Health check endpoint (`/healthz`)
- [ ] CORS configuration for web clients

## Security Notes

- Component names are allowlisted in `GET /v1/packs/.../{component}` to prevent path traversal
- Feedback payloads bounded (max 2000 chars)
- Feedback is opt-in; no raw photos/audio accepted
- Trust store (`/v1/keys/publishers`) must serve signed publisher key response