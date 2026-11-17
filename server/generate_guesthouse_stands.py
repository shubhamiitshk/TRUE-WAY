"""Batch Generator for TrueWay Guesthouse Acrylic Tabletop QR Standees.

Seeds initial Bodh Gaya partner guesthouses and generates personalized,
print-ready HTML cards ready for acrylic stands at hotel check-in desks.

The QR codes are REAL (segno) and encode:
  $TRUEWAY_AFF_BASE_URL?aff=<AFFILIATE_ID>&src=standee
(default base: https://trueway.travel/dl)

IMPORTANT — DO NOT PRINT until:
1. The base domain is registered and resolves to a landing page that redirects
   Android -> Play Store and iPhone -> App Store, forwarding the aff/src params
   (or set TRUEWAY_AFF_BASE_URL to your live URL when regenerating).
2. The Play Store listing exists (or adjust the base URL accordingly).
3. You have replaced the placeholder phone/UPI details with real ones.
The generated stand will scan to a dead link otherwise.
"""
from __future__ import annotations

import io
import json
import os
from pathlib import Path

import segno

from affiliates import Affiliate, AffiliateManager

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "content" / "field" / "stands"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AFF_BASE_URL = os.environ.get("TRUEWAY_AFF_BASE_URL", "https://trueway.travel/dl")


def affiliate_url(affiliate_id: str) -> str:
    sep = "&" if "?" in AFF_BASE_URL else "?"
    return f"{AFF_BASE_URL}{sep}aff={affiliate_id}&src=standee"


def qr_svg(url: str, scale: int = 6) -> str:
    """Generate a REAL, scannable QR code as inline SVG."""
    qr = segno.make(url, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=scale, dark="#1C2331", light="#FFFFFF", border=1)
    return buf.getvalue().decode("utf-8")

TOP_GUESTHOUSES = [
    {
        "id": "GH_ROOT_01",
        "name": "Root Institute for Wisdom Culture",
        "category": "guesthouse",
        "location": "Bodh Gaya, Bihar",
        "contact_person": "Front Office Manager",
        "phone": "+91-94312-XXXXX",
        "upi": "rootinstitute@upi",
        "rate": 0.30
    },
    {
        "id": "GH_ROYAL_02",
        "name": "The Royal Residency",
        "category": "hotel",
        "location": "Dumuhan-Bodh Gaya Road, Bihar",
        "contact_person": "General Manager",
        "phone": "+91-94314-XXXXX",
        "upi": "royalresidency@upi",
        "rate": 0.30
    },
    {
        "id": "GH_REGENCY_03",
        "name": "Bodhgaya Regency Hotel",
        "category": "hotel",
        "location": "Near Japanese Temple, Bodh Gaya",
        "contact_person": "Reception Supervisor",
        "phone": "+91-94310-XXXXX",
        "upi": "bodhgayaregency@upi",
        "rate": 0.30
    },
    {
        "id": "GH_THAI_04",
        "name": "Wat Thai Monastery Guesthouse",
        "category": "monastery",
        "location": "Bodh Gaya, Bihar",
        "contact_person": "Guest Liaison",
        "phone": "+91-94318-XXXXX",
        "upi": "watthai.bg@upi",
        "rate": 0.30
    },
    {
        "id": "GH_BHUTAN_05",
        "name": "Bhutan Royal Monastery Guesthouse",
        "category": "monastery",
        "location": "Bodh Gaya, Bihar",
        "contact_person": "Liaison Officer",
        "phone": "+91-94319-XXXXX",
        "upi": "bhutanmonastery@upi",
        "rate": 0.30
    },
    {
        "id": "GH_ZOSTEL_06",
        "name": "Zostel Bodh Gaya",
        "category": "hostel",
        "location": "Bodh Gaya, Bihar",
        "contact_person": "Community Lead",
        "phone": "+91-98110-XXXXX",
        "upi": "zostelbg@upi",
        "rate": 0.30
    },
    {
        "id": "GH_MAYA_07",
        "name": "Maya Heritage Hotel",
        "category": "hotel",
        "location": "Main Road, Bodh Gaya",
        "contact_person": "Front Desk Manager",
        "phone": "+91-94315-XXXXX",
        "upi": "mayaheritage@upi",
        "rate": 0.30
    },
    {
        "id": "GH_TATHAGAT_08",
        "name": "Hotel Tathagat International",
        "category": "hotel",
        "location": "Near Kalachakra Maidan, Bodh Gaya",
        "contact_person": "Operations Manager",
        "phone": "+91-94316-XXXXX",
        "upi": "tathagatbg@upi",
        "rate": 0.30
    }
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>TrueWay Reception Stand — {hotel_name}</title>
  <style>
    :root {{
      --bg: #FAF6F0;
      --surface: #FFFFFF;
      --ink: #1C2331;
      --muted: #5A6270;
      --terracotta: #B84A27;
      --saffron: #D97706;
      --emerald: #1E6B52;
      --border: #E2D9C8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans Devanagari", sans-serif;
      background: var(--bg);
      color: var(--ink);
      padding: 24px;
      line-height: 1.5;
    }}
    .stand {{
      max-width: 600px;
      margin: 0 auto;
      background: var(--surface);
      border: 3px solid var(--terracotta);
      border-radius: 18px;
      padding: 30px;
      box-shadow: 0 10px 30px rgba(28, 35, 49, 0.1);
      text-align: center;
    }}
    .partner-tag {{
      display: inline-block;
      background: #FDF2E9;
      color: var(--terracotta);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      padding: 5px 14px;
      border-radius: 999px;
      border: 1px solid var(--terracotta);
      margin-bottom: 12px;
    }}
    h1 {{ font-size: 26px; color: var(--ink); margin-bottom: 6px; }}
    .venue-name {{ font-size: 17px; font-weight: 600; color: var(--terracotta); margin-bottom: 14px; }}
    .alert-banner {{
      background: #FFF8EB;
      border-left: 4px solid var(--saffron);
      padding: 12px 16px;
      border-radius: 8px;
      font-size: 13px;
      color: #92400E;
      text-align: left;
      margin-bottom: 20px;
    }}
    .qr-container {{
      background: var(--ink);
      color: #FFFFFF;
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
    }}
    .qr-code {{
      background: #FFFFFF;
      padding: 14px;
      border-radius: 12px;
      width: 170px;
      height: 170px;
    }}
    .features {{
      text-align: left;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 20px;
    }}
    .feature-card {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      font-size: 12.5px;
    }}
    .feature-card strong {{ color: var(--terracotta); display: block; margin-bottom: 2px; }}
    .qr-code svg {{ display: block; width: 100%; height: 100%; }}
    .staff-footer {{
      border-top: 1px dashed var(--border);
      padding-top: 14px;
      font-size: 11px;
      color: var(--muted);
      display: flex;
      justify-content: space-between;
    }}
    @media print {{
      body {{ background: #FFFFFF; padding: 0; }}
      .stand {{ box-shadow: none; border: 2px solid #000000; }}
    }}
  </style>
</head>
<body>
  <div class="stand">
    <div class="partner-tag">Official Guesthouse Heritage Amenity</div>
    <h1>TrueWay Heritage Companion</h1>
    <div class="venue-name">Complimentary Offline Guide for Guests of {hotel_name}</div>

    <div class="alert-banner">
      <strong>⚠️ Network Dead Zones Ahead</strong>
      Cellular data drops inside Mahabodhi sanctum &amp; Nalanda ruins. Scan below on our <b>Hotel Wi-Fi</b> to download the pack before stepping out!
    </div>

    <div class="qr-container">
      <div style="font-size: 14px; font-weight: bold; letter-spacing: 0.05em; text-transform: uppercase;">
        Scan on Hotel Wi-Fi to Download
      </div>
      <div class="qr-code">
        <!-- REAL QR CODE (segno) encoding: {affiliate_url} -->
        {qr_svg}
      </div>
      <div style="font-size: 12px; color: #E2E8F0;">
        Works 100% in <b>Airplane Mode</b> · Zero Roaming Fees · Audio in English &amp; हिन्दी
      </div>
    </div>

    <div class="features">
      <div class="feature-card">
        <strong>📸 Offline AI Camera Lens</strong>
        Point phone at ruins or stupas to see verified names &amp; ASI history without internet.
      </div>
      <div class="feature-card">
        <strong>🎧 Scholar Audio Docent</strong>
        20 curated bilingual stories explaining the Bodhi Tree, Nalanda, and Rajgir hilltops.
      </div>
      <div class="feature-card">
        <strong>📚 Provenance Over Myths</strong>
        Backed by Alexander Cunningham (1871) and Xuanzang (637 CE) archaeological sources.
      </div>
      <div class="feature-card">
        <strong>🚫 Zero Tourist Scams</strong>
        Explore independently at your own pace without intrusive touts or unsolicited guides.
      </div>
    </div>

    <div class="staff-footer">
      <span>Affiliate ID: <b>{affiliate_id}</b> ({rev_share}% Partner Commission)</span>
      <span>Support: partner@trueway.travel</span>
    </div>
  </div>
</body>
</html>
"""

def generate_all():
    mgr = AffiliateManager()
    generated_files = []
    
    for gh in TOP_GUESTHOUSES:
        aff = Affiliate(
            affiliate_id=gh["id"],
            name=gh["name"],
            category=gh["category"],
            location=gh["location"],
            contact_person=gh["contact_person"],
            contact_phone=gh["phone"],
            payout_upi_or_bank=gh["upi"],
            commission_rate=gh["rate"]
        )
        mgr.register_affiliate(aff)
        
        # Render HTML
        affiliate_url_value = affiliate_url(gh["id"])
        html_content = HTML_TEMPLATE.format(
            hotel_name=gh["name"],
            affiliate_id=gh["id"],
            rev_share=int(gh["rate"] * 100),
            affiliate_url=affiliate_url_value,
            qr_svg=qr_svg(affiliate_url_value),
        )
        file_path = OUTPUT_DIR / f"{gh['id'].lower()}_standee.html"
        file_path.write_text(html_content, encoding="utf-8")
        generated_files.append(file_path)
        print(f"Generated standee: {file_path.name}")
        
    print(f"\nSuccessfully registered {len(TOP_GUESTHOUSES)} affiliates and created {len(generated_files)} standees in {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_all()
