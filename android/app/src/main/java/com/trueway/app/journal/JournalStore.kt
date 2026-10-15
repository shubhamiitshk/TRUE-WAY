package com.trueway.app.journal

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.RoomDatabase
import androidx.room.Transaction
import kotlinx.coroutines.flow.Flow

/**
 * Private journal database (blueprint §10.1, §28.4; content/schema/journal_schema.sql).
 *
 * SEPARATE Room file (`user_journal.sqlite`, ADR-0008) from any publisher pack database:
 * deleting a downloaded region must never delete private notes. A journal row
 * may reference a `place_id` that is no longer installed — the UI shows
 * "content missing" instead of dropping the user's data. No account, no
 * upload, one-tap deletion (§15).
 */

// ---------------------------------------------------------------- entities

@Entity(tableName = "journal_entries")
data class JournalEntry(
    @PrimaryKey @ColumnInfo(name = "entry_id") val entryId: String,
    @ColumnInfo(name = "place_id") val placeId: String?,
    @ColumnInfo(name = "created_at") val createdAt: String,
    @ColumnInfo(name = "user_note") val userNote: String?,
    @ColumnInfo(name = "local_photo_uri") val localPhotoUri: String?,
    @ColumnInfo(name = "include_location_on_export") val includeLocationOnExport: Int = 0,
    @ColumnInfo(name = "local_only") val localOnly: Int = 1,
)

@Entity(tableName = "achievement_defs")
data class AchievementDef(
    @PrimaryKey @ColumnInfo(name = "achievement_id") val achievementId: String,
    @ColumnInfo(name = "name") val name: String,
    @ColumnInfo(name = "criteria_json") val criteriaJson: String,
)

@Entity(
    tableName = "achievement_events",
    primaryKeys = ["achievement_id", "unlocked_at"],
)
data class AchievementEvent(
    @ColumnInfo(name = "achievement_id") val achievementId: String,
    @ColumnInfo(name = "unlocked_at") val unlockedAt: String,
    @ColumnInfo(name = "evidence_entry_id") val evidenceEntryId: String?,
)

@Entity(tableName = "consent_choices")
data class ConsentChoice(
    @PrimaryKey @ColumnInfo(name = "consent_id") val consentId: String,
    @ColumnInfo(name = "purpose") val purpose: String,
    @ColumnInfo(name = "granted") val granted: Int,
    @ColumnInfo(name = "changed_at") val changedAt: String,
)

// ---------------------------------------------------------------- dao

@Dao
interface JournalDao {
    @Query("SELECT * FROM journal_entries ORDER BY created_at DESC")
    fun observeEntries(): Flow<List<JournalEntry>>

    @Query("SELECT * FROM journal_entries ORDER BY created_at DESC")
    suspend fun listEntries(): List<JournalEntry>

    @Insert
    suspend fun insert(entry: JournalEntry)

    @Query("UPDATE journal_entries SET user_note = :note WHERE entry_id = :entryId")
    suspend fun updateNote(entryId: String, note: String?)

    @Query("DELETE FROM journal_entries WHERE entry_id = :entryId")
    suspend fun delete(entryId: String)

    @Query("DELETE FROM journal_entries")
    suspend fun deleteAll()

    @Query("DELETE FROM achievement_events")
    suspend fun deleteAllAchievements()

    @Query("DELETE FROM consent_choices")
    suspend fun deleteAllConsent()

    /**
     * One-tap deletion of EVERYTHING private (§15 secure-defaults checklist):
     * notes, unlocked-achievement history (whose evidence_entry_id would
     * otherwise dangle) and consent records, in one transaction.
     */
    @Transaction
    suspend fun deleteEverythingPrivate() {
        deleteAll()
        deleteAllAchievements()
        deleteAllConsent()
    }

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun setConsent(choice: ConsentChoice)

    @Query("SELECT * FROM consent_choices WHERE consent_id = :consentId LIMIT 1")
    suspend fun consent(consentId: String): ConsentChoice?

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun unlockAchievement(event: AchievementEvent)
}

// ---------------------------------------------------------------- database

@Database(
    entities = [JournalEntry::class, AchievementDef::class, AchievementEvent::class, ConsentChoice::class],
    version = 1,
    exportSchema = false, // P0: single-device store; migration discipline starts at v2.
)
abstract class JournalDatabase : RoomDatabase() {
    abstract fun journalDao(): JournalDao
}
