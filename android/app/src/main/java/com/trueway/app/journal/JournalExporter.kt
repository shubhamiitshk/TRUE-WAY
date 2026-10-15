package com.trueway.app.journal

import android.content.Context
import android.graphics.Color
import android.graphics.Paint
import android.graphics.pdf.PdfDocument
import com.trueway.app.data.PlaceRepository
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.time.Instant

/**
 * P1A Journal Exporter (blueprint v3.0 §3, §6, F114/F117).
 *
 * Implements privacy-preserving offline export:
 * - Selected entries only (never dumps entire database without user confirmation).
 * - Supported formats: Structured JSON and Android PDF Document.
 * - Explicit privacy controls: Zero raw GPS/EXIF attached by default; explicit notice that place names, timestamps, and notes reveal travel itineraries.
 */
object JournalExporter {

    const val FORMAT_VERSION = "trueway-journal-v1"
    const val PRIVACY_DISCLAIMER =
        "Personal travel journal export generated locally on device. While raw GPS coordinates and device identifiers are omitted by default, note that place names, place IDs, timestamps, and free-text notes inherently reveal personal itineraries and physical presence. Stored outside TrueWay sandbox; manage external file permissions carefully."

    /** Pure JSON formatter (JVM-testable). */
    fun exportToJson(entries: List<JournalEntry>): String {
        val root = JSONObject()
        root.put("format_version", FORMAT_VERSION)
        root.put("exported_at", Instant.now().toString())
        root.put("privacy_disclaimer", PRIVACY_DISCLAIMER)
        root.put("total_entries", entries.size)

        val array = JSONArray()
        for (entry in entries) {
            val item = JSONObject()
            item.put("entry_id", entry.entryId)
            item.put("place_id", entry.placeId ?: JSONObject.NULL)
            val place = entry.placeId?.let { PlaceRepository.get(it) }
            item.put("place_name", place?.canonicalName ?: "Unknown / Removed Place")
            item.put("created_at", entry.createdAt)
            item.put("user_note", entry.userNote ?: "")
            item.put("location_attached", entry.includeLocationOnExport == 1)
            array.put(item)
        }
        root.put("entries", array)
        return root.toString(2)
    }

    /** Clean Plaintext summary (for instant sharing via SMS/message). */
    fun exportToPlainText(entries: List<JournalEntry>): String = buildString {
        append("TRUEWAY PERSONAL TRAVEL JOURNAL\n")
        append("Exported: ${Instant.now()}\n")
        append("Entries: ${entries.size}\n")
        append("Notice: $PRIVACY_DISCLAIMER\n")
        append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
        entries.forEachIndexed { i, e ->
            val p = e.placeId?.let { PlaceRepository.get(it) }
            append("[${i + 1}] Date: ${e.createdAt.take(10)}\n")
            append("Place: ${p?.canonicalName ?: e.placeId ?: "Custom Entry"}\n")
            if (!e.userNote.isNullOrBlank()) {
                append("Note: ${e.userNote}\n")
            }
            append("------------------------------------\n")
        }
    }

    /** Generates a PDF file in context cache using Android's built-in PdfDocument API. */
    fun exportToPdf(context: Context, entries: List<JournalEntry>): File {
        val pdfDocument = PdfDocument()
        val entriesPerPage = 10
        val pages = if (entries.isEmpty()) listOf(emptyList()) else entries.chunked(entriesPerPage)

        val titlePaint = Paint().apply {
            color = Color.DKGRAY
            textSize = 18f
            isFakeBoldText = true
        }

        val subtitlePaint = Paint().apply {
            color = Color.GRAY
            textSize = 10f
        }

        val bodyPaint = Paint().apply {
            color = Color.BLACK
            textSize = 11f
        }

        val boxPaint = Paint().apply {
            color = Color.LTGRAY
            style = Paint.Style.STROKE
            strokeWidth = 1f
        }

        for ((pageIndex, pageEntries) in pages.withIndex()) {
            val pageNumber = pageIndex + 1
            val pageInfo = PdfDocument.PageInfo.Builder(595, 842, pageNumber).create() // A4 portrait in points
            val page = pdfDocument.startPage(pageInfo)
            val canvas = page.canvas

            var y = 50f
            canvas.drawText("TRUEWAY PERSONAL TRAVEL JOURNAL", 40f, y, titlePaint)
            y += 18f
            canvas.drawText("Exported: ${Instant.now()} | Total Selected Entries: ${entries.size} | Page $pageNumber of ${pages.size}", 40f, y, subtitlePaint)
            y += 14f
            canvas.drawText("No raw GPS/EXIF attached. Note: Place names & timestamps reflect travel itineraries.", 40f, y, subtitlePaint)
            y += 25f

            val startIndex = pageIndex * entriesPerPage
            for ((itemIndex, entry) in pageEntries.withIndex()) {
                val overallIndex = startIndex + itemIndex
                val place = entry.placeId?.let { PlaceRepository.get(it) }
                val placeName = place?.canonicalName ?: entry.placeId ?: "Heritage Visit"

                canvas.drawRect(40f, y, 555f, y + 55f, boxPaint)
                canvas.drawText("${overallIndex + 1}. $placeName", 50f, y + 18f, titlePaint.apply { textSize = 13f })
                canvas.drawText("Date: ${entry.createdAt.take(10)}", 430f, y + 18f, subtitlePaint)

                val note = entry.userNote?.take(80) ?: "No personal note recorded."
                canvas.drawText(note, 50f, y + 38f, bodyPaint)

                y += 65f
                if (y > 780f) break
            }

            pdfDocument.finishPage(page)
        }

        pruneOldExports(context)
        val outputFile = File(context.cacheDir, "trueway-journal-export-${System.currentTimeMillis()}.pdf")
        FileOutputStream(outputFile).use { out ->
            pdfDocument.writeTo(out)
        }
        pdfDocument.close()
        return outputFile
    }

    /**
     * Writes JSON export to context.cacheDir and automatically prunes stale exports.
     */
    fun exportToJsonFile(context: Context, entries: List<JournalEntry>): File {
        pruneOldExports(context)
        val outputFile = File(context.cacheDir, "trueway-journal-export-${System.currentTimeMillis()}.json")
        outputFile.writeText(exportToJson(entries))
        return outputFile
    }

    /**
     * Purges temporary exported journal files from context.cacheDir older than [maxAgeHours].
     * Returns the count of deleted files.
     */
    fun pruneOldExports(context: Context, maxAgeHours: Long = 24): Int {
        val dir = context.cacheDir ?: return 0
        return pruneOldExports(dir, maxAgeHours)
    }

    /** Overload accepting [File] directory directly for deterministic JVM unit testing. */
    fun pruneOldExports(cacheDir: File, maxAgeHours: Long = 24): Int {
        val cutoff = System.currentTimeMillis() - (maxAgeHours * 3600 * 1000)
        val files = cacheDir.listFiles { file ->
            file.isFile && file.name.startsWith("trueway-journal-export-") &&
                (file.name.endsWith(".pdf") || file.name.endsWith(".json") || file.name.endsWith(".txt"))
        } ?: return 0

        var deletedCount = 0
        for (f in files) {
            if (f.lastModified() < cutoff) {
                if (f.delete()) {
                    deletedCount++
                }
            }
        }
        return deletedCount
    }
}
