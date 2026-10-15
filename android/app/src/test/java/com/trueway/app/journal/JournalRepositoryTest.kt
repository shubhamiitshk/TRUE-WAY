package com.trueway.app.journal

import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Journal repository gates (F007, §28.4): blank-place rejection, note
 * normalization, newest-first listing, consent round-trip, full deletion.
 * Runs against a fake DAO — Room itself needs a device; the DAO surface is
 * thin by design so the fake is faithful. Uses runBlocking (coroutines-core
 * only, no extra test dep).
 */
class JournalRepositoryTest {

    private class FakeDao : JournalDao {
        val rows = mutableMapOf<String, JournalEntry>()
        val consents = mutableMapOf<String, ConsentChoice>()
        val achievements = mutableListOf<AchievementEvent>()
        private val signal = MutableStateFlow(0)

        override fun observeEntries(): Flow<List<JournalEntry>> =
            signal.map { rows.values.sortedByDescending { it.createdAt } }

        override suspend fun listEntries(): List<JournalEntry> =
            rows.values.sortedByDescending { it.createdAt }

        override suspend fun insert(entry: JournalEntry) {
            rows[entry.entryId] = entry
            signal.value++
        }

        override suspend fun updateNote(entryId: String, note: String?) {
            rows[entryId]?.let { rows[entryId] = it.copy(userNote = note) }
            signal.value++
        }

        override suspend fun delete(entryId: String) {
            rows.remove(entryId)
            signal.value++
        }

        override suspend fun deleteAll() {
            rows.clear()
            signal.value++
        }

        override suspend fun deleteAllAchievements() {
            achievements.clear()
        }

        override suspend fun deleteAllConsent() {
            consents.clear()
        }

        override suspend fun setConsent(choice: ConsentChoice) {
            consents[choice.consentId] = choice // REPLACE semantics
        }

        override suspend fun consent(consentId: String): ConsentChoice? = consents[consentId]

        override suspend fun unlockAchievement(event: AchievementEvent) {
            // IGNORE semantics: no duplicate (achievement_id, unlocked_at)
            if (achievements.none { it.achievementId == event.achievementId && it.unlockedAt == event.unlockedAt }) {
                achievements.add(event)
            }
        }
    }

    @Test
    fun saveNormalizesAndListsNewestFirst(): Unit = runBlocking {
        val dao = FakeDao()
        val repo = JournalGraph.forTests(dao)
        val id1 = repo.save("place-a", "  first note  ")
        delay(5)
        val id2 = repo.save("place-b", "   ")
        val all = dao.listEntries()
        assertEquals(2, all.size)
        assertEquals(id2, all[0].entryId) // newest first
        assertEquals("first note", all.find { it.entryId == id1 }!!.userNote)
        assertNull(all.find { it.entryId == id2 }!!.userNote) // blank → null
        assertEquals(1, all[0].localOnly) // never leaves the device by default
    }

    @Test
    fun deleteAndDeleteAll(): Unit = runBlocking {
        val dao = FakeDao()
        val repo = JournalGraph.forTests(dao)
        val id = repo.save("place-a", "note")
        repo.delete(id)
        assertTrue(dao.listEntries().isEmpty())
        repo.save("place-a", "x")
        repo.save("place-b", "y")
        // One-tap deletion must wipe notes AND achievements AND consent (§15).
        dao.unlockAchievement(AchievementEvent("ach-first-read", "2026-10-11T00:00:00Z", id))
        repo.setConsent("gap-beacon", true)
        repo.deleteAll()
        assertTrue(dao.listEntries().isEmpty())
        assertTrue(dao.achievements.isEmpty())
        assertTrue(dao.consents.isEmpty())
        assertNull(repo.consentGranted("gap-beacon"))
    }

    @Test
    fun reUnlockingSameAchievementDoesNotThrow(): Unit = runBlocking {
        val dao = FakeDao()
        val ev = AchievementEvent("ach-first-read", "2026-10-11T00:00:00Z", null)
        dao.unlockAchievement(ev)
        dao.unlockAchievement(ev) // IGNORE: no crash, no duplicate
        assertEquals(1, dao.achievements.size)
    }

    @Test
    fun consentRoundTrip(): Unit = runBlocking {
        val repo = JournalGraph.forTests(FakeDao())
        assertEquals(null, repo.consentGranted("gap-beacon"))
        repo.setConsent("gap-beacon", true)
        assertEquals(true, repo.consentGranted("gap-beacon"))
        repo.setConsent("gap-beacon", false)
        assertEquals(false, repo.consentGranted("gap-beacon"))
    }

    @Test(expected = IllegalArgumentException::class)
    fun blankPlaceRejected(): Unit = runBlocking {
        JournalGraph.forTests(FakeDao()).save("   ", "note")
    }
}
