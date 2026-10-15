package com.trueway.app.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material.icons.outlined.Download
import androidx.compose.material.icons.outlined.Explore
import androidx.compose.material.icons.outlined.PhotoCamera
import androidx.compose.ui.graphics.vector.ImageVector
import com.trueway.app.R

/** Route table. Bottom navigation = Explore · Scan · Saved · Packs (blueprint §6.7). */
object Routes {
    const val ONBOARDING = "onboarding"
    const val EXPLORE = "explore"
    const val SCAN = "scan"
    const val SAVED = "saved"
    const val PACKS = "packs"
    const val SETTINGS = "settings"
    const val QR = "qr"
    const val PLACE = "place/{placeId}"
    const val BEFORE_YOU_ENTER = "before-you-enter/{placeId}"
    const val WALK = "walk/{walkId}"
    val BOTTOM = listOf(EXPLORE, SCAN, SAVED, PACKS)

    fun place(placeId: String) = "place/$placeId"
    fun beforeYouEnter(placeId: String) = "before-you-enter/$placeId"
    fun walk(walkId: String) = "walk/$walkId"
}

enum class BottomTab(
    val route: String,
    val labelRes: Int,
    val icon: ImageVector,
    val contentDescriptionRes: Int,
) {
    EXPLORE(Routes.EXPLORE, R.string.nav_explore, Icons.Outlined.Explore, R.string.nav_explore),
    SCAN(Routes.SCAN, R.string.nav_scan, Icons.Outlined.PhotoCamera, R.string.nav_scan),
    SAVED(Routes.SAVED, R.string.nav_saved, Icons.Outlined.BookmarkBorder, R.string.nav_saved),
    PACKS(Routes.PACKS, R.string.nav_downloads, Icons.Outlined.Download, R.string.nav_downloads),
}
