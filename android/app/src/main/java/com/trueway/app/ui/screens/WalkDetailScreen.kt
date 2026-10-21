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
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Headphones
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Pause
import androidx.compose.material.icons.outlined.Place
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.trueway.app.audio.AudioPlaybackState
import com.trueway.app.audio.AudioStoryController
import com.trueway.app.data.AudioStoriesCorpus
import com.trueway.app.data.CuratedWalksCorpus
import com.trueway.app.data.GeoUtils
import com.trueway.app.data.HeritageInsightsCorpus
import com.trueway.app.data.PlaceRepository
import com.trueway.app.pack.PackMediaResolver
import com.trueway.app.pack.PrefsActivePackStore
import com.trueway.app.pack.ResolvedMedia
import java.io.File

/**
 * P1A / P1B Curated Walk detail screen (blueprint v3.0 §3, §7, F105/F106/F112).
 *
 * Displays authored walking routes with:
 * - Estimated duration labelled as estimate.
 * - Terrain and seasonal heat advisories.
 * - F106 Foreground Trail Tracker: On-device geodesic Haversine stop-to-stop distances,
 *   active stop selector, and visited-stop progress checklist (zero background tracking).
 * - F106 Inline Offline Audio Playback: One-tap EN/HI audio story playback at each stop
 *   via [AudioStoryController] and [PackMediaResolver].
 */
@Composable
fun WalkDetailScreen(
    walkId: String,
    onBack: () -> Unit,
    onOpenPlace: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val walk = remember(walkId) { CuratedWalksCorpus.get(walkId) }
    val context = LocalContext.current
    val audioController = remember(context) { AudioStoryController.get(context) }
    val playbackState by audioController.state.collectAsState()
    val mediaResolver = remember(context) { PackMediaResolver(context) }
    val activePackDir = remember(context) {
        val activePackId = "in-bihar-buddhist-circuit"
        val root = File(context.filesDir, "packs")
        val activeVersion = PrefsActivePackStore(context).getActive(activePackId)
        val dir = if (activeVersion != null) File(File(root, activePackId), activeVersion) else File(root, activePackId)
        if (dir.exists()) dir else null
    }

    var activeStopSeq by remember(walkId) { mutableIntStateOf(1) }
    var visitedStopIds by remember(walkId) { mutableStateOf(setOf<String>()) }

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

        val activeStopPlace = remember(activeStopSeq, walk) {
            val stop = walk.stops.find { it.sequenceNumber == activeStopSeq } ?: walk.stops.firstOrNull()
            stop?.let { PlaceRepository.get(it.placeId) }
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
                        text = "${visitedStopIds.size}/${walk.stops.size} visited",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                    Text(
                        text = "Trail Progress",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
            }
        }

        // F106 Foreground Geodesic Stop Reference Selector
        Surface(
            color = MaterialTheme.colorScheme.secondaryContainer,
            shape = MaterialTheme.shapes.small,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Place,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSecondaryContainer,
                    )
                    Text(
                        text = "Foreground Trail Position & Geodesic Distance (F106)",
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onSecondaryContainer,
                    )
                }
                Text(
                    text = "Select the stop you are currently standing at to calculate offline geodesic distances to the remaining trail stops (zero background tracking):",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSecondaryContainer,
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    walk.stops.forEach { stop ->
                        FilterChip(
                            selected = activeStopSeq == stop.sequenceNumber,
                            onClick = { activeStopSeq = stop.sequenceNumber },
                            label = { Text("Stop ${stop.sequenceNumber}") },
                        )
                    }
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
            text = "Ordered Stop Sequence, Offline Audio & Site Insights",
            style = MaterialTheme.typography.titleMedium,
        )

        walk.stops.forEachIndexed { idx, stop ->
            val stopPlace = remember(stop.placeId) { PlaceRepository.get(stop.placeId) }
            val prevPlace = remember(idx, walk) {
                if (idx > 0) PlaceRepository.get(walk.stops[idx - 1].placeId) else null
            }
            val stopInsight = remember(stop.placeId) { HeritageInsightsCorpus.get(stop.placeId) }
            val topSpotter = stopInsight?.whatToSpotOnSite?.firstOrNull()
            val audioStory = remember(stop.placeId) { AudioStoriesCorpus.get(stop.placeId) }
            val isVisited = stop.placeId in visitedStopIds

            val distanceFromActiveBadge = remember(activeStopPlace, stopPlace, activeStopSeq, stop.sequenceNumber) {
                val aLat = activeStopPlace?.latitude
                val aLon = activeStopPlace?.longitude
                val sLat = stopPlace?.latitude
                val sLon = stopPlace?.longitude
                if (activeStopSeq == stop.sequenceNumber) {
                    "You are at Stop ${stop.sequenceNumber}"
                } else if (aLat != null && aLon != null && sLat != null && sLon != null) {
                    val meters = GeoUtils.distanceMeters(aLat, aLon, sLat, sLon)
                    "${GeoUtils.formatDistance(meters)} from Stop $activeStopSeq"
                } else null
            }

            val legDistanceBadge = remember(prevPlace, stopPlace) {
                val pLat = prevPlace?.latitude
                val pLon = prevPlace?.longitude
                val sLat = stopPlace?.latitude
                val sLon = stopPlace?.longitude
                if (pLat != null && pLon != null && sLat != null && sLon != null) {
                    val meters = GeoUtils.distanceMeters(pLat, pLon, sLat, sLon)
                    "Walk leg: ${GeoUtils.formatDistance(meters)} from Stop $idx"
                } else "Trail starting point"
            }

            Surface(
                color = if (activeStopSeq == stop.sequenceNumber) {
                    MaterialTheme.colorScheme.surfaceVariant
                } else {
                    MaterialTheme.colorScheme.surface
                },
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
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Stop ${stop.sequenceNumber}: ${stop.stopLabel}",
                                style = MaterialTheme.typography.titleSmall,
                                color = MaterialTheme.colorScheme.primary,
                            )
                            Text(
                                text = listOfNotNull(legDistanceBadge, distanceFromActiveBadge).joinToString(" · "),
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.secondary,
                            )
                        }
                        OutlinedButton(onClick = { onOpenPlace(stop.placeId) }) {
                            Text("View Story")
                        }
                    }

                    Text(
                        text = stop.segmentNotes,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )

                    if (stopInsight != null) {
                        HorizontalDivider(modifier = Modifier.padding(vertical = 2.dp))
                        Text(
                            text = "Site Insight: ${stopInsight.quickTakeawayEn}",
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }

                    if (topSpotter != null) {
                        Surface(
                            color = MaterialTheme.colorScheme.secondaryContainer,
                            shape = MaterialTheme.shapes.extraSmall,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text(
                                text = "Spot On-Site: ${topSpotter.featureTitle} — ${topSpotter.whereToLook}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSecondaryContainer,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                            )
                        }
                    }

                    // Inline F106 Audio Playback + Stop Visited Check
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        if (audioStory != null) {
                            val isPlayingEn = playbackState is AudioPlaybackState.Playing &&
                                (playbackState as AudioPlaybackState.Playing).placeId == stop.placeId &&
                                (playbackState as AudioPlaybackState.Playing).locale == "en"
                            val isPlayingHi = playbackState is AudioPlaybackState.Playing &&
                                (playbackState as AudioPlaybackState.Playing).placeId == stop.placeId &&
                                (playbackState as AudioPlaybackState.Playing).locale == "hi"

                            Row(
                                horizontalArrangement = Arrangement.spacedBy(6.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Icon(
                                    imageVector = Icons.Outlined.Headphones,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.primary,
                                )
                                OutlinedButton(
                                    onClick = {
                                        if (isPlayingEn) {
                                            audioController.pause()
                                        } else {
                                            val media = mediaResolver.resolve(audioStory.audioAssetPath, activePackDir)
                                            if (media !is ResolvedMedia.Rejected) {
                                                audioController.play(stop.placeId, "en", media)
                                            }
                                        }
                                    },
                                ) {
                                    Icon(
                                        imageVector = if (isPlayingEn) Icons.Outlined.Pause else Icons.Outlined.PlayArrow,
                                        contentDescription = null,
                                    )
                                    Text(if (isPlayingEn) "Pause EN" else "Audio EN")
                                }
                                OutlinedButton(
                                    onClick = {
                                        if (isPlayingHi) {
                                            audioController.pause()
                                        } else {
                                            val dotIndex = audioStory.audioAssetPath.lastIndexOf('.')
                                            val hiPath = if (dotIndex > 0) {
                                                audioStory.audioAssetPath.substring(0, dotIndex) + "_hi" + audioStory.audioAssetPath.substring(dotIndex)
                                            } else {
                                                audioStory.audioAssetPath + "_hi"
                                            }
                                            var media = mediaResolver.resolve(hiPath, activePackDir)
                                            if (media is ResolvedMedia.Rejected) {
                                                media = mediaResolver.resolve(audioStory.audioAssetPath, activePackDir)
                                            }
                                            if (media !is ResolvedMedia.Rejected) {
                                                audioController.play(stop.placeId, "hi", media)
                                            }
                                        }
                                    },
                                ) {
                                    Icon(
                                        imageVector = if (isPlayingHi) Icons.Outlined.Pause else Icons.Outlined.PlayArrow,
                                        contentDescription = null,
                                    )
                                    Text(if (isPlayingHi) "रोकें" else "हिन्दी ऑडियो")
                                }
                            }
                        } else {
                            Text(
                                text = "Text & Spotter Guide Ready",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }

                        TextButton(
                            onClick = {
                                visitedStopIds = if (isVisited) {
                                    visitedStopIds - stop.placeId
                                } else {
                                    visitedStopIds + stop.placeId
                                }
                                if (!isVisited && stop.sequenceNumber < walk.stops.size) {
                                    activeStopSeq = stop.sequenceNumber + 1
                                }
                            },
                        ) {
                            Icon(
                                imageVector = Icons.Outlined.CheckCircle,
                                contentDescription = null,
                                tint = if (isVisited) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.padding(end = 4.dp),
                            )
                            Text(if (isVisited) "Visited ✓" else "Mark Visited")
                        }
                    }
                }
            }
        }
    }
}

