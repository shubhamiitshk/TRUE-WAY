-- TrueWay publication (knowledge) database
-- Verbatim structure from TrueWay_FINAL_Master_Blueprint_2026.md §28.3.
-- Executable SQLite DDL; approved/published content only is exported to packs.

PRAGMA foreign_keys = ON;

CREATE TABLE places (
  place_id TEXT PRIMARY KEY,
  parent_place_id TEXT REFERENCES places(place_id),
  canonical_name TEXT NOT NULL,
  category TEXT NOT NULL,
  latitude REAL CHECK(latitude IS NULL OR latitude BETWEEN -90 AND 90),
  longitude REAL CHECK(longitude IS NULL OR longitude BETWEEN -180 AND 180),
  visitor_mode TEXT NOT NULL CHECK(visitor_mode IN
    ('PHOTO_SUPPORTED','SEARCH_ONLY','QR_PARTNER','TRAIL_STOP','TEXT_REFERENCE_ONLY')),
  visitor_notice TEXT,
  last_reviewed_at TEXT NOT NULL,
  editorial_state TEXT NOT NULL CHECK(editorial_state IN ('DRAFT','REVIEWED','PUBLISHED'))
);

CREATE TABLE place_aliases (
  alias_id TEXT PRIMARY KEY,
  place_id TEXT NOT NULL REFERENCES places(place_id),
  language_tag TEXT NOT NULL,
  alias_text TEXT NOT NULL,
  alias_kind TEXT NOT NULL
);

CREATE TABLE sources (
  source_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  author_or_publisher TEXT,
  publication_year TEXT,
  source_url TEXT,
  rights_id TEXT,
  accessed_at TEXT,
  archived_anchor TEXT
);

CREATE TABLE claims (
  claim_id TEXT PRIMARY KEY,
  place_id TEXT NOT NULL REFERENCES places(place_id),
  claim_type TEXT NOT NULL CHECK(claim_type IN
    ('DOCUMENTED','INTERPRETATION','TRADITION','CONTESTED','OPERATIONAL','HYPOTHESIS')),
  locale TEXT NOT NULL,
  claim_text TEXT NOT NULL,
  era_start TEXT,
  era_end TEXT,
  reviewed_at TEXT NOT NULL,
  reviewer_id TEXT NOT NULL,
  editorial_state TEXT NOT NULL CHECK(editorial_state IN ('DRAFT','REVIEWED','PUBLISHED'))
);

CREATE TABLE claim_sources (
  claim_id TEXT NOT NULL REFERENCES claims(claim_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  page_or_anchor TEXT,
  PRIMARY KEY (claim_id, source_id)
);

CREATE TABLE assets (
  asset_id TEXT PRIMARY KEY,
  place_id TEXT REFERENCES places(place_id),
  media_type TEXT NOT NULL,
  original_url TEXT,
  creator TEXT,
  licence_id TEXT NOT NULL,
  rights_review_state TEXT NOT NULL CHECK(rights_review_state IN
    ('PENDING','APPROVED','REJECTED')),
  sha256 TEXT NOT NULL,
  reviewed_at TEXT NOT NULL
);

CREATE TABLE reference_embeddings (
  asset_id TEXT NOT NULL REFERENCES assets(asset_id),
  model_id TEXT NOT NULL,
  model_version TEXT NOT NULL,
  dimensions INTEGER NOT NULL CHECK(dimensions > 0),
  vector BLOB NOT NULL,
  PRIMARY KEY (asset_id, model_id, model_version)
);

CREATE TABLE operational_notices (
  notice_id TEXT PRIMARY KEY,
  place_id TEXT NOT NULL REFERENCES places(place_id),
  notice_kind TEXT NOT NULL,
  text TEXT NOT NULL,
  authority_source_id TEXT REFERENCES sources(source_id),
  last_verified_at TEXT NOT NULL,
  expires_at TEXT
);

CREATE TABLE touchpoints (
  touchpoint_id TEXT PRIMARY KEY,
  place_id TEXT NOT NULL REFERENCES places(place_id),
  issuer_id TEXT NOT NULL,
  key_id TEXT NOT NULL,
  site_serial TEXT,
  approved_location_note TEXT,
  last_inspected_at TEXT,
  status TEXT NOT NULL CHECK(status IN ('DRAFT','ACTIVE','SUSPENDED','REVOKED'))
);

CREATE TABLE pack_releases (
  pack_id TEXT NOT NULL,
  release_version TEXT NOT NULL,
  schema_version INTEGER NOT NULL,
  manifest_sha256 TEXT NOT NULL,
  publisher_key_id TEXT NOT NULL,
  source_snapshot_at TEXT NOT NULL,
  PRIMARY KEY (pack_id, release_version)
);

CREATE TABLE pack_change_events (
  event_id TEXT PRIMARY KEY,
  pack_id TEXT NOT NULL,
  release_version TEXT NOT NULL,
  change_type TEXT NOT NULL,
  human_summary TEXT NOT NULL,
  previous_claim_id TEXT,
  editor_id TEXT,
  FOREIGN KEY (pack_id, release_version)
    REFERENCES pack_releases(pack_id, release_version)
);

CREATE INDEX idx_places_parent ON places(parent_place_id);
CREATE INDEX idx_places_coords ON places(latitude, longitude);
CREATE INDEX idx_alias_place ON place_aliases(place_id);
CREATE INDEX idx_claim_place_locale ON claims(place_id, locale, editorial_state);
CREATE INDEX idx_asset_place ON assets(place_id);
CREATE INDEX idx_notice_place ON operational_notices(place_id);

-- Index built from PUBLISHED and REVIEWED content at pack-compilation time.
CREATE VIRTUAL TABLE place_search USING fts5(
  place_id UNINDEXED,
  display_name,
  aliases,
  body,
  tokenize='unicode61 remove_diacritics 2'
);
