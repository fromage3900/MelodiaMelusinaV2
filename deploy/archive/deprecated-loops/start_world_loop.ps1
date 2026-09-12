# Start detached world micro-loop (survives Cursor shell exit)
param(
    [int]$IntervalSeconds = 600
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$pidFile = Join-Path $deploy "SURREAL_WORLD_LOOP.pid"
$stopFile = Join-Path $deploy "SURREAL_WORLD_LOOP_STOP"
$loopScript = Join-Path $deploy "surreal_world_loop.ps1"

if (Test-Path $stopFile) {
    Remove-Item $stopFile -Force
}

if (Test-Path $pidFile) {
    $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
        Write-Host "World loop already running (PID $oldPid). Use stop_world_loop.ps1 first."
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

Write-Host "World loop started PID $($proc.Id) interval=${IntervalSeconds}s"
Write-Host "Log: deploy/SURREAL_WORLD_LOOP.log"
Write-Host "Stop: deploy/stop_world_loop.ps1"
