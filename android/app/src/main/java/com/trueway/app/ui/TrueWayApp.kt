package com.trueway.app.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.trueway.app.R
import com.trueway.app.navigation.BottomTab
import com.trueway.app.navigation.Routes
import com.trueway.app.scan.QrScanScreen
import com.trueway.app.scan.ScanScreen
import com.trueway.app.ui.screens.BeforeYouEnterScreen
import com.trueway.app.ui.screens.ExploreScreen
import com.trueway.app.ui.screens.OnboardingScreen
import com.trueway.app.ui.screens.PacksScreen
import com.trueway.app.ui.screens.PlaceDetailScreen
import com.trueway.app.ui.screens.SavedScreen
import com.trueway.app.ui.screens.SettingsScreen
import com.trueway.app.ui.screens.WalkDetailScreen

/**
 * Shell: bottom navigation Explore · Scan · Saved · Packs with Settings from
 * the top bar (blueprint §6.7 recommendation [D]).
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TrueWayApp() {
    val navController = rememberNavController()
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("trueway_onboarding", android.content.Context.MODE_PRIVATE) }
    var onboardingSeen by remember { mutableStateOf(prefs.getBoolean("seen", false)) }
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route
    val onOnboarding = currentRoute == Routes.ONBOARDING

    Scaffold(
        topBar = {
            if (!onOnboarding) {
                TopAppBar(
                    title = { Text("TRUEWAY", style = MaterialTheme.typography.titleMedium) },
                    actions = {
                        val settingsLabel = stringResource(R.string.nav_settings)
                        androidx.compose.material3.TextButton(
                            onClick = { navController.navigate(Routes.SETTINGS) },
                        ) { Text(settingsLabel) }
                    },
                )
            }
        },
        bottomBar = {
            if (!onOnboarding) {
                NavigationBar {
                    BottomTab.entries.forEach { tab ->
                        val label = stringResource(tab.labelRes)
                        NavigationBarItem(
                            selected = currentRoute == tab.route,
                            onClick = {
                                navController.navigate(tab.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = { Icon(tab.icon, contentDescription = label) },
                            label = { Text(label) },
                        )
                    }
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = if (onboardingSeen) Routes.EXPLORE else Routes.ONBOARDING,
            modifier = Modifier.padding(padding),
        ) {
            composable(Routes.ONBOARDING) {
                OnboardingScreen(
                    onComplete = {
                        prefs.edit().putBoolean("seen", true).apply()
                        onboardingSeen = true
                        navController.navigate(Routes.EXPLORE) {
                            popUpTo(Routes.ONBOARDING) { inclusive = true }
                        }
                    },
                )
            }
            composable(Routes.EXPLORE) {
                ExploreScreen(
                    onScanInstead = { navController.navigate(Routes.SCAN) },
                    onOpenPlace = { id -> navController.navigate(Routes.place(id)) },
                    onOpenWalk = { walkId -> navController.navigate(Routes.walk(walkId)) },
                )
            }
            composable(Routes.SCAN) {
                ScanScreen(
                    onSearchInstead = { navController.navigate(Routes.EXPLORE) },
                    onOpenPlace = { id -> navController.navigate(Routes.place(id)) },
                    onScanQr = { navController.navigate(Routes.QR) },
                )
            }
            composable(Routes.QR) {
                QrScanScreen(
                    onOpenPlace = { id -> navController.navigate(Routes.place(id)) },
                    onSearchInstead = { navController.navigate(Routes.EXPLORE) },
                    onBack = { navController.popBackStack() },
                )
            }
            composable(Routes.SAVED) { SavedScreen() }
            composable(Routes.PACKS) {
                PacksScreen(
                    onOpenPlace = { id -> navController.navigate(Routes.place(id)) },
                )
            }
            composable(
                route = Routes.PLACE,
                arguments = listOf(navArgument("placeId") { type = NavType.StringType }),
            ) { entry ->
                val id = entry.arguments?.getString("placeId").orEmpty()
                PlaceDetailScreen(
                    placeId = id,
                    onBack = { navController.popBackStack() },
                    onOpenPlace = { next -> navController.navigate(Routes.place(next)) },
                    onBeforeYouEnter = { next -> navController.navigate(Routes.beforeYouEnter(next)) },
                )
            }
            composable(
                route = Routes.BEFORE_YOU_ENTER,
                arguments = listOf(navArgument("placeId") { type = NavType.StringType }),
            ) { entry ->
                val id = entry.arguments?.getString("placeId").orEmpty()
                BeforeYouEnterScreen(
                    placeId = id,
                    onBack = { navController.popBackStack() },
                    onOpenPlace = { next -> navController.navigate(Routes.place(next)) },
                )
            }
            composable(
                route = Routes.WALK,
                arguments = listOf(navArgument("walkId") { type = NavType.StringType }),
            ) { entry ->
                val id = entry.arguments?.getString("walkId").orEmpty()
                WalkDetailScreen(
                    walkId = id,
                    onBack = { navController.popBackStack() },
                    onOpenPlace = { next -> navController.navigate(Routes.place(next)) },
                )
            }
            composable(Routes.SETTINGS) {
                SettingsScreen(onBack = { navController.popBackStack() })
            }
        }
    }
}
