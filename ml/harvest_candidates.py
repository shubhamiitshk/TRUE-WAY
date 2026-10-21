"""Candidate harvester — downloads UNVERIFIED reference photographs into a
quarantine so they can be reviewed before they touch the model.

Why this exists
---------------
The original harvester wrote free-text Commons search results straight into the
training corpus. A visual review of that corpus (see
`ml/dataset/verification_review.json`) found that 41 of 85 source photographs
were unusable: a Shanghai *replica* of the Mahabodhi Temple, three photographs
of a bamboo grove in **Kyoto** labelled as Venu Vana in Rajgir, portraits of a
politician labelled as the Shanti Stupa, a lecture hall in Mumbai labelled as
Nalanda Monastery 1, and a category of "brick ruins" that contained only
rendered brick textures.

The fix is a human-in-the-loop pipeline:

    harvest_candidates.py     download -> ml/dataset/candidates/  (never trained on)
    build_verification_review.py  human verdicts -> verification_review.json
    resplit_dataset.py        promote approved candidates -> corpus, re-split

Nothing in `ml/dataset/candidates/` is ever read by the training pipeline
until a reviewer approves it, so an unreviewed harvest can never poison the
model.

    python ml/harvest_candidates.py --per-class 60
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("hv", ROOT / "ml" / "harvest_training_dataset.py")
hv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hv)

CANDIDATE_DIR = ROOT / "ml" / "dataset" / "candidates"
CANDIDATE_MANIFEST = ROOT / "ml" / "dataset" / "candidates_manifest.json"

# Titles that indicate the asset is not a usable modern field photograph of a
# PLACE. The first corpus was reviewed photograph by photograph and 41 of 85
# source photographs had to be rejected; nearly all of them were caught by
# these patterns. They are filtered BEFORE download so an unreviewed harvest
# cannot flood the candidate pool with unusable material.
REJECT_PATTERNS = re.compile(
    r"(replica|miniature|scale model|model of|museum model|"
    r"statue of|statuette|statue|bust of|figure of|"
    r"coin|token|seal|stamp|banknote|note of|"
    r"manuscript|scroll|palm leaf|inscription|epigraph|"
    r"painting|drawing|sketch|engraving|lithograph|etching|fresco|mural|"
    r"illustration|graphic|diagram|plan of|map of|cross section|elevation|"
    r"logo|coat of arms|flag of|banner|icon|svg|blazon|"
    r"relief|panel of|carving|ornament|"
    r"postcard|photograph of a photograph|"
    r"185\d|186\d|187\d|188\d|189\d|190\d|191\d|192\d|193\d|194\d|195\d|196\d|197\d|198\d|199\d|"
    r"archive|archival|historical photo|old photograph|early photograph|"
    r"advertisement|brochure|catalogue|calendar|"
    r"signboard|sign board|plaque|notice board|information board|board at)",
    re.I,
)


def is_rejected_title(title: str, exempt: Optional[List[str]] = None) -> bool:
    """Is this title unusable as a field photograph of a PLACE?

    `exempt` lists fragments that are PART OF THE SUBJECT for a particular
    negative category, and are therefore removed from the title before the
    filter is applied. The "colossal seated Buddha statue" negatives are
    literally statues, and the "rock-cut cave complex" negatives are literally
    carved reliefs: without the exemption the title filter would have
    discarded every one of them, and with them the hardest negatives in the
    corpus. The exemption is a REMOVAL, not a bypass - "miniature Buddha
    statue" still fails on "miniature".
    """
    t = title or ""
    for frag in (exempt or []):
        t = re.sub(frag, " ", t, flags=re.I)
    return bool(REJECT_PATTERNS.search(t))


def stable_name(prefix: str, title: str) -> str:
    """A filename that depends ONLY on the source photograph.

    The previous naming used the discovery INDEX, which shifts as the candidate
    set grows - so a re-download wrote the file somewhere else and the manifest
    kept pointing at a path that no longer existed (599 of 1768 candidates were
    left pointing at nothing). Keying the filename on the title hash makes every
    re-download land on the same path.
    """
    safe = hashlib.sha256(title.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{safe}.jpg"


def download(item: Dict[str, str], dest_dir: Path, prefix: str, idx: int) -> Optional[Dict[str, str]]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe = hashlib.sha256(item["title"].encode("utf-8")).hexdigest()[:12]
    out_path = dest_dir / stable_name(prefix, item["title"])
    if out_path.is_file() and out_path.stat().st_size > 1024:
        raw = out_path.read_bytes()
    else:
        raw = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(item["url"], headers={"User-Agent": hv.USER_AGENT})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    raw = resp.read()
                img = Image.open(io.BytesIO(raw)).convert("RGB")
                img.thumbnail((640, 640), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=92)
                raw = buf.getvalue()
                out_path.write_bytes(raw)
                break
            except Exception:
                time.sleep(0.5 * (attempt + 1))
        if raw is None:
            return None
    rec = dict(item)
    rec["local_path"] = str(out_path.relative_to(ROOT)).replace("\\", "/")
    rec["sha256"] = hashlib.sha256(raw).hexdigest()
    rec["source_photo_id"] = "commons:" + hashlib.sha256(item["title"].encode("utf-8")).hexdigest()[:16]
    rec["status"] = "pending"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description="Harvest UNVERIFIED reference candidates into quarantine")
    ap.add_argument("--per-class", type=int, default=60)
    ap.add_argument("--only", nargs="*", default=None,
                    help="Restrict to these place_id / neg_category keys")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = CANDIDATE_MANIFEST
    manifest: Dict[str, object] = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.setdefault("harvested_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    manifest.setdefault("classes", {})

    seen_titles: set = set()
    for c in manifest["classes"].values():
        for r in c.get("records", []):
            # Only skip a title if its file is STILL on disk. If the quarantine
            # was pruned, the photograph must be fetched again rather than
            # silently lost.
            if (ROOT / r.get("local_path", "")).is_file():
                seen_titles.add(r.get("title", ""))

    targets: List[tuple] = []
    for spec in hv.POI_SPECS:
        pid = str(spec["place_id"])
        if args.only and pid not in args.only:
            continue
        targets.append(("place", pid, list(spec["categories"]), list(spec["queries"]), []))
    for spec in hv.NEGATIVE_SPECS:
        ncat = str(spec["neg_category"])
        if args.only and ncat not in args.only:
            continue
        targets.append(("neg", ncat, list(spec["categories"]), list(spec["queries"]),
                        list(spec.get("title_exempt") or [])))

    deadline = time.time() + args.timeout
    for kind, cid, cats, queries, exempt in targets:
        if time.time() > deadline:
            print("  (time budget exhausted)")
            break
        cands = hv.discover_candidates(cats, queries, target_count=args.per_class,
                                       global_seen=seen_titles)
        # drop obvious non-photographs and archival material before downloading
        filtered = [c for c in cands if not is_rejected_title(c.get("title", ""), exempt)]
        skipped = len(cands) - len(filtered)
        for c in filtered:
            seen_titles.add(c.get("title", ""))
        dest = CANDIDATE_DIR / kind / cid
        got: List[Dict[str, str]] = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = [ex.submit(download, c, dest, cid.split("-")[-1], i)
                    for i, c in enumerate(filtered)]
            for f in as_completed(futs):
                try:
                    r = f.result()
                except Exception:
                    r = None
                if r:
                    got.append(r)
        got.sort(key=lambda x: x["local_path"])
        manifest["classes"].setdefault(cid, {"kind": kind, "records": []})
        existing = {r["source_photo_id"] for r in manifest["classes"][cid]["records"]}
        for r in got:
            if r["source_photo_id"] not in existing:
                manifest["classes"][cid]["records"].append(r)
                existing.add(r["source_photo_id"])
        print(f"  [{kind:5s}] {cid:42s} candidates={len(filtered):3d} "
              f"(skipped {skipped} non-photo/archival)  total={len(existing)}")
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    total = sum(len(c["records"]) for c in manifest["classes"].values())
    manifest["total_candidates"] = total
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n-> {manifest_path}  ({total} candidates awaiting review)")
    print("   Candidates are QUARANTINED: the training pipeline never reads them")
    print("   until a reviewer approves them in ml/dataset/verification_review.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
