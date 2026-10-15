package com.trueway.app.data

import android.database.Cursor
import android.database.sqlite.SQLiteDatabase
import java.io.Closeable
import java.io.File
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.locks.ReentrantReadWriteLock
import kotlin.concurrent.read
import kotlin.concurrent.write

/**
 * Framework-SQLite [SqlRunner] (production; epoch-leased read-only pool, no WAL writes).
 * Applies SQLite PRAGMA query_only = ON, temp_store = MEMORY, mmap_size = 16MB.
 * Prevents stale inode reads and SQLiteDiskIOException during atomic pack updates.
 */
class AndroidSqlRunner : SqlRunner, Closeable {

    private data class PoolEntry(
        val canonicalPath: String,
        val lastModified: Long,
        val db: SQLiteDatabase
    )

    private val lock = ReentrantReadWriteLock()
    private val pool = ConcurrentHashMap<String, PoolEntry>()

    fun <T> query(
        dbFile: File,
        sql: String,
        selectionArgs: Array<String> = emptyArray(),
        mapper: (Cursor) -> T
    ): T = lock.read {
        val db = acquireReadOnlyDatabase(dbFile)
        db.rawQuery(sql, selectionArgs).use { cursor ->
            mapper(cursor)
        }
    }

    override fun query(dbPath: String, sql: String, args: Array<out Any?>): List<Map<String, Any?>> {
        val file = File(dbPath)
        if (!file.exists()) return emptyList()
        val bind = args.map { it?.toString() ?: "" }.toTypedArray()
        return try {
            query(file, sql, bind) { cursor -> cursor.toRows() }
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun evictPackDirectory(packDir: File) = lock.write {
        val prefix = runCatching { packDir.canonicalPath }.getOrDefault(packDir.absolutePath)
        val keysToRemove = pool.keys().toList().filter { it.startsWith(prefix) }
        for (key in keysToRemove) {
            pool.remove(key)?.db?.runCatching { close() }
        }
    }

    private fun acquireReadOnlyDatabase(dbFile: File): SQLiteDatabase {
        val canonical = dbFile.canonicalPath
        val lastMod = dbFile.lastModified()
        val existing = pool[canonical]
        if (existing != null && existing.lastModified == lastMod && existing.db.isOpen) {
            return existing.db
        }
        return pool.compute(canonical) { _, prev ->
            if (prev != null && prev.lastModified == lastMod && prev.db.isOpen) {
                prev
            } else {
                prev?.db?.runCatching { close() }
                val flags = SQLiteDatabase.OPEN_READONLY or SQLiteDatabase.NO_LOCALIZED_COLLATORS
                val opened = SQLiteDatabase.openDatabase(canonical, null, flags).apply {
                    execSQL("PRAGMA query_only = ON;")
                    execSQL("PRAGMA temp_store = MEMORY;")
                    execSQL("PRAGMA mmap_size = 16777216;")
                }
                PoolEntry(canonical, lastMod, opened)
            }
        }!!.db
    }

    private fun Cursor.toRows(): List<Map<String, Any?>> {
        val out = mutableListOf<Map<String, Any?>>()
        while (moveToNext()) {
            val row = mutableMapOf<String, Any?>()
            for (i in 0 until columnCount) {
                row[getColumnName(i)] = when (getType(i)) {
                    Cursor.FIELD_TYPE_NULL -> null
                    Cursor.FIELD_TYPE_INTEGER -> getLong(i)
                    Cursor.FIELD_TYPE_FLOAT -> getDouble(i)
                    Cursor.FIELD_TYPE_BLOB -> getBlob(i)
                    else -> getString(i)
                }
            }
            out += row
        }
        return out
    }

    override fun close() = lock.write {
        pool.values.forEach { it.db.runCatching { close() } }
        pool.clear()
    }
}
