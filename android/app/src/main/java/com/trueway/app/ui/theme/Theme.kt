package com.trueway.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColors = lightColorScheme(
    primary = DeepIndigo,
    onPrimary = StoneIvory,
    secondary = Terracotta,
    onSecondary = StoneIvory,
    background = StoneIvory,
    onBackground = CharcoalText,
    surface = StoneIvorySurface,
    onSurface = CharcoalText,
    surfaceVariant = StoneIvorySurface,
    onSurfaceVariant = DeepIndigo,
    error = Color(0xFF9E2A2B),
)

private val DarkColors = darkColorScheme(
    primary = NightIndigo,
    onPrimary = NightBackground,
    secondary = Terracotta,
    onSecondary = StoneIvory,
    background = NightBackground,
    onBackground = NightText,
    surface = NightSurface,
    onSurface = NightText,
    surfaceVariant = NightSurface,
    onSurfaceVariant = NightIndigo,
)

@Composable
fun TrueWayTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = TrueWayTypography,
        content = content,
    )
}
