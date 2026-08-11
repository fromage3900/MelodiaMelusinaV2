# Stop surreal kit micro-loop
$deploy = $PSScriptRoot
$stopFile = Join-Path $deploy "SURREAL_ARCH_LOOP_STOP"
$pidFile = Join-Path $deploy "SURREAL_ARCH_LOOP.pid"

"" | Out-File -FilePath $stopFile -Encoding ascii

if (Test-Path $pidFile) {
    $pid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($pid) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped surreal loop PID $pid"
        }
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

Write-Host "Stop sentinel written: deploy/SURREAL_ARCH_LOOP_STOP"
