package com.trueway.app.ui.screens

import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.trueway.app.R
import com.trueway.app.journal.JournalGraph
import kotlinx.coroutines.launch
import java.io.File

/**
 * Settings: privacy, permissions, language, about, one-tap deletion
 * (blueprint F015, §15.1 — deletion of personal data must be verifiable).
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    Column(modifier = modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        TopAppBar(
            title = { Text(stringResource(R.string.settings_title)) },
            navigationIcon = {
                IconButton(onClick = onBack) {
                    Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = null)
                }
            },
        )

        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp),
        ) {
            Section(
                title = stringResource(R.string.settings_privacy_title),
                body = stringResource(R.string.settings_privacy_body),
            )
            HorizontalDivider()
            Section(
                title = stringResource(R.string.settings_permissions_title),
                body = stringResource(R.string.settings_permissions_body),
            )
            HorizontalDivider()
            Section(
                title = stringResource(R.string.settings_language_title),
                body = stringResource(R.string.settings_language_body),
            )
            HorizontalDivider()
            Section(
                title = stringResource(R.string.settings_about_title),
                body = stringResource(R.string.settings_about_body),
            )
            HorizontalDivider()

            Text(
                text = stringResource(R.string.settings_clear_scans_title),
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                text = stringResource(R.string.settings_clear_scans_body),
                style = MaterialTheme.typography.bodyMedium,
            )
            OutlinedButton(
                onClick = {
                    val deleted = deleteCapturedScans(context)
                    Toast.makeText(
                        context,
                        context.getString(
                            if (deleted) R.string.settings_scans_deleted
                            else R.string.settings_scans_delete_failed,
                        ),
                        Toast.LENGTH_SHORT,
                    ).show()
                },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.settings_clear_scans_action))
            }

            HorizontalDivider()

            // One-tap deletion of ALL private data (§15 never-cut): scanner
            // photos + journal notes + achievement history + consent records.
            Text(
                text = stringResource(R.string.settings_delete_all_title),
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                text = stringResource(R.string.settings_delete_all_body),
                style = MaterialTheme.typography.bodyMedium,
            )
            OutlinedButton(
                onClick = {
                    deleteCapturedScans(context)
                    scope.launch {
                        JournalGraph.get().deleteAll()
                        Toast.makeText(
                            context,
                            context.getString(R.string.settings_all_deleted),
                            Toast.LENGTH_SHORT,
                        ).show()
                    }
                },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.settings_delete_all_action))
            }
        }
    }
}

@Composable
private fun Section(title: String, body: String) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(title, style = MaterialTheme.typography.titleMedium)
        Text(body, style = MaterialTheme.typography.bodyMedium)
    }
}

/** One-tap deletion of scanner photos (F015 / §15.1). */
private fun deleteCapturedScans(context: Context): Boolean {
    val dir = File(context.cacheDir, "scans")
    val files = dir.listFiles() ?: return false
    if (files.isEmpty()) return false
    return files.all { it.delete() }
}
