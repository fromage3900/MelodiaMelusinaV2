# Cursor agent wake loop — emits AGENT_LOOP_TICK for monitored shell notifications
param(
    [int]$IntervalSeconds = 300
)

$ErrorActionPreference = "Continue"
$deploy = $PSScriptRoot
$pidFile = Join-Path $deploy "CURSOR_AGENT_LOOP.pid"
$stopFile = Join-Path $deploy "CURSOR_AGENT_LOOP_STOP"
$tickPrompt = "5m micro-cycle: read deploy/SURREAL_ARCH_LOOP_STATE.md backlog, implement one slice, sync+verify, update LOOP_STATE. Do NOT edit plan files."

$PID | Out-File -FilePath $pidFile -Encoding ascii -Force
Write-Output "AGENT_LOOP_START_surreal_micro2 pid=$PID interval=${IntervalSeconds}s"

if (Test-Path $stopFile) {
    Remove-Item $stopFile -Force
}

$tick = 0
while ($true) {
    try {
        Start-Sleep -Seconds $IntervalSeconds
    } catch {
        Write-Output "sleep interrupted: $_"
        continue
    }

    if (Test-Path $stopFile) {
        Write-Output "AGENT_LOOP_STOP_surreal_micro2 stop sentinel detected"
        break
    }

    $tick++
    $json = @{ prompt = $tickPrompt } | ConvertTo-Json -Compress
    Write-Output "AGENT_LOOP_TICK_surreal_micro2 $json"
}

if (Test-Path $pidFile) { Remove-Item $pidFile -Force }
Write-Output "AGENT_LOOP_EXIT_surreal_micro2"
