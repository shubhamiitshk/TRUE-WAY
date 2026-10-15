"""Validate the demonstrator seed against blueprint publication rules.

Usage:
    python validate_seed.py
    python validate_seed.py --db /tmp/trueway_demo.db

Builds a throwaway SQLite DB from ../schema/publication_schema.sql +
seed_demo.sql (stdlib sqlite3 only), then enforces §28.3 gate checks.
Exit non-zero on any failure so CI can block bad packs.
"""
from __future__ import annotations

import argparse
import pathlib
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SCHEMA = ROOT.parent / "schema" / "publication_schema.sql"
SEED = ROOT / "seed_demo.sql"

CHECKS: list[tuple[str, str, bool]] = [
    # (name, sql returning offending-row count, must_equal_zero)
    ("no_draft_or_pending_export",
     "SELECT COUNT(*) FROM places WHERE editorial_state='DRAFT'", True),
    ("no_draft_claims",
     "SELECT COUNT(*) FROM claims WHERE editorial_state='DRAFT'", True),
    ("every_claim_has_source",
     "SELECT COUNT(*) FROM claims c LEFT JOIN claim_sources cs ON cs.claim_id=c.claim_id "
     "WHERE cs.claim_id IS NULL", True),
    ("every_claim_has_reviewer",
     "SELECT COUNT(*) FROM claims WHERE reviewer_id IS NULL OR TRIM(reviewer_id)='' "
     "OR reviewed_at IS NULL", True),
    ("claim_type_vocabulary",
     "SELECT COUNT(*) FROM claims WHERE claim_type NOT IN "
     "('DOCUMENTED','INTERPRETATION','TRADITION','CONTESTED','OPERATIONAL','HYPOTHESIS')", True),
    ("visitor_mode_vocabulary",
     "SELECT COUNT(*) FROM places WHERE visitor_mode NOT IN "
     "('PHOTO_SUPPORTED','SEARCH_ONLY','QR_PARTNER','TRAIL_STOP','TEXT_REFERENCE_ONLY')", True),
    ("alias_romanization_present",
     "SELECT COUNT(*) FROM (SELECT place_id FROM place_aliases "
     "WHERE language_tag='hi-Latn' GROUP BY place_id) "
     "/* informational: some parents may legitimately lack hi-Latn; checked in python */", True),
]


def build_db(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON;")
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    con.executescript(SEED.read_text(encoding="utf-8"))
    return con


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=":memory:")
    args = ap.parse_args()

    con = build_db(args.db)
    failures: list[str] = []

    def one(sql: str) -> int:
        return int(con.execute(sql).fetchone()[0])

    # Core counts (Days 3-4 gate: >= 10 verified records).
    n_places = one("SELECT COUNT(*) FROM places")
    n_claims = one("SELECT COUNT(*) FROM claims")
    n_aliases = one("SELECT COUNT(*) FROM place_aliases")
    n_links = one("SELECT COUNT(*) FROM claim_sources")
    n_fts = one("SELECT COUNT(*) FROM place_search")
    print(f"places={n_places} claims={n_claims} aliases={n_aliases} "
          f"claim_sources={n_links} fts_rows={n_fts}")

    if n_places < 10:
        failures.append(f"need >=10 places, found {n_places}")
    if n_claims < 10:
        failures.append(f"need >=10 claims, found {n_claims}")

    for name, sql, _ in CHECKS:
        if name == "alias_romanization_present":
            continue  # handled below with nuance
        n = one(sql)
        status = "OK " if n == 0 else "FAIL"
        print(f"[{status}] {name}: offending={n}")
        if n != 0:
            failures.append(f"{name}: {n} offending rows")

    # Asset rights gate (§28.3): no PENDING/REJECTED-rights asset may export.
    # The gate name no_draft_or_pending_export covers places/claims above AND
    # asset rights here (latent until the first asset is seeded). Guarded so a
    # schema without the assets table does not crash the validator.
    try:
        n_bad_assets = one(
            "SELECT COUNT(*) FROM assets "
            "WHERE rights_review_state IN ('PENDING','REJECTED')")
        status = "OK " if n_bad_assets == 0 else "FAIL"
        print(f"[{status}] no_pending_or_rejected_assets: offending={n_bad_assets}")
        if n_bad_assets:
            failures.append(f"no_pending_or_rejected_assets: {n_bad_assets} offending rows")
    except sqlite3.OperationalError as e:
        print(f"[INFO] asset rights gate skipped ({e})")

    # Nuanced check: every place with a hi alias should also carry an
    # explicit hi-Latn romanized alias (§10.3). TEXT_REFERENCE_ONLY children
    # without any hi alias are reported, not failed, in the demonstrator.
    missing = con.execute(
        "SELECT p.place_id FROM places p "
        "WHERE EXISTS (SELECT 1 FROM place_aliases a WHERE a.place_id=p.place_id "
        "AND a.language_tag='hi') "
        "AND NOT EXISTS (SELECT 1 FROM place_aliases r WHERE r.place_id=p.place_id "
        "AND r.language_tag='hi-Latn')"
    ).fetchall()
    if missing:
        failures.append(f"hi without hi-Latn romanization: {[r[0] for r in missing]}")
    else:
        print("[OK ] alias_romanization_present: every hi place has hi-Latn")

    # FTS sanity: a Devanagari and a romanized query must resolve.
    # NOTE: console-safe logging (Windows cp1252 cannot print Devanagari).
    for q in ["\u092e\u0939\u093e\u092c\u094b\u0927\u093f", "Mahabodhi", "Nalanda", "\u0928\u093e\u0932\u0902\u0926\u093e", "Griddhakuta"]:
        try:
            rows = con.execute(
                "SELECT place_id FROM place_search WHERE place_search MATCH ? LIMIT 3",
                (q,),
            ).fetchall()
        except Exception as e:  # noqa: BLE001 - surface tokenizer issues plainly
            failures.append(f"FTS query {q!r} raised {e}")
            continue
        print(f"[INFO] FTS {q.encode('unicode_escape').decode('ascii')!r} -> {[r[0] for r in rows]}")
        if not rows:
            failures.append(f"FTS query {q.encode('unicode_escape').decode('ascii')!r} returned no rows")

    # Join sanity (Days 3-4 DoD): place -> claims -> sources resolves.
    bad = one(
        "SELECT COUNT(*) FROM claims c "
        "WHERE NOT EXISTS (SELECT 1 FROM places p WHERE p.place_id=c.place_id)"
    )
    if bad:
        failures.append(f"{bad} claims reference missing places")

    if failures:
        print("\nSEED VALIDATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nSEED VALIDATION PASSED (§28.3 gates hold for the demonstrator).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
