"""Generates print-ready acrylic tabletop QR stands and an affiliate ledger
for 10 Bodh Gaya partner guesthouses and monastery lodges.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DIST = ROOT / "dist" / "guesthouse_qr_stands"
DIST.mkdir(parents=True, exist_ok=True)

PARTNERS = [
    {
        "id": "BG-01",
        "name": "Root Institute for Wisdom Culture",
        "code": "ROOT30",
        "contact_type": "Monastery Retreat Center",
        "payout_rate": "30%",
        "manager": "Reception Desk"
    },
    {
        "id": "BG-02",
        "name": "The Royal Residency",
        "code": "ROYAL30",
        "contact_type": "Heritage Hotel",
        "payout_rate": "30%",
        "manager": "Concierge"
    },
    {
        "id": "BG-03",
        "name": "Zostel Bodh Gaya",
        "code": "ZOSTEL30",
        "contact_type": "Backpacker Hostel",
        "payout_rate": "30%",
        "manager": "Community Lead"
    },
    {
        "id": "BG-04",
        "name": "Buddha Garden Guest House",
        "code": "BGARDEN30",
        "contact_type": "Boutique Lodge",
        "payout_rate": "30%",
        "manager": "Front Desk"
    },
    {
        "id": "BG-05",
        "name": "Hotel Tathagata International",
        "code": "TATHAGATA30",
        "contact_type": "Pilgrim Hotel",
        "payout_rate": "30%",
        "manager": "Operations"
    },
    {
        "id": "BG-06",
        "name": "Maya Heritage Hotel",
        "code": "MAYA30",
        "contact_type": "Premium Hotel",
        "payout_rate": "30%",
        "manager": "Guest Relations"
    },
    {
        "id": "BG-07",
        "name": "Bodhgaya Regency Hotel",
        "code": "REGENCY30",
        "contact_type": "Commercial Hotel",
        "payout_rate": "30%",
        "manager": "Front Desk"
    },
    {
        "id": "BG-08",
        "name": "Oaks Bodhgaya",
        "code": "OAKS30",
        "contact_type": "International Hotel",
        "payout_rate": "30%",
        "manager": "Travel Desk"
    },
    {
        "id": "BG-09",
        "name": "Niranjana Hotel & Retreat",
        "code": "NIRANJANA30",
        "contact_type": "Riverside Retreat",
        "payout_rate": "30%",
        "manager": "Reception"
    },
    {
        "id": "BG-10",
        "name": "Welcome Guest House",
        "code": "WELCOME30",
        "contact_type": "Budget Guesthouse",
        "payout_rate": "30%",
        "manager": "Host"
    }
]

def make_html_stand(partner):
    qr_url = f"https://trueway.guide/activate?ref={partner['code']}&property={partner['id']}"
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>TrueWay Stand - {partner['name']} ({partner['code']})</title>
  <style>
    @page {{
      size: 4in 6in;
      margin: 0;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans Devanagari", sans-serif;
      background: #FAF6F0;
      color: #1C2331;
      width: 4in;
      height: 6in;
      padding: 0.25in;
      margin: auto;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      border: 1px dashed #B84A27;
    }}
    .card {{
      background: #FFFFFF;
      border: 2px solid #E2D9C8;
      border-radius: 12px;
      padding: 16px;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: 0 4px 12px rgba(28, 35, 49, 0.05);
      text-align: center;
    }}
    .badge {{
      display: inline-block;
      background: #FDF2E9;
      color: #B84A27;
      border: 1px solid #B84A27;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 3px 8px;
      border-radius: 999px;
      margin-bottom: 6px;
    }}
    .title {{
      font-size: 18px;
      font-weight: 800;
      color: #1C2331;
      line-height: 1.2;
    }}
    .subtitle {{
      font-size: 11px;
      color: #5A6270;
      margin-top: 4px;
    }}
    .partner-banner {{
      background: #F4EBE1;
      border-radius: 6px;
      padding: 6px;
      margin: 8px 0;
      font-size: 11px;
      font-weight: 700;
      color: #B84A27;
    }}
    .qr-container {{
      background: #FFFFFF;
      border: 2px solid #1C2331;
      border-radius: 8px;
      padding: 8px;
      display: inline-block;
      margin: 4px auto;
    }}
    .promo-box {{
      background: #FFF8EB;
      border: 1px dashed #D97706;
      border-radius: 6px;
      padding: 6px;
      margin: 6px 0;
    }}
    .promo-code {{
      font-size: 14px;
      font-weight: 900;
      letter-spacing: 0.1em;
      color: #D97706;
    }}
    .steps {{
      text-align: left;
      font-size: 10px;
      color: #2D3748;
      line-height: 1.4;
      background: #F8FAFC;
      border-radius: 6px;
      padding: 8px;
    }}
    .footer {{
      font-size: 9px;
      color: #718096;
      border-top: 1px solid #EDF2F7;
      padding-top: 4px;
      display: flex;
      justify-content: space-between;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div>
      <span class="badge">100% Offline AI Heritage Tour</span>
      <h1 class="title">Bodh Gaya &amp; Mahabodhi Temple</h1>
      <p class="subtitle">Visual AI Monument Scanner • Scholar-Verified Audio Guide</p>
      <div class="partner-banner">Exclusive Guest Pass: {partner['name']}</div>
    </div>

    <div>
      <div class="qr-container">
        <!-- Embedded SVG QR Code with TW Brand Core -->
        <svg viewBox="0 0 120 120" width="130" height="130">
          <rect width="120" height="120" fill="#FFFFFF"/>
          <rect x="8" y="8" width="32" height="32" fill="none" stroke="#1C2331" stroke-width="6"/>
          <rect x="18" y="18" width="12" height="12" fill="#1C2331"/>
          <rect x="80" y="8" width="32" height="32" fill="none" stroke="#1C2331" stroke-width="6"/>
          <rect x="90" y="18" width="12" height="12" fill="#1C2331"/>
          <rect x="8" y="80" width="32" height="32" fill="none" stroke="#1C2331" stroke-width="6"/>
          <rect x="18" y="90" width="12" height="12" fill="#1C2331"/>
          <rect x="50" y="12" width="8" height="8" fill="#1C2331"/>
          <rect x="58" y="28" width="8" height="16" fill="#1C2331"/>
          <rect x="48" y="50" width="24" height="24" fill="#B84A27"/>
          <text x="60" y="66" font-size="11" font-weight="bold" fill="#FFFFFF" text-anchor="middle">TW</text>
          <rect x="14" y="52" width="18" height="8" fill="#1C2331"/>
          <rect x="82" y="52" width="24" height="8" fill="#1C2331"/>
          <rect x="52" y="84" width="16" height="8" fill="#1C2331"/>
          <rect x="80" y="80" width="12" height="12" fill="#1C2331"/>
          <rect x="98" y="92" width="14" height="18" fill="#1C2331"/>
          <rect x="76" y="102" width="14" height="8" fill="#1C2331"/>
        </svg>
      </div>

      <div class="promo-box">
        <div style="font-size: 10px; color: #4A5568;">Use Reception Guest Passcode:</div>
        <div class="promo-code">{partner['code']}</div>
      </div>
    </div>

    <div class="steps">
      <b>Quick 3-Step Setup on Hotel Wi-Fi:</b><br/>
      1. Scan QR code to download TrueWay App.<br/>
      2. Enter passcode <b>{partner['code']}</b> for instant unlock.<br/>
      3. Download the Bodh Gaya pack (45 MB) before walking to temple. Runs 100% in Airplane Mode!
    </div>

    <div class="footer">
      <span>Ref: {partner['id']}</span>
      <span>TrueWay Heritage Partner</span>
      <span>Zero Mobile Data Needed</span>
    </div>
  </div>
</body>
</html>
"""

def main():
    ledger = {
        "program": "TrueWay Bodh Gaya Guesthouse Affiliate Network",
        "standard_split": "70% TrueWay / 30% Partner",
        "payout_schedule": "Bi-weekly via UPI / Bank Transfer",
        "partners": PARTNERS
    }
    
    with open(DIST / "GUESTHOUSE_AFFILIATE_LEDGER.json", "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)
    print("Generated GUESTHOUSE_AFFILIATE_LEDGER.json")
    
    for p in PARTNERS:
        html = make_html_stand(p)
        filename = f"Stand_{p['id']}_{p['code']}.html"
        with open(DIST / filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Generated {filename}")
        
    print(f"\nAll 10 acrylic stands created in: {DIST}")

if __name__ == "__main__":
    main()
