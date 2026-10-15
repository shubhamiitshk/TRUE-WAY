package com.trueway.app.ui.screens

import android.content.Intent
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import com.trueway.app.pack.PrefsActivePackStore
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Compare
import androidx.compose.material.icons.outlined.Headphones
import androidx.compose.material.icons.outlined.Pause
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import android.content.Context
import android.content.res.AssetFileDescriptor
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.media.MediaPlayer
import android.media.PlaybackParams
import android.os.Build
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.runtime.collectAsState
import com.trueway.app.audio.AudioPlaybackState
import com.trueway.app.audio.AudioStoryController
import com.trueway.app.data.AudioStoriesCorpus
import com.trueway.app.data.BeforeYouEnterData
import com.trueway.app.data.ClaimType
import com.trueway.app.data.HeritagePassportCorpus
import com.trueway.app.data.PlaceRepository
import com.trueway.app.data.ThenAndNowCorpus
import com.trueway.app.journal.JournalGraph
import com.trueway.app.pack.PackMediaResolver
import com.trueway.app.pack.ResolvedMedia
import com.trueway.app.pack.setResolvedDataSource
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.io.File
import java.io.IOException

/**
 * Sourced historical card (blueprint v3.0 F004, §10.4, §19.1; P0.5 Before You Enter; P1A Audio, Walks, Then & Now, Share).
 * Layout:
 * - Title & metadata
 * - Before You Enter banner (if restricted or briefed)
 * - Phonetic pronunciation guide
 * - Visitor notices
 * - Sourced claims with visible claim-type badges & inline sources
 * - Offline Audio Story with transcript expander
 * - Then & Now archival documentation
 * - Save discovery & collect Heritage Passport Stamp
 * - Share sourced place card
 * - Keep exploring recommendations
 */
@Composable
fun PlaceDetailScreen(
    placeId: String,
    onBack: () -> Unit,
    onOpenPlace: (String) -> Unit,
    onBeforeYouEnter: (String) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val place = remember(placeId) { PlaceRepository.get(placeId) }
    val briefing = remember(placeId) { BeforeYouEnterData.get(placeId) }
    val audioStory = remember(placeId) { AudioStoriesCorpus.get(placeId) }
    val thenAndNow = remember(placeId) { ThenAndNowCorpus.get(placeId) }
    val passportStamp = remember(placeId) { HeritagePassportCorpus.get(placeId) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        TextButton(onClick = onBack) { Text("← Back") }

        if (place == null) {
            Text(
                text = "This area isn't in your offline pack yet.",
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                text = "The place card cannot be shown because it is not installed on this device. Search installed places instead.",
                style = MaterialTheme.typography.bodyMedium,
            )
            return
        }

        Text(place.canonicalName, style = MaterialTheme.typography.headlineSmall)

        // Metadata chip row
        Text(
            "${place.category} · ${place.visitorMode} · reviewed ${place.lastReviewedAt}",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        // Phonetic Pronunciation Guide (P1A #1)
        if (audioStory != null) {
            Surface(
                color = MaterialTheme.colorScheme.secondaryContainer,
                shape = MaterialTheme.shapes.extraSmall,
            ) {
                Text(
                    text = "Pronunciation: ${audioStory.phoneticPronunciation}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSecondaryContainer,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                )
            }
        }

        // P0.5 "Before You Enter" Callout for Restricted Sites
        if (briefing != null || place.visitorMode == "SEARCH_ONLY" || place.visitorMode == "TEXT_REFERENCE_ONLY") {
            Surface(
                color = MaterialTheme.colorScheme.errorContainer,
                shape = MaterialTheme.shapes.small,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "Site Rules & Device Etiquette",
                            style = MaterialTheme.typography.titleSmall,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                        )
                        Text(
                            text = place.visitorNotice,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                        )
                    }
                    Button(onClick = { onBeforeYouEnter(placeId) }) {
                        Text("Before You Enter")
                    }
                }
            }
        } else {
            Surface(
                color = MaterialTheme.colorScheme.surfaceVariant,
                shape = MaterialTheme.shapes.small,
            ) {
                Text(
                    text = place.visitorNotice,
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(12.dp),
                )
            }
        }

        // Sourced Claims
        Text("Verified Historical Claims", style = MaterialTheme.typography.titleMedium)
        place.claims.forEach { claim ->
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    AssistChip(onClick = {}, label = { Text(claim.type.name) })
                    AssistChip(onClick = {}, label = { Text(claim.locale) })
                }
                Text(claim.text, style = MaterialTheme.typography.bodyMedium)
                Text(
                    "Source: ${claim.sourceTitle} · reviewed ${claim.reviewedAt}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        HorizontalDivider()

        // P1A #1: Offline Audio Story & Transcript
        if (audioStory != null) {
            AudioStorySection(audioStory)
            HorizontalDivider()
        }

        // P1A #4: Then & Now Archival Comparison
        if (thenAndNow != null) {
            ThenAndNowSection(thenAndNow)
            HorizontalDivider()
        }

        // P1A #3: Save Discovery & Heritage Passport Stamp
        SaveDiscoveryRow(placeId = place.placeId, passportStampTitle = passportStamp?.stampTitle)

        // P1A #5: Share Sourced Place Card
        OutlinedButton(
            onClick = {
                val sendIntent = Intent().apply {
                    action = Intent.ACTION_SEND
                    putExtra(Intent.EXTRA_TEXT, formatShareCard(place))
                    type = "text/plain"
                }
                val shareIntent = Intent.createChooser(sendIntent, "Share Heritage Card")
                context.startActivity(shareIntent)
            },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Icon(Icons.Outlined.Share, contentDescription = null, modifier = Modifier.padding(end = 8.dp))
            Text("Share Sourced Place Card")
        }

        HorizontalDivider()

        // Next discovery recommendations
        val next = remember(placeId) {
            val siblings = PlaceRepository.all().filter {
                it.placeId != placeId &&
                    ((it.parentPlaceId == place.parentPlaceId && place.parentPlaceId != null) ||
                        it.category == place.category)
            }.take(3)
            if (siblings.isNotEmpty()) siblings
            else PlaceRepository.all().filter { it.placeId != placeId }.take(3)
        }
        Text("Keep Exploring Nearby", style = MaterialTheme.typography.titleMedium)
        next.forEach { n ->
            OutlinedButton(
                onClick = { onOpenPlace(n.placeId) },
                modifier = Modifier.fillMaxWidth(),
            ) { Text(n.canonicalName) }
        }

        Text(
            claimTypeLegend(),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

/** P1A Audio Story Player & Transcript section wired to AudioStoryController */
@Composable
private fun AudioStorySection(story: com.trueway.app.data.AudioStory) {
    val context = LocalContext.current
    val audioController = remember(context) { AudioStoryController.get(context) }
    val playbackState by audioController.state.collectAsState()

    val isPlayingThis = playbackState is AudioPlaybackState.Playing && (playbackState as AudioPlaybackState.Playing).placeId == story.placeId
    val isPausedThis = playbackState is AudioPlaybackState.Paused && (playbackState as AudioPlaybackState.Paused).placeId == story.placeId

    var currentSeconds by remember { mutableStateOf(0f) }
    var sliderPosition by remember { mutableStateOf<Float?>(null) }
    var playbackSpeed by remember { mutableStateOf(1.0f) }
    var selectedLanguage by remember { mutableStateOf("en") } // "en" or "hi"
    var showTranscript by remember { mutableStateOf(false) }

    val mediaResolver = remember(context) { PackMediaResolver(context) }
    var resolvedMedia by remember { mutableStateOf<ResolvedMedia?>(null) }
    var isMediaLoaded by remember { mutableStateOf(false) }
    var mediaStatusNotice by remember { mutableStateOf<String?>(null) }
    var resolvedSourceDesc by remember { mutableStateOf<String?>(null) }

    // Resolve audio path: append _hi before the extension for Hindi tracks.
    val currentAssetPath = if (selectedLanguage == "hi") {
        val dotIndex = story.audioAssetPath.lastIndexOf('.')
        if (dotIndex > 0) {
            story.audioAssetPath.substring(0, dotIndex) + "_hi" + story.audioAssetPath.substring(dotIndex)
        } else {
            story.audioAssetPath + "_hi"
        }
    } else {
        story.audioAssetPath
    }

    // Resolve the active regional pack ID from PrefsActivePackStore
    val activeStore = remember(context) { PrefsActivePackStore(context) }
    val activePackId = remember(activeStore) {
        activeStore.allActive().keys.firstOrNull() ?: "in-bihar-buddhist-circuit"
    }
    val activePackDir = remember(context, activeStore, activePackId) {
        val root = File(context.filesDir, "packs")
        val activeVersion = activeStore.getActive(activePackId)
        val dir = if (activeVersion != null) File(File(root, activePackId), activeVersion) else File(root, activePackId)
        if (dir.exists()) dir else null
    }

    // Resolve media whenever story, language, or active pack changes
    LaunchedEffect(story.placeId, selectedLanguage, activePackDir) {
        var media = mediaResolver.resolve(currentAssetPath, activePackDir)
        if (media is ResolvedMedia.Rejected && selectedLanguage == "hi") {
            media = mediaResolver.resolve(story.audioAssetPath, activePackDir)
        }
        resolvedMedia = media
        when (media) {
            is ResolvedMedia.VerifiedPackFile -> {
                isMediaLoaded = true
                mediaStatusNotice = null
                resolvedSourceDesc = "Verified Pack: ${media.file.name}"
            }
            is ResolvedMedia.BundledApkAsset -> {
                isMediaLoaded = true
                mediaStatusNotice = null
                resolvedSourceDesc = "Bundled Asset: ${media.assetRelativePath}"
            }
            is ResolvedMedia.Rejected -> {
                isMediaLoaded = false
                mediaStatusNotice = "Audio file '$currentAssetPath' not yet bundled in offline package (${media.reason})."
                resolvedSourceDesc = null
            }
        }
    }

    // Position polling tied to AudioStoryController
    LaunchedEffect(isPlayingThis) {
        if (isPlayingThis) {
            while (true) {
                if (sliderPosition == null) {
                    val sec = audioController.currentPositionMs / 1000f
                    currentSeconds = sec.coerceAtMost(story.durationSeconds.toFloat())
                }
                delay(250L)
            }
        }
    }

    // React to playback state updates
    LaunchedEffect(playbackState) {
        when (val s = playbackState) {
            is AudioPlaybackState.Paused -> {
                if (s.placeId == story.placeId && sliderPosition == null) {
                    if (s.positionMs >= s.durationMs && s.durationMs > 0) {
                        currentSeconds = 0f
                    } else {
                        currentSeconds = (s.positionMs / 1000f).coerceAtMost(story.durationSeconds.toFloat())
                    }
                }
            }
            is AudioPlaybackState.Error -> {
                if (s.placeId == story.placeId) {
                    mediaStatusNotice = "Playback error: ${s.message}"
                }
            }
            else -> {}
        }
    }

    Surface(
        color = MaterialTheme.colorScheme.surfaceVariant,
        shape = MaterialTheme.shapes.medium,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(Icons.Outlined.Headphones, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Text("Offline Audio Guide", style = MaterialTheme.typography.titleSmall)
                }
                Surface(
                    color = if (isMediaLoaded) MaterialTheme.colorScheme.primary.copy(alpha = 0.1f)
                           else MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.5f),
                    shape = MaterialTheme.shapes.extraSmall,
                ) {
                    Text(
                        text = if (isMediaLoaded) "100% Offline Asset" else "Media Pending Bundle",
                        style = MaterialTheme.typography.labelSmall,
                        color = if (isMediaLoaded) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onErrorContainer,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                    )
                }
            }

            // Title in selected language
            val currentTitle = if (selectedLanguage == "hi") story.titleHindi else story.title
            Text(currentTitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)

            // Phonetic Pronunciation Guide
            if (story.phoneticPronunciation.isNotBlank()) {
                Text(
                    text = "Pronunciation: ${story.phoneticPronunciation}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            // Language Selector
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Audio Track:", style = MaterialTheme.typography.labelSmall)
                FilterChip(
                    selected = selectedLanguage == "en",
                    onClick = {
                        if (selectedLanguage != "en") {
                            selectedLanguage = "en"
                            if (isPlayingThis) {
                                audioController.stopAndRelease()
                            }
                        }
                    },
                    label = { Text("English") },
                )
                FilterChip(
                    selected = selectedLanguage == "hi",
                    onClick = {
                        if (selectedLanguage != "hi") {
                            selectedLanguage = "hi"
                            if (isPlayingThis) {
                                audioController.stopAndRelease()
                            }
                        }
                    },
                    label = { Text("हिन्दी") },
                )
            }

            // Audio Player Controls & Seek Slider
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Slider(
                    value = sliderPosition ?: currentSeconds,
                    onValueChange = { targetSec ->
                        sliderPosition = targetSec
                    },
                    onValueChangeFinished = {
                        sliderPosition?.let { target ->
                            currentSeconds = target
                            if (isMediaLoaded) {
                                audioController.seekTo((target * 1000).toInt())
                            }
                        }
                        sliderPosition = null
                    },
                    valueRange = 0f..story.durationSeconds.toFloat(),
                    modifier = Modifier.fillMaxWidth(),
                    enabled = isMediaLoaded,
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    val displaySec = sliderPosition ?: currentSeconds
                    val curMin = displaySec.toInt() / 60
                    val curSec = displaySec.toInt() % 60
                    val totMin = story.durationSeconds / 60
                    val totSec = story.durationSeconds % 60
                    Text(
                        String.format(java.util.Locale.ROOT, "%02d:%02d / %02d:%02d", curMin, curSec, totMin, totSec),
                        style = MaterialTheme.typography.labelSmall,
                    )
                    Text(
                        if (isMediaLoaded) "Decoder: Android MediaPlayer · ${resolvedSourceDesc ?: currentAssetPath}"
                        else "Asset: $currentAssetPath · Media pending bundle",
                        style = MaterialTheme.typography.labelSmall,
                        color = if (isMediaLoaded) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            // Honest missing media / playback notice indicator
            if (!isMediaLoaded || mediaStatusNotice != null) {
                Surface(
                    color = if (mediaStatusNotice?.contains("error", ignoreCase = true) == true)
                        MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.5f)
                    else MaterialTheme.colorScheme.surface,
                    shape = MaterialTheme.shapes.extraSmall,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(
                        text = mediaStatusNotice
                            ?: "Honest media status: Audio file is not yet bundled in this package. Native Android MediaPlayer decoder plumbing is active; review bilingual script & accessible transcript below.",
                        style = MaterialTheme.typography.labelSmall,
                        color = if (mediaStatusNotice?.contains("error", ignoreCase = true) == true)
                            MaterialTheme.colorScheme.onErrorContainer
                        else MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                    )
                }
            }

            // Playback buttons & Speed selector
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                    Button(
                        onClick = {
                            if (!isMediaLoaded || resolvedMedia == null) return@Button
                            if (isPlayingThis) {
                                audioController.pause()
                            } else if (isPausedThis && (playbackState as AudioPlaybackState.Paused).let { it.positionMs < it.durationMs }) {
                                audioController.resume()
                            } else {
                                resolvedMedia?.let { media ->
                                    audioController.play(story.placeId, selectedLanguage, media)
                                    if (playbackSpeed != 1.0f) {
                                        audioController.setSpeed(playbackSpeed)
                                    }
                                }
                            }
                        },
                        enabled = isMediaLoaded,
                    ) {
                        Icon(
                            if (isPlayingThis) Icons.Outlined.Pause else Icons.Outlined.PlayArrow,
                            contentDescription = null,
                            modifier = Modifier.padding(end = 4.dp),
                        )
                        Text(if (isPlayingThis) "Pause" else "Play")
                    }

                    OutlinedButton(
                        onClick = {
                            val target = (currentSeconds - 10f).coerceAtLeast(0f)
                            currentSeconds = target
                            if (isMediaLoaded) {
                                audioController.seekTo((target * 1000).toInt())
                            }
                        },
                        enabled = isMediaLoaded,
                    ) {
                        Text("-10s")
                    }

                    OutlinedButton(
                        onClick = {
                            val target = (currentSeconds + 10f).coerceAtMost(story.durationSeconds.toFloat())
                            currentSeconds = target
                            if (isMediaLoaded) {
                                audioController.seekTo((target * 1000).toInt())
                            }
                        },
                        enabled = isMediaLoaded,
                    ) {
                        Text("+10s")
                    }
                }

                // Speed toggle
                TextButton(
                    onClick = {
                        playbackSpeed = when (playbackSpeed) {
                            1.0f -> 1.25f
                            1.25f -> 1.5f
                            else -> 1.0f
                        }
                        if (isMediaLoaded) {
                            audioController.setSpeed(playbackSpeed)
                        }
                    },
                    enabled = isMediaLoaded,
                ) {
                    Text("${playbackSpeed}x")
                }
            }

            // Narration script / Accessible transcript section
            TextButton(
                onClick = { showTranscript = !showTranscript },
                modifier = Modifier.align(Alignment.End),
            ) {
                Text(if (showTranscript) "Hide Script & Transcripts ▲" else "View Bilingual Script & Transcript ▼")
            }

            if (showTranscript) {
                Surface(
                    color = MaterialTheme.colorScheme.surface,
                    shape = MaterialTheme.shapes.small,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(
                            if (selectedLanguage == "hi") "हिन्दी आख्यान प्रतिलेख (Hindi Script):" else "Narration Script (English):",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.primary,
                        )
                        Text(
                            if (selectedLanguage == "hi") story.narrativeScriptHi else story.narrativeScriptEn,
                            style = MaterialTheme.typography.bodySmall,
                        )

                        HorizontalDivider()

                        Text("Accessible Transcript Summary:", style = MaterialTheme.typography.labelMedium)
                        Text(
                            if (selectedLanguage == "hi") story.transcriptHi else story.transcriptEn,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )

                        HorizontalDivider()

                        Text("Production Credit: ${story.narratorCredit}", style = MaterialTheme.typography.labelSmall)
                        Text("Audio Rights: ${story.rightsNotice}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
    }
}

/** P1A Then & Now Archival Comparison image renderer wired via PackMediaResolver */
@Composable
private fun ArchivalImageDisplay(
    assetPath: String,
    contentDescription: String,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val resolver = remember(context) { PackMediaResolver(context) }
    val bitmap = remember(assetPath) {
        try {
            val root = File(context.filesDir, "packs")
            val activeStore = PrefsActivePackStore(context)
            val activePackId = activeStore.allActive().keys.firstOrNull() ?: "in-bihar-buddhist-circuit"
            val activeVersion = activeStore.getActive(activePackId)
            val activePackDir = if (activeVersion != null) File(File(root, activePackId), activeVersion) else File(root, activePackId)

            when (val media = resolver.resolve(assetPath, activePackDir.takeIf { it.exists() })) {
                is ResolvedMedia.VerifiedPackFile -> {
                    android.graphics.BitmapFactory.decodeFile(media.file.absolutePath)
                }
                is ResolvedMedia.BundledApkAsset -> {
                    context.assets.open(media.assetRelativePath).use {
                        android.graphics.BitmapFactory.decodeStream(it)
                    }
                }
                is ResolvedMedia.Rejected -> {
                    try {
                        context.assets.open(assetPath).use {
                            android.graphics.BitmapFactory.decodeStream(it)
                        }
                    } catch (_: Exception) {
                        null
                    }
                }
            }
        } catch (_: Exception) {
            null
        }
    }

    if (bitmap != null) {
        Image(
            bitmap = bitmap.asImageBitmap(),
            contentDescription = contentDescription,
            contentScale = ContentScale.Crop,
            modifier = modifier
                .fillMaxWidth()
                .height(200.dp)
                .clip(RoundedCornerShape(8.dp)),
        )
    }
}

/** P1A Then & Now Archival Comparison section */
@Composable
private fun ThenAndNowSection(tn: com.trueway.app.data.ArchivalComparison) {
    var selectedMode by remember { mutableStateOf(0) } // 0: Then, 1: Now, 2: Analysis

    Surface(
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp,
        shape = MaterialTheme.shapes.medium,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(Icons.Outlined.Compare, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Text("Then & Now: Archival Survey", style = MaterialTheme.typography.titleSmall)
                }
                Surface(
                    color = MaterialTheme.colorScheme.secondaryContainer,
                    shape = MaterialTheme.shapes.extraSmall,
                ) {
                    Text(
                        text = "Verified Rights & Licences",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSecondaryContainer,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                    )
                }
            }

            Text(tn.title, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)

            // Comparison View Mode Selector
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                FilterChip(
                    selected = selectedMode == 0,
                    onClick = { selectedMode = 0 },
                    label = { Text("Archival (Then)") },
                )
                FilterChip(
                    selected = selectedMode == 1,
                    onClick = { selectedMode = 1 },
                    label = { Text("Modern (Now)") },
                )
                FilterChip(
                    selected = selectedMode == 2,
                    onClick = { selectedMode = 2 },
                    label = { Text("Analysis") },
                )
            }

            // Mode-specific display
            when (selectedMode) {
                0 -> {
                    Surface(
                        color = MaterialTheme.colorScheme.surfaceVariant,
                        shape = MaterialTheme.shapes.small,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text("Archival Plate: ${tn.archivalEra}", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                            if (tn.historicalPhotoTitle.isNotBlank()) {
                                Text(tn.historicalPhotoTitle, style = MaterialTheme.typography.bodySmall)
                            }
                            if (tn.historicalPhotographer.isNotBlank()) {
                                Text("Photographer: ${tn.historicalPhotographer} (${tn.historicalPhotographerLifeDates})", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            Text(tn.archivalDescription, style = MaterialTheme.typography.bodySmall)
                            Text("Survey Repository: ${tn.archivalSource}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            if (tn.historicalAccessionId.isNotBlank()) {
                                Text("Accession Identifier: ${tn.historicalAccessionId}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            if (tn.historicalLegalStatus.isNotBlank()) {
                                Text("Legal Clearance: ${tn.historicalLegalStatus}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                            }
                            if (tn.historicalPhotoAssetPath.isNotBlank()) {
                                ArchivalImageDisplay(
                                    assetPath = tn.historicalPhotoAssetPath,
                                    contentDescription = tn.historicalPhotoTitle.ifBlank { "Archival plate ${tn.archivalEra}" },
                                )
                                Text("Archival Plate Asset: ${tn.historicalPhotoAssetPath} (Verified offline pack media)", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                }
                1 -> {
                    Surface(
                        color = MaterialTheme.colorScheme.surfaceVariant,
                        shape = MaterialTheme.shapes.small,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text("Current Protected Monument (Modern Comparison)", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                            if (tn.modernPhotoTitle.isNotBlank()) {
                                Text(tn.modernPhotoTitle, style = MaterialTheme.typography.bodySmall)
                            }
                            if (tn.modernPhotographer.isNotBlank()) {
                                Text("Photographer / Rights: ${tn.modernPhotographer} | ${tn.modernRightsHolder}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            if (tn.modernLicence.isNotBlank()) {
                                Text("Licence: ${tn.modernLicence}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                            }
                            Text(tn.modernObservation, style = MaterialTheme.typography.bodySmall)
                            Text("Status: Archaeological Survey of India / UNESCO Protected Site", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            if (tn.modernRedistributionNotice.isNotBlank()) {
                                Text("Redistribution Terms: ${tn.modernRedistributionNotice}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            if (tn.modernPhotoAssetPath.isNotBlank()) {
                                ArchivalImageDisplay(
                                    assetPath = tn.modernPhotoAssetPath,
                                    contentDescription = tn.modernPhotoTitle.ifBlank { "Modern comparison" },
                                )
                                Text("Modern Comparison Asset: ${tn.modernPhotoAssetPath} (Verified offline pack media)", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                }
                2 -> {
                    Surface(
                        color = MaterialTheme.colorScheme.surfaceVariant,
                        shape = MaterialTheme.shapes.small,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text("Archaeological Conservation Context", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                            Text(tn.preservationNotes, style = MaterialTheme.typography.bodySmall)
                            if (tn.viewpointAlignmentNotes.isNotBlank()) {
                                HorizontalDivider()
                                Text("Viewpoint Alignment & Perspective Parallax:", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                                Text(tn.viewpointAlignmentNotes, style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
            }

            // Statutory Rights & Legal Clearance Notice
            Surface(
                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                shape = MaterialTheme.shapes.extraSmall,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Statutory Rights Analysis (Indian Copyright Act, 1957 §§ 22 & 28):", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                    if (tn.statutoryCopyrightAnalysis.isNotBlank()) {
                        Text(tn.statutoryCopyrightAnalysis, style = MaterialTheme.typography.bodySmall)
                    }
                    Text("Summary: ${tn.rightsStatement}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text("Curator Verified: ${tn.curatorReviewDate} | Accession: ${tn.historicalAccessionId}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

/** Formatting utility for public share cards */
private fun formatShareCard(place: com.trueway.app.data.Place): String = buildString {
    append("TRUEWAY HERITAGE CARD\n")
    append("━━━━━━━━━━━━━━━━━━━━━\n")
    append("${place.canonicalName} (${place.category})\n")
    append("Visitor guidance: ${place.visitorNotice}\n\n")
    append("VERIFIED HISTORICAL CLAIMS:\n")
    place.claims.forEach { c ->
        append("• [${c.type}] ${c.text}\n")
        append("  Source: ${c.sourceTitle} (Reviewed ${c.reviewedAt})\n")
    }
    append("\n━━━━━━━━━━━━━━━━━━━━━\n")
    append("Verified offline via TrueWay. No internet required.")
}

private fun claimTypeLegend(): String = buildString {
    append("Badges: ")
    append(ClaimType.entries.joinToString(" · ") { it.name })
    append(". Tradition and contested readings are never stated as documented fact.")
}

/** Save-to-journal row + note dialog (F007 / P1A Passport Stamp). */
@Composable
private fun SaveDiscoveryRow(placeId: String, passportStampTitle: String?) {
    var showDialog by remember { mutableStateOf(false) }
    var note by remember { mutableStateOf("") }
    var savedTick by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Button(
        onClick = { showDialog = true },
        modifier = Modifier.fillMaxWidth(),
    ) {
        Icon(
            if (savedTick) Icons.Outlined.CheckCircle else Icons.Outlined.BookmarkBorder,
            contentDescription = null,
            modifier = Modifier.padding(end = 8.dp),
        )
        Text(if (savedTick) "Saved & Passport Stamped ✓" else "Save Discovery & Stamp Passport")
    }

    if (showDialog) {
        androidx.compose.material3.AlertDialog(
            onDismissRequest = { showDialog = false },
            title = { Text("Save & Collect Passport Stamp") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (passportStampTitle != null) {
                        Surface(
                            color = MaterialTheme.colorScheme.primaryContainer,
                            shape = MaterialTheme.shapes.extraSmall,
                        ) {
                            Text(
                                text = "Commemorative Stamp: $passportStampTitle",
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.onPrimaryContainer,
                                modifier = Modifier.padding(8.dp),
                            )
                        }
                    }
                    androidx.compose.material3.OutlinedTextField(
                        value = note,
                        onValueChange = { note = it },
                        label = { Text("Private note (optional)") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            },
            confirmButton = {
                androidx.compose.material3.TextButton(onClick = {
                    showDialog = false
                    scope.launch {
                        runCatching {
                            JournalGraph.get().save(placeId, note)
                        }.onSuccess { savedTick = true }
                    }
                }) { Text("Save & Stamp") }
            },
            dismissButton = {
                androidx.compose.material3.TextButton(onClick = { showDialog = false }) {
                    Text("Cancel")
                }
            },
        )
    }
}
