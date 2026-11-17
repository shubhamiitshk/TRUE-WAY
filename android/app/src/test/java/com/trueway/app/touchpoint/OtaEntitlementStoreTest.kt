package com.trueway.app.touchpoint

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * OTA entitlement store semantics (pure JVM, no Android runtime).
 */
class OtaEntitlementStoreTest {

    private fun store(): InMemoryOtaEntitlementStore = InMemoryOtaEntitlementStore()

    @Test
    fun `redeem unlocks pack and records redemption`() {
        val s = store()
        assertTrue(s.redeem("V-1", "in-bihar-buddhist-circuit", "viator", 1000L))
        assertTrue(s.isPackUnlocked("in-bihar-buddhist-circuit"))
        assertTrue(s.isVoucherRedeemed("V-1"))
        assertEquals(listOf("in-bihar-buddhist-circuit"), s.unlockedPackIds())
        assertEquals(1, s.redeemedVoucherCount())
        val last = s.lastRedemption()
        assertNotNull(last)
        assertEquals("V-1", last?.voucherId)
        assertEquals("viator", last?.otaPartner)
        assertEquals(1000L, last?.redeemedAtMillis)
    }

    @Test
    fun `same voucher cannot be redeemed twice`() {
        val s = store()
        assertTrue(s.redeem("V-1", "pack-a", "klook", 1000L))
        assertFalse(s.redeem("V-1", "pack-a", "klook", 2000L))
        assertEquals(1, s.redeemedVoucherCount())
    }

    @Test
    fun `different vouchers can unlock same pack`() {
        val s = store()
        assertTrue(s.redeem("V-1", "pack-a", "klook", 1000L))
        assertTrue(s.redeem("V-2", "pack-a", "viator", 2000L))
        assertEquals(listOf("pack-a"), s.unlockedPackIds())
        assertEquals(2, s.redeemedVoucherCount())
        assertEquals("V-2", s.lastRedemption()?.voucherId)
    }

    @Test
    fun `redemptions return oldest first`() {
        val s = store()
        s.redeem("V-2", "pack-b", "tripcom", 2000L)
        s.redeem("V-1", "pack-a", "viator", 1000L)
        s.redeem("V-3", "pack-a", "booking", 3000L)
        assertEquals(listOf("V-1", "V-2", "V-3"), s.redemptions().map { it.voucherId })
    }

    @Test
    fun `redeemer refuses double redemption across calls`() {
        val s = InMemoryOtaEntitlementStore()
        val payload = OtaVoucherPayload(
            voucherId = "V-9",
            otaPartner = "makemytrip",
            packId = "world-icons-tier1",
            expiresAt = null,
            issuedAt = null,
        )
        val first = OtaVoucherRedeemer.redeem(payload, s)
        val second = OtaVoucherRedeemer.redeem(payload, s)
        assertTrue(first is OtaVoucherResult.Valid)
        assertTrue(second is OtaVoucherResult.AlreadyRedeemed)
        assertTrue(s.isPackUnlocked("world-icons-tier1"))
    }

    @Test
    fun `partner and pack name mappings are human readable`() {
        assertEquals("Viator", OtaPartners.displayName("viator"))
        assertEquals("Klook", OtaPartners.displayName("klook"))
        assertEquals("MakeMyTrip", OtaPartners.displayName("makemytrip"))
        assertEquals("EaseMyTrip", OtaPartners.displayName("easyonemytip"))
        assertEquals("Trip.com", OtaPartners.displayName("tripcom"))
        assertEquals("Booking.com", OtaPartners.displayName("booking"))
        assertEquals("unknown-partner", OtaPartners.displayName("unknown-partner"))
        assertEquals("Bihar Buddhist Circuit", PackNames.displayName("in-bihar-buddhist-circuit"))
        assertEquals("India Golden Triangle", PackNames.displayName("in-golden-triangle"))
        assertEquals("World Icons Tier 1", PackNames.displayName("world-icons-tier1"))
        assertEquals("some-pack", PackNames.displayName("some-pack"))
        assertNull(null)
    }
}
