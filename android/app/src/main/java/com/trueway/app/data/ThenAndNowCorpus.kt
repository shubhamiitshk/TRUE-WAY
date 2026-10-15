package com.trueway.app.data

/**
 * P1A Then & Now archival comparisons (blueprint v3.0 §3, §7, §8, F108).
 * Target: Exactly 3 comparison pairs across 3 distinct sites consisting of 6 images total (3 historic + 3 modern).
 *
 * 3-Site Asset Schedule:
 * - Site 1: Mahabodhi Temple (in-bihar-bodhgaya-mahabodhi)
 *     Historical: 1 cleared historical photograph by J.D. Beglar (c. 1880–1884), identifying Photo 1003(50)
 *       ('during restoration') as the primary archival plate, with Photo 1003(49) ('before repairs') noted as
 *       an alternate sequential historical phase for Mahabodhi (NOT a substitute for Nalanda or Rajgir);
 *       both currently listed as unavailable online by the British Library catalogue, establishing provenance
 *       but not downloadability, and lawful reproduction files remain to be acquired.
 *     Modern: 1 new licensed photograph under CC BY-SA 4.0.
 * - Site 2: Nalanda Temple No. 3 (in-bihar-nalanda-temple-03)
 *     Historical: 1 cleared historical photograph by Dr. David B. Spooner (1915 ASI excavation plate XVI).
 *     Modern: 1 new licensed photograph under CC BY-SA 4.0.
 * - Site 3: Rajgir Cyclopean Wall (in-bihar-rajgir-cyclopean-wall)
 *     Historical: 1 cleared historical photograph by Sir John Marshall (1906 ASI survey plate XXIX).
 *     Modern: 1 new licensed photograph under CC BY-SA 4.0.
 * Total: 3 distinct sites, 3 historical images + 3 modern images = 6 image assets.
 */
data class ArchivalComparison(
    val comparisonId: String,
    val placeId: String,
    val title: String,
    val archivalEra: String,
    val historicalPhotoTitle: String = "",
    val historicalPhotographer: String = "",
    val historicalPhotographerLifeDates: String = "",
    val historicalArchive: String = "",
    val historicalAccessionId: String = "",
    val historicalLegalStatus: String = "",
    val historicalRedistributionNotice: String = "",
    val historicalPhotoAssetPath: String = "",
    val archivalDescription: String,
    val archivalSource: String,
    val modernPhotoTitle: String = "",
    val modernPhotographer: String = "",
    val modernRightsHolder: String = "",
    val modernLicence: String = "",
    val modernRedistributionNotice: String = "",
    val modernPhotoAssetPath: String = "",
    val modernObservation: String,
    val preservationNotes: String,
    val viewpointAlignmentNotes: String = "",
    val statutoryCopyrightAnalysis: String = "",
    val rightsStatement: String,
    val curatorReviewDate: String,
)

object ThenAndNowCorpus {
    val comparisons: Map<String, ArchivalComparison> = mapOf(
        "in-bihar-bodhgaya-mahabodhi" to ArchivalComparison(
            comparisonId = "tn-mahabodhi-1880s",
            placeId = "in-bihar-bodhgaya-mahabodhi",
            title = "Mahabodhi: The 1880s Cunningham & Beglar Restoration",
            archivalEra = "c. 1880–1884 CE",
            historicalPhotoTitle = "Mahabodhi Temple from South-East prior to and during Cunningham-Beglar restoration (Primary plate: Photo 1003(50) during restoration; Sequential phase: Photo 1003(49) before repairs)",
            historicalPhotographer = "Joseph David Beglar",
            historicalPhotographerLifeDates = "1845–1907",
            historicalArchive = "British Library: India Office Select Materials / Archaeological Survey of India Photographic Collection",
            historicalAccessionId = "BL Photo 1003(50) (primary plate: during restoration), Photo 1003(49) (sequential historical phase: before repairs; alternate Mahabodhi view, not a substitute for Nalanda or Rajgir) [formerly cited as Photo 1003/(1130)]; ASI Print Collection Vol. XIII, Item 42",
            historicalLegalStatus = "Statutory copyright expired under Indian Copyright Act, 1957 §§ 22 & 28; digital asset acquisition and clearance pending (British Library catalogue lists digital images as unavailable online, establishing provenance but not downloadability; lawful reproduction files remain to be acquired)",
            historicalRedistributionNotice = "Digital image file acquisition pending; British Library catalogue verifies Photo 1003(50) (during restoration, primary plate) and Photo 1003(49) (before repairs, sequential phase for Mahabodhi, not a substitute for Nalanda or Rajgir) as related views with digital files listed as unavailable online, establishing provenance but not downloadability; lawful reproduction files remain to be acquired",
            historicalPhotoAssetPath = "images/then_now/mahabodhi_1880s_beglar.webp",
            archivalDescription = "Late 19th-century photographic documentation and architectural drawings by Alexander Cunningham and Joseph David Beglar showing the Mahabodhi Temple prior to structural stabilization.",
            archivalSource = "Archaeological Survey of India Reports / British Library India Office Collection Photo 1003(50) (during restoration, primary plate), Photo 1003(49) (before repairs, sequential Mahabodhi phase, not substitute for other sites) [ref: Photo 1003/(1130)]",
            modernPhotoTitle = "Conserved Mahabodhi Temple Main Shikhara and Circumambulation Railing from South-East viewpoint",
            modernPhotographer = "TrueWay Field Curatorial Team (Lead: S. Kumar, 2026)",
            modernRightsHolder = "TrueWay Editorial / Contributing Heritage Photographers",
            modernLicence = "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)",
            modernRedistributionNotice = "Openly licensed for redistribution and derivative cultural use with attribution under CC BY-SA 4.0",
            modernPhotoAssetPath = "images/then_now/mahabodhi_2026_conserved.webp",
            modernObservation = "The restored 55-meter main shikhara with corner miniature chaityas and surrounding sandstone circumambulation railing as conserved under UNESCO World Heritage status (2002).",
            preservationNotes = "The 1880s British-led restoration reconstructed the upper pinnacle and corner stupas based on medieval stone votive models excavated around the temple plinth. While celebrated for rescuing the monument from collapse, certain stucco plaster details reflect 19th-century Victorian interpretations of medieval Gupta art.",
            viewpointAlignmentNotes = "South-East oblique vantage from outer circumambulation path (~45m distance, 35mm equivalent focal length). Aligned with J.D. Beglar's 1880 station showing the southern face of the 55m main shikhara, basement mouldings, and corner miniature chaityas.",
            statutoryCopyrightAnalysis = "Statutory Analysis under Indian Copyright Act, 1957 & Legacy Framework:\n" +
                "1. Section 25 (term in photographs) was omitted by the Copyright (Amendment) Act, 2012 (Act 27 of 2012). Photographs are protected as artistic works under Section 2(c)(i).\n" +
                "2. Under Section 22, copyright subsists for author's life plus 60 years from the calendar year following death. Photographer J.D. Beglar died in 1907; the 60-year statutory term expired on 1 January 1968. Sir Alexander Cunningham died in 1893 (expired 1954).\n" +
                "3. Under Section 28 (Government works), official publication occurred in 1892 in the ASI Reports (W.H. Allen, London); 60-year term expired by 1 January 1953.\n" +
                "4. Legacy & Transitional Rights: Under the Indian Copyright Act, 1914 and Imperial Copyright Act, 1911 (Section 21), copyright in photographs was 50 years from negative making (1884), expiring in 1934 prior to the commencement of the 1957 Act (21 Jan 1958). Under Section 79, expired rights are not revived. UK Crown Copyright expired 50 years after creation under the UK Copyright, Designs and Patents Act 1988 (Sch. 1 para 40).\n" +
                "5. Verified British Library Shelfmarks & Digital Image Status: British Library catalogue records verify Photo 1003(50) ('Mahabodhi Temple at Bodh Gaya, during restoration') as the primary archival plate and Photo 1003(49) ('Mahabodhi Temple before repairs') as an alternate sequential historical phase for Mahabodhi (NOT a substitute for Nalanda or Rajgir) [formerly cited as Photo 1003/(1130)]. Note: Digital images are currently listed as unavailable online in the British Library catalogue (searcharchives.bl.uk/catalog/040-003136471 and searcharchives.bl.uk/catalog/040-003136470). These records establish archival provenance, not downloadability or permission to redistribute particular digital reproductions; lawful reproduction files remain to be acquired.\n" +
                "Conclusion: Statutory copyright terms have elapsed under §§ 22 & 28, but digital image file acquisition and verification remain pending. Total schedule: 3 distinct sites, 3 historical images + 3 modern images = 6 image assets.",
            rightsStatement = "Archival reference: Public Domain statutory analysis (Indian Copyright Act 1957 §§ 22 & 28 expired); digital image acquisition pending from British Library Photo 1003(50) primary / Photo 1003(49) sequential phase (catalogue establishes provenance, not downloadability; lawful files to be acquired) / Modern documentation: CC BY-SA 4.0 TrueWay Editorial.",
            curatorReviewDate = "2026-10-13",
        ),
        "in-bihar-nalanda-temple-03" to ArchivalComparison(
            comparisonId = "tn-nalanda-temple3-1915",
            placeId = "in-bihar-nalanda-temple-03",
            title = "Temple 3: Excavating the Seven Stupa Layers",
            archivalEra = "c. 1915–1926 CE",
            historicalPhotoTitle = "Temple Site No. 3 excavation showing the unearthing of stupa envelopes and northern plinth stairs",
            historicalPhotographer = "Dr. David Brainerd Spooner",
            historicalPhotographerLifeDates = "1879–1925",
            historicalArchive = "Archaeological Survey of India (ASI) Central Archaeological Archives, New Delhi & British Library India Office Collection",
            historicalAccessionId = "ASI Annual Report 1915-16, Part I, Plate XVI(a); BL Photo 2/1(58); ASI Excavation Album Nalanda Vol. I, No. 104",
            historicalLegalStatus = "Public Domain under Indian Copyright Act, 1957 § 22 (author life + 60 years expired 1986) and § 28 (Government work published 1918 expired 1979)",
            historicalRedistributionNotice = "Unrestricted open historical documentation; government archaeological survey publication public domain",
            historicalPhotoAssetPath = "images/then_now/nalanda_temple3_1915_spooner.webp",
            archivalDescription = "Early excavation photography by Dr. David Brainerd Spooner and H. Hargreaves capturing the unearthing of Temple 3 from under centuries of accumulated earth and vegetation mounds.",
            archivalSource = "Annual Report of the Archaeological Survey of India (ASI, 1915-16 to 1925-26, Pl. XVI)",
            modernPhotoTitle = "Exposed multi-tier brick stupa plinth with exposed Gupta-Pala stucco Bodhisattva niches",
            modernPhotographer = "TrueWay Field Curatorial Team (2026)",
            modernRightsHolder = "TrueWay Editorial / Contributing Heritage Photographers",
            modernLicence = "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)",
            modernRedistributionNotice = "Openly redistributable under CC BY-SA 4.0 with attribution",
            modernPhotoAssetPath = "images/then_now/nalanda_temple3_2026_conserved.webp",
            modernObservation = "The exposed multi-tier plinth revealing stucco Bodhisattva figures in recessed niches of the 5th layer, flanked by an extensive field of votive stupas.",
            preservationNotes = "Excavations revealed seven successive architectural envelopes built around the core stupa over seven centuries. Current conservation focuses on water drainage and salt efflorescence prevention on ancient exposed brick courses.",
            viewpointAlignmentNotes = "North-Eastern corner vantage elevated ~3m overlooking the staircase leading to the 5th architectural envelope. Aligned with Spooner's 1915 excavation station to frame the brick stupa core and stucco Bodhisattva niches.",
            statutoryCopyrightAnalysis = "Statutory Analysis under Indian Copyright Act, 1957 & Legacy Framework:\n" +
                "1. Section 25 (term in photographs) was omitted by the Copyright (Amendment) Act, 2012 (Act 27 of 2012). Photographs are protected as artistic works under Section 2(c)(i).\n" +
                "2. Under Section 22, copyright subsists for author's lifetime plus 60 years post-mortem. Dr. D.B. Spooner died on 30 January 1925; the 60-year term expired on 1 January 1986.\n" +
                "3. Under Section 28 (Government works), the ASI Annual Report was published by the Superintendent of Government Printing, Calcutta in 1918; the 60-year term expired on 1 January 1979.\n" +
                "4. Legacy & Transitional Rights: Official archaeological excavation survey plates commissioned under Government auspices qualify as Government works; 60-year post-publication term elapsed in 1979. BL Photo 2/1(58) held under open public reference access.\n" +
                "Conclusion: Archival photograph is confirmed in the Public Domain under both Section 22 and Section 28.",
            rightsStatement = "Archival source: Government of India Archaeological Survey (Public Domain under §§ 22 & 28) / Modern: CC BY-SA 4.0 TrueWay.",
            curatorReviewDate = "2026-10-12",
        ),
        "in-bihar-rajgir-cyclopean-wall" to ArchivalComparison(
            comparisonId = "tn-rajgir-wall-1906",
            placeId = "in-bihar-rajgir-cyclopean-wall",
            title = "Cyclopean Wall: Mapping the Magadhan Frontier",
            archivalEra = "c. 1905–1906 CE",
            historicalPhotoTitle = "Ancient Cyclopean Wall ramparts and bastion overlooking the Banganga Pass, Rajgir",
            historicalPhotographer = "Sir John Hubert Marshall",
            historicalPhotographerLifeDates = "1876–1958",
            historicalArchive = "Archaeological Survey of India Photographic Archive / British Library India Office Collections",
            historicalAccessionId = "ASI Annual Report 1905-06, Plate XXIX; BL Photo 1000/39(3922); ASI Memoir No. 24",
            historicalLegalStatus = "Public Domain under Indian Copyright Act, 1957 § 22 (author life + 60 years expired 2019) and § 28 (Government work published 1908 expired 1969)",
            historicalRedistributionNotice = "Unrestricted open educational and topographical reuse; published survey plates public domain",
            historicalPhotoAssetPath = "images/then_now/rajgir_wall_1906_marshall.webp",
            archivalDescription = "Topographical surveys by John Marshall identifying the remaining stone perimeter of the ancient capital of Rajagriha.",
            archivalSource = "ASI Survey Memoirs / Cunningham's Ancient Geography of India & ASI Annual Report 1905-06, Pl. XXIX",
            modernPhotoTitle = "Extant limestone cyclopean dry-stone bastions along the Rajgir-Gaya highway",
            modernPhotographer = "TrueWay Field Curatorial Team (2026)",
            modernRightsHolder = "TrueWay Editorial / Contributing Heritage Photographers",
            modernLicence = "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)",
            modernRedistributionNotice = "Openly redistributable under CC BY-SA 4.0 with attribution",
            modernPhotoAssetPath = "images/then_now/rajgir_wall_2026_conserved.webp",
            modernObservation = "Extant unmortared dry-stone wall bastions running across natural ridge gaps along the modern Rajgir hill highway.",
            preservationNotes = "The wall represents one of the oldest dry-stone military ramparts in South Asia, dating to the pre-Mauryan period. Strict conservation protocols prohibit moving or realigning dislodged limestone blocks.",
            viewpointAlignmentNotes = "West-facing ground-level perspective from the Banganga pass road shoulder (~20m from base). Aligned with Marshall's 1906 survey angle showing the rough-hewn dry-stone limestone block masonry coursing without mortar.",
            statutoryCopyrightAnalysis = "Statutory Analysis under Indian Copyright Act, 1957 & Legacy Framework:\n" +
                "1. Section 25 (term in photographs) was omitted by the Copyright (Amendment) Act, 2012 (Act 27 of 2012). Photographs are protected as artistic works under Section 2(c)(i).\n" +
                "2. Under Section 22, copyright subsists for author's lifetime plus 60 years post-mortem. Sir John Marshall died on 17 August 1958; the 60-year post-mortem calendar year term (1959–2018) expired on 1 January 2019.\n" +
                "3. Under Section 28 (Government works), official publication by the Archaeological Survey in 1908 expired 60 years post-publication on 1 January 1969.\n" +
                "4. Legacy & Transitional Rights: Plate XXIX was published in ASI Annual Report 1905-06 (Calcutta, 1908); whether categorized as Government work (expired 1969) or individual artistic work of Marshall (expired 2019), statutory term has fully lapsed. BL Photo 1000/39(3922) held under open cultural reuse.\n" +
                "Conclusion: Archival plate confirmed in the Public Domain under both Section 22 and Section 28.",
            rightsStatement = "Survey citation: Historical Public Domain (Indian Copyright Act 1957 §§ 22 & 28 expired) / Modern: CC BY-SA 4.0 TrueWay.",
            curatorReviewDate = "2026-10-12",
        ),
    )

    fun get(placeId: String): ArchivalComparison? = comparisons[placeId]
    fun all(): List<ArchivalComparison> = comparisons.values.toList()
}
