// Top-level build file — plugin versions live in gradle/libs.versions.toml.
// See docs/adr/0001-technology-stack.md for why these choices were made.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
}
