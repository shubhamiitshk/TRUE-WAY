package com.trueway.app.touchpoint

import android.content.Context

/**
 * Persistent OTA voucher redemption & pack entitlement store.
 *
 * Records, per device:
 * - every OTA voucher ever redeemed (`voucherId`), and
 * - which packs are thereby unlocked (`packId`).
 *
 * Redemptions survive process death and reinstall-less restarts, and double
 * redemption of the same voucher is refused. The interface is pure JVM so
 * `InMemoryOtaEntitlementStore` can be unit-tested without an Android runtime.
 */

data class VoucherRedemption(
    val voucherId: String,
    val packId: String,
    val otaPartner: String,
    val redeemedAtMillis: Long,
)

interface OtaEntitlementStore {
    fun isVoucherRedeemed(voucherId: String): Boolean
    fun isPackUnlocked(packId: String): Boolean

    /** Redeem a voucher. Returns false if it was already redeemed on this device. */
    fun redeem(
        voucherId: String,
        packId: String,
        otaPartner: String,
        redeemedAtMillis: Long = System.currentTimeMillis(),
    ): Boolean

    /** All unlocked pack ids (unique, insertion order). */
    fun unlockedPackIds(): List<String>

    /** All redemptions, oldest first. */
    fun redemptions(): List<VoucherRedemption>

    /** The most recent redemption, if any. */
    fun lastRedemption(): VoucherRedemption? = redemptions().lastOrNull()

    fun redeemedVoucherCount(): Int = redemptions().size
}

/** Pure-Kotlin in-memory store: used by JVM tests and previews. */
class InMemoryOtaEntitlementStore : OtaEntitlementStore {
    private val events = mutableListOf<VoucherRedemption>()

    override fun isVoucherRedeemed(voucherId: String): Boolean =
        events.any { it.voucherId == voucherId }

    override fun isPackUnlocked(packId: String): Boolean =
        events.any { it.packId == packId }

    override fun redeem(
        voucherId: String,
        packId: String,
        otaPartner: String,
        redeemedAtMillis: Long,
    ): Boolean {
        if (isVoucherRedeemed(voucherId)) return false
        events.add(VoucherRedemption(voucherId, packId, otaPartner, redeemedAtMillis))
        return true
    }

    override fun unlockedPackIds(): List<String> =
        events.map { it.packId }.distinct()

    override fun redemptions(): List<VoucherRedemption> =
        events.sortedBy { it.redeemedAtMillis }
}

/** SharedPreferences-backed store used in production builds. */
class PrefsOtaEntitlementStore(context: Context) : OtaEntitlementStore {
    private val prefs = context.getSharedPreferences("trueway_entitlements", Context.MODE_PRIVATE)

    override fun isVoucherRedeemed(voucherId: String): Boolean =
        prefs.getBoolean("redeemed:$voucherId", false)

    override fun isPackUnlocked(packId: String): Boolean =
        prefs.getBoolean("unlocked:$packId", false)

    override fun redeem(
        voucherId: String,
        packId: String,
        otaPartner: String,
        redeemedAtMillis: Long,
    ): Boolean {
        if (isVoucherRedeemed(voucherId)) return false
        prefs.edit()
            .putBoolean("redeemed:$voucherId", true)
            .putBoolean("unlocked:$packId", true)
            .putString("redemption:$redeemedAtMillis", "$voucherId|$packId|$otaPartner")
            .apply()
        return true
    }

    override fun unlockedPackIds(): List<String> {
        val result = mutableListOf<String>()
        for ((key, value) in prefs.all) {
            if (key.startsWith("unlocked:") && value == true) {
                result.add(key.removePrefix("unlocked:"))
            }
        }
        return result.sorted()
    }

    override fun redemptions(): List<VoucherRedemption> {
        val result = mutableListOf<VoucherRedemption>()
        for ((key, value) in prefs.all) {
            if (!key.startsWith("redemption:") || value !is String) continue
            val parts = value.split('|', limit = 3)
            if (parts.size != 3) continue
            val ts = key.removePrefix("redemption:").toLongOrNull() ?: 0L
            result.add(VoucherRedemption(parts[0], parts[1], parts[2], ts))
        }
        return result.sortedBy { it.redeemedAtMillis }
    }
}

/** Human-facing partner names. */
object OtaPartners {
    fun displayName(partnerId: String): String = when (partnerId.lowercase()) {
        "viator" -> "Viator"
        "klook" -> "Klook"
        "makemytrip" -> "MakeMyTrip"
        "easyonemytip" -> "EaseMyTrip"
        "tripcom" -> "Trip.com"
        "booking" -> "Booking.com"
        else -> partnerId
    }
}

/** Human-facing pack names. */
object PackNames {
    fun displayName(packId: String): String = when (packId.lowercase()) {
        "in-bihar-buddhist-circuit" -> "Bihar Buddhist Circuit"
        "in-golden-triangle" -> "India Golden Triangle"
        "world-icons-tier1" -> "World Icons Tier 1"
        else -> packId
    }
}
