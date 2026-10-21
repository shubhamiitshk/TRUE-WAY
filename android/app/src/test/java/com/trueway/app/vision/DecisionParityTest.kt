package com.trueway.app.vision

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * CROSS-LANGUAGE PARITY.
 *
 * The workstation evaluator (`ml/vision_index.py`) and the Android device
 * (`BinaryVectorIndex.evaluate`) are two implementations of ONE rule, and that
 * rule is the product. If they drift, every number the team reports stops
 * describing what the app does.
 *
 * This test replays golden vectors — exported by `ml/export_parity_vectors.py`
 * from the REAL committed index — through the REAL binary reader and asserts
 * the device reaches the same decision the workstation did.
 *
 * It also verifies the committed `content/vision/` assets agree with each
 * other (header, dimension, counts, calibration), which is how the TWVEC002
 * header-size mismatch between the writer and the reader was caught.
 */
class DecisionParityTest {

    /** Walks up from the working directory until the repo's content/vision is found. */
    private fun repoRoot(): File {
        var dir = File(System.getProperty("user.dir")).absoluteFile
        while (true) {
            val candidate = File(dir, "content/vision/reference_vectors.bin")
            if (candidate.isFile) return dir
            dir = dir.parentFile ?: throw IllegalStateException("repo root not found")
        }
    }

    private fun loadMeta(root: File): VectorIndexMeta {
        val metaFile = File(root, "content/vision/reference_vectors.meta.json")
        assertTrue("missing ${metaFile.path}", metaFile.isFile)
        val raw = metaFile.readText()
        val meta = ReferenceStore.parseVectorIndexMeta(raw)
        assertNotNull("metadata must parse", meta)
        return meta!!
    }

    @Test
    fun `device reproduces the workstation decision for every golden vector`() {
        val root = repoRoot()
        val meta = loadMeta(root)
        val bin = File(root, "content/vision/reference_vectors.bin")
        val index = BinaryVectorIndex.mmapReadOnly(bin, meta)

        val fixture = JSONObject(File("src/test/resources/decision_parity.json").readText())
        val calJson = fixture.getJSONObject("calibration")
        val calibration = VisionCalibration.parse(calJson)
        assertNotNull("the shipped calibration must be complete", calibration)
        val policy = SiblingCalibrationPolicy.from(calibration)

        val cases = fixture.getJSONArray("cases")
        assertTrue("parity fixture must not be empty", cases.length() > 0)

        var accepted = 0
        var abstained = 0
        var mismatches = 0
        for (i in 0 until cases.length()) {
            val c = cases.getJSONObject(i)
            val q = FloatArray(c.getJSONArray("query").length()) { c.getJSONArray("query").getDouble(it).toFloat() }
            val expected = c.getJSONObject("expected")
            val outcome = index.evaluate(q, policy)

            val actualAccepted = outcome is CalibratedScanOutcome.Identified
            val actualPlace = when (outcome) {
                is CalibratedScanOutcome.Identified -> outcome.placeId
                is CalibratedScanOutcome.AmbiguousSiblingPair -> outcome.primaryPlaceId
                is CalibratedScanOutcome.AbstainUnknown -> outcome.bestPlaceId
            }
            val actualReason = when (outcome) {
                is CalibratedScanOutcome.Identified -> "ACCEPTED"
                is CalibratedScanOutcome.AmbiguousSiblingPair -> "AMBIGUOUS_SIBLING_PAIR"
                is CalibratedScanOutcome.AbstainUnknown -> outcome.reason
            }
            val label = c.getString("id")
            val deviceDetail = when (outcome) {
                is CalibratedScanOutcome.Identified ->
                    "score=${outcome.score} open=${outcome.relativeScore} neg=${outcome.maxNegativeScoreOf()}"
                is CalibratedScanOutcome.AmbiguousSiblingPair ->
                    "sibling pair delta=${outcome.scoreDelta}"
                is CalibratedScanOutcome.AbstainUnknown ->
                    "reason=${outcome.reason} top=${outcome.topRawScore} neg=${outcome.maxNegativeScore} open=${outcome.relativeScore}"
            }
            if (actualAccepted != expected.getBoolean("accepted")) {
                mismatches++
                assertEquals(
                    "$label: accepted differs (device=$actualAccepted, workstation=${expected.getBoolean("accepted")}) " +
                        "device[$deviceDetail] workstation[score=${expected.getDouble("score")} " +
                        "open=${expected.getDouble("open_margin")} neg=${expected.getDouble("best_negative")}]",
                    expected.getBoolean("accepted"), actualAccepted
                )
            }
            if (actualAccepted) {
                accepted++
                val expPlace = expected.getString("place_id")
                assertEquals("$label: place differs", expPlace, actualPlace)
                val expScore = expected.getDouble("score")
                val actualScore = (outcome as CalibratedScanOutcome.Identified).score.toDouble()
                assertTrue("$label: score differs (device=$actualScore, workstation=$expScore)",
                    kotlin.math.abs(actualScore - expScore) < 2e-3)
                val expOpen = expected.getDouble("open_margin")
                val actualOpen = outcome.relativeScore.toDouble()
                assertTrue("$label: open margin differs (device=$actualOpen, workstation=$expOpen)",
                    kotlin.math.abs(actualOpen - expOpen) < 2e-3)
            } else {
                abstained++
                assertEquals("$label: abstain reason differs", expected.getString("reason"), actualReason)
            }
        }
        assertEquals("no decision may differ between the device and the workstation", 0, mismatches)
        assertTrue("the fixture must exercise both outcomes", accepted > 0 && abstained > 0)
        println("parity: $accepted accepted, $abstained abstained, 0 mismatches over ${cases.length()} cases")
    }

    @Test
    fun `the committed binary index agrees with its metadata`() {
        val root = repoRoot()
        val meta = loadMeta(root)
        val bin = File(root, "content/vision/reference_vectors.bin")
        val index = BinaryVectorIndex.mmapReadOnly(bin, meta)

        val expectedPrototypes = meta.places.sumOf { it.prototypeCount }
        assertEquals("header prototype count must match the metadata", expectedPrototypes, index.numPrototypes)
        assertEquals("header negative count must match the metadata", meta.negativeLabels.size, index.numNegatives)
        assertEquals("the index must be float32", BinaryVectorIndex.Storage.FLOAT32, index.storage)

        // the body must be exactly the size the header implies, INCLUDING the
        // CSLS local-scale section when the metadata declares one
        val expectedBytes = 40L + (index.numPrototypes + index.numNegatives) * index.dim * 4L +
            (if (meta.localScaleCount > 0) meta.localScaleCount * 4L else 0L)
        assertEquals("binary body size mismatch", expectedBytes, bin.length())
        assertEquals(
            "the local-scale section must hold one value per gallery vector",
            index.numPrototypes + index.numNegatives,
            meta.localScaleCount,
        )

        // the calibration must be COMPLETE — an incomplete one would make the
        // scanner present names it cannot calibrate
        assertNotNull("the shipped index must carry a complete calibration", meta.calibration)
        assertEquals("pack", meta.calibration!!.source)
    }
}
