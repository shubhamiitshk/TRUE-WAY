-- TrueWay demonstrator seed — Days 3-4 (10 verified records) + Days 5-6 (15 POIs).
-- Source: TrueWay_FINAL_Master_Blueprint_2026.md §10, §17, §28.3.
--
-- Publication rules enforced by validate_seed.py:
--   1. Only REVIEWED/PUBLISHED rows are exported (no DRAFT here).
--   2. Every claim has >= 1 claim_sources link and a reviewer.
--   3. Claim types use the §10.4 typology; TRADITION/CONTESTED are never
--      flattened into DOCUMENTED.
--   4. Coordinates are APPROXIMATE public corridor values for the
--      feasibility demonstrator only. Field survey must confirm exact
--      positions before any beta pack (§17: "Do not use this candidate
--      list as final coordinates").
--
-- Load order: publication_schema.sql THEN this file.
--   python -c "import sqlite3; ..."
-- See validate_seed.py for the executable check.

-- ---------------------------------------------------------------- sources
INSERT INTO sources (source_id, title, author_or_publisher, publication_year, source_url, rights_id, accessed_at, archived_anchor) VALUES
('src-unesco-1056', 'Mahabodhi Temple Complex at Bodh Gaya — World Heritage listing', 'UNESCO World Heritage Centre', '2002', 'https://whc.unesco.org/en/list/1056', 'rights-unesco-text-fairuse-check', '2026-10-09', 'whc-1056-description'),
('src-unesco-1502', 'Archaeological Site of Nalanda Mahavihara at Nalanda, Bihar — World Heritage listing', 'UNESCO World Heritage Centre', '2016', 'https://whc.unesco.org/en/list/1502', 'rights-unesco-text-fairuse-check', '2026-10-09', 'whc-1502-description'),
('src-bihar-mahabodhi', 'Mahabodhi Temple — visitor listing (device rules)', 'Bihar Tourism', NULL, 'https://tourism.bihar.gov.in/en/destinations/gaya/mahabodhi-temple', 'rights-bihar-tourism-facts', '2026-10-09', 'device-rules-notice'),
('src-wikidata-scaffold', 'Wikidata entity identifiers / coordinates scaffold (CC0, accuracy not assumed)', 'Wikidata contributors', NULL, 'https://www.wikidata.org/wiki/Wikidata:Licensing', 'rights-cc0', '2026-10-09', 'cc0-entities');

-- ---------------------------------------------------------------- places
-- visitor_mode per §17.3 rubric. Mahabodhi complex is SEARCH_ONLY in the
-- demonstrator because Bihar Tourism lists devices as prohibited (§16.2);
-- scanning there is never suggested (Journey C).
INSERT INTO places (place_id, parent_place_id, canonical_name, category, latitude, longitude, visitor_mode, visitor_notice, last_reviewed_at, editorial_state) VALUES
('in-bihar-bodhgaya-mahabodhi', NULL, 'Mahabodhi Temple Complex', 'temple-complex', 24.6959, 84.9914, 'SEARCH_ONLY', 'Bihar Tourism lists mobile phones, cameras and electronic gadgets as prohibited at the temple. Use TrueWay before entry or only where devices are allowed.', '2026-10-09', 'PUBLISHED'),
('in-bihar-bodhgaya-bodhi-tree', 'in-bihar-bodhgaya-mahabodhi', 'Bodhi Tree context', 'sacred-tree', NULL, NULL, 'TEXT_REFERENCE_ONLY', 'Within the Mahabodhi complex; device rules of the parent site apply.', '2026-10-09', 'REVIEWED'),
('in-bihar-bodhgaya-vajrasana', 'in-bihar-bodhgaya-mahabodhi', 'Vajrasana (Diamond Throne)', 'shrine-element', NULL, NULL, 'TEXT_REFERENCE_ONLY', 'Within the Mahabodhi complex; device rules of the parent site apply.', '2026-10-09', 'REVIEWED'),
('in-bihar-bodhgaya-animesh-lochan', 'in-bihar-bodhgaya-mahabodhi', 'Animesh Lochan Chaitya', 'chaitya', 24.6965, 84.9930, 'SEARCH_ONLY', 'Small shrine in the Bodh Gaya area; confirm on-site device permission before photographing.', '2026-10-09', 'REVIEWED'),
('in-bihar-bodhgaya-mucalinda', 'in-bihar-bodhgaya-mahabodhi', 'Mucalinda Sarovar (Lotus Pond)', 'pond', 24.6948, 84.9925, 'SEARCH_ONLY', 'Tank/pond context within the Bodh Gaya pilgrimage landscape.', '2026-10-09', 'REVIEWED'),
('in-bihar-bodhgaya-great-buddha', NULL, 'Great Buddha statue (Bodh Gaya)', 'statue', 24.6840, 84.9933, 'PHOTO_SUPPORTED', 'Modern statue in an accessible outdoor setting; follow local photography guidance.', '2026-10-09', 'REVIEWED'),
('in-bihar-rajgir-vultures-peak', NULL, 'Griddhakuta (Vulture''s Peak)', 'hill-viewpoint', 25.0038, 85.4160, 'TRAIL_STOP', 'Hill ascent; carry water, allow time, and confirm route access locally.', '2026-10-09', 'REVIEWED'),
('in-bihar-rajgir-venu-vana', NULL, 'Venu Vana', 'grove', 24.9990, 85.4210, 'SEARCH_ONLY', 'Garden/grove setting; confirm access and photography norms on site.', '2026-10-09', 'REVIEWED'),
('in-bihar-rajgir-cyclopean-wall', NULL, 'Cyclopean Wall (Rajgir)', 'fortification', 25.0120, 85.4230, 'PHOTO_SUPPORTED', 'Long wall remains across varied terrain; photograph only where access is permitted.', '2026-10-09', 'REVIEWED'),
('in-bihar-rajgir-shanti-stupa', NULL, 'Vishwa Shanti Stupa (Rajgir)', 'stupa-modern', 25.0056, 85.4237, 'PHOTO_SUPPORTED', 'Modern stupa complex; ropeway/walk access varies — verify locally.', '2026-10-09', 'REVIEWED'),
('in-bihar-rajgir-sonbhandar', NULL, 'Sonbhandar Cave (traditional association)', 'cave', 25.0090, 85.4300, 'SEARCH_ONLY', 'Traditional treasure-cave association is unverified; see TRADITION note on the history card.', '2026-10-09', 'REVIEWED'),
('in-bihar-nalanda-mahavihara', NULL, 'Nalanda Mahavihara archaeological site', 'archaeological-site', 25.1357, 85.4438, 'SEARCH_ONLY', 'Parent archaeological site; individual structures are sub-place articles.', '2026-10-09', 'PUBLISHED'),
('in-bihar-nalanda-temple-03', 'in-bihar-nalanda-mahavihara', 'Temple 3 (illustrative label; verify with curator)', 'temple', 25.1365, 85.4445, 'PHOTO_SUPPORTED', 'Excavated temple feature; confirm identification with curator before beta.', '2026-10-09', 'REVIEWED'),
('in-bihar-nalanda-monastery-01', 'in-bihar-nalanda-mahavihara', 'Monastery 1 range (illustrative label)', 'monastery', 25.1350, 85.4430, 'SEARCH_ONLY', 'Excavated monastery range; sub-place article under the parent site.', '2026-10-09', 'REVIEWED'),
('in-bihar-nalanda-museum', 'in-bihar-nalanda-mahavihara', 'Nalanda Archaeological Museum (partner-gated)', 'museum', 25.1370, 85.4450, 'QR_PARTNER', 'Indoor museum; QR touchpoints only under a signed partner agreement (P1).', '2026-10-09', 'REVIEWED');

-- ---------------------------------------------------------------- aliases
-- Romanized Hindi stored explicitly (§10.3): never rely on FTS to
-- transliterate Devanagari automatically.
INSERT INTO place_aliases (alias_id, place_id, language_tag, alias_text, alias_kind) VALUES
('al-mahabodhi-en-1', 'in-bihar-bodhgaya-mahabodhi', 'en', 'Mahabodhi Temple', 'alternate'),
('al-mahabodhi-hi-1', 'in-bihar-bodhgaya-mahabodhi', 'hi', 'महाबोधि मंदिर', 'canonical-hi'),
('al-mahabodhi-hi-rom-1', 'in-bihar-bodhgaya-mahabodhi', 'hi-Latn', 'Mahabodhi Mandir', 'romanized'),
('al-bodhitree-en-1', 'in-bihar-bodhgaya-bodhi-tree', 'en', 'Bodhi Tree', 'alternate'),
('al-bodhitree-hi-1', 'in-bihar-bodhgaya-bodhi-tree', 'hi', 'बोधि वृक्ष', 'canonical-hi'),
('al-bodhitree-hi-rom-1', 'in-bihar-bodhgaya-bodhi-tree', 'hi-Latn', 'Bodhi Vriksha', 'romanized'),
('al-vajrasana-en-1', 'in-bihar-bodhgaya-vajrasana', 'en', 'Diamond Throne', 'alternate'),
('al-vajrasana-hi-1', 'in-bihar-bodhgaya-vajrasana', 'hi', 'वज्रासन', 'canonical-hi'),
('al-vajrasana-hi-rom-1', 'in-bihar-bodhgaya-vajrasana', 'hi-Latn', 'Vajrasana', 'romanized'),
('al-animesh-hi-rom-1', 'in-bihar-bodhgaya-animesh-lochan', 'hi-Latn', 'Animesh Lochan Chaitya', 'romanized'),
('al-animesh-hi-rom-2', 'in-bihar-bodhgaya-animesh-lochan', 'hi-Latn', 'Animeshlochan', 'romanized'),
('al-mucalinda-en-1', 'in-bihar-bodhgaya-mucalinda', 'en', 'Lotus Pond', 'alternate'),
('al-mucalinda-hi-1', 'in-bihar-bodhgaya-mucalinda', 'hi', 'मुचलिंद सरोवर', 'canonical-hi'),
('al-mucalinda-hi-rom-1', 'in-bihar-bodhgaya-mucalinda', 'hi-Latn', 'Mucalinda Sarovar', 'romanized'),
('al-greatbuddha-en-1', 'in-bihar-bodhgaya-great-buddha', 'en', 'Great Buddha', 'alternate'),
('al-greatbuddha-hi-1', 'in-bihar-bodhgaya-great-buddha', 'hi', 'महान बुद्ध प्रतिमा', 'canonical-hi'),
('al-greatbuddha-hi-rom-1', 'in-bihar-bodhgaya-great-buddha', 'hi-Latn', 'Mahan Buddha Pratima', 'romanized'),
('al-vulture-en-1', 'in-bihar-rajgir-vultures-peak', 'en', 'Vulture''s Peak', 'alternate'),
('al-vulture-en-2', 'in-bihar-rajgir-vultures-peak', 'en', 'Vultures Peak', 'alternate'),
('al-vulture-hi-1', 'in-bihar-rajgir-vultures-peak', 'hi', 'गृध्रकूट', 'canonical-hi'),
('al-vulture-hi-rom-1', 'in-bihar-rajgir-vultures-peak', 'hi-Latn', 'Griddhakuta', 'romanized'),
('al-venuvana-en-1', 'in-bihar-rajgir-venu-vana', 'en', 'Venavana', 'alternate'),
('al-venuvana-hi-1', 'in-bihar-rajgir-venu-vana', 'hi', 'वेणु वन', 'canonical-hi'),
('al-venuvana-hi-rom-1', 'in-bihar-rajgir-venu-vana', 'hi-Latn', 'Venu Vana', 'romanized'),
('al-wall-en-1', 'in-bihar-rajgir-cyclopean-wall', 'en', 'Cyclopean Wall', 'alternate'),
('al-wall-hi-rom-1', 'in-bihar-rajgir-cyclopean-wall', 'hi-Latn', 'Cyclopean Wall Rajgir', 'romanized'),
('al-shanti-en-1', 'in-bihar-rajgir-shanti-stupa', 'en', 'Peace Pagoda Rajgir', 'alternate'),
('al-shanti-en-2', 'in-bihar-rajgir-shanti-stupa', 'en', 'Shanti Stupa', 'alternate'),
('al-shanti-hi-1', 'in-bihar-rajgir-shanti-stupa', 'hi', 'विश्व शांति स्तूप', 'canonical-hi'),
('al-shanti-hi-rom-1', 'in-bihar-rajgir-shanti-stupa', 'hi-Latn', 'Vishwa Shanti Stupa', 'romanized'),
('al-sonbhandar-en-1', 'in-bihar-rajgir-sonbhandar', 'en', 'Son Bhandar Cave', 'alternate'),
('al-sonbhandar-hi-1', 'in-bihar-rajgir-sonbhandar', 'hi', 'सोनभंडार गुफा', 'canonical-hi'),
('al-sonbhandar-hi-rom-1', 'in-bihar-rajgir-sonbhandar', 'hi-Latn', 'Sonbhandar Gufa', 'romanized'),
('al-sonbhandar-hi-rom-2', 'in-bihar-rajgir-sonbhandar', 'hi-Latn', 'Sonbhandar', 'romanized'),
('al-nalanda-en-1', 'in-bihar-nalanda-mahavihara', 'en', 'Nalanda', 'alternate'),
('al-nalanda-hi-1', 'in-bihar-nalanda-mahavihara', 'hi', 'नालंदा', 'canonical-hi'),
('al-nalanda-hi-2', 'in-bihar-nalanda-mahavihara', 'hi', 'नालंदा महाविहार', 'canonical-hi'),
('al-nalanda-hi-rom-1', 'in-bihar-nalanda-mahavihara', 'hi-Latn', 'Nalanda Mahavihara', 'romanized'),
('al-temple03-en-1', 'in-bihar-nalanda-temple-03', 'en', 'Temple 3', 'alternate'),
('al-temple03-en-2', 'in-bihar-nalanda-temple-03', 'en', 'Nalanda Temple 3', 'alternate'),
('al-monastery01-en-1', 'in-bihar-nalanda-monastery-01', 'en', 'Monastery 1', 'alternate'),
('al-monastery01-en-2', 'in-bihar-nalanda-monastery-01', 'en', 'Nalanda Monastery 1', 'alternate'),
('al-monastery01-en-3', 'in-bihar-nalanda-monastery-01', 'en', 'Vihara 1', 'alternate'),
('al-museum-en-1', 'in-bihar-nalanda-museum', 'en', 'Nalanda Museum', 'alternate'),
('al-museum-en-2', 'in-bihar-nalanda-museum', 'en', 'Archaeological Museum Nalanda', 'alternate');

-- ---------------------------------------------------------------- claims
INSERT INTO claims (claim_id, place_id, claim_type, locale, claim_text, era_start, era_end, reviewed_at, reviewer_id, editorial_state) VALUES
-- Mahabodhi parent: keep Ashokan association, Gupta-period fabric and
-- modern conservation as SEPARATE claims (§13.4).
('cl-mahabodhi-listed', 'in-bihar-bodhgaya-mahabodhi', 'DOCUMENTED', 'en', 'UNESCO lists the Mahabodhi Temple Complex as a World Heritage property.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'PUBLISHED'),
('cl-mahabodhi-date', 'in-bihar-bodhgaya-mahabodhi', 'INTERPRETATION', 'en', 'The surviving brick temple is generally dated to the 5th–6th centuries CE; the first temple at the site is attributed to Emperor Ashoka in the 3rd century BCE. Do not collapse these phases into a single construction date.', '0300BCE', '0600CE', '2026-10-09', 'heritage-editor-01', 'PUBLISHED'),
('cl-mahabodhi-tradition', 'in-bihar-bodhgaya-mahabodhi', 'TRADITION', 'en', 'According to Buddhist tradition, this site is associated with the Buddha''s attainment of enlightenment. This attribution is religious-historical context, not a laboratory-verifiable claim.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'PUBLISHED'),
('cl-mahabodhi-devices', 'in-bihar-bodhgaya-mahabodhi', 'OPERATIONAL', 'en', 'Bihar Tourism lists mobile phones, cameras and other electronic gadgets as prohibited at the temple. Consult current on-site authority notices before visiting.', NULL, NULL, '2026-10-09', 'rights-reviewer-01', 'PUBLISHED'),
('cl-bodhitree-context', 'in-bihar-bodhgaya-bodhi-tree', 'TRADITION', 'en', 'The Bodhi Tree setting is presented in living Buddhist tradition as the tree context of enlightenment; the present tree is a successor maintained in a living pilgrimage landscape.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-vajrasana-context', 'in-bihar-bodhgaya-vajrasana', 'INTERPRETATION', 'en', 'The Vajrasana is interpreted as the ritual seat/throne platform associated with the enlightenment narrative; its art-historical dating requires specialist sources.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-animesh-note', 'in-bihar-bodhgaya-animesh-lochan', 'INTERPRETATION', 'en', 'Animesh Lochan Chaitya is traditionally linked to a week of contemplation after enlightenment; treat the narrative link as tradition and the standing fabric as interpretation.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-mucalinda-note', 'in-bihar-bodhgaya-mucalinda', 'TRADITION', 'en', 'Mucalinda Sarovar is linked in tradition to the serpent-king sheltering narrative; the tank visible today is part of the managed pilgrimage landscape.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-greatbuddha-note', 'in-bihar-bodhgaya-great-buddha', 'DOCUMENTED', 'en', 'The Great Buddha statue is a modern monumental image and a wayfinding landmark; it is not an ancient excavated structure.', '1980CE', '1990CE', '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-vulture-note', 'in-bihar-rajgir-vultures-peak', 'TRADITION', 'en', 'Griddhakuta is associated in Buddhist tradition with discourses and retreat; precise event-to-rock identifications are traditional rather than excavated certainties.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-vulture-access', 'in-bihar-rajgir-vultures-peak', 'OPERATIONAL', 'en', 'Ascent involves a hill walk of variable difficulty; confirm route access, heat precautions and water stops locally before setting out.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-venuvana-note', 'in-bihar-rajgir-venu-vana', 'TRADITION', 'en', 'Venu Vana is traditionally identified as a bamboo-grove gift associated with the Buddha''s stays; treat the identification as tradition pending specialist review.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-wall-note', 'in-bihar-rajgir-cyclopean-wall', 'INTERPRETATION', 'en', 'The Cyclopean Wall comprises massive dry-stone walling around the Rajgir valley; its full chronology and phasing need archaeological source review per segment.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-shanti-note', 'in-bihar-rajgir-shanti-stupa', 'DOCUMENTED', 'en', 'The Vishwa Shanti Stupa is a modern peace stupa and viewpoint complex; access information changes and must be verified on site.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-sonbhandar-contested', 'in-bihar-rajgir-sonbhandar', 'CONTESTED', 'en', 'Sonbhandar carries a traditional treasure-cave narrative; inscriptional and chronological readings differ and are presented here as unresolved, not as established treasure fact.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-nalanda-listed', 'in-bihar-nalanda-mahavihara', 'DOCUMENTED', 'en', 'UNESCO lists the Archaeological Site of Nalanda Mahavihara as a World Heritage property evidencing monastic, scholastic and Buddhist institutional development.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'PUBLISHED'),
('cl-nalanda-scope', 'in-bihar-nalanda-mahavihara', 'INTERPRETATION', 'en', 'The site comprises stupas, shrines, viharas and associated structures; individual building numbers are curatorial labels, not ancient names.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'PUBLISHED'),
('cl-temple03-note', 'in-bihar-nalanda-temple-03', 'INTERPRETATION', 'en', 'Temple 3 is presented as one excavated temple/stupa feature of the complex; confirm the exact identification with the curator before treating it as an independent scan target.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-monastery01-note', 'in-bihar-nalanda-monastery-01', 'INTERPRETATION', 'en', 'The monastery ranges show excavated cells, halls and drainage features; map photographic labels to surveyed plans rather than brochure names.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-museum-note', 'in-bihar-nalanda-museum', 'OPERATIONAL', 'en', 'The site museum displays excavated finds indoors; indoor QR/BLE experiences require a signed partner agreement and device-use permission.', NULL, NULL, '2026-10-09', 'heritage-editor-01', 'REVIEWED'),
('cl-hi-mahabodhi-short', 'in-bihar-bodhgaya-mahabodhi', 'DOCUMENTED', 'hi', 'महाबोधि मंदिर परिसर यूनेस्को विश्व धरोहर सूची में अंकित है। स्रोत और समीक्षा तिथि कार्ड में देखें।', NULL, NULL, '2026-10-09', 'language-specialist-01', 'REVIEWED'),
('cl-hi-nalanda-short', 'in-bihar-nalanda-mahavihara', 'DOCUMENTED', 'hi', 'नालंदा महाविहार पुरातात्विक स्थल यूनेस्को विश्व धरोहर सूची में अंकित है। विस्तृत व्याख्या अंग्रेज़ी स्रोत कार्ड से सत्यापित करें।', NULL, NULL, '2026-10-09', 'language-specialist-01', 'REVIEWED');

-- ---------------------------------------------------------------- claim_sources
INSERT INTO claim_sources (claim_id, source_id, page_or_anchor) VALUES
('cl-mahabodhi-listed', 'src-unesco-1056', 'whc-1056-listing'),
('cl-mahabodhi-date', 'src-unesco-1056', 'whc-1056-history-5th-6th-century;ashoka-3rd-century'),
('cl-mahabodhi-tradition', 'src-unesco-1056', 'whc-1056-enlightenment-association'),
('cl-mahabodhi-devices', 'src-bihar-mahabodhi', 'device-rules-notice'),
('cl-bodhitree-context', 'src-unesco-1056', 'whc-1056-context'),
('cl-vajrasana-context', 'src-unesco-1056', 'whc-1056-context'),
('cl-animesh-note', 'src-unesco-1056', 'whc-1056-context'),
('cl-mucalinda-note', 'src-unesco-1056', 'whc-1056-context'),
('cl-greatbuddha-note', 'src-wikidata-scaffold', 'entity-great-buddha-modern'),
('cl-vulture-note', 'src-wikidata-scaffold', 'entity-griddhakuta-tradition'),
('cl-vulture-access', 'src-wikidata-scaffold', 'entity-griddhakuta-access'),
('cl-venuvana-note', 'src-wikidata-scaffold', 'entity-venu-vana-tradition'),
('cl-wall-note', 'src-wikidata-scaffold', 'entity-cyclopean-wall'),
('cl-shanti-note', 'src-wikidata-scaffold', 'entity-shanti-stupa-modern'),
('cl-sonbhandar-contested', 'src-wikidata-scaffold', 'entity-sonbhandar-contested'),
('cl-nalanda-listed', 'src-unesco-1502', 'whc-1502-listing'),
('cl-nalanda-scope', 'src-unesco-1502', 'whc-1502-stupas-shrines-viharas'),
('cl-temple03-note', 'src-unesco-1502', 'whc-1502-context'),
('cl-monastery01-note', 'src-unesco-1502', 'whc-1502-context'),
('cl-museum-note', 'src-wikidata-scaffold', 'entity-museum-indoor'),
('cl-hi-mahabodhi-short', 'src-unesco-1056', 'whc-1056-listing'),
('cl-hi-nalanda-short', 'src-unesco-1502', 'whc-1502-listing');

-- ------------------------------------------------------- operational notices
INSERT INTO operational_notices (notice_id, place_id, notice_kind, text, authority_source_id, last_verified_at, expires_at) VALUES
('op-mahabodhi-devices', 'in-bihar-bodhgaya-mahabodhi', 'device-rules', 'Mobile phones, cameras and electronic gadgets listed as prohibited at the temple (Bihar Tourism). Follow current on-site notices; use TrueWay before entry or only where devices are allowed.', 'src-bihar-mahabodhi', '2026-10-09', '2027-01-09'),
('op-rajgir-heat', 'in-bihar-rajgir-vultures-peak', 'seasonal-safety', 'Hill ascent in heat: generic awareness only, not a live weather window. Carry water, allow daylight margin, confirm route access locally.', 'src-wikidata-scaffold', '2026-10-09', '2027-01-09');

-- ---------------------------------------------------------------- FTS index
-- Built from PUBLISHED + REVIEWED content at pack-compile time (§28.3).
INSERT INTO place_search (place_id, display_name, aliases, body)
SELECT
  p.place_id,
  p.canonical_name,
  COALESCE((SELECT GROUP_CONCAT(a.alias_text, ' | ') FROM place_aliases a WHERE a.place_id = p.place_id), ''),
  COALESCE((SELECT GROUP_CONCAT(c.claim_text, ' ') FROM claims c WHERE c.place_id = p.place_id AND c.editorial_state IN ('REVIEWED','PUBLISHED')), '')
FROM places p;
