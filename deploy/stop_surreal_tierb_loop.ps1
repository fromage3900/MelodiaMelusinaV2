# Stop Surreal Architecture tier-B Cursor wake loop
$deploy = $PSScriptRoot
$pidFile = Join-Path $deploy "SURREAL_TIERB_LOOP.pid"
$stopFile = Join-Path $deploy "SURREAL_TIERB_LOOP_STOP"

New-Item -Path $stopFile -ItemType File -Force | Out-Null

if (Test-Path $pidFile) {
    $loopPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($loopPid) {
        $proc = Get-Process -Id $loopPid -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $loopPid -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped surreal tier-B loop PID $loopPid"
        }
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "SURREAL_TIERB_LOOP_STOP sentinel written (no pid file)"
}
