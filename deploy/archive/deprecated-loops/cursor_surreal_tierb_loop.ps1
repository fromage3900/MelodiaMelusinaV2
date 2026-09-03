# Cursor-monitored Surreal Architecture tier-B wake loop
param(
    [int]$IntervalSeconds = 300
)

$ErrorActionPreference = "Continue"
$deploy = $PSScriptRoot
$pidFile = Join-Path $deploy "SURREAL_TIERB_LOOP.pid"
$stopFile = Join-Path $deploy "SURREAL_TIERB_LOOP_STOP"
$logFile = Join-Path $deploy "SURREAL_ARCH_LOOP.log"
$tickPrompt = "AAA Architecture Genome Expansion micro-cycle: read deploy/SURREAL_ARCH_LOOP_STATE.md + CHANGELOG + AGENTS.md; research first in research/; pick ONE impactful slice (new genome+grammar, compose polish, or hero preset); sync deploy/sync_surreal_to_live.ps1; run deploy/run_verify.ps1 -Mode all; update LOOP_STATE + CHANGELOG; bump bl_info patch; do NOT edit .cursor/plans/ files."

function Write-Log([string]$msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Output $line
}

$PID | Out-File -FilePath $pidFile -Encoding ascii -Force
Write-Log "AGENT_LOOP_START_surreal_tierb pid=$PID interval=${IntervalSeconds}s"

if (Test-Path $stopFile) {
    Remove-Item $stopFile -Force
}

function Emit-Tick([int]$n) {
    $json = @{ prompt = $tickPrompt } | ConvertTo-Json -Compress
    Write-Log "AGENT_LOOP_TICK_surreal_tierb tick=$n $json"
}

# Tick 0 immediately — "starting now" without waiting for first sleep
$tick = 0
Emit-Tick $tick

while ($true) {
    try {
        Start-Sleep -Seconds $IntervalSeconds
    } catch {
        Write-Log "sleep interrupted: $_"
        continue
    }

    if (Test-Path $stopFile) {
        Write-Log "AGENT_LOOP_STOP_surreal_tierb stop sentinel detected"
        break
    }

    $tick++
    Emit-Tick $tick
}

if (Test-Path $pidFile) { Remove-Item $pidFile -Force }
Write-Log "AGENT_LOOP_EXIT_surreal_tierb"
