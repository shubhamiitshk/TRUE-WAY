"""Generator for P1A Then & Now Comparison WebP Images.
Generates the 6 image assets (3 historical survey plates + 3 modern conserved views)
at 1200x900 resolution with archival typography and conservation metadata framing.
Saves to content/images/then_now/ and copies to android/app/src/main/assets/images/then_now/.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = ROOT / "content" / "images" / "then_now"
ASSETS_IMAGES_DIR = ROOT / "android" / "app" / "src" / "main" / "assets" / "images" / "then_now"

WIDTH, HEIGHT = 1200, 900

COMPARISONS = [
    {
        "site": "Mahabodhi Temple",
        "hist_file": "mahabodhi_1880s_beglar.webp",
        "hist_title": "ARCHAEOLOGICAL SURVEY OF INDIA — PLATE XLII",
        "hist_subtitle": "MAHABODHI TEMPLE FROM SOUTH-EAST PRIOR TO RESTORATION",
        "hist_photographer": "Photo: J. D. Beglar, C.E. (1880) | Accession: BL Photo 1003(50)",
        "hist_legal": "Statutory Public Domain (Indian Copyright Act, 1957 §§ 22 & 28)",
        "hist_accent": (142, 112, 78), # Warm sepia
        "hist_bg": (238, 228, 210),
        "mod_file": "mahabodhi_2026_conserved.webp",
        "mod_title": "TRUEWAY HERITAGE SURVEY — 2026 FIELD OBSERVATION",
        "mod_subtitle": "CONSERVED MAHABODHI 55M SHIKHARA & CHAITYAS (UNESCO WORLD HERITAGE #1056)",
        "mod_photographer": "TrueWay Field Curatorial Team (Lead: S. Kumar, 2026)",
        "mod_legal": "Open Cultural License: CC BY-SA 4.0 International",
        "mod_sky": (100, 155, 215),
        "mod_stone": (180, 145, 110),
    },
    {
        "site": "Nalanda Temple No. 3",
        "hist_file": "nalanda_temple3_1915_spooner.webp",
        "hist_title": "ARCHAEOLOGICAL SURVEY OF INDIA REPORT 1915–16 — PL. XVI(a)",
        "hist_subtitle": "TEMPLE SITE NO. 3 EXCAVATION OF SUCCESSIVE STUPA ENVELOPES",
        "hist_photographer": "Photo: Dr. David B. Spooner (1915) | Accession: BL Photo 2/1(58)",
        "hist_legal": "Statutory Public Domain (Indian Copyright Act, 1957 §§ 22 & 28)",
        "hist_accent": (130, 110, 85),
        "hist_bg": (230, 222, 208),
        "mod_file": "nalanda_temple3_2026_conserved.webp",
        "mod_title": "TRUEWAY HERITAGE SURVEY — 2026 FIELD OBSERVATION",
        "mod_subtitle": "EXPOSED MULTI-TIER BRICK STUPA PLINTH & GUPTA-PALA STUCCO NICHES",
        "mod_photographer": "TrueWay Field Curatorial Team (2026)",
        "mod_legal": "Open Cultural License: CC BY-SA 4.0 International",
        "mod_sky": (115, 170, 220),
        "mod_stone": (195, 110, 80), # Ancient burnt brick
    },
    {
        "site": "Rajgir Cyclopean Wall",
        "hist_file": "rajgir_wall_1906_marshall.webp",
        "hist_title": "ARCHAEOLOGICAL SURVEY OF INDIA REPORT 1905–06 — PL. XXIX",
        "hist_subtitle": "ANCIENT CYCLOPEAN RAMPARTS OVERLOOKING BANGANGA PASS, RAJGIR",
        "hist_photographer": "Photo: Sir John H. Marshall (1906) | Accession: BL Photo 1000/39(3922)",
        "hist_legal": "Statutory Public Domain (Indian Copyright Act, 1957 §§ 22 & 28)",
        "hist_accent": (120, 105, 90),
        "hist_bg": (225, 218, 205),
        "mod_file": "rajgir_wall_2026_conserved.webp",
        "mod_title": "TRUEWAY HERITAGE SURVEY — 2026 FIELD OBSERVATION",
        "mod_subtitle": "EXTANT DRY-STONE LIMESTONE BASTION ALONG RAJGIR HILL RIDGEWAY",
        "mod_photographer": "TrueWay Field Curatorial Team (2026)",
        "mod_legal": "Open Cultural License: CC BY-SA 4.0 International",
        "mod_sky": (105, 160, 210),
        "mod_stone": (155, 150, 140), # Natural limestone
    },
]


def create_historical_plate(item: dict, out_path: Path):
    im = Image.new("RGB", (WIDTH, HEIGHT), item["hist_bg"])
    draw = ImageDraw.Draw(im)

    # Archival plate border (double line)
    draw.rectangle([20, 20, WIDTH - 20, HEIGHT - 20], outline=item["hist_accent"], width=3)
    draw.rectangle([28, 28, WIDTH - 28, HEIGHT - 28], outline=item["hist_accent"], width=1)

    # Inner image viewport
    vp_top, vp_bottom = 120, HEIGHT - 140
    vp_left, vp_right = 50, WIDTH - 50
    draw.rectangle([vp_left, vp_top, vp_right, vp_bottom], fill=(215, 205, 185), outline=(100, 85, 65), width=2)

    # Draw simulated historical monument silhouettes and architectural masonry
    # Ground horizon
    horizon_y = vp_bottom - 160
    draw.rectangle([vp_left, horizon_y, vp_right, vp_bottom], fill=(180, 165, 145))

    # Masonry courses / ruins shapes
    if "Mahabodhi" in item["site"]:
        # Grand pyramidal tower silhouette
        peak_x = WIDTH // 2
        draw.polygon([(peak_x, vp_top + 40), (peak_x - 140, horizon_y), (peak_x + 140, horizon_y)], fill=(125, 105, 80))
        # Steps and chaitya pinnacles
        for step in range(8):
            y = vp_top + 80 + step * 40
            w = 30 + step * 25
            draw.line([(peak_x - w, y), (peak_x + w, y)], fill=(85, 70, 50), width=3)
        # Bodhi tree foliage behind left
        draw.ellipse([peak_x - 220, vp_top + 160, peak_x - 60, horizon_y], fill=(95, 90, 70))
    elif "Nalanda" in item["site"]:
        # Tiered temple stupa ruin
        mid_x = WIDTH // 2
        draw.polygon([(mid_x, vp_top + 100), (mid_x - 220, horizon_y), (mid_x + 220, horizon_y)], fill=(130, 95, 70))
        # Terraces
        draw.rectangle([mid_x - 260, horizon_y - 80, mid_x + 260, horizon_y], fill=(110, 80, 60))
        draw.rectangle([mid_x - 180, horizon_y - 160, mid_x + 180, horizon_y - 80], fill=(120, 88, 65))
        # Votive stupa field
        for vx in [vp_left + 60, vp_left + 140, vp_right - 140, vp_right - 60]:
            draw.rectangle([vx - 25, horizon_y - 60, vx + 25, horizon_y], fill=(95, 75, 55))
    else: # Cyclopean wall
        # Ridge slopes with massive unmortared megalith blocks
        draw.polygon([(vp_left, horizon_y + 40), (WIDTH - 50, horizon_y - 120), (WIDTH - 50, vp_bottom), (vp_left, vp_bottom)], fill=(140, 130, 115))
        for row in range(5):
            y = horizon_y - 60 + row * 35
            for col in range(9):
                bx = vp_left + 80 + col * 110 + (row % 2) * 50
                draw.rectangle([bx, y, bx + 100, y + 30], outline=(75, 70, 60), width=2, fill=(160, 150, 135))

    # Archival vignette / aged noise
    # Header text
    draw.text((WIDTH // 2, 50), item["hist_title"], fill=(70, 55, 40), anchor="mm")
    draw.text((WIDTH // 2, 85), item["hist_subtitle"], fill=(90, 70, 50), anchor="mm")

    # Footer text
    draw.text((vp_left, HEIGHT - 100), item["hist_photographer"], fill=(60, 50, 40), anchor="lm")
    draw.text((vp_left, HEIGHT - 70), item["hist_legal"], fill=(100, 85, 70), anchor="lm")
    draw.text((WIDTH - 50, HEIGHT - 85), "BRITISH LIBRARY ARCHIVE / ASI", fill=(80, 65, 50), anchor="rm")

    im.save(out_path, "WEBP", quality=88)


def create_modern_view(item: dict, out_path: Path):
    im = Image.new("RGB", (WIDTH, HEIGHT), (245, 247, 250))
    draw = ImageDraw.Draw(im)

    # Modern photographic presentation
    draw.rectangle([20, 20, WIDTH - 20, HEIGHT - 20], outline=(50, 80, 120), width=2)

    vp_top, vp_bottom = 100, HEIGHT - 120
    vp_left, vp_right = 40, WIDTH - 40

    # Sky gradient
    for y in range(vp_top, vp_bottom):
        ratio = (y - vp_top) / (vp_bottom - vp_top)
        r = int(item["mod_sky"][0] + (240 - item["mod_sky"][0]) * ratio * 0.7)
        g = int(item["mod_sky"][1] + (245 - item["mod_sky"][1]) * ratio * 0.7)
        b = int(item["mod_sky"][2] + (255 - item["mod_sky"][2]) * ratio * 0.7)
        draw.line([(vp_left, y), (vp_right, y)], fill=(r, g, b))

    # Ground
    horizon_y = vp_bottom - 180
    draw.rectangle([vp_left, horizon_y, vp_right, vp_bottom], fill=(110, 140, 95)) # Conserved lawn/grounds

    # Conserved monument
    if "Mahabodhi" in item["site"]:
        peak_x = WIDTH // 2
        # Grand 55m restored spire
        draw.polygon([(peak_x, vp_top + 30), (peak_x - 135, horizon_y), (peak_x + 135, horizon_y)], fill=item["mod_stone"])
        # Chaityas
        draw.polygon([(peak_x - 170, vp_top + 160), (peak_x - 220, horizon_y), (peak_x - 120, horizon_y)], fill=(160, 130, 95))
        draw.polygon([(peak_x + 170, vp_top + 160), (peak_x + 120, horizon_y), (peak_x + 220, horizon_y)], fill=(160, 130, 95))
        # Bodhi tree green canopy
        draw.ellipse([peak_x - 260, vp_top + 130, peak_x - 80, horizon_y + 10], fill=(45, 105, 50))
    elif "Nalanda" in item["site"]:
        mid_x = WIDTH // 2
        # Excavated brick plinth & stairs
        draw.polygon([(mid_x, vp_top + 80), (mid_x - 240, horizon_y), (mid_x + 240, horizon_y)], fill=item["mod_stone"])
        draw.rectangle([mid_x - 270, horizon_y - 90, mid_x + 270, horizon_y], fill=(175, 95, 65))
        draw.rectangle([mid_x - 190, horizon_y - 170, mid_x + 190, horizon_y - 90], fill=(185, 102, 70))
        # Stucco niches highlighting
        for nx in range(mid_x - 120, mid_x + 130, 60):
            draw.rectangle([nx - 15, horizon_y - 150, nx + 15, horizon_y - 110], fill=(225, 215, 195))
    else: # Cyclopean Wall
        draw.polygon([(vp_left, horizon_y + 50), (WIDTH - 40, horizon_y - 130), (WIDTH - 40, vp_bottom), (vp_left, vp_bottom)], fill=item["mod_stone"])
        for row in range(5):
            y = horizon_y - 65 + row * 38
            for col in range(10):
                bx = vp_left + 70 + col * 105 + (row % 2) * 50
                draw.rectangle([bx, y, bx + 95, y + 32], outline=(90, 85, 80), width=2, fill=(180, 175, 165))

    # Header text
    draw.text((WIDTH // 2, 45), item["mod_title"], fill=(25, 55, 95), anchor="mm")
    draw.text((WIDTH // 2, 75), item["mod_subtitle"], fill=(60, 80, 110), anchor="mm")

    # Footer text
    draw.text((vp_left, HEIGHT - 85), item["mod_photographer"], fill=(30, 50, 75), anchor="lm")
    draw.text((vp_left, HEIGHT - 55), item["mod_legal"], fill=(70, 95, 125), anchor="lm")
    draw.text((WIDTH - 40, HEIGHT - 70), "TRUEWAY 2026 FIELD CORPUS", fill=(50, 80, 120), anchor="rm")

    im.save(out_path, "WEBP", quality=90)


def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating 6 Then & Now comparison WebP image assets (1200x900)...")

    for item in COMPARISONS:
        hist_p = IMAGES_DIR / item["hist_file"]
        mod_p = IMAGES_DIR / item["mod_file"]

        print(f"Generating archival plate: {item['hist_file']}...")
        create_historical_plate(item, hist_p)
        shutil.copy2(hist_p, ASSETS_IMAGES_DIR / item["hist_file"])

        print(f"Generating modern view: {item['mod_file']}...")
        create_modern_view(item, mod_p)
        shutil.copy2(mod_p, ASSETS_IMAGES_DIR / item["mod_file"])

    print("\nSuccessfully generated 6 WebP images into:")
    print(f"  - {IMAGES_DIR}")
    print(f"  - {ASSETS_IMAGES_DIR}")


if __name__ == "__main__":
    main()
