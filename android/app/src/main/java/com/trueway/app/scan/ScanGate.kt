package com.trueway.app.scan

/**
 * Pure state machine for the Scan permission/site-advisory gate (blueprint F009,
 * §19.4, §6.3). No Android types here so the transition table is unit-testable.
 *
 * Flow: SiteAdvisory → Rationale → [system permission dialog] → Granted | Denied
 *       Denied → (can ask again) Rationale  |  (permanently) Blocked
 * Blocked and Denied always keep the no-camera route (search) prominent.
 */
sealed interface ScanGateState {
    /** First visit: site-camera rules shown before any system dialog (§6.3). */
    data object SiteAdvisory : ScanGateState

    /** Point-of-use explanation immediately before the system request (§19.4). */
    data object Rationale : ScanGateState

    /** System dialog is showing; result arrives as PermissionGranted/Denied. */
    data object RequestingPermission : ScanGateState

    /** Camera usable: preview + one-shot capture. */
    data object Granted : ScanGateState

    /** Denied but the system will still show the dialog on a new request. */
    data object DeniedCanAskAgain : ScanGateState

    /** Denied with "don't ask again": only system settings can restore it. */
    data object BlockedFromSettings : ScanGateState
}

sealed interface ScanGateEvent {
    /** User accepted the site advisory and wants to continue. */
    data object AdvisoryAccepted : ScanGateEvent

    /** User asked to skip camera and use search — the always-valid fallback. */
    data object UseSearchInstead : ScanGateEvent

    /** User pressed Continue on the rationale screen; trigger system request. */
    data object RationaleAccepted : ScanGateEvent

    data class PermissionResult(val granted: Boolean, val canAskAgain: Boolean) : ScanGateEvent

    /** User returned from system settings; re-check/re-request. */
    data object RetryFromSettings : ScanGateEvent
}

/** Where the user should be sent when they decline camera use. */
enum class ScanFallback { NONE, SEARCH }

data class ScanGateModel(
    val state: ScanGateState = ScanGateState.SiteAdvisory,
    val fallback: ScanFallback = ScanFallback.NONE,
    /** True when a system permission request must be launched (side-effect flag). */
    val requestPermission: Boolean = false,
) {
    val showCamera: Boolean get() = state == ScanGateState.Granted
    val showNoCameraRoute: Boolean
        get() = state == ScanGateState.DeniedCanAskAgain ||
            state == ScanGateState.BlockedFromSettings ||
            fallback == ScanFallback.SEARCH
}

fun ScanGateModel.reduce(event: ScanGateEvent): ScanGateModel = when (event) {
    ScanGateEvent.AdvisoryAccepted -> copy(
        state = ScanGateState.Rationale,
        fallback = ScanFallback.NONE,
    )

    ScanGateEvent.UseSearchInstead -> copy(
        state = if (state == ScanGateState.Granted) state else ScanGateState.SiteAdvisory,
        fallback = ScanFallback.SEARCH,
    )

    ScanGateEvent.RationaleAccepted -> when (state) {
        ScanGateState.Rationale, ScanGateState.DeniedCanAskAgain, ScanGateState.BlockedFromSettings ->
            copy(state = ScanGateState.RequestingPermission, requestPermission = true)
        else -> copy(requestPermission = false)
    }

    is ScanGateEvent.PermissionResult -> {
        when {
            event.granted -> copy(
                state = ScanGateState.Granted,
                fallback = ScanFallback.NONE,
                requestPermission = false,
            )
            event.canAskAgain -> copy(
                state = ScanGateState.DeniedCanAskAgain,
                requestPermission = false,
            )
            else -> copy(
                state = ScanGateState.BlockedFromSettings,
                requestPermission = false,
            )
        }
    }

    ScanGateEvent.RetryFromSettings -> copy(
        state = ScanGateState.Rationale,
        requestPermission = false,
    )
}

/** One-shot consumption of the request flag so Compose fires the launcher once. */
fun ScanGateModel.consumePermissionRequest(): ScanGateModel =
    if (requestPermission) copy(requestPermission = false) else this
