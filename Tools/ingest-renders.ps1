# ingest-renders.ps1 — Import new renders from UE5 into the site
#
# Copies render captures from BS_GodFile/Saved/Portfolio/ into
# generated/assets/ with organized naming.
#
# Retargeted 2026-08-20: the old my-site-clean/ staging copy had decayed to 11
# stray PNGs, so every ingest since was writing into a directory nothing read.
# Then optionally deploys everything live.
#
# Usage:
#   .\tools\ingest-renders.ps1
#   .\tools\ingest-renders.ps1 -Deploy

param(
    [switch]$Deploy,
    [string]$SourceDir = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio"
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $PSScriptRoot
$assetDir   = Join-Path $scriptRoot "generated\assets"

# --- Subdirectories -------------------------------------------------------
$subdirs = @{
    "unreal"  = @("*.png", "*.jpg", "*.exr")
    "props"   = @("*.png", "*.jpg")
    "ornaments" = @("*.png", "*.jpg")
    "landscape-loops" = @("*.webm", "*.mp4", "*.png", "*.jpg")
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════╗"
Write-Host "  ║      Melodia — Render Ingest Pipeline        ║"
Write-Host "  ╚══════════════════════════════════════════════╝"
Write-Host ""
Write-Host "  Source: $SourceDir"
Write-Host "  Target: generated/assets/"
Write-Host ""

# --- Scan for new files ---------------------------------------------------
$newFiles = @()
if (Test-Path $SourceDir) {
    foreach ($ext in @("*.png", "*.jpg", "*.webm", "*.mp4", "*.exr")) {
        $newFiles += Get-ChildItem -Path $SourceDir -Filter $ext -File -ErrorAction SilentlyContinue
    }
}

if ($newFiles.Count -eq 0) {
    Write-Host "  [INFO] No new renders found in Saved/Portfolio/"
    Write-Host ""
    Write-Host "  To capture renders from UE5:"
    Write-Host "    1. Open the map in UE5"
    Write-Host "    2. Position your camera"
    Write-Host "    3. Press F9 (or use HighResScreenshot command)"
    Write-Host "    4. Run this script again"
    exit 0
}

Write-Host "  Found $($newFiles.Count) new file(s):"
$newFiles | ForEach-Object { Write-Host "    - $($_.Name)" }

# --- Ingest by subdirectory -----------------------------------------------
foreach ($dirName in $subdirs.Keys) {
    $targetDir = Join-Path $assetDir $dirName
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
}

$ingested = 0
foreach ($file in $newFiles) {
    $ext = $file.Extension.ToLower()
    $name = $file.BaseName

    if ($ext -eq ".webm" -or $ext -eq ".mp4") {
        Copy-Item $file.FullName (Join-Path $assetDir "landscape-loops\$($file.Name)") -Force
        Write-Host "  [INGEST] landscape-loops/$($file.Name)"
        $ingested++
    } elseif ($ext -eq ".exr") {
        # EXR stays in unreal/ for potential later use, but skip for now
        Copy-Item $file.FullName (Join-Path $assetDir "unreal\$($file.Name)") -Force
        Write-Host "  [INGEST] unreal/$($file.Name) (EXR — high-dynamic range)"
        $ingested++
    } else {
        # Heuristic: if name contains "prop", "lantern", "wand" → props/
        if ($name -match "(prop|lantern|wand|petal|statue)") {
            Copy-Item $file.FullName (Join-Path $assetDir "props\$($file.Name)") -Force
            Write-Host "  [INGEST] props/$($file.Name)"
        } elseif ($name -match "(ornament|column|capital|rosette|knot)") {
            Copy-Item $file.FullName (Join-Path $assetDir "ornaments\$($file.Name)") -Force
            Write-Host "  [INGEST] ornaments/$($file.Name)"
        } else {
            Copy-Item $file.FullName (Join-Path $assetDir "unreal\$($file.Name)") -Force
            Write-Host "  [INGEST] unreal/$($file.Name)"
        }
        $ingested++
    }
}

Write-Host ""
Write-Host "  [OK] $ingested files ingested into generated/assets/"
Write-Host ""

# --- Optional deploy ------------------------------------------------------
if ($Deploy) {
    Write-Host "  ── Deploying to GitHub Pages ──"
    & $scriptRoot\deploy\sync_site_to_github.ps1 -Message "Ingest $ingested new renders"
} else {
    Write-Host "  Next step: run deploy/quick-deploy.ps1 to make live"
    Write-Host "  Or use: .\tools\ingest-renders.ps1 -Deploy"
}