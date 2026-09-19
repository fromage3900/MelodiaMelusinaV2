# Stop realtime world conductor
$deploy = $PSScriptRoot
$stopFile = Join-Path $deploy "SURREAL_REALTIME_WORLD_LOOP_STOP"
$pidFile = Join-Path $deploy "SURREAL_REALTIME_WORLD_LOOP.pid"

"" | Out-File -FilePath $stopFile -Encoding ascii

if (Test-Path $pidFile) {
    $loopPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($loopPid) {
        $proc = Get-Process -Id $loopPid -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $loopPid -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped realtime world conductor PID $loopPid"
        }
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

Write-Host "Stop sentinel written: deploy/SURREAL_REALTIME_WORLD_LOOP_STOP"
