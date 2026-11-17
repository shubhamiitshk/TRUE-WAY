-- TrueWay Regional Seed: India Golden Triangle Corridor
-- Package ID: in-golden-triangle
-- Version: 2026.10.1
-- Sites: Taj Mahal, Qutub Minar, Red Fort, Hawa Mahal, Amer Fort, Agra Fort, Fatehpur Sikri, Humayun's Tomb, City Palace Jaipur.
-- Strictly compliant with publication_schema.sql and places_schema.sql.

-- ---------------------------------------------------------------- sources
INSERT INTO sources (source_id, title, author_or_publisher, publication_year, source_url, rights_id, accessed_at, archived_anchor) VALUES
('src-unesco-252', 'Taj Mahal — World Heritage Inscription & Advisory Body Evaluation', 'UNESCO World Heritage Centre', '1983', 'https://whc.unesco.org/en/list/252', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-252-eval'),
('src-unesco-233', 'Qutb Minar and its Monuments, Delhi — World Heritage Inscription', 'UNESCO World Heritage Centre', '1993', 'https://whc.unesco.org/en/list/233', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-233-eval'),
('src-unesco-1054', 'Red Fort Complex — World Heritage Inscription & Evaluation', 'UNESCO World Heritage Centre', '2007', 'https://whc.unesco.org/en/list/1054', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-1054-eval'),
('src-unesco-251', 'Agra Fort — World Heritage Inscription', 'UNESCO World Heritage Centre', '1983', 'https://whc.unesco.org/en/list/251', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-251-eval'),
('src-unesco-255', 'Fatehpur Sikri — World Heritage Inscription', 'UNESCO World Heritage Centre', '1986', 'https://whc.unesco.org/en/list/255', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-255-eval'),
('src-unesco-232', 'Humayun''s Tomb, Delhi — World Heritage Inscription', 'UNESCO World Heritage Centre', '1993', 'https://whc.unesco.org/en/list/232', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-232-eval'),
('src-unesco-247', 'Hill Forts of Rajasthan (Amer Fort) — World Heritage Inscription', 'UNESCO World Heritage Centre', '2013', 'https://whc.unesco.org/en/list/247', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-247-eval'),
('src-asi-agra-circle', 'Monuments of Agra: Taj Mahal, Agra Fort, Fatehpur Sikri Monograph', 'Archaeological Survey of India (ASI)', '2018', 'https://asi.nic.in/circle-agra/', 'rights-asi-official-doc', '2026-10-15', 'asi-agra-monograph'),
('src-asi-delhi-circle', 'Monuments of Delhi: Qutb Minar, Red Fort, Humayun''s Tomb', 'Archaeological Survey of India (ASI)', '2019', 'https://asi.nic.in/circle-delhi/', 'rights-asi-official-doc', '2026-10-15', 'asi-delhi-monograph'),
('src-rajasthan-tourism-jaipur', 'Jaipur Monuments: Hawa Mahal and City Palace Official Archive', 'Department of Tourism, Government of Rajasthan', '2021', 'https://www.tourism.rajasthan.gov.in/jaipur.html', 'rights-gov-open', '2026-10-15', 'raj-tourism-jaipur'),
('src-koch-taj', 'The Complete Taj Mahal and the Riverfront Gardens of Agra', 'Ebba Koch, Thames & Hudson', '2006', 'https://www.thamesandhudson.com/the-complete-taj-mahal', 'rights-academic-cite', '2026-10-15', 'koch-taj-ch3');

-- ---------------------------------------------------------------- places
INSERT INTO places (place_id, parent_place_id, canonical_name, category, latitude, longitude, visitor_mode, visitor_notice, last_reviewed_at, editorial_state) VALUES
('in-up-agra-taj-mahal', NULL, 'Taj Mahal', 'mausoleum', 27.1751, 78.0421, 'PHOTO_SUPPORTED', 'Footwear covers or removal required on marble plinth; tripods, drones and commercial filming gear restricted without ASI permit; closed on Fridays.', '2026-10-15', 'PUBLISHED'),
('in-delhi-qutub-minar', NULL, 'Qutub Minar', 'minaret-complex', 28.5245, 77.1855, 'PHOTO_SUPPORTED', 'Internal minaret staircase closed to visitors since 1981; photography permitted in the surrounding courtyard; ASI ticket required.', '2026-10-15', 'PUBLISHED'),
('in-delhi-red-fort', NULL, 'Red Fort (Lal Qila)', 'fortress-palace', 28.6562, 77.2410, 'PHOTO_SUPPORTED', 'High-security zone; baggage scanners at Lahori Gate; drone flights strictly prohibited; closed on Mondays.', '2026-10-15', 'PUBLISHED'),
('in-rj-jaipur-hawa-mahal', NULL, 'Hawa Mahal (Palace of Winds)', 'palace-facade', 26.9239, 75.8267, 'PHOTO_SUPPORTED', 'Upper terraces feature narrow passageways and low parapets; best exterior photography from pedestrian sidewalk opposite in morning light.', '2026-10-15', 'PUBLISHED'),
('in-rj-jaipur-amer-fort', NULL, 'Amer Fort (Amber Palace)', 'hill-fort', 26.9855, 75.8513, 'TRAIL_STOP', 'Hilltop palace complex; ascent on foot, shuttle, or vehicle; cobblestone courtyard ramps can be slippery when wet; sound & light show in evening.', '2026-10-15', 'PUBLISHED'),
('in-up-agra-agra-fort', NULL, 'Agra Fort', 'fortress-palace', 27.1795, 78.0211, 'PHOTO_SUPPORTED', 'Substantial northern sector is active Indian Military cantonment and strictly out of bounds; entry via Amar Singh Gate only.', '2026-10-15', 'PUBLISHED'),
('in-up-agra-fatehpur-sikri', NULL, 'Fatehpur Sikri', 'city-complex', 27.0945, 77.6675, 'PHOTO_SUPPORTED', 'Extensive pedestrian site on sandstone ridge; wear head coverings and remove shoes inside Jama Masjid and Salim Chishti Dargah.', '2026-10-15', 'PUBLISHED'),
('in-delhi-humayuns-tomb', NULL, 'Humayun''s Tomb', 'garden-tomb', 28.5933, 77.2507, 'PHOTO_SUPPORTED', 'Extensive charbagh gardens; walking pathways restored by Aga Khan Trust for Culture (AKTC); photography permitted on plinth.', '2026-10-15', 'PUBLISHED'),
('in-rj-jaipur-city-palace', NULL, 'City Palace Jaipur', 'royal-palace', 26.9258, 75.8236, 'PHOTO_SUPPORTED', 'Private royal trust property; museum ticket covers public courtyards; royal apartment tours (Chandra Mahal) require special royal ticket.', '2026-10-15', 'PUBLISHED');

-- ---------------------------------------------------------------- place_aliases
INSERT INTO place_aliases (alias_id, place_id, language_tag, alias_text, alias_kind) VALUES
('al-taj-en-1', 'in-up-agra-taj-mahal', 'en', 'Taj Mahal Agra', 'alternate'),
('al-taj-hi-1', 'in-up-agra-taj-mahal', 'hi', 'ताज महल', 'canonical-hi'),
('al-taj-hi-rom-1', 'in-up-agra-taj-mahal', 'hi-Latn', 'Taj Mahal', 'romanized'),
('al-taj-ur-1', 'in-up-agra-taj-mahal', 'ur', 'تاج محل', 'local'),

('al-qutub-en-1', 'in-delhi-qutub-minar', 'en', 'Qutb Minar', 'alternate'),
('al-qutub-en-2', 'in-delhi-qutub-minar', 'en', 'Qutab Minar', 'alternate'),
('al-qutub-hi-1', 'in-delhi-qutub-minar', 'hi', 'क़ुतुब मीनार', 'canonical-hi'),
('al-qutub-hi-rom-1', 'in-delhi-qutub-minar', 'hi-Latn', 'Qutub Minar', 'romanized'),

('al-redfort-en-1', 'in-delhi-red-fort', 'en', 'Lal Qila Delhi', 'alternate'),
('al-redfort-hi-1', 'in-delhi-red-fort', 'hi', 'लाल क़िला', 'canonical-hi'),
('al-redfort-hi-rom-1', 'in-delhi-red-fort', 'hi-Latn', 'Lal Qila', 'romanized'),
('al-redfort-ur-1', 'in-delhi-red-fort', 'ur', 'لال قلعہ', 'local'),

('al-hawamahal-en-1', 'in-rj-jaipur-hawa-mahal', 'en', 'Palace of Winds', 'alternate'),
('al-hawamahal-hi-1', 'in-rj-jaipur-hawa-mahal', 'hi', 'हवा महल', 'canonical-hi'),
('al-hawamahal-hi-rom-1', 'in-rj-jaipur-hawa-mahal', 'hi-Latn', 'Hawa Mahal', 'romanized'),

('al-amerfort-en-1', 'in-rj-jaipur-amer-fort', 'en', 'Amber Fort', 'alternate'),
('al-amerfort-en-2', 'in-rj-jaipur-amer-fort', 'en', 'Amber Palace Jaipur', 'alternate'),
('al-amerfort-hi-1', 'in-rj-jaipur-amer-fort', 'hi', 'आमेर का क़िला', 'canonical-hi'),
('al-amerfort-hi-rom-1', 'in-rj-jaipur-amer-fort', 'hi-Latn', 'Amer Kila', 'romanized'),

('al-agrafort-en-1', 'in-up-agra-agra-fort', 'en', 'Agra Red Fort', 'alternate'),
('al-agrafort-hi-1', 'in-up-agra-agra-fort', 'hi', 'आगरा का क़िला', 'canonical-hi'),
('al-agrafort-hi-rom-1', 'in-up-agra-agra-fort', 'hi-Latn', 'Agra Kila', 'romanized'),

('al-fatehpur-en-1', 'in-up-agra-fatehpur-sikri', 'en', 'Fatehpur Sikri Complex', 'alternate'),
('al-fatehpur-hi-1', 'in-up-agra-fatehpur-sikri', 'hi', 'फ़तेहपुर सीकरी', 'canonical-hi'),
('al-fatehpur-hi-rom-1', 'in-up-agra-fatehpur-sikri', 'hi-Latn', 'Fatehpur Sikri', 'romanized'),

('al-humayun-en-1', 'in-delhi-humayuns-tomb', 'en', 'Humayun Tomb Delhi', 'alternate'),
('al-humayun-hi-1', 'in-delhi-humayuns-tomb', 'hi', 'हुमायूँ का मक़बरा', 'canonical-hi'),
('al-humayun-hi-rom-1', 'in-delhi-humayuns-tomb', 'hi-Latn', 'Humayun Ka Maqbara', 'romanized'),

('al-citypalace-en-1', 'in-rj-jaipur-city-palace', 'en', 'Jaipur City Palace', 'alternate'),
('al-citypalace-hi-1', 'in-rj-jaipur-city-palace', 'hi', 'सिटी पैलेस जयपुर', 'canonical-hi'),
('al-citypalace-hi-rom-1', 'in-rj-jaipur-city-palace', 'hi-Latn', 'City Palace Jaipur', 'romanized');

-- ---------------------------------------------------------------- claims
INSERT INTO claims (claim_id, place_id, claim_type, locale, claim_text, era_start, era_end, reviewed_at, reviewer_id, editorial_state) VALUES
-- Taj Mahal
('cl-taj-inscribed', 'in-up-agra-taj-mahal', 'DOCUMENTED', 'en', 'UNESCO inscribed the Taj Mahal as a World Heritage site in 1983 as the jewel of Muslim art in India and a universally admired masterpiece.', '1983CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-taj-builder', 'in-up-agra-taj-mahal', 'DOCUMENTED', 'en', 'Commissioned in 1631 by Mughal Emperor Shah Jahan to house the tomb of his favourite wife, Mumtaz Mahal; the main mausoleum was completed around 1648 CE with ancillary buildings and garden finished by 1653 CE.', '1631CE', '1653CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-taj-charbagh', 'in-up-agra-taj-mahal', 'INTERPRETATION', 'en', 'The architectural layout employs the bilateral symmetry of Timurid charbagh garden design, symbolizing the Garden of Paradise (Jannat) described in the Quranic inscriptions flanking the darwaza.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-taj-black-myth', 'in-up-agra-taj-mahal', 'TRADITION', 'en', 'European traveler Jean-Baptiste Tavernier recorded a popular 17th-century myth that Shah Jahan planned a matching black marble mausoleum on the opposite bank of the Yamuna at Mehtab Bagh; modern archaeological excavations disproved this, revealing a pleasure garden pool reflecting the white Taj.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-taj-tejo-contested', 'in-up-agra-taj-mahal', 'CONTESTED', 'en', 'Revisionist claims asserting the Taj Mahal was originally an ancient Shiva temple (Tejo Mahalaya) have been repeatedly refuted by epigraphic records, contemporary Mughal administrative chronicles (Badshahnama), and sworn affidavits by the Archaeological Survey of India in courts.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-taj-hi-summary', 'in-up-agra-taj-mahal', 'DOCUMENTED', 'hi', 'ताज महल मुगल वास्तुकला का अनुपम उदाहरण है, जिसे शाहजहाँ ने मुमताज महल की स्मृति में 1631 से 1653 के मध्य बनवाया था।', '1631CE', '1653CE', '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Qutub Minar
('cl-qutub-inscribed', 'in-delhi-qutub-minar', 'DOCUMENTED', 'en', 'UNESCO inscribed Qutb Minar and its Monuments as a World Heritage property in 1993, recognizing it as one of the earliest standing monuments of Islamic architecture in northern India.', '1993CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-qutub-construction', 'in-delhi-qutub-minar', 'DOCUMENTED', 'en', 'Started around 1199 CE by Qutb-ud-din Aibak who built the base storey; Shams-ud-din Iltutmish added three storeys, and Firoz Shah Tughlaq restored and rebuilt the upper two storeys in red sandstone and marble in 1368 CE following lightning damage.', '1199CE', '1368CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-qutub-spolia', 'in-delhi-qutub-minar', 'CONTESTED', 'en', 'The Persian dedication inscription on the eastern gate of the adjoining Quwwat-ul-Islam mosque records that stone pillars were acquired from the dismantling of 27 previous temple structures; art historians debate the exact proportion of reused spolia versus newly carved architectural elements.', '1192CE', '1198CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-qutub-iron-pillar', 'in-delhi-qutub-minar', 'DOCUMENTED', 'en', 'The 7.2-metre 4th-century Gupta-era iron pillar in the complex courtyard carries a 6-line Sanskrit Brahmi inscription commemorating King Chandra and demonstrates remarkable metallurgical resistance to atmospheric corrosion.', '0350CE', '0420CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-qutub-hi-summary', 'in-delhi-qutub-minar', 'DOCUMENTED', 'hi', 'क़ुतुब मीनार 72.5 मीटर ऊँची विजय मीनार है, जिसकी नींव 1199 ईस्वी में क़ुतुबुद्दीन ऐबक ने रखी थी। यह यूनेस्को विश्व धरोहर स्थल है।', '1199CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Red Fort
('cl-redfort-inscribed', 'in-delhi-red-fort', 'DOCUMENTED', 'en', 'UNESCO inscribed the Red Fort Complex as a World Heritage site in 2007, recognizing its innovative architectural style that synthesizes Persian, Timurid and Hindu traditions.', '2007CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-redfort-origin', 'in-delhi-red-fort', 'DOCUMENTED', 'en', 'Constructed between 1638 and 1648 CE by Emperor Shah Jahan when he shifted the imperial capital from Agra to Shahjahanabad; supervised by architect Ustad Ahmad Lahori.', '1638CE', '1648CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-redfort-destruction', 'in-delhi-red-fort', 'INTERPRETATION', 'en', 'British military forces demolished approximately 80 percent of the inner pavilions, gardens, and harems following the uprising of 1857 to construct colonial military barracks, severely altering the original ceremonial urban fabric.', '1857CE', '1865CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-redfort-hi-summary', 'in-delhi-red-fort', 'DOCUMENTED', 'hi', 'दिल्ली का लाल क़िला 1638-1648 के दौरान सम्राट शाहजहाँ द्वारा बनवाया गया था और यह भारतीय स्वतंत्रता दिवस के राष्ट्रीय ध्वजारोहण का ऐतिहासिक स्थल है।', '1638CE', '1648CE', '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Hawa Mahal
('cl-hawamahal-built', 'in-rj-jaipur-hawa-mahal', 'DOCUMENTED', 'en', 'Built in 1799 CE by Kachhwaha ruler Maharaja Sawai Pratap Singh and designed by royal architect Lal Chand Ustad as an extension of the City Palace complex.', '1799CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-hawamahal-purpose', 'in-rj-jaipur-hawa-mahal', 'INTERPRETATION', 'en', 'Engineered with 953 jharokha casements and delicate sandstone lattice screens (jali) so royal women observed festive street processions on Badi Choupad without breaking strict purdah seclusion customs, while cooling air via the Venturi airflow effect.', '1799CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-hawamahal-crown', 'in-rj-jaipur-hawa-mahal', 'TRADITION', 'en', 'According to Jaipur court tradition, the five-storey stepped facade was inspired by the crown (mukut) of the Hindu deity Lord Krishna, of whom Maharaja Sawai Pratap Singh was a devoted worshipper.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-hawamahal-hi-summary', 'in-rj-jaipur-hawa-mahal', 'DOCUMENTED', 'hi', 'हवा महल का निर्माण 1799 ईस्वी में महाराजा सवाई प्रताप सिंह ने करवाया था। इसमें 953 नक्काशीदार झरोखे हैं जो वेंटुरी प्रभाव से ठंडी हवा प्रदान करते हैं।', '1799CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Amer Fort
('cl-amer-inscribed', 'in-rj-jaipur-amer-fort', 'DOCUMENTED', 'en', 'Inscribed by UNESCO in 2013 as one of the six Hill Forts of Rajasthan, exemplifying Rajput military hill architecture and indigenous water-harvesting engineering.', '2013CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-amer-builder', 'in-rj-jaipur-amer-fort', 'DOCUMENTED', 'en', 'Begun in 1592 CE by Raja Man Singh I over the ruins of an 11th-century Meena settlement, and expanded across the 17th century by Mirza Raja Jai Singh and Sawai Jai Singh II before moving the capital to Jaipur in 1727 CE.', '1592CE', '1727CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-amer-treasure-myth', 'in-rj-jaipur-amer-fort', 'TRADITION', 'en', 'Popular folklore of an immense hidden Kachhwaha royal treasure in the interconnected Jaigarh and Amer fortresses prompted a five-month government military search operation in 1976 during the Emergency, which yielded no documented treasure hoard.', '1976CE', '1977CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-amer-hi-summary', 'in-rj-jaipur-amer-fort', 'DOCUMENTED', 'hi', 'आमेर दुर्ग का निर्माण 1592 में राजा मानसिंह प्रथम ने शुरू करवाया था। यह यूनेस्को विश्व धरोहर में शामिल राजस्थान के छह पहाड़ी किलों में से एक है।', '1592CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Agra Fort
('cl-agrafort-inscribed', 'in-up-agra-agra-fort', 'DOCUMENTED', 'en', 'UNESCO inscribed Agra Fort as a World Heritage property in 1983 as a premier example of 16th-century Mughal imperial fortified palaces.', '1983CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-agrafort-phases', 'in-up-agra-agra-fort', 'INTERPRETATION', 'en', 'Exhibits two major architectural phases: Akbar''s red sandstone defensive ramparts and trabeate vernacular halls (Jahangiri Mahal, 1565–1573 CE), contrasted with Shah Jahan''s white marble arcaded palatial pavilions (Diwan-i-Khas, Khas Mahal, 1630s).', '1565CE', '1638CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-agrafort-shahjahan-death', 'in-up-agra-agra-fort', 'DOCUMENTED', 'en', 'Emperor Shah Jahan was placed under palace house arrest in Agra Fort by his son Aurangzeb in 1658 CE and lived out his final eight years confined to the Musamman Burj tower overlooking the Taj Mahal until his death in 1666 CE.', '1658CE', '1666CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-agrafort-hi-summary', 'in-up-agra-agra-fort', 'DOCUMENTED', 'hi', 'आगरा का लाल क़िला मुगल साम्राज्य का प्रमुख निवास था। इसे अकबर ने 1565-1573 में बनवाया और शाहजहाँ ने सफेद संगमरमर के महलों से सजाया।', '1565CE', '1573CE', '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Fatehpur Sikri
('cl-fatehpur-inscribed', 'in-up-agra-fatehpur-sikri', 'DOCUMENTED', 'en', 'UNESCO inscribed Fatehpur Sikri as a World Heritage site in 1986, recognizing its architectural urbanism as the zenith of Akbar''s imperial court.', '1986CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-fatehpur-founding', 'in-up-agra-fatehpur-sikri', 'DOCUMENTED', 'en', 'Founded in 1571 CE by Emperor Akbar near the hermitage of Chishti Sufi Shaikh Salim Chishti following the prophesied birth of his heir Prince Salim (Jahangir); served as imperial capital until 1585 CE.', '1571CE', '1585CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-fatehpur-abandonment', 'in-up-agra-fatehpur-sikri', 'INTERPRETATION', 'en', 'While popular accounts attribute the abandonment in 1585 CE solely to sudden drinking-water exhaustion, historical evidence demonstrates Akbar moved the imperial encampment to Lahore to address urgent geopolitical military threats on the northwest frontier.', '1585CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-fatehpur-buland', 'in-up-agra-fatehpur-sikri', 'DOCUMENTED', 'en', 'The Buland Darwaza (54 metres tall) was erected by Akbar around 1575 CE to commemorate his successful military conquest of Gujarat; it features a famous Persian inscription warning against worldly attachment.', '1575CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-fatehpur-hi-summary', 'in-up-agra-fatehpur-sikri', 'DOCUMENTED', 'hi', 'फ़तेहपुर सीकरी की स्थापना 1571 में सम्राट अकबर ने सूफी संत शेख सलीम चिश्ती के सम्मान में की थी। 1585 तक यह मुगल साम्राज्य की राजधानी रही।', '1571CE', '1585CE', '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Humayun's Tomb
('cl-humayun-inscribed', 'in-delhi-humayuns-tomb', 'DOCUMENTED', 'en', 'UNESCO inscribed Humayun''s Tomb in 1993 as the first substantial example of monumental garden-tomb architecture in India, setting the prototype for the Taj Mahal.', '1993CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-humayun-patron', 'in-delhi-humayuns-tomb', 'DOCUMENTED', 'en', 'Commissioned in 1565 CE by Humayun''s chief consort Empress Bega Begum (Haji Begum) and designed by Persian master architect Mirak Mirza Ghiyas; completed in 1572 CE.', '1565CE', '1572CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-humayun-dormitory', 'in-delhi-humayuns-tomb', 'INTERPRETATION', 'en', 'Referred to by historians as the "Dormitory of the House of Timur" because more than 150 members of the Mughal royal lineage, including Dara Shikoh, are buried in unlabelled crypts beneath the grand plinth.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-humayun-1857-capture', 'in-delhi-humayuns-tomb', 'DOCUMENTED', 'en', 'The tomb complex was the refuge of the last Mughal Emperor Bahadur Shah Zafar during the 1857 rebellion before his surrender to British Major William Hodson on 21 September 1857.', '1857CE', '1857CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-humayun-hi-summary', 'in-delhi-humayuns-tomb', 'DOCUMENTED', 'hi', 'हुमायूँ का मक़बरा 1565-1572 में बेगा बेगम द्वारा बनवाया गया पहला भव्य चारबाग उद्यान मक़बरा है, जो ताज महल का अग्रदूत माना जाता है।', '1565CE', '1572CE', '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- City Palace Jaipur
('cl-citypalace-founding', 'in-rj-jaipur-city-palace', 'DOCUMENTED', 'en', 'Founded in 1727 CE by Maharaja Sawai Jai Singh II when planning the new fortified city of Jaipur based on Vastu Shastra and Shilpa Shastra principles under architect Vidyadhar Bhattacharya.', '1727CE', '1732CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-citypalace-fusion', 'in-rj-jaipur-city-palace', 'INTERPRETATION', 'en', 'The palace complex displays an architectural fusion of Mughal courtly geometry, Rajput fortification traditions, and European classical colonnades added in late 19th-century renovations.', '1727CE', '1900CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-citypalace-silver-vessels', 'in-rj-jaipur-city-palace', 'DOCUMENTED', 'en', 'The Diwan-i-Khas houses two colossal sterling silver vessels (Gangajalis) measuring 1.6 metres in height and weighing 345 kg each, certified by Guinness World Records as the largest sterling silver objects in the world; cast by local silversmiths without soldering in 1902 for Maharaja Sawai Madho Singh II to carry Ganges water to England.', '1902CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-citypalace-hi-summary', 'in-rj-jaipur-city-palace', 'DOCUMENTED', 'hi', 'जयपुर का सिटी पैलेस 1727 में महाराजा सवाई जयसिंह द्वितीय द्वारा स्थापित किया गया था। इसमें राजपूत और मुगल वास्तुकला का शानदार समन्वय देखने को मिलता है।', '1727CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED');

-- ---------------------------------------------------------------- claim_sources
INSERT INTO claim_sources (claim_id, source_id, page_or_anchor) VALUES
('cl-taj-inscribed', 'src-unesco-252', 'whc-252-brief-synthesis'),
('cl-taj-builder', 'src-asi-agra-circle', 'taj-mahal-history-chronology'),
('cl-taj-charbagh', 'src-koch-taj', 'koch-taj-ch3-garden-layout'),
('cl-taj-black-myth', 'src-asi-agra-circle', 'mehtab-bagh-excavation-findings'),
('cl-taj-tejo-contested', 'src-asi-agra-circle', 'asi-affidavit-court-declaration'),
('cl-taj-hi-summary', 'src-unesco-252', 'whc-252-brief-synthesis'),

('cl-qutub-inscribed', 'src-unesco-233', 'whc-233-brief-synthesis'),
('cl-qutub-construction', 'src-asi-delhi-circle', 'qutb-minar-storey-chronology'),
('cl-qutub-spolia', 'src-asi-delhi-circle', 'quwwat-ul-islam-epigraphy'),
('cl-qutub-iron-pillar', 'src-asi-delhi-circle', 'iron-pillar-gupta-brahmi'),
('cl-qutub-hi-summary', 'src-unesco-233', 'whc-233-brief-synthesis'),

('cl-redfort-inscribed', 'src-unesco-1054', 'whc-1054-brief-synthesis'),
('cl-redfort-origin', 'src-asi-delhi-circle', 'red-fort-shahjahan-1638'),
('cl-redfort-destruction', 'src-asi-delhi-circle', 'post-1857-military-alterations'),
('cl-redfort-hi-summary', 'src-unesco-1054', 'whc-1054-brief-synthesis'),

('cl-hawamahal-built', 'src-rajasthan-tourism-jaipur', 'hawa-mahal-1799-pratap-singh'),
('cl-hawamahal-purpose', 'src-rajasthan-tourism-jaipur', 'hawa-mahal-jharokha-venturi'),
('cl-hawamahal-crown', 'src-rajasthan-tourism-jaipur', 'hawa-mahal-krishna-crown'),
('cl-hawamahal-hi-summary', 'src-rajasthan-tourism-jaipur', 'hawa-mahal-1799-pratap-singh'),

('cl-amer-inscribed', 'src-unesco-247', 'whc-247-brief-synthesis'),
('cl-amer-builder', 'src-rajasthan-tourism-jaipur', 'amer-fort-man-singh-1592'),
('cl-amer-treasure-myth', 'src-rajasthan-tourism-jaipur', 'jaigarh-amer-vaults-1976'),
('cl-amer-hi-summary', 'src-unesco-247', 'whc-247-brief-synthesis'),

('cl-agrafort-inscribed', 'src-unesco-251', 'whc-251-brief-synthesis'),
('cl-agrafort-phases', 'src-asi-agra-circle', 'agra-fort-akbar-shahjahan-fabric'),
('cl-agrafort-shahjahan-death', 'src-asi-agra-circle', 'musamman-burj-confinement-1666'),
('cl-agrafort-hi-summary', 'src-unesco-251', 'whc-251-brief-synthesis'),

('cl-fatehpur-inscribed', 'src-unesco-255', 'whc-255-brief-synthesis'),
('cl-fatehpur-founding', 'src-asi-agra-circle', 'fatehpur-sikri-salim-chishti-1571'),
('cl-fatehpur-abandonment', 'src-asi-agra-circle', 'lahore-campaign-abandonment-1585'),
('cl-fatehpur-buland', 'src-asi-agra-circle', 'buland-darwaza-gujarat-1575'),
('cl-fatehpur-hi-summary', 'src-unesco-255', 'whc-255-brief-synthesis'),

('cl-humayun-inscribed', 'src-unesco-232', 'whc-232-brief-synthesis'),
('cl-humayun-patron', 'src-asi-delhi-circle', 'humayun-tomb-bega-begum-1565'),
('cl-humayun-dormitory', 'src-asi-delhi-circle', 'dormitory-house-of-timur-crypts'),
('cl-humayun-1857-capture', 'src-asi-delhi-circle', 'bahadur-shah-zafar-hodson-1857'),
('cl-humayun-hi-summary', 'src-unesco-232', 'whc-232-brief-synthesis'),

('cl-citypalace-founding', 'src-rajasthan-tourism-jaipur', 'city-palace-jai-singh-1727'),
('cl-citypalace-fusion', 'src-rajasthan-tourism-jaipur', 'city-palace-architecture-fusion'),
('cl-citypalace-silver-vessels', 'src-rajasthan-tourism-jaipur', 'guinness-gangajali-silver-urns'),
('cl-citypalace-hi-summary', 'src-rajasthan-tourism-jaipur', 'city-palace-jai-singh-1727');

-- ---------------------------------------------------------------- spotter_items
INSERT INTO spotter_items (spotter_id, place_id, feature_title, where_to_look, explanation, claim_type, source_id) VALUES
('sp-taj-pietradura', 'in-up-agra-taj-mahal', 'Pietra Dura Floral Parchin Kari', 'Main entrance archways (pishtaq) and around the cenotaphs', 'Intricate marble inlay using semi-precious carnelian, lapis lazuli, jade, and jasper depicting botanical blooms.', 'DOCUMENTED', 'src-koch-taj'),
('sp-taj-calligraphy', 'in-up-agra-taj-mahal', 'Optical Illusion Quranic Script', 'Great Gate (Darwaza-i-Rauza) and tomb portal frames', 'Calligrapher Abd ul-Haq (Amanat Khan) gradually scaled font heights larger toward the top so letters appear uniform from eye level.', 'DOCUMENTED', 'src-koch-taj'),
('sp-taj-minarets', 'in-up-agra-taj-mahal', 'Outwardly Leaning Minarets', 'The four corner minarets of the marble plinth', 'Engineered to lean slightly outward (c. 3 degrees) so that in the event of an earthquake, they collapse away from the central tomb.', 'DOCUMENTED', 'src-koch-taj'),

('sp-qutub-balconies', 'in-delhi-qutub-minar', 'Corbelled Stalactite Balcony Brackets', 'Underside of projecting balconies on storeys 1 and 2', 'Clusters of intricate mini-alcoves and stalactite corbels transferring balcony loads to the sandstone core.', 'DOCUMENTED', 'src-asi-delhi-circle'),
('sp-qutub-calligraphy-bands', 'in-delhi-qutub-minar', 'Curving Kufic & Naskh Inscription Bands', 'Encircling the fluted shaft of the base storey', 'Intertwining Quranic verses and titles of Sultan Qutb-ud-din Aibak executed in raised red sandstone relief.', 'DOCUMENTED', 'src-asi-delhi-circle'),
('sp-qutub-iron-pillar', 'in-delhi-qutub-minar', 'Gupta Brahmi Iron Inscription', 'Western face of the courtyard Iron Pillar', 'Six lines of metric Sanskrit in early classical Brahmi script praising the conquests of King Chandra (Chandragupta II Vikramaditya).', 'DOCUMENTED', 'src-asi-delhi-circle'),

('sp-redfort-diwan-khas', 'in-delhi-red-fort', 'Paradise Couplet on Diwan-i-Khas', 'North and south arches above corner piers inside Diwan-i-Khas', 'Inscribed Persian verse by Amir Khusrow: "Agar Firdaus bar ruye zamin ast, hamin ast o hamin ast o hamin ast" (If there be paradise on earth, it is here).', 'DOCUMENTED', 'src-asi-delhi-circle'),
('sp-redfort-stream-paradise', 'in-delhi-red-fort', 'Nahr-i-Bihisht Marble Water Channel', 'Center aisle running through Khas Mahal and Diwan-i-Khas', 'Continuous marble channel that circulated cooled water diverted from the Yamuna via the Western Yamuna Canal.', 'DOCUMENTED', 'src-asi-delhi-circle'),

('sp-hawamahal-jharokha', 'in-rj-jaipur-hawa-mahal', 'Latticed Jharokha Overhangs', 'Exterior street facade facing Badi Choupad', 'Miniature carved sandstone casements with pierced stone screens (jali) designed to accelerate breezes into the interior galleries.', 'DOCUMENTED', 'src-rajasthan-tourism-jaipur'),
('sp-hawamahal-glass', 'in-rj-jaipur-hawa-mahal', 'Polychromatic Belgian Glass Casements', 'Upper floor rear viewing chambers', 'Stained Belgian glass inserts that cast kaleidoscope patterns across the marble floors under changing desert sunlight.', 'DOCUMENTED', 'src-rajasthan-tourism-jaipur'),

('sp-amer-sheesh-mahal', 'in-rj-jaipur-amer-fort', 'Convex Mirror Mosaic (Sheesh Mahal)', 'Hall of Mirrors in third courtyard (Diwan-i-Khas)', 'Thousands of imported convex glass foil mirrors embedded in plaster ceiling motifs that reflect a single candle like a starry sky.', 'DOCUMENTED', 'src-rajasthan-tourism-jaipur'),
('sp-amer-magic-flower', 'in-rj-jaipur-amer-fort', 'Seven-in-One Magic Flower Panel', 'Sandstone base panel near Sheesh Mahal pillar', 'Relief carving containing seven hidden motifs (fish tail, lotus bud, cobra, elephant trunk, lion tail, cob of corn, scorpion) revealed by partially concealing sections.', 'DOCUMENTED', 'src-rajasthan-tourism-jaipur'),

('sp-agrafort-musamman-burj', 'in-up-agra-agra-fort', 'Musamman Burj Octagonal Marble Pavilions', 'Eastern riverside bastion overlooking the Yamuna', 'Shah Jahan''s opulent multi-story open marble tower providing an unobstructed sightline to the Taj Mahal 2 km downstream.', 'DOCUMENTED', 'src-asi-agra-circle'),
('sp-agrafort-jahangiri-brackets', 'in-up-agra-agra-fort', 'Serpentine Stone Struts of Jahangiri Mahal', 'Central inner courtyard of Jahangiri Mahal', 'Elaborate carved serpentine brackets and lotus pendants reflecting Gujarati Hindu and Jain timber-building traditions translated into red sandstone.', 'DOCUMENTED', 'src-asi-agra-circle'),

('sp-fatehpur-diwan-khas-pillar', 'in-up-agra-fatehpur-sikri', 'Central Octagonal Pillar with 36 Brackets', 'Center of Diwan-i-Khas hall of private audience', 'Single monolithic stone pillar flaring into 36 serpentine brackets supporting Akbar''s suspended imperial seating platform.', 'DOCUMENTED', 'src-asi-agra-circle'),
('sp-fatehpur-salim-chishti-jali', 'in-up-agra-fatehpur-sikri', 'Mother-of-Pearl Canopy & Pierced Marble Jali', 'Inner sanctum of Sheikh Salim Chishti Tomb', 'Finely perforated white marble lattice screens where pilgrims tie sacred threads; inner canopy covered in iridescent mother-of-pearl veneer.', 'DOCUMENTED', 'src-asi-agra-circle'),

('sp-humayun-double-dome', 'in-delhi-humayuns-tomb', 'Timurid Double Marble Dome Construction', 'Top of central tomb drum', 'White marble exterior shell built 42 metres high over an interior ceiling, establishing proper internal proportions while dominating the skyline.', 'DOCUMENTED', 'src-asi-delhi-circle'),
('sp-humayun-water-chutes', 'in-delhi-humayuns-tomb', 'Chadar Sloping Water Chutes', 'Charbagh garden axial walkways', 'Textured chevron sandstone ramps engineered to break flowing water into glistening, oxygenated ripples along garden rills.', 'DOCUMENTED', 'src-asi-delhi-circle'),

('sp-citypalace-peacock-gate', 'in-rj-jaipur-city-palace', 'Four Seasonal Courtyard Gates (Pritam Niwas)', 'Inner courtyard leading to Chandra Mahal', 'Four vibrant stucco gates representing seasons: Autumn Peacock Gate, Summer Lotus Gate, Winter Rose Gate, and Spring Green Gate.', 'DOCUMENTED', 'src-rajasthan-tourism-jaipur'),
('sp-citypalace-gangajali', 'in-rj-jaipur-city-palace', 'Guinness World Record Gangajali Silver Urns', 'Diwan-i-Khas open courtyard pavilion', 'Twin 345 kg sterling silver urns, hand-beaten without solder from silver coins to carry sacred water on Maharaja Madho Singh II''s voyage.', 'DOCUMENTED', 'src-rajasthan-tourism-jaipur');

-- ---------------------------------------------------------------- operational_notices
INSERT INTO operational_notices (notice_id, place_id, notice_kind, text, authority_source_id, last_verified_at, expires_at) VALUES
('op-taj-friday-closure', 'in-up-agra-taj-mahal', 'weekly-closure', 'Taj Mahal is closed for general tourist visits every Friday; open for afternoon prayer to bona fide worshippers only.', 'src-asi-agra-circle', '2026-10-15', '2027-10-15'),
('op-qutub-staircase', 'in-delhi-qutub-minar', 'safety-restriction', 'Entry into the interior minaret staircase is permanently closed by order of ASI following the 1981 stampede; viewing is exterior ground level only.', 'src-asi-delhi-circle', '2026-10-15', '2027-10-15'),
('op-redfort-security', 'in-delhi-red-fort', 'security-protocol', 'Rigorous baggage security screening at Lahori Gate. Powerbanks, pocketknives, and large backpacks may be restricted; deposit lockers available outside.', 'src-asi-delhi-circle', '2026-10-15', '2027-10-15');

-- ---------------------------------------------------------------- FTS index
INSERT INTO place_search (place_id, display_name, aliases, body)
SELECT
  p.place_id,
  p.canonical_name,
  COALESCE((SELECT GROUP_CONCAT(a.alias_text, ' | ') FROM place_aliases a WHERE a.place_id = p.place_id), ''),
  COALESCE((SELECT GROUP_CONCAT(c.claim_text, ' ') FROM claims c WHERE c.place_id = p.place_id AND c.editorial_state IN ('REVIEWED','PUBLISHED')), '')
FROM places p;
