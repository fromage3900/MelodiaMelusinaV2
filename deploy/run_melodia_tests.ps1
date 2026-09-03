# Headless Melodia test runner — runs all Melodia.* automation tests.
param(
    [string]$TestFilter = "Melodia.*",
    [switch]$ListTests,
    [switch]$QuitOnEnd = $true
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$project = Join-Path $deploy ".." "BS_GodFile.uproject"

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

$logFile = Join-Path $deploy ".." "Saved" "Logs" "MelodiaTests-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
$quit = if ($QuitOnEnd) { "-ExecCmds=`"Automation RunTests $TestFilter; quit`"" } else { "-ExecCmds=`"Automation RunTests $TestFilter`"" }

Write-Host "Engine:      $engine"
Write-Host "Project:     $project"
Write-Host "Filter:      $TestFilter"
Write-Host "Log:         $logFile"
Write-Host ""

$args = @(
    $project
    "-Unattended"
    "-NoSplash"
    "-NoSound"
    "-NullRHI"
    "-nullrhi"
    "-log=`"$logFile`""
    "-AbsLog=`"$logFile`""
    $quit
)

$proc = Start-Process -FilePath $engine -ArgumentList $args -NoNewWindow -Wait -PassThru
Write-Host "Exit code: $($proc.ExitCode)"
Write-Host "Test log written to $logFile"

if ($proc.ExitCode -ne 0) {
    Write-Warning "Tests reported failures. Check $logFile for details."
}

exit $proc.ExitCode
