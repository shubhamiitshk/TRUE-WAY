# Stage the vision-encoder asset (gitignored, on demand).
#
# The P0 scanner shell (`MediaPipeEmbedder`) loads `vision_encoder.tflite` from
# app assets. The model is a MobileCLIP-S0 image encoder with the trained
# Sub-Center-ArcFace adapter and MediaPipe `TFLITE_METADATA`.
#
# WHICH VARIANT SHIPS IS DECIDED BY MEASUREMENT, NOT BY FILE SIZE.
# The previous build shipped the 12 MB INT8 model because it was smallest —
# and it measured **6x slower** than the 45 MB FP32 model on the workstation
# CPU (1707 ms vs 284 ms). "Smaller" is not "faster" (arXiv:2509.21173 measures
# quantised CLIP running 4x slower than FP32). `ml/convert_encoder.py` now
# produces fp32 / fp16 / int8_per_tensor / int8_per_axis / int8_dynamic,
# measures each one, and records the fastest acceptable variant as
# `tflite.chosen_variant` in `ml/models/s0/conversion_log.json`. This script
# stages THAT file.
#
# If the conversion log is missing (fresh clone), fall back to the fastest
# artefact present, and only then to the public Apache-2.0 MediaPipe
# MobileNetV3 sample so the asset path is always exercised.
#
# Absent asset = honest "not installed" state, never a build break.

$ErrorActionPreference = "Stop"
$assets = Join-Path $PSScriptRoot "app/src/main/assets"
New-Item -ItemType Directory -Force -Path $assets | Out-Null
$dest = Join-Path $assets "vision_encoder.tflite"
$repo = Split-Path $PSScriptRoot -Parent
$work = Join-Path $repo "ml/models/s0"
$logPath = Join-Path $work "conversion_log.json"

# --- 1. the variant the conversion measured as fastest -------------------------
$chosen = $null
$chosenFile = $null
if (Test-Path -LiteralPath $logPath) {
    try {
        $log = Get-Content -LiteralPath $logPath -Raw | ConvertFrom-Json
        if ($log.tflite.chosen_variant) { $chosen = [string]$log.tflite.chosen_variant }
        if ($log.tflite.chosen_file) { $chosenFile = [string]$log.tflite.chosen_file }
    } catch {
        Write-Output "conversion_log.json unreadable; falling back to the fastest artefact present"
    }
}

# The variant KEY and the artefact FILE NAME are not the same string: the
# per-tensor INT8 variant is keyed "int8_per_tensor" but is written
# "mci_s0_int8.tflite". Resolve the key explicitly; prefer the file name the
# converter recorded when it is present.
$byKey = @{
    "fp32"            = "mci_s0_fp32.tflite"
    "fp16"            = "mci_s0_fp16.tflite"
    "int8_per_tensor" = "mci_s0_int8.tflite"
    "int8_per_axis"   = "mci_s0_int8_per_axis.tflite"
    "int8_dynamic"    = "mci_s0_int8_dynamic.tflite"
}

$ordered = @()
if ($chosenFile) { $ordered += @($chosenFile) }
elseif ($chosen -and $byKey.ContainsKey($chosen)) { $ordered += @($byKey[$chosen]) }
# deterministic fallbacks, fastest-first by what we have measured
$ordered += @(
    "mci_s0_int8_dynamic.tflite",
    "mci_s0_fp16.tflite",
    "mci_s0_int8_per_axis.tflite",
    "mci_s0_int8.tflite",
    "mci_s0_fp32.tflite"
)

foreach ($name in $ordered) {
    $src = Join-Path $work $name
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination $dest -Force
        $bytes = (Get-Item -LiteralPath $dest).Length
        $mb = [math]::Round($bytes / 1MB, 2)
        $note = if ($chosen) { " (chosen by ml/convert_encoder.py as the fastest variant)" } else { " (no conversion log; fastest available)" }
        Write-Output ("staged {0} -> vision_encoder.tflite  {1} MB{2}" -f $name, $mb, $note)
        exit 0
    }
}

if (Test-Path -LiteralPath $dest) {
    Write-Output ("present: vision_encoder.tflite  {0} bytes" -f (Get-Item -LiteralPath $dest).Length)
    exit 0
}

# --- 2. last resort: the public Apache-2.0 MediaPipe sample -------------------
$url = "https://storage.googleapis.com/mediapipe-models/image_embedder/mobilenet_v3_small/float32/1/mobilenet_v3_small.tflite"
Write-Output "downloading floor encoder (MobileNetV3-small, ~4 MB) ..."
Invoke-WebRequest -Uri $url -OutFile $dest -TimeoutSec 300
Write-Output ("saved: vision_encoder.tflite  {0} bytes" -f (Get-Item -LiteralPath $dest).Length)
Write-Output "provenance: MediaPipe sample model (Apache-2.0 sample). Run ml/convert_encoder.py to replace with MobileCLIP-S0."
