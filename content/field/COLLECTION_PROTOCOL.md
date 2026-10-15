# content/field — lawful reference-photo collection kit (blueprint §17)

No pack ships a photo whose creator, licence, original and permission are
not all recorded (blueprint §16.1 **[G]**). This kit operationalizes the field
collection phase of [content/DATASET_RESEARCH_AND_HARVESTING_SPECIFICATION.md](../DATASET_RESEARCH_AND_HARVESTING_SPECIFICATION.md).
It covers the **15-POI demonstrator**; scale the numbers, not the rules, for the 50–70 pilot (target 5,000–14,000 total images).

## Per-POI capture target (§17.4)

- **10–30 lawful reference photos** per `PHOTO_SUPPORTED` POI for demonstrator (scaling to 100–200 per POI for pilot), across:
  façade, 3/4 view, partial crop, daylight, shade, distance, moderate
  occlusion — **only where photography is permitted**.
- `SEARCH_ONLY` / `TEXT_REFERENCE_ONLY` POIs (all Mahabodhi-complex
  records): **no reference capture on site**. BTMC/CISF regulations strictly
  prohibit phones and recording devices inside the inner complex — use pre-visit content and external kiosks, never a workaround.
- **Unknown/background set (2,500–3,500 corridor scenes, per Dataset Spec §5):**
  Places365 categories (ruins, towers, courtyards, markets, shops), generic Indian temples,
  Southeast Asian stupas, scaffolding, brickwork close-ups, vegetation, crowds, and lookalike structures.
  This set decides the $\le 5\%$ false-accept gate — it is as critical as the reference corpus.

## Session discipline (split integrity, §18.3)

- Group by **photographer + visit/day + viewpoint**; one session never
  appears in both reference and test. Record `photographer_id`,
  `visit_date`, `device_model` per session.
- File naming (enforced by `validate_collection.py`, future):
  `{place_id}__{yyyymmdd}__{photographer}__{viewpoint}__{seq}.jpg`
  Unknowns: `unknown__{category}__{yyyymmdd}__{photographer}__{seq}.jpg`
  where category ∈ shop, scaffold, ruin-generic, brick-closeup, vegetation,
  market, lookalike, interior-museum, crowd, night.
- Keep EXIF at capture; **strip precise geolocation + faces policy review**
  before any contribution leaves the device (§13.6). No photo with an
  identifiable non-consenting person enters the reference index.

## Permission checklist (per site, before shutter)

1. Current on-site photography notice read and recorded
   (`permission_checked_on`, `site_authority` in the field sheet).
2. Venue/ASI/museum consent where required; commercial-shoot rules checked
   via India Cine Hub guidance as a lead only (§31 S27).
3. Contributor rights grant signed (see `consent_template.md`):
   compatible licence target **CC BY-SA 4.0 or compatible**, attribution
   preference, withdrawal policy.
4. Mahabodhi complex: **no capture** — form records `CAPTURE_REFUSED_SITE_RULES`.

## What lands in the pack-builder

For each accepted photo: `asset_id`, `place_id`, `creator`, `original_url`,
`licence_id`, `rights_review_state=APPROVED`, `sha256`, `capture-permission
status`, `collection date`, `reviewer`. Anything else stays out (§28.3
publication rule). Rights registry lives in `content/seed/rights_registry.json`.
