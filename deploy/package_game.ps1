# deploy/package_game.ps1
# Packages Melodia as a Windows executable for playtesting and portfolio download
# Usage: ./package_game.ps1

$ErrorActionPreference = "Stop"

$ROOT_DIR = Split-Path $PSScriptRoot -Parent
$UPROJECT = Join-Path $ROOT_DIR "BS_GodFile.uproject"
# Find UnrealEngine UAT location
$UAT_CMD = "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat"

$OUTPUT_DIR = Join-Path $ROOT_DIR "Products\Builds\$(Get-Date -Format 'yyyy-MM-dd')"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Packaging Melodia (Win64 Development) " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Output Directory: $OUTPUT_DIR"

if (-not (Test-Path $OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $OUTPUT_DIR -Force | Out-Null
}

$BUILD_CMD = "& `"$UAT_CMD`" BuildCookRun -project=`"$UPROJECT`" -noP4 -platform=Win64 -clientconfig=Development -cook -build -stage -pak -archive -archivedirectory=`"$OUTPUT_DIR`""

Write-Host "Running Unreal Automation Tool..." -ForegroundColor Yellow
Invoke-Expression $BUILD_CMD

if ($LASTEXITCODE -eq 0) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host " SUCCESS: Build packaged to $OUTPUT_DIR" -ForegroundColor Green
    Write-Host " Zip this folder and upload to GitHub Releases." -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
} else {
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host " ERROR: Build failed. Check logs." -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    exit 1
}
