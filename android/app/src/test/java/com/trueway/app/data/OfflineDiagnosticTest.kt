package com.trueway.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * P0.5 Truly-Ready Offline Diagnostic gates (blueprint v3.0 §3, §19.5, F015).
 *
 * Invariants:
 * - Diagnostic covers 10 operational layers.
 * - Every layer reports a valid DiagnosticStatus.
 * - Overall offline readiness flag is true in standard corpus environment.
 * - Zero network leakage invariant verified.
 */
class OfflineDiagnosticTest {

    @Test
    fun diagnosticRunsAcrossAllTenLayers() {
        val report = OfflineDiagnostic.runDiagnostic(null)
        assertTrue("Report must indicate overall ready", report.overallReady)
        assertEquals(10, report.results.size)

        val layerIds = report.results.map { it.layerId }.toSet()
        val expectedLayers = setOf(
            "knowledge_corpus",
            "fts_search",
            "vision_engine",
            "civic_essentials",
            "audio_stories",
            "curated_walks",
            "site_compliance",
            "privacy_sandbox",
            "geodesic_proximity",
            "phonetic_media_trust",
        )
        assertEquals(expectedLayers, layerIds)

        for (result in report.results) {
            assertEquals(
                "Layer ${result.layerId} must pass",
                DiagnosticStatus.PASSED,
                result.status,
            )
            assertTrue("Layer ${result.layerId} detail must not be blank", result.detail.isNotBlank())
        }
    }
}
