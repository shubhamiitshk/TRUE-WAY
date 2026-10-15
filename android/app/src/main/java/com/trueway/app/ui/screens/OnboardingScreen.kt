package com.trueway.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Download
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.PhotoCamera
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.trueway.app.R

/**
 * Onboarding screen — explains TrueWay's offline-first model, pack system,
 * and privacy guarantees. Shown on first launch or when no pack is installed.
 */
@Composable
fun OnboardingScreen(
    onComplete: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var currentPage by remember { mutableStateOf(0) }

    val titles = listOf(
        stringResource(R.string.onboarding_offline_title),
        stringResource(R.string.onboarding_scan_title),
        stringResource(R.string.onboarding_qr_title),
        stringResource(R.string.onboarding_privacy_title),
        stringResource(R.string.onboarding_trust_title),
    )
    val bodies = listOf(
        stringResource(R.string.onboarding_offline_body),
        stringResource(R.string.onboarding_scan_body),
        stringResource(R.string.onboarding_qr_body),
        stringResource(R.string.onboarding_privacy_body),
        stringResource(R.string.onboarding_trust_body),
    )
    val highlights = listOf(
        stringResource(R.string.onboarding_offline_highlight),
        stringResource(R.string.onboarding_scan_highlight),
        stringResource(R.string.onboarding_qr_highlight),
        stringResource(R.string.onboarding_privacy_highlight),
        stringResource(R.string.onboarding_trust_highlight),
    )
    val icons: List<ImageVector> = listOf(
        Icons.Outlined.Download,
        Icons.Outlined.PhotoCamera,
        Icons.Outlined.Search,
        Icons.Outlined.Shield,
        Icons.Outlined.CheckCircle,
    )

    Column(
        modifier = modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        // Progress indicator
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            titles.indices.forEach { index ->
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .height(4.dp)
                        .background(
                            if (index <= currentPage) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.surfaceVariant,
                            shape = MaterialTheme.shapes.extraSmall,
                        ),
                )
            }
        }

        // Page content
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentAlignment = Alignment.Center,
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Icon(
                    imageVector = icons[currentPage],
                    contentDescription = null,
                    modifier = Modifier.size(72.dp),
                    tint = MaterialTheme.colorScheme.primary,
                )
                Text(
                    text = titles[currentPage],
                    style = MaterialTheme.typography.headlineSmall,
                    textAlign = TextAlign.Center,
                )
                Text(
                    text = bodies[currentPage],
                    style = MaterialTheme.typography.bodyLarge,
                    textAlign = TextAlign.Center,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                    ),
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
                ) {
                    Text(
                        text = highlights[currentPage],
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                        modifier = Modifier.padding(16.dp),
                        textAlign = TextAlign.Center,
                    )
                }
            }
        }

        // Navigation
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (currentPage > 0) {
                OutlinedButton(
                    onClick = { currentPage-- },
                    modifier = Modifier.weight(1f),
                ) {
                    Text(stringResource(R.string.onboarding_back))
                }
            }
            if (currentPage < titles.lastIndex) {
                Button(
                    onClick = { currentPage++ },
                    modifier = Modifier.weight(1f),
                ) {
                    Text(stringResource(R.string.onboarding_next))
                }
            } else {
                Button(
                    onClick = onComplete,
                    modifier = Modifier.weight(1f),
                ) {
                    Text(stringResource(R.string.onboarding_get_started))
                }
            }
        }
        TextButton(onClick = onComplete) {
            Text(stringResource(R.string.onboarding_skip))
        }
    }
}
