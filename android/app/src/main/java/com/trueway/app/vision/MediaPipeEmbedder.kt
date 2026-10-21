package com.trueway.app.vision

import android.content.Context
import android.graphics.Bitmap
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.core.Delegate
import com.google.mediapipe.tasks.vision.imageembedder.ImageEmbedder
import java.util.concurrent.Executors

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
 *   and the MobileCLIP-S0 `.tflite` land under the same name, with
 *   identity + dim recorded in the pack manifest `vision` section so a
 *   model/pack mismatch can be refused.
 *
 * NOTE ON THE OUTPUT: the exported graph ends at `backbone.head.fc` and does
 * NOT contain an L2-normalisation op, so the returned embedding is
 * unnormalised. Every consumer here normalises explicitly — do NOT also set
 * MediaPipe's `l2_normalize` option, and do not assume unit-norm output.
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

/**
 * Process-scoped encoder holder.
 *
 * The 12 MB INT8 encoder was previously re-loaded and re-initialised on EVERY
 * capture (`ScanPipeline` constructed a fresh `MediaPipeEmbedder` per scan and
 * closed it in a `finally`), which put a full model parse plus delegate
 * initialisation inside the capture-to-card latency budget.
 *
 * The holder keeps one encoder alive on ONE dedicated thread. Single-threaded
 * because the MediaPipe GPU delegate requires that initialisation and
 * invocation happen on the same thread; single because two concurrent scans
 * would only contend for the same model.
 */
object VisionEncoder {
    private val executor = Executors.newSingleThreadExecutor { r ->
        Thread(r, "trueway-vision-encoder").apply { isDaemon = true }
    }

    @Volatile
    private var cached: MediaPipeEmbedder? = null

    @Volatile
    private var cachedGpu: Boolean = false

    private val lock = Any()

    /**
     * Runs [block] with a ready encoder on the dedicated vision thread.
     * Returns null when no encoder is installed.
     */
    fun <T> withEncoder(context: Context, preferGpu: Boolean, block: (MediaPipeEmbedder) -> T): T? {
        return try {
            executor.submit<T?> {
                val e = synchronized(lock) {
                    var cur = cached
                    if (cur == null || cur.state != MediaPipeEmbedder.State.Ready || cachedGpu != preferGpu) {
                        cur?.close()
                        cur = MediaPipeEmbedder(context, preferGpu = preferGpu)
                        cached = cur
                        cachedGpu = preferGpu
                    }
                    cur
                }
                if (e.state != MediaPipeEmbedder.State.Ready) null else block(e)
            }.get()
        } catch (_: Exception) {
            null
        }
    }

    /** Releases the encoder (app backgrounded / low memory). */
    fun release() {
        synchronized(lock) {
            cached?.close()
            cached = null
        }
    }
}
