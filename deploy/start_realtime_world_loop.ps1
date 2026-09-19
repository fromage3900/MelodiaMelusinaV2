# Start detached realtime world conductor (survives Cursor shell exit)
#
# Composes with, does not replace:
#   deploy/start_world_loop.ps1         10m world micro-cycle + run_verify -Mode world
#   deploy/monolith_orchestrator.py     5-agent health / routing
#
# First vertical (use case B): Castle SurrealPlan → HISM + ROLE_UE_HINTS.
# Default --manifest is deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json.
# Zen shrine:  -Manifest (Join-Path $deploy "fixtures/SurrealPlan_ZenShrine_WorldRoot.world.json")
param(
    [int]$IntervalSeconds = 5,
    [string]$Manifest = $(Join-Path $PSScriptRoot "fixtures/SurrealPlan_Castle_WorldRoot.world.json")
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$project = Split-Path $deploy -Parent
$pidFile = Join-Path $deploy "SURREAL_REALTIME_WORLD_LOOP.pid"
$stopFile = Join-Path $deploy "SURREAL_REALTIME_WORLD_LOOP_STOP"
$logFile = Join-Path $deploy "SURREAL_REALTIME_WORLD_LOOP.log"
$conductor = Join-Path $deploy "realtime_world_conductor.py"

if (Test-Path $stopFile) {
    Remove-Item $stopFile -Force
}

if (Test-Path $pidFile) {
    $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
        Write-Host "Realtime world conductor already running (PID $oldPid). Use stop_realtime_world_loop.ps1 first."
        exit 0
    }
    Remove-Item $pidFile -Force
}

$argList = @(
    $conductor,
    "--watch",
    "--interval",
    "$IntervalSeconds"
)
if ($Manifest) {
    $argList += @("--manifest", $Manifest)
}

$proc = Start-Process -FilePath "python" `
    -ArgumentList $argList `
    -WorkingDirectory $project `
    -WindowStyle Hidden `
    -RedirectStandardOutput $logFile `
    -PassThru

$proc.Id | Out-File -FilePath $pidFile -Encoding ascii -Force

Write-Host "Realtime world conductor started PID $($proc.Id) interval=${IntervalSeconds}s"
Write-Host "Compose: start_world_loop.ps1 (slow verify) + monolith_orchestrator.py (5 agents)"
Write-Host "Log: deploy/SURREAL_REALTIME_WORLD_LOOP.log"
Write-Host "Status: Saved/Audit/realtime_world_conductor_status.json"
Write-Host "Stop: deploy/stop_realtime_world_loop.ps1"
