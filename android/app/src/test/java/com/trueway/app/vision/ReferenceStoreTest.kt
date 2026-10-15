package com.trueway.app.vision

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Reference-index gates: corrupt/mismatched packs degrade to Empty (never a
 * fabricated match); present-but-uncalibrated refs must not yield names.
 */
class ReferenceStoreTest {

    private fun ref(place: String, vararg vals: Float) =
        """{"place_id":"$place","asset_id":"$place-r1","values":[${vals.joinToString(",")}]}"""

    @Test
    fun parsesReadyIndexWithCalibration() {
        val json = """{"model_id":"m","refs":[${ref("p1", 0.1f, 0.2f)},${ref("p2", 0.3f, 0.4f)}],""" +
            """"calibration":{"accept_threshold":0.6,"min_margin":0.05}}"""
        val idx = ReferenceStore.parse(json)
        assertTrue(idx is ReferenceIndex.Ready)
        val ready = idx as ReferenceIndex.Ready
        assertEquals(2, ready.refs.size)
        assertEquals(0.6, ready.calibration.acceptThreshold, 1e-9)
        assertEquals("m", ready.modelId)
    }

    @Test
    fun refsWithoutCalibrationAreUncalibrated() {
        val json = """{"refs":[${ref("p1", 0.1f, 0.2f)}]}"""
        val idx = ReferenceStore.parse(json)
        assertTrue(idx is ReferenceIndex.Uncalibrated)
    }

    @Test
    fun corruptEmptyAndDimMismatchedAreEmpty() {
        assertTrue(ReferenceStore.parse("") is ReferenceIndex.Empty)
        assertTrue(ReferenceStore.parse("{oops") is ReferenceIndex.Empty)
        assertTrue(ReferenceStore.parse("""{"refs":[]}""") is ReferenceIndex.Empty)
        // Dim mismatch = model/pack mismatch → refuse the whole index.
        val bad = """{"refs":[${ref("p1", 0.1f, 0.2f)},${ref("p2", 0.1f)}]}"""
        assertTrue(ReferenceStore.parse(bad) is ReferenceIndex.Empty)
        // Refs without place_id are skipped; none usable → Empty.
        assertTrue(
            ReferenceStore.parse("""{"refs":[{"asset_id":"x","values":[0.1]}]}""")
                is ReferenceIndex.Empty,
        )
    }

    @Test
    fun loadsFromPackDirOverride() {
        val tempDir = java.nio.file.Files.createTempDirectory("test-pack").toFile()
        try {
            val json = """{"model_id":"mobileclip-v1","refs":[${ref("p1", 0.5f, 0.5f)}],""" +
                """"calibration":{"accept_threshold":0.65,"min_margin":0.04}}"""
            java.io.File(tempDir, "reference_index.json").writeText(json)

            val idx = ReferenceStore.load(context = null, packDir = tempDir)
            assertTrue(idx is ReferenceIndex.Ready)
            val ready = idx as ReferenceIndex.Ready
            assertEquals(1, ready.refs.size)
            assertEquals("p1", ready.refs[0].placeId)
            assertEquals("mobileclip-v1", ready.modelId)
            assertEquals(tempDir.name, ready.packId)
        } finally {
            tempDir.deleteRecursively()
        }
    }

    @Test
    fun loadsFromPackContentSubdir() {
        val tempDir = java.nio.file.Files.createTempDirectory("test-pack-content").toFile()
        try {
            val contentDir = java.io.File(tempDir, "content").apply { mkdirs() }
            val json = """{"model_id":"mobileclip-v1","refs":[${ref("p2", 0.7f, 0.7f)}],""" +
                """"calibration":{"accept_threshold":0.62,"min_margin":0.03}}"""
            java.io.File(contentDir, "reference_index.json").writeText(json)

            val idx = ReferenceStore.load(context = null, packDir = tempDir)
            assertTrue(idx is ReferenceIndex.Ready)
            val ready = idx as ReferenceIndex.Ready
            assertEquals(1, ready.refs.size)
            assertEquals("p2", ready.refs[0].placeId)
        } finally {
            tempDir.deleteRecursively()
        }
    }

    @Test
    fun missingIndexInPackDirDegradesToEmpty() {
        val tempDir = java.nio.file.Files.createTempDirectory("test-pack-empty").toFile()
        try {
            val idx = ReferenceStore.load(context = null, packDir = tempDir)
            assertTrue(idx is ReferenceIndex.Empty)
        } finally {
            tempDir.deleteRecursively()
        }
    }

    @Test
    fun loadsBinaryVectorsWhenPresentInPackDir() {
        val tempDir = java.nio.file.Files.createTempDirectory("test-pack-bin").toFile()
        try {
            val visionDir = java.io.File(tempDir, "vision").apply { mkdirs() }
            val binFile = java.io.File(visionDir, "reference_vectors.bin")
            val metaFile = java.io.File(visionDir, "reference_vectors.meta.json")

            val buffer = java.nio.ByteBuffer.allocate(36).order(java.nio.ByteOrder.LITTLE_ENDIAN)
            buffer.put("TWVEC001".toByteArray(Charsets.US_ASCII))
            buffer.putInt(1) // version
            buffer.putInt(0x1234) // crc
            buffer.putInt(4) // dim
            buffer.putInt(1) // numPos
            buffer.putInt(0) // numNeg
            buffer.putInt(0) // padding
            buffer.put(byteArrayOf(127, 0, 0, 0)) // vector
            java.io.RandomAccessFile(binFile, "rw").use { it.write(buffer.array()) }

            metaFile.writeText("""
                {
                    "prototypes": [
                        {
                            "place_id": "nalanda-temple-3",
                            "parent_place_id": "nalanda-ruins",
                            "viewpoint_tag": "main-stairs",
                            "distinguishing_hint": "Corner stupas"
                        }
                    ]
                }
            """.trimIndent())

            val binIndex = ReferenceStore.loadBinaryIfPresent(tempDir)
            org.junit.Assert.assertNotNull(binIndex)
            assertEquals(4, binIndex!!.dim)
            assertEquals(1, binIndex.numPrototypes)
        } finally {
            tempDir.deleteRecursively()
        }
    }
}
