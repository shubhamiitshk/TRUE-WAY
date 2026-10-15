package com.trueway.app.vision

import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test

class BinaryVectorIndexTest {

    private val dim = 4
    private lateinit var prototypes: List<PrototypeRecord>

    @Before
    fun setUp() {
        prototypes = listOf(
            PrototypeRecord(
                placeId = "nalanda-temple-3",
                parentPlaceId = "nalanda-ruins",
                viewpointTag = "corner-tower",
                distinguishingHint = "Stucco votive stupas flanking stairs"
            ),
            PrototypeRecord(
                placeId = "nalanda-monastery-1",
                parentPlaceId = "nalanda-ruins",
                viewpointTag = "cells-quad",
                distinguishingHint = "Multi-level monks cells around courtyard"
            ),
            PrototypeRecord(
                placeId = "mahabodhi-temple",
                parentPlaceId = null,
                viewpointTag = "central-shikhara",
                distinguishingHint = "55-meter stepped pyramidal spire"
            )
        )
    }

    private fun createIndexBuffer(
        posVectors: List<ByteArray>,
        negVectors: List<ByteArray>
    ): ByteBuffer {
        val totalBytes = 32 + (posVectors.size + negVectors.size) * dim
        val buffer = ByteBuffer.allocate(totalBytes).order(ByteOrder.LITTLE_ENDIAN)

        // Header (32 bytes)
        buffer.put("TWVEC001".toByteArray(Charsets.US_ASCII)) // 8 bytes
        buffer.putInt(1) // version = 1 (4 bytes)
        buffer.putInt(0x12345678) // modelCrc (4 bytes)
        buffer.putInt(dim) // dim = 4 (4 bytes)
        buffer.putInt(posVectors.size) // numPos (4 bytes)
        buffer.putInt(negVectors.size) // numNeg (4 bytes)
        buffer.putInt(0) // reserved/padding to reach 32 bytes (4 bytes)

        // Positive prototypes
        for (v in posVectors) {
            buffer.put(v)
        }
        // Negative prototypes
        for (v in negVectors) {
            buffer.put(v)
        }
        buffer.flip()
        return buffer
    }

    @Test
    fun `identifies matching prototype above threshold and margins`() {
        val posVecs = listOf(
            byteArrayOf(127, 0, 0, 0),    // nalanda-temple-3
            byteArrayOf(0, 127, 0, 0),    // nalanda-monastery-1
            byteArrayOf(0, 0, 127, 0)     // mahabodhi-temple
        )
        val negVecs = listOf(
            byteArrayOf(0, 0, 0, 127)     // generic foliage/wall
        )
        val buf = createIndexBuffer(posVecs, negVecs)
        val index = BinaryVectorIndex(buf, dim, posVecs.size, negVecs.size, prototypes)

        val queryVec = floatArrayOf(1.0f, 0.0f, 0.0f, 0.0f)
        val outcome = index.evaluate(queryVec, SiblingCalibrationPolicy())

        assertTrue(outcome is CalibratedScanOutcome.Identified)
        val identified = outcome as CalibratedScanOutcome.Identified
        assertEquals("nalanda-temple-3", identified.placeId)
        assertTrue(identified.score >= 0.99f)
        assertEquals("Stucco votive stupas flanking stairs", identified.distinguishingHint)
    }

    @Test
    fun `abstains when query matches hard negative centroid`() {
        val posVecs = listOf(
            byteArrayOf(127, 0, 0, 0),
            byteArrayOf(0, 127, 0, 0),
            byteArrayOf(0, 0, 127, 0)
        )
        val negVecs = listOf(
            byteArrayOf(0, 0, 0, 127) // negative vector along axis 3
        )
        val buf = createIndexBuffer(posVecs, negVecs)
        val index = BinaryVectorIndex(buf, dim, posVecs.size, negVecs.size, prototypes)

        // Query matches negative centroid along axis 3
        val queryVec = floatArrayOf(0.1f, 0.0f, 0.0f, 1.0f)
        val outcome = index.evaluate(queryVec, SiblingCalibrationPolicy())

        assertTrue(outcome is CalibratedScanOutcome.AbstainUnknown)
        val abstain = outcome as CalibratedScanOutcome.AbstainUnknown
        assertEquals("MATCHED_HARD_NEGATIVE_CENTROID", abstain.reason)
    }

    @Test
    fun `abstains when score is below absolute threshold`() {
        val posVecs = listOf(
            byteArrayOf(127, 0, 0, 0),
            byteArrayOf(0, 127, 0, 0),
            byteArrayOf(0, 0, 127, 0)
        )
        val negVecs = emptyList<ByteArray>()
        val buf = createIndexBuffer(posVecs, negVecs)
        val index = BinaryVectorIndex(buf, dim, posVecs.size, negVecs.size, prototypes)

        // Query vector oblique to all prototypes: dot product ~ 0.5 < 0.72
        val queryVec = floatArrayOf(0.5f, 0.5f, 0.5f, 0.5f)
        val outcome = index.evaluate(queryVec, SiblingCalibrationPolicy(absThreshold = 0.72f))

        assertTrue(outcome is CalibratedScanOutcome.AbstainUnknown)
        val abstain = outcome as CalibratedScanOutcome.AbstainUnknown
        assertEquals("BELOW_ABSOLUTE_THRESHOLD", abstain.reason)
    }

    @Test
    fun `disambiguates ambiguous sibling pair sharing same parentPlaceId`() {
        // Both nalanda-temple-3 and nalanda-monastery-1 have high, almost identical scores
        val posVecs = listOf(
            byteArrayOf(90, 90, 0, 0),   // temple-3: dot ~ 0.71
            byteArrayOf(90, 88, 0, 0),   // monastery-1: dot ~ 0.70 (delta < 0.04)
            byteArrayOf(0, 0, 127, 0)
        )
        val negVecs = emptyList<ByteArray>()
        val buf = createIndexBuffer(posVecs, negVecs)
        val index = BinaryVectorIndex(buf, dim, posVecs.size, negVecs.size, prototypes)

        val queryVec = floatArrayOf(0.707f, 0.707f, 0.0f, 0.0f)
        val policy = SiblingCalibrationPolicy(absThreshold = 0.65f, hardNegativeMargin = 0.05f, siblingMargin = 0.04f)
        val outcome = index.evaluate(queryVec, policy)

        assertTrue(outcome is CalibratedScanOutcome.AmbiguousSiblingPair)
        val sibling = outcome as CalibratedScanOutcome.AmbiguousSiblingPair
        assertEquals("nalanda-ruins", sibling.parentPlaceId)
        assertEquals("nalanda-temple-3", sibling.primaryPlaceId)
        assertEquals("nalanda-monastery-1", sibling.secondaryPlaceId)
    }

    @Test
    fun `mmapReadOnly loads valid TWVEC001 binary file`() {
        val tempFile = File.createTempFile("test_twvec", ".bin").apply { deleteOnExit() }
        val posVecs = listOf(byteArrayOf(127, 0, 0, 0))
        val negVecs = listOf(byteArrayOf(0, 127, 0, 0))
        val buf = createIndexBuffer(posVecs, negVecs)

        RandomAccessFile(tempFile, "rw").use { raf ->
            raf.write(buf.array())
        }

        val loaded = BinaryVectorIndex.mmapReadOnly(tempFile, prototypes.subList(0, 1))
        assertEquals(4, loaded.dim)
        assertEquals(1, loaded.numPrototypes)
        assertEquals(1, loaded.numNegatives)
    }

    @Test
    fun `rejects invalid dimension query`() {
        val buf = createIndexBuffer(listOf(byteArrayOf(127, 0, 0, 0)), emptyList())
        val index = BinaryVectorIndex(buf, dim, 1, 0, prototypes.subList(0, 1))

        try {
            index.evaluate(floatArrayOf(1.0f, 0.0f), SiblingCalibrationPolicy())
            fail("Expected IllegalArgumentException for dim mismatch")
        } catch (_: IllegalArgumentException) {
            // Expected
        }
    }
}
