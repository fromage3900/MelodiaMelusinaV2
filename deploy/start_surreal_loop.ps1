# Start detached surreal kit micro-loop
param(
    [int]$IntervalSeconds = 600
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$pidFile = Join-Path $deploy "SURREAL_ARCH_LOOP.pid"
$stopFile = Join-Path $deploy "SURREAL_ARCH_LOOP_STOP"
$loopScript = Join-Path $deploy "surreal_micro_loop.ps1"

if (Test-Path $stopFile) {
    Remove-Item $stopFile -Force
}

if (Test-Path $pidFile) {
    $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
        Write-Host "Surreal loop already running (PID $oldPid). Use stop_surreal_loop.ps1 first."
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

Write-Host "Surreal loop started PID $($proc.Id) interval=${IntervalSeconds}s"
Write-Host "Log: deploy/SURREAL_ARCH_LOOP.log"
Write-Host "Stop: deploy/stop_surreal_loop.ps1"
