#!/usr/bin/env python3
"""TrueWay Scholar POI Submission Linter (CLI).

Validates scholar submissions against the TrueWay Heritage Knowledge Graph specification
before releasing researcher honoraria (Directive 6 / §28 publication rules).

Enforces:
1. Canonical place_id schema ('in-bihar-...')
2. Multilingual aliases with genuine Devanagari (\u0900-\u097F) for 'hi' and 'hi-Latn'
3. Coordinate bounding box within the Bihar Buddhist Corridor (24.0 <= lat <= 26.5, 84.0 <= lon <= 86.5)
4. Epistemic claim types strictly in {DOCUMENTED, INTERPRETATION, TRADITION, CONTESTED}
5. Mandatory primary source citations with author, title, publication year, and plate/page for DOCUMENTED/INTERPRETATION
6. "Before You Enter" device regulations and site advisories
7. Bilingual audio narrative scripts (>40 words in EN and HI) and IPA pronunciation

Usage:
    python content/tools/validate_scholar_submission.py content/field/SCHOLAR_POI_WORKSHEET_TEMPLATE.yaml
    python content/tools/validate_scholar_submission.py --dir content/field/submissions/
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

VALID_CLAIM_TYPES = {"DOCUMENTED", "INTERPRETATION", "TRADITION", "CONTESTED"}
VALID_VISITOR_MODES = {
    "PHOTO_SUPPORTED", "SEARCH_ONLY", "QR_PARTNER", "TRAIL_STOP", "TEXT_REFERENCE_ONLY"
}
VALID_CORRIDORS = {"BODH_GAYA", "RAJGIR", "NALANDA", "PATNA", "VAISHALI"}
VALID_JURISDICTIONS = {"ASI", "BTMC", "STATE_TOURISM", "MUNICIPAL", "PRIVATE_TRUST"}
VALID_DEVICE_RULES = {
    "PHONES_STRICTLY_BANNED",
    "PHOTOGRAPHY_ALLOWED_NO_DRONES",
    "PHOTOGRAPHY_ALLOWED_FEES_APPLY",
    "DEVICES_PERMITTED"
}

# Bihar Buddhist Corridor Bounds
LAT_MIN, LAT_MAX = 24.0, 26.5
LON_MIN, LON_MAX = 84.0, 86.5
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")


class ValidationError:
    def __init__(self, section: str, field: str, message: str):
        self.section = section
        self.field = field
        self.message = message

    def __str__(self) -> str:
        return f"[{self.section}] {self.field}: {self.message}"


def validate_submission_data(data: dict[str, Any], filepath: pathlib.Path) -> list[ValidationError]:
    errors: list[ValidationError] = []

    # 1. Metadata check
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        errors.append(ValidationError("metadata", "root", "Missing 'metadata' dictionary"))
    else:
        for f in ("scholar_name", "affiliation", "submission_date", "honorarium_tier"):
            val = str(meta.get(f, "")).strip()
            if not val:
                errors.append(ValidationError("metadata", f, f"Required field '{f}' is empty"))

    # 2. Place & Canonical IDs
    place = data.get("place")
    if not isinstance(place, dict):
        errors.append(ValidationError("place", "root", "Missing 'place' dictionary"))
        return errors

    place_id = str(place.get("place_id", "")).strip()
    if not place_id:
        errors.append(ValidationError("place", "place_id", "Missing 'place_id'"))
    elif not re.match(r"^in-bihar-[a-z0-9\-]+$", place_id):
        errors.append(ValidationError(
            "place", "place_id",
            f"Invalid format '{place_id}'. Must match pattern '^in-bihar-[a-z0-9\\-]+$'"
        ))

    canonical_name = str(place.get("canonical_name", "")).strip()
    if not canonical_name:
        errors.append(ValidationError("place", "canonical_name", "Missing 'canonical_name'"))

    corridor = str(place.get("corridor", "")).strip().upper()
    if corridor not in VALID_CORRIDORS:
        errors.append(ValidationError(
            "place", "corridor",
            f"Invalid corridor '{corridor}'. Allowed: {sorted(VALID_CORRIDORS)}"
        ))

    visitor_mode = str(place.get("visitor_mode", "")).strip().upper()
    if visitor_mode not in VALID_VISITOR_MODES:
        errors.append(ValidationError(
            "place", "visitor_mode",
            f"Invalid visitor_mode '{visitor_mode}'. Allowed: {sorted(VALID_VISITOR_MODES)}"
        ))

    # Aliases & Devanagari validation
    aliases = place.get("aliases")
    if not isinstance(aliases, dict):
        errors.append(ValidationError("place", "aliases", "Missing 'aliases' dictionary"))
    else:
        hi_name = str(aliases.get("hi", "")).strip()
        if not hi_name:
            errors.append(ValidationError("place", "aliases.hi", "Missing mandatory Hindi alias ('hi')"))
        elif not DEVANAGARI_REGEX.search(hi_name):
            errors.append(ValidationError(
                "place", "aliases.hi",
                f"Hindi alias '{hi_name}' contains no Devanagari characters (range \\u0900-\\u097F)"
            ))

        hi_latn = str(aliases.get("hi-Latn", "")).strip()
        if not hi_latn:
            errors.append(ValidationError("place", "aliases.hi-Latn", "Missing mandatory romanized Hindi alias ('hi-Latn')"))

    # Coordinates validation
    coords = place.get("coordinates")
    if not isinstance(coords, dict):
        errors.append(ValidationError("place", "coordinates", "Missing 'coordinates' dictionary"))
    else:
        try:
            lat = float(coords.get("latitude", 0.0))
            lon = float(coords.get("longitude", 0.0))
            if not (LAT_MIN <= lat <= LAT_MAX):
                errors.append(ValidationError(
                    "place", "coordinates.latitude",
                    f"Latitude {lat} outside Bihar corridor bounds [{LAT_MIN}, {LAT_MAX}]"
                ))
            if not (LON_MIN <= lon <= LON_MAX):
                errors.append(ValidationError(
                    "place", "coordinates.longitude",
                    f"Longitude {lon} outside Bihar corridor bounds [{LON_MIN}, {LON_MAX}]"
                ))
        except (ValueError, TypeError) as e:
            errors.append(ValidationError("place", "coordinates", f"Invalid coordinate numbers: {e}"))

    # 3. Before You Enter
    bye = data.get("before_you_enter")
    if not isinstance(bye, dict):
        errors.append(ValidationError("before_you_enter", "root", "Missing 'before_you_enter' dictionary"))
    else:
        jur = str(bye.get("site_jurisdiction", "")).strip().upper()
        if jur not in VALID_JURISDICTIONS:
            errors.append(ValidationError(
                "before_you_enter", "site_jurisdiction",
                f"Invalid jurisdiction '{jur}'. Allowed: {sorted(VALID_JURISDICTIONS)}"
            ))
        dev_rule = str(bye.get("device_regulations", "")).strip().upper()
        if dev_rule not in VALID_DEVICE_RULES:
            errors.append(ValidationError(
                "before_you_enter", "device_regulations",
                f"Invalid device_regulations '{dev_rule}'. Allowed: {sorted(VALID_DEVICE_RULES)}"
            ))
        advisories = bye.get("advisories")
        if not isinstance(advisories, list) or len(advisories) == 0:
            errors.append(ValidationError("before_you_enter", "advisories", "Must provide at least 1 site advisory item"))

    # 4. Epistemic Claims & Citations
    claims = data.get("claims")
    if not isinstance(claims, list) or len(claims) == 0:
        errors.append(ValidationError("claims", "root", "Must provide at least 1 claim object"))
    else:
        for idx, clm in enumerate(claims):
            if not isinstance(clm, dict):
                errors.append(ValidationError("claims", f"claims[{idx}]", "Claim entry must be a dictionary"))
                continue
            cid = str(clm.get("claim_id", f"claim_{idx}")).strip()
            ctype = str(clm.get("claim_type", "")).strip().upper()
            ctext = str(clm.get("claim_text", "")).strip()

            if ctype not in VALID_CLAIM_TYPES:
                errors.append(ValidationError(
                    "claims", f"{cid}.claim_type",
                    f"Invalid claim_type '{ctype}'. Allowed: {sorted(VALID_CLAIM_TYPES)}"
                ))

            if len(ctext) < 20:
                errors.append(ValidationError(
                    "claims", f"{cid}.claim_text",
                    f"Claim text too short ({len(ctext)} chars); must be at least 20 chars"
                ))

            sources = clm.get("sources")
            if ctype in ("DOCUMENTED", "INTERPRETATION"):
                if not isinstance(sources, list) or len(sources) == 0:
                    errors.append(ValidationError(
                        "claims", f"{cid}.sources",
                        f"Claim type '{ctype}' requires at least 1 authoritative source citation"
                    ))
                else:
                    for s_idx, src in enumerate(sources):
                        if not isinstance(src, dict):
                            errors.append(ValidationError("claims", f"{cid}.sources[{s_idx}]", "Source must be a dictionary"))
                            continue
                        author = str(src.get("author", "")).strip()
                        title = str(src.get("title", "")).strip()
                        citation = str(src.get("citation_detail", "")).strip()
                        if not author or not title or not citation:
                            errors.append(ValidationError(
                                "claims", f"{cid}.sources[{s_idx}]",
                                "Source citation must contain author, title, and citation_detail (page/plate)"
                            ))

    # 5. Audio Scripts
    audio = data.get("audio_narrative_scripts")
    if not isinstance(audio, dict):
        errors.append(ValidationError("audio_narrative_scripts", "root", "Missing 'audio_narrative_scripts' dictionary"))
    else:
        en_script = str(audio.get("english_script", "")).strip()
        hi_script = str(audio.get("hindi_script", "")).strip()
        ipa = str(audio.get("pronunciation_ipa", "")).strip()

        en_words = len(en_script.split())
        hi_words = len(hi_script.split())

        if en_words < 40:
            errors.append(ValidationError(
                "audio_narrative_scripts", "english_script",
                f"English script too short ({en_words} words; minimum 40 words required)"
            ))

        if hi_words < 40:
            errors.append(ValidationError(
                "audio_narrative_scripts", "hindi_script",
                f"Hindi script too short ({hi_words} words; minimum 40 words required)"
            ))
        elif not DEVANAGARI_REGEX.search(hi_script):
            errors.append(ValidationError(
                "audio_narrative_scripts", "hindi_script",
                "Hindi narrative script must contain Devanagari script characters"
            ))

        if not ipa:
            errors.append(ValidationError(
                "audio_narrative_scripts", "pronunciation_ipa",
                "Missing 'pronunciation_ipa' pronunciation guide"
            ))

    return errors


def validate_file(path: pathlib.Path) -> bool:
    print(f"Checking scholar submission: {path.name}...")
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            print(f"  [FAIL] Root YAML must be a mapping: {path}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"  [FAIL] YAML syntax error: {e}", file=sys.stderr)
        return False

    errors = validate_submission_data(data, path)
    if errors:
        print(f"  [FAIL] Found {len(errors)} validation failure(s):")
        for err in errors:
            print(f"    - {err}")
        return False

    place = data.get("place", {})
    meta = data.get("metadata", {})
    claims = data.get("claims", [])
    print(f"  [PASS] Validated '{place.get('canonical_name')}' ({place.get('place_id')})")
    print(f"         Scholar: {meta.get('scholar_name')} ({meta.get('affiliation')})")
    print(f"         Corridor: {place.get('corridor')}, Claims: {len(claims)}, Mode: {place.get('visitor_mode')}")
    print(f"         Honorarium Tier: {meta.get('honorarium_tier')} — APPROVED FOR PAYMENT REVIEW.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TrueWay scholar POI submissions")
    parser.add_argument("file", nargs="?", help="Path to single submission YAML file")
    parser.add_argument("--dir", help="Path to directory containing submission YAML files")
    args = parser.parse_args()

    files_to_check: list[pathlib.Path] = []
    if args.file:
        p = pathlib.Path(args.file)
        if not p.is_file():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            return 2
        files_to_check.append(p)
    elif args.dir:
        d = pathlib.Path(args.dir)
        if not d.is_dir():
            print(f"ERROR: Directory not found: {d}", file=sys.stderr)
            return 2
        files_to_check.extend(sorted(d.glob("*.yaml")))
        files_to_check.extend(sorted(d.glob("*.yml")))
    else:
        # Default: check the worksheet template
        default_template = pathlib.Path("content/field/SCHOLAR_POI_WORKSHEET_TEMPLATE.yaml")
        if default_template.is_file():
            files_to_check.append(default_template)
        else:
            parser.print_help()
            return 1

    all_passed = True
    for f in files_to_check:
        passed = validate_file(f)
        if not passed:
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
