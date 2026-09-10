# Start detached Surreal Architecture tier-B Cursor wake loop (default 5 min)
param(
    [int]$IntervalSeconds = 300
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$pidFile = Join-Path $deploy "SURREAL_TIERB_LOOP.pid"
$stopFile = Join-Path $deploy "SURREAL_TIERB_LOOP_STOP"
$loopScript = Join-Path $deploy "cursor_surreal_tierb_loop.ps1"

if (Test-Path $stopFile) {
    Remove-Item $stopFile -Force
}

if (Test-Path $pidFile) {
    $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
        Write-Host "Surreal tier-B loop already running (PID $oldPid). Use stop_surreal_tierb_loop.ps1 first."
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

Write-Host "Surreal tier-B loop started PID $($proc.Id) interval=${IntervalSeconds}s"
Write-Host "Stop: deploy/stop_surreal_tierb_loop.ps1"
