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

/**
 * The shipped decision rule (blueprint §7.5–7.6).
 *
 * The rule has TWO margins and they answer different questions:
 *  * `openMargin`  = winner - best hard negative  → "is this one of OURS?"
 *  * `placeMargin` = winner - runner-up place    → "which one of ours?"
 *
 * and a per-place score that is a ROBUST TOP-K MEAN over that place's
 * reference vectors, not a MAX over a single centroid.
 */
class BinaryVectorIndexTest {

    private val dim = 4
    private lateinit var prototypes: List<PrototypeRecord>

    private fun policy(
        abs: Float = 0.72f,
        hardNeg: Float = 0.0f,
        sibling: Float = 0.04f,
        relative: Float = 0.12f,
        k: Int = 2,
    ) = SiblingCalibrationPolicy(abs, hardNeg, sibling, relative, 0.05f, k)

    @Before
    fun setUp() {
        prototypes = listOf(
            PrototypeRecord(
                placeId = "nalanda-temple-3",
                parentPlaceId = "nalanda-ruins",
                viewpointTag = "corner-tower",
                distinguishingHint = "Stucco votive stupas flanking stairs",
                prototypeStart = 0,
                prototypeCount = 1,
            ),
            PrototypeRecord(
                placeId = "nalanda-monastery-1",
                parentPlaceId = "nalanda-ruins",
                viewpointTag = "cells-quad",
                distinguishingHint = "Multi-level monks cells around courtyard",
                prototypeStart = 1,
                prototypeCount = 1,
            ),
            PrototypeRecord(
                placeId = "mahabodhi-temple",
                parentPlaceId = null,
                viewpointTag = "central-shikhara",
                distinguishingHint = "55-meter stepped pyramidal spire",
                prototypeStart = 2,
                prototypeCount = 1,
            )
        )
    }

    /** Builds a TWVEC002 float32 buffer. */
    private fun createFloat32IndexBuffer(
        posVectors: List<FloatArray>,
        negVectors: List<FloatArray>
    ): ByteBuffer {
        val totalBytes = 40 + (posVectors.size + negVectors.size) * dim * 4
        val buffer = ByteBuffer.allocate(totalBytes).order(ByteOrder.LITTLE_ENDIAN)
        buffer.put("TWVEC002".toByteArray(Charsets.US_ASCII))
        buffer.putInt(2)                       // version
        buffer.putInt(0x12345678)              // modelCrc
        buffer.putInt(dim)
        buffer.putInt(posVectors.size)         // numPos
        buffer.putInt(negVectors.size)         // numNeg
        buffer.putInt(3)                       // numPlaces
        buffer.putInt(1)                       // flags: float32 storage
        buffer.putInt(0)                       // reserved
        for (v in posVectors) for (x in v) buffer.putFloat(x)
        for (v in negVectors) for (x in v) buffer.putFloat(x)
        buffer.flip()
        return buffer
    }

    @Test
    fun `identifies matching prototype above threshold and margins`() {
        val posVecs = listOf(
            floatArrayOf(1f, 0f, 0f, 0f),
            floatArrayOf(0f, 1f, 0f, 0f),
            floatArrayOf(0f, 0f, 1f, 0f),
        )
        val negVecs = listOf(floatArrayOf(0f, 0f, 0f, 1f))
        val buf = createFloat32IndexBuffer(posVecs, negVecs)
        val index = BinaryVectorIndex(buf, dim, posVecs.size, negVecs.size, prototypes)

        // the query is closest to temple-3, then monastery-1, then mahabodhi
        val outcome = index.evaluate(floatArrayOf(0.9f, 0.4f, 0.1f, 0f), policy())

        assertTrue(outcome is CalibratedScanOutcome.Identified)
        val identified = outcome as CalibratedScanOutcome.Identified
        assertEquals("nalanda-temple-3", identified.placeId)
        assertTrue(identified.score >= 0.85f)
        assertEquals("Stucco votive stupas flanking stairs", identified.distinguishingHint)
        // the runner-up score is MEASURED, never fabricated
        assertEquals("nalanda-monastery-1", identified.runnerUpPlaceId)
        assertTrue("runner-up score must be a real measurement", identified.runnerUpScore < 0.6f)
    }

    @Test
    fun `abstains when the winner does not clear the open margin over the negative bank`() {
        val posVecs = listOf(
            floatArrayOf(0.9f, 0f, 0f, 0f),
            floatArrayOf(0f, 1f, 0f, 0f),
            floatArrayOf(0f, 0f, 1f, 0f),
        )
        // a negative exemplar nearly parallel to the query
        val negVecs = listOf(floatArrayOf(0.95f, 0f, 0f, 0f))
        val buf = createFloat32IndexBuffer(posVecs, negVecs)
        val index = BinaryVectorIndex(buf, dim, posVecs.size, negVecs.size, prototypes)

        val outcome = index.evaluate(floatArrayOf(1f, 0f, 0f, 0f), policy(relative = 0.20f))

        assertTrue(outcome is CalibratedScanOutcome.AbstainUnknown)
        val abstain = outcome as CalibratedScanOutcome.AbstainUnknown
        assertEquals("BELOW_RELATIVE_THRESHOLD", abstain.reason)
    }

    @Test
    fun `abstains when score is below absolute threshold`() {
        val posVecs = listOf(
            floatArrayOf(1f, 0f, 0f, 0f),
            floatArrayOf(0f, 1f, 0f, 0f),
            floatArrayOf(0f, 0f, 1f, 0f),
        )
        val buf = createFloat32IndexBuffer(posVecs, emptyList())
        val index = BinaryVectorIndex(buf, dim, posVecs.size, 0, prototypes)

        // cos = 0.707 against the best prototype, which is below the 0.72 floor
        val outcome = index.evaluate(floatArrayOf(0.707f, 0.707f, 0f, 0f), policy(abs = 0.72f))

        assertTrue(outcome is CalibratedScanOutcome.AbstainUnknown)
        val abstain = outcome as CalibratedScanOutcome.AbstainUnknown
        assertEquals("BELOW_ABSOLUTE_THRESHOLD", abstain.reason)
    }

    @Test
    fun `disambiguates ambiguous sibling pair sharing same parentPlaceId`() {
        // Two near-identical places that share a parent. The query is
        // equidistant-ish, so the two scores differ by ~0.007 — below the
        // sibling margin, hence an ambiguous PAIR rather than a forced name.
        val posVecs = listOf(
            floatArrayOf(0.70f, 0.70f, 0f, 0f),
            floatArrayOf(0.68f, 0.71f, 0f, 0f),
            floatArrayOf(0f, 0f, 1f, 0f),
        )
        val buf = createFloat32IndexBuffer(posVecs, emptyList())
        val index = BinaryVectorIndex(buf, dim, posVecs.size, 0, prototypes)

        val outcome = index.evaluate(floatArrayOf(0.707f, 0.707f, 0f, 0f), policy(abs = 0.5f, sibling = 0.20f))

        assertTrue(outcome is CalibratedScanOutcome.AmbiguousSiblingPair)
        val sibling = outcome as CalibratedScanOutcome.AmbiguousSiblingPair
        assertEquals("nalanda-ruins", sibling.parentPlaceId)
        assertEquals("nalanda-temple-3", sibling.primaryPlaceId)
        assertEquals("nalanda-monastery-1", sibling.secondaryPlaceId)
    }

    @Test
    fun `robust top-k mean is used instead of a max over the place's references`() {
        // nalanda-temple-3 owns TWO references: one perfectly matching (1,0,0,0)
        // and one unrelated (0,0,0,1). The top-2 MEAN must land at 0.5, not 1.0.
        val places = listOf(
            PrototypeRecord("nalanda-temple-3", "nalanda-ruins", "v", "h", prototypeStart = 0, prototypeCount = 2),
            PrototypeRecord("nalanda-monastery-1", "nalanda-ruins", "v", "h", prototypeStart = 2, prototypeCount = 1),
            PrototypeRecord("mahabodhi-temple", null, "v", "h", prototypeStart = 3, prototypeCount = 1),
        )
        val posVecs = listOf(
            floatArrayOf(1f, 0f, 0f, 0f),
            floatArrayOf(0f, 0f, 0f, 1f),
            floatArrayOf(0f, 1f, 0f, 0f),
            floatArrayOf(0f, 0f, 1f, 0f),
        )
        val buf = createFloat32IndexBuffer(posVecs, emptyList())
        val index = BinaryVectorIndex(buf, dim, posVecs.size, 0, places)

        val outcome = index.evaluate(floatArrayOf(1f, 0f, 0f, 0f), policy(abs = 0.4f, k = 2))

        assertTrue(outcome is CalibratedScanOutcome.Identified)
        val identified = outcome as CalibratedScanOutcome.Identified
        assertEquals("nalanda-temple-3", identified.placeId)
        assertEquals("top-2 mean must be (1.0 + 0.0) / 2", 0.5f, identified.score, 1e-5f)
    }

    @Test
    fun `geo prior re-ranks but never creates an acceptance`() {
        val posVecs = listOf(
            floatArrayOf(1f, 0f, 0f, 0f),
            floatArrayOf(0.9f, 0.4f, 0f, 0f),
            floatArrayOf(0f, 0f, 1f, 0f),
        )
        val negVecs = listOf(floatArrayOf(0f, 0f, 0f, 1f))
        val buf = createFloat32IndexBuffer(posVecs, negVecs)
        val index = BinaryVectorIndex(buf, dim, posVecs.size, negVecs.size, prototypes)

        // the query matches place 1 exactly; place 2 is the near runner-up.
        val query = floatArrayOf(1f, 0f, 0f, 0f)
        val far = mapOf("nalanda-temple-3" to 50.0, "nalanda-monastery-1" to 0.1)
        val prior = GeoPrior(tauKm = 1.0, kappaKm = 5.0, lambda = 0.3)

        val withPrior = index.evaluate(query, policy(abs = 0.3f), prior, far)
        assertTrue(withPrior is CalibratedScanOutcome.Identified)
        assertEquals(
            "a nearby runner-up must be able to out-rank a far winner",
            "nalanda-monastery-1",
            (withPrior as CalibratedScanOutcome.Identified).placeId,
        )

        // A prior may only subtract: with a heavy tail the penalty is bounded,
        // so it can never promote a place the image does not support.
        val huge = mapOf("nalanda-temple-3" to 5000.0, "nalanda-monastery-1" to 0.1)
        val withHuge = index.evaluate(query, policy(abs = 0.3f), prior, huge)
        assertTrue(withHuge is CalibratedScanOutcome.Identified)
        assertEquals(
            "nalanda-monastery-1",
            (withHuge as CalibratedScanOutcome.Identified).placeId,
        )
    }

    @Test
    fun `geo prior is disabled when there is no fix`() {
        val posVecs = listOf(
            floatArrayOf(1f, 0f, 0f, 0f),
            floatArrayOf(0f, 1f, 0f, 0f),
            floatArrayOf(0f, 0f, 1f, 0f),
        )
        val buf = createFloat32IndexBuffer(posVecs, emptyList())
        val index = BinaryVectorIndex(buf, dim, posVecs.size, 0, prototypes)
        val outcome = index.evaluate(floatArrayOf(1f, 0f, 0f, 0f), policy(), GeoPrior.DISABLED, emptyMap())
        assertTrue(outcome is CalibratedScanOutcome.Identified)
    }

    @Test
    fun `mmapReadOnly loads a valid TWVEC002 binary file`() {
        val tempFile = File.createTempFile("test_twvec002", ".bin").apply { deleteOnExit() }
        val posVecs = listOf(floatArrayOf(1f, 0f, 0f, 0f))
        val negVecs = listOf(floatArrayOf(0f, 1f, 0f, 0f))
        val buf = createFloat32IndexBuffer(posVecs, negVecs)

        RandomAccessFile(tempFile, "rw").use { raf -> raf.write(buf.array()) }

        val meta = VectorIndexMeta(places = prototypes.subList(0, 1))
        val loaded = BinaryVectorIndex.mmapReadOnly(tempFile, meta)
        assertEquals(4, loaded.dim)
        assertEquals(1, loaded.numPrototypes)
        assertEquals(1, loaded.numNegatives)
        assertEquals(BinaryVectorIndex.Storage.FLOAT32, loaded.storage)
    }

    @Test
    fun `rejects invalid dimension query`() {
        val posVecs = listOf(floatArrayOf(1f, 0f, 0f, 0f))
        val buf = createFloat32IndexBuffer(posVecs, emptyList())
        val index = BinaryVectorIndex(buf, dim, posVecs.size, 0, prototypes.subList(0, 1))

        try {
            index.evaluate(floatArrayOf(1f, 0f), policy())
            fail("Expected IllegalArgumentException for dim mismatch")
        } catch (_: IllegalArgumentException) {
            // Expected
        }
    }
}
