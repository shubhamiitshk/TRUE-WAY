package com.trueway.app.scan

import android.content.Context
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
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
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.trueway.app.R
import com.trueway.app.data.PlaceRepository
import com.trueway.app.vision.RankDecision
import com.trueway.app.vision.ScanOutcome
import com.trueway.app.vision.runScanBlocking
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * CameraX preview + one-shot shutter (blueprint §19.1: single-shot default,
 * not a continuous recognition loop).
 *
 * Bind happens in a [DisposableEffect] keyed to the lifecycle owner; `onDispose`
 * calls `unbindAll()`, firing on backgrounding or navigation away — the Day 1–2
 * DoD item "camera released on background" (also F012).
 *
 * On success the JPEG lands in cacheDir/scans/ (private to the app; never
 * uploaded). The follow-up runs capture → embed → rank → decide offline and
 * reports a calibrated match or an explicit unknown state (F002/F010).
 */
@Composable
internal fun CameraCaptureView(
    capturedFile: File?,
    onCaptured: (File) -> Unit,
    onRetake: () -> Unit,
    onSearchInstead: () -> Unit,
    onOpenPlace: (String) -> Unit,
    onScanQr: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val previewView = remember {
        PreviewView(context).apply {
            scaleType = PreviewView.ScaleType.FILL_CENTER
            implementationMode = PreviewView.ImplementationMode.COMPATIBLE
        }
    }
    val imageCapture = remember {
        ImageCapture.Builder()
            .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
            .setFlashMode(ImageCapture.FLASH_MODE_AUTO)
            .build()
    }
    var capturing by remember { mutableStateOf(false) }
    var cameraError by remember { mutableStateOf(false) }
    var flashMode by remember { mutableStateOf(ImageCapture.FLASH_MODE_AUTO) }
    val flashLabel = when (flashMode) {
        ImageCapture.FLASH_MODE_ON -> stringResource(R.string.scan_flash_on)
        ImageCapture.FLASH_MODE_OFF -> stringResource(R.string.scan_flash_off)
        else -> stringResource(R.string.scan_flash_auto)
    }

    DisposableEffect(lifecycleOwner) {
        val future = ProcessCameraProvider.getInstance(context)
        future.addListener({
            runCatching {
                val provider = future.get()
                val preview = Preview.Builder().build().also {
                    it.surfaceProvider = previewView.surfaceProvider
                }
                provider.unbindAll()
                provider.bindToLifecycle(
                    lifecycleOwner,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    imageCapture,
                )
            }.onFailure { cameraError = true }
        }, ContextCompat.getMainExecutor(context))

        onDispose {
            // Release promptly on background/composition exit (F012, Day 1–2 DoD).
            runCatching { future.get().unbindAll() }
        }
    }

    if (capturedFile != null) {
        ResultCard(
            file = capturedFile,
            onRetake = onRetake,
            onSearchInstead = onSearchInstead,
            onOpenPlace = onOpenPlace,
        )
        return
    }

    Box(modifier = modifier.fillMaxSize()) {
        AndroidView(factory = { previewView }, modifier = Modifier.fillMaxSize())

        if (cameraError) {
            GateCard(
                title = stringResource(R.string.scan_denied_title),
                body = stringResource(R.string.scan_denied_body),
                primaryText = stringResource(R.string.scan_site_advisory_no_camera),
                onPrimary = onSearchInstead,
                secondaryText = stringResource(R.string.scan_site_advisory_no_camera),
                onSecondary = onSearchInstead,
                icon = Icons.Outlined.Info,
                modifier = Modifier.align(Alignment.Center),
            )
        } else {
            // Top bar: flash toggle + QR shortcut
            Row(
                modifier = Modifier
                    .align(Alignment.TopCenter)
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                TextButton(
                    onClick = {
                        flashMode = when (flashMode) {
                            ImageCapture.FLASH_MODE_AUTO -> ImageCapture.FLASH_MODE_ON
                            ImageCapture.FLASH_MODE_ON -> ImageCapture.FLASH_MODE_OFF
                            else -> ImageCapture.FLASH_MODE_AUTO
                        }
                        imageCapture.flashMode = flashMode
                    },
                ) {
                    Text(flashLabel)
                }
                TextButton(onClick = onScanQr) {
                    Text(stringResource(R.string.qr_scan_instead))
                }
            }
            ShutterButton(
                capturing = capturing,
                onCapture = {
                    capturing = true
                    capturePhoto(context, imageCapture) { file, ok ->
                        capturing = false
                        if (ok && file != null) onCaptured(file) else cameraError = true
                    }
                },
                onScanQr = onScanQr,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(bottom = 32.dp),
            )
        }
    }
}

@Composable
private fun ShutterButton(
    capturing: Boolean,
    onCapture: () -> Unit,
    onScanQr: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        if (capturing) {
            CircularProgressIndicator(modifier = Modifier.size(36.dp))
        } else {
            FilledTonalButton(onClick = onCapture) {
                Icon(
                    Icons.Outlined.PhotoCamera,
                    contentDescription = stringResource(R.string.scan_capture_cd),
                )
                Text(" " + stringResource(R.string.scan_capture))
            }
            TextButton(onClick = onScanQr) {
                Text(stringResource(R.string.qr_scan_instead))
            }
        }
    }
}

/**
 * Post-capture outcome (blueprint F002/F010, §7.4, §19.3).
 * Runs capture → embed → rank → decide off the main thread; each state has
 * honest copy and keeps manual search one tap away. Candidate names appear
 * ONLY on a calibrated Accept — never from an uncalibrated ranking.
 */
@Composable
private fun ResultCard(
    file: File,
    onRetake: () -> Unit,
    onSearchInstead: () -> Unit,
    onOpenPlace: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    var outcome by remember(file) { mutableStateOf<ScanOutcome?>(null) }

    LaunchedEffect(file) {
        outcome = withContext(Dispatchers.Default) {
            runScanBlocking(context.applicationContext, file)
        }
    }

    androidx.compose.foundation.layout.Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp)
            .verticalScroll(rememberScrollState()),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        when (val o = outcome) {
            null -> {
                CircularProgressIndicator(modifier = Modifier.size(36.dp))
                Text(
                    stringResource(R.string.scan_matching),
                    style = MaterialTheme.typography.bodyLarge,
                    textAlign = TextAlign.Center,
                )
            }
            ScanOutcome.NoModel -> NoModelCopy()
            ScanOutcome.NoIndex -> UnknownCopy(
                title = stringResource(R.string.explore_no_pack_title),
                body = stringResource(R.string.explore_demo_body),
                alternatives = emptyList(),
                onOpenPlace = onOpenPlace,
            )
            ScanOutcome.Uncalibrated -> UnknownCopy(
                title = stringResource(R.string.scan_uncalibrated_title),
                body = stringResource(R.string.scan_uncalibrated_body),
                alternatives = emptyList(),
                onOpenPlace = onOpenPlace,
            )
            ScanOutcome.ProcessError -> UnknownCopy(
                title = stringResource(R.string.scan_error_title),
                body = stringResource(R.string.scan_error_body),
                alternatives = emptyList(),
                onOpenPlace = onOpenPlace,
            )
            is ScanOutcome.Decided -> when (val d = o.decision) {
                is RankDecision.Accepted -> MatchCopy(
                    decision = d,
                    onOpenPlace = onOpenPlace,
                )
                is RankDecision.Uncertain -> UnknownCopy(
                    title = stringResource(R.string.scan_unknown_title),
                    body = stringResource(R.string.scan_unknown_body),
                    alternatives = d.alternatives.mapNotNull {
                        PlaceRepository.get(it.placeId)?.canonicalName?.let { name -> it.placeId to name }
                    },
                    onOpenPlace = onOpenPlace,
                )
            }
        }
        Text(
            file.name,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        androidx.compose.material3.Button(onClick = onRetake, modifier = Modifier.fillMaxWidth()) {
            Text(stringResource(R.string.scan_retake))
        }
        androidx.compose.material3.OutlinedButton(
            onClick = onSearchInstead,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Icon(
                Icons.Outlined.Search,
                contentDescription = null,
                modifier = Modifier.size(18.dp),
            )
            Text(" " + stringResource(R.string.scan_site_advisory_no_camera))
        }
    }
}

/** Encoder missing: the pre-existing honest state (F010). */
@Composable
private fun NoModelCopy() {
    Text(
        stringResource(R.string.scan_no_model_title),
        style = MaterialTheme.typography.headlineSmall,
        textAlign = TextAlign.Center,
    )
    Text(
        stringResource(R.string.scan_no_model_body),
        style = MaterialTheme.typography.bodyLarge,
        textAlign = TextAlign.Center,
    )
}

/** Calibrated accept: name + alternatives + history-card entry (F002/F004). */
@Composable
private fun MatchCopy(
    decision: RankDecision.Accepted,
    onOpenPlace: (String) -> Unit,
) {
    val place = PlaceRepository.get(decision.place.placeId)
    if (place == null) {
        // Index references a place outside the installed corpus: abstain.
        UnknownCopy(
            title = stringResource(R.string.scan_unknown_title),
            body = stringResource(R.string.scan_unknown_body),
            alternatives = emptyList(),
            onOpenPlace = onOpenPlace,
        )
        return
    }
    Text(
        stringResource(R.string.scan_match_title),
        style = MaterialTheme.typography.headlineSmall,
        textAlign = TextAlign.Center,
    )
    Text(
        place.canonicalName,
        style = MaterialTheme.typography.titleLarge,
        textAlign = TextAlign.Center,
    )
    Text(
        stringResource(R.string.scan_match_body),
        style = MaterialTheme.typography.bodyMedium,
        textAlign = TextAlign.Center,
    )
    androidx.compose.material3.Button(
        onClick = { onOpenPlace(place.placeId) },
        modifier = Modifier.fillMaxWidth(),
    ) { Text(stringResource(R.string.scan_view_card)) }
    val alts = decision.alternatives.mapNotNull {
        PlaceRepository.get(it.placeId)?.let { p -> it.placeId to p.canonicalName }
    }
    if (alts.isNotEmpty()) {
        Text(
            stringResource(R.string.scan_alternatives_title),
            style = MaterialTheme.typography.titleSmall,
        )
        alts.forEach { (id, name) ->
            androidx.compose.material3.TextButton(onClick = { onOpenPlace(id) }) { Text(name) }
        }
    }
}

/** Every abstention path: reason, resolvable alternatives, no raw IDs shown. */
@Composable
private fun UnknownCopy(
    title: String,
    body: String,
    alternatives: List<Pair<String, String>>,
    onOpenPlace: (String) -> Unit,
) {
    Text(title, style = MaterialTheme.typography.headlineSmall, textAlign = TextAlign.Center)
    Text(body, style = MaterialTheme.typography.bodyLarge, textAlign = TextAlign.Center)
    alternatives.forEach { (id, name) ->
        androidx.compose.material3.TextButton(onClick = { onOpenPlace(id) }) { Text(name) }
    }
}

private fun capturePhoto(
    context: Context,
    imageCapture: ImageCapture,
    onDone: (File?, Boolean) -> Unit,
) {
    val dir = File(context.cacheDir, "scans").apply { mkdirs() }
    val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
    val file = File(dir, "scan_$stamp.jpg")
    val options = ImageCapture.OutputFileOptions.Builder(file).build()
    imageCapture.takePicture(
        options,
        ContextCompat.getMainExecutor(context),
        object : ImageCapture.OnImageSavedCallback {
            override fun onImageSaved(output: ImageCapture.OutputFileResults) = onDone(file, true)
            override fun onError(exception: ImageCaptureException) = onDone(null, false)
        },
    )
}
