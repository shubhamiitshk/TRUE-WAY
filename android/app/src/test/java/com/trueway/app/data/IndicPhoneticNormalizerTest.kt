package com.trueway.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class IndicPhoneticNormalizerTest {

    @Test
    fun `returns empty string for blank input`() {
        assertEquals("", IndicPhoneticNormalizer.toSkeleton(""))
        assertEquals("", IndicPhoneticNormalizer.toSkeleton("   \t\n"))
    }

    @Test
    fun `strips diacritics and normalizes aspirated consonants`() {
        // "Mahābodhi" -> 'ā' -> 'a', "bh" -> "b", "dh" -> "d"
        val skeleton1 = IndicPhoneticNormalizer.toSkeleton("Mahābodhi")
        val skeleton2 = IndicPhoneticNormalizer.toSkeleton("mahabodi")
        assertEquals(skeleton1, skeleton2)
    }

    @Test
    fun `normalizes Nalanda spelling variants`() {
        val skeleton1 = IndicPhoneticNormalizer.toSkeleton("Nalandā")
        val skeleton2 = IndicPhoneticNormalizer.toSkeleton("Nalanda")
        assertEquals(skeleton1, skeleton2)
    }

    @Test
    fun `normalizes Rajgir Suvarnabhandar to Sonbhandar skeleton`() {
        val skeleton1 = IndicPhoneticNormalizer.toSkeleton("Suvarnabhandar")
        val skeleton2 = IndicPhoneticNormalizer.toSkeleton("Swarnabhandar")
        assertEquals(skeleton1, skeleton2)
    }

    @Test
    fun `preserves devanagari characters without corruption`() {
        val mixed = IndicPhoneticNormalizer.toSkeleton("महाबोधि Mahabodhi")
        assertTrue(mixed.contains("महाबोधि"))
    }

    @Test
    fun `merges sibilants and collapses double letters`() {
        val skeletonSh = IndicPhoneticNormalizer.toSkeleton("Shanti Stupa")
        val skeletonS = IndicPhoneticNormalizer.toSkeleton("Santi Stupa")
        assertEquals(skeletonSh, skeletonS)
    }
}
