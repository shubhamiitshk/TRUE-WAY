package com.trueway.app.touchpoint

import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters
import org.bouncycastle.crypto.signers.Ed25519Signer
import org.json.JSONObject
import java.time.Instant

/**
 * OTA voucher resolver (Viator, Klook, MakeMyTrip, EaseMyTrip, Trip.com).
 *
 * Security model:
 * - OTA vouchers are Ed25519-signed JSON envelopes with a `voucher_id`,
 *   `ota_partner`, `pack_id`, `expires_at`, and `signature`.
 * - The signature is verified against a trust store of OTA partner public keys.
 * - Verification happens 100% offline (no network requests).
 * - Once verified, the voucher unlocks the specified pack.
 *
 * Voucher format (JSON):
 * ```json
 * {
 *   "v": 1,
 *   "voucher_id": "VIATOR-2026-11-001",
 *   "ota_partner": "viator",
 *   "pack_id": "in-bihar-buddhist-circuit",
 *   "expires_at": "2026-12-31T23:59:59Z",
 *   "signature": "<base64url>"
 * }
 * ```
 *
 * The signature is computed over the canonical JSON (without the signature field).
 */

data class OtaVoucherPayload(
    val voucherId: String,
    val otaPartner: String,
    val packId: String,
    val expiresAt: Instant?,
    val issuedAt: Instant?,
)

data class OtaPartnerKey(
    val partnerId: String,
    val keyId: String,
    val pubkey: ByteArray,
)

enum class OtaVoucherReject {
    NOT_A_VOUCHER,
    BAD_FORMAT,
    UNKNOWN_PARTNER,
    BAD_SIGNATURE,
    EXPIRED,
    UNKNOWN_PACK,
    ALREADY_REDEEMED,
}

sealed interface OtaVoucherResult {
    data class Valid(val payload: OtaVoucherPayload) : OtaVoucherResult
    data class Invalid(val reason: OtaVoucherReject) : OtaVoucherResult
    data class AlreadyRedeemed(val payload: OtaVoucherPayload) : OtaVoucherResult
}

object OtaVoucherParser {
    const val SCHEME_PREFIX = "trueway://voucher/v1/"

    /**
     * Parse a scanned QR code or deep link.
     * Supports:
     * - `trueway://voucher/v1/<base64url_json>`
     * - Raw JSON starting with `{"v":1,"ota_partner":...}`
     */
    fun parseQrText(text: String): Pair<ByteArray, ByteArray>? {
        val t = text.trim()

        // Scheme-based voucher
        if (t.startsWith(SCHEME_PREFIX)) {
            val encoded = t.removePrefix(SCHEME_PREFIX)
            return try {
                val json = String(java.util.Base64.getUrlDecoder().decode(encoded), Charsets.UTF_8)
                val obj = JSONObject(json)
                val canonical = canonicalizeVoucher(obj)
                val sig = b64u(obj.optString("signature").takeIf { it.isNotBlank() } ?: return null)
                canonical to sig
            } catch (_: Exception) {
                null
            }
        }

        // Raw JSON voucher
        if (t.startsWith("{")) {
            return try {
                val obj = JSONObject(t)
                if (obj.optInt("v", -1) != 1) return null
                val canonical = canonicalizeVoucher(obj)
                val sig = b64u(obj.optString("signature").takeIf { it.isNotBlank() } ?: return null)
                canonical to sig
            } catch (_: Exception) {
                null
            }
        }

        return null
    }

    /**
     * Canonicalize a voucher JSON for signature verification.
     *
     * MUST be byte-identical to the Python fixture generator's:
     *   json.dumps(obj, sort_keys=True, separators=(',', ':'))
     * i.e. keys sorted lexicographically, zero whitespace, strings JSON-escaped,
     * and the integer `v` emitted as a bare number. This is the cross-language
     * parity contract — the signature is verified over these exact bytes.
     */
    fun canonicalizeVoucher(obj: JSONObject): ByteArray {
        val parts = mutableListOf<String>()
        fun stringField(key: String) {
            val v = obj.optString(key).takeIf { it.isNotEmpty() } ?: return
            parts.add("\"$key\":\"${escapeJsonString(v)}\"")
        }
        // sorted order: expires_at, issued_at, ota_partner, pack_id, v, voucher_id
        stringField("expires_at")
        stringField("issued_at")
        stringField("ota_partner")
        stringField("pack_id")
        parts.add("\"v\":${obj.optInt("v")}")
        stringField("voucher_id")
        return parts.joinToString(",", "{", "}").toByteArray(Charsets.UTF_8)
    }

    /** Minimal JSON string escaper (control chars, backslash, double quote). */
    private fun escapeJsonString(s: String): String {
        val sb = StringBuilder(s.length + 8)
        for (c in s) {
            when (c) {
                '\\' -> sb.append("\\\\")
                '"' -> sb.append("\\\"")
                '\b' -> sb.append("\\b")
                '\u000C' -> sb.append("\\f")
                '\n' -> sb.append("\\n")
                '\r' -> sb.append("\\r")
                '\t' -> sb.append("\\t")
                else -> {
                    if (c < ' ') {
                        sb.append(String.format("\\u%04x", c.code))
                    } else {
                        sb.append(c)
                    }
                }
            }
        }
        return sb.toString()
    }

    fun parsePayload(canonical: ByteArray): OtaVoucherPayload? {
        return try {
            val o = JSONObject(canonical.toString(Charsets.UTF_8))
            fun req(name: String): String {
                return o.optString(name).takeIf { it.isNotBlank() } ?: throw BadVoucher()
            }

            val expires = o.optString("expires_at").takeIf { it.isNotBlank() }?.let {
                try {
                    Instant.parse(it)
                } catch (_: Exception) {
                    return null
                }
            }

            val issued = o.optString("issued_at").takeIf { it.isNotBlank() }?.let {
                try {
                    Instant.parse(it)
                } catch (_: Exception) {
                    return null
                }
            }

            OtaVoucherPayload(
                voucherId = req("voucher_id"),
                otaPartner = req("ota_partner"),
                packId = req("pack_id"),
                expiresAt = expires,
                issuedAt = issued,
            )
        } catch (_: BadVoucher) {
            null
        } catch (_: Exception) {
            null
        }
    }

    private class BadVoucher : Exception()

    private fun b64u(s: String): ByteArray {
        var p = s.trim()
        repeat((4 - p.length % 4) % 4) { p += "=" }
        return java.util.Base64.getUrlDecoder().decode(p)
    }
}

object OtaVoucherVerifier {
    /**
     * Verify an OTA voucher signature.
     *
     * @param canonical The canonical JSON bytes (without signature)
     * @param signature The Ed25519 signature
     * @param partnerKeys List of trusted OTA partner public keys
     * @param nowMs Current time in milliseconds (for expiry check)
     * @return Verification result
     */
    fun verify(
        canonical: ByteArray,
        signature: ByteArray,
        partnerKeys: List<OtaPartnerKey>,
        nowMs: Long = System.currentTimeMillis(),
    ): OtaVoucherResult {
        val payload = OtaVoucherParser.parsePayload(canonical)
            ?: return OtaVoucherResult.Invalid(OtaVoucherReject.BAD_FORMAT)

        // Find the partner's public key
        val partnerKey = partnerKeys.firstOrNull {
            it.partnerId == payload.otaPartner
        } ?: return OtaVoucherResult.Invalid(OtaVoucherReject.UNKNOWN_PARTNER)

        // Verify Ed25519 signature
        if (!ed25519Verify(partnerKey.pubkey, canonical, signature)) {
            return OtaVoucherResult.Invalid(OtaVoucherReject.BAD_SIGNATURE)
        }

        // Check expiry
        val exp = payload.expiresAt
        if (exp != null && nowMs > exp.toEpochMilli()) {
            return OtaVoucherResult.Invalid(OtaVoucherReject.EXPIRED)
        }

        // Check if pack exists (this would be done by the caller)
        // For now, assume valid if signature and expiry pass

        return OtaVoucherResult.Valid(payload)
    }

    /**
     * Shared Ed25519 verification (same as TouchpointVerifier).
     */
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
     * Load OTA partner trust store from assets.
     * Format:
     * ```json
     * {
     *   "partners": [
     *     {
     *       "partner_id": "viator",
     *       "key_id": "viator-prod-2026",
     *       "pubkey_b64u": "..."
     *     }
     *   ]
     * }
     * ```
     */
    fun parsePartnerTrustStore(json: String): List<OtaPartnerKey> {
        return try {
            val arr = JSONObject(json).optJSONArray("partners") ?: return emptyList()
            buildList {
                for (i in 0 until arr.length()) {
                    val o = arr.optJSONObject(i) ?: continue
                    val partnerId = o.optString("partner_id").takeIf { it.isNotBlank() } ?: continue
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
                    add(OtaPartnerKey(partnerId, keyId, raw))
                }
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    /**
     * Load partner trust store from context assets.
     */
    fun loadPartnerTrustStore(context: android.content.Context): List<OtaPartnerKey> {
        return try {
            context.assets.open("ota_partner_keys.json").bufferedReader().use { reader ->
                parsePartnerTrustStore(reader.readText())
            }
        } catch (_: Exception) {
            emptyList()
        }
    }
}

/**
 * Redeems an OTA voucher and records the pack entitlement.
 *
 * Redemptions persist in the provided [OtaEntitlementStore] (SharedPreferences
 * in production, in-memory in tests), so double-redemption is refused even
 * after process death. The actual pack activation pointer is managed via
 * `PrefsActivePackStore` by the caller (or the Packs screen).
 */
object OtaVoucherRedeemer {
    /**
     * Redeem a voucher and return the outcome.
     * Valid when the voucher is redeemed (or already redeemed on this device);
     * the caller decides how to activate the entitled pack.
     */
    fun redeem(voucher: OtaVoucherPayload, store: OtaEntitlementStore): OtaVoucherResult {
        val ok = store.redeem(
            voucherId = voucher.voucherId,
            packId = voucher.packId,
            otaPartner = voucher.otaPartner,
        )
        return if (ok) {
            OtaVoucherResult.Valid(voucher)
        } else {
            OtaVoucherResult.AlreadyRedeemed(voucher)
        }
    }
}