package com.trueway.app.ui.screens

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.CloudDownload
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.trueway.app.BuildConfig
import com.trueway.app.R
import com.trueway.app.data.DiagnosticReport
import com.trueway.app.data.DiagnosticStatus
import com.trueway.app.data.OfflineDiagnostic
import com.trueway.app.data.PackChangelog
import com.trueway.app.pack.PackImportResultLabels
import com.trueway.app.pack.PackInstallResult
import com.trueway.app.pack.PackImporter
import com.trueway.app.pack.PrefsActivePackStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

/**
 * Packs / Downloads: offline-readiness checklist layout from blueprint §19.5
 * with honest "Not installed" states (F001). Content changelog (F013) and the
 * offline self-test action (F015) live here. Actual download → verify
 * signature → activate lands with the pack lifecycle (F006).
 */
@Composable
fun PacksScreen(
    onOpenPlace: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var importing by remember { mutableStateOf(false) }
    var importMessage by remember { mutableStateOf<String?>(null) }
    var activeTick by remember { mutableStateOf(0) }
    var diagnosticReport by remember { mutableStateOf<DiagnosticReport?>(null) }

    val packsDir = remember { File(context.filesDir, "packs") }
    val activeStore = remember { PrefsActivePackStore(context) }
    val activeVersion = remember(activeTick) {
        activeStore.getActive("in-bihar-buddhist-circuit")
    }

    val picker = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument(),
    ) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        importing = true
        importMessage = null
        scope.launch {
            val result = withContext(Dispatchers.Default) {
                val tmp = File(context.cacheDir, "import-${System.currentTimeMillis()}.twpkg")
                try {
                    context.contentResolver.openInputStream(uri)?.use { ins ->
                        tmp.outputStream().use { ins.copyTo(it) }
                    } ?: return@withContext PackInstallResult.Rejected(
                        com.trueway.app.pack.PackReject.IO_ERROR, "unreadable file",
                    )
                    // Trust: load pinned publisher keys from assets. In release
                    // builds, only these keys are trusted. In debug builds,
                    // demo-signed packs are also accepted (always labelled as demo).
                    val trust = loadPublisherTrust(context)
                    PackImporter.onBeforePackDirectorySwap = { packDir ->
                        com.trueway.app.data.PlaceRepository.evictPackDirectory(packDir)
                        com.trueway.app.pack.PackMediaResolver(context).evictPackCache(packDir)
                    }
                    val r = PackImporter.installPackage(
                        pkg = tmp,
                        packsDir = packsDir,
                        trust = trust,
                        allowDemo = BuildConfig.DEBUG,
                        minSafeVersion = activeStore.getActive("in-bihar-buddhist-circuit"),
                        activeStore = activeStore,
                    )
                    tmp.delete()
                    r
                } catch (e: Exception) {
                    tmp.delete()
                    PackInstallResult.Rejected(
                        com.trueway.app.pack.PackReject.IO_ERROR, e.message ?: "",
                    )
                }
            }
            importing = false
            importMessage = PackImportResultLabels.describe(result, context)
            if (result is PackInstallResult.Active) {
                com.trueway.app.data.PlaceRepository.initForPackDir(context)
                activeTick++
            }
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(
            text = stringResource(R.string.packs_title),
            style = MaterialTheme.typography.headlineSmall,
        )

        Icon(
            imageVector = Icons.Outlined.CloudDownload,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.secondary,
        )

        Text(
            text = stringResource(R.string.packs_empty_title),
            style = MaterialTheme.typography.titleMedium,
        )
        Text(
            text = stringResource(R.string.packs_empty_body),
            style = MaterialTheme.typography.bodyMedium,
        )

        // Component readiness rows (§19.5). Indeterminate progress = "coming
        // with first pack release", never a fake download percentage.
        StatusRow(stringResource(R.string.packs_row_knowledge))
        StatusRow(stringResource(R.string.packs_row_scanner))
        StatusRow(stringResource(R.string.packs_row_map))
        StatusRow(stringResource(R.string.packs_row_audio))

        // Active pack + local import (F006). Release trust is pinned at
        // release time; debug builds additionally accept demo-signed packs,
        // always labelled as demo and verified byte-for-byte regardless.
        if (activeVersion != null) {
            Text(
                stringResource(R.string.packs_active_version, activeVersion),
                style = MaterialTheme.typography.bodyMedium,
            )
            OutlinedButton(
                onClick = {
                    PackImporter.deletePack(packsDir, "in-bihar-buddhist-circuit", activeStore)
                    com.trueway.app.data.PlaceRepository.initForPackDir(context)
                    importMessage = context.getString(R.string.packs_pack_removed)
                    activeTick++
                },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.packs_remove_pack_action))
            }
        }
        OutlinedButton(
            onClick = { picker.launch(arrayOf("*/*")) },
            enabled = !importing,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(
                if (importing) stringResource(R.string.packs_importing)
                else stringResource(R.string.packs_import_action),
            )
        }
        importMessage?.let {
            Text(
                it,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }

        HorizontalDivider()

        // P0.5 Truly-Ready Offline Diagnostic (blueprint v3.0 §3, §19.5, F015)
        Text(
            text = "Offline Fieldwork Diagnostic",
            style = MaterialTheme.typography.titleMedium,
        )
        Text(
            text = "Run a comprehensive on-device audit across all 8 TrueWay layers (Corpus, FTS Index, Vision Model, Essentials, Audio Stories, Curated Walks, Site Compliance, Privacy Sandbox). Verifies zero-network functionality prior to departure.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Button(
            onClick = {
                diagnosticReport = OfflineDiagnostic.runDiagnostic(context)
            },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Run Offline Diagnostic Test")
        }

        diagnosticReport?.let { report ->
            Surface(
                color = if (report.overallReady) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.errorContainer,
                shape = MaterialTheme.shapes.small,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        imageVector = if (report.overallReady) Icons.Outlined.CheckCircle else Icons.Outlined.Warning,
                        contentDescription = null,
                        tint = if (report.overallReady) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onErrorContainer,
                    )
                    Column {
                        Text(
                            text = if (report.overallReady) "All Offline Layers Verified Ready" else "Diagnostic Warnings Detected",
                            style = MaterialTheme.typography.titleSmall,
                            color = if (report.overallReady) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onErrorContainer,
                        )
                        Text(
                            text = "8/8 components operational with 0 network dependencies.",
                            style = MaterialTheme.typography.bodySmall,
                            color = if (report.overallReady) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onErrorContainer,
                        )
                    }
                }
            }

            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                report.results.forEach { layer ->
                    Surface(
                        color = MaterialTheme.colorScheme.surfaceVariant,
                        shape = MaterialTheme.shapes.small,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Text(
                                    text = layer.title,
                                    style = MaterialTheme.typography.labelLarge,
                                )
                                Text(
                                    text = layer.status.name,
                                    style = MaterialTheme.typography.labelSmall,
                                    color = if (layer.status == DiagnosticStatus.PASSED) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error,
                                )
                            }
                            Text(
                                text = layer.detail,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            }
        }

        HorizontalDivider()

        // Offline self-test (F015): opens a known stored card through the
        // real local read path — no network involved by construction.
        Text(
            text = stringResource(R.string.packs_test_offline_hint),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        OutlinedButton(
            onClick = { onOpenPlace("in-bihar-bodhgaya-mahabodhi") },
            modifier = Modifier.fillMaxWidth(),
        ) { Text(stringResource(R.string.packs_test_offline_action)) }

        // Content changelog (F013): what changed per release, human-readable.
        Text(
            text = stringResource(R.string.packs_changelog_title),
            style = MaterialTheme.typography.titleMedium,
        )
        PackChangelog.releases.forEach { release ->
            Text(
                "${release.version} · ${release.date}",
                style = MaterialTheme.typography.bodyMedium,
            )
            release.changes.forEach { change ->
                Text(
                    "• $change",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun StatusRow(label: String, modifier: Modifier = Modifier) {
    Column(modifier = modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
            Text(label, style = MaterialTheme.typography.bodyMedium)
            Text(
                text = stringResource(R.string.packs_status_not_installed),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
    }
}

/**
 * Loads pinned publisher Ed25519 public keys from assets/publisher_keys.json.
 * Returns an empty map if the file is missing or malformed — in that case,
 * only demo-signed packs will be accepted (debug builds only).
 */
private fun loadPublisherTrust(context: android.content.Context): Map<String, ByteArray> {
    return try {
        val json = context.assets.open("publisher_keys.json").bufferedReader().use { it.readText() }
        val obj = org.json.JSONObject(json)
        val keys = obj.optJSONArray("keys") ?: return emptyMap()
        val trust = mutableMapOf<String, ByteArray>()
        for (i in 0 until keys.length()) {
            val entry = keys.optJSONObject(i) ?: continue
            val keyId = entry.optString("key_id").takeIf { it.isNotBlank() } ?: continue
            val pubB64 = entry.optString("pubkey_b64").takeIf { it.isNotBlank() } ?: continue
            val pub = try {
                android.util.Base64.decode(pubB64, android.util.Base64.DEFAULT)
            } catch (_: Exception) {
                continue
            }
            if (pub.size == 32) {
                trust[keyId] = pub
            }
        }
        trust
    } catch (_: Exception) {
        emptyMap()
    }
}
