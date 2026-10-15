package com.trueway.app.vision

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import java.io.File

/**
 * Capture → embed → rank → decide orchestration (blueprint §7.4 pipeline).
 * Runs fully offline on a background thread; every failure degrades to an
 * explicit state, never to a forced identity. Model/pack dim mismatch is
 * refused outright (pack manifest `vision` contract, ADR-0003).
 */
sealed interface ScanOutcome {
    /** No encoder asset (or it failed to init): search/QR only. */
    data object NoModel : ScanOutcome

    /** No reference vectors installed: outside downloaded coverage. */
    data object NoIndex : ScanOutcome

    /** Refs present but no learned calibration: names must NOT be shown. */
    data object Uncalibrated : ScanOutcome

    /** Photo undecodable or embed failed on-device. */
    data object ProcessError : ScanOutcome

    data class Decided(
        val decision: RankDecision,
        val provenance: ScanProvenance,
    ) : ScanOutcome
}

/**
 * QA provenance recorded WITH every decided scan (Epic SCAN acceptance /
 * §28.5): which model + pack produced the answer and how it was derived.
 * Internal diagnostics only — never shown as user-facing certainty.
 */
data class ScanProvenance(
    val modelId: String?,
    val packId: String?,
    val evidenceKind: EvidenceKind,
)

fun runScanBlocking(appContext: Context, file: File, maxSidePx: Int = 512): ScanOutcome {
    val store = com.trueway.app.pack.PrefsActivePackStore(appContext)
    val activePacks = store.allActive().ifEmpty {
        store.getActive("in-bihar-buddhist-circuit")?.let { mapOf("in-bihar-buddhist-circuit" to it) } ?: emptyMap()
    }
    val packsDir = File(appContext.filesDir, "packs")
    val activePackDir = activePacks.entries.firstOrNull()?.let { (pid, ver) ->
        File(File(packsDir, pid), ver)
    }
    val binaryIndex = ReferenceStore.loadBinaryIfPresent(activePackDir)
    val jsonIndex = if (binaryIndex == null) ReferenceStore.load(appContext) else null

    if (binaryIndex == null && jsonIndex is ReferenceIndex.Empty) return ScanOutcome.NoIndex

    val embedder = MediaPipeEmbedder(appContext)
    if (embedder.state != MediaPipeEmbedder.State.Ready) {
        embedder.close()
        return ScanOutcome.NoModel
    }
    try {
        val bitmap = decodeBoundedWithRotation(file, maxSidePx) ?: return ScanOutcome.ProcessError
        val query = embedder.embed(bitmap) ?: return ScanOutcome.ProcessError

        if (binaryIndex != null) {
            if (query.size != binaryIndex.dim) return ScanOutcome.ProcessError
            val scanOutcome = binaryIndex.evaluate(query, SiblingCalibrationPolicy())
            val decision = when (scanOutcome) {
                is CalibratedScanOutcome.Identified -> {
                    val placeScore = PlaceScore(
                        placeId = scanOutcome.placeId,
                        score = scanOutcome.score.toDouble(),
                        margin = 0.05,
                        supporters = 1
                    )
                    val runnerUpScore = scanOutcome.runnerUpPlaceId?.let {
                        listOf(PlaceScore(it, (scanOutcome.score - 0.05).toDouble(), 0.0, 1))
                    } ?: emptyList()
                    RankDecision.Accepted(placeScore, runnerUpScore)
                }
                is CalibratedScanOutcome.AmbiguousSiblingPair -> {
                    val primaryScore = PlaceScore(
                        placeId = scanOutcome.primaryPlaceId,
                        score = 0.75,
                        margin = scanOutcome.scoreDelta.toDouble(),
                        supporters = 1
                    )
                    val secondaryScore = PlaceScore(
                        placeId = scanOutcome.secondaryPlaceId,
                        score = (0.75 - scanOutcome.scoreDelta).toDouble(),
                        margin = 0.0,
                        supporters = 1
                    )
                    RankDecision.Uncertain(
                        reason = UnknownReason.AMBIGUOUS_LOOKALIKES,
                        alternatives = listOf(primaryScore, secondaryScore)
                    )
                }
                is CalibratedScanOutcome.AbstainUnknown -> {
                    val placeScore = if (scanOutcome.topRawScore > 0f) {
                        listOf(PlaceScore("unknown", scanOutcome.topRawScore.toDouble(), 0.0, 1))
                    } else emptyList()
                    RankDecision.Uncertain(
                        reason = UnknownReason.LOW_SCORE,
                        alternatives = placeScore
                    )
                }
            }
            return ScanOutcome.Decided(
                decision,
                ScanProvenance(
                    modelId = "mobileclip-s0",
                    packId = activePacks.keys.firstOrNull(),
                    evidenceKind = EvidenceKind.VISION_RANKING,
                )
            )
        }

        val index = jsonIndex!!
        val refs = (index as? ReferenceIndex.Ready)?.refs
            ?: (index as ReferenceIndex.Uncalibrated).refs
        if (refs.isEmpty() || query.size != refs[0].values.size) return ScanOutcome.ProcessError
        if (index !is ReferenceIndex.Ready) return ScanOutcome.Uncalibrated
        val ranked = RetrievalEngine.rank(query, refs)
        val scores = RetrievalEngine.aggregateByPlace(ranked)
        return ScanOutcome.Decided(
            RetrievalEngine.decide(scores, index.calibration.acceptThreshold, index.calibration.minMargin),
            ScanProvenance(
                modelId = index.modelId,
                packId = index.packId,
                evidenceKind = EvidenceKind.VISION_RANKING,
            ),
        )
    } finally {
        embedder.close()
    }
}

/** Downsampled decode with EXIF orientation applied (§7.4 normalization). */
internal fun decodeBoundedWithRotation(file: File, maxSidePx: Int): Bitmap? {
    return try {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(file.absolutePath, bounds)
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null
        var sample = 1
        while (bounds.outWidth / sample > maxSidePx || bounds.outHeight / sample > maxSidePx) sample *= 2
        val opts = BitmapFactory.Options().apply { inSampleSize = sample }
        var bmp = BitmapFactory.decodeFile(file.absolutePath, opts) ?: return null
        val exif = ExifInterface(file.absolutePath)
        val deg = when (exif.getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL)) {
            ExifInterface.ORIENTATION_ROTATE_90 -> 90f
            ExifInterface.ORIENTATION_ROTATE_180 -> 180f
            ExifInterface.ORIENTATION_ROTATE_270 -> 270f
            else -> 0f
        }
        if (deg != 0f) {
            val m = Matrix().apply { postRotate(deg) }
            Bitmap.createBitmap(bmp, 0, 0, bmp.width, bmp.height, m, true).also { bmp.recycle() }
        } else {
            bmp
        }
    } catch (_: Exception) {
        null
    }
}
