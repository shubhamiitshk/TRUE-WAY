package com.trueway.app.vision

import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.roundToInt
import kotlin.math.sqrt

/**
 * One place inside the binary reference index.
 *
 * A place owns a RANGE of gallery vectors (`prototypeStart .. +count`), not a
 * single vector. The blueprint (§7.2, §7.5) requires "at least 10–20
 * independently sourced viewpoints" per POI and a "robust top-2 mean" over a
 * place's reference similarities. Shipping one blended centroid per place —
 * as the previous TWVEC001 index did — makes that aggregation impossible and
 * silently turns the score into a single-centroid cosine.
 */
data class PrototypeRecord(
    val placeId: String,
    val parentPlaceId: String?,
    val viewpointTag: String,
    val distinguishingHint: String,
    val prototypeStart: Int = 0,
    val prototypeCount: Int = 1,
)

/**
 * Per-place reference ranges plus the negative bank, as read from the index
 * metadata. [calibration] is the pack's learned decision calibration; a null
 * value means the pack carries none and the scanner must not present names.
 */
data class VectorIndexMeta(
    val places: List<PrototypeRecord>,
    val negativeLabels: List<String> = emptyList(),
    val calibration: VisionCalibration? = null,
    val modelId: String? = null,
    val modelSha256: String? = null,
    /**
     * The CSLS neighbourhood size: the number of nearest neighbours used to
     * estimate the local density of a gallery vector. 10 is the value the
     * CSLS paper reports as insensitive.
     */
    val localScaleK: Int = 10,
    /** How many local-scale values the binary index carries (0 = none). */
    val localScaleCount: Int = 0,
)

/**
 * The decision gate inputs, all LEARNED on the held-out calibration split and
 * shipped in the pack. [source] records where the values came from so QA can
 * tell a pack-calibrated decision from a defaulted one.
 */
data class SiblingCalibrationPolicy(
    val absThreshold: Float,
    val hardNegativeMargin: Float,
    val siblingMargin: Float,
    val relativeThreshold: Float,
    val minMargin: Float,
    val topKMean: Int,
    /** Margin below which a RELATED pair (parent/child or siblings) is reported
     *  as an ambiguous pair rather than forced onto one of them. */
    val relatedMargin: Float = 0f,
    /** The CSLS neighbourhood size (the local-density estimator). */
    val cslsK: Int = 10,
    val source: String = "pack",
) {
    companion object {
        /**
         * Fallback used only when a pack carries no calibration. It is marked
         * `source = "default"`; a pack without calibration is reported as
         * UNCALIBRATED upstream and never used to present a name.
         */
        val DEFAULT = SiblingCalibrationPolicy(
            absThreshold = 0.72f,
            hardNegativeMargin = 0.06f,
            siblingMargin = 0.04f,
            relativeThreshold = 0.12f,
            minMargin = 0.05f,
            topKMean = 2,
            relatedMargin = 0f,
            source = "default",
        )

        fun from(calibration: VisionCalibration?): SiblingCalibrationPolicy {
            if (calibration == null) return DEFAULT
            return SiblingCalibrationPolicy(
                absThreshold = calibration.acceptThreshold.toFloat(),
                hardNegativeMargin = calibration.hardNegativeMargin.toFloat(),
                siblingMargin = calibration.siblingMargin.toFloat(),
                relativeThreshold = calibration.relativeThreshold.toFloat(),
                minMargin = calibration.minMargin.toFloat(),
                topKMean = calibration.topKMean,
                relatedMargin = calibration.relatedMargin.toFloat(),
                cslsK = calibration.cslsK,
                source = calibration.source,
            )
        }
    }
}

sealed interface CalibratedScanOutcome {
    data class Identified(
        val placeId: String,
        val score: Float,
        val runnerUpPlaceId: String?,
        val distinguishingHint: String,
        /** Visual-only score of the winner (before any geo prior). */
        val visualScore: Float = score,
        /** Winner score minus the best hard negative — the OPEN-SET margin. */
        val relativeScore: Float = 0f,
        /** Measured score of the runner-up — never a fabricated number. */
        val runnerUpScore: Float = 0f,
        /** Calibrated P(correct) for QA provenance; never shown to users. */
        val probabilityCorrect: Double = Double.NaN,
        /** Best hard-negative similarity, for QA provenance. */
        val maxNegativeScore: Float = 0f,
    ) : CalibratedScanOutcome {
        fun maxNegativeScoreOf(): Float = maxNegativeScore
    }

    data class AmbiguousSiblingPair(
        val parentPlaceId: String,
        val primaryPlaceId: String,
        val primaryHint: String,
        val secondaryPlaceId: String,
        val secondaryHint: String,
        val scoreDelta: Float,
    ) : CalibratedScanOutcome

    data class AbstainUnknown(
        val reason: String,
        val topRawScore: Float,
        val maxNegativeScore: Float,
        val relativeScore: Float = 0f,
        val bestPlaceId: String? = null,
    ) : CalibratedScanOutcome
}

/**
 * Zero-copy reference index.
 *
 * Storage is **float32** rather than INT8. The gallery is tiny — 15 places ×
 * 30 references × 512 dims × 4 B ≈ 0.9 MB — so quantising it saves nothing
 * meaningful inside a 100 MB APK while adding a SECOND quantisation error on
 * top of the encoder's own, on top of an asymmetric per-tensor rounding of
 * unit-norm vectors. The query path quantises nothing.
 *
 * TWVEC001 (INT8, one vector per place) is still readable so existing
 * installed packs keep working; TWVEC002 is what the pack builder emits.
 */
class BinaryVectorIndex(
    private val buffer: ByteBuffer,
    val dim: Int,
    val numPrototypes: Int,
    val numNegatives: Int,
    private val prototypes: List<PrototypeRecord>,
    val numPlaces: Int = prototypes.size,
    val storage: Storage = Storage.FLOAT32,
    /**
     * The offset (in float32 elements) of the CSLS LOCAL SCALE section, or -1
     * when the index carries none. The section holds one float32 per gallery
     * vector - the place references first, then the negative bank - giving
     * r_k(v), the mean cosine of v to its k nearest neighbours.
     */
    private val localScaleOffset: Int = -1,
) {
    enum class Storage { FLOAT32, INT8 }

    /** TWVEC002 header is 40 bytes (8-byte aligned); TWVEC001 is 32. */
    private val posOffset = if (storage == Storage.FLOAT32) 40 else 32
    private val negOffset = posOffset + numPrototypes * dim * storage.bytesPerValue()
    private val hasLocalScale = localScaleOffset >= 0

    /** r_k(v) for a gallery vector: `index` counts the place references first,
     *  then the negative bank. */
    private fun localScaleAt(index: Int): Float {
        if (!hasLocalScale) return 0f
        val off = (localScaleOffset + index) * 4
        return buffer.getFloat(off)
    }

    fun evaluate(
        queryFloatVec: FloatArray,
        policy: SiblingCalibrationPolicy,
        geoPrior: GeoPrior = GeoPrior.DISABLED,
        placeDistancesKm: Map<String, Double> = emptyMap(),
    ): CalibratedScanOutcome {
        require(queryFloatVec.size == dim) { "Expected dim=$dim, got ${queryFloatVec.size}" }
        val q = l2Normalize(queryFloatVec)

        // ---- the raw similarity to every gallery vector ------------------------
        val rawPos = FloatArray(numPrototypes)
        for (i in 0 until numPrototypes) rawPos[i] = similarityTo(i, q, posOffset)
        val rawNeg = FloatArray(numNegatives)
        for (n in 0 until numNegatives) rawNeg[n] = similarityTo(n, q, negOffset)

        // ---- CSLS: s'(q, v) = 2 s(q, v) - r_k(q) - r_k(v) ---------------------
        //
        // r_k(x) is the mean cosine of x to its k nearest neighbours in the
        // gallery. Subtracting it from both sides removes the HUBNESS of the
        // embedding space: a few gallery vectors are close to almost
        // everything, and those are exactly the ones that turn a lookalike
        // into a confident false accept.
        //
        // r_k(q) is computed here, at query time, from the whole gallery;
        // r_k(v) is SHIPPED in the index (it depends only on the gallery).
        val scaledPos = FloatArray(numPrototypes)
        val scaledNeg = FloatArray(numNegatives)
        if (hasLocalScale) {
            val pool = FloatArray(numPrototypes + numNegatives)
            System.arraycopy(rawPos, 0, pool, 0, numPrototypes)
            System.arraycopy(rawNeg, 0, pool, numPrototypes, numNegatives)
            val k = policy.cslsK.coerceIn(1, pool.size)
            val sorted = pool.sortedDescending()
            var acc = 0.0
            for (i in 0 until k) acc += sorted[i].toDouble()
            val rq = acc / k
            for (i in 0 until numPrototypes) {
                scaledPos[i] = (2.0 * rawPos[i].toDouble() - rq - localScaleAt(i).toDouble()).toFloat()
            }
            for (n in 0 until numNegatives) {
                scaledNeg[n] = (2.0 * rawNeg[n].toDouble() - rq - localScaleAt(numPrototypes + n).toDouble()).toFloat()
            }
        } else {
            System.arraycopy(rawPos, 0, scaledPos, 0, numPrototypes)
            System.arraycopy(rawNeg, 0, scaledNeg, 0, numNegatives)
        }

        // ---- negative bank ----------------------------------------------------
        var maxNegativeScore = -1.0f
        for (n in 0 until numNegatives) {
            val sim = scaledNeg[n]
            if (sim > maxNegativeScore) maxNegativeScore = sim
        }

        // ---- per-place score: robust top-k mean over that place's references --
        val visual = HashMap<String, PlaceScore>()
        for (p in prototypes) {
            val sims = ArrayList<Float>(p.prototypeCount)
            for (i in 0 until p.prototypeCount) {
                val idx = p.prototypeStart + i
                if (idx in 0 until numPrototypes) {
                    sims.add(scaledPos[idx])
                }
            }
            if (sims.isEmpty()) continue
            sims.sortDescending()
            val k = policy.topKMean.coerceIn(1, sims.size)
            var sum = 0.0
            for (i in 0 until k) sum += sims[i]
            val score = (sum / k).toFloat()
            val prev = visual[p.placeId]
            if (prev == null || score > prev.visualScore) {
                visual[p.placeId] = PlaceScore(
                    placeId = p.placeId,
                    visualScore = score,
                    fusedScore = score,
                    parentPlaceId = p.parentPlaceId,
                    hint = p.distinguishingHint,
                    viewpointTag = p.viewpointTag,
                )
            }
        }
        if (visual.isEmpty()) {
            return CalibratedScanOutcome.AbstainUnknown("NO_CANDIDATES", 0f, maxNegativeScore)
        }

        // ---- geo prior: re-rank only, never create an accept ------------------
        for (entry in visual.values) {
            val d = placeDistancesKm[entry.placeId]
            val fused = if (d == null) entry.visualScore
            else geoPrior.fuse(entry.visualScore.toDouble(), d).toFloat()
            visual[entry.placeId] = entry.copy(fusedScore = fused)
        }

        val ranked = visual.values.sortedByDescending { it.fusedScore }
        val first = ranked[0]
        val second = ranked.getOrNull(1)

        // TWO separate margins, because they answer two different questions:
        //   openMargin  — "is this one of our places, or an unknown?"  (vs the
        //                  strongest NON-MATCHING exemplar: the hard-negative bank)
        //   placeMargin — "which of our places?"  (vs the runner-up PLACE)
        // They must not be merged into one max(...) margin: the runner-up PLACE
        // is a DIFFERENT TRUE CLASS, so folding it into the open-set margin
        // penalises legitimate fine-grained confusions.
        val openMargin = first.fusedScore - maxNegativeScore
        val placeMargin = second?.let { first.fusedScore - it.fusedScore } ?: Float.MAX_VALUE

        if (first.visualScore < policy.absThreshold) {
            return CalibratedScanOutcome.AbstainUnknown(
                reason = "BELOW_ABSOLUTE_THRESHOLD",
                topRawScore = first.visualScore,
                maxNegativeScore = maxNegativeScore,
                relativeScore = openMargin,
                bestPlaceId = first.placeId,
            )
        }
        // `hardNegativeMargin` is the LEGACY name of the open-set gate. A
        // legacy pack shipped a POSITIVE margin there; a newly fitted
        // calibration sets it to 0 meaning "not used". Treat 0 as absent so a
        // fitted threshold of e.g. -0.44 is not silently tightened to 0.0.
        val openGate = if (policy.hardNegativeMargin > 0f) {
            maxOf(policy.relativeThreshold, policy.hardNegativeMargin)
        } else {
            policy.relativeThreshold
        }
        if (openMargin < openGate) {
            return CalibratedScanOutcome.AbstainUnknown(
                reason = "BELOW_RELATIVE_THRESHOLD",
                topRawScore = first.visualScore,
                maxNegativeScore = maxNegativeScore,
                relativeScore = openMargin,
                bestPlaceId = first.placeId,
            )
        }
        if (second != null && placeMargin < policy.siblingMargin) {
            if (areRelated(first.placeId, second.placeId, visual)) {
                val parent = first.parentPlaceId ?: second.parentPlaceId
                return CalibratedScanOutcome.AmbiguousSiblingPair(
                    parentPlaceId = parent ?: first.placeId,
                    primaryPlaceId = first.placeId,
                    primaryHint = first.hint,
                    secondaryPlaceId = second.placeId,
                    secondaryHint = second.hint,
                    scoreDelta = placeMargin,
                )
            }
            return CalibratedScanOutcome.AbstainUnknown(
                reason = "AMBIGUOUS_NON_SIBLING_MARGIN",
                topRawScore = first.visualScore,
                maxNegativeScore = maxNegativeScore,
                relativeScore = openMargin,
                bestPlaceId = first.placeId,
            )
        }
        if (second != null && policy.relatedMargin > 0f &&
            placeMargin < policy.relatedMargin &&
            areRelated(first.placeId, second.placeId, visual)
        ) {
            // A parent site and its child (or two siblings) that look alike:
            // report the PAIR rather than forcing one of them (§7.2).
            val parent = first.parentPlaceId ?: second.parentPlaceId
            return CalibratedScanOutcome.AmbiguousSiblingPair(
                parentPlaceId = parent ?: first.placeId,
                primaryPlaceId = first.placeId,
                primaryHint = first.hint,
                secondaryPlaceId = second.placeId,
                secondaryHint = second.hint,
                scoreDelta = placeMargin,
            )
        }

        return CalibratedScanOutcome.Identified(
            placeId = first.placeId,
            score = first.fusedScore,
            runnerUpPlaceId = second?.placeId,
            distinguishingHint = first.hint,
            visualScore = first.visualScore,
            relativeScore = openMargin,
            runnerUpScore = second?.fusedScore ?: 0f,
            maxNegativeScore = maxNegativeScore,
        )
    }

    private data class PlaceScore(
        val placeId: String,
        val visualScore: Float,
        val fusedScore: Float,
        val parentPlaceId: String?,
        val hint: String,
        val viewpointTag: String,
    )

    /**
     * Are two places the same site — siblings, or a parent and its child?
     *
     * Blueprint §7.2: "Separate parent sites from visually identifiable child
     * structures, to prevent inflated 'accuracy' from generic large-site names."
     * A photograph of the Nalanda site as a whole is genuinely not separable
     * from a photograph of Nalanda Monastery 1, so the two must be reported as
     * an AMBIGUOUS PAIR rather than one of them forced.
     */
    private fun areRelated(a: String, b: String, visual: Map<String, PlaceScore>): Boolean {
        val pa = visual[a]?.parentPlaceId
        val pb = visual[b]?.parentPlaceId
        if (pa != null && pa == pb) return true
        if (pa == b || pb == a) return true
        return false
    }

    private fun similarityTo(index: Int, q: FloatArray, base: Int): Float {
        return when (storage) {
            Storage.FLOAT32 -> {
                // Accumulate in DOUBLE, sequentially, in index order. The
                // workstation evaluator does the same, so the two produce
                // bit-identical results — a float32 accumulator with a
                // SIMD/reduction order difference flips knife-edge decisions.
                var dot = 0.0
                val off = base + index * dim * 4
                for (d in 0 until dim) {
                    dot += q[d].toDouble() * buffer.getFloat(off + d * 4).toDouble()
                }
                dot.toFloat()
            }
            Storage.INT8 -> {
                val qInt8 = quantizeInt8(q)
                var dot = 0
                val off = base + index * dim
                for (d in 0 until dim) dot += buffer.get(off + d).toInt() * qInt8[d].toInt()
                dot / (127.0f * 127.0f)
            }
        }
    }

    companion object {
        fun l2Normalize(vec: FloatArray): FloatArray {
            // Sequential DOUBLE accumulation, then divide in double and round
            // to float32 — the same order of operations as the workstation
            // evaluator (ml/vision_index.py), so both are bit-identical.
            var sumSq = 0.0
            for (v in vec) sumSq += v.toDouble() * v.toDouble()
            val n = if (sumSq > 0.0) kotlin.math.sqrt(sumSq) else 1.0
            val out = FloatArray(vec.size)
            for (i in vec.indices) out[i] = (vec[i].toDouble() / n).toFloat()
            return out
        }

        fun quantizeInt8(vec: FloatArray): ByteArray {
            var sumSq = 0.0f
            for (v in vec) sumSq += v * v
            val norm = if (sumSq > 0f) sqrt(sumSq) else 1.0f
            val out = ByteArray(vec.size)
            for (i in vec.indices) {
                val scaled = ((vec[i] / norm) * 127.0f).roundToInt().coerceIn(-127, 127)
                out[i] = scaled.toByte()
            }
            return out
        }

        fun Storage.bytesPerValue(): Int = if (this == Storage.FLOAT32) 4 else 1

        /**
         * Maps a binary index file to its metadata.
         *
         * TWVEC002 — float32 gallery, one or more references per place:
         *   magic "TWVEC002", version 2, model_crc, dim, num_pos, num_neg,
         *   num_places, flags(=1 float32)
         *
         * TWVEC001 — legacy INT8 gallery, one vector per place (still readable).
         */
        fun mmapReadOnly(binFile: File, meta: VectorIndexMeta): BinaryVectorIndex {
            RandomAccessFile(binFile, "r").use { raf ->
                val mapped = raf.channel.map(
                    java.nio.channels.FileChannel.MapMode.READ_ONLY,
                    0,
                    raf.length(),
                ).order(ByteOrder.LITTLE_ENDIAN)

                val magicBytes = ByteArray(8)
                mapped.get(magicBytes)
                val magic = String(magicBytes, Charsets.US_ASCII)
                val version = mapped.int
                require(magic == "TWVEC001" || magic == "TWVEC002") {
                    "Unsupported binary vector index header: $magic v=$version"
                }
                val modelCrc = mapped.int
                val dim = mapped.int
                val numPos = mapped.int
                val numNeg = mapped.int
                var flags = 0
                val storage = if (magic == "TWVEC002") {
                    val numPlaces = mapped.int
                    flags = mapped.int
                    mapped.int // reserved
                    require(numPlaces > 0) { "TWVEC002 header declares no places" }
                    require(flags and 1 == 1) { "TWVEC002 flags must declare float32 storage" }
                    Storage.FLOAT32
                } else {
                    mapped.int // reserved
                    Storage.INT8
                }
                // The CSLS local-scale section, when the header declares it
                // (flags bit 1): one float32 per gallery vector, the place
                // references first and then the negative bank.
                var scaleOffset = -1
                if (magic == "TWVEC002" && flags and 2 == 2) {
                    // The section starts right after the vectors, so its
                    // ABSOLUTE offset in float32 elements is the body end
                    // divided by four.
                    val bodyEnd = 40 + (numPos + numNeg) * dim * 4
                    scaleOffset = bodyEnd / 4
                }
                return BinaryVectorIndex(
                    buffer = mapped,
                    dim = dim,
                    numPrototypes = numPos,
                    numNegatives = numNeg,
                    prototypes = meta.places,
                    numPlaces = meta.places.size,
                    storage = storage,
                    localScaleOffset = scaleOffset,
                )
            }
        }
    }
}
