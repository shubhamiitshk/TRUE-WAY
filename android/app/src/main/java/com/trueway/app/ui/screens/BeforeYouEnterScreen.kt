package com.trueway.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.DoNotDisturb
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.trueway.app.data.BeforeYouEnterData
import com.trueway.app.data.PlaceRepository
import com.trueway.app.data.RestrictionLevel
import com.trueway.app.journal.JournalGraph
import kotlinx.coroutines.launch

/**
 * P0.5 "Before You Enter" briefing screen (blueprint v3.0 §3, §5B, §6).
 *
 * Designed specifically for restricted-device contexts like Mahabodhi Temple:
 * - Read and save outside the security perimeter.
 * - Explains official prohibition rules and permitted boundaries.
 * - Provides a "screen-free observation list" to watch for inside.
 * - Explicitly tells travelers to put device away and follow on-site staff.
 */
@Composable
fun BeforeYouEnterScreen(
    placeId: String,
    onBack: () -> Unit,
    onOpenPlace: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val place = remember(placeId) { PlaceRepository.get(placeId) }
    val briefing = remember(placeId) { BeforeYouEnterData.get(placeId) }
    val scope = rememberCoroutineScope()
    var savedTick by remember { mutableStateOf(false) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        TextButton(onClick = onBack) { Text("← Back") }

        Text(
            text = "Before You Enter",
            style = MaterialTheme.typography.headlineMedium,
        )

        val siteName = briefing?.siteName ?: place?.canonicalName ?: "Heritage Site"
        Text(
            text = siteName,
            style = MaterialTheme.typography.titleLarge,
            color = MaterialTheme.colorScheme.primary,
        )

        // Restriction Level Indicator
        val restrictionBadge = when (briefing?.restrictionLevel) {
            RestrictionLevel.DEVICE_PROHIBITED -> "Devices Prohibited (Temple Complex)"
            RestrictionLevel.PHOTOGRAPHY_RESTRICTED -> "Photography Restricted in Designated Zones"
            RestrictionLevel.ASCENT_SAFETY_HAZARD -> "Steep Hill Terrain / Sun Safety"
            RestrictionLevel.ARCHAEOLOGICAL_CAUTION -> "Fragile Archaeological Ruins"
            null -> "Site Visitor Advisory"
        }

        Surface(
            color = MaterialTheme.colorScheme.errorContainer,
            shape = MaterialTheme.shapes.medium,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Row(
                modifier = Modifier.padding(14.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    imageVector = Icons.Outlined.DoNotDisturb,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onErrorContainer,
                )
                Column {
                    Text(
                        text = restrictionBadge,
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onErrorContainer,
                    )
                    Text(
                        text = briefing?.authorityNotice
                            ?: place?.visitorNotice
                            ?: "Observe official notices posted on site.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onErrorContainer,
                    )
                    Text(
                        text = "Last verified: ${briefing?.lastVerified ?: "2026-10-12"}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onErrorContainer,
                    )
                }
            }
        }

        // Permitted Use Boundary
        Surface(
            color = MaterialTheme.colorScheme.surfaceVariant,
            shape = MaterialTheme.shapes.medium,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.padding(14.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Info,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Text(
                        text = "Permitted Use Boundary",
                        style = MaterialTheme.typography.titleSmall,
                    )
                }
                Text(
                    text = briefing?.permittedUseBoundary
                        ?: "Use your device only outside the gate where permitted. Comply with security cloakroom checks.",
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }

        // Observation Checklist (Eyes only, no screens)
        if (!briefing?.keyObservations.isNullOrEmpty()) {
            Text(
                text = "Observe With Your Own Eyes (No Screens):",
                style = MaterialTheme.typography.titleMedium,
            )
            briefing!!.keyObservations.forEach { obs ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Visibility,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(top = 2.dp),
                    )
                    Text(
                        text = obs,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        }

        // Preparation advice
        if (!briefing?.preparationAdvice.isNullOrBlank()) {
            Surface(
                color = MaterialTheme.colorScheme.primaryContainer,
                shape = MaterialTheme.shapes.medium,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Text(
                        text = "Preparation for Your Visit",
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                    Text(
                        text = briefing!!.preparationAdvice,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
            }
        }

        HorizontalDivider()

        // Action Buttons
        Button(
            onClick = {
                scope.launch {
                    runCatching {
                        JournalGraph.get().save(
                            placeId,
                            "Pre-visit briefing read before entering $siteName",
                        )
                    }.onSuccess { savedTick = true }
                }
            },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Icon(
                imageVector = if (savedTick) Icons.Outlined.CheckCircle else Icons.Outlined.BookmarkBorder,
                contentDescription = null,
                modifier = Modifier.padding(end = 8.dp),
            )
            Text(if (savedTick) "Briefing Saved to Offline Journal ✓" else "Save Briefing to Journal")
        }

        OutlinedButton(
            onClick = { onOpenPlace(placeId) },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Read Full History Card")
        }
    }
}
