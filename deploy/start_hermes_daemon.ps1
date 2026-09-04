# Hermes Daemon - Documentation, Git Health, and Blessings/Burdens Verification
# Uses the checkout containing this script.

param(
    [switch]$Stop,
    [switch]$Status,
    [switch]$RunOnce
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$AuditDir = Join-Path $ProjectRoot "Saved\Audit"

Write-Host "Hermes checkout: $ProjectRoot" -ForegroundColor DarkGray

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
        } catch {
            Write-Host "  ACTIVE (unparseable)"
        }
    } else {
        Write-Host "  INACTIVE (no health report found)"
    }

    $stopFile = Join-Path $ProjectRoot "deploy\HERMES_DAEMON_STOP"
    if (Test-Path $stopFile) {
        Write-Host "  STOP SIGNAL PRESENT"
    }
    exit 0
}

if ($Stop) {
    Write-Host "Stopping Hermes daemon for this checkout..."
    $stopFile = Join-Path $ProjectRoot "deploy\HERMES_DAEMON_STOP"
    $null = New-Item -ItemType File -Force -Path $stopFile

    $allStop = Join-Path $ProjectRoot "deploy\STOP_ALL"
    $null = New-Item -ItemType File -Force -Path $allStop
    exit 0
}

$null = New-Item -ItemType Directory -Force -Path $AuditDir
Remove-Item (Join-Path $ProjectRoot "deploy\HERMES_DAEMON_STOP") -ErrorAction SilentlyContinue
Remove-Item (Join-Path $ProjectRoot "deploy\STOP_ALL") -ErrorAction SilentlyContinue

Write-Host "========================================"
Write-Host "  Hermes Daemon"
Write-Host "  Documentation & Git Health Monitor"
Write-Host "========================================"

if ($RunOnce) {
    & python (Join-Path $ProjectRoot "deploy\hermes_daemon.py") --run-once
    exit $LASTEXITCODE
}

Start-Process python -ArgumentList @(
    "`"$(Join-Path $ProjectRoot 'deploy\hermes_daemon.py')`""
) -WorkingDirectory $ProjectRoot -WindowStyle Minimized -PassThru | Out-Null

Write-Host "Monitor file: $(Join-Path $AuditDir 'hermes_health.json')"
