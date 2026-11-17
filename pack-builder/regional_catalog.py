"""TrueWay Regional Pack Distribution Catalog — blueprint §9.2, §20.1, §20.5.

Manages regional pack definitions, versions, release metadata, and asset distribution.
Cleanly separates regional definitions from the demonstrator pack and allows
dynamic discovery and serving of .twpkg archives.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class RegionalPackDefinition:
    pack_id: str
    title: str
    description: str
    release_version: str = "2026.10.1"
    schema_version: int = 3
    content_locales: List[str] = field(default_factory=lambda: ["en", "hi"])
    place_count: int = 0
    publisher_id: str = "trueway.editorial"
    signing_key_id: str = "pubkey-2026-q4"
    schema_file: Optional[str] = None
    seed_file: Optional[str] = None
    rights_registry: Optional[str] = None
    audio_dir: Optional[str] = None
    images_dir: Optional[str] = None
    vision_dir: Optional[str] = None
    bundle_filename: Optional[str] = None
    bundle_bytes: Optional[int] = None
    bundle_sha256: Optional[str] = None
    components: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegionalPackDefinition":
        valid_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# Standard canonical corridors defined by TrueWay
DEFAULT_REGIONS: Dict[str, RegionalPackDefinition] = {
    "in-bihar-buddhist-circuit": RegionalPackDefinition(
        pack_id="in-bihar-buddhist-circuit",
        title="Bihar Buddhist Circuit (demonstrator)",
        description="Bodh Gaya, Nalanda, and Rajgir flagship Buddhist heritage sites (15 POIs, bilingual audio, Then & Now comparisons, TWVEC002 vector index).",
        release_version="2026.10.1",
        schema_version=3,
        content_locales=["en", "hi"],
        place_count=15,
        publisher_id="trueway.editorial",
        signing_key_id="pubkey-2026-q4",
        schema_file="content/schema/publication_schema.sql",
        seed_file="content/seed/seed_demo.sql",
        rights_registry="content/seed/rights_registry.json",
        audio_dir="content/audio",
        images_dir="content/images/then_now",
        vision_dir="content/vision",
        bundle_filename="trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg",
    ),
    "in-golden-triangle": RegionalPackDefinition(
        pack_id="in-golden-triangle",
        title="India Golden Triangle Corridor",
        description="Delhi, Agra, and Jaipur cultural circuit: Taj Mahal, Qutub Minar, Red Fort, Hawa Mahal, Amer Fort, Agra Fort, Fatehpur Sikri, Humayun's Tomb, and City Palace Jaipur.",
        release_version="2026.10.1",
        schema_version=3,
        content_locales=["en", "hi"],
        place_count=9,
        publisher_id="trueway.editorial",
        signing_key_id="pubkey-2026-q4",
        schema_file="content/schema/publication_schema.sql",
        seed_file="content/seed/seed_golden_triangle.sql",
        rights_registry="content/seed/rights_registry.json",
        bundle_filename="trueway-in-golden-triangle-2026.10.1.twpkg",
    ),
    "global-icons-tier1": RegionalPackDefinition(
        pack_id="global-icons-tier1",
        title="World Icons Tier-1 Showcase",
        description="Global cultural icons: Eiffel Tower, Colosseum, Pyramids of Giza, Angkor Wat, Machu Picchu, and Statue of Liberty.",
        release_version="2026.10.1",
        schema_version=3,
        content_locales=["en", "fr", "es", "hi"],
        place_count=6,
        publisher_id="trueway.editorial",
        signing_key_id="pubkey-2026-q4",
        schema_file="content/schema/publication_schema.sql",
        seed_file="content/seed/seed_global_icons.sql",
        rights_registry="content/seed/rights_registry.json",
        bundle_filename="trueway-global-icons-tier1-2026.10.1.twpkg",
    ),
}


class RegionalPackCatalog:
    """Regional pack distribution catalog supporting multi-region discovery and distribution."""

    def __init__(self, catalog_file: Optional[Path] = None, dist_dir: Optional[Path] = None) -> None:
        self.catalog_file = catalog_file or (ROOT / "pack-builder" / "catalog.json")
        self.dist_dir = dist_dir or (ROOT / "dist")
        self.regions: Dict[str, RegionalPackDefinition] = dict(DEFAULT_REGIONS)
        if self.catalog_file.is_file():
            self.load_from_file(self.catalog_file)
        if self.dist_dir.is_dir():
            self.scan_dist(self.dist_dir)

    def register(self, pack: RegionalPackDefinition) -> None:
        self.regions[pack.pack_id] = pack

    def get(self, pack_id: str) -> Optional[RegionalPackDefinition]:
        return self.regions.get(pack_id)

    def list_regions(self, lang: str = "en") -> List[Dict[str, Any]]:
        result = []
        for pack in self.regions.values():
            result.append({
                "pack_id": pack.pack_id,
                "title": pack.title,
                "description": pack.description,
                "lang": lang,
                "latest_version": pack.release_version,
                "place_count": pack.place_count,
                "content_locales": pack.content_locales,
                "bundle_available": self.has_bundle(pack.pack_id, pack.release_version),
            })
        return result

    def get_latest_release(self, pack_id: str) -> Optional[Dict[str, Any]]:
        pack = self.get(pack_id)
        if not pack:
            return None
        return {
            "pack_id": pack.pack_id,
            "release_version": pack.release_version,
            "schema_version": pack.schema_version,
            "place_count": pack.place_count,
            "content_locales": pack.content_locales,
            "publisher_id": pack.publisher_id,
            "signing_key_id": pack.signing_key_id,
            "bundle_filename": pack.bundle_filename or f"trueway-{pack.pack_id}-{pack.release_version}.twpkg",
            "bundle_bytes": pack.bundle_bytes,
            "bundle_sha256": pack.bundle_sha256,
        }

    def get_bundle_path(self, pack_id: str, version: Optional[str] = None) -> Optional[Path]:
        pack = self.get(pack_id)
        ver = version or (pack.release_version if pack else "2026.10.1")
        filename = f"trueway-{pack_id}-{ver}.twpkg"
        candidate = self.dist_dir / filename
        if candidate.is_file():
            return candidate
        # Look for any twpkg matching pack_id and version in dist_dir
        if self.dist_dir.is_dir():
            for p in self.dist_dir.glob(f"*{pack_id}*{ver}*.twpkg"):
                if p.is_file():
                    return p
        return None

    def has_bundle(self, pack_id: str, version: Optional[str] = None) -> bool:
        return self.get_bundle_path(pack_id, version) is not None

    def read_manifest(self, pack_id: str, version: str) -> Optional[bytes]:
        bundle = self.get_bundle_path(pack_id, version)
        if not bundle:
            return None
        try:
            with zipfile.ZipFile(bundle, "r") as z:
                return z.read("manifest.cjson")
        except Exception:
            return None

    def read_component(self, pack_id: str, version: str, component_path: str) -> Optional[bytes]:
        bundle = self.get_bundle_path(pack_id, version)
        if not bundle:
            return None
        # Sanitize path to prevent zip traversal
        norm = component_path.replace("\\", "/").lstrip("/")
        if ".." in norm.split("/"):
            return None
        try:
            with zipfile.ZipFile(bundle, "r") as z:
                if norm in z.namelist():
                    return z.read(norm)
        except Exception:
            pass
        return None

    def scan_dist(self, dist_dir: Path) -> int:
        """Discovers and registers .twpkg packages from dist directory."""
        if not dist_dir.is_dir():
            return 0
        count = 0
        for pkg_path in dist_dir.glob("*.twpkg"):
            try:
                with zipfile.ZipFile(pkg_path, "r") as z:
                    if "manifest.cjson" not in z.namelist():
                        continue
                    mdata = json.loads(z.read("manifest.cjson").decode("utf-8"))
                    pack_id = mdata.get("pack_id")
                    if not pack_id:
                        continue
                    raw = pkg_path.read_bytes()
                    h = hashlib.sha256(raw).hexdigest()
                    existing = self.regions.get(pack_id)
                    title = existing.title if existing else f"{pack_id} regional pack"
                    desc = existing.description if existing else f"Offline pack for {pack_id}"
                    names = [n for n in z.namelist() if not n.endswith("/")]
                    reg = RegionalPackDefinition(
                        pack_id=pack_id,
                        title=title,
                        description=desc,
                        release_version=mdata.get("release_version", "2026.10.1"),
                        schema_version=mdata.get("schema_version", 3),
                        content_locales=mdata.get("content_locales", ["en", "hi"]),
                        place_count=mdata.get("place_count", 0),
                        publisher_id=mdata.get("publisher_id", "trueway.editorial"),
                        signing_key_id=mdata.get("signing_key_id", "pubkey-2026-q4"),
                        schema_file=existing.schema_file if existing else None,
                        seed_file=existing.seed_file if existing else None,
                        rights_registry=existing.rights_registry if existing else None,
                        audio_dir=existing.audio_dir if existing else None,
                        images_dir=existing.images_dir if existing else None,
                        vision_dir=existing.vision_dir if existing else None,
                        bundle_filename=pkg_path.name,
                        bundle_bytes=len(raw),
                        bundle_sha256=h,
                        components=names,
                    )
                    self.regions[pack_id] = reg
                    count += 1
            except Exception:
                continue
        return count

    def save_to_file(self, path: Optional[Path] = None) -> None:
        target = path or self.catalog_file
        target.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "catalog_format": "trueway.regional_catalog.v1",
            "schema_version": 3,
            "regions": {pid: pack.to_dict() for pid, pack in self.regions.items()},
        }
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_from_file(self, path: Path) -> None:
        if not path.is_file():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            regions_data = data.get("regions", {})
            for pid, pdata in regions_data.items():
                self.regions[pid] = RegionalPackDefinition.from_dict(pdata)
        except Exception:
            pass


default_catalog = RegionalPackCatalog()
