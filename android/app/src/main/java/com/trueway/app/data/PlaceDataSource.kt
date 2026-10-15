package com.trueway.app.data

import java.io.File

/**
 * Knowledge-source seam (blueprint §10.3, Strategic §4.1).
 *
 * - [DemoCorpusSource]: bundled 15-POI demonstrator (works with zero packs).
 * - [SqlitePackSource]: reads an installed pack's `places.sqlite`
 *   (publication_schema.sql + FTS5) through a [SqlRunner]. Production uses
 *   the framework SQLite; JVM tests inject a sqlite-jdbc runner over the
 *   fixture DB built from the real seed SQL — so pack SQL, FTS5 queries and
 *   the corpus/parity contract are tested, not mocked.
 */
interface PlaceDataSource {
    fun get(placeId: String): Place?
    fun all(): List<Place>
    fun search(rawQuery: String, limit: Int = 20): List<Place>

    /**
     * Finds places within [maxRadiusMeters] of ([latitude], [longitude]),
     * ranked in ascending order by distance using offline Haversine formula (F005/F008).
     */
    fun nearby(latitude: Double, longitude: Double, maxRadiusMeters: Double = 50_000.0): List<NearbyPlace> {
        return all().mapNotNull { p ->
            val pLat = p.latitude ?: return@mapNotNull null
            val pLon = p.longitude ?: return@mapNotNull null
            val dist = GeoUtils.distanceMeters(latitude, longitude, pLat, pLon)
            if (dist <= maxRadiusMeters) {
                NearbyPlace(
                    place = p,
                    distanceMeters = dist,
                    distanceFormatted = GeoUtils.formatDistance(dist),
                )
            } else null
        }.sortedBy { it.distanceMeters }
    }
}

/** Minimal SQL execution seam: SQL text + bound args in, rows out. */
interface SqlRunner {
    fun query(dbPath: String, sql: String, args: Array<out Any?>): List<Map<String, Any?>>
}

class DemoCorpusSource : PlaceDataSource {
    private val byId: Map<String, Place> = DemoCorpus.places.associateBy { it.placeId }

    override fun get(placeId: String): Place? = byId[placeId]

    override fun all(): List<Place> = DemoCorpus.places

    override fun search(rawQuery: String, limit: Int): List<Place> {
        val q = rawQuery.trim().lowercase()
        if (q.isEmpty()) return emptyList()
        val querySkeleton = IndicPhoneticNormalizer.toSkeleton(q)
        val querySkeletonTokens = querySkeleton.split(" ").filter { it.isNotBlank() }

        val exactName = mutableListOf<Place>()
        val exactAlias = mutableListOf<Place>()
        val partial = mutableListOf<Place>()
        val phonetic = mutableListOf<Place>()

        for (p in DemoCorpus.places) {
            val nameLower = p.canonicalName.lowercase()
            if (nameLower == q) {
                exactName += p
                continue
            }
            if (p.aliases.any { it.lowercase() == q }) {
                exactAlias += p
                continue
            }
            if (nameLower.contains(q) ||
                p.aliases.any { it.lowercase().contains(q) }
            ) {
                partial += p
                continue
            }
            if (querySkeleton.isNotEmpty()) {
                val haystackRaw = buildString {
                    append(nameLower).append(' ')
                    p.aliases.forEach { append(it.lowercase()).append(' ') }
                }
                val haystackSkeleton = IndicPhoneticNormalizer.toSkeleton(haystackRaw)
                if (haystackSkeleton.contains(querySkeleton) ||
                    (querySkeletonTokens.isNotEmpty() && querySkeletonTokens.all { tok -> haystackSkeleton.contains(tok) })
                ) {
                    phonetic += p
                }
            }
        }
        return (exactName + exactAlias + partial + phonetic).distinctBy { it.placeId }.take(limit.coerceAtLeast(1))
    }
}

class SqlitePackSource(
    private val dbFile: File,
    private val runner: SqlRunner,
) : PlaceDataSource {
    private val path: String = dbFile.absolutePath

    override fun get(placeId: String): Place? {
        if (!dbFile.exists()) return null
        return try {
            val places = runner.query(
                path,
                "SELECT place_id, parent_place_id, canonical_name, category, " +
                    "visitor_mode, visitor_notice, last_reviewed_at, latitude, longitude " +
                    "FROM places WHERE place_id = ? AND editorial_state IN ('REVIEWED','PUBLISHED')",
                arrayOf(placeId),
            )
            if (places.isEmpty()) return null
            hydrate(places[0])
        } catch (_: Exception) {
            null
        }
    }

    override fun all(): List<Place> {
        if (!dbFile.exists()) return emptyList()
        return try {
            runner.query(
                path,
                "SELECT place_id FROM places " +
                    "WHERE editorial_state IN ('REVIEWED','PUBLISHED') ORDER BY canonical_name",
                emptyArray(),
            ).mapNotNull { get(it["place_id"] as? String ?: return@mapNotNull null) }
        } catch (_: Exception) {
            emptyList()
        }
    }

    override fun search(rawQuery: String, limit: Int): List<Place> {
        val q = rawQuery.trim()
        if (q.isEmpty() || !dbFile.exists()) return emptyList()
        return try {
            val ids = linkedSetOf<String>()
            // 1. Exact canonical / alias match (same rank contract as DemoCorpusSource).
            runner.query(
                path,
                "SELECT place_id FROM places WHERE lower(canonical_name) = lower(?) " +
                    "AND editorial_state IN ('REVIEWED','PUBLISHED')",
                arrayOf(q),
            ).forEach { ids += it["place_id"] as String }
            runner.query(
                path,
                "SELECT DISTINCT a.place_id AS place_id FROM place_aliases a " +
                    "JOIN places p ON p.place_id = a.place_id " +
                    "WHERE lower(a.alias_text) = lower(?) " +
                    "AND p.editorial_state IN ('REVIEWED','PUBLISHED')",
                arrayOf(q),
            ).forEach { ids += it["place_id"] as String }
            // 2. FTS5 over names/aliases/body (parameterized; never interpolated),
            // ranked by BM25 exactly as §10.3 specifies. The editorial_state
            // filter is applied INSIDE the query (joined to places) so unpublished
            // rows don't consume LIMIT slots ahead of published ones.
            val match = toFtsMatch(q)
            if (match != null) {
                runner.query(
                    path,
                    "SELECT place_search.place_id FROM place_search " +
                        "JOIN places p ON p.place_id = place_search.place_id " +
                        "WHERE place_search MATCH ? " +
                        "AND p.editorial_state IN ('REVIEWED','PUBLISHED') " +
                        "ORDER BY bm25(place_search) LIMIT ?",
                    arrayOf<Any?>(match, limit.coerceAtLeast(1)),
                ).forEach { ids += it["place_id"] as String }
            }
            // 3. Phonetic expansion fallback if slots remain
            if (ids.size < limit) {
                val skeletonMatch = toFtsSkeletonMatch(q)
                if (skeletonMatch != null && skeletonMatch != match) {
                    runner.query(
                        path,
                        "SELECT place_search.place_id FROM place_search " +
                            "JOIN places p ON p.place_id = place_search.place_id " +
                            "WHERE place_search MATCH ? " +
                            "AND p.editorial_state IN ('REVIEWED','PUBLISHED') " +
                            "ORDER BY bm25(place_search) LIMIT ?",
                        arrayOf<Any?>(skeletonMatch, limit.coerceAtLeast(1)),
                    ).forEach { ids += it["place_id"] as String }
                }
            }
            ids.take(limit.coerceAtLeast(1)).mapNotNull { get(it) }
        } catch (_: Exception) {
            emptyList()
        }
    }

    /**
     * Quote each token as a prefix phrase (`"tok"*`, AND-ed). Quoting
     * neutralizes FTS5 syntax (`* : " OR --`) so hostile input degrades to
     * no-match instead of a syntax error or altered semantics.
     */
    internal fun toFtsMatch(q: String): String? {
        val tokens = q.split("\\s+".toRegex()).map { it.replace("\"", "").trim() }
            .filter { it.isNotEmpty() }
        if (tokens.isEmpty()) return null
        return tokens.joinToString(" AND ") { "\"$it\"*" }
    }

    internal fun toFtsSkeletonMatch(q: String): String? {
        val rawTokens = q.split("\\s+".toRegex()).map { it.replace("\"", "").trim() }.filter { it.isNotEmpty() }
        val skeletonTokens = IndicPhoneticNormalizer.toSkeleton(q)
            .split("\\s+".toRegex())
            .map { it.replace("\"", "").trim() }
            .filter { it.length >= 2 }
        val combined = (rawTokens + skeletonTokens).distinct()
        if (combined.isEmpty()) return null
        return combined.joinToString(" OR ") { "\"$it\"*" }
    }

    private fun hydrate(row: Map<String, Any?>): Place? {
        val placeId = row["place_id"] as? String ?: return null
        return try {
            val aliases = runner.query(
                path,
                "SELECT alias_text FROM place_aliases WHERE place_id = ? ORDER BY alias_text",
                arrayOf(placeId),
            ).mapNotNull { it["alias_text"] as? String }
            val claims = runner.query(
                path,
                "SELECT c.claim_id, c.claim_type, c.locale, c.claim_text, " +
                    "c.reviewed_at, cs.source_id, s.title AS source_title " +
                    "FROM claims c LEFT JOIN claim_sources cs ON cs.claim_id = c.claim_id " +
                    "LEFT JOIN sources s ON s.source_id = cs.source_id " +
                    "WHERE c.place_id = ? AND c.editorial_state IN ('REVIEWED','PUBLISHED') " +
                    "ORDER BY c.claim_id, cs.source_id",
                arrayOf(placeId),
            ).filter { it["claim_id"] != null }.groupBy { it["claim_id"] as String }
                .mapNotNull { (_, rows) ->
                    val first = rows[0]
                    // One unknown claim_type must skip only THAT claim, never
                    // drop the whole place (fail-soft on vocabulary, not the POI).
                    val type = runCatching {
                        ClaimType.valueOf(first["claim_type"] as String)
                    }.getOrNull() ?: return@mapNotNull null
                    SourcedClaim(
                        claimId = first["claim_id"] as String,
                        type = type,
                        locale = (first["locale"] as? String).orEmpty(),
                        text = (first["claim_text"] as? String).orEmpty(),
                        sourceId = (first["source_id"] as? String).orEmpty(),
                        sourceTitle = (first["source_title"] as? String).orEmpty(),
                        reviewedAt = (first["reviewed_at"] as? String).orEmpty(),
                    )
                }
            // Every published claim must carry a source anchor (§28.3 gate).
            if (claims.any { it.sourceId.isBlank() }) return null
            val lat = (row["latitude"] as? Number)?.toDouble()
            val lon = (row["longitude"] as? Number)?.toDouble()
            Place(
                placeId = placeId,
                parentPlaceId = row["parent_place_id"] as? String,
                canonicalName = (row["canonical_name"] as? String).orEmpty(),
                category = (row["category"] as? String).orEmpty(),
                aliases = aliases,
                visitorMode = (row["visitor_mode"] as? String).orEmpty(),
                visitorNotice = (row["visitor_notice"] as? String).orEmpty(),
                lastReviewedAt = (row["last_reviewed_at"] as? String).orEmpty(),
                claims = claims,
                latitude = lat,
                longitude = lon,
            )
        } catch (_: Exception) {
            null
        }
    }
}
