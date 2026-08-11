# start_td_loop.ps1 — TouchDesigner autonomous production daemon
# Runs continuous TOA cycle: audio analysis → particle update → OSC push → Spout health
# Branch: feature/touchdesigner-mcp-integration

param(
    [int]$IntervalSeconds = 60,
    [string]$SentinelName = "AGENT_LOOP_TICK_td_orch"
)

$ProjectRoot = "G:\EnvironmentPortfolio"
$SentinelPath = "$ProjectRoot\BS_GodFile\Saved\Audit\$SentinelName"
$StopPath = "$ProjectRoot\BS_GodFile\Saved\Audit\td_loop_STOP"
$TdBridge = "$ProjectRoot\BS_GodFile\Content\Python\td_bridge.py"

# Ensure audit directory exists
New-Item -ItemType Directory -Force -Path "$ProjectRoot\BS_GodFile\Saved\Audit" | Out-Null

Write-Host "[TOA] ========================================"
Write-Host "[TOA]  TouchDesigner Orchestrator Daemon"
Write-Host "[TOA]  Interval: ${IntervalSeconds}s"
Write-Host "[TOA]  Sentinel: $SentinelName"
Write-Host "[TOA] ========================================"

$tickCount = 0

while ($true) {
    # Check global stop signal
    if (Test-Path "$ProjectRoot\BS_GodFile\Saved\Audit\AGENT_LOOP_STOP") {
        Write-Host "[TOA] Global STOP signal detected. Exiting."
        break
    }
    
    # Check TD-specific stop signal
    if (Test-Path $StopPath) {
        Write-Host "[TOA] TD STOP signal detected. Exiting daemon."
        Remove-Item $StopPath -Force -ErrorAction SilentlyContinue
        break
    }
    
    $tickCount++
    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    
    # Write heartbeat sentinel
    @{ 
        tick = $tickCount
        timestamp = $timestamp
        agent = "TOA"
        status = "running" 
        interval = $IntervalSeconds
    } | ConvertTo-Json | Set-Content $SentinelPath
    
    # Execute TD tick via Python bridge
    try {
        Write-Host "[TOA] Tick #$tickCount — $timestamp"
        & python $TdBridge --tick 2>&1 | ForEach-Object { Write-Host "[TOA]   $_" }
    }
    catch {
        Write-Host "[TOA] ERROR: $_"
        @{
            tick = $tickCount
            timestamp = $timestamp
            agent = "TOA"
            status = "error"
            error = $_.Exception.Message
        } | ConvertTo-Json | Set-Content $SentinelPath
    }
    
    Start-Sleep -Seconds $IntervalSeconds
}

Write-Host "[TOA] Daemon stopped after $tickCount ticks."
