"""TrueWay pack distribution server & regional catalog — blueprint §20.1, §20.5.

No inference here: metadata + immutable bytes + opt-in feedback queues.
Pack bytes come from pack-builder / dist archives; the server never invents content.
"""
from __future__ import annotations

import json
import mimetypes
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pack-builder"))

try:
    from regional_catalog import RegionalPackCatalog, default_catalog
except ImportError:
    default_catalog = None

app = FastAPI(title="TrueWay pack distribution & regional catalog")


class Feedback(BaseModel):
    # Bounded so the opt-in feedback endpoints are not an unbounded write
    # surface. These are UNAUTHENTICATED stubs: wire auth + rate limiting +
    # persistence policy (§13.5) before storing anything server-side.
    place_id: Optional[str] = Field(default=None, max_length=128)
    text: str = Field(default="", max_length=2000)
    contact: Optional[str] = Field(default=None, max_length=256)


def _get_catalog() -> RegionalPackCatalog:
    if default_catalog is not None:
        return default_catalog
    return RegionalPackCatalog()


@app.get("/v1/regions")
def regions(lang: str = "en"):
    catalog = _get_catalog()
    pack_list = catalog.list_regions(lang=lang)
    return {"regions": pack_list}


@app.get("/v1/regions/{pack_id}/releases/latest")
def latest(pack_id: str):
    catalog = _get_catalog()
    rel = catalog.get_latest_release(pack_id)
    if not rel:
        raise HTTPException(404, f"unknown region pack: {pack_id}")
    return rel


@app.get("/v1/packs/{pack_id}/{version}/manifest.cjson")
def manifest(pack_id: str, version: str):
    catalog = _get_catalog()
    pack = catalog.get(pack_id)
    if not pack:
        raise HTTPException(404, f"unknown region pack: {pack_id}")
    if version != pack.release_version:
        raise HTTPException(404, f"release version {version} not found for pack {pack_id}")

    # Serve the byte-identical manifest.cjson from the built .twpkg when present
    manifest_bytes = catalog.read_manifest(pack_id, version)
    if manifest_bytes:
        return Response(content=manifest_bytes, media_type="application/json")

    return {
        "notice": "serve the byte-identical manifest.cjson from the built .twpkg",
        "pack_id": pack_id,
        "release_version": version,
    }


# §20.5 component byte-serving allowlist
_ALLOWED_COMPONENTS_PREFIXES = (
    "content/",
    "audio/",
    "images/",
    "vision/",
    "translations/",
    "maps/",
)
_ALLOWED_EXACT_COMPONENTS = {
    "ATTRIBUTIONS.json",
    "LICENSES.json",
    "CHANGELOG.md",
    "manifest.ed25519",
    "manifest.cjson",
}


def _is_safe_component(component: str) -> bool:
    norm = component.replace("\\", "/").lstrip("/")
    parts = norm.split("/")
    if ".." in parts:
        return False
    if norm in _ALLOWED_EXACT_COMPONENTS:
        return True
    return any(norm.startswith(pfx) for pfx in _ALLOWED_COMPONENTS_PREFIXES)


@app.get("/v1/packs/{pack_id}/{version}/{component:path}")
def component(pack_id: str, version: str, component: str):
    catalog = _get_catalog()
    pack = catalog.get(pack_id)
    if not pack:
        raise HTTPException(404, f"unknown region pack: {pack_id}")
    if version != pack.release_version:
        raise HTTPException(404, f"release version {version} not found for pack {pack_id}")

    if not _is_safe_component(component):
        raise HTTPException(404, f"unknown or disallowed component: {component}")

    # Serve byte-identical component from the built .twpkg when available
    comp_bytes = catalog.read_component(pack_id, version, component)
    if comp_bytes is not None:
        mime, _ = mimetypes.guess_type(component)
        return Response(content=comp_bytes, media_type=mime or "application/octet-stream")

    return {
        "notice": f"serve byte-identical {component} from the built .twpkg",
        "pack_id": pack_id,
        "release_version": version,
        "component": component,
    }


@app.get("/v1/keys/publishers")
def publishers():
    trust_file = ROOT / "tests" / "fixtures" / "qr" / "trust_store.json"
    if trust_file.is_file():
        try:
            return json.loads(trust_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"notice": "signed trust-store response only; pin key IDs in-app (§9.3)"}


@app.post("/v1/feedback/coverage")
def coverage(fb: Feedback):
    # Explicit opt-in; coarse request only, no raw photo (§5.3 F115).
    return {"queued": True, "kind": "coverage", "place_id": fb.place_id}


@app.post("/v1/feedback/correction")
def correction(fb: Feedback):
    # Curated moderation queue (§13.5); never auto-publishes.
    return {"queued": True, "kind": "correction", "place_id": fb.place_id}
