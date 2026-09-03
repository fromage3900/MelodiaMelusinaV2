# Surreal Architecture kit micro-loop — runs detached via start_surreal_loop.ps1
param(
    [int]$IntervalSeconds = 600
)

$ErrorActionPreference = "Continue"
$deploy = $PSScriptRoot
$stopFile = Join-Path $deploy "SURREAL_ARCH_LOOP_STOP"
$pidFile = Join-Path $deploy "SURREAL_ARCH_LOOP.pid"
$logFile = Join-Path $deploy "SURREAL_ARCH_LOOP.log"
$tickPrompt = "Surreal Architecture micro-cycle: read SURREAL_ARCH_LOOP_STATE.md, pick one Tier B slice (new genome, grammar graph, or kit polish), node design + taxonomy before code; sync; verify; update LOOP_STATE"

function Write-Log([string]$msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Output $line
}

$PID | Out-File -FilePath $pidFile -Encoding ascii -Force
Write-Log "AGENT_LOOP_START_surreal_micro10 pid=$PID interval=${IntervalSeconds}s"

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
        Write-Log "AGENT_LOOP_STOP_surreal_micro10 stop sentinel detected"
        break
    }

    $tick++
    Write-Log "AGENT_LOOP_TICK_surreal_micro10 tick=$tick {`"prompt`":`"$tickPrompt`"}"

    $verifyScript = Join-Path $deploy "run_verify.ps1"
    if (Test-Path $verifyScript) {
        try {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $verifyScript -Mode overhaul 2>&1 |
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
Write-Log "AGENT_LOOP_EXIT_surreal_micro10"
