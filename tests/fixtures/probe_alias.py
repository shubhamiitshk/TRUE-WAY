"""Probe fixture DB for alias/FTS behavior behind the parity failures."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent.parent / "android" / "app" / "src" / "test" / "resources" / "demo_places.sqlite"


def show(obj) -> str:
    return ascii(obj)


def main() -> None:
    con = sqlite3.connect(str(DB))
    for pid in ("in-bihar-nalanda-temple-03", "in-bihar-rajgir-vultures-peak",
                "in-bihar-bodhgaya-mahabodhi", "in-bihar-nalanda-mahavihara"):
        rows = con.execute(
            "SELECT alias_text FROM place_aliases WHERE place_id = ? ORDER BY alias_text",
            (pid,)).fetchall()
        print(pid, "->", show([r[0] for r in rows]))
    print("exact-alias temple:",
          show(con.execute("SELECT a.place_id FROM place_aliases a WHERE lower(a.alias_text) = lower(?)",
                           ("Temple 3",)).fetchall()))
    print("exact-alias join:",
          show(con.execute("SELECT DISTINCT a.place_id AS place_id FROM place_aliases a "
                           "JOIN places p ON p.place_id = a.place_id "
                           "WHERE lower(a.alias_text) = lower(?) "
                           "AND p.editorial_state IN ('REVIEWED','PUBLISHED')",
                           ("Temple 3",)).fetchall()))
    print("fts temple:",
          show(con.execute("SELECT place_id FROM place_search WHERE place_search MATCH ?",
                           ('"Temple"* AND "3"*',)).fetchall()))
    print("bodhi-tree aliases:",
          show(con.execute("SELECT alias_text FROM place_aliases WHERE place_id = ?",
                           ("in-bihar-bodhgaya-bodhi-tree",)).fetchall()))
    print("temple03 claim links:",
          show(con.execute("SELECT cs.claim_id, cs.source_id, s.title FROM claim_sources cs "
                           "LEFT JOIN sources s ON s.source_id = cs.source_id "
                           "WHERE cs.claim_id LIKE 'cl-temple%'").fetchall()))
    print("temple03 get-sim:",
          show(con.execute("SELECT c.claim_id, c.claim_type, c.locale, c.reviewed_at, cs.source_id "
                           "FROM claims c LEFT JOIN claim_sources cs ON cs.claim_id = c.claim_id "
                           "WHERE c.place_id = ?",
                           ("in-bihar-nalanda-temple-03",)).fetchall()))


if __name__ == "__main__":
    main()
