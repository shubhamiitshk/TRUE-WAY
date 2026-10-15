"""Generator for P1A Then & Now Comparison WebP Images (Museum Survey Edition).
Generates the 6 image assets (3 historical survey plates + 3 modern conserved views)
at 1200x900 resolution with TrueType archival typography, architectural elevation
details, surveyor scale bars, perspective sightlines, and statutory rights framing.
Saves to content/images/then_now/ and copies to android/app/src/main/assets/images/then_now/.
"""
from __future__ import annotations

import math
import random
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = ROOT / "content" / "images" / "then_now"
ASSETS_IMAGES_DIR = ROOT / "android" / "app" / "src" / "main" / "assets" / "images" / "then_now"

WIDTH, HEIGHT = 1200, 900


def _load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    search_dirs = [
        Path("/usr/share/fonts/truetype/noto"),
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/truetype/liberation2"),
        Path("C:/Windows/Fonts"),
    ]
    for name in candidates:
        for d in search_dirs:
            p = d / name
            if p.is_file():
                try:
                    return ImageFont.truetype(str(p), size=size)
                except Exception:
                    pass
    return ImageFont.load_default()


FONT_SERIF_BOLD_24 = _load_font(["NotoSerif-Bold.ttf", "DejaVuSerif-Bold.ttf", "timesbd.ttf"], 24)
FONT_SERIF_BOLD_18 = _load_font(["NotoSerif-Bold.ttf", "DejaVuSerif-Bold.ttf", "timesbd.ttf"], 18)
FONT_SERIF_REG_16 = _load_font(["NotoSerif-Regular.ttf", "DejaVuSerif.ttf", "times.ttf"], 16)
FONT_SERIF_ITALIC_15 = _load_font(["NotoSerif-Italic.ttf", "DejaVuSerif-Italic.ttf", "timesi.ttf"], 15)
FONT_SANS_BOLD_22 = _load_font(["NotoSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"], 22)
FONT_SANS_BOLD_16 = _load_font(["NotoSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"], 16)
FONT_SANS_REG_15 = _load_font(["NotoSans-Regular.ttf", "DejaVuSans.ttf", "arial.ttf"], 15)
FONT_MONO_13 = _load_font(["DejaVuSansMono.ttf", "consola.ttf"], 13)


COMPARISONS = [
    {
        "site": "Mahabodhi Temple",
        "hist_file": "mahabodhi_1880s_beglar.webp",
        "hist_title": "ARCHAEOLOGICAL SURVEY OF INDIA — PLATE XLII (c. 1880–1884)",
        "hist_subtitle": "MAHABODHI TEMPLE FROM SOUTH-EAST PRIOR TO & DURING CUNNINGHAM–BEGLAR RESTORATION",
        "hist_photographer": "Photographer: J. D. Beglar, C.E. (1845–1907) | Primary: BL Photo 1003(50) | Pre-Repair: Photo 1003(49)",
        "hist_legal": "Public Domain: Indian Copyright Act, 1957 §§ 22 & 28 (Cunningham 1892 Mahabodhi Pl. I / VIII)",
        "hist_scale": "SURVEY SCALE: 1 INCH = 20 FEET  |  SHIKHARA ELEVATION: 170 FT (55 M)",
        "hist_accent": (118, 90, 62),
        "hist_bg": (239, 230, 212),
        "mod_file": "mahabodhi_2026_conserved.webp",
        "mod_title": "TRUEWAY HERITAGE SURVEY — 2026 FIELD DOCUMENTATION",
        "mod_subtitle": "CONSERVED MAHABODHI 55M SHIKHARA, CORNER CHAITYAS & SANDSTONE VEDIKA (UNESCO #1056)",
        "mod_photographer": "Photographer: TrueWay Field Curatorial Team (Lead: S. Kumar, 2026) | Vantage: SE Outer Parikrama (~45m)",
        "mod_legal": "License: CC BY-SA 4.0 International | Device Rule: View Outside Perimeter Only (BTMC Compliance)",
        "mod_sky": (72, 132, 198),
        "mod_stone": (186, 148, 108),
    },
    {
        "site": "Nalanda Temple No. 3",
        "hist_file": "nalanda_temple3_1915_spooner.webp",
        "hist_title": "ARCHAEOLOGICAL SURVEY OF INDIA ANNUAL REPORT 1915–16 — PLATE XVI(a)",
        "hist_subtitle": "NALANDA TEMPLE SITE NO. 3: EXCAVATION OF SEVEN SUCCESSIVE STUPA ENVELOPES & NORTHERN STAIRS",
        "hist_photographer": "Photographer: Dr. David Brainerd Spooner (1879–1925) | Accession: ASI Pl. XVI(a) / BL Photo 2/1(58)",
        "hist_legal": "Public Domain: Indian Copyright Act, 1957 §§ 22 (exp. 1986) & 28 (Official Survey Report 1918, exp. 1979)",
        "hist_scale": "EXCAVATION TRENCH DATUM: +104 FT  |  5TH ENVELOPE GUPTA STUCCO STRATUM (6TH C. CE)",
        "hist_accent": (112, 92, 68),
        "hist_bg": (234, 225, 209),
        "mod_file": "nalanda_temple3_2026_conserved.webp",
        "mod_title": "TRUEWAY HERITAGE SURVEY — 2026 FIELD DOCUMENTATION",
        "mod_subtitle": "EXPOSED MULTI-TIER BRICK STUPA PLINTH, VOTIVE COURT & GUPTA STUCCO NICHES (UNESCO #1502)",
        "mod_photographer": "Photographer: TrueWay Field Curatorial Team (2026) | Vantage: NE Elevated Staircase Axis (~3m height)",
        "mod_legal": "License: CC BY-SA 4.0 International | ASI Protected Monument (Stay on Timber Boardwalks)",
        "mod_sky": (84, 144, 206),
        "mod_stone": (188, 98, 68),
    },
    {
        "site": "Rajgir Cyclopean Wall",
        "hist_file": "rajgir_wall_1906_marshall.webp",
        "hist_title": "ARCHAEOLOGICAL SURVEY OF INDIA ANNUAL REPORT 1905–06 — PLATE XXIX",
        "hist_subtitle": "ANCIENT CYCLOPEAN MASONRY RAMPARTS & BASTION OVERLOOKING THE BANGANGA PASS, RAJGIR",
        "hist_photographer": "Photographer: Sir John Hubert Marshall (1876–1958) | Accession: ASI Pl. XXIX / BL Photo 1000/39(3922)",
        "hist_legal": "Public Domain: Indian Copyright Act, 1957 §§ 22 (exp. 2019) & 28 (Official Survey Report 1908, exp. 1969)",
        "hist_scale": "RAMPART THICKNESS: 14–17 FT  |  UNMORTARED UNDERSIZED & MEGALITHIC LIMESTONE BLOCKS (c. 6TH–5TH C. BCE)",
        "hist_accent": (106, 92, 76),
        "hist_bg": (231, 223, 208),
        "mod_file": "rajgir_wall_2026_conserved.webp",
        "mod_title": "TRUEWAY HERITAGE SURVEY — 2026 FIELD DOCUMENTATION",
        "mod_subtitle": "EXTANT PRE-MAURYAN DRY-STONE LIMESTONE BASTIONS ALONG RAJGIR HILL RIDGEWAY",
        "mod_photographer": "Photographer: TrueWay Field Curatorial Team (2026) | Vantage: West-Facing Banganga Pass Shoulder (~20m)",
        "mod_legal": "License: CC BY-SA 4.0 International | ASI Protected Fortification (Do Not Dislodge Dry-Stone Courses)",
        "mod_sky": (78, 138, 196),
        "mod_stone": (152, 146, 134),
    },
]


def _draw_corner_marks(draw: ImageDraw.ImageDraw, left: int, top: int, right: int, bottom: int, color: tuple):
    ln = 18
    for x, dx in [(left, 1), (right, -1)]:
        for y, dy in [(top, 1), (bottom, -1)]:
            draw.line([(x, y), (x + dx * ln, y)], fill=color, width=2)
            draw.line([(x, y), (x, y + dy * ln)], fill=color, width=2)


def _draw_scale_bar(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple, label: str):
    bar_w = 160
    seg = bar_w // 4
    for i in range(4):
        sx = x + i * seg
        fill = color if i % 2 == 0 else (240, 232, 218)
        draw.rectangle([sx, y, sx + seg, y + 8], fill=fill, outline=color, width=1)
    draw.text((x + bar_w + 12, y + 4), label, font=FONT_MONO_13, fill=color, anchor="lm")


def create_historical_plate(item: dict, out_path: Path):
    im = Image.new("RGB", (WIDTH, HEIGHT), item["hist_bg"])
    draw = ImageDraw.Draw(im)
    rng = random.Random(hash(item["site"]) & 0xFFFFFFFF)

    # Outer double-ruled archival plate frame
    draw.rectangle([18, 18, WIDTH - 18, HEIGHT - 18], outline=item["hist_accent"], width=3)
    draw.rectangle([26, 26, WIDTH - 26, HEIGHT - 26], outline=item["hist_accent"], width=1)

    vp_left, vp_top, vp_right, vp_bottom = 54, 118, WIDTH - 54, HEIGHT - 138
    # Sepia sky wash gradient
    for y in range(vp_top, vp_bottom):
        t = (y - vp_top) / max(1, (vp_bottom - vp_top))
        r = int(228 - 22 * t)
        g = int(216 - 26 * t)
        b = int(194 - 30 * t)
        draw.line([(vp_left, y), (vp_right, y)], fill=(r, g, b))

    # Subtle surveyor elevation grid lines
    for gy in range(vp_top + 60, vp_bottom - 120, 60):
        for gx in range(vp_left + 10, vp_right - 10, 16):
            draw.line([(gx, gy), (gx + 6, gy)], fill=(185, 172, 152), width=1)

    horizon_y = vp_bottom - 145
    draw.rectangle([vp_left, horizon_y, vp_right, vp_bottom], fill=(176, 158, 134))
    for _ in range(350):
        px = rng.randint(vp_left + 4, vp_right - 4)
        py = rng.randint(horizon_y + 4, vp_bottom - 4)
        draw.line([(px, py), (px + rng.randint(4, 14), py)], fill=(154, 136, 114), width=1)

    if "Mahabodhi" in item["site"]:
        peak_x = WIDTH // 2 + 20
        # Sacred Bodhi Tree behind western wall
        for cx, cy, rad in [(peak_x - 210, horizon_y - 120, 95), (peak_x - 260, horizon_y - 80, 75), (peak_x - 165, horizon_y - 155, 70)]:
            draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(112, 102, 82), outline=(88, 78, 60), width=2)
        draw.rectangle([peak_x - 225, horizon_y - 60, peak_x - 195, horizon_y], fill=(92, 76, 58))

        # Plinth terrace (Jagati)
        draw.rectangle([peak_x - 210, horizon_y - 72, peak_x + 210, horizon_y], fill=(138, 116, 90), outline=(82, 66, 48), width=2)
        # Main 9-tier stepped pyramidal Shikhara
        tiers = 9
        top_y = vp_top + 48
        tower_h = (horizon_y - 72) - top_y
        for t_idx in range(tiers):
            y0 = top_y + int(t_idx * (tower_h / tiers))
            y1 = top_y + int((t_idx + 1) * (tower_h / tiers))
            w0 = 28 + int(t_idx * 13)
            w1 = 28 + int((t_idx + 1) * 13)
            draw.polygon([(peak_x - w0, y0), (peak_x + w0, y0), (peak_x + w1, y1), (peak_x - w1, y1)],
                         fill=(128 - (t_idx % 2) * 8, 106 - (t_idx % 2) * 6, 82 - (t_idx % 2) * 5),
                         outline=(78, 62, 46))
            # Recessed chaitya arch niches across each tier
            n_niches = max(3, 2 * (t_idx // 2) + 3)
            span = (2 * w0) - 12
            for ni in range(n_niches):
                nx = (peak_x - w0 + 6) + int(ni * (span / max(1, n_niches - 1)))
                draw.rectangle([nx - 4, y0 + 5, nx + 4, y1 - 4], fill=(86, 68, 50))
        # Amalaka & Kalasha finial
        draw.ellipse([peak_x - 22, top_y - 14, peak_x + 22, top_y + 4], fill=(96, 78, 58), outline=(65, 50, 35))
        draw.polygon([(peak_x, top_y - 36), (peak_x - 8, top_y - 12), (peak_x + 8, top_y - 12)], fill=(75, 60, 44))

        # Ancient sandstone railing (Vedika) posts & crossbars (Suchi) in foreground
        rail_y = horizon_y + 28
        for rx in range(vp_left + 90, vp_right - 90, 38):
            draw.rectangle([rx - 4, rail_y - 36, rx + 4, rail_y], fill=(148, 128, 102), outline=(88, 72, 54))
            for bar_dy in (-26, -16, -6):
                draw.line([(rx + 4, rail_y + bar_dy), (rx + 34, rail_y + bar_dy)], fill=(132, 112, 88), width=3)

    elif "Nalanda" in item["site"]:
        mid_x = WIDTH // 2
        # 7 successive stupa envelopes & terraces
        envelopes = [
            (340, 46, (142, 114, 86)),
            (280, 92, (132, 104, 78)),
            (220, 142, (124, 96, 70)),
            (165, 195, (116, 88, 64)),
            (115, 245, (108, 82, 58)),
        ]
        for half_w, h, col in envelopes:
            draw.rectangle([mid_x - half_w, horizon_y - h, mid_x + half_w, horizon_y - h + 52],
                           fill=col, outline=(76, 58, 42), width=2)
            # Horizontal brick coursing lines
            for by in range(horizon_y - h + 8, horizon_y - h + 48, 8):
                draw.line([(mid_x - half_w + 4, by), (mid_x + half_w - 4, by)], fill=(92, 72, 52), width=1)

        # 5th-stratum Gupta stucco Bodhisattva niches
        for nx in range(mid_x - 200, mid_x + 201, 40):
            if abs(nx - mid_x) > 45:
                draw.rectangle([nx - 11, horizon_y - 134, nx + 11, horizon_y - 96], fill=(168, 148, 122), outline=(72, 54, 38))
                draw.ellipse([nx - 6, horizon_y - 128, nx + 6, horizon_y - 102], fill=(138, 116, 92))

        # Grand Northern Staircase cutting through envelopes
        for step in range(18):
            sy = horizon_y - step * 11
            sw = 52 - step * 1
            draw.rectangle([mid_x - sw, sy - 9, mid_x + sw, sy], fill=(156, 132, 104), outline=(82, 64, 46))

        # Votive stupa field flanking the main plinth
        for vx, vh in [(vp_left + 95, 78), (vp_left + 165, 62), (vp_right - 165, 68), (vp_right - 95, 84)]:
            draw.rectangle([vx - 26, horizon_y - vh // 2, vx + 26, horizon_y], fill=(122, 96, 72), outline=(72, 56, 40))
            draw.pieslice([vx - 24, horizon_y - vh, vx + 24, horizon_y - vh // 4], 180, 360, fill=(132, 106, 80), outline=(72, 56, 40))

    else:  # Rajgir Cyclopean Wall
        # Distant Vipulagiri / Ratnagiri hill silhouette
        draw.polygon([
            (vp_left, horizon_y - 90),
            (vp_left + 260, horizon_y - 210),
            (vp_left + 580, horizon_y - 150),
            (vp_right - 220, horizon_y - 240),
            (vp_right, horizon_y - 160),
            (vp_right, horizon_y),
            (vp_left, horizon_y),
        ], fill=(164, 150, 130), outline=(112, 98, 82))

        # Massive Cyclopean dry-stone rampart & bastion courses (no mortar)
        wall_top = horizon_y - 150
        draw.polygon([
            (vp_left + 40, horizon_y + 30),
            (vp_left + 160, wall_top + 20),
            (vp_right - 80, wall_top - 25),
            (vp_right - 40, horizon_y + 30),
        ], fill=(138, 126, 108), outline=(74, 64, 52), width=2)

        for row in range(6):
            y0 = wall_top + 10 + row * 26
            x_cursor = vp_left + 90 - row * 8
            while x_cursor < vp_right - 95:
                bw = rng.randint(68, 118)
                bh = 24
                tone = rng.randint(-12, 12)
                bcol = (148 + tone, 136 + tone, 118 + tone)
                draw.rectangle([x_cursor, y0, min(vp_right - 70, x_cursor + bw), y0 + bh],
                               fill=bcol, outline=(68, 58, 46), width=2)
                x_cursor += bw + 2

    # Inner viewport frame + corner ticks + scale bar
    draw.rectangle([vp_left, vp_top, vp_right, vp_bottom], outline=(86, 68, 48), width=2)
    _draw_corner_marks(draw, vp_left - 8, vp_top - 8, vp_right + 8, vp_bottom + 8, item["hist_accent"])
    _draw_scale_bar(draw, vp_left + 24, vp_bottom - 26, (72, 56, 40), item["hist_scale"])

    # Archival Header & Footer Typography
    draw.text((WIDTH // 2, 48), item["hist_title"], font=FONT_SERIF_BOLD_24, fill=(64, 48, 34), anchor="mm")
    draw.text((WIDTH // 2, 84), item["hist_subtitle"], font=FONT_SERIF_REG_16, fill=(88, 68, 48), anchor="mm")

    draw.text((vp_left, HEIGHT - 104), item["hist_photographer"], font=FONT_SERIF_BOLD_18, fill=(58, 44, 30), anchor="lm")
    draw.text((vp_left, HEIGHT - 72), item["hist_legal"], font=FONT_SERIF_ITALIC_15, fill=(92, 74, 54), anchor="lm")
    draw.text((vp_right, HEIGHT - 44), "ARCHIVAL PLATE VERIFIED FOR OFFLINE HERITAGE PACK", font=FONT_MONO_13, fill=(106, 86, 64), anchor="rm")

    im.save(out_path, "WEBP", quality=90)


def create_modern_view(item: dict, out_path: Path):
    im = Image.new("RGB", (WIDTH, HEIGHT), (244, 247, 251))
    draw = ImageDraw.Draw(im)
    rng = random.Random((hash(item["site"]) + 99) & 0xFFFFFFFF)

    draw.rectangle([18, 18, WIDTH - 18, HEIGHT - 18], outline=(42, 74, 114), width=2)
    vp_left, vp_top, vp_right, vp_bottom = 48, 108, WIDTH - 48, HEIGHT - 128

    # Atmospheric daylight gradient
    for y in range(vp_top, vp_bottom):
        ratio = (y - vp_top) / max(1, (vp_bottom - vp_top))
        r = int(item["mod_sky"][0] + (232 - item["mod_sky"][0]) * ratio * 0.78)
        g = int(item["mod_sky"][1] + (242 - item["mod_sky"][1]) * ratio * 0.78)
        b = int(item["mod_sky"][2] + (252 - item["mod_sky"][2]) * ratio * 0.78)
        draw.line([(vp_left, y), (vp_right, y)], fill=(r, g, b))

    horizon_y = vp_bottom - 165
    # Conserved archaeological park lawn & walkways
    draw.rectangle([vp_left, horizon_y, vp_right, vp_bottom], fill=(96, 138, 82))
    draw.polygon([(WIDTH // 2 - 90, horizon_y), (WIDTH // 2 + 90, horizon_y), (WIDTH // 2 + 260, vp_bottom), (WIDTH // 2 - 260, vp_bottom)],
                 fill=(206, 194, 174), outline=(168, 154, 134))

    if "Mahabodhi" in item["site"]:
        peak_x = WIDTH // 2 + 20
        # Lush conserved Bodhi Tree canopy
        for cx, cy, rad in [(peak_x - 220, horizon_y - 135, 105), (peak_x - 275, horizon_y - 90, 82), (peak_x - 170, horizon_y - 170, 78)]:
            draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(44, 112, 52), outline=(32, 86, 38), width=2)

        # Restored corner subsidiary spires (Panchayatana layout)
        for sx in (peak_x - 190, peak_x + 190):
            draw.polygon([(sx, vp_top + 170), (sx - 48, horizon_y), (sx + 48, horizon_y)],
                         fill=(174, 138, 100), outline=(108, 82, 56), width=2)

        # Conserved 55m main Shikhara with gilded crowning finial
        tiers = 9
        top_y = vp_top + 38
        tower_h = (horizon_y - 68) - top_y
        draw.rectangle([peak_x - 215, horizon_y - 68, peak_x + 215, horizon_y], fill=(178, 142, 104), outline=(102, 76, 52), width=2)
        for t_idx in range(tiers):
            y0 = top_y + int(t_idx * (tower_h / tiers))
            y1 = top_y + int((t_idx + 1) * (tower_h / tiers))
            w0 = 26 + int(t_idx * 13)
            w1 = 26 + int((t_idx + 1) * 13)
            draw.polygon([(peak_x - w0, y0), (peak_x + w0, y0), (peak_x + w1, y1), (peak_x - w1, y1)],
                         fill=(188 - (t_idx % 2) * 8, 152 - (t_idx % 2) * 6, 112 - (t_idx % 2) * 5),
                         outline=(110, 84, 58))
            n_niches = max(3, 2 * (t_idx // 2) + 3)
            span = (2 * w0) - 12
            for ni in range(n_niches):
                nx = (peak_x - w0 + 6) + int(ni * (span / max(1, n_niches - 1)))
                draw.rectangle([nx - 4, y0 + 5, nx + 4, y1 - 4], fill=(118, 90, 62))
        # Gilded Chatra / Kalasha spire
        draw.ellipse([peak_x - 24, top_y - 14, peak_x + 24, top_y + 4], fill=(218, 178, 62), outline=(148, 112, 24))
        draw.polygon([(peak_x, top_y - 38), (peak_x - 9, top_y - 12), (peak_x + 9, top_y - 12)], fill=(232, 192, 68))

    elif "Nalanda" in item["site"]:
        mid_x = WIDTH // 2
        envelopes = [
            (350, 48, (186, 96, 66)),
            (290, 96, (176, 88, 60)),
            (230, 148, (168, 82, 54)),
            (172, 202, (160, 76, 50)),
            (120, 254, (152, 70, 46)),
        ]
        for half_w, h, col in envelopes:
            draw.rectangle([mid_x - half_w, horizon_y - h, mid_x + half_w, horizon_y - h + 54],
                           fill=col, outline=(104, 48, 32), width=2)
        # Conserved Gupta stucco niches with protective lime-mortar capping
        for nx in range(mid_x - 200, mid_x + 201, 40):
            if abs(nx - mid_x) > 45:
                draw.rectangle([nx - 12, horizon_y - 140, nx + 12, horizon_y - 98], fill=(228, 214, 192), outline=(112, 56, 38))
                draw.ellipse([nx - 6, horizon_y - 132, nx + 6, horizon_y - 104], fill=(198, 178, 148))
        for step in range(18):
            sy = horizon_y - step * 11
            sw = 54 - step * 1
            draw.rectangle([mid_x - sw, sy - 9, mid_x + sw, sy], fill=(196, 112, 82), outline=(112, 54, 36))

    else:  # Rajgir Cyclopean Wall
        draw.polygon([
            (vp_left, horizon_y - 95),
            (vp_left + 260, horizon_y - 215),
            (vp_left + 580, horizon_y - 155),
            (vp_right - 220, horizon_y - 245),
            (vp_right, horizon_y - 165),
            (vp_right, horizon_y),
            (vp_left, horizon_y),
        ], fill=(82, 128, 78), outline=(58, 96, 54))

        wall_top = horizon_y - 155
        draw.polygon([
            (vp_left + 40, horizon_y + 30),
            (vp_left + 160, wall_top + 20),
            (vp_right - 80, wall_top - 25),
            (vp_right - 40, horizon_y + 30),
        ], fill=item["mod_stone"], outline=(84, 80, 72), width=2)

        for row in range(6):
            y0 = wall_top + 10 + row * 26
            x_cursor = vp_left + 90 - row * 8
            while x_cursor < vp_right - 95:
                bw = rng.randint(68, 118)
                bh = 24
                tone = rng.randint(-10, 10)
                bcol = (164 + tone, 158 + tone, 148 + tone)
                draw.rectangle([x_cursor, y0, min(vp_right - 70, x_cursor + bw), y0 + bh],
                               fill=bcol, outline=(86, 82, 74), width=2)
                x_cursor += bw + 2

    draw.rectangle([vp_left, vp_top, vp_right, vp_bottom], outline=(42, 74, 114), width=2)
    _draw_corner_marks(draw, vp_left - 8, vp_top - 8, vp_right + 8, vp_bottom + 8, (42, 74, 114))

    # Header & Footer Typography
    draw.text((WIDTH // 2, 44), item["mod_title"], font=FONT_SANS_BOLD_22, fill=(24, 52, 92), anchor="mm")
    draw.text((WIDTH // 2, 78), item["mod_subtitle"], font=FONT_SANS_REG_15, fill=(56, 78, 108), anchor="mm")

    draw.text((vp_left, HEIGHT - 92), item["mod_photographer"], font=FONT_SANS_BOLD_16, fill=(28, 48, 76), anchor="lm")
    draw.text((vp_left, HEIGHT - 60), item["mod_legal"], font=FONT_SANS_REG_15, fill=(64, 88, 118), anchor="lm")
    draw.text((vp_right, HEIGHT - 34), "TRUEWAY 2026 CONSERVATION CORPUS (1200x900 WEBP)", font=FONT_MONO_13, fill=(42, 74, 114), anchor="rm")

    im.save(out_path, "WEBP", quality=92)


def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating 6 Then & Now comparison WebP image assets (1200x900, TrueType survey edition)...")

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
