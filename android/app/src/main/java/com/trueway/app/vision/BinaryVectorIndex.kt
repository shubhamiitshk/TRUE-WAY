package com.trueway.app.vision

import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.roundToInt
import kotlin.math.sqrt

data class PrototypeRecord(
    val placeId: String,
    val parentPlaceId: String?,
    val viewpointTag: String,
    val distinguishingHint: String
)

data class SiblingCalibrationPolicy(
    val absThreshold: Float = 0.72f,
    val hardNegativeMargin: Float = 0.06f,
    val siblingMargin: Float = 0.04f
)

sealed interface CalibratedScanOutcome {
    data class Identified(
        val placeId: String,
        val score: Float,
        val runnerUpPlaceId: String?,
        val distinguishingHint: String
    ) : CalibratedScanOutcome

    data class AmbiguousSiblingPair(
        val parentPlaceId: String,
        val primaryPlaceId: String,
        val primaryHint: String,
        val secondaryPlaceId: String,
        val secondaryHint: String,
        val scoreDelta: Float
    ) : CalibratedScanOutcome

    data class AbstainUnknown(
        val reason: String,
        val topRawScore: Float,
        val maxNegativeScore: Float
    ) : CalibratedScanOutcome
}

class BinaryVectorIndex(
    private val buffer: ByteBuffer,
    val dim: Int,
    val numPrototypes: Int,
    val numNegatives: Int,
    private val prototypes: List<PrototypeRecord>
) {
    private val posOffset = 32
    private val negOffset = 32 + numPrototypes * dim

    fun evaluate(queryFloatVec: FloatArray, policy: SiblingCalibrationPolicy): CalibratedScanOutcome {
        require(queryFloatVec.size == dim) { "Expected dim=$dim, got ${queryFloatVec.size}" }
        val qInt8 = quantizeL2Int8(queryFloatVec)
        val denom = 127.0f * 127.0f

        var maxNegScore = -1.0f
        for (n in 0 until numNegatives) {
            val base = negOffset + n * dim
            var dot = 0
            for (d in 0 until dim) {
                dot += buffer.get(base + d).toInt() * qInt8[d].toInt()
            }
            val sim = dot / denom
            if (sim > maxNegScore) maxNegScore = sim
        }

        val bestByPlace = HashMap<String, Pair<Float, PrototypeRecord>>()
        for (p in 0 until numPrototypes) {
            val base = posOffset + p * dim
            var dot = 0
            for (d in 0 until dim) {
                dot += buffer.get(base + d).toInt() * qInt8[d].toInt()
            }
            val sim = dot / denom
            val meta = prototypes[p]
            val prev = bestByPlace[meta.placeId]
            if (prev == null || sim > prev.first) {
                bestByPlace[meta.placeId] = sim to meta
            }
        }

        val ranked = bestByPlace.values.sortedByDescending { it.first }
        if (ranked.isEmpty()) {
            return CalibratedScanOutcome.AbstainUnknown("NO_CANDIDATES", 0f, maxNegScore)
        }

        val (s1, m1) = ranked[0]
        val (s2, m2) = if (ranked.size > 1) ranked[1] else (-1.0f to m1)

        if (s1 - maxNegScore < policy.hardNegativeMargin) {
            return CalibratedScanOutcome.AbstainUnknown("MATCHED_HARD_NEGATIVE_CENTROID", s1, maxNegScore)
        }
        if (s1 < policy.absThreshold) {
            return CalibratedScanOutcome.AbstainUnknown("BELOW_ABSOLUTE_THRESHOLD", s1, maxNegScore)
        }
        if (ranked.size > 1 && (s1 - s2) < policy.siblingMargin) {
            if (m1.parentPlaceId != null && m1.parentPlaceId == m2.parentPlaceId) {
                return CalibratedScanOutcome.AmbiguousSiblingPair(
                    parentPlaceId = m1.parentPlaceId,
                    primaryPlaceId = m1.placeId,
                    primaryHint = m1.distinguishingHint,
                    secondaryPlaceId = m2.placeId,
                    secondaryHint = m2.distinguishingHint,
                    scoreDelta = s1 - s2
                )
            }
            return CalibratedScanOutcome.AbstainUnknown("AMBIGUOUS_NON_SIBLING_MARGIN", s1, maxNegScore)
        }

        return CalibratedScanOutcome.Identified(
            placeId = m1.placeId,
            score = s1,
            runnerUpPlaceId = if (ranked.size > 1) m2.placeId else null,
            distinguishingHint = m1.distinguishingHint
        )
    }

    private fun quantizeL2Int8(vec: FloatArray): ByteArray {
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

    companion object {
        fun mmapReadOnly(binFile: File, prototypes: List<PrototypeRecord>): BinaryVectorIndex {
            RandomAccessFile(binFile, "r").use { raf ->
                val mapped = raf.channel.map(
                    java.nio.channels.FileChannel.MapMode.READ_ONLY,
                    0,
                    raf.length()
                ).order(ByteOrder.LITTLE_ENDIAN)

                val magicBytes = ByteArray(8)
                mapped.get(magicBytes)
                val magic = String(magicBytes, Charsets.US_ASCII)
                val version = mapped.int
                require(magic == "TWVEC001" && version == 1) {
                    "Unsupported binary vector index header: $magic v=$version"
                }
                val modelCrc = mapped.int
                val dim = mapped.int
                val numPos = mapped.int
                val numNeg = mapped.int
                return BinaryVectorIndex(mapped, dim, numPos, numNeg, prototypes)
            }
        }
    }
}
