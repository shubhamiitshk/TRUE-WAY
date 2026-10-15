package com.trueway.app.vision

import android.content.Context
import android.graphics.Bitmap
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.core.Delegate
import com.google.mediapipe.tasks.vision.imageembedder.ImageEmbedder

/**
 * P0 scanner encoder shell (research §3.1, ADR-0003).
 *
 * - Integration surface: MediaPipe `ImageEmbedder`, `RunningMode.IMAGE`
 *   (single-shot — no streaming loop, matching the battery policy).
 * - Delegate ladder: GPU attempt → CPU fallback. GPU init and invoke stay on
 *   one thread (call from a dedicated single-thread dispatcher).
 * - Asset `vision_encoder.tflite` is fetched on demand (see
 *   `android/fetch_vision_assets.ps1`) and gitignored. Absent asset yields
 *   [State.NotInstalled] — the scan UI keeps its honest "recognition is not
 *   installed yet" copy instead of crashing.
 * - The filename is encoder-agnostic on purpose: the MobileNetV3 floor model
 *   and the future MobileCLIP-S0 `.tflite` land under the same name, with
 *   identity + dim recorded in the pack manifest `vision` section so this
 *   class can refuse a model/pack mismatch (wired at benchmark week).
 */
class MediaPipeEmbedder(
    private val context: Context,
    private val assetName: String = VISION_ASSET,
    private val preferGpu: Boolean = false,
) {
    sealed interface State {
        data object NotInstalled : State
        data object Ready : State
        data class Failed(val reason: String) : State
    }

    companion object {
        const val VISION_ASSET = "vision_encoder.tflite"
    }

    private var embedder: ImageEmbedder? = null

    val state: State = try {
        context.assets.openFd(assetName).close()
        val base = BaseOptions.builder()
            .setModelAssetPath(assetName)
            .setDelegate(if (preferGpu) Delegate.GPU else Delegate.CPU)
            .build()
        // RunningMode defaults to IMAGE (single-shot) — exactly our policy.
        embedder = ImageEmbedder.createFromOptions(
            context,
            ImageEmbedder.ImageEmbedderOptions.builder()
                .setBaseOptions(base)
                .build(),
        )
        State.Ready
    } catch (e: java.io.FileNotFoundException) {
        State.NotInstalled
    } catch (e: IllegalStateException) {
        State.NotInstalled // e.g. asset present but unreadable as a model
    } catch (e: RuntimeException) {
        // GPU delegate unsupported on this device → caller retries CPU.
        State.Failed(e.message ?: "embedder init failed")
    }

    /** Single-shot embedding, or null when unavailable — never throws. */
    fun embed(bitmap: Bitmap): FloatArray? {
        val e = embedder ?: return null
        return try {
            val image = BitmapImageBuilder(bitmap).build()
            e.embed(image).embeddingResult().embeddings()
                .firstOrNull()?.floatEmbedding()
        } catch (t: Throwable) {
            null
        }
    }

    fun close() {
        try {
            embedder?.close()
        } catch (_: Exception) {
        } finally {
            embedder = null
        }
    }
}
