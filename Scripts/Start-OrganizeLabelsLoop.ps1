# Metadata-only organize loop — uses YOUR open editor via Monolith. Never spawns UE.
$Root = Split-Path -Parent $PSScriptRoot
$Python = "python"
$Loop = Join-Path $Root "Content\Python\run_organize_labels_safe_loop.py"

$running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*run_organize_labels_safe_loop*" }
if ($running) {
    Write-Host "Organize labels loop already running."
    exit 0
}

Start-Process -FilePath $Python -ArgumentList "`"$Loop`" --interval 600" -WorkingDirectory $Root -WindowStyle Hidden
Write-Host "Started organize labels loop (10 min interval)."
Write-Host "Heartbeat: $Root\Saved\Audit\organize_labels_loop_heartbeat.json"
Write-Host "Log: $Root\Saved\Logs\organize_labels_safe_loop.log"
