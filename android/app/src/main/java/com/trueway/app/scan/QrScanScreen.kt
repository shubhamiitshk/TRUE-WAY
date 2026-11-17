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
import com.trueway.app.pack.PackImporter
import com.trueway.app.pack.PackVerifyResult
import com.trueway.app.pack.PackDownloader
import com.trueway.app.pack.PrefsActivePackStore
import com.trueway.app.touchpoint.OtaVoucherParser
import com.trueway.app.touchpoint.OtaVoucherReject
import com.trueway.app.touchpoint.OtaVoucherResult
import com.trueway.app.touchpoint.OtaVoucherRedeemer
import com.trueway.app.touchpoint.OtaVoucherVerifier
import com.trueway.app.touchpoint.PrefsOtaEntitlementStore
import com.trueway.app.touchpoint.TouchpointParser
import com.trueway.app.touchpoint.TouchpointReject
import com.trueway.app.touchpoint.TouchpointResult
import com.trueway.app.touchpoint.TouchpointVerifier
import java.io.File

/**
 * Represents the outcome of scanning a QR code.
 * Can be either a touchpoint result or an OTA voucher result.
 */
sealed interface ScanOutcome {
    data class Touchpoint(val result: TouchpointResult) : ScanOutcome
    data class OtaVoucher(val result: OtaVoucherResult) : ScanOutcome
    data class UnknownFormat(val rawText: String) : ScanOutcome
}

/**
 * Signed site-code and OTA voucher scanner (blueprint §11, F014; TOUCH-033…036).
 * ML Kit reads QR codes; ONLY `tw://place/v1/…` touchpoint payloads,
 * `trueway://voucher/v1/…` OTA vouchers, and TrueWay JSON envelopes are parsed —
 * URLs and WiFi tags are ignored and never launched.
 *
 * - Touchpoint: verifies Ed25519 signature against touchpoint trust store,
 *   resolves place_id against installed corpus.
 * - OTA Voucher: verifies Ed25519 signature against OTA partner trust store,
 *   unlocks the specified pack (Viator, Klook, MakeMyTrip, etc.).
 *
 * Both paths work 100% offline (no network requests).
 */
@Composable
fun QrScanScreen(
    onOpenPlace: (String) -> Unit,
    onSearchInstead: () -> Unit,
    onBack: () -> Unit,
    onVoucherRedeemed: (String) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var outcome by remember { mutableStateOf<ScanOutcome?>(null) }

    val touchpointTrust = remember {
        TouchpointVerifier.loadTrustStore(context)
    }
    val otaPartnerTrust = remember {
        OtaVoucherVerifier.loadPartnerTrustStore(context)
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
                            outcome = processScannedCode(raw, touchpointTrust, otaPartnerTrust)
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
                onVoucherRedeemed = onVoucherRedeemed,
            )
        }
    }
}

/**
 * Processes a scanned QR code and routes it to the appropriate verifier.
 * Detects whether the code is a touchpoint or an OTA voucher based on the prefix.
 */
private fun processScannedCode(
    raw: String,
    touchpointTrust: List<com.trueway.app.touchpoint.TrustedIssuer>,
    otaPartnerTrust: List<com.trueway.app.touchpoint.OtaPartnerKey>,
): ScanOutcome {
    val trimmed = raw.trim()

    // Check for touchpoint scheme
    if (trimmed.startsWith("tw://place/v1/") || trimmed.startsWith("{")) {
        val parts = TouchpointParser.parseQrText(trimmed)
        if (parts != null) {
            val result = TouchpointVerifier.verify(parts.first, parts.second, touchpointTrust)
            return ScanOutcome.Touchpoint(result)
        }
    }

    // Check for OTA voucher scheme
    if (trimmed.startsWith("trueway://voucher/v1/") || trimmed.startsWith("{")) {
        val parts = OtaVoucherParser.parseQrText(trimmed)
        if (parts != null) {
            val result = OtaVoucherVerifier.verify(parts.first, parts.second, otaPartnerTrust)
            return ScanOutcome.OtaVoucher(result)
        }
    }

    // Unknown format - not a touchpoint or OTA voucher
    return ScanOutcome.UnknownFormat(raw)
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
    outcome: ScanOutcome,
    onOpenPlace: (String) -> Unit,
    onSearchInstead: () -> Unit,
    onBack: () -> Unit,
    onRescan: () -> Unit,
    onVoucherRedeemed: (String) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically),
    ) {
        when (outcome) {
            is ScanOutcome.Touchpoint -> {
                when (val tpResult = outcome.result) {
                    is TouchpointResult.Valid -> {
                        val place = PlaceRepository.get(tpResult.payload.placeId)
                        Text(
                            stringResource(R.string.qr_verified_title),
                            style = MaterialTheme.typography.headlineSmall,
                            textAlign = TextAlign.Center,
                        )
                        Text(
                            stringResource(R.string.qr_verified_body, tpResult.payload.issuerId),
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                        )
                        if (place != null) {
                            Text(place.canonicalName, style = MaterialTheme.typography.titleLarge)
                        }
                        tpResult.payload.humanLabel?.let {
                            Text(it, style = MaterialTheme.typography.bodyMedium)
                        }
                        tpResult.payload.siteSerial?.let {
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
                            stringResource(R.string.qr_unknown_place_body, tpResult.payload.packId),
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
                            if (tpResult.reason == TouchpointReject.EXPIRED) {
                                stringResource(R.string.qr_expired_body)
                            } else {
                                stringResource(R.string.qr_unverified_body)
                            },
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                        )
                    }
                }
            }
            is ScanOutcome.OtaVoucher -> {
                when (val voucherResult = outcome.result) {
                    is OtaVoucherResult.Valid -> {
                        val payload = voucherResult.payload
                        Text(
                            "OTA Voucher Redeemed!",
                            style = MaterialTheme.typography.headlineSmall,
                            textAlign = TextAlign.Center,
                        )
                        Text(
                            "Voucher ID: ${payload.voucherId}",
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                        )
                        Text(
                            "Partner: ${payload.otaPartner.replaceFirstChar { it.uppercase() }}",
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                        )
                        Text(
                            "Pack: ${payload.packId}",
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                        )
                        if (payload.expiresAt != null) {
                            Text(
                                "Valid until: ${payload.expiresAt}",
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                        Button(
                            onClick = {
                                // Persist the redemption + entitlement (survives process death),
                                // set the entitled pack active, then let the caller navigate.
                                val store = PrefsOtaEntitlementStore(context)
                                OtaVoucherRedeemer.redeem(payload, store)
                                PrefsActivePackStore(context).setActive(payload.packId, PackDownloader.ENTITLED_PACK_VERSION)
                                onVoucherRedeemed(payload.packId)
                            },
                            modifier = Modifier.fillMaxWidth(),
                        ) { Text("Activate Pack") }
                    }
                    is OtaVoucherResult.AlreadyRedeemed -> {
                        Text(
                            "Voucher Already Redeemed",
                            style = MaterialTheme.typography.headlineSmall,
                            textAlign = TextAlign.Center,
                        )
                        Text(
                            "This voucher has already been activated on this device.",
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                        )
                        Text(
                            "Voucher ID: ${outcome.result.payload.voucherId}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    is OtaVoucherResult.Invalid -> {
                        Text(
                            "Invalid OTA Voucher",
                            style = MaterialTheme.typography.headlineSmall,
                            textAlign = TextAlign.Center,
                        )
                        Text(
                            when (voucherResult.reason) {
                                OtaVoucherReject.EXPIRED -> "This voucher has expired."
                                OtaVoucherReject.UNKNOWN_PARTNER -> "Unknown OTA partner."
                                OtaVoucherReject.BAD_SIGNATURE -> "Invalid voucher signature."
                                OtaVoucherReject.UNKNOWN_PACK -> "Pack not available."
                                else -> "This voucher could not be verified."
                            },
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                        )
                    }
                }
            }
            is ScanOutcome.UnknownFormat -> {
                Text(
                    "Unrecognized QR Code",
                    style = MaterialTheme.typography.headlineSmall,
                    textAlign = TextAlign.Center,
                )
                Text(
                    "This QR code is not a TrueWay touchpoint or OTA voucher.",
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

