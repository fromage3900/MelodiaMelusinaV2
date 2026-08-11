# Consolidated Melodia project health runner.
# Orchestrates: MPC param fix, automation tests, and audit suite.
param(
    [ValidateSet("all", "fix-mpc", "test", "audit")]
    [string]$Mode = "all"
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$project = Join-Path $deploy ".." "BS_GodFile.uproject"
$projectRoot = Resolve-Path (Join-Path $deploy "..")
$contentPy = Join-Path $projectRoot "Content" "Python"

$engine = @(
    "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
    "C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
    "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $engine) {
    Write-Error "UnrealEditor-Cmd.exe not found"
    exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = Join-Path $projectRoot "Saved" "Logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Run-PythonScript {
    param([string]$ScriptName, [string]$Label)
    $scriptPath = Join-Path $contentPy $ScriptName
    $logFile = Join-Path $logDir "$Label-$timestamp.log"
    $absScript = (Resolve-Path $scriptPath).Path

    Write-Host ">>> [$Label] $absScript" -ForegroundColor Cyan
    & $engine $project -Unattended -NoSplash -NoSound -NullRHI `
        -log="$logFile" -AbsLog="$logFile" `
        -ExecutePythonScript="$absScript" -ExecCmds="quit"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "    PASS [$Label] (exit=$LASTEXITCODE)" -ForegroundColor Green
    } else {
        Write-Host "    FAIL [$Label] (exit=$LASTEXITCODE) — check $logFile" -ForegroundColor Red
    }
    return $LASTEXITCODE
}

$exitCode = 0

if ($Mode -in "all", "fix-mpc") {
    Write-Host "`n=== Phase: MPC Param Fix ===" -ForegroundColor Yellow
    $ec = Run-PythonScript -ScriptName "add_cozy_mpc_params.py" -Label "CozyMPC"
    if ($ec -ne 0) { $exitCode = $ec }
}

if ($Mode -in "all", "test") {
    Write-Host "`n=== Phase: Automation Tests ===" -ForegroundColor Yellow
    & $engine $project -Unattended -NoSplash -NoSound -NullRHI `
        -log="$logDir\MelodiaTests-$timestamp.log" `
        -ExecCmds="Automation RunTests Melodia.*; quit"
    if ($LASTEXITCODE -ne 0) { $exitCode = $LASTEXITCODE; Write-Warning "Tests reported failures" }
    else { Write-Host "    Tests PASS" -ForegroundColor Green }
}

if ($Mode -in "all", "audit") {
    Write-Host "`n=== Phase: Health Audit ===" -ForegroundColor Yellow
    $ec = Run-PythonScript -ScriptName "run_melodia_health_audits.py" -Label "MelodiaHealth"
    if ($ec -ne 0) { $exitCode = $ec }
}

Write-Host "`n=== Done (exit=$exitCode) ===" -ForegroundColor Yellow
exit $exitCode
