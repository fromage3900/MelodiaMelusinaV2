# Stop Cursor-monitored surreal agent wake loop
$deploy = $PSScriptRoot
$pidFile = Join-Path $deploy "CURSOR_AGENT_LOOP.pid"
$stopFile = Join-Path $deploy "CURSOR_AGENT_LOOP_STOP"

New-Item -Path $stopFile -ItemType File -Force | Out-Null

if (Test-Path $pidFile) {
    $loopPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($loopPid) {
        $proc = Get-Process -Id $loopPid -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $loopPid -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped cursor agent loop PID $loopPid"
        }
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "CURSOR_AGENT_LOOP_STOP sentinel written (no pid file)"
}
