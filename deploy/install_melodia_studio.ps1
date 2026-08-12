# Install Melodia Studio into a live Blender addons folder (default 5.2).
#
#   .\install_melodia_studio.ps1
#   .\install_melodia_studio.ps1 -BlenderVersion 5.2
param(
    [string]$BlenderVersion = "5.2"
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot

if ($BlenderVersion -eq "5.2") {
    Write-Host "Syncing via _sync_addon_to_blender_5_2.py ..."
    python (Join-Path $deploy "_sync_addon_to_blender_5_2.py")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    & (Join-Path $deploy "sync_surreal_to_live.ps1") -BlenderVersion $BlenderVersion
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$live = Join-Path $env:APPDATA "Blender Foundation\Blender\$BlenderVersion\scripts\addons"
Write-Host ""
Write-Host "Melodia Studio installed to:"
Write-Host "  $live"
Write-Host "Enable addon in Preferences: surreal_architecture_gen (UI label: Melodia Studio)"
Write-Host "Then F3 Reload Scripts, or use N-panel Sync and Reload."
