package com.trueway.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Essentials + changelog gates (F011/F013): every entry dated, every call
 * caveated, and the Kotlin objects mirror content/seed/essentials.json +
 * content/CHANGELOG.md (single-sourcing moves to the pack builder).
 */
class EssentialsTest {

    @Test
    fun everyEntryDatedAndCaveatPresent() {
        assertTrue(Essentials.contacts.isNotEmpty())
        assertTrue(Essentials.advice.isNotEmpty())
        (Essentials.contacts.map { it.lastVerified } +
            Essentials.advice.map { it.lastVerified }).forEach {
            assertTrue(it.matches(Regex("\\d{4}-\\d{2}-\\d{2}")))
        }
        assertTrue(Essentials.CALL_CAVEAT.contains("mobile network"))
        assertTrue(Essentials.FRESHNESS_NOTE.contains("may have changed"))
    }

    @Test
    fun kotlinMirrorsSeedJson() {
        val root = org.json.JSONObject(
            javaClass.classLoader?.getResourceAsStream("essentials.json")!!
                .bufferedReader().readText(),
        )
        assertEquals(
            root.getJSONArray("contacts").length(),
            Essentials.contacts.size,
        )
        assertEquals(
            root.getJSONArray("advice").length(),
            Essentials.advice.size,
        )
        assertEquals(root.getString("call_caveat"), Essentials.CALL_CAVEAT)
    }

    @Test
    fun changelogDatedAndNonEmpty() {
        assertTrue(PackChangelog.releases.isNotEmpty())
        PackChangelog.releases.forEach { r ->
            assertTrue(r.version.isNotBlank())
            assertTrue(r.date.matches(Regex("\\d{4}-\\d{2}-\\d{2}")))
            assertTrue(r.changes.isNotEmpty())
        }
    }
}
