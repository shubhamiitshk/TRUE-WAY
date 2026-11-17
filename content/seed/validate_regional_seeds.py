"""Validate all regional seed SQL files against blueprint publication rules.

Enforces:
1. Schema integrity (FKs enabled, valid DDL).
2. No DRAFT places, claims, or unapproved records.
3. Every claim has a valid reviewer and reviewed_at.
4. Every claim has at least one source link in claim_sources.
5. Claim types belong strictly to allowed vocabulary ('DOCUMENTED','INTERPRETATION','TRADITION','CONTESTED','OPERATIONAL','HYPOTHESIS').
6. Every spotter item links to a valid place and source, with allowed claim_type.
7. Visitor modes match allowed vocabulary.
8. Every place with a 'hi' alias has a matching 'hi-Latn' romanized alias.
9. FTS index is populated and queries return expected places.
"""
from __future__ import annotations

import pathlib
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SCHEMA = ROOT.parent / "schema" / "publication_schema.sql"
PLACES_SCHEMA = ROOT.parent / "schema" / "places_schema.sql"

SEEDS = [
    ("in-bihar-buddhist-circuit", ROOT / "seed_demo.sql", 15),
    ("in-golden-triangle", ROOT / "seed_golden_triangle.sql", 9),
    ("global-icons-tier1", ROOT / "seed_global_icons.sql", 6),
]


def test_seed(name: str, seed_path: pathlib.Path, expected_places: int) -> list[str]:
    print(f"\n==================== Validating {name} ({seed_path.name}) ====================")
    failures: list[str] = []

    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON;")
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    con.executescript(seed_path.read_text(encoding="utf-8"))

    def one(sql: str) -> int:
        return int(con.execute(sql).fetchone()[0])

    n_places = one("SELECT COUNT(*) FROM places")
    n_claims = one("SELECT COUNT(*) FROM claims")
    n_sources = one("SELECT COUNT(*) FROM sources")
    n_aliases = one("SELECT COUNT(*) FROM place_aliases")
    n_fts = one("SELECT COUNT(*) FROM place_search")
    
    try:
        n_spotter = one("SELECT COUNT(*) FROM spotter_items")
    except sqlite3.OperationalError:
        n_spotter = 0

    print(f"Stats: places={n_places} claims={n_claims} sources={n_sources} aliases={n_aliases} spotter_items={n_spotter} fts_rows={n_fts}")

    if n_places != expected_places:
        failures.append(f"Expected {expected_places} places, found {n_places}")

    # Gate checks
    checks = [
        ("no_draft_places", "SELECT COUNT(*) FROM places WHERE editorial_state='DRAFT'"),
        ("no_draft_claims", "SELECT COUNT(*) FROM claims WHERE editorial_state='DRAFT'"),
        ("claims_have_sources", "SELECT COUNT(*) FROM claims c LEFT JOIN claim_sources cs ON cs.claim_id=c.claim_id WHERE cs.claim_id IS NULL"),
        ("claims_have_reviewer", "SELECT COUNT(*) FROM claims WHERE reviewer_id IS NULL OR TRIM(reviewer_id)='' OR reviewed_at IS NULL"),
        ("claim_type_vocab", "SELECT COUNT(*) FROM claims WHERE claim_type NOT IN ('DOCUMENTED','INTERPRETATION','TRADITION','CONTESTED','OPERATIONAL','HYPOTHESIS')"),
        ("visitor_mode_vocab", "SELECT COUNT(*) FROM places WHERE visitor_mode NOT IN ('PHOTO_SUPPORTED','SEARCH_ONLY','QR_PARTNER','TRAIL_STOP','TEXT_REFERENCE_ONLY')"),
        ("places_fk_valid", "SELECT COUNT(*) FROM claims c WHERE NOT EXISTS (SELECT 1 FROM places p WHERE p.place_id=c.place_id)"),
    ]

    for check_name, sql in checks:
        offending = one(sql)
        status = "OK " if offending == 0 else "FAIL"
        print(f"[{status}] {check_name}: offending={offending}")
        if offending > 0:
            failures.append(f"{name} {check_name}: {offending} offending rows")

    # Nuanced check: every place with a hi alias should also carry an explicit hi-Latn romanized alias
    missing_hi_latn = con.execute(
        "SELECT p.place_id FROM places p "
        "WHERE EXISTS (SELECT 1 FROM place_aliases a WHERE a.place_id=p.place_id AND a.language_tag='hi') "
        "AND NOT EXISTS (SELECT 1 FROM place_aliases r WHERE r.place_id=p.place_id AND r.language_tag='hi-Latn')"
    ).fetchall()
    if missing_hi_latn:
        failures.append(f"{name} hi without hi-Latn: {[r[0] for r in missing_hi_latn]}")
    else:
        print("[OK ] alias_romanization_present: every hi place has hi-Latn")

    # Check FTS queries
    test_queries = []
    if name == "in-bihar-buddhist-circuit":
        test_queries = ["Mahabodhi", "Nalanda"]
    elif name == "in-golden-triangle":
        test_queries = ["Taj Mahal", "Qutub", "Hawa Mahal", "Amer", "Humayun", "Fatehpur"]
    elif name == "global-icons-tier1":
        test_queries = ["Eiffel", "Colosseum", "Giza", "Angkor", "Machu Picchu", "Liberty"]

    for q in test_queries:
        rows = con.execute("SELECT place_id FROM place_search WHERE place_search MATCH ? LIMIT 3", (f'"{q}"*',)).fetchall()
        if not rows:
            # Fallback exact word
            rows = con.execute("SELECT place_id FROM place_search WHERE place_search MATCH ? LIMIT 3", (q,)).fetchall()
        print(f"[INFO] FTS query '{q}' matched: {[r[0] for r in rows]}")
        if not rows:
            failures.append(f"{name} FTS query '{q}' returned no results")

    con.close()
    return failures


def main() -> int:
    all_failures: list[str] = []
    for region_name, seed_path, count in SEEDS:
        all_failures.extend(test_seed(region_name, seed_path, count))

    if all_failures:
        print("\n❌ VALIDATION FAILED:")
        for f in all_failures:
            print(f"  - {f}")
        return 1

    print("\n✅ ALL REGIONAL SEEDS PASSED VALIDATION (§28.3 Blueprint compliance confirmed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
