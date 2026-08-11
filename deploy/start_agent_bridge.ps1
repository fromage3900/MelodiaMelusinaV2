# Agent Bridge Startup Script
# Starts the blessing evolution daemon and prepares agent bridge

param(
    [string]$Action = "status"
)

$PROJECT_ROOT = "G:\EnvironmentPortfolio\BS_GodFile"
$DAEMON_SCRIPT = Join-Path $PROJECT_ROOT "deploy\blessing_evolution_daemon.py"

Write-Host "[AgentBridge] Checking status..." -ForegroundColor Cyan

# Check if blessing evolution queue exists
$QUEUE_FILE = Join-Path $PROJECT_ROOT "Saved\AgentMemory\blessing_evolution_queue.json"
if (Test-Path $QUEUE_FILE) {
    Write-Host "  [INFO] Blessing evolution queue exists - daemon will process when started" -ForegroundColor Yellow
} else {
    Write-Host "  [INFO] No evolution queue - ready for requests" -ForegroundColor Green
}

# Check agent bridge MCP
$BRIDGE_SCRIPT = Join-Path $PROJECT_ROOT "deploy\agent_bridge_mcp.py"
if (Test-Path $BRIDGE_SCRIPT) {
    Write-Host "  [OK] Agent bridge MCP available" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Agent bridge MCP not found" -ForegroundColor Red
    exit 1
}

# List available tools
Write-Host "`n[AgentBridge] Available tools via MCP:" -ForegroundColor Cyan
Write-Host "  - delegate_to_agent (route to any agent)" -ForegroundColor White
Write-Host "  - get_agent_status (check agent readiness)" -ForegroundColor White
Write-Host "  - get_agent_memory (query shared context)" -ForegroundColor White
Write-Host "  - run_blessing_evolution (generate new blessings)" -ForegroundColor White
Write-Host "  - ue_editor_command (send commands to UE)" -ForegroundColor White

if ($Action -eq "start") {
    Write-Host "`n[AgentBridge] Starting blessing evolution daemon..." -ForegroundColor Cyan
    Start-Process -FilePath "python" -ArgumentList "`"$DAEMON_SCRIPT`"" -WorkingDirectory $PROJECT_ROOT
    Write-Host "  [OK] Daemon started in background" -ForegroundColor Green
}

if ($Action -eq "status") {
    Write-Host "`n[AgentBridge] Status check complete." -ForegroundColor Green
}