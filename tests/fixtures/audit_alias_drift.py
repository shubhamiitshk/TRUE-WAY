"""One-off audit: diff DemoCorpus.kt aliases vs seed_demo.sql aliases per place."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> None:
    seed = (ROOT / "content" / "seed" / "seed_demo.sql").read_text(encoding="utf-8")
    m = re.search(r"INSERT INTO place_aliases.*?VALUES\s*(.*?);", seed, re.S)
    assert m, "alias block not found"
    seed_aliases: dict[str, set[str]] = {}
    # SQLite escapes a single quote by doubling it ('Vulture''s Peak'); the
    # token/capture must allow '' inside a quoted string, then be unescaped.
    qt = r"'(?:[^']|'')*'"
    cap = r"'((?:[^']|'')*)'"
    rows = re.findall(
        rf"\(\s*{qt}\s*,\s*{cap}\s*,\s*{qt}\s*,\s*{cap}\s*,\s*{qt}\s*\)",
        m.group(1),
    )
    for pid, text in rows:
        seed_aliases.setdefault(pid.replace("''", "'"), set()).add(text.replace("''", "'"))

    kt = (ROOT / "android" / "app" / "src" / "main" / "java" / "com" /
            "trueway" / "app" / "data" / "DemoCorpus.kt").read_text(encoding="utf-8")
    blocks = re.findall(r'placeId = "([^"]+)"(.*?)claims = listOf', kt, re.S)
    drift = 0
    for pid, body in blocks:
        am = re.search(r"aliases = listOf\((.*?)\)", body, re.S)
        kalias = set(re.findall(r'"([^"]+)"', am.group(1))) if am else set()
        salias = seed_aliases.get(pid, set())
        if kalias != salias:
            drift += 1
            print(pid)
            print("  only-kt:  ", sorted(kalias - salias))
            print("  only-seed:", sorted(salias - kalias))
    print(f"places={len(blocks)} drifted={drift}")


if __name__ == "__main__":
    sys.exit(main())
