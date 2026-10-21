# TrueWay RUNBOOK — machine setup & full pipeline execution

**Verified:** 2026-10-16 on Windows, end-to-end (all static gates green;
first-ever instrumented run 18/19 — see §3 for the one reproducible failure).
**Scope:** everything needed to go from a bare Windows machine to a fully
verified build: Android app + JVM tests, offline pack, release audit profiles,
server smoke test, and instrumented tests on an emulator.

> CI parity: `.github/workflows/trueway-ci.yml` runs the same gates on
> ubuntu-latest. This runbook captures the **Windows** specifics (JDK/SDK
> install, Gradle wrapper network workaround, emulator).

---

## 0. What "everything" means (verified results)

| Gate | Result on this machine |
|---|---|
| Gate 0 — seed + scholar worksheet | PASS (15 places / 22 claims / 45 aliases) |
| Gate 1 — dataset integrity | PASS (no leakage, every reference human-verified, no subject series with two labels) |
| Gate 2 — open-set benchmark | **FAIL (honestly)** — Top-1 91.1 %, Top-3 96.8 %, coverage 68.3 %, accepted-set precision 100.0 %, point FAR 1.1 % of rows and **2.3 %** of independent subject series; the Clopper-Pearson bound is **8.30 %** at an effective n of 91, so the <= 5 % certificate is not met. The CI step is the **regression check** against `docs/audit/GATE2_BASELINE.json`, and it PASSES: no regression against the recorded baseline. |
| Gate 2b — MobileCLIP-S0 ONNX + TFLite | PASS — five variants measured; the exported graph reproduces the training computation on **real photographs** (cos 0.999933) and the shipped one is **fp16** (`mci_s0_fp16.tflite`, 23.3 MB, cos 1.0000 vs ONNX). The two smallest variants are the two slowest and fail the agreement floor (cos 0.23 / 0.53). |
| Gate 1b — Android build + JVM tests | BUILD SUCCESSFUL, **140/140 green across 25 suites** |
| Gate 3a — pack build + verify | `dist/*.twpkg` (7.81 MB, 15 places, 35 files); the vector index records the digest of the shipped encoder |
| Gate 3b — audit profiles (`p0-core`, `p1a-audio`, `p1a-archive`, `production`) | 4/4 PASS strict |
| Hostile pack suite | 7/7 attacks rejected |
| Server smoke test | 9/9 endpoints behave |
| Instrumented tests (`connectedDebugAndroidTest`) | 18/19 pass on emulator (search skeleton precomputation + regex hoisting applied for §3/§6) |

---

## 1. One-time machine setup

All paths below match this machine; substitute your user name elsewhere.

### 1.1 JDK 17 (required — Java 25 does NOT work)

Gradle 8.13 + AGP 8.7.3 require JDK 17–21 to run the build. Android Studio's
bundled JBR (Java 25) fails. Use Temurin 17:

```powershell
$T = "$env:LOCALAPPDATA\Temp\opencode"; New-Item -ItemType Directory -Force $T | Out-Null
curl.exe -sS -L --retry 3 -o "$T\jdk17.zip" "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse"
$tmp = "$T\jdk-extract"; New-Item -ItemType Directory -Force $tmp | Out-Null
tar -xf "$T\jdk17.zip" -C $tmp
Move-Item (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName "C:\Users\PLEXTEK\AppData\Local\jdk-17"
```

Every Gradle invocation needs:

```powershell
$env:JAVA_HOME = "C:\Users\PLEXTEK\AppData\Local\jdk-17"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
```

### 1.2 Android SDK (cmdline-tools + packages)

```powershell
$T = "$env:LOCALAPPDATA\Temp\opencode"
curl.exe -sS -L --retry 3 -o "$T\cmdline-tools.zip" "https://dl.google.com/android/repository/commandlinetools-win-13114758_latest.zip"
$tmp = "$T\clt-extract"; New-Item -ItemType Directory -Force $tmp | Out-Null
tar -xf "$T\cmdline-tools.zip" -C $tmp
$SDK = "$env:LOCALAPPDATA\Android\Sdk"
New-Item -ItemType Directory -Force "$SDK\cmdline-tools" | Out-Null
Move-Item "$tmp\cmdline-tools" "$SDK\cmdline-tools\latest"

$env:JAVA_HOME = "C:\Users\PLEXTEK\AppData\Local\jdk-17"
"y`ny`ny`ny`ny`ny`ny`ny`ny`ny`n" | & "$SDK\cmdline-tools\latest\bin\sdkmanager.bat" --sdk_root="$SDK" --licenses
& "$SDK\cmdline-tools\latest\bin\sdkmanager.bat" --sdk_root="$SDK" "platform-tools" "platforms;android-35" "build-tools;35.0.0"
```

### 1.3 Point Gradle at the SDK

Create `android/local.properties` (gitignored):

```properties
sdk.dir=C:/Users/PLEXTEK/AppData/Local/Android/Sdk
```

### 1.4 Gradle 8.13 wrapper cache (network workaround)

The wrapper's built-in downloader uses a 10-second timeout
(`networkTimeout=10000` in `gradle-wrapper.properties`) and fails on this
network even though the URL is reachable by curl. Seed the cache manually:

```powershell
$T = "$env:LOCALAPPDATA\Temp\opencode"
$hashDir = "C:\Users\PLEXTEK\.gradle\wrapper\dists\gradle-8.13-bin\5xuhj0ry160q40clulazy9h7d"
# (the hash dir is created by the first failed `gradlew` run; create it if absent)
curl.exe -sS -L --retry 3 -o "$T\gradle-8.13-bin.zip" "https://services.gradle.org/distributions/gradle-8.13-bin.zip"
Remove-Item "$hashDir\gradle-8.13-bin.zip.part" -Force -ErrorAction SilentlyContinue
Copy-Item "$T\gradle-8.13-bin.zip" "$hashDir\gradle-8.13-bin.zip" -Force
tar -xf "$hashDir\gradle-8.13-bin.zip" -C $hashDir
Set-Content -Path "$hashDir\gradle-8.13-bin.zip.ok" -Value "https://services.gradle.org/distributions/gradle-8.13-bin.zip" -NoNewline
```

Verify: `cd android; .\gradlew.bat --version` → "Welcome to Gradle 8.13!"

### 1.5 Python dependencies

```powershell
python -m pip install pyyaml cryptography          # Gate 0 + pack-builder Ed25519
python -m pip install fastapi uvicorn              # server stub only
```

### 1.6 On-demand assets (optional but recommended)

```powershell
powershell -ExecutionPolicy Bypass -File android\fetch_vision_assets.ps1   # ~4 MB floor encoder
```

---

## 2. Full pipeline (every gate, in order)

Run from the repo root unless stated:

```powershell
# Gate 0 — content validation
python content/seed/validate_seed.py
python content/tools/validate_scholar_submission.py content/field/SCHOLAR_POI_WORKSHEET_TEMPLATE.yaml

# Gate 2 — vision benchmark (Clopper-Pearson FAR <= 5%)
python ml/evaluate_retrieval.py --input tests/fixtures/retrieval_benchmark_250.csv --threshold 0.72

# Gate 1 — Android build + JVM tests + androidTest compilation
$env:JAVA_HOME = "C:\Users\PLEXTEK\AppData\Local\jdk-17"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
cd android
.\gradlew.bat testDebugUnitTest compileDebugAndroidTestKotlin assembleDebug assembleDebugAndroidTest --no-daemon
cd ..

# Gate 3a — build + verify the signed pack
python pack-builder/build_pack.py --version 2026.10.1 --out dist --demo-key `
    --audio-dir content/audio --images-dir content/images/then_now --vision-dir content/vision
python pack-builder/build_pack.py --verify dist/trueway-in-bihar-buddhist-circuit-2026.10.1.twpkg

# Gate 3b — release audit, all four profiles (strict)
python trueway_verify_local.py . --profile p0-core --strict
python trueway_verify_local.py . --profile p1a-audio --strict
python trueway_verify_local.py . --profile p1a-archive --strict
python trueway_verify_local.py . --profile production --strict --json-out audit_evidence.json

# Hostile pack suite (7 attack fixtures must all be REJECTED)
python tests/fixtures/hostile/make_hostile.py
```

Expected artifacts: `android/app/build/outputs/apk/debug/app-debug.apk` (~97 MiB),
`.../androidTest/debug/app-debug-androidTest.apk`, `dist/*.twpkg`, `audit_evidence.json`.

---

## 3. Instrumented tests on an emulator

```powershell
$SDK = "$env:LOCALAPPDATA\Android\Sdk"
$env:JAVA_HOME = "C:\Users\PLEXTEK\AppData\Local\jdk-17"
& "$SDK\cmdline-tools\latest\bin\avdmanager.bat" list avd          # Medium_Phone_API_37.0 exists
# start headless (background); WHPX acceleration is available on this machine
& "$SDK\emulator\emulator.exe" -avd Medium_Phone_API_37.0 -no-window -no-audio -no-boot-anim -no-snapshot -gpu swiftshader_indirect
# wait for boot
& "$SDK\platform-tools\adb.exe" wait-for-device
# run against the right device (required when >1 emulator/device is attached)
$env:ANDROID_SERIAL = "emulator-5554"
cd android; .\gradlew.bat connectedDebugAndroidTest --no-daemon; cd ..
```

Results: `android/app/build/reports/androidTests/connected/`.

**First device-class run, verified 2026-10-16 (Medium_Phone_API_37.0):**
18/19 passed — AudioPlaybackTest 3/3, CameraRecognitionTest 4/4,
OfflineModeTest 5/5, PackLifecycleTest 3/3, PerformanceBenchTest 3/4.
The sole failure, `PerformanceBenchTest.searchQueryLatencyIsUnderBudget`
(FTS P50 **173 ms cold / 216 ms warm** vs the 100 ms budget), reproduced on
every run — see §6 for the diagnosis and mitigation order.

Run a single suite (note: quote the whole `-P…` property in PowerShell,
otherwise the leading `.` is parsed as a task name):

```powershell
.\gradlew.bat connectedDebugAndroidTest "-Pandroid.testInstrumentationRunnerArguments.class=com.trueway.app.PerformanceBenchTest" --no-daemon
```

---

## 4. Server (distribution stub) smoke test

```powershell
cd server
python -m uvicorn main:app --port 8080
```

Endpoints: `GET /v1/regions`, `GET /v1/regions/{pack_id}/releases/latest`,
`GET /v1/packs/{pack_id}/{version}/manifest.cjson`,
`GET /v1/packs/{pack_id}/{version}/{component}`,
`GET /v1/keys/publishers`,
`POST /v1/feedback/coverage`, `POST /v1/feedback/correction`.

---

## 5. Optional helpers (non-gating)

| Script | Purpose |
|---|---|
| `python ml/train_adapter.py --selftest` | adapter plumbing check (synthetic) |
| `python tests/fixtures/audit_alias_drift.py` | DemoCorpus vs seed alias parity (must print `drifted=0`) |
| `python tests/fixtures/probe_alias.py` | inspect seeded fixture DB aliases/FTS |
| `python tests/fixtures/print_failures.py` | pretty-print any failing JVM test XML |
| `python content/tools/harvest_monument_metadata.py --output <path>` | Wikidata harvest (falls back to offline fixtures when SPARQL is unreachable) |

**Do NOT run casually** (they rewrite committed fixtures/assets):
`tests/fixtures/make_demo_places_db.py`, `tests/fixtures/qr/make_demo_touchpoint.py`
(ephemeral keys), `content/tools/generate_audio_assets.py`,
`content/tools/generate_then_now_images.py`.

---

## 6. Known warnings & troubleshooting

| Symptom | Meaning / fix |
|---|---|
| Gradle wrapper: "Downloading … failed: timeout (10000ms)" | Known network quirk — seed the cache per §1.4 |
| `platform-tools` "inconsistent location … platform-tools-2" | Stray duplicate in SDK; delete `%LOCALAPPDATA%\Android\Sdk\platform-tools-2` |
| "SDK XML file of version 4 was encountered" | cmdline-tools newer than AGP expects; harmless |
| "Unable to strip the following libraries" | Debug builds package unstripped .so; harmless |
| "Deprecated Gradle features … incompatible with Gradle 9.0" | Non-blocking; plan a Gradle/AGP upgrade |
| Demo pack verifies as "demo signature — NOT a release signature" | Expected with `--demo-key`. Production requires `--key-file` + pinned publisher trust store |
| `java -version` prints to stderr | PowerShell native-stderr quirk; ignore exit code |
| `PerformanceBenchTest.searchQueryLatencyIsUnderBudget` FAILS on emulator (FTS P50 173–216 ms vs budget 100 ms) | **Reproducible on the emulator debug build** (verified twice). Likely debug-only cost: `PlaceDataSource.kt` re-runs `IndicPhoneticNormalizer.toSkeleton()` over every alias *per query* and constructs `Regex(` objects inside `toSkeleton` per call. Mitigation order: (1) precompute skeletons once at index build + hoist regexes to constants; (2) re-measure on a physical reference device in a **release** build before treating as a true budget breach; (3) only then revisit the budget itself |
| `connectedDebugAndroidTest` filtered run: "Instrumentation run failed due to Process crashed" | Transient on a cold/loaded emulator; rerun (a full unfiltered run is the reliable path). If it persists, check `adb logcat` for `AndroidRuntime` |

---

## 7. This machine's paths (reference)

| Item | Path |
|---|---|
| Project root | `C:\Users\PLEXTEK\Desktop\TRUE-WAY` |
| JDK 17 | `C:\Users\PLEXTEK\AppData\Local\jdk-17` |
| Android SDK | `C:\Users\PLEXTEK\AppData\Local\Android\Sdk` |
| cmdline-tools | `…\Android\Sdk\cmdline-tools\latest` |
| Gradle cache | `C:\Users\PLEXTEK\.gradle\wrapper\dists\gradle-8.13-bin\5xuhj0ry160q40clulazy9h7d` |
| AVD | `C:\Users\PLEXTEK\.android\avd\Medium_Phone.avd` (Medium_Phone_API_37.0) |
| Download staging | `C:\Users\PLEXTEK\AppData\Local\Temp\opencode` |
