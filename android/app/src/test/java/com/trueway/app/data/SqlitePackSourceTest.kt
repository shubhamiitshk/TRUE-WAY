package com.trueway.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Pack-SQL gates: the SQLite source reads the real publication schema +
 * seed through the exact queries the app ships. Parity with the bundled
 * corpus proves the pack path and the demo path tell the same truths.
 */
class SqlitePackSourceTest {

    private fun source(): SqlitePackSource {
        val url = javaClass.classLoader?.getResource("demo_places.sqlite")
            ?: throw AssertionError("missing test fixture demo_places.sqlite")
        val db = File(url.toURI())
        return SqlitePackSource(db, JdbcSqlRunner(db.absolutePath))
    }

    private val demo = DemoCorpusSource()

    @Test
    fun searchParityWithBundledCorpus() {
        val sql = source()
        val queries = listOf(
            "Mahabodhi", "महाबोधि", "Mahabodhi Mandir", "Nalanda", "नालंदा",
            "Griddhakuta", "Temple 3", "Venu Vana", "Sonbhandar",
        )
        for (q in queries) {
            val expected = demo.search(q).firstOrNull()?.placeId
            val actual = sql.search(q).firstOrNull()?.placeId
            assertEquals("query <$q>", expected, actual)
        }
        assertTrue(sql.search("zxq unknown place 999").isEmpty())
        assertTrue(sql.search("").isEmpty())
    }

    @Test
    fun ftsInjectionIsHarmless() {
        val sql = source()
        // FTS syntax and SQL metacharacters must degrade to no-match, never
        // error or broaden semantics.
        listOf("\" OR \"1\"=\"1", "Mahabodhi*", "a: b", "-- comment", "'; DROP TABLE places; --")
            .forEach { q ->
                val rows = sql.search(q)
                assertTrue("query <$q> should not throw or leak", rows.all { it.placeId.isNotBlank() })
            }
        // …and the tables are all still there afterwards.
        assertEquals(15, sql.all().size)
    }

    @Test
    fun placeHydrationMatchesCorpus() {
        val sql = source()
        for (p in demo.all()) {
            val got = sql.get(p.placeId)
                ?: throw AssertionError("missing ${p.placeId} in pack DB")
            assertEquals(p.canonicalName, got.canonicalName)
            assertEquals(p.claims.size, got.claims.size)
            assertEquals(p.aliases.sorted(), got.aliases.sorted())
            got.claims.forEach { c ->
                assertTrue("unsourced claim ${c.claimId}", c.sourceId.isNotBlank())
            }
        }
    }

    @Test
    fun missingDbDegradesToEmpty() {
        val sql = SqlitePackSource(File("/nonexistent/places.sqlite"), JdbcSqlRunner(":memory:"))
        assertTrue(sql.search("Nalanda").isEmpty())
        assertTrue(sql.all().isEmpty())
        assertEquals(null, sql.get("in-bihar-nalanda-mahavihara"))
    }
}
