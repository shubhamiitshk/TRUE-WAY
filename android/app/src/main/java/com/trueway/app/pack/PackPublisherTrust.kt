package com.trueway.app.pack

import android.content.Context

/**
 * Publisher trust store for pack signature verification, loaded from
 * `assets/publisher_keys.json` (pinned at release time). Shared by the
 * offline import picker and the in-app downloader so both paths verify packs
 * exactly the same way.
 */
object PackPublisherTrust {
    fun load(context: Context): Map<String, ByteArray> {
        return try {
            val json = context.assets.open("publisher_keys.json").bufferedReader().use { it.readText() }
            val obj = org.json.JSONObject(json)
            val keys = obj.optJSONArray("keys") ?: return emptyMap()
            val trust = mutableMapOf<String, ByteArray>()
            for (i in 0 until keys.length()) {
                val entry = keys.optJSONObject(i) ?: continue
                val keyId = entry.optString("key_id").takeIf { it.isNotBlank() } ?: continue
                val pubB64 = entry.optString("pubkey_b64").takeIf { it.isNotBlank() } ?: continue
                val pub = try {
                    android.util.Base64.decode(pubB64, android.util.Base64.DEFAULT)
                } catch (_: Exception) {
                    continue
                }
                if (pub.size == 32) trust[keyId] = pub
            }
            trust
        } catch (_: Exception) {
            emptyMap()
        }
    }
}
