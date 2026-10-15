"""TrueWay distribution stub — blueprint §20.1/§20.5 (Days 11-12 scaffold).

No inference here: metadata + immutable bytes + opt-in feedback queues.
Pack bytes must come from pack-builder; the server never invents content.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="TrueWay pack distribution (stub)")

PACK_ID = "in-bihar-buddhist-circuit"
LATEST = "2026.10.1"


class Feedback(BaseModel):
    # Bounded so the opt-in feedback endpoints are not an unbounded write
    # surface. These are UNAUTHENTICATED stubs: wire auth + rate limiting +
    # persistence policy (§13.5) before storing anything server-side.
    place_id: str | None = Field(default=None, max_length=128)
    text: str = Field(default="", max_length=2000)
    contact: str | None = Field(default=None, max_length=256)


@app.get("/v1/regions")
def regions(lang: str = "en"):
    return {"regions": [{"pack_id": PACK_ID, "lang": lang,
                         "title": "Bihar Buddhist Circuit (demonstrator)"}]}


@app.get("/v1/regions/{pack_id}/releases/latest")
def latest(pack_id: str):
    if pack_id != PACK_ID:
        raise HTTPException(404, "unknown region pack")
    return {"pack_id": pack_id, "release_version": LATEST,
            "schema_version": 3, "place_count": 15,
            "content_locales": ["en", "hi"]}


@app.get("/v1/packs/{pack_id}/{version}/manifest.cjson")
def manifest(pack_id: str, version: str):
    if (pack_id, version) != (PACK_ID, LATEST):
        raise HTTPException(404, "no such release")
    return {"notice": "serve the byte-identical manifest.cjson from the built .twpkg"}


# §20.5 component byte-serving (the 7th endpoint). Allowlisted component names
# only — the stub never touches the filesystem, and an unknown or traversal-y
# name is a flat 404 (no path is ever joined to disk here).
_PACK_COMPONENTS = {
    "content/places.sqlite", "ATTRIBUTIONS.json", "LICENSES.json",
    "CHANGELOG.md", "manifest.ed25519",
}


@app.get("/v1/packs/{pack_id}/{version}/{component:path}")
def component(pack_id: str, version: str, component: str):
    if (pack_id, version) != (PACK_ID, LATEST):
        raise HTTPException(404, "no such release")
    if component not in _PACK_COMPONENTS:
        raise HTTPException(404, "unknown component")
    return {"notice": f"serve byte-identical {component} from the built .twpkg",
            "component": component}


@app.get("/v1/keys/publishers")
def publishers():
    return {"notice": "signed trust-store response only; pin key IDs in-app (§9.3)"}


@app.post("/v1/feedback/coverage")
def coverage(fb: Feedback):
    # Explicit opt-in; coarse request only, no raw photo (§5.3 F115).
    return {"queued": True, "kind": "coverage", "place_id": fb.place_id}


@app.post("/v1/feedback/correction")
def correction(fb: Feedback):
    # Curated moderation queue (§13.5); never auto-publishes.
    return {"queued": True, "kind": "correction", "place_id": fb.place_id}
