# Procedural World micro-loop — runs detached via start_world_loop.ps1
# Stop: deploy/stop_world_loop.ps1  OR  create deploy/SURREAL_WORLD_LOOP_STOP
param(
    [int]$IntervalSeconds = 600
)

$ErrorActionPreference = "Continue"
$deploy = $PSScriptRoot
$stopFile = Join-Path $deploy "SURREAL_WORLD_LOOP_STOP"
$pidFile = Join-Path $deploy "SURREAL_WORLD_LOOP.pid"
$logFile = Join-Path $deploy "SURREAL_WORLD_LOOP.log"
$tickPrompt = "10m world micro-cycle: read SURREAL_WORLD_LOOP_STATE.md, pick one slice, implement, run deploy/run_verify.ps1 -Mode world"

function Write-Log([string]$msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Output $line
}

# Record our PID (launcher may have started us detached)
$PID | Out-File -FilePath $pidFile -Encoding ascii -Force
Write-Log "AGENT_LOOP_START_world_micro10 pid=$PID interval=${IntervalSeconds}s"

if (Test-Path $stopFile) {
    Remove-Item $stopFile -Force
}

$tick = 0
while ($true) {
    try {
        Start-Sleep -Seconds $IntervalSeconds
    } catch {
        Write-Log "sleep interrupted: $_"
        continue
    }

    if (Test-Path $stopFile) {
        Write-Log "AGENT_LOOP_STOP_world_micro10 stop sentinel detected"
        break
    }

    $tick++
    Write-Log "AGENT_LOOP_TICK_world_micro10 tick=$tick {`"prompt`":`"$tickPrompt`"}"

    # Health check each tick (does not replace agent implementation work)
    $verifyScript = Join-Path $deploy "run_verify.ps1"
    if (Test-Path $verifyScript) {
        try {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $verifyScript -Mode world 2>&1 |
                ForEach-Object { Write-Log "verify: $_" }
            if ($LASTEXITCODE -eq 0) {
                Write-Log "verify_health: OK"
            } else {
                Write-Log "verify_health: FAIL exit=$LASTEXITCODE"
            }
        } catch {
            Write-Log "verify_health: ERROR $_"
        }
    }
}

if (Test-Path $pidFile) { Remove-Item $pidFile -Force }
Write-Log "AGENT_LOOP_EXIT_world_micro10"
