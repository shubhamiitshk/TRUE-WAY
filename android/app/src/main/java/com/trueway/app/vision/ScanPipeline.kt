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
 *
 * What this pipeline now does that it did not before:
 *  1. **Honours the pack's learned calibration.** The decision gate used to be
 *     three hard-coded Kotlin constants; the pack has always shipped a
 *     `calibration` block that was silently ignored.
 *  2. **Scores relatively, not absolutely.** The gate is
 *     `winner − max(second-best place, best hard negative)` against a learned
 *     threshold, not a raw cosine against a magic number. An absolute cosine
 *     moves with the encoder, the quantisation, the input resolution and the
 *     number of prototypes; a relative score does not
 *     (Miller et al., ECCV 2024, arXiv:2403.16528).
 *  3. **Uses test-time augmentation** — the query is embedded twice (image and
 *     horizontal mirror), the two L2-normalised embeddings are averaged and
 *     re-normalised (MeTTA, NeurIPS 2021, arXiv:2106.08038). Deliberately
 *     flip-only: crop / brightness / blur / rotate are the transforms the
 *     TRAINING set was synthesised from, so using them at test time would
 *     flatter the benchmark without adding genuine invariance.
 *  4. **Applies the geographic prior as a soft re-ranker**, never as a gate.
 *  5. **Reuses one encoder** for the process instead of reloading 12 MB per
 *     capture.
 *  6. **Reports measured margins.** The runner-up score used to be fabricated
 *     as `score − 0.05`.
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
    /** "VISION" or "VISION+GPS" — whether the answer leaned on the geo prior. */
    val evidenceSource: String = "VISION",
    /** Where the decision thresholds came from: "pack" or "default". */
    val calibrationSource: String = "pack",
    /** Calibrated P(correct) for QA only; never rendered as a user-facing %. */
    val probabilityCorrect: Double = Double.NaN,
)

fun runScanBlocking(
    appContext: Context,
    file: File,
    maxSidePx: Int = 1024,
    preferGpu: Boolean = false,
): ScanOutcome {
    val store = com.trueway.app.pack.PrefsActivePackStore(appContext)
    val activePacks = store.allActive().ifEmpty {
        store.getActive("in-bihar-buddhist-circuit")?.let { mapOf("in-bihar-buddhist-circuit" to it) } ?: emptyMap()
    }
    val packsDir = File(appContext.filesDir, "packs")
    val activePackDir = activePacks.entries.firstOrNull()?.let { (pid, ver) ->
        File(File(packsDir, pid), ver)
    }
    val loaded = ReferenceStore.loadBinaryIfPresent(activePackDir)
    val jsonIndex = if (loaded == null) ReferenceStore.load(appContext) else null

    if (loaded == null && jsonIndex is ReferenceIndex.Empty) return ScanOutcome.NoIndex

    // The pack's calibration is the source of truth. Without it we may still
    // RANK for diagnostics, but we must not present a name (§3 principle 2).
    val calibration: VisionCalibration? = loaded?.meta?.calibration
    if (loaded != null && calibration == null) return ScanOutcome.Uncalibrated

    val bitmap = decodeBoundedWithRotation(file, maxSidePx) ?: return ScanOutcome.ProcessError

    val embedding = VisionEncoder.withEncoder(appContext, preferGpu) { encoder ->
        embedWithFlipTta(encoder, bitmap)
    } ?: return ScanOutcome.ProcessError

    if (loaded != null) {
        val policy = SiblingCalibrationPolicy.from(calibration)
        val prior = DeviceLocationProvider.priorFor(appContext)
        val distances = placeDistancesKm(appContext, prior)
        val outcome = loaded.index.evaluate(embedding, policy, prior, distances)
        val provenance = ScanProvenance(
            modelId = loaded.meta.modelId ?: "mobileclip-s0",
            packId = activePacks.keys.firstOrNull(),
            evidenceKind = EvidenceKind.VISION_RANKING,
            evidenceSource = DeviceLocationProvider.evidenceLabel(prior),
            calibrationSource = policy.source,
            probabilityCorrect = probabilityOf(calibration, outcome),
        )
        return ScanOutcome.Decided(toRankDecision(outcome), provenance)
    }

    // ---- legacy JSON reference path -------------------------------------------
    val index = jsonIndex!!
    val refs = (index as? ReferenceIndex.Ready)?.refs
        ?: (index as ReferenceIndex.Uncalibrated).refs
    if (refs.isEmpty() || embedding.size != refs[0].values.size) return ScanOutcome.ProcessError
    if (index !is ReferenceIndex.Ready) return ScanOutcome.Uncalibrated
    val ranked = RetrievalEngine.rank(embedding, refs)
    val scores = RetrievalEngine.aggregateByPlace(ranked)
    val decision = RetrievalEngine.decide(scores, index.calibration.acceptThreshold, index.calibration.minMargin)
    return ScanOutcome.Decided(
        decision,
        ScanProvenance(
            modelId = index.modelId,
            packId = activePacks.keys.firstOrNull(),
            evidenceKind = EvidenceKind.VISION_RANKING,
            calibrationSource = "pack-json",
        ),
    )
}

/**
 * Flip-only test-time augmentation (MeTTA): embed the image and its mirror,
 * average the two L2-normalised embeddings, re-normalise.
 */
private fun embedWithFlipTta(encoder: MediaPipeEmbedder, bitmap: Bitmap): FloatArray? {
    val a = encoder.embed(bitmap) ?: return null
    val mirrored = try {
        val m = Matrix().apply { postScale(-1f, 1f) }
        Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, m, true)
    } catch (_: Exception) {
        null
    }
    if (mirrored == null) return a
    val b = encoder.embed(mirrored) ?: return a
    if (b.size != a.size) return a
    val out = FloatArray(a.size)
    for (i in a.indices) {
        val na = a[i] / norm(a)
        val nb = b[i] / norm(b)
        out[i] = na + nb
    }
    val n = norm(out)
    if (n <= 0f) return a
    for (i in out.indices) out[i] = out[i] / n
    return out
}

private fun norm(v: FloatArray): Float {
    var s = 0.0
    for (x in v) s += x * x
    return if (s > 0.0) kotlin.math.sqrt(s).toFloat() else 1f
}

/** Distance from the device fix to each place, in km. Empty when no fix. */
private fun placeDistancesKm(context: Context, prior: GeoPrior): Map<String, Double> {
    if (prior.lambda <= 0.0) return emptyMap()
    val loc = DeviceLocationProvider.lastKnown(context) ?: return emptyMap()
    val out = HashMap<String, Double>()
    for (place in com.trueway.app.data.PlaceRepository.all()) {
        val lat = place.latitude ?: continue
        val lon = place.longitude ?: continue
        out[place.placeId] = GeoDistance.km(loc.latitude, loc.longitude, lat, lon)
    }
    return out
}

private fun probabilityOf(calibration: VisionCalibration?, outcome: CalibratedScanOutcome): Double {
    if (calibration == null) return Double.NaN
    val rel = when (outcome) {
        is CalibratedScanOutcome.Identified -> outcome.relativeScore.toDouble()
        else -> return Double.NaN
    }
    return calibration.probabilityOfCorrect(rel)
}

/** Maps the binary-index outcome onto the app-level decision contract (§28.5). */
internal fun toRankDecision(outcome: CalibratedScanOutcome): RankDecision {
    return when (outcome) {
        is CalibratedScanOutcome.Identified -> {
            val placeScore = PlaceScore(
                placeId = outcome.placeId,
                score = outcome.score.toDouble(),
                margin = outcome.relativeScore.toDouble(),
                supporters = 1,
                distinguishingHint = outcome.distinguishingHint.ifBlank { null },
            )
            val runnerUp = outcome.runnerUpPlaceId?.let {
                listOf(PlaceScore(it, outcome.runnerUpScore.toDouble(), 0.0, 1))
            } ?: emptyList()
            RankDecision.Accepted(placeScore, runnerUp)
        }
        is CalibratedScanOutcome.AmbiguousSiblingPair -> {
            val primary = PlaceScore(
                placeId = outcome.primaryPlaceId,
                score = 0.0,
                margin = outcome.scoreDelta.toDouble(),
                supporters = 1,
                distinguishingHint = outcome.primaryHint.ifBlank { null },
            )
            val secondary = PlaceScore(
                placeId = outcome.secondaryPlaceId,
                score = 0.0,
                margin = 0.0,
                supporters = 1,
                distinguishingHint = outcome.secondaryHint.ifBlank { null },
            )
            RankDecision.Uncertain(
                reason = UnknownReason.AMBIGUOUS_LOOKALIKES,
                alternatives = listOf(primary, secondary),
            )
        }
        is CalibratedScanOutcome.AbstainUnknown -> {
            val alternatives = outcome.bestPlaceId?.let {
                listOf(PlaceScore(it, outcome.topRawScore.toDouble(), 0.0, 1))
            } ?: emptyList()
            RankDecision.Uncertain(UnknownReason.LOW_SCORE, alternatives)
        }
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
