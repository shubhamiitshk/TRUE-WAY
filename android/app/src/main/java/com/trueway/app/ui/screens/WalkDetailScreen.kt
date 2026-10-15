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
import androidx.compose.material.icons.automirrored.outlined.DirectionsWalk
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Place
import androidx.compose.material.icons.outlined.Warning
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
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.trueway.app.data.CuratedWalksCorpus

/**
 * P1A Curated Walk detail screen (blueprint v3.0 §3, §7, F105/F112).
 *
 * Displays authored walking routes with:
 * - Estimated duration labelled as estimate.
 * - Terrain and seasonal heat advisories.
 * - Ordered stop sequence with segment navigation notes.
 * - Zero network or GPS requirement.
 */
@Composable
fun WalkDetailScreen(
    walkId: String,
    onBack: () -> Unit,
    onOpenPlace: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val walk = remember(walkId) { CuratedWalksCorpus.get(walkId) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        TextButton(onClick = onBack) { Text("← Back") }

        if (walk == null) {
            Text(
                text = "Walk route not found.",
                style = MaterialTheme.typography.titleMedium,
            )
            return
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            AssistChip(
                onClick = {},
                label = { Text(walk.circuitName) },
                leadingIcon = { Icon(Icons.AutoMirrored.Outlined.DirectionsWalk, contentDescription = null) },
            )
            Text(
                text = "Verified: ${walk.lastVerified}",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }

        Text(
            text = walk.title,
            style = MaterialTheme.typography.headlineSmall,
        )
        Text(
            text = walk.titleHindi,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.primary,
        )

        Text(
            text = walk.summary,
            style = MaterialTheme.typography.bodyMedium,
        )

        // Metrics Banner
        Surface(
            color = MaterialTheme.colorScheme.primaryContainer,
            shape = MaterialTheme.shapes.small,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                horizontalArrangement = Arrangement.SpaceEvenly,
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = "~${walk.estimatedMinutes} mins",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                    Text(
                        text = "Estimated Time",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = "${walk.totalDistanceKm} km",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                    Text(
                        text = "Total Distance",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = "${walk.stops.size} stops",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                    Text(
                        text = "Itinerary",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
            }
        }

        // Terrain & Heat Advisories
        Surface(
            color = MaterialTheme.colorScheme.surfaceVariant,
            shape = MaterialTheme.shapes.small,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Warning,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.secondary,
                    )
                    Text("Terrain & Mobility Notes", style = MaterialTheme.typography.titleSmall)
                }
                Text(walk.terrainNotes, style = MaterialTheme.typography.bodySmall)

                HorizontalDivider(modifier = Modifier.padding(vertical = 4.dp))

                Row(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Info,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.secondary,
                    )
                    Text("Seasonal & Weather Advisory", style = MaterialTheme.typography.titleSmall)
                }
                Text(walk.seasonalAdvisory, style = MaterialTheme.typography.bodySmall)
            }
        }

        // Stops List
        Text(
            text = "Ordered Stop Sequence",
            style = MaterialTheme.typography.titleMedium,
        )

        walk.stops.forEach { stop ->
            Surface(
                color = MaterialTheme.colorScheme.surface,
                tonalElevation = 2.dp,
                shape = MaterialTheme.shapes.small,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            text = "Stop ${stop.sequenceNumber}: ${stop.stopLabel}",
                            style = MaterialTheme.typography.titleSmall,
                            color = MaterialTheme.colorScheme.primary,
                        )
                        OutlinedButton(onClick = { onOpenPlace(stop.placeId) }) {
                            Text("View Story")
                        }
                    }
                    Text(
                        text = stop.segmentNotes,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}
