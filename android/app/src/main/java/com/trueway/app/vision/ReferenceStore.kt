package com.trueway.app.vision

import android.content.Context
import com.trueway.app.pack.PrefsActivePackStore
import org.json.JSONObject
import java.io.File

/**
 * Pack-side reference index loader (blueprint §9.4 `vision/` component,
 * §28.3 `reference_embeddings`).
 *
 * Asset format (`assets/reference_index.json`, gitignored until the pack
 * builder emits real adapted vectors):
 * ```json
 * {
 *   "model_id": "mobileclip-s0+diag-adapter",
 *   "refs": [{"place_id": "...", "asset_id": "...", "values": [0.01, ...]}],
 *   "calibration": {"accept_threshold": 0.62, "min_margin": 0.04}
 * }
 * ```
 * Missing asset, corrupt JSON, or zero usable refs → [ReferenceIndex.Empty]:
 * the scanner reports "not in your offline pack", never a fabricated match.
 * Present refs but absent calibration → [ReferenceIndex.Uncalibrated]:
 * ranking runs for diagnostics only; the UI must NOT present candidate names.
 */
data class PackCalibration(val acceptThreshold: Double, val minMargin: Double)

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
            ReferenceIndex.Ready(
                refs = refs,
                calibration = PackCalibration(accept, margin),
                modelId = root.optString("model_id").ifBlank { null },
                packId = packId,
            )
        } else {
            ReferenceIndex.Uncalibrated(refs = refs, packId = packId)
        }
    }

    /**
     * Attempts to mmap a TWVEC001 zero-copy binary vector index if present in [activePackDir].
     * Returns null if files are absent or invalid, allowing graceful fallback to JSON index.
     */
    fun loadBinaryIfPresent(activePackDir: File?): BinaryVectorIndex? {
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
                return runCatching {
                    val root = JSONObject(metaFile.readText(Charsets.UTF_8))
                    val arr = root.getJSONArray("prototypes")
                    val protos = ArrayList<PrototypeRecord>(arr.length())
                    for (i in 0 until arr.length()) {
                        val item = arr.getJSONObject(i)
                        protos.add(
                            PrototypeRecord(
                                placeId = item.getString("place_id"),
                                parentPlaceId = item.optString("parent_place_id", "").ifEmpty { null },
                                viewpointTag = item.optString("viewpoint_tag", "default"),
                                distinguishingHint = item.optString("distinguishing_hint", "")
                            )
                        )
                    }
                    BinaryVectorIndex.mmapReadOnly(binFile, protos)
                }.getOrNull()
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
