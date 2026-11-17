# TrueWay Guesthouse QR Standees — Print-Ready Package

These are print-ready HTML standees (A5 tabletop acrylic). QR codes are **real**
(segno) and encode: `<base>?aff=<AFFILIATE_ID>&src=standee`, default base
`https://trueway.travel/dl`.

## ⛔ DO NOT PRINT until all of the following are true

1. **The base domain/URL is live.** `trueway.travel` does not exist yet. Register it
   (or set `TRUEWAY_AFF_BASE_URL`) so the URL resolves to a landing page that:
   - Redirects Android → Google Play listing, iPhone → App Store listing
   - Forwards the `aff` and `src` query parameters so affiliate attribution is preserved
2. **The TrueWay app is actually on the Play Store.** A QR that sends guests to a page
   saying "app not found" kills trust at check-in.
3. **Placeholders are replaced.** The phone numbers (`+91-94312-XXXXX`) and UPI IDs are
   placeholders — replace with real guesthouse contacts and your payout details in
   `server/generate_guesthouse_stands.py` before regenerating.

## Regenerating with your live URL

```powershell
cd server
$env:TRUEWAY_AFF_BASE_URL = "https://trueway.travel/dl"   # or Play Store link
python generate_guesthouse_stands.py
python ..\tests\fixtures\qr\verify_guesthouse_qr.py      # confirms real QR + URL
```

## Printing

1. Open any `*_standee.html` in Chrome/Edge
2. `Ctrl+P` → Save as PDF, **A5**, 100% scale, enable "Background graphics"
3. Print on 200–300 gsm or drop into A5 acrylic stands
4. Test-scan the printed QR with a phone before deployment

## Verify

```powershell
python tests\fixtures\qr\verify_guesthouse_qr.py
```

Confirms every standee has a real segno-generated QR and the correct affiliate URL.
