package com.trueway.app.ui.screens

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.DirectionsWalk
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.SearchOff
import androidx.compose.material3.AssistChip
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.trueway.app.R
import com.trueway.app.data.CuratedWalksCorpus
import com.trueway.app.data.Essentials
import com.trueway.app.data.PlaceRepository

/**
 * Explore: local name/alias search over the installed demonstrator corpus
 * (blueprint v3.0 F003, F010, §19.3; P0.5 category filters & transliteration pills; P1A Curated Walks).
 * Ranking is name > alias > substring; GPS never reorders results.
 */
@Composable
fun ExploreScreen(
    onScanInstead: () -> Unit,
    onOpenPlace: (String) -> Unit,
    onOpenWalk: (String) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    var query by remember { mutableStateOf("") }
    var selectedCategory by remember { mutableStateOf("All") }
    val categories = listOf("All", "temple-complex", "archaeological-site", "hill-viewpoint", "chaitya", "monastery", "fortification", "sacred-tree")

    // Recent searches (in-memory, cleared on app restart)
    var recentSearches by remember { mutableStateOf(listOf<String>()) }

    // Debounce search to avoid running FTS queries on every keystroke
    val debouncedQuery = remember { mutableStateOf("") }
    LaunchedEffect(query) {
        kotlinx.coroutines.delay(300L)
        debouncedQuery.value = query
    }

    val allResults = remember(debouncedQuery.value) { PlaceRepository.search(debouncedQuery.value) }
    val filteredResults = remember(allResults, selectedCategory) {
        if (selectedCategory == "All") allResults
        else allResults.filter { it.category == selectedCategory }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(
            text = stringResource(R.string.explore_title),
            style = MaterialTheme.typography.headlineSmall,
        )

        // Search field with voice hint and clear action
        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            label = { Text(stringResource(R.string.explore_search_hint)) },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
            trailingIcon = {
                if (query.isNotBlank()) {
                    IconButton(onClick = { query = "" }) {
                        Icon(Icons.Filled.Close, contentDescription = stringResource(R.string.explore_clear_search))
                    }
                } else {
                    IconButton(onClick = { /* Voice search - future */ }) {
                        Icon(Icons.Filled.Mic, contentDescription = stringResource(R.string.explore_voice_search), tint = MaterialTheme.colorScheme.primary)
                    }
                }
            },
        )

        // P0.5 Transliteration quick-search pills
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            val quickPills = listOf("महाबोधि", "Nalanda", "Griddhakuta", "Vajrasana", "Cyclopean Wall", "Sonbhandar")
            quickPills.forEach { pill ->
                AssistChip(
                    onClick = { query = pill },
                    label = { Text(pill) },
                )
            }
        }

        // Recent searches (appear when field is empty)
        if (query.isBlank() && recentSearches.isNotEmpty()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                recentSearches.forEach { recent ->
                    AssistChip(
                        onClick = { query = recent },
                        label = { Text(recent) },
                        leadingIcon = { Icon(Icons.Filled.History, contentDescription = null, tint = MaterialTheme.colorScheme.onSurfaceVariant) },
                    )
                }
            }
        }

        // Category filter chips
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            categories.forEach { cat ->
                FilterChip(
                    selected = selectedCategory == cat,
                    onClick = { selectedCategory = cat },
                    label = { Text(cat.replace("-", " ").replaceFirstChar { it.uppercase() }) },
                )
            }
        }

        if (query.isBlank()) {
            // Empty-state card (§19.3 exact copy) — corpus summary, honest scope.
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Icon(
                    imageVector = Icons.Outlined.Info,
                    contentDescription = null,
                    modifier = Modifier.size(36.dp),
                    tint = MaterialTheme.colorScheme.secondary,
                )
                Text(
                    text = stringResource(R.string.explore_no_pack_title),
                    style = MaterialTheme.typography.titleMedium,
                    textAlign = TextAlign.Center,
                )
                Text(
                    text = stringResource(R.string.explore_demo_body),
                    style = MaterialTheme.typography.bodyMedium,
                    textAlign = TextAlign.Center,
                )
                OutlinedButton(onClick = onScanInstead) {
                    Text(stringResource(R.string.nav_scan))
                }
            }

            HorizontalDivider()

            // P1A Curated Walks Section
            CuratedWalksSection(onOpenWalk = onOpenWalk)

            HorizontalDivider()

            // F005 / F008 Offline Nearby Places Section
            NearbyPlacesSection(onOpenPlace = onOpenPlace)

        } else if (filteredResults.isEmpty()) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Icon(
                    imageVector = Icons.Outlined.SearchOff,
                    contentDescription = null,
                    modifier = Modifier.size(48.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(
                    text = stringResource(R.string.explore_no_results),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Center,
                )
                if (selectedCategory != "All") {
                    OutlinedButton(onClick = { selectedCategory = "All" }) {
                        Text(stringResource(R.string.explore_clear_filters))
                    }
                }
            }
        } else {
            // Results with enhanced cards
            Text(
                text = "${filteredResults.size} result${if (filteredResults.size == 1) "" else "s"}",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            filteredResults.forEach { place ->
                PlaceResultCard(
                    place = place,
                    onClick = {
                        if (!recentSearches.contains(place.canonicalName)) {
                            recentSearches = (listOf(place.canonicalName) + recentSearches).take(5)
                        }
                        onOpenPlace(place.placeId)
                    },
                )
            }
        }

        HorizontalDivider()

        EssentialsStrip()
    }
}

// Enhanced result card with more context
@Composable
private fun PlaceResultCard(
    place: com.trueway.app.data.Place,
    onClick: () -> Unit,
) {
    val primaryAlias = place.aliases.firstOrNull { it != place.canonicalName } ?: ""
    
    androidx.compose.material3.Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        colors = androidx.compose.material3.CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        ),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column {
                    Text(
                        text = place.canonicalName,
                        style = MaterialTheme.typography.titleSmall,
                    )
                    if (primaryAlias.isNotBlank() && primaryAlias != place.canonicalName) {
                        Text(
                            text = primaryAlias,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                // Category badge
                Surface(
                    color = MaterialTheme.colorScheme.primaryContainer,
                    shape = MaterialTheme.shapes.extraSmall,
                ) {
                    Text(
                        text = place.category.replace("-", " ").replaceFirstChar { it.uppercase() },
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                    )
                }
            }
            // Visitor mode indicator
            if (place.visitorMode.isNotBlank()) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Info,
                        contentDescription = null,
                        modifier = Modifier.size(14.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Text(
                        text = place.visitorMode,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

/** P1A Curated Walks preview strip on Explore screen */
@Composable
private fun CuratedWalksSection(onOpenWalk: (String) -> Unit) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = "Curated Heritage Walks",
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                text = "Offline Trails",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
            )
        }

        CuratedWalksCorpus.walks.forEach { walk ->
            Surface(
                color = MaterialTheme.colorScheme.surfaceVariant,
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
                            text = walk.title,
                            style = MaterialTheme.typography.titleSmall,
                            color = MaterialTheme.colorScheme.primary,
                        )
                        Text(
                            text = "~${walk.estimatedMinutes}m",
                            style = MaterialTheme.typography.labelSmall,
                        )
                    }
                    Text(
                        text = walk.summary,
                        style = MaterialTheme.typography.bodySmall,
                    )
                    OutlinedButton(
                        onClick = { onOpenWalk(walk.walkId) },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Icon(
                            Icons.AutoMirrored.Outlined.DirectionsWalk,
                            contentDescription = null,
                            modifier = Modifier.padding(end = 4.dp),
                        )
                        Text("View ${walk.stops.size}-Stop Itinerary")
                    }
                }
            }
        }
    }
}

/**
 * Offline Nearby Places section (F005 / F008): calculates proximity using on-device
 * Haversine formula against the corridor hubs or local coordinates with zero tracking.
 */
@Composable
private fun NearbyPlacesSection(onOpenPlace: (String) -> Unit) {
    var selectedHub by remember { mutableStateOf("Bodh Gaya") }
    val hubs = listOf(
        "Bodh Gaya" to Pair(24.6959, 84.9914),
        "Rajgir" to Pair(25.0038, 85.4160),
        "Nalanda" to Pair(25.1357, 85.4438),
    )
    val currentCoord = hubs.firstOrNull { it.first == selectedHub }?.second ?: Pair(24.6959, 84.9914)
    val nearbyList = remember(currentCoord) {
        PlaceRepository.nearby(currentCoord.first, currentCoord.second, maxRadiusMeters = 35_000.0)
    }

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = "Nearby Heritage Places",
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                text = "Offline Proximity",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
            )
        }

        Text(
            text = "Select reference corridor hub to view proximity-sorted sites. Calculated locally using on-device Haversine mathematics with zero network tracking.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            hubs.forEach { (name, _) ->
                FilterChip(
                    selected = selectedHub == name,
                    onClick = { selectedHub = name },
                    label = { Text(name) },
                )
            }
        }

        nearbyList.take(5).forEach { item ->
            Surface(
                color = MaterialTheme.colorScheme.surfaceVariant,
                shape = MaterialTheme.shapes.small,
                modifier = Modifier.fillMaxWidth(),
                onClick = { onOpenPlace(item.place.placeId) },
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = item.place.canonicalName,
                            style = MaterialTheme.typography.titleSmall,
                            color = MaterialTheme.colorScheme.primary,
                        )
                        Text(
                            text = item.place.category.replace("-", " ").replaceFirstChar { it.uppercase() },
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    Surface(
                        color = MaterialTheme.colorScheme.primaryContainer,
                        shape = MaterialTheme.shapes.extraSmall,
                    ) {
                        Text(
                            text = item.distanceFormatted,
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        )
                    }
                }
            }
        }
    }
}

/**
 * Offline essentials strip (F011): dated contacts + advice with the
 * connectivity caveat always attached. Reference data, never live services.
 */
@Composable
private fun EssentialsStrip(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(
            text = stringResource(R.string.essentials_title),
            style = MaterialTheme.typography.titleMedium,
        )
        Essentials.contacts.forEach { c ->
            Column {
                Text("${c.label}: ${c.value}", style = MaterialTheme.typography.bodyMedium)
                Text(
                    stringResource(R.string.essentials_verified, c.lastVerified),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        Text(
            text = Essentials.CALL_CAVEAT,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Essentials.advice.forEach { a ->
            Column {
                Text(a.title, style = MaterialTheme.typography.bodyMedium)
                Text(a.body, style = MaterialTheme.typography.bodySmall)
                Text(
                    stringResource(R.string.essentials_verified, a.lastVerified),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
