# content/seed — demonstrator corpus (blueprint §17, §28)

This directory holds the **15-POI feasibility corpus** for the 14-day
sprint (Days 3–6). It is editorial source material, not app code.

| File | Purpose |
|---|---|
| `seed_demo.sql` | 15 places, 25 aliases, 22 claims, 22 claim↔source links, 2 operational notices, FTS rows. Runs **after** `../schema/publication_schema.sql`. |
| `validate_seed.py` | CI gate: builds a throwaway SQLite DB (stdlib only) and enforces §28.3 publication rules + FTS sanity queries. `python validate_seed.py` must exit 0. |
| `bibliography.json` | Source registry behind `source_id` (title, publisher, URL, rights pointer, accessed date). |
| `rights_registry.json` | Asset/rights gate state for Days 5–6: which POIs may ship reference photos and under what licence. No `APPROVED` photo asset is claimed yet — vectors land Days 7–10. |

## Publication rules (from `../README.md`, §28.3)

1. No `DRAFT` / rights-`PENDING` rows are exported — this seed contains none.
2. Coordinates are **approximate public corridor values** for the
   demonstrator; field survey must confirm exact positions before beta.
3. Mahabodhi records are `SEARCH_ONLY` / `TEXT_REFERENCE_ONLY`: Bihar
   Tourism lists devices as prohibited, so the app never suggests
   scanning there (Journey C, §6.3).

## Status

- ✅ 15 places ≥ 10-record Days 3–4 gate
- ✅ `python validate_seed.py` passes (run it after any edit)
- ⬜ Real reference-photo assets + `APPROVED` rights rows (Days 5–6 field work)
- ⬜ Hindi long-form articles beyond short claims (Days 12–15)
