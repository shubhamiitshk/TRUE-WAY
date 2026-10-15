# Fetch the floor vision-encoder asset (gitignored, on demand).
# The P0 scanner shell (MediaPipeEmbedder) loads `vision_encoder.tflite`
# from app assets; the MobileCLIP-S0 .tflite will land under the SAME name
# when conversion unblocks, with identity recorded in the pack manifest.
# Absent asset = honest "not installed" state, never a build break.

$ErrorActionPreference = "Stop"
$assets = Join-Path $PSScriptRoot "app/src/main/assets"
New-Item -ItemType Directory -Force -Path $assets | Out-Null
$dest = Join-Path $assets "vision_encoder.tflite"

if (Test-Path -LiteralPath $dest) {
    Write-Output ("present: {0} ({1} bytes)" -f $dest, (Get-Item -LiteralPath $dest).Length)
    return
}

$url = "https://storage.googleapis.com/mediapipe-models/image_embedder/mobilenet_v3_small/float32/1/mobilenet_v3_small.tflite"
Write-Output "downloading floor encoder (MobileNetV3-small, ~4 MB) ..."
Invoke-WebRequest -Uri $url -OutFile $dest -TimeoutSec 300
Write-Output ("saved: {0} ({1} bytes)" -f $dest, (Get-Item -LiteralPath $dest).Length)
Write-Output "provenance: MediaPipe sample model (Apache-2.0 sample). Replace with the rights-cleared S0 build at benchmark week."
