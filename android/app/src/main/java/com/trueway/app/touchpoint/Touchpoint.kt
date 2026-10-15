package com.trueway.app.touchpoint

import android.content.Context
import com.trueway.app.data.PlaceRepository
import com.trueway.app.pack.PrefsActivePackStore
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters
import org.bouncycastle.crypto.signers.Ed25519Signer
import org.json.JSONObject
import java.io.File
import java.time.Instant

/**
 * Signed touchpoint resolver (blueprint §11.2, F014; threat model §15.3).
 *
 * Security model, enforced here:
 * - Only `tw://place/v1/<c>.<s>` and `{"v":1,"c":"..","s":".."}` envelopes
 *   are parsed. Anything else — http(s) URLs included — is rejected and
 *   NEVER launched or fetched.
 * - Transports carry opaque (canonical, signature) bytes; this parser never
 *   re-serializes JSON, so no canonicalization mismatch can exist. The exact
 *   byte contract is shared with `tests/fixtures/qr/make_demo_touchpoint.py`.
 * - A valid signature authenticates the PAYLOAD's publisher, not the
 *   physical plate's placement (§11.2): the UI always shows human label +
 *   site serial + a report-mismatch route (TOUCH-036).
 * - Pure Kotlin + org.json + BouncyCastle: fully JVM-testable with real
 *   (not mocked) Ed25519. Clock is injected for deterministic expiry tests.
 */

data class TouchpointPayload(
    val issuerId: String,
    val keyId: String,
    val touchpointId: String,
    val placeId: String,
    val packId: String,
    val issuedAt: Instant,
    val expiresAt: Instant?,
    val siteSerial: String?,
    val humanLabel: String?,
)

data class TrustedIssuer(val issuerId: String, val keyId: String, val pubkey: ByteArray)

enum class TouchpointReject {
    NOT_A_TOUCHPOINT,
    BAD_FORMAT,
    UNKNOWN_ISSUER,
    BAD_SIGNATURE,
    EXPIRED,
    UNKNOWN_PLACE,
}

sealed interface TouchpointResult {
    /** Authenticated AND resolved against installed corpus: open the card. */
    data class Valid(val payload: TouchpointPayload) : TouchpointResult

    /**
     * Authenticated but the place is not installed: honest missing-pack
     * screen, never invented metadata (TOUCH-035).
     */
    data class ValidUnknownPlace(val payload: TouchpointPayload) : TouchpointResult
    data class Invalid(val reason: TouchpointReject) : TouchpointResult
}

object TouchpointParser {
    const val SCHEME = "tw://place/v1/"

    /** Parse any scanned string; never throws, never launches anything. */
    fun parseQrText(text: String): Pair<ByteArray, ByteArray>? {
        val t = text.trim()
        if (t.startsWith(SCHEME)) {
            val parts = t.removePrefix(SCHEME).split(".")
            if (parts.size != 2 || parts.any { it.isBlank() }) return null
            return try {
                b64u(parts[0]) to b64u(parts[1])
            } catch (_: Exception) {
                null
            }
        }
        if (t.startsWith("{")) {
            return try {
                val o = JSONObject(t)
                if (o.optInt("v", -1) != 1) return null
                val c = o.optString("c").takeIf { it.isNotBlank() } ?: return null
                val s = o.optString("s").takeIf { it.isNotBlank() } ?: return null
                b64u(c) to b64u(s)
            } catch (_: Exception) {
                null
            }
        }
        return null // http(s) URLs and everything else: not ours, never touch.
    }

    fun parsePayload(canonical: ByteArray): TouchpointPayload? {
        return try {
            val o = JSONObject(canonical.toString(Charsets.UTF_8))
            fun req(name: String): String {
                return o.optString(name).takeIf { it.isNotBlank() } ?: throw BadPayload()
            }
            val expires = o.optString("expires_at").takeIf { it.isNotBlank() }?.let {
                try {
                    Instant.parse(it)
                } catch (_: Exception) {
                    return null
                }
            }
            TouchpointPayload(
                issuerId = req("issuer_id"),
                keyId = req("key_id"),
                touchpointId = req("touchpoint_id"),
                placeId = req("place_id"),
                packId = req("pack_id"),
                issuedAt = try {
                    Instant.parse(req("issued_at"))
                } catch (_: Exception) {
                    return null
                },
                expiresAt = expires,
                siteSerial = o.optString("site_serial").ifBlank { null },
                humanLabel = o.optString("human_label").ifBlank { null },
            )
        } catch (_: BadPayload) {
            null
        } catch (_: Exception) {
            null
        }
    }

    private class BadPayload : Exception()

    private fun b64u(s: String): ByteArray {
        var p = s.trim()
        repeat((4 - p.length % 4) % 4) { p += "=" }
        return java.util.Base64.getUrlDecoder().decode(p)
    }
}

object TouchpointVerifier {
    fun verify(
        canonical: ByteArray,
        signature: ByteArray,
        trust: List<TrustedIssuer>,
        nowMs: Long = System.currentTimeMillis(),
    ): TouchpointResult {
        val payload = TouchpointParser.parsePayload(canonical)
            ?: return TouchpointResult.Invalid(TouchpointReject.BAD_FORMAT)
        val issuer = trust.firstOrNull { it.issuerId == payload.issuerId && it.keyId == payload.keyId }
            ?: return TouchpointResult.Invalid(TouchpointReject.UNKNOWN_ISSUER)
        if (!ed25519Verify(issuer.pubkey, canonical, signature)) {
            return TouchpointResult.Invalid(TouchpointReject.BAD_SIGNATURE)
        }
        val exp = payload.expiresAt
        if (exp != null && nowMs > exp.toEpochMilli()) {
            return TouchpointResult.Invalid(TouchpointReject.EXPIRED)
        }
        return if (PlaceRepository.get(payload.placeId) != null) {
            TouchpointResult.Valid(payload)
        } else {
            TouchpointResult.ValidUnknownPlace(payload)
        }
    }

    /** Trust store as shipped in assets/touch_issuers.json (pinned keys, §9.3). */
    fun parseTrustStore(json: String): List<TrustedIssuer> {
        return try {
            val arr = JSONObject(json).optJSONArray("issuers") ?: return emptyList()
            buildList {
                for (i in 0 until arr.length()) {
                    val o = arr.optJSONObject(i) ?: continue
                    val issuerId = o.optString("issuer_id").takeIf { it.isNotBlank() } ?: continue
                    val keyId = o.optString("key_id").takeIf { it.isNotBlank() } ?: continue
                    val pub = o.optString("pubkey_b64u").takeIf { it.isNotBlank() } ?: continue
                    val raw = try {
                        var p = pub.trim()
                        repeat((4 - p.length % 4) % 4) { p += "=" }
                        java.util.Base64.getUrlDecoder().decode(p)
                    } catch (_: Exception) {
                        continue
                    }
                    if (raw.size != 32) continue
                    add(TrustedIssuer(issuerId, keyId, raw))
                }
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    /** Shared Ed25519 primitive (also used by the pack importer, ADR-0006). */
    fun ed25519Verify(pub32: ByteArray, msg: ByteArray, sig: ByteArray): Boolean {
        if (pub32.size != 32 || sig.size != 64) return false
        return try {
            val v = Ed25519Signer()
            v.init(false, Ed25519PublicKeyParameters(pub32, 0))
            v.update(msg, 0, msg.size)
            v.verifySignature(sig)
        } catch (_: Exception) {
            false
        }
    }

    /**
     * Resolves the active trust store (pinned keys, §9.3, TOUCH-033).
     * Precedence:
     * 1. Active pack's `touch_issuers.json` (pack-based trust rotation)
     * 2. Bundled `assets/touch_issuers.json` fallback
     * Issuers are merged so pack-updated keys take precedence while retaining bundled roots.
     */
    fun loadTrustStore(context: Context? = null, packDir: File? = null): List<TrustedIssuer> {
        val issuersMap = mutableMapOf<Pair<String, String>, TrustedIssuer>()

        // 1. Load bundled baseline trust store
        if (context != null) {
            try {
                context.assets.open("touch_issuers.json").bufferedReader().use { reader ->
                    val bundled = parseTrustStore(reader.readText())
                    for (iss in bundled) {
                        issuersMap[iss.issuerId to iss.keyId] = iss
                    }
                }
            } catch (_: Exception) {
                // No bundled trust store
            }
        }

        // 2. Check explicitly provided pack directory
        if (packDir != null && packDir.exists() && packDir.isDirectory) {
            loadIssuersFromDir(packDir)?.let { packIssuers ->
                for (iss in packIssuers) {
                    issuersMap[iss.issuerId to iss.keyId] = iss
                }
            }
        }

        // 3. Check active pack directories from PrefsActivePackStore
        if (context != null) {
            try {
                val store = PrefsActivePackStore(context)
                val packsDir = File(context.filesDir, "packs")
                val activePacks = store.allActive().ifEmpty {
                    store.getActive("in-bihar-buddhist-circuit")?.let { mapOf("in-bihar-buddhist-circuit" to it) } ?: emptyMap()
                }
                for ((packId, version) in activePacks) {
                    val dir = File(File(packsDir, packId), version)
                    if (dir.exists() && dir.isDirectory) {
                        loadIssuersFromDir(dir)?.let { packIssuers ->
                            for (iss in packIssuers) {
                                issuersMap[iss.issuerId to iss.keyId] = iss
                            }
                        }
                    }
                }
            } catch (_: Exception) {
                // Fail open to bundled trust
            }
        }

        return issuersMap.values.toList()
    }

    private fun loadIssuersFromDir(dir: File): List<TrustedIssuer>? {
        val candidates = listOf(
            File(dir, "touch_issuers.json"),
            File(dir, "content/touch_issuers.json"),
            File(dir, "assets/touch_issuers.json"),
        )
        for (candidate in candidates) {
            if (candidate.isFile && candidate.exists()) {
                try {
                    val issuers = parseTrustStore(candidate.readText())
                    if (issuers.isNotEmpty()) return issuers
                } catch (_: Exception) {
                    // Try next
                }
            }
        }
        return null
    }
}
