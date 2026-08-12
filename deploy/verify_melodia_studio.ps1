# Verify Melodia Studio against Blender 5.2 (health + smoke queue).
param(
    [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot

$blender = @(
    "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
    "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $blender) {
    Write-Error "Blender 5.2/5.1/4.5 not found"
}

Write-Host "Using: $blender"
$health = Join-Path $deploy "_health_check_gn_builders.py"
& $blender --background --factory-startup --python $health
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not $SkipSmoke) {
    $smoke = Join-Path $deploy "run_blender_smoke_queue.ps1"
    if (Test-Path $smoke) {
        & $smoke
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}

Write-Host "verify_melodia_studio: OK"
