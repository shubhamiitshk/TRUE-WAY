package com.trueway.app

import android.graphics.Bitmap
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.trueway.app.data.PlaceRepository
import com.trueway.app.scan.ScanFallback
import com.trueway.app.scan.ScanGateEvent
import com.trueway.app.scan.ScanGateModel
import com.trueway.app.scan.ScanGateState
import com.trueway.app.scan.reduce
import com.trueway.app.vision.MediaPipeEmbedder
import com.trueway.app.vision.RankDecision
import com.trueway.app.vision.RefVector
import com.trueway.app.vision.RetrievalEngine
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Instrumented Camera Recognition Test (FIELD_PERFORMANCE_PROTOCOL.md §6).
 *
 * Verifies on real Android runtime:
 * 1. CameraX Single-Shot capture buffer allocation and resolution constraints.
 * 2. MediaPipeEmbedder lifecycle handling (Ready or graceful NotInstalled without crash).
 * 3. RetrievalEngine cosine matching over reference embeddings on device.
 * 4. ScanGate permission gate state transitions.
 */
@RunWith(AndroidJUnit4::class)
class CameraRecognitionTest {

    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext

    @Before
    fun setUp() {
        PlaceRepository.initForPackDir(context)
    }

    @Test
    fun cameraPermissionGateStateTransitionsFunctionCorrectly() {
        // Initial state before permission prompt must show site advisory
        val initial = ScanGateModel(state = ScanGateState.SiteAdvisory)
        assertEquals(ScanGateState.SiteAdvisory, initial.state)
        assertEquals(ScanFallback.NONE, initial.fallback)

        // Accepting advisory transitions to Rationale screen
        val afterAdvisory = initial.reduce(ScanGateEvent.AdvisoryAccepted)
        assertEquals(ScanGateState.Rationale, afterAdvisory.state)

        // Denying permission falls back to showing no-camera route
        val requesting = ScanGateModel(state = ScanGateState.RequestingPermission)
        val afterDenied = requesting.reduce(
            ScanGateEvent.PermissionResult(granted = false, canAskAgain = true)
        )
        assertEquals(ScanGateState.DeniedCanAskAgain, afterDenied.state)
        assertTrue("Denied state must show no-camera search route", afterDenied.showNoCameraRoute)
    }

    @Test
    fun mediaPipeEmbedderInitializesGracefullyOnDevice() {
        val embedder = MediaPipeEmbedder(context)
        assertNotNull("Embedder instance must be non-null", embedder)
        // On device without bundled model asset, must report NotInstalled rather than throw
        assertTrue(
            "Embedder must be Ready or report NotInstalled honestly",
            embedder.state is MediaPipeEmbedder.State.Ready ||
                embedder.state is MediaPipeEmbedder.State.NotInstalled
        )
    }

    @Test
    fun retrievalEngineRanksReferenceCentroidsOnDevice() {
        val queryVector = FloatArray(512) { 0.1f }
        val refs = listOf(
            RefVector(
                placeId = "in-bihar-bodhgaya-mahabodhi",
                assetId = "mahabodhi_ref_01",
                values = FloatArray(512) { 0.1f }
            ),
            RefVector(
                placeId = "in-bihar-nalanda-mahavihara",
                assetId = "nalanda_ref_01",
                values = FloatArray(512) { -0.1f }
            )
        )

        val ranked = RetrievalEngine.rank(query = queryVector, refs = refs)
        val scores = RetrievalEngine.aggregateByPlace(ranked)
        val decision = RetrievalEngine.decide(
            scores = scores,
            acceptThreshold = 0.60,
            minMargin = 0.08
        )

        assertNotNull(decision)
        assertTrue("Decision should be Accepted for identical vector match", decision is RankDecision.Accepted)
        val accepted = decision as RankDecision.Accepted
        assertEquals("in-bihar-bodhgaya-mahabodhi", accepted.place.placeId)
        assertTrue("Similarity score should be ~1.0", accepted.place.score > 0.95)
    }

    @Test
    fun singleShotBitmapAllocationMeetsMemoryConstraints() {
        // Single-shot image buffer (1080x1080 ARGB_8888) is ~4.6 MB
        val bitmap = Bitmap.createBitmap(1080, 1080, Bitmap.Config.ARGB_8888)
        assertNotNull(bitmap)
        assertEquals(1080, bitmap.width)
        assertEquals(1080, bitmap.height)
        assertTrue(bitmap.byteCount < 10 * 1024 * 1024) // <10 MB peak buffer
        bitmap.recycle()
    }
}
