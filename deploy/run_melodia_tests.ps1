# Headless Melodia test runner — runs all Melodia automation tests.
#
# The filter is a PREFIX match, not a regex. "Melodia." selects every Melodia.*
# test; "Melodia.*" selects none and the run reports
# "No automation tests matched 'Melodia.*'" with a non-zero exit code.
# Verified 2026-09-28 against UE 5.8 on this project.
param(
    [string]$TestFilter = "Melodia.",
    [switch]$ListTests,
    [switch]$QuitOnEnd = $true
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$root = Split-Path -Parent $deploy
$project = Join-Path $root "BS_GodFile.uproject"

$engine = @(
    "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
    "C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
    "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $engine) {
    Write-Error "UnrealEditor-Cmd.exe not found"
    exit 1
}

if (-not (Test-Path $project)) {
    Write-Error "Project file not found at $project"
    exit 1
}

if ($ListTests) {
    Write-Host "Listing tests matching '$TestFilter' ..."
    & $engine $project -RunTests "$TestFilter" -ListTests -stdout "C:/UnrealTestList.log" -Unattended -NoSplash
    exit $LASTEXITCODE
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$reportDir = Join-Path $root "Saved\Audit\MelodiaTests-$stamp"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$quit = if ($QuitOnEnd) { "Automation RunTests $TestFilter; quit" } else { "Automation RunTests $TestFilter" }

Write-Host "Engine:      $engine"
Write-Host "Project:     $project"
Write-Host "Filter:      $TestFilter"
Write-Host "Report:      $reportDir"
Write-Host ""

# Do NOT pass -log=<path> / -AbsLog=<path>. On this project that suppressed all
# logging: three separate invocations on 2026-09-28 exited 0 having done nothing
# and wrote no log at the given path, while identical runs without those two
# flags logged and executed normally. -ReportExportPath is the proven way to get
# a deterministic, machine-readable result (index.json + index.html).
#
# -nop4: a headless test run has no use for source control, and an expired p4
# ticket has visibly stalled boot here. Keep results independent of p4 state.
#
# The call operator is used instead of Start-Process so the arguments are passed
# without an extra round of quote handling, and $launchArgs does not shadow the
# automatic $args variable.
$launchArgs = @(
    $project
    "-nop4"
    "-Unattended"
    "-NoSplash"
    "-NoSound"
    "-NullRHI"
    "-ReportExportPath=$reportDir"
    "-ExecCmds=$quit"
)

& $engine @launchArgs
$engineExit = $LASTEXITCODE
Write-Host "Exit code: $engineExit"

$reportJson = Join-Path $reportDir "index.json"
if (Test-Path $reportJson) {
    Write-Host "Report written to $reportJson"
} else {
    Write-Warning "No automation report was produced in $reportDir even though the engine exited $engineExit. Treat this run as having produced NO evidence."
}

if ($engineExit -ne 0) {
    Write-Warning "Tests reported failures. Check $reportDir for details."
}

exit $engineExit
