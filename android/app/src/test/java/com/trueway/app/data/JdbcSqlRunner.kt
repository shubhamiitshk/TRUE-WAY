package com.trueway.app.data

import java.sql.DriverManager

/**
 * sqlite-jdbc [SqlRunner] for JVM tests (test source set only — production
 * uses the framework SQLite via [AndroidSqlRunner]). Runs the exact same
 * SQL the app ships, including FTS5 MATCH, against the fixture DB built
 * from the real publication schema + seed (`make_demo_places_db.py`).
 */
class JdbcSqlRunner(dbPath: String) : SqlRunner {
    private val url = "jdbc:sqlite:$dbPath"

    init {
        Class.forName("org.sqlite.JDBC")
    }

    override fun query(dbPath: String, sql: String, args: Array<out Any?>): List<Map<String, Any?>> {
        DriverManager.getConnection(url).use { con ->
            con.prepareStatement(sql).use { ps ->
                args.forEachIndexed { i, a ->
                    when (a) {
                        null -> ps.setNull(i + 1, java.sql.Types.NULL)
                        is Int -> ps.setInt(i + 1, a)
                        is Long -> ps.setLong(i + 1, a)
                        is Double -> ps.setDouble(i + 1, a)
                        is Float -> ps.setDouble(i + 1, a.toDouble())
                        is ByteArray -> ps.setBytes(i + 1, a)
                        else -> ps.setString(i + 1, a.toString())
                    }
                }
                ps.executeQuery().use { rs ->
                    val meta = rs.metaData
                    val out = mutableListOf<Map<String, Any?>>()
                    while (rs.next()) {
                        val row = mutableMapOf<String, Any?>()
                        for (i in 1..meta.columnCount) {
                            row[meta.getColumnName(i)] = rs.getObject(i)?.let {
                                if (it is Double && meta.getColumnType(i) == java.sql.Types.FLOAT) it
                                else it
                            }
                        }
                        out += row
                    }
                    return out
                }
            }
        }
    }
}
