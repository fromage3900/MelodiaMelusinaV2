# Start Cursor-monitored surreal agent wake loop (default 5 min)
param(
    [int]$IntervalSeconds = 300
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$pidFile = Join-Path $deploy "CURSOR_AGENT_LOOP.pid"
$stopFile = Join-Path $deploy "CURSOR_AGENT_LOOP_STOP"
$loopScript = Join-Path $deploy "cursor_surreal_agent_loop.ps1"

if (Test-Path $stopFile) {
    Remove-Item $stopFile -Force
}

if (Test-Path $pidFile) {
    $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
        Write-Host "Cursor agent loop already running (PID $oldPid). Use stop_cursor_agent_loop.ps1 first."
        exit 0
    }
    Remove-Item $pidFile -Force
}

$proc = Start-Process -FilePath "powershell.exe" `
    -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $loopScript,
        "-IntervalSeconds", $IntervalSeconds
    ) `
    -WorkingDirectory $deploy `
    -WindowStyle Hidden `
    -PassThru

Write-Host "Cursor agent loop started PID $($proc.Id) interval=${IntervalSeconds}s"
Write-Host "Stop: deploy/stop_cursor_agent_loop.ps1"
