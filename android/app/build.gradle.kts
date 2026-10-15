plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    kotlin("kapt") // same Kotlin classpath as kotlin-android; no separate version (Room compiler).
}

android {
    namespace = "com.trueway.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.trueway.app"
        // minSdk 26 keeps the entry-tier device promise (blueprint §8.3) realistic.
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables.useSupportLibrary = true
    }

    buildTypes {
        release {
            // Shrink/obfuscate once R8 rules are proven; off for the demonstrator.
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf("-Xmetadata-version=2.0.0")
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    testOptions {
        unitTests.isReturnDefaultValues = true
    }

    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
        // BouncyCastle ships duplicate versioned OSGI manifests.
        resources.excludes += "META-INF/versions/9/OSGI-INF/MANIFEST.MF"
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.activity.compose)

    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons.extended)
    implementation(libs.androidx.navigation.compose)

    // CameraX — single-shot capture bound to lifecycle (blueprint §8.2, F002).
    implementation(libs.androidx.camera.core)
    implementation(libs.androidx.camera.camera2)
    implementation(libs.androidx.camera.lifecycle)
    implementation(libs.androidx.camera.view)

    // MediaPipe ImageEmbedder — P0 scanner shell (ADR-0003 §3.1).
    // Model asset (assets/vision_encoder.tflite) is fetched on demand and
    // gitignored; absent asset = honest "not installed", never a crash.
    implementation(libs.mediapipe.tasks.vision)

    // Private journal: separate Room database file (blueprint §28.4, F007).
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    kapt(libs.androidx.room.compiler)

    // Signed QR touchpoints: ML Kit barcode scan + BouncyCastle Ed25519
    // verify (blueprint §11, F014). Only tw://place/v1 payloads are parsed;
    // http(s) QR codes are never launched (threat model §15.3).
    implementation(libs.mlkit.barcode.scanning)
    implementation(libs.bouncycastle.bcprov)

    testImplementation(libs.junit)
    testImplementation(libs.org.json)
    testImplementation(libs.sqlite.jdbc)

    androidTestImplementation(libs.junit)
    androidTestImplementation(libs.androidx.test.core)
    androidTestImplementation(libs.androidx.test.runner)
    androidTestImplementation(libs.androidx.test.ext.junit)

    debugImplementation(libs.androidx.compose.ui.tooling)
}
