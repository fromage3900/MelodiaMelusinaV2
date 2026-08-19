# Dreamprint headless build orchestrator v2 — one editor at a time.
# Pre-flight: waits for a sustained editor-free window (no UnrealEditor-Cmd for
# 5 minutes), so other lanes' commandlets (ingest loops) never overlap ours.
$ErrorActionPreference = "Continue"
$UE = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$PROJ = "C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject"
$PY = "C:\EnvironmentPortfolio\BS_GodFile\Content\Python"
$LOG = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Logs"

Write-Host "=== Dreamprint build orchestrator v2 ==="

# ---- Pre-flight: sustained editor-free window ----
$absent = 0
Write-Host "Waiting for a sustained editor-free window (5 min of no UnrealEditor-Cmd)..."
$deadline = (Get-Date).AddHours(4)
while ((Get-Date) -lt $deadline) {
  $p = Get-Process UnrealEditor-Cmd -ErrorAction SilentlyContinue
  if (-not $p) {
    $absent++
    if ($absent -ge 20) { Write-Host "Window secured (5 min clean). Proceeding."; break }  # 20 x 15s
  } else {
    $absent = 0
    Write-Host ("  busy: " + $p.StartTime.ToString("HH:mm:ss") + " CPU=" + [math]::Round($p.CPU,0))
  }
  Start-Sleep -Seconds 15
}
if ($absent -lt 20) { Write-Host "ABORT: never got a clean window"; exit 2 }

function Run-Step([string]$script, [string]$logName) {
  $logPath = Join-Path $LOG $logName
  Write-Host "=== Step: $script ==="
  # NOTE: `-foo=$var` in native-call position is parsed as a parameter
  # declaration and NOT interpolated — always pre-build the argument string.
  $projArg = "`"$PROJ`""
  $scriptArg = "-ExecutePythonScript=$script"
  $logArg = "-log=`"$logPath`""
  & $UE $projArg $scriptArg -stdout -unattended -nullrhi -DisablePlugins=Monolith $logArg > $logPath 2>&1
  $rc = $LASTEXITCODE
  Write-Host "exit=$rc"
  Get-Content $logPath -Tail 4 | ForEach-Object { Write-Host "  | $_" }
  return $rc
}

$rc = Run-Step "$PY/build_dreamprint_material.py" "dreamprint_material.log"
if ($rc -ne 0) { Write-Host "ABORT: material build failed ($rc)"; exit 1 }
$rc = Run-Step "$PY/upgrade_grade_dreamprint.py" "dreamprint_grade.log"
if ($rc -ne 0) { Write-Host "ABORT: grade upgrade failed ($rc)"; exit 1 }
$rc = Run-Step "$PY/verify_dreamprint.py" "dreamprint_verify.log"
Write-Host "=== BUILD SEQUENCE COMPLETE (last exit=$rc) ==="
exit $rc