package com.trueway.app.scan

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Transition tests for the Scan permission gate (blueprint F009, §19.4).
 * The gate must never strand the user: every negative path keeps a
 * no-camera route to search.
 */
class ScanGateTest {

    private fun start(): ScanGateModel = ScanGateModel()

    @Test
    fun `initial state is site advisory before any system dialog`() {
        assertEquals(ScanGateState.SiteAdvisory, start().state)
        assertFalse(start().showCamera)
        assertFalse(start().showNoCameraRoute)
    }

    @Test
    fun `advisory accepted leads to rationale not directly to camera`() {
        val model = start().reduce(ScanGateEvent.AdvisoryAccepted)
        assertEquals(ScanGateState.Rationale, model.state)
        assertFalse(model.showCamera)
        assertFalse(model.requestPermission)
    }

    @Test
    fun `rationale accepted sets one-shot permission request flag`() {
        val model = start()
            .reduce(ScanGateEvent.AdvisoryAccepted)
            .reduce(ScanGateEvent.RationaleAccepted)
        assertEquals(ScanGateState.RequestingPermission, model.state)
        assertTrue(model.requestPermission)

        val consumed = model.consumePermissionRequest()
        assertFalse(consumed.requestPermission)
        // Consuming must not change the visible state.
        assertEquals(ScanGateState.RequestingPermission, consumed.state)
    }

    @Test
    fun `granted permission opens camera`() {
        val model = start()
            .reduce(ScanGateEvent.AdvisoryAccepted)
            .reduce(ScanGateEvent.RationaleAccepted)
            .reduce(ScanGateEvent.PermissionResult(granted = true, canAskAgain = false))
        assertEquals(ScanGateState.Granted, model.state)
        assertTrue(model.showCamera)
        assertFalse(model.showNoCameraRoute)
    }

    @Test
    fun `denied but askable keeps retry and search routes`() {
        val model = start()
            .reduce(ScanGateEvent.AdvisoryAccepted)
            .reduce(ScanGateEvent.RationaleAccepted)
            .reduce(ScanGateEvent.PermissionResult(granted = false, canAskAgain = true))
        assertEquals(ScanGateState.DeniedCanAskAgain, model.state)
        assertFalse(model.showCamera)
        assertTrue(model.showNoCameraRoute)

        val retried = model.reduce(ScanGateEvent.RationaleAccepted)
        assertEquals(ScanGateState.RequestingPermission, retried.state)
        assertTrue(retried.requestPermission)
    }

    @Test
    fun `permanently denied routes to settings but never blocks search`() {
        val model = start()
            .reduce(ScanGateEvent.AdvisoryAccepted)
            .reduce(ScanGateEvent.RationaleAccepted)
            .reduce(ScanGateEvent.PermissionResult(granted = false, canAskAgain = false))
        assertEquals(ScanGateState.BlockedFromSettings, model.state)
        assertTrue(model.showNoCameraRoute)
        assertFalse(model.showCamera)
    }

    @Test
    fun `returning from settings reopens rationale before requesting again`() {
        val model = start()
            .reduce(ScanGateEvent.AdvisoryAccepted)
            .reduce(ScanGateEvent.RationaleAccepted)
            .reduce(ScanGateEvent.PermissionResult(granted = false, canAskAgain = false))
            .reduce(ScanGateEvent.RetryFromSettings)
        assertEquals(ScanGateState.Rationale, model.state)
        assertFalse(model.requestPermission)
    }

    @Test
    fun `search fallback works from any pre-grant state`() {
        for (event in listOf<ScanGateEvent>(
            ScanGateEvent.UseSearchInstead,
        )) {
            val model = start().reduce(event)
            assertEquals(ScanFallback.SEARCH, model.fallback)
            assertTrue(model.showNoCameraRoute)
        }
        // And after a denial, search remains offered.
        val denied = start()
            .reduce(ScanGateEvent.AdvisoryAccepted)
            .reduce(ScanGateEvent.RationaleAccepted)
            .reduce(ScanGateEvent.PermissionResult(granted = false, canAskAgain = true))
            .reduce(ScanGateEvent.UseSearchInstead)
        assertEquals(ScanFallback.SEARCH, denied.fallback)
        assertTrue(denied.showNoCameraRoute)
    }

    @Test
    fun `granted camera is not torn down by advisory-level events`() {
        val granted = start()
            .reduce(ScanGateEvent.AdvisoryAccepted)
            .reduce(ScanGateEvent.RationaleAccepted)
            .reduce(ScanGateEvent.PermissionResult(granted = true, canAskAgain = false))
        // UseSearchInstead in granted state must not silently disable the camera.
        val after = granted.reduce(ScanGateEvent.UseSearchInstead)
        assertEquals(ScanGateState.Granted, after.state)
        assertTrue(after.showCamera)
    }
}
