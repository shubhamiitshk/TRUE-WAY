package com.trueway.app.data

import android.content.Context
import com.trueway.app.pack.PrefsActivePackStore
import java.io.File

/**
 * Knowledge facade (F003/F004). Delegates to the installed pack's
 * `places.sqlite` when one is active, else the bundled demonstrator corpus.
 * Same ranking contract either way; call `initForPackDir` on launch and
 * after every pack install.
 */
object PlaceRepository {
    @Volatile
    private var source: PlaceDataSource = DemoCorpusSource()

    val sharedSqlRunner = AndroidSqlRunner()

    fun init(source: PlaceDataSource) {
        this.source = source
    }

    fun evictPackDirectory(packDir: File) {
        sharedSqlRunner.evictPackDirectory(packDir)
    }

    /** Switch to the active pack's DB if present, else the bundled corpus. Supports multi-pack aggregation. */
    fun initForPackDir(context: Context) {
        val store = PrefsActivePackStore(context)
        val activePacks = store.allActive()
        val packsDir = File(context.filesDir, "packs")
        val packSources = mutableListOf<PlaceDataSource>()
        for ((packId, version) in activePacks) {
            val dir = File(File(packsDir, packId), version)
            val db = File(dir, "content/places.sqlite").takeIf { it.exists() }
                ?: dir.walkTopDown().firstOrNull { f -> f.isFile && f.name == "places.sqlite" }
            if (db != null && db.exists()) {
                packSources.add(SqlitePackSource(db, sharedSqlRunner))
            }
        }
        if (packSources.isEmpty()) {
            val version = store.getActive("in-bihar-buddhist-circuit")
            val db = version?.let { File(File(packsDir, "in-bihar-buddhist-circuit"), "$it/content/places.sqlite") }
                ?.let { direct ->
                    if (direct.exists()) direct
                    else File(
                        File(packsDir, "in-bihar-buddhist-circuit"), "$version",
                    ).walkTopDown().firstOrNull { f -> f.isFile && f.name == "places.sqlite" }
                }
            if (db != null && db.exists()) {
                packSources.add(SqlitePackSource(db, sharedSqlRunner))
            }
        }
        source = when {
            packSources.size == 1 -> packSources[0]
            packSources.size > 1 -> CompositePlaceDataSource(packSources)
            else -> DemoCorpusSource()
        }
    }

    fun currentSourceName(): String =
        when (source) {
            is SqlitePackSource -> "pack"
            is CompositePlaceDataSource -> "multi-pack"
            else -> "demo"
        }

    fun get(placeId: String): Place? = source.get(placeId)

    fun all(): List<Place> = source.all()

    fun search(rawQuery: String, limit: Int = 20): List<Place> = source.search(rawQuery, limit)

    fun nearby(latitude: Double, longitude: Double, maxRadiusMeters: Double = 50_000.0): List<NearbyPlace> =
        source.nearby(latitude, longitude, maxRadiusMeters)
}
