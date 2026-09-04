# Install the CURRENT CHECKOUT's Melodia Studio deploy tree into Blender 5.2.
#
# The installer deliberately refuses to guess another repository root. The Python
# sync helper stamps the live addon with source checkout + Git branch + HEAD and
# verifies every copied file byte-for-byte.
#
#   .\deploy\install_melodia_studio.ps1
#   .\deploy\install_melodia_studio.ps1 -CheckOnly
param(
    [string]$BlenderVersion = "5.2",
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$projectRoot = Split-Path -Parent $deploy

if ($BlenderVersion -ne "5.2") {
    if ($CheckOnly) {
        Write-Error "-CheckOnly is currently supported for Blender 5.2 only."
        exit 2
    }
    & (Join-Path $deploy "sync_surreal_to_live.ps1") -BlenderVersion $BlenderVersion
    exit $LASTEXITCODE
}

$head = (& git -C $projectRoot rev-parse HEAD 2>$null | Out-String).Trim()
$branch = (& git -C $projectRoot branch --show-current 2>$null | Out-String).Trim()
Write-Host "Melodia Studio source checkout:"
Write-Host "  root:   $projectRoot"
Write-Host "  branch: $branch"
Write-Host "  HEAD:   $head"
Write-Host ""

$syncScript = Join-Path $deploy "_sync_addon_to_blender_5_2.py"

if ($CheckOnly) {
    python $syncScript --check
    exit $LASTEXITCODE
}

$liveBlender = @(Get-Process blender -ErrorAction SilentlyContinue)
if ($liveBlender) {
    $pids = ($liveBlender | ForEach-Object { $_.Id }) -join ", "
    Write-Error @"
Blender is running (PID $pids). The live addon cannot be replaced safely while
the GUI may have modules loaded. Close every Blender process, rerun this command,
then restart Blender. Do not hot-reload across workstation handoffs.
"@
    exit 2
}

python $syncScript
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Melodia Studio live addon is byte-identical to this checkout and stamped with:"
Write-Host "  branch: $branch"
Write-Host "  HEAD:   $head"
Write-Host ""
Write-Host "Start Blender 5.2 fresh. Do not use an older AppData copy from another checkout."
