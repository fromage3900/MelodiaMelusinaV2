# Agent Bridge Startup Script
# Uses the checkout containing this script; no machine-specific repo root.

param(
    [ValidateSet("status", "start")]
    [string]$Action = "status"
)

$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$DAEMON_SCRIPT = Join-Path $PROJECT_ROOT "deploy\blessing_evolution_daemon.py"

Write-Host "[AgentBridge] Project root: $PROJECT_ROOT" -ForegroundColor DarkGray
Write-Host "[AgentBridge] Checking status..." -ForegroundColor Cyan

$QUEUE_FILE = Join-Path $PROJECT_ROOT "Saved\AgentMemory\blessing_evolution_queue.json"
if (Test-Path $QUEUE_FILE) {
    Write-Host "  [INFO] Blessing evolution queue exists - daemon will process when started" -ForegroundColor Yellow
} else {
    Write-Host "  [INFO] No evolution queue - ready for requests" -ForegroundColor Green
}

$BRIDGE_SCRIPT = Join-Path $PROJECT_ROOT "deploy\agent_bridge_mcp.py"
if (Test-Path $BRIDGE_SCRIPT) {
    Write-Host "  [OK] Agent bridge MCP available" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Agent bridge MCP not found" -ForegroundColor Red
    exit 1
}

Write-Host "`n[AgentBridge] Available tools via MCP:" -ForegroundColor Cyan
Write-Host "  - delegate_to_agent"
Write-Host "  - get_agent_status"
Write-Host "  - get_agent_memory"
Write-Host "  - run_blessing_evolution"
Write-Host "  - ue_editor_command"

if ($Action -eq "start") {
    Write-Host "`n[AgentBridge] Starting blessing evolution daemon..." -ForegroundColor Cyan
    Start-Process -FilePath "python" -ArgumentList "`"$DAEMON_SCRIPT`"" -WorkingDirectory $PROJECT_ROOT
    Write-Host "  [OK] Daemon started for this checkout" -ForegroundColor Green
} else {
    Write-Host "`n[AgentBridge] Status check complete." -ForegroundColor Green
}
