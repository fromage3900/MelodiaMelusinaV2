# Hermes Daemon - Documentation, Git Health, and Blessings/Burdens Verification
param(
    [switch]$Stop,
    [switch]$Status,
    [switch]$RunOnce
)

$ProjectRoot = "C:\EnvironmentPortfolio\BS_GodFile"
$AuditDir = "$ProjectRoot\Saved\Audit"

if ($Status) {
    Write-Host "========================================"
    Write-Host "  Hermes Daemon Status"
    Write-Host "========================================"
    
    $sentinel = Join-Path $AuditDir "hermes_health.json"
    if (Test-Path $sentinel) {
        try {
            $content = Get-Content $sentinel -Raw | ConvertFrom-Json
            Write-Host "  Last run: $($content.timestamp)"
            Write-Host "  Git status: $($content.git.status)"
            Write-Host "  Blessings: $($content.blessings.blessings_count) valid, $($content.blessings.burdens_count) burden pairs"
        }
        catch {
            Write-Host "  ACTIVE (unparseable)"
        }
    }
    else {
        Write-Host "  INACTIVE (no health report found)"
    }
    
    $stopFile = Join-Path $ProjectRoot "deploy\HERMES_DAEMON_STOP"
    if (Test-Path $stopFile) {
        Write-Host "  STOP SIGNAL PRESENT"
    }
    exit 0
}

if ($Stop) {
    Write-Host "Stopping Hermes daemon..."
    $stopFile = Join-Path $ProjectRoot "deploy\HERMES_DAEMON_STOP"
    $null = New-Item -ItemType File -Force -Path $stopFile
    Write-Host "Stop signal written. Daemon will exit on next tick."
    
    # Also stop all ollama daemons
    $allStop = Join-Path $ProjectRoot "deploy\STOP_ALL"
    $null = New-Item -ItemType File -Force -Path $allStop
    Write-Host "Global STOP_ALL signal written."
    exit 0
}

# Start mode
$null = New-Item -ItemType Directory -Force -Path $AuditDir
Remove-Item "$ProjectRoot\deploy\HERMES_DAEMON_STOP" -ErrorAction SilentlyContinue
Remove-Item "$ProjectRoot\deploy\STOP_ALL" -ErrorAction SilentlyContinue

Write-Host "========================================"
Write-Host "  Hermes Daemon"
Write-Host "  Documentation & Git Health Monitor"
Write-Host "========================================"
Write-Host ""

# Run once mode (non-daemon)
if ($RunOnce) {
    Write-Host "Running single verification pass..."
    & python "$ProjectRoot\deploy\hermes_daemon.py"
    exit $LASTEXITCODE
}

# Daemon mode
Write-Host "Starting Hermes daemon (60s interval)..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-File", "$ProjectRoot\deploy\hermes_daemon.ps1",
    "-IntervalSeconds", "60"
) -WindowStyle Minimized -PassThru

Write-Host ""
Write-Host "Monitor file: $AuditDir\hermes_health.json"
Write-Host ""
Write-Host "Commands:"
Write-Host "  .\start_hermes_daemon.ps1 -Status"
Write-Host "  .\start_hermes_daemon.ps1 -Stop"
Write-Host "  .\start_hermes_daemon.ps1 -RunOnce"