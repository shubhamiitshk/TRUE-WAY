package com.trueway.app.vision

import android.content.Context
import com.trueway.app.pack.PrefsActivePackStore
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/**
 * Pack-side reference index loader (blueprint §9.4 `vision/` component,
 * §28.3 `reference_embeddings`).
 *
 * Asset format (`vision/reference_vectors.meta.json`):
 * ```json
 * {
 *   "format": "TWVEC002",
 *   "model_id": "mobileclip-s0-v1",
 *   "model_sha256": "…",
 *   "dim": 512,
 *   "storage": "float32",
 *   "places": [{"place_id": "…", "parent_place_id": null, "viewpoint_tag": "…",
 *               "distinguishing_hint": "…", "prototype_start": 0, "prototype_count": 3}],
 *   "negatives": [{"label": "…"}],
 *   "calibration": {"accept_threshold": 0.62, "relative_threshold": 0.12,
 *                   "hard_negative_margin": 0.06, "sibling_margin": 0.04,
 *                   "min_margin": 0.05, "top_k_mean": 2,
 *                   "calibrator": {"a": 12.4, "b": -7.1}}
 * }
 * ```
 * The legacy TWVEC001 metadata (`prototypes[]` + `negative_labels[]`) is still
 * parsed so packs built by earlier versions keep importing.
 *
 * Missing asset, corrupt JSON, or zero usable refs → [ReferenceIndex.Empty]:
 * the scanner reports "not in your offline pack", never a fabricated match.
 * Present refs but absent calibration → [ReferenceIndex.Uncalibrated]:
 * ranking runs for diagnostics only; the UI must NOT present candidate names.
 */
/**
 * Calibration carried by the pack.
 *
 * [acceptThreshold] and [minMargin] are the legacy absolute gate. The newer
 * fields carry the RELATIVE gate and the fitted calibrator; a pack that only
 * has the legacy pair is still usable through the JSON path, but the binary
 * path refuses to run without a complete calibration (§3 principle 2 — the
 * scanner must not present a name it cannot calibrate).
 */
data class PackCalibration(
    val acceptThreshold: Double,
    val minMargin: Double,
    val relativeThreshold: Double = Double.NaN,
    val hardNegativeMargin: Double = Double.NaN,
    val siblingMargin: Double = Double.NaN,
    val topKMean: Int = 2,
    val calibrator: ScoreCalibrator = ScoreCalibrator.DISABLED,
) {
    /** Complete calibration, or null when the pack only carries the legacy pair. */
    fun toVisionCalibration(): VisionCalibration? {
        if (relativeThreshold.isNaN() || hardNegativeMargin.isNaN() || siblingMargin.isNaN()) return null
        return VisionCalibration(
            acceptThreshold = acceptThreshold,
            relativeThreshold = relativeThreshold,
            hardNegativeMargin = hardNegativeMargin,
            siblingMargin = siblingMargin,
            minMargin = minMargin,
            topKMean = topKMean,
            calibrator = calibrator,
            source = "pack",
        )
    }
}

sealed interface ReferenceIndex {
    data object Empty : ReferenceIndex
    data class Uncalibrated(
        val refs: List<RefVector>,
        val packId: String? = null,
    ) : ReferenceIndex
    data class Ready(
        val refs: List<RefVector>,
        val calibration: PackCalibration,
        val modelId: String?,
        val packId: String? = null,
    ) : ReferenceIndex
}

/** A binary index together with the metadata it was loaded with. */
data class LoadedVectorIndex(
    val index: BinaryVectorIndex,
    val meta: VectorIndexMeta,
)

object ReferenceStore {
    const val ASSET = "reference_index.json"

    /** Pure parser: asset bytes in, typed index out. JVM-testable. */
    fun parse(json: String, packId: String? = null): ReferenceIndex {
        val root: JSONObject
        try {
            root = JSONObject(json)
        } catch (_: Exception) {
            return ReferenceIndex.Empty
        }
        val refs = mutableListOf<RefVector>()
        try {
            val arr = root.optJSONArray("refs") ?: return ReferenceIndex.Empty
            for (i in 0 until arr.length()) {
                val o = arr.optJSONObject(i) ?: continue
                val placeId = o.optString("place_id").takeIf { it.isNotBlank() } ?: continue
                val assetId = o.optString("asset_id").ifBlank { "ref-$i" }
                val vals = o.optJSONArray("values") ?: o.optJSONArray("vector") ?: continue
                if (vals.length() == 0) continue
                val hint = o.optString("distinguishing_hint").ifBlank { null }
                refs += RefVector(
                    placeId = placeId,
                    assetId = assetId,
                    values = FloatArray(vals.length()) { vals.optDouble(it, 0.0).toFloat() },
                    distinguishingHint = hint,
                )
            }
        } catch (_: Exception) {
            return ReferenceIndex.Empty
        }
        if (refs.isEmpty()) return ReferenceIndex.Empty
        // All refs must share one dim, else the index is corrupt (model/pack mismatch).
        val dim = refs[0].values.size
        if (refs.any { it.values.size != dim }) return ReferenceIndex.Empty
        val cal = root.optJSONObject("calibration")
        val accept = cal?.optDouble("accept_threshold", Double.NaN)?.takeIf { !it.isNaN() }
        val margin = cal?.optDouble("min_margin", Double.NaN)?.takeIf { !it.isNaN() }
        return if (accept != null && margin != null) {
            val full = VisionCalibration.parse(cal)
            ReferenceIndex.Ready(
                refs = refs,
                calibration = PackCalibration(
                    acceptThreshold = accept,
                    minMargin = margin,
                    relativeThreshold = full?.relativeThreshold ?: Double.NaN,
                    hardNegativeMargin = full?.hardNegativeMargin ?: Double.NaN,
                    siblingMargin = full?.siblingMargin ?: Double.NaN,
                    topKMean = full?.topKMean ?: 2,
                    calibrator = full?.calibrator ?: ScoreCalibrator.DISABLED,
                ),
                modelId = root.optString("model_id").ifBlank { null },
                packId = packId,
            )
        } else {
            ReferenceIndex.Uncalibrated(refs = refs, packId = packId)
        }
    }

    /**
     * Parses the binary index metadata. Understands both TWVEC002 (current,
     * float32, one-or-more references per place) and TWVEC001 (legacy INT8,
     * exactly one reference per place).
     */
    fun parseVectorIndexMeta(json: String): VectorIndexMeta? {
        val root = try {
            JSONObject(json)
        } catch (_: Exception) {
            return null
        }
        val places = mutableListOf<PrototypeRecord>()
        val newFormat = root.optJSONArray("places")
        if (newFormat != null) {
            for (i in 0 until newFormat.length()) {
                val o = newFormat.optJSONObject(i) ?: continue
                val placeId = o.optString("place_id").takeIf { it.isNotBlank() } ?: continue
                places += PrototypeRecord(
                    placeId = placeId,
                    parentPlaceId = o.optString("parent_place_id", "").ifEmpty { null },
                    viewpointTag = o.optString("viewpoint_tag", "default"),
                    distinguishingHint = o.optString("distinguishing_hint", ""),
                    prototypeStart = o.optInt("prototype_start", i),
                    prototypeCount = o.optInt("prototype_count", 1).coerceAtLeast(1),
                )
            }
        } else {
            val legacy = root.optJSONArray("prototypes")
            if (legacy != null) {
                for (i in 0 until legacy.length()) {
                    val o = legacy.optJSONObject(i) ?: continue
                    val placeId = o.optString("place_id").takeIf { it.isNotBlank() } ?: continue
                    places += PrototypeRecord(
                        placeId = placeId,
                        parentPlaceId = o.optString("parent_place_id", "").ifEmpty { null },
                        viewpointTag = o.optString("viewpoint_tag", "default"),
                        distinguishingHint = o.optString("distinguishing_hint", ""),
                        prototypeStart = i,
                        prototypeCount = 1,
                    )
                }
            }
        }
        if (places.isEmpty()) return null
        val negatives = mutableListOf<String>()
        val negArr: JSONArray? = root.optJSONArray("negatives")
        if (negArr != null) {
            for (i in 0 until negArr.length()) {
                val o = negArr.optJSONObject(i)
                negatives += o?.optString("label") ?: "neg-$i"
            }
        } else {
            val legacyNeg = root.optJSONArray("negative_labels")
            if (legacyNeg != null) {
                for (i in 0 until legacyNeg.length()) negatives += legacyNeg.optString(i)
            }
        }
        val scale = root.optJSONObject("local_scale")
        return VectorIndexMeta(
            places = places,
            negativeLabels = negatives,
            calibration = VisionCalibration.parse(root.optJSONObject("calibration")),
            modelId = root.optString("model_id").ifBlank { null },
            modelSha256 = root.optString("model_sha256").ifBlank { null },
            localScaleK = scale?.optInt("k", 10) ?: 10,
            localScaleCount = scale?.optInt("count", 0) ?: 0,
        )
    }

    /**
     * Attempts to mmap a zero-copy binary vector index if present in [activePackDir].
     * Returns null if files are absent or invalid, allowing graceful fallback to JSON index.
     */
    fun loadBinaryIfPresent(activePackDir: File?): LoadedVectorIndex? {
        if (activePackDir == null || !activePackDir.exists()) return null
        val candidates = listOf(
            File(activePackDir, "vision/reference_vectors.bin") to File(activePackDir, "vision/reference_vectors.meta.json"),
            File(activePackDir, "content/vision/reference_vectors.bin") to File(activePackDir, "content/vision/reference_vectors.meta.json"),
            File(activePackDir, "vision/index.bin") to File(activePackDir, "vision/index.meta.json"),
            File(activePackDir, "content/vision/index.bin") to File(activePackDir, "content/vision/index.meta.json"),
            File(activePackDir, "index.bin") to File(activePackDir, "index.meta.json"),
            File(activePackDir, "reference_vectors.bin") to File(activePackDir, "reference_vectors.meta.json")
        )
        for ((binFile, metaFile) in candidates) {
            if (binFile.isFile && metaFile.isFile) {
                val loaded = runCatching {
                    val meta = parseVectorIndexMeta(metaFile.readText(Charsets.UTF_8))
                        ?: return null
                    val index = BinaryVectorIndex.mmapReadOnly(binFile, meta)
                    LoadedVectorIndex(index, meta)
                }.getOrNull()
                if (loaded != null) return loaded
            }
        }
        return null
    }

    /**
     * Resolves the reference index with active pack precedence:
     * 1. Explicit [packDir] if supplied
     * 2. Active pack(s) tracked in [PrefsActivePackStore]
     * 3. Bundled application assets fallback ([assetName])
     */
    fun load(
        context: Context?,
        assetName: String = ASSET,
        packDir: File? = null,
        packId: String? = null,
    ): ReferenceIndex {
        // 1. Explicit pack directory (testing & direct overrides)
        if (packDir != null && packDir.exists() && packDir.isDirectory) {
            val resolvedPackId = packId ?: packDir.name
            val fromDir = tryLoadFromDir(packDir, assetName, packId = resolvedPackId)
            if (fromDir !is ReferenceIndex.Empty) {
                return fromDir
            }
        }

        // 2. Active pack(s) via PrefsActivePackStore
        if (context != null) {
            try {
                val store = PrefsActivePackStore(context)
                val packsDir = File(context.filesDir, "packs")
                val activePacks = store.allActive().ifEmpty {
                    store.getActive("in-bihar-buddhist-circuit")?.let { mapOf("in-bihar-buddhist-circuit" to it) } ?: emptyMap()
                }
                for ((packId, version) in activePacks) {
                    val candidateDir = File(File(packsDir, packId), version)
                    if (candidateDir.exists() && candidateDir.isDirectory) {
                        val fromDir = tryLoadFromDir(candidateDir, assetName, packId = packId)
                        if (fromDir !is ReferenceIndex.Empty) {
                            return fromDir
                        }
                    }
                }
            } catch (_: Exception) {
                // Fall through to bundled asset
            }

            // 3. Bundled APK assets fallback
            return try {
                context.assets.open(assetName).bufferedReader().use { parse(it.readText(), packId = null) }
            } catch (_: Exception) {
                ReferenceIndex.Empty
            }
        }

        return ReferenceIndex.Empty
    }

    private fun tryLoadFromDir(dir: File, assetName: String, packId: String?): ReferenceIndex {
        val candidates = listOf(
            File(dir, assetName),
            File(dir, "content/$assetName"),
            File(dir, "assets/$assetName"),
        )
        for (f in candidates) {
            if (f.isFile && f.exists()) {
                try {
                    val idx = parse(f.readText(), packId = packId)
                    if (idx !is ReferenceIndex.Empty) {
                        return idx
                    }
                } catch (_: Exception) {
                    // Try next candidate
                }
            }
        }
        return ReferenceIndex.Empty
    }
}
