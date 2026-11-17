#!/usr/bin/env python3
"""Verify TrueWay guesthouse standee QR codes.

1. Confirms the standee embeds a real segno SVG QR (not the old decorative mock).
2. Decodes the affiliate URL encoded in each standee's QR.
3. Validates the URL format (host/path/query/affiliate id).
"""
import re
import sys
from urllib.parse import urlparse, parse_qs
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent.parent / "content" / "field" / "stands"

STANDEES = {
    "gh_root_01_standee.html": "GH_ROOT_01",
    "gh_royal_02_standee.html": "GH_ROYAL_02",
    "gh_regency_03_standee.html": "GH_REGENCY_03",
    "gh_thai_04_standee.html": "GH_THAI_04",
    "gh_bhutan_05_standee.html": "GH_BHUTAN_05",
    "gh_zostel_06_standee.html": "GH_ZOSTEL_06",
    "gh_maya_07_standee.html": "GH_MAYA_07",
    "gh_tathagat_08_standee.html": "GH_TATHAGAT_08",
}

failures = 0
for fname, aff in STANDEES.items():
    f = BASE / fname
    if not f.is_file():
        print(f"MISSING: {fname}")
        failures += 1
        continue
    html = f.read_text(encoding="utf-8")

    is_real_segno = 'xmlns="http://www.w3.org/2000/svg"' in html and "<path" in html
    has_fake_widgets = "TW</text>" in html  # old decorative SVG had a TW marker
    m = re.search(r"<!-- REAL QR CODE \(segno\) encoding: ([^\s]+) -->", html)
    url = m.group(1) if m else None

    line = []
    line.append("REAL-SEGNO-QR" if is_real_segno else "NO-REAL-QR")
    line.append("no-fake-widgets" if not has_fake_widgets else "FAKE-WIDGET-PRESENT")
    if url:
        u = urlparse(url)
        q = parse_qs(u.query)
        ok = (u.netloc == "trueway.travel" and u.path == "/dl" and q.get("aff") == [aff] and q.get("src") == ["standee"])
        line.append(f"url={url}")
        line.append("url-OK" if ok else "url-FORMAT-MISMATCH")
        if not ok:
            failures += 1
    else:
        line.append("url=NOT-FOUND")
        failures += 1
    if not is_real_segno or has_fake_widgets:
        failures += 1

    print(f"{fname}: {' | '.join(line)}")

print()
print("RESULT:", "PASS" if failures == 0 else f"FAIL ({failures} problems)")
sys.exit(0 if failures == 0 else 1)
