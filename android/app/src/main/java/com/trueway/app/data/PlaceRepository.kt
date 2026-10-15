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

    /** Switch to the active pack's DB if present, else the bundled corpus. */
    fun initForPackDir(context: Context) {
        val store = PrefsActivePackStore(context)
        val version = store.getActive("in-bihar-buddhist-circuit")
        val db = version?.let { File(File(context.filesDir, "packs/in-bihar-buddhist-circuit"), "$it/content/places.sqlite") }
            // Packs written by the importer land at packs/<id>/<version>/…;
            // accept both that layout and the builder's content/places.sqlite.
            ?.let { direct ->
                if (direct.exists()) direct
                else File(
                    File(context.filesDir, "packs/in-bihar-buddhist-circuit"), "$version",
                ).walkTopDown().firstOrNull { f -> f.isFile && f.name == "places.sqlite" }
            }
        source = if (db != null && db.exists()) {
            SqlitePackSource(db, sharedSqlRunner)
        } else {
            DemoCorpusSource()
        }
    }

    fun currentSourceName(): String =
        (source as? SqlitePackSource)?.let { "pack" } ?: "demo"

    fun get(placeId: String): Place? = source.get(placeId)

    fun all(): List<Place> = source.all()

    fun search(rawQuery: String, limit: Int = 20): List<Place> = source.search(rawQuery, limit)

    fun nearby(latitude: Double, longitude: Double, maxRadiusMeters: Double = 50_000.0): List<NearbyPlace> =
        source.nearby(latitude, longitude, maxRadiusMeters)
}
