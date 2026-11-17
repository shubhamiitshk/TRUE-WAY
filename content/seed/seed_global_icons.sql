-- TrueWay Regional Seed: Global Icons Tier-1 Showcase
-- Package ID: global-icons-tier1
-- Version: 2026.10.1
-- Sites: Eiffel Tower, Colosseum, Pyramids of Giza, Angkor Wat, Machu Picchu, Statue of Liberty.
-- Strictly compliant with publication_schema.sql and places_schema.sql.

-- ---------------------------------------------------------------- sources
INSERT INTO sources (source_id, title, author_or_publisher, publication_year, source_url, rights_id, accessed_at, archived_anchor) VALUES
('src-unesco-600', 'Paris, Banks of the Seine (Eiffel Tower) — World Heritage Inscription', 'UNESCO World Heritage Centre', '1991', 'https://whc.unesco.org/en/list/600', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-600-eval'),
('src-unesco-91', 'Historic Centre of Rome (Colosseum) — World Heritage Inscription', 'UNESCO World Heritage Centre', '1980', 'https://whc.unesco.org/en/list/91', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-91-eval'),
('src-unesco-86', 'Memphis and its Necropolis: Pyramid Fields from Giza to Dahshur', 'UNESCO World Heritage Centre', '1979', 'https://whc.unesco.org/en/list/86', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-86-eval'),
('src-unesco-668', 'Angkor (Angkor Wat) — World Heritage Inscription & State of Conservation', 'UNESCO World Heritage Centre', '1992', 'https://whc.unesco.org/en/list/668', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-668-eval'),
('src-unesco-274', 'Historic Sanctuary of Machu Picchu — World Heritage Inscription', 'UNESCO World Heritage Centre', '1983', 'https://whc.unesco.org/en/list/274', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-274-eval'),
('src-unesco-307', 'Statue of Liberty — World Heritage Inscription & Advisory Evaluation', 'UNESCO World Heritage Centre', '1984', 'https://whc.unesco.org/en/list/307', 'rights-unesco-text-fairuse', '2026-10-15', 'whc-307-eval'),
('src-sete-eiffel', 'Tour Eiffel: Histoire, Architecture et Chiffres Clés', 'Société d''Exploitation de la Tour Eiffel (SETE)', '2023', 'https://www.toureiffel.paris/fr/le-monument/histoire', 'rights-sete-official', '2026-10-15', 'sete-history-stats'),
('src-parco-colosseo', 'Il Colosseo: Guida Archeologica e Storica', 'Parco Archeologico del Colosseo, Ministero della Cultura', '2022', 'https://colosseo.it/area/colosseo/', 'rights-parco-official', '2026-10-15', 'parco-colosseo-guide'),
('src-egypt-moa', 'Giza Plateau Archaeological Survey and Conservation Reports', 'Egyptian Ministry of Tourism and Antiquities', '2020', 'https://egymonuments.gov.eg/archaeological-sites/giza-plateau/', 'rights-egypt-gov', '2026-10-15', 'moa-giza-survey'),
('src-apsara-angkor', 'Angkor Wat Architectural Documentation and Epigraphy', 'APSARA National Authority of Cambodia', '2021', 'https://apsaraauthority.gov.kh/', 'rights-apsara-official', '2026-10-15', 'apsara-angkor-doc'),
('src-sernanp-peru', 'Santuario Histórico de Machu Picchu — Plan Maestro', 'SERNANP / Ministerio de Cultura del Perú', '2019', 'https://www.gob.pe/sernanp', 'rights-peru-gov', '2026-10-15', 'sernanp-machupicchu'),
('src-nps-liberty', 'Statue of Liberty National Monument: History & Culture', 'US National Park Service', '2022', 'https://www.nps.gov/stli/learn/historyculture/index.htm', 'rights-us-nps-public-domain', '2026-10-15', 'nps-stli-history');

-- ---------------------------------------------------------------- places
INSERT INTO places (place_id, parent_place_id, canonical_name, category, latitude, longitude, visitor_mode, visitor_notice, last_reviewed_at, editorial_state) VALUES
('fr-paris-eiffel-tower', NULL, 'Eiffel Tower (Tour Eiffel)', 'monumental-tower', 48.8584, 2.2945, 'PHOTO_SUPPORTED', 'Security perimeter around the Champ de Mars base; pre-booked elevator or staircase summit tickets recommended; tripod permits enforced by SETE.', '2026-10-15', 'PUBLISHED'),
('it-rome-colosseum', NULL, 'Colosseum (Flavian Amphitheatre)', 'ancient-amphitheatre', 41.8902, 12.4922, 'PHOTO_SUPPORTED', 'Timed entry tickets strictly mandatory; security screening at outer perimeter; arena floor and underground hypogeum access requires special tour reservation.', '2026-10-15', 'PUBLISHED'),
('eg-giza-pyramids', NULL, 'Pyramids of Giza', 'pyramid-complex', 29.9792, 31.1342, 'PHOTO_SUPPORTED', 'Plateau entrance ticket grants exterior access; internal chambers of Khufu and Khafre require separate tickets; avoid unauthorized touts; extreme desert heat midday.', '2026-10-15', 'PUBLISHED'),
('kh-siemreap-angkor-wat', NULL, 'Angkor Wat', 'temple-complex', 13.4125, 103.8670, 'PHOTO_SUPPORTED', 'Angkor Pass required; dress code strictly enforced (covered shoulders and knees required for Bakan upper level); sunrise viewing at northern reflection pond.', '2026-10-15', 'PUBLISHED'),
('pe-cusco-machu-picchu', NULL, 'Machu Picchu', 'archaeological-citadel', -13.1631, -72.5450, 'TRAIL_STOP', 'High-altitude archaeological sanctuary (2,430m); designated one-way visitor circuits strictly enforced; licensed local guide required; plastic bottles prohibited.', '2026-10-15', 'PUBLISHED'),
('us-nyc-statue-of-liberty', NULL, 'Statue of Liberty', 'colossal-monument', 40.6892, -74.0445, 'PHOTO_SUPPORTED', 'National Park Service ferry access from Battery Park (NYC) or Liberty State Park (NJ); separate advance reservations required for Pedestal and Crown access.', '2026-10-15', 'PUBLISHED');

-- ---------------------------------------------------------------- place_aliases
INSERT INTO place_aliases (alias_id, place_id, language_tag, alias_text, alias_kind) VALUES
('al-eiffel-fr-1', 'fr-paris-eiffel-tower', 'fr', 'Tour Eiffel', 'canonical-fr'),
('al-eiffel-en-1', 'fr-paris-eiffel-tower', 'en', 'Eiffel Tower Paris', 'alternate'),
('al-eiffel-es-1', 'fr-paris-eiffel-tower', 'es', 'Torre Eiffel', 'alternate'),
('al-eiffel-hi-1', 'fr-paris-eiffel-tower', 'hi', 'एफिल टॉवर', 'canonical-hi'),
('al-eiffel-hi-rom-1', 'fr-paris-eiffel-tower', 'hi-Latn', 'Eiffel Tower', 'romanized'),

('al-colo-it-1', 'it-rome-colosseum', 'it', 'Colosseo', 'canonical-it'),
('al-colo-it-2', 'it-rome-colosseum', 'it', 'Anfiteatro Flavio', 'alternate'),
('al-colo-en-1', 'it-rome-colosseum', 'en', 'Flavian Amphitheatre', 'alternate'),
('al-colo-es-1', 'it-rome-colosseum', 'es', 'Coliseo Romano', 'alternate'),
('al-colo-hi-1', 'it-rome-colosseum', 'hi', 'कोलोसियम', 'canonical-hi'),
('al-colo-hi-rom-1', 'it-rome-colosseum', 'hi-Latn', 'Colosseum', 'romanized'),

('al-giza-ar-1', 'eg-giza-pyramids', 'ar', 'أهرامات الجيزة', 'canonical-ar'),
('al-giza-en-1', 'eg-giza-pyramids', 'en', 'Great Pyramids of Giza', 'alternate'),
('al-giza-fr-1', 'eg-giza-pyramids', 'fr', 'Pyramides de Gizeh', 'alternate'),
('al-giza-es-1', 'eg-giza-pyramids', 'es', 'Pirámides de Guiza', 'alternate'),
('al-giza-hi-1', 'eg-giza-pyramids', 'hi', 'गीज़ा के पिरामिड', 'canonical-hi'),
('al-giza-hi-rom-1', 'eg-giza-pyramids', 'hi-Latn', 'Giza Ke Pyramid', 'romanized'),

('al-angkor-km-1', 'kh-siemreap-angkor-wat', 'km', 'ប្រាសាទអង្គរវត្ត', 'canonical-km'),
('al-angkor-en-1', 'kh-siemreap-angkor-wat', 'en', 'Angkor Wat Temple', 'alternate'),
('al-angkor-fr-1', 'kh-siemreap-angkor-wat', 'fr', 'Angkor Vat', 'alternate'),
('al-angkor-es-1', 'kh-siemreap-angkor-wat', 'es', 'Angkor Wat', 'alternate'),
('al-angkor-hi-1', 'kh-siemreap-angkor-wat', 'hi', 'अंकोरवाट मंदिर', 'canonical-hi'),
('al-angkor-hi-rom-1', 'kh-siemreap-angkor-wat', 'hi-Latn', 'Angkor Wat Mandir', 'romanized'),

('al-machu-es-1', 'pe-cusco-machu-picchu', 'es', 'Machu Picchu Ciudadela Inca', 'canonical-es'),
('al-machu-qu-1', 'pe-cusco-machu-picchu', 'qu', 'Machu Pikchu', 'canonical-qu'),
('al-machu-en-1', 'pe-cusco-machu-picchu', 'en', 'Machu Picchu Lost City of the Incas', 'alternate'),
('al-machu-fr-1', 'pe-cusco-machu-picchu', 'fr', 'Machu Picchu', 'alternate'),
('al-machu-hi-1', 'pe-cusco-machu-picchu', 'hi', 'माचू पिच्चू', 'canonical-hi'),
('al-machu-hi-rom-1', 'pe-cusco-machu-picchu', 'hi-Latn', 'Machu Picchu', 'romanized'),

('al-liberty-en-1', 'us-nyc-statue-of-liberty', 'en', 'Liberty Enlightening the World', 'official'),
('al-liberty-en-2', 'us-nyc-statue-of-liberty', 'en', 'Lady Liberty', 'colloquial'),
('al-liberty-fr-1', 'us-nyc-statue-of-liberty', 'fr', 'La Liberté éclairant le monde', 'canonical-fr'),
('al-liberty-es-1', 'us-nyc-statue-of-liberty', 'es', 'Estatua de la Libertad', 'alternate'),
('al-liberty-hi-1', 'us-nyc-statue-of-liberty', 'hi', 'स्टैच्यू ऑफ लिबर्टी', 'canonical-hi'),
('al-liberty-hi-rom-1', 'us-nyc-statue-of-liberty', 'hi-Latn', 'Statue of Liberty', 'romanized');

-- ---------------------------------------------------------------- claims
INSERT INTO claims (claim_id, place_id, claim_type, locale, claim_text, era_start, era_end, reviewed_at, reviewer_id, editorial_state) VALUES
-- Eiffel Tower
('cl-eiffel-inscribed', 'fr-paris-eiffel-tower', 'DOCUMENTED', 'en', 'Inscribed by UNESCO in 1991 as part of the Paris, Banks of the Seine World Heritage site, celebrating 19th-century civil engineering and architectural heritage.', '1991CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-eiffel-construction', 'fr-paris-eiffel-tower', 'DOCUMENTED', 'en', 'Constructed between 1887 and 1889 as the grand entrance arch for the 1889 Exposition Universelle; engineered by Gustave Eiffel with engineers Maurice Koechlin and Émile Nouguier and architect Stephen Sauvestre.', '1887CE', '1889CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-eiffel-material', 'fr-paris-eiffel-tower', 'DOCUMENTED', 'en', 'Built entirely from 7,300 tonnes of puddle iron fastened by 2.5 million thermal rivets; total height with broadcast antennas is 330 metres; remained the world''s tallest man-made structure until the completion of New York''s Chrysler Building in 1930.', '1889CE', '1930CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-eiffel-maupassant', 'fr-paris-eiffel-tower', 'TRADITION', 'en', 'A famous literary anecdote recounts that French author Guy de Maupassant regularly dined at the Eiffel Tower''s restaurant because it was the only vantage point in Paris from which the tower itself was not visible.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-eiffel-demolition-dispute', 'fr-paris-eiffel-tower', 'INTERPRETATION', 'en', 'Originally commissioned with a temporary permit of 20 years and slated for dismantling in 1909; saved permanently by Eiffel''s strategic repurposing of the tower as a vital military radio telegraphy antenna during the First World War.', '1903CE', '1914CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-eiffel-fr-desc', 'fr-paris-eiffel-tower', 'DOCUMENTED', 'fr', 'La tour Eiffel est une tour de fer puddlé de 330 mètres de hauteur conçue par Gustave Eiffel pour l''Exposition universelle de 1889 à Paris.', '1889CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),
('cl-eiffel-es-desc', 'fr-paris-eiffel-tower', 'DOCUMENTED', 'es', 'La Torre Eiffel es una estructura de hierro pudelado de 330 metros diseñada por Gustave Eiffel para la Exposición Universal de 1889 en París.', '1889CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),
('cl-eiffel-hi-desc', 'fr-paris-eiffel-tower', 'DOCUMENTED', 'hi', 'एफिल टॉवर पेरिस में स्थित 330 मीटर ऊँचा लोहे का विश्व प्रसिद्ध स्मारक है, जिसे गुस्ताव एफिल ने 1889 के विश्व मेले के लिए बनवाया था।', '1889CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Colosseum
('cl-colo-inscribed', 'it-rome-colosseum', 'DOCUMENTED', 'en', 'UNESCO inscribed the Historic Centre of Rome, including the Colosseum, in 1980 as an outstanding universal monument of ancient Roman civilization.', '1980CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-colo-flavian-origin', 'it-rome-colosseum', 'DOCUMENTED', 'en', 'Commissioned around 70–72 CE under Emperor Vespasian on the drained artificial lake bed of Nero''s Golden House (Domus Aurea); inaugurated in 80 CE by Emperor Titus with 100 days of gladiatorial and venationes games.', '0070CE', '0080CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-colo-architecture', 'it-rome-colosseum', 'INTERPRETATION', 'en', 'Accommodated an estimated 50,000 to 80,000 spectators stratified by social rank; the exterior travertine facade showcases superimposed classical orders: Tuscan/Doric ground arcades, Ionic second level, and Corinthian third level.', '0080CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-colo-naumachiae', 'it-rome-colosseum', 'CONTESTED', 'en', 'Ancient historians Dio Cassius and Suetonius record mock naval sea battles (naumachiae) held in the flooded amphitheatre; modern architectural engineers dispute whether the hydraulic infrastructure permitted rapid flooding before the permanent subterranean hypogeum was installed under Domitian.', '0080CE', '0096CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-colo-martyrs', 'it-rome-colosseum', 'TRADITION', 'en', 'While Christian tradition since the 16th century revere the Colosseum as the primary site of early Christian martyrdom (leading Pope Benedict XIV to erect the Stations of the Cross in 1749), contemporary Roman judicial records confirm executions across multiple venues (Circus Maximus, Circus of Nero) with limited specific documentation for the Colosseum itself.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-colo-es-desc', 'it-rome-colosseum', 'DOCUMENTED', 'es', 'El Coliseo o Anfiteatro Flavio es un gran anfiteatro de la época del Imperio romano construido en el siglo I d. C. en el centro de Roma.', '0080CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),
('cl-colo-hi-desc', 'it-rome-colosseum', 'DOCUMENTED', 'hi', 'कोलोसियम इटली के रोम शहर में स्थित प्राचीन रोमन साम्राज्य का सबसे बड़ा अखाड़ा (एम्फीथिएटर) है, जिसका निर्माण 70-80 ईस्वी में हुआ था।', '0070CE', '0080CE', '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Pyramids of Giza
('cl-giza-inscribed', 'eg-giza-pyramids', 'DOCUMENTED', 'en', 'UNESCO inscribed Memphis and its Necropolis — the Pyramid Fields from Giza to Dahshur in 1979 as the defining funerary landscape of Old Kingdom ancient Egypt.', '1979CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-giza-khufu', 'eg-giza-pyramids', 'DOCUMENTED', 'en', 'The Great Pyramid was erected around 2580–2560 BCE as the tomb for Fourth Dynasty Pharaoh Khufu; constructed of approximately 2.3 million limestone and granite blocks weighing an average of 2.5 tonnes each; original height was 146.6 metres.', '2580BCE', '2560BCE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-giza-workers-consensus', 'eg-giza-pyramids', 'DOCUMENTED', 'en', 'Excavations by Mark Lehner and Zahi Hawass of the Lost City of the Pyramid Builders uncovered permanent barracks, animal bone rations, and bakeries, proving the pyramids were built by organized, salaried Egyptian seasonal workers rather than enslaved captives as claimed by Greek historian Herodotus.', '2560BCE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-giza-alignment', 'eg-giza-pyramids', 'INTERPRETATION', 'en', 'The cardinal alignment of Khufu''s pyramid exhibits an astonishing precision error of less than one-tenth of a degree off true north, accomplished via astronomical observation of circumpolar stars (the "indestructible ones").', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-giza-pseudohistory', 'eg-giza-pyramids', 'CONTESTED', 'en', 'Popular pseudohistorical assertions claiming extraterrestrial intervention, lost super-civilizations (Atlantis), or pyramid energy vortexes are decisively rejected by stratigraphic archaeological continuity, tool mark evidence, and the Diary of Merer papyrus describing limestone barge logistics.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-giza-es-desc', 'eg-giza-pyramids', 'DOCUMENTED', 'es', 'Las Pirámides de Guiza en Egipto fueron construidas durante la IV dinastía del Imperio Antiguo (c. 2580-2500 a. C.) como monumentos funerarios para los faraones.', '2580BCE', '2500BCE', '2026-10-15', 'language-specialist-01', 'PUBLISHED'),
('cl-giza-hi-desc', 'eg-giza-pyramids', 'DOCUMENTED', 'hi', 'गीज़ा के पिरामिड प्राचीन मिस्र के चौथे राजवंश के फिरौन (खूफू, खाफरे, मेनकौरे) के भव्य मक़बरे हैं, जो लगभग 2580 ईसा पूर्व में निर्मित हुए थे।', '2580BCE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Angkor Wat
('cl-angkor-inscribed', 'kh-siemreap-angkor-wat', 'DOCUMENTED', 'en', 'Inscribed by UNESCO in 1992 as part of the Angkor World Heritage site, acknowledged as one of the most remarkable architectural and artistic complexes in Southeast Asia.', '1992CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-angkor-suryavarman', 'kh-siemreap-angkor-wat', 'DOCUMENTED', 'en', 'Commissioned in the first half of the 12th century (c. 1113–1150 CE) by Khmer King Suryavarman II as his state temple and eventual funerary shrine; dedicated to the Hindu preserver deity Vishnu.', '1113CE', '1150CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-angkor-cosmology', 'kh-siemreap-angkor-wat', 'INTERPRETATION', 'en', 'Designed as a physical stone mandala of the Hindu cosmic order: the five central lotus-bud towers symbolize Mount Meru, home of the devas; the concentric rectangular enclosures represent surrounding mountain ranges, and the 190-metre-wide moat represents the cosmic ocean.', '1113CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-angkor-orientation', 'kh-siemreap-angkor-wat', 'CONTESTED', 'en', 'Unlike almost all classical Khmer Hindu temples which orient toward the rising sun in the east, Angkor Wat faces west; scholars debate whether this unique westward orientation signifies a funerary association with Yama or homage to Vishnu whose directional domain includes the west.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-angkor-pisnokar-myth', 'kh-siemreap-angkor-wat', 'TRADITION', 'en', 'Khmer oral folklore recounts that Angkor Wat was not constructed by mortal masons but was miraculously raised in a single night by Preah Pisnokar, the divine architect son of Indra.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-angkor-fr-desc', 'kh-siemreap-angkor-wat', 'DOCUMENTED', 'fr', 'Angkor Vat est le plus grand des temples du complexe monumental d''Angkor au Cambodge, fondé au XIIe siècle par le roi Suryavarman II.', '1113CE', '1150CE', '2026-10-15', 'language-specialist-01', 'PUBLISHED'),
('cl-angkor-hi-desc', 'kh-siemreap-angkor-wat', 'DOCUMENTED', 'hi', 'अंकोरवाट कंबोडिया में स्थित दुनिया का सबसे बड़ा धार्मिक स्मारक है, जिसे 12वीं शताब्दी में राजा सूर्यवर्मन द्वितीय ने भगवान विष्णु को समर्पित किया था।', '1113CE', '1150CE', '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Machu Picchu
('cl-machu-inscribed', 'pe-cusco-machu-picchu', 'DOCUMENTED', 'en', 'UNESCO inscribed the Historic Sanctuary of Machu Picchu in 1983 as a mixed cultural and natural World Heritage property, celebrating its supreme integration of architecture and Andean landscape.', '1983CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-machu-pachacuti', 'pe-cusco-machu-picchu', 'DOCUMENTED', 'en', 'Constructed around 1450 CE under the reign of the ninth Inca Emperor Pachacuti Yupanqui as an elite royal estate and ritual retreat; abandoned around 1572 CE following the Spanish collapse of the Inca Empire.', '1450CE', '1572CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-machu-bingham-myth', 'pe-cusco-machu-picchu', 'CONTESTED', 'en', 'Bingham mistakenly popularized the site in 1911 as the "Lost City of the Incas" and Vilcabamba; archaeological consensus confirms local indigenous farmers (including Melchor Arteaga) were aware of and cultivating the ruins before Bingham''s visit.', '1911CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-machu-ashlar', 'pe-cusco-machu-picchu', 'INTERPRETATION', 'en', 'Exhibits classical Inca dry-stone ashlar masonry without mortar; granite blocks were chiseled with bronze and stone tools and fitted so tightly that a knife blade cannot penetrate joints; engineered with seismic tilt and drainage terraces to withstand earthquakes and tropical downpours.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-machu-es-desc', 'pe-cusco-machu-picchu', 'DOCUMENTED', 'es', 'Machu Picchu es una antigua ciudadela inca del siglo XV situada en los Andes peruanos, construida durante el reinado del emperador Pachacútec.', '1450CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),
('cl-machu-hi-desc', 'pe-cusco-machu-picchu', 'DOCUMENTED', 'hi', 'माचू पिच्चू पेरू के एंडीज पर्वतों में स्थित 15वीं शताब्दी का प्रसिद्ध इंका साम्राज्य का दुर्ग-नगर है, जिसे 1450 ईस्वी में सम्राट पचाकुती ने बनवाया था।', '1450CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),

-- Statue of Liberty
('cl-liberty-inscribed', 'us-nyc-statue-of-liberty', 'DOCUMENTED', 'en', 'UNESCO inscribed the Statue of Liberty in 1984 as a masterpiece of the human creative spirit and a colossal symbol of liberty, peace and democracy.', '1984CE', NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-liberty-gift', 'us-nyc-statue-of-liberty', 'DOCUMENTED', 'en', 'Gifted by the people of France to the United States to celebrate the centennial of the Declaration of Independence; designed by French sculptor Frédéric-Auguste Bartholdi with internal structural iron pylon engineered by Gustave Eiffel; dedicated October 28, 1886.', '1875CE', '1886CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-liberty-abolition', 'us-nyc-statue-of-liberty', 'INTERPRETATION', 'en', 'Conceived in 1865 by French abolitionist Édouard René de Laboulaye primarily to commemorate the abolition of slavery following the Union victory in the American Civil War; this original intent is materialized by the broken shackle and severed chain at Liberty''s feet.', '1865CE', '1886CE', '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-liberty-mother-model', 'us-nyc-statue-of-liberty', 'TRADITION', 'en', 'A persistent popular tradition holds that Bartholdi modeled the neoclassical facial features of Libertas on his own mother, Charlotte Beysser Bartholdi, although scholars note stylistic synthesis with classic Roman sculpture.', NULL, NULL, '2026-10-15', 'heritage-editor-01', 'PUBLISHED'),
('cl-liberty-fr-desc', 'us-nyc-statue-of-liberty', 'DOCUMENTED', 'fr', 'La Liberté éclairant le monde, dite statue de la Liberté, est une sculpture monumentale offerte par la France aux États-Unis, conçue par Bartholdi et Eiffel.', '1886CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),
('cl-liberty-es-desc', 'us-nyc-statue-of-liberty', 'DOCUMENTED', 'es', 'La Estatua de la Libertad es un monumento colosal en Nueva York, regalo del pueblo de Francia a los Estados Unidos en 1886.', '1886CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED'),
('cl-liberty-hi-desc', 'us-nyc-statue-of-liberty', 'DOCUMENTED', 'hi', 'स्टैच्यू ऑफ लिबर्टी न्यूयॉर्क हार्बर में स्थित तांबे की विशाल मूर्ति है, जिसे फ्रांस की जनता ने 1886 में अमेरिका को स्वतंत्रता के प्रतीक के रूप में भेंट किया था।', '1886CE', NULL, '2026-10-15', 'language-specialist-01', 'PUBLISHED');

-- ---------------------------------------------------------------- claim_sources
INSERT INTO claim_sources (claim_id, source_id, page_or_anchor) VALUES
('cl-eiffel-inscribed', 'src-unesco-600', 'whc-600-brief-synthesis'),
('cl-eiffel-construction', 'src-sete-eiffel', 'sete-construction-1889'),
('cl-eiffel-material', 'src-sete-eiffel', 'sete-puddle-iron-metrics'),
('cl-eiffel-maupassant', 'src-sete-eiffel', 'sete-cultural-anecdotes'),
('cl-eiffel-demolition-dispute', 'src-sete-eiffel', 'sete-military-radio-1909'),
('cl-eiffel-fr-desc', 'src-sete-eiffel', 'sete-construction-1889'),
('cl-eiffel-es-desc', 'src-sete-eiffel', 'sete-construction-1889'),
('cl-eiffel-hi-desc', 'src-unesco-600', 'whc-600-brief-synthesis'),

('cl-colo-inscribed', 'src-unesco-91', 'whc-91-brief-synthesis'),
('cl-colo-flavian-origin', 'src-parco-colosseo', 'parco-vespasian-titus-dedication'),
('cl-colo-architecture', 'src-parco-colosseo', 'parco-classical-orders-tiers'),
('cl-colo-naumachiae', 'src-parco-colosseo', 'parco-naumachiae-hydraulic-study'),
('cl-colo-martyrs', 'src-parco-colosseo', 'parco-christian-martyrdom-tradition'),
('cl-colo-es-desc', 'src-parco-colosseo', 'parco-vespasian-titus-dedication'),
('cl-colo-hi-desc', 'src-unesco-91', 'whc-91-brief-synthesis'),

('cl-giza-inscribed', 'src-unesco-86', 'whc-86-brief-synthesis'),
('cl-giza-khufu', 'src-egypt-moa', 'moa-khufu-tomb-metrics'),
('cl-giza-workers-consensus', 'src-egypt-moa', 'moa-lehner-workers-barracks'),
('cl-giza-alignment', 'src-egypt-moa', 'moa-astronomical-alignment'),
('cl-giza-pseudohistory', 'src-egypt-moa', 'moa-merer-papyrus-evidence'),
('cl-giza-es-desc', 'src-egypt-moa', 'moa-khufu-tomb-metrics'),
('cl-giza-hi-desc', 'src-unesco-86', 'whc-86-brief-synthesis'),

('cl-angkor-inscribed', 'src-unesco-668', 'whc-668-brief-synthesis'),
('cl-angkor-suryavarman', 'src-apsara-angkor', 'apsara-suryavarman-chronology'),
('cl-angkor-cosmology', 'src-apsara-angkor', 'apsara-mount-meru-mandala'),
('cl-angkor-orientation', 'src-apsara-angkor', 'apsara-west-facing-debates'),
('cl-angkor-pisnokar-myth', 'src-apsara-angkor', 'apsara-khmer-folklore-pisnokar'),
('cl-angkor-fr-desc', 'src-apsara-angkor', 'apsara-suryavarman-chronology'),
('cl-angkor-hi-desc', 'src-unesco-668', 'whc-668-brief-synthesis'),

('cl-machu-inscribed', 'src-unesco-274', 'whc-274-brief-synthesis'),
('cl-machu-pachacuti', 'src-sernanp-peru', 'sernanp-pachacuti-estate-1450'),
('cl-machu-bingham-myth', 'src-sernanp-peru', 'sernanp-indigenous-farmers-pre-bingham'),
('cl-machu-ashlar', 'src-sernanp-peru', 'sernanp-seismic-ashlar-masonry'),
('cl-machu-es-desc', 'src-sernanp-peru', 'sernanp-pachacuti-estate-1450'),
('cl-machu-hi-desc', 'src-unesco-274', 'whc-274-brief-synthesis'),

('cl-liberty-inscribed', 'src-unesco-307', 'whc-307-brief-synthesis'),
('cl-liberty-gift', 'src-nps-liberty', 'nps-bartholdi-eiffel-dedication'),
('cl-liberty-abolition', 'src-nps-liberty', 'nps-laboulaye-civil-war-emancipation'),
('cl-liberty-mother-model', 'src-nps-liberty', 'nps-bartholdi-mother-portrait'),
('cl-liberty-fr-desc', 'src-nps-liberty', 'nps-bartholdi-eiffel-dedication'),
('cl-liberty-es-desc', 'src-nps-liberty', 'nps-bartholdi-eiffel-dedication'),
('cl-liberty-hi-desc', 'src-unesco-307', 'whc-307-brief-synthesis');

-- ---------------------------------------------------------------- spotter_items
INSERT INTO spotter_items (spotter_id, place_id, feature_title, where_to_look, explanation, claim_type, source_id) VALUES
('sp-eiffel-72-names', 'fr-paris-eiffel-tower', '72 Inscribed French Scientists', 'Perimeter frieze beneath the first platform', 'Gold letters 60 cm high honoring 72 French mathematicians, physicists, and engineers (e.g., Fourier, Laplace, Ampère) engraved by Gustave Eiffel.', 'DOCUMENTED', 'src-sete-eiffel'),
('sp-eiffel-puddle-rivets', 'fr-paris-eiffel-tower', 'Thermal Puddle-Iron Rivets', 'Corner pillar trusses and diagonal cross-bracing', 'Pattern of 2.5 million hand-driven hot rivets locking the puddle-iron latticework with minimal wind drag.', 'DOCUMENTED', 'src-sete-eiffel'),
('sp-eiffel-gustave-apartment', 'fr-paris-eiffel-tower', 'Gustave Eiffel''s Summit Laboratory', 'Third level glassed pavilion at the summit', 'Preserved private apartment and meteorological lab where Eiffel entertained Thomas Edison in 1889.', 'DOCUMENTED', 'src-sete-eiffel'),

('sp-colo-hypogeum', 'it-rome-colosseum', 'Subterranean Hypogeum Maze', 'Sunken central floor beneath the wooden arena', 'Two-level underground labyrinth of masonry chambers, holding cages for wild beasts, and counterweight elevator shafts (pegmata).', 'DOCUMENTED', 'src-parco-colosseo'),
('sp-colo-velarium-brackets', 'it-rome-colosseum', 'Velarium Awning Mast Corbel Stones', 'Outer upper attic cornice stone ring', 'Travertine corbel stones with holes carved to seat 240 wooden masts that suspended the giant Roman naval canvas shade.', 'DOCUMENTED', 'src-parco-colosseo'),
('sp-colo-three-orders', 'it-rome-colosseum', 'Superimposed Classical Greek-Roman Orders', 'Exterior facade three-tier arcades', 'Ground arches framed with Tuscan half-columns, middle arches with Ionic columns, top arches with ornate Corinthian capitals.', 'DOCUMENTED', 'src-parco-colosseo'),

('sp-giza-casing-apex', 'eg-giza-pyramids', 'Polished Tura Casing Stones at Apex', 'Top 45 metres of the Pyramid of Khafre', 'The sole remaining section of original smooth, fine-grained white Tura limestone casing that originally enveloped all three pyramids.', 'DOCUMENTED', 'src-egypt-moa'),
('sp-giza-boat-pit', 'eg-giza-pyramids', 'Solar Khufu Cedar Bark Pit', 'Southern base of the Great Pyramid of Khufu', 'Rock-cut trench where the disassembled 43-metre cedar funeral boat of Khufu was excavated and reconstructed.', 'DOCUMENTED', 'src-egypt-moa'),
('sp-giza-sphinx-dream-stele', 'eg-giza-pyramids', 'Thutmose IV Dream Stele', 'Between the front paws of the Great Sphinx', 'Red granite slab recording the prophetic dream of Prince Thutmose IV promising him the crown of Egypt if he cleared the encroaching desert sand.', 'DOCUMENTED', 'src-egypt-moa'),

('sp-angkor-churning-milk', 'kh-siemreap-angkor-wat', 'Churning of the Ocean of Milk (Samudra Manthan)', 'East gallery third enclosure wall bas-relief', '49-metre continuous sandstone carving depicting 88 asuras and 92 devas using the serpent Vasuki to churn the celestial ocean for the elixir of immortality.', 'DOCUMENTED', 'src-apsara-angkor'),
('sp-angkor-apsaras', 'kh-siemreap-angkor-wat', 'Devata & Apsara High-Relief Carvings', 'Outer gallery walls, pillars and porticos', 'Over 1,790 individually carved celestial dancers displaying distinct hairstyles, ornate jewelry, and floral waist wraps.', 'DOCUMENTED', 'src-apsara-angkor'),
('sp-angkor-reflection-towers', 'kh-siemreap-angkor-wat', 'Quincunx Lotus-Bud Towers Reflection', 'Northern outer courtyard lotus pond', 'Iconic visual axis reflecting the five pine-cone shaped central prasat towers mirroring the sacred peaks of Mount Meru.', 'DOCUMENTED', 'src-apsara-angkor'),

('sp-machu-intihuatana', 'pe-cusco-machu-picchu', 'Intihuatana Astronomical Hitching Post', 'Highest terrace of the Sacred District', 'Monolithic granite bedrock outcrop carved into a precise solar clock and solstice calendar that casts no shadow at solar noon during equinoxes.', 'DOCUMENTED', 'src-sernanp-peru'),
('sp-machu-three-windows', 'pe-cusco-machu-picchu', 'Temple of the Three Windows', 'Eastern face of the Sacred Plaza', 'Massive trapezoidal cyclopean granite wall framing views over the Andes; symbolizes the three mythical caves of the Ayar brothers in Inca origin mythology.', 'DOCUMENTED', 'src-sernanp-peru'),
('sp-machu-drainage-terraces', 'pe-cusco-machu-picchu', 'Engineered Agricultural Terracing & Drainage', 'Southern agricultural sector flanking Urubamba slopes', 'Multi-layered gravel and topsoil retaining walls that prevented slope erosion and channelled mountain runoff during tropical rains.', 'DOCUMENTED', 'src-sernanp-peru'),

('sp-liberty-broken-shackle', 'us-nyc-statue-of-liberty', 'Severed Foot Shackle & Emancipation Chain', 'Beneath the folds of the copper robe at right foot', 'Bronze and copper broken chain links celebrating the abolition of slavery in the United States and the passage of the 13th Amendment.', 'DOCUMENTED', 'src-nps-liberty'),
('sp-liberty-tabula-date', 'us-nyc-statue-of-liberty', 'Tabula Ansata Roman Independence Date', 'Held in Lady Liberty''s left hand', 'Keystone tablet inscribed in raised Roman lettering: "JULY IV MDCCLXXVI" commemorating the American Declaration of Independence.', 'DOCUMENTED', 'src-nps-liberty'),
('sp-liberty-seven-rays', 'us-nyc-statue-of-liberty', 'Seven-Rayed Radiant Solar Crown', 'Crown resting atop head above forehead', 'Seven tapering spiked rays projecting outward, representing the enlightenment of the seven seas and seven continents across the globe.', 'DOCUMENTED', 'src-nps-liberty');

-- ---------------------------------------------------------------- operational_notices
INSERT INTO operational_notices (notice_id, place_id, notice_kind, text, authority_source_id, last_verified_at, expires_at) VALUES
('op-eiffel-security', 'fr-paris-eiffel-tower', 'security-perimeter', 'Anti-ram glass barriers and security checks enclose the tower base. Large luggage, glass bottles, and unauthorized commercial tripods prohibited without SETE accreditation.', 'src-sete-eiffel', '2026-10-15', '2027-10-15'),
('op-colo-timed-entry', 'it-rome-colosseum', 'ticketing-restriction', 'Mandatory nominal timed tickets booked online in advance. Weapons, glass, aerosol cans, and bulky bags (> 30x40x15 cm) strictly barred from entry.', 'src-parco-colosseo', '2026-10-15', '2027-10-15'),
('op-machu-circuit-rules', 'pe-cusco-machu-picchu', 'conservation-protocol', 'Visitors must follow strictly designated unidirectional circuits with an accredited licensed guide. Re-entry, drones, trekking poles without rubber tips, and single-use plastics are prohibited.', 'src-sernanp-peru', '2026-10-15', '2027-10-15');

-- ---------------------------------------------------------------- FTS index
INSERT INTO place_search (place_id, display_name, aliases, body)
SELECT
  p.place_id,
  p.canonical_name,
  COALESCE((SELECT GROUP_CONCAT(a.alias_text, ' | ') FROM place_aliases a WHERE a.place_id = p.place_id), ''),
  COALESCE((SELECT GROUP_CONCAT(c.claim_text, ' ') FROM claims c WHERE c.place_id = p.place_id AND c.editorial_state IN ('REVIEWED','PUBLISHED')), '')
FROM places p;
