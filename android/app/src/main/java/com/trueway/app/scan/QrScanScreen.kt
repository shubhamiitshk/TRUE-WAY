package com.trueway.app.scan

import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.QrCode2
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
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
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import com.trueway.app.R
import com.trueway.app.data.PlaceRepository
import com.trueway.app.touchpoint.TouchpointParser
import com.trueway.app.touchpoint.TouchpointReject
import com.trueway.app.touchpoint.TouchpointResult
import com.trueway.app.touchpoint.TouchpointVerifier

/**
 * Signed site-code scanner (blueprint §11, F014; TOUCH-033…036).
 * ML Kit reads QR codes; ONLY `tw://place/v1/…` payloads and TrueWay JSON
 * envelopes are parsed — URLs and WiFi tags are ignored and never launched.
 * A valid signature authenticates the payload's publisher, NOT the plate's
 * physical placement: the verified card always shows human label + plate
 * serial with a report-mismatch route (TOUCH-036).
 */
@Composable
fun QrScanScreen(
    onOpenPlace: (String) -> Unit,
    onSearchInstead: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var outcome by remember { mutableStateOf<TouchpointResult?>(null) }

    val trust = remember {
        TouchpointVerifier.loadTrustStore(context)
    }
    val previewView = remember {
        PreviewView(context).apply { scaleType = PreviewView.ScaleType.FILL_CENTER }
    }

    if (!hasCameraPermission(context)) {
        GateCard(
            title = stringResource(R.string.scan_denied_title),
            body = stringResource(R.string.scan_denied_body),
            primaryText = stringResource(R.string.scan_site_advisory_no_camera),
            onPrimary = onSearchInstead,
            secondaryText = stringResource(R.string.nav_explore),
            onSecondary = onSearchInstead,
        )
        return
    }

    DisposableEffect(lifecycleOwner, outcome) {
        val providerFuture = ProcessCameraProvider.getInstance(context)
        val scanner = BarcodeScanning.getClient(
            BarcodeScannerOptions.Builder()
                .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
                .build(),
        )
        var bound = false
        providerFuture.addListener({
            if (outcome != null) return@addListener
            val provider = providerFuture.get()
            provider.unbindAll()
            val analysis = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
            analysis.setAnalyzer(ContextCompat.getMainExecutor(context)) { proxy ->
                if (outcome != null) {
                    proxy.close()
                    return@setAnalyzer
                }
                val media = proxy.image
                if (media == null) {
                    proxy.close()
                    return@setAnalyzer
                }
                val input = InputImage.fromMediaImage(media, proxy.imageInfo.rotationDegrees)
                scanner.process(input)
                    .addOnSuccessListener { codes ->
                        val raw = codes.firstOrNull()?.rawValue
                        if (raw != null && outcome == null) {
                            val parts = TouchpointParser.parseQrText(raw)
                            outcome = if (parts == null) {
                                TouchpointResult.Invalid(TouchpointReject.NOT_A_TOUCHPOINT)
                            } else {
                                TouchpointVerifier.verify(parts.first, parts.second, trust)
                            }
                        }
                    }
                    .addOnCompleteListener { proxy.close() }
            }
            // Preview + analysis bind together so the finder shows the live frame.
            val preview = Preview.Builder().build().also {
                it.surfaceProvider = previewView.surfaceProvider
            }
            provider.bindToLifecycle(
                lifecycleOwner,
                CameraSelector.DEFAULT_BACK_CAMERA,
                preview,
                analysis,
            )
            bound = true
        }, ContextCompat.getMainExecutor(context))
        onDispose {
            runCatching {
                if (bound) providerFuture.get().unbindAll()
            }
            runCatching { scanner.close() }
        }
    }

    Box(modifier = modifier.fillMaxSize()) {
        if (outcome == null) {
            AndroidView(factory = { previewView }, modifier = Modifier.fillMaxSize())
            QrHintOverlay(modifier = Modifier.align(Alignment.BottomCenter))
        } else {
            QrOutcomeCard(
                outcome = outcome!!,
                onOpenPlace = onOpenPlace,
                onSearchInstead = onSearchInstead,
                onBack = onBack,
                onRescan = { outcome = null },
            )
        }
    }
}

@Composable
private fun QrHintOverlay(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Icon(
            Icons.Outlined.QrCode2,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurface,
        )
        Text(
            stringResource(R.string.qr_title),
            style = MaterialTheme.typography.titleMedium,
            textAlign = TextAlign.Center,
        )
        Text(
            stringResource(R.string.qr_hint),
            style = MaterialTheme.typography.bodySmall,
            textAlign = TextAlign.Center,
        )
    }
}

@Composable
private fun QrOutcomeCard(
    outcome: TouchpointResult,
    onOpenPlace: (String) -> Unit,
    onSearchInstead: () -> Unit,
    onBack: () -> Unit,
    onRescan: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically),
    ) {
        when (outcome) {
            is TouchpointResult.Valid -> {
                val place = PlaceRepository.get(outcome.payload.placeId)
                Text(
                    stringResource(R.string.qr_verified_title),
                    style = MaterialTheme.typography.headlineSmall,
                    textAlign = TextAlign.Center,
                )
                Text(
                    stringResource(R.string.qr_verified_body, outcome.payload.issuerId),
                    style = MaterialTheme.typography.bodyMedium,
                    textAlign = TextAlign.Center,
                )
                if (place != null) {
                    Text(place.canonicalName, style = MaterialTheme.typography.titleLarge)
                }
                outcome.payload.humanLabel?.let {
                    Text(it, style = MaterialTheme.typography.bodyMedium)
                }
                outcome.payload.siteSerial?.let {
                    Text(
                        stringResource(R.string.qr_serial, it),
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                Text(
                    stringResource(R.string.qr_mismatch),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Center,
                )
                if (place != null) {
                    Button(
                        onClick = { onOpenPlace(place.placeId) },
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text(stringResource(R.string.scan_view_card)) }
                }
            }
            is TouchpointResult.ValidUnknownPlace -> {
                Text(
                    stringResource(R.string.qr_unknown_place_title),
                    style = MaterialTheme.typography.headlineSmall,
                    textAlign = TextAlign.Center,
                )
                Text(
                    stringResource(R.string.qr_unknown_place_body, outcome.payload.packId),
                    style = MaterialTheme.typography.bodyMedium,
                    textAlign = TextAlign.Center,
                )
            }
            is TouchpointResult.Invalid -> {
                Text(
                    stringResource(R.string.qr_unverified_title),
                    style = MaterialTheme.typography.headlineSmall,
                    textAlign = TextAlign.Center,
                )
                Text(
                    if (outcome.reason == TouchpointReject.EXPIRED) {
                        stringResource(R.string.qr_expired_body)
                    } else {
                        stringResource(R.string.qr_unverified_body)
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    textAlign = TextAlign.Center,
                )
            }
        }
        OutlinedButton(onClick = onSearchInstead, modifier = Modifier.fillMaxWidth()) {
            Text(stringResource(R.string.scan_site_advisory_no_camera))
        }
        TextButton(onClick = onRescan) { Text(stringResource(R.string.scan_retake)) }
        TextButton(onClick = onBack) { Text(stringResource(R.string.nav_scan)) }
    }
}

// Keep the analyzer import referenced for lint stability across build types.
