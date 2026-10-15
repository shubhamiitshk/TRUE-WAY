package com.trueway.app.scan

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.PhotoCamera
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.trueway.app.R

/**
 * Scan tab gate: site advisory → point-of-use rationale → system permission →
 * camera (blueprint F009, §19.4, §6.3). Every negative path keeps the
 * no-camera route to search prominent. After capture, capture → embed →
 * rank → decide runs offline; candidate names appear only on a calibrated
 * Accept (F002/F010).
 */
@Composable
fun ScanScreen(
    onSearchInstead: () -> Unit,
    onOpenPlace: (String) -> Unit,
    onScanQr: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    var model by remember { mutableStateOf(ScanGateModel()) }
    var capturedFile by remember { mutableStateOf<java.io.File?>(null) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        val canAskAgain = !granted && shouldShowRationale(context)
        model = model.reduce(ScanGateEvent.PermissionResult(granted, canAskAgain))
    }

    LaunchedEffect(model.requestPermission) {
        if (model.requestPermission) {
            model = model.consumePermissionRequest()
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    // Permission revoked while in use (system toggle) → fall back safely.
    LaunchedEffect(model.state) {
        if (model.state == ScanGateState.Granted && !hasCameraPermission(context)) {
            model = model.reduce(
                ScanGateEvent.PermissionResult(granted = false, canAskAgain = true),
            )
        }
    }

    Box(modifier = modifier.fillMaxSize()) {
        when (model.state) {
            ScanGateState.SiteAdvisory -> GateCard(
                title = stringResource(R.string.scan_site_advisory_title),
                body = stringResource(R.string.scan_site_advisory_body),
                primaryText = stringResource(R.string.scan_site_advisory_continue),
                onPrimary = { model = model.reduce(ScanGateEvent.AdvisoryAccepted) },
                secondaryText = stringResource(R.string.scan_site_advisory_no_camera),
                onSecondary = {
                    model = model.reduce(ScanGateEvent.UseSearchInstead)
                    onSearchInstead()
                },
                icon = Icons.Outlined.PhotoCamera,
                modifier = Modifier.align(Alignment.Center),
            )

            ScanGateState.Rationale -> GateCard(
                title = stringResource(R.string.scan_permission_rationale_title),
                body = stringResource(R.string.scan_permission_rationale_body),
                primaryText = stringResource(R.string.scan_permission_request),
                onPrimary = { model = model.reduce(ScanGateEvent.RationaleAccepted) },
                secondaryText = stringResource(R.string.scan_site_advisory_no_camera),
                onSecondary = {
                    model = model.reduce(ScanGateEvent.UseSearchInstead)
                    onSearchInstead()
                },
                icon = Icons.Outlined.Info,
                modifier = Modifier.align(Alignment.Center),
            )

            ScanGateState.RequestingPermission -> Column(
                modifier = Modifier.align(Alignment.Center),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                CircularProgressIndicator(modifier = Modifier.size(36.dp))
                Text(
                    stringResource(R.string.scan_requesting_permission),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            ScanGateState.Granted -> CameraCaptureView(
                capturedFile = capturedFile,
                onCaptured = { capturedFile = it },
                onRetake = { capturedFile = null },
                onSearchInstead = onSearchInstead,
                onOpenPlace = onOpenPlace,
                onScanQr = onScanQr,
            )

            ScanGateState.DeniedCanAskAgain -> GateCard(
                title = stringResource(R.string.scan_denied_title),
                body = stringResource(R.string.scan_denied_body),
                primaryText = stringResource(R.string.scan_permission_request),
                onPrimary = { model = model.reduce(ScanGateEvent.RationaleAccepted) },
                secondaryText = stringResource(R.string.scan_site_advisory_no_camera),
                onSecondary = {
                    model = model.reduce(ScanGateEvent.UseSearchInstead)
                    onSearchInstead()
                },
                icon = Icons.Outlined.Info,
                modifier = Modifier.align(Alignment.Center),
            )

            ScanGateState.BlockedFromSettings -> GateCard(
                title = stringResource(R.string.scan_denied_title),
                body = stringResource(R.string.scan_blocked_body),
                primaryText = stringResource(R.string.scan_denied_open_settings),
                onPrimary = { openAppSettings(context) },
                secondaryText = stringResource(R.string.scan_site_advisory_no_camera),
                onSecondary = {
                    model = model.reduce(ScanGateEvent.UseSearchInstead)
                    onSearchInstead()
                },
                icon = Icons.Outlined.Settings,
                modifier = Modifier.align(Alignment.Center),
            )
        }
    }
}

@Composable
internal fun GateCard(
    title: String,
    body: String,
    primaryText: String,
    onPrimary: () -> Unit,
    secondaryText: String,
    onSecondary: () -> Unit,
    icon: androidx.compose.ui.graphics.vector.ImageVector = Icons.Outlined.PhotoCamera,
    modifier: Modifier = Modifier,
) {
    androidx.compose.foundation.layout.Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(24.dp)
            .verticalScroll(rememberScrollState()),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(40.dp),
            tint = MaterialTheme.colorScheme.secondary,
        )
        Text(title, style = MaterialTheme.typography.headlineSmall, textAlign = TextAlign.Center)
        Text(body, style = MaterialTheme.typography.bodyLarge, textAlign = TextAlign.Center)
        Button(onClick = onPrimary, modifier = Modifier.fillMaxWidth()) { Text(primaryText) }
        OutlinedButton(onClick = onSecondary, modifier = Modifier.fillMaxWidth()) {
            Icon(
                Icons.Outlined.Search,
                contentDescription = null,
                modifier = Modifier.size(18.dp),
            )
            Text(" $secondaryText")
        }
    }
}

internal fun hasCameraPermission(context: android.content.Context): Boolean =
    ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
        PackageManager.PERMISSION_GRANTED

private fun shouldShowRationale(context: android.content.Context): Boolean {
    val activity = context as? android.app.Activity ?: return false
    return activity.shouldShowRequestPermissionRationale(Manifest.permission.CAMERA)
}

internal fun openAppSettings(context: android.content.Context) {
    val intent = android.content.Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
        data = android.net.Uri.fromParts("package", context.packageName, null)
        addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
    }
    runCatching { context.startActivity(intent) }
}
