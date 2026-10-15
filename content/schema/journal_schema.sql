-- TrueWay private journal database — SEPARATE FILE from publisher content.
-- From TrueWay_FINAL_Master_Blueprint_2026.md §28.4.
-- Deleting a downloaded region must never silently delete private notes;
-- a journal row may reference a place_id that is no longer installed —
-- show "content missing" rather than dropping the user's data.

CREATE TABLE journal_entries (
  entry_id TEXT PRIMARY KEY,
  place_id TEXT,
  created_at TEXT NOT NULL,
  user_note TEXT,
  local_photo_uri TEXT,
  include_location_on_export INTEGER NOT NULL DEFAULT 0,
  local_only INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE achievement_defs (
  achievement_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  criteria_json TEXT NOT NULL
);

CREATE TABLE achievement_events (
  achievement_id TEXT NOT NULL REFERENCES achievement_defs(achievement_id),
  unlocked_at TEXT NOT NULL,
  evidence_entry_id TEXT REFERENCES journal_entries(entry_id),
  PRIMARY KEY (achievement_id, unlocked_at)
);

CREATE TABLE consent_choices (
  consent_id TEXT PRIMARY KEY,
  purpose TEXT NOT NULL,
  granted INTEGER NOT NULL CHECK(granted IN (0,1)),
  changed_at TEXT NOT NULL
);
