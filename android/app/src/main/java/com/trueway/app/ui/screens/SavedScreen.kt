package com.trueway.app.ui.screens

import android.content.Intent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.FileDownload
import androidx.compose.material.icons.outlined.MilitaryTech
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.Code
import androidx.compose.material.icons.outlined.PictureAsPdf
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.trueway.app.R
import com.trueway.app.data.HeritagePassportCorpus
import com.trueway.app.data.PlaceRepository
import com.trueway.app.journal.JournalExporter
import com.trueway.app.journal.JournalGraph
import kotlinx.coroutines.launch

/**
 * Saved: private journal over installed places (F007, §10.1; P1A Heritage Passport F107 & Export F117).
 * Separate local database file — deleting a region pack never deletes notes.
 * Includes commemorative stamps and private export to plain text / JSON.
 */
@Composable
fun SavedScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val repo = remember { JournalGraph.get() }
    val entries by repo.entries.collectAsState(initial = emptyList())
    val scope = rememberCoroutineScope()
    var selectedEntryIds by remember { mutableStateOf<Set<String>>(emptySet()) }
    var showExportDialog by remember { mutableStateOf(false) }
    var journalQuery by remember { mutableStateOf("") }
    val snackbarHost = remember { SnackbarHostState() }

    // Determine collected passport stamps based on saved places
    val collectedStamps = remember(entries) {
        entries.mapNotNull { it.placeId?.let { pid -> HeritagePassportCorpus.get(pid) } }.distinctBy { it.stampId }
    }

    // Filter entries by place name or note text
    val visibleEntries = remember(entries, journalQuery) {
        if (journalQuery.isBlank()) entries
        else {
            val q = journalQuery.trim().lowercase()
            entries.filter { e ->
                val placeName = e.placeId?.let { PlaceRepository.get(it)?.canonicalName } ?: ""
                e.userNote?.lowercase()?.contains(q) == true ||
                    placeName.lowercase().contains(q)
            }
        }
    }

    androidx.compose.foundation.layout.Box(modifier = modifier.fillMaxSize()) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = stringResource(R.string.saved_title),
                style = MaterialTheme.typography.headlineSmall,
            )
            if (entries.isNotEmpty()) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    TextButton(onClick = {
                        selectedEntryIds = if (selectedEntryIds.size == entries.size) emptySet() else entries.map { it.entryId }.toSet()
                    }) {
                        Text(if (selectedEntryIds.size == entries.size) "Deselect" else "Select All")
                    }
                    Button(onClick = { showExportDialog = true }) {
                        Icon(Icons.Outlined.FileDownload, contentDescription = null, modifier = Modifier.padding(end = 4.dp))
                        Text(if (selectedEntryIds.isEmpty()) "Export (${entries.size})" else "Export (${selectedEntryIds.size})")
                    }
                }
            }
        }

        if (entries.isNotEmpty()) {
            OutlinedTextField(
                value = journalQuery,
                onValueChange = { journalQuery = it },
                label = { Text("Search saved notes & places") },
                leadingIcon = { Icon(Icons.Outlined.Search, contentDescription = null) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
        }

        if (showExportDialog) {
            val targetEntries = if (selectedEntryIds.isEmpty()) entries else entries.filter { it.entryId in selectedEntryIds }
            AlertDialog(
                onDismissRequest = { showExportDialog = false },
                title = { Text("Privacy-Controlled Journal Export") },
                text = {
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text(
                            text = "Exporting ${targetEntries.size} of ${entries.size} selected entries.",
                            style = MaterialTheme.typography.titleSmall,
                        )

                        Surface(
                            color = MaterialTheme.colorScheme.primaryContainer,
                            shape = MaterialTheme.shapes.small,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Row(
                                modifier = Modifier.padding(10.dp),
                                horizontalArrangement = Arrangement.spacedBy(6.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Icon(Icons.Outlined.Check, contentDescription = null, tint = MaterialTheme.colorScheme.onPrimaryContainer)
                                Text(
                                    text = "No raw GPS coordinates or device identifiers attached. Pure local export.",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                                )
                            }
                        }

                        Text(
                            text = "Itinerary Notice: Place names, place IDs, timestamps, and personal notes inherently reveal travel movements and physical whereabouts even without GPS coordinates. Once exported from TrueWay's on-device sandbox, external recipient apps manage storage permissions.",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )

                        HorizontalDivider()

                        Text("Choose Export Format:", style = MaterialTheme.typography.labelLarge)

                        // Format Option 1: JSON
                        OutlinedButton(
                            onClick = {
                                showExportDialog = false
                                val json = JournalExporter.exportToJson(targetEntries)
                                val sendIntent = Intent().apply {
                                    action = Intent.ACTION_SEND
                                    putExtra(Intent.EXTRA_TEXT, json)
                                    type = "application/json"
                                }
                                context.startActivity(Intent.createChooser(sendIntent, "Export Journal as JSON"))
                            },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Icon(Icons.Outlined.Code, contentDescription = null, modifier = Modifier.padding(end = 6.dp))
                            Text("Export as JSON (.json)")
                        }

                        // Format Option 2: PDF Document
                        OutlinedButton(
                            onClick = {
                                showExportDialog = false
                                try {
                                    val pdfFile = JournalExporter.exportToPdf(context, targetEntries)
                                    val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", pdfFile)
                                    val sendIntent = Intent().apply {
                                        action = Intent.ACTION_SEND
                                        putExtra(Intent.EXTRA_STREAM, uri)
                                        type = "application/pdf"
                                        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                                    }
                                    context.startActivity(Intent.createChooser(sendIntent, "Export Journal as PDF"))
                                } catch (_: Exception) {
                                    val plain = JournalExporter.exportToPlainText(targetEntries)
                                    val sendIntent = Intent().apply {
                                        action = Intent.ACTION_SEND
                                        putExtra(Intent.EXTRA_TEXT, plain)
                                        type = "text/plain"
                                    }
                                    context.startActivity(Intent.createChooser(sendIntent, "Export Journal"))
                                }
                            },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Icon(Icons.Outlined.PictureAsPdf, contentDescription = null, modifier = Modifier.padding(end = 6.dp))
                            Text("Export as PDF (.pdf)")
                        }

                        // Format Option 3: Plaintext
                        OutlinedButton(
                            onClick = {
                                showExportDialog = false
                                val plain = JournalExporter.exportToPlainText(targetEntries)
                                val sendIntent = Intent().apply {
                                    action = Intent.ACTION_SEND
                                    putExtra(Intent.EXTRA_TEXT, plain)
                                    type = "text/plain"
                                }
                                context.startActivity(Intent.createChooser(sendIntent, "Share Plaintext Journal"))
                            },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Icon(Icons.Outlined.FileDownload, contentDescription = null, modifier = Modifier.padding(end = 6.dp))
                            Text("Share Plaintext Summary")
                        }
                    }
                },
                confirmButton = {},
                dismissButton = {
                    TextButton(onClick = { showExportDialog = false }) {
                        Text("Cancel")
                    }
                },
            )
        }

        if (entries.isEmpty()) {
            EmptyJournal()
        } else if (visibleEntries.isEmpty()) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    "No saved entries match \"$journalQuery\".",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Center,
                )
                OutlinedButton(onClick = { journalQuery = "" }) {
                    Text("Clear search")
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                // P1A Heritage Passport Section
                if (collectedStamps.isNotEmpty()) {
                    item {
                        PassportSection(stamps = collectedStamps)
                        HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))
                        Text(
                            text = "Private Journal Entries",
                            style = MaterialTheme.typography.titleMedium,
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                }

                items(visibleEntries, key = { it.entryId }) { entry ->
                    val place = entry.placeId?.let { PlaceRepository.get(it) }
                    val stamp = entry.placeId?.let { HeritagePassportCorpus.get(it) }

                    Surface(
                        color = MaterialTheme.colorScheme.surfaceVariant,
                        shape = MaterialTheme.shapes.small,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(12.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Checkbox(
                                checked = entry.entryId in selectedEntryIds,
                                onCheckedChange = { checked ->
                                    selectedEntryIds = if (checked) {
                                        selectedEntryIds + entry.entryId
                                    } else {
                                        selectedEntryIds - entry.entryId
                                    }
                                },
                            )
                            Column(modifier = Modifier.weight(1f).padding(horizontal = 8.dp)) {
                                Text(
                                    place?.canonicalName
                                        ?: stringResource(R.string.saved_missing_place),
                                    style = MaterialTheme.typography.titleSmall,
                                )
                                if (stamp != null) {
                                    Text(
                                        "Seal: ${stamp.stampTitle}",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.primary,
                                    )
                                }
                                entry.userNote?.takeIf { it.isNotBlank() }?.let {
                                    Text(it, style = MaterialTheme.typography.bodyMedium)
                                }
                                Text(
                                    runCatching {
                                        entry.createdAt.substringBefore("T").take(10)
                                    }.getOrDefault(entry.createdAt.take(10)),
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                            IconButton(onClick = {
                                scope.launch {
                                    val snapshot = entry
                                    repo.delete(snapshot.entryId)
                                    selectedEntryIds = selectedEntryIds - snapshot.entryId
                                    val result = snackbarHost.showSnackbar(
                                        message = "Entry deleted",
                                        actionLabel = "Undo",
                                        duration = SnackbarDuration.Short,
                                    )
                                    if (result == SnackbarResult.ActionPerformed) {
                                        runCatching { repo.restore(snapshot) }
                                    }
                                }
                            }) {
                                Icon(
                                    Icons.Outlined.Delete,
                                    contentDescription = stringResource(R.string.saved_delete_cd),
                                )
                            }
                        }
                    }
                }
            }
        }

        Surface(
            color = MaterialTheme.colorScheme.surfaceVariant,
            shape = MaterialTheme.shapes.small,
        ) {
            Text(
                text = stringResource(R.string.saved_local_badge),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            )
        }
    }
    SnackbarHost(
        hostState = snackbarHost,
        modifier = Modifier.align(Alignment.BottomCenter).padding(16.dp),
    )
    }
}

/** P1A Heritage Passport visual seals section */
@Composable
private fun PassportSection(stamps: List<com.trueway.app.data.PassportStamp>) {
    Surface(
        color = MaterialTheme.colorScheme.primaryContainer,
        shape = MaterialTheme.shapes.medium,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Icon(
                    Icons.Outlined.MilitaryTech,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onPrimaryContainer,
                )
                Text(
                    text = "Personal Heritage Passport (${stamps.size} Seals)",
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                )
            }
            Text(
                text = HeritagePassportCorpus.DISCLAIMER,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
            )

            stamps.forEach { stamp ->
                Surface(
                    color = MaterialTheme.colorScheme.surface,
                    shape = MaterialTheme.shapes.extraSmall,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(modifier = Modifier.padding(8.dp)) {
                        Text(
                            text = "✦ ${stamp.stampTitle} (${stamp.stampTitleHindi})",
                            style = MaterialTheme.typography.titleSmall,
                            color = MaterialTheme.colorScheme.primary,
                        )
                        Text(
                            text = stamp.historicalInscription,
                            style = MaterialTheme.typography.bodySmall,
                        )
                        Text(
                            text = "Emblem: ${stamp.emblemDescription}",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
    }
}


@Composable
private fun EmptyJournal() {
    Icon(
        imageVector = Icons.Outlined.BookmarkBorder,
        contentDescription = null,
        modifier = Modifier.size(48.dp),
        tint = MaterialTheme.colorScheme.secondary,
    )
    Text(
        text = stringResource(R.string.saved_empty_title),
        style = MaterialTheme.typography.titleMedium,
        textAlign = TextAlign.Center,
    )
    Text(
        text = stringResource(R.string.saved_empty_body),
        style = MaterialTheme.typography.bodyLarge,
        textAlign = TextAlign.Center,
    )
}
