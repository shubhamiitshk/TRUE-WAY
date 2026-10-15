package com.trueway.app.journal

import android.content.Context
import androidx.room.Room
import kotlinx.coroutines.flow.Flow
import java.time.Instant
import java.util.UUID

/**
 * Journal repository (F007): private notes over installed places.
 * Validation lives here so both the UI and future export share it; the DAO
 * stays a thin interface — which is also what makes this JVM-testable with
 * a fake DAO (Room itself needs a device).
 */
class JournalRepository(private val dao: JournalDao) {

    val entries: Flow<List<JournalEntry>> = dao.observeEntries()

    /** Save a discovery; returns the new entry id. Blank notes are stored as null. */
    suspend fun save(placeId: String, note: String?): String {
        require(placeId.isNotBlank()) { "placeId must not be blank" }
        val id = UUID.randomUUID().toString()
        dao.insert(
            JournalEntry(
                entryId = id,
                placeId = placeId,
                createdAt = Instant.now().toString(),
                userNote = note?.trim()?.takeIf { it.isNotEmpty() },
                localPhotoUri = null, // P0: text notes; photo attach is P1.
                includeLocationOnExport = 0,
                localOnly = 1,
            ),
        )
        return id
    }

    suspend fun updateNote(entryId: String, note: String?) {
        dao.updateNote(entryId, note?.trim()?.takeIf { it.isNotEmpty() })
    }

    suspend fun delete(entryId: String) = dao.delete(entryId)

    /** Re-insert a previously deleted entry (undo delete). */
    suspend fun restore(entry: JournalEntry) = dao.insert(entry)

    /** One-tap deletion of everything private (§15 secure-defaults checklist):
     *  notes, achievement history and consent records. */
    suspend fun deleteAll() = dao.deleteEverythingPrivate()

    suspend fun setConsent(consentId: String, granted: Boolean) {
        dao.setConsent(
            ConsentChoice(consentId, consentId, if (granted) 1 else 0, Instant.now().toString()),
        )
    }

    suspend fun consentGranted(consentId: String): Boolean? =
        dao.consent(consentId)?.let { it.granted == 1 }
}

/** Manual DI: single journal file for the app lifetime. */
object JournalGraph {
    @Volatile
    private var repo: JournalRepository? = null

    fun init(context: Context): JournalRepository =
        repo ?: synchronized(this) {
            repo ?: JournalRepository(
                Room.databaseBuilder(
                    context.applicationContext,
                    JournalDatabase::class.java,
                    // ADR-0008: filename matches the architecture spec so pack
                    // tooling and docs refer to one private database.
                    "user_journal.sqlite",
                ).build().journalDao(),
            ).also { repo = it }
        }

    /** Test/Preview entry point: repository backed by any DAO. */
    fun forTests(dao: JournalDao): JournalRepository = JournalRepository(dao)

    fun get(): JournalRepository =
        repo ?: throw IllegalStateException("JournalGraph.init(context) first")
}
