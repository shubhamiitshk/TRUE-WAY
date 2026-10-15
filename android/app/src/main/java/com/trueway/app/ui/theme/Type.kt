package com.trueway.app.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.sp

// Default platform fonts keep full Devanagari coverage (blueprint §19.1 requires
// multilingual Unicode font testing; custom fonts arrive with content packs).
val TrueWayTypography = Typography(
    headlineSmall = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold,
        fontSize = 24.sp,
        lineHeight = 32.sp,
    ),
    titleMedium = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold,
        fontSize = 18.sp,
        lineHeight = 26.sp,
    ),
    bodyLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = androidx.compose.ui.text.font.FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 26.sp, // comfortable long-form history reading
    ),
    bodyMedium = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = androidx.compose.ui.text.font.FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 22.sp,
    ),
    labelMedium = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = androidx.compose.ui.text.font.FontWeight.Medium,
        fontSize = 12.sp,
        lineHeight = 16.sp,
    ),
)
