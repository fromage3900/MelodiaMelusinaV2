# Sync Melodia Studio (surreal_arch) deploy tree to a live Blender addons folder.
#
# Docs/MELODIA_STUDIO_SHIP_CHECKLIST.md names Blender 5.2 as the product target.
#
#   .\sync_surreal_to_live.ps1                     # -> 5.2 (product target)
#   .\sync_surreal_to_live.ps1 -BlenderVersion 5.1 # -> 5.1 legacy
param(
    [string]$BlenderVersion = "5.2"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$deploy = Join-Path $root "deploy"
$live = Join-Path $env:APPDATA "Blender Foundation\Blender\$BlenderVersion\scripts\addons"

if (-not (Test-Path $live)) {
    New-Item -ItemType Directory -Path $live -Force | Out-Null
}
Write-Host "Target: $live"

Copy-Item (Join-Path $deploy "surreal_architecture_gen.py") (Join-Path $live "surreal_architecture_gen.py") -Force
Get-ChildItem (Join-Path $deploy "surreal_arch") -Filter "*.py" -Recurse | ForEach-Object {
    $rel = $_.FullName.Substring((Join-Path $deploy "surreal_arch").Length)
    $dest = Join-Path (Join-Path $live "surreal_arch") $rel
    $destDir = Split-Path -Parent $dest
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    Copy-Item $_.FullName $dest -Force
}
if (Test-Path (Join-Path $deploy "surreal_greybox")) {
    Copy-Item (Join-Path $deploy "surreal_greybox") (Join-Path $live "surreal_greybox") -Recurse -Force
}
if (Test-Path (Join-Path $deploy "surreal_world")) {
    Get-ChildItem (Join-Path $deploy "surreal_world") -Filter "*.py" -Recurse | ForEach-Object {
        $rel = $_.FullName.Substring((Join-Path $deploy "surreal_world").Length)
        $dest = Join-Path (Join-Path $live "surreal_world") $rel
        $destDir = Split-Path -Parent $dest
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        Copy-Item $_.FullName $dest -Force
    }
}
if (Test-Path (Join-Path $deploy "surreal_os")) {
    $destOs = Join-Path $live "surreal_os"
    if (Test-Path $destOs) { Remove-Item $destOs -Recurse -Force }
    Copy-Item (Join-Path $deploy "surreal_os") $destOs -Recurse -Force
}
$required = @(
    "surreal_arch\nikki_materials.py",
    "surreal_arch\bagapie_bridge.py",
    "surreal_arch\integration.py"
)
foreach ($rel in $required) {
    $dest = Join-Path $live $rel
    if (-not (Test-Path $dest)) {
        throw "SurrealArch sync missing required file: $rel"
    }
}
Write-Host "Synced deploy -> live Blender $BlenderVersion addons"
