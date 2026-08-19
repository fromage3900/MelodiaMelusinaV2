param(
    [switch]$SkipBuild,
    [switch]$SkipGMM,
    [switch]$SkipNative
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ProjectFile = Join-Path $ProjectRoot "BS_GodFile.uproject"
$BuildBat = "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat"
$UnrealCmd = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$AuditRoot = Join-Path $ProjectRoot "Saved\Audit\BackendVerification\$Timestamp"
New-Item -ItemType Directory -Path $AuditRoot -Force | Out-Null

$runningEditor = Get-Process UnrealEditor, UnrealEditor-Cmd -ErrorAction SilentlyContinue
if ($runningEditor) {
    $ids = ($runningEditor | Select-Object -ExpandProperty Id) -join ", "
    throw "Backend verification refused: Unreal Editor process is live (PID $ids). Close it before a cold build or commandlet run."
}

$results = [ordered]@{
    timestamp = $Timestamp
    project = $ProjectFile
    build = if ($SkipBuild) { "skipped" } else { "pending" }
    gmm = if ($SkipGMM) { "skipped" } else { "pending" }
    native = if ($SkipNative) { "skipped" } else { "pending" }
    passed = $false
}

try {
    if (-not $SkipBuild) {
        if (-not (Test-Path -LiteralPath $BuildBat)) { throw "Build.bat not found: $BuildBat" }
        $buildLog = Join-Path $AuditRoot "build.log"
        & $BuildBat BS_GodFileEditor Win64 Development "-Project=$ProjectFile" -NoUBA -MaxParallelActions=4 2>&1 |
            Tee-Object -FilePath $buildLog
        if ($LASTEXITCODE -ne 0) {
            $results.build = "failed"
            throw "Cold UE build failed with exit code $LASTEXITCODE. See $buildLog"
        }
        $results.build = "passed"
    }

    if (-not $SkipGMM) {
        $gmmLog = Join-Path $AuditRoot "gmm.log"
        $gmmStdout = Join-Path $AuditRoot "gmm-stdout.log"
        $gmmStderr = Join-Path $AuditRoot "gmm-stderr.log"
        $gmmRunner = Join-Path $ProjectRoot "run_tests.ps1"
        $gmmArguments = "-NoProfile -ExecutionPolicy Bypass -File `"$gmmRunner`""
        $gmmProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $gmmArguments -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $gmmStdout -RedirectStandardError $gmmStderr
        @($gmmStdout, $gmmStderr) | ForEach-Object { if (Test-Path $_) { Get-Content $_ } } | Tee-Object -FilePath $gmmLog
        if ($gmmProcess.ExitCode -ne 0) {
            $results.gmm = "failed"
            throw "GMM verification failed with exit code $($gmmProcess.ExitCode). See $gmmLog"
        }
        $results.gmm = "passed"
    }

    if (-not $SkipNative) {
        if (-not (Test-Path -LiteralPath $UnrealCmd)) { throw "UnrealEditor-Cmd not found: $UnrealCmd" }
        $nativeLog = Join-Path $AuditRoot "native-automation.log"
        $reportPath = Join-Path $AuditRoot "AutomationReport"
        $arguments = @(
            $ProjectFile,
            "-unattended",
            "-nop4",
            "-nosplash",
            "-NullRHI",
            "-DisablePlugins=Monolith",
            '"-ExecCmds=Automation RunTests Melodia"',
            '"-TestExit=Automation Test Queue Empty"',
            "-ReportExportPath=`"$reportPath`"",
            "-abslog=`"$nativeLog`""
        )
        $process = Start-Process -FilePath $UnrealCmd -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden
        if ($process.ExitCode -ne 0) {
            $results.native = "failed"
            throw "Native Melodia automation process failed with exit code $($process.ExitCode). See $nativeLog"
        }
        if (-not (Test-Path -LiteralPath $nativeLog)) {
            $results.native = "failed"
            throw "Native automation produced no log: $nativeLog"
        }

        $nativeText = Get-Content -LiteralPath $nativeLog -Raw
        $completedMatches = [regex]::Matches($nativeText, 'Test Completed\. Result=\{(Success|Fail|NotRun)\}.*?Path=\{Melodia\.')
        $failedMatches = [regex]::Matches($nativeText, 'Test Completed\. Result=\{Fail\}.*?Path=\{Melodia\.')
        $queueMatch = [regex]::Match($nativeText, 'Automation Test Queue Empty ([0-9]+) tests performed')
        if (-not $queueMatch.Success) {
            $results.native = "failed"
            throw "Native automation did not prove queue completion. See $nativeLog"
        }
        $queuedCount = [int]$queueMatch.Groups[1].Value
        if ($queuedCount -lt 1 -or $completedMatches.Count -ne $queuedCount) {
            $results.native = "failed"
            throw "Native automation completion count mismatch: queue=$queuedCount completed=$($completedMatches.Count). See $nativeLog"
        }
        if ($failedMatches.Count -gt 0) {
            $results.native = "failed"
            throw "Native automation completed with $($failedMatches.Count) failed Melodia test(s). See $nativeLog"
        }
        if ($nativeText -match 'Fatal error:|Assertion failed:|ChooseDoor not implemented|Failed to instantiate the room: Level asset is invalid') {
            $results.native = "failed"
            throw "Native automation logged a fatal or ProceduralDungeon contract failure. See $nativeLog"
        }
        $results.native_test_count = $queuedCount
        $results.native = "passed"
    }

    $results.passed = $true
}
finally {
    $results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $AuditRoot "summary.json") -Encoding utf8
    Write-Host "Backend verification artifacts: $AuditRoot"
    Write-Host ($results | ConvertTo-Json -Compress)
}

if (-not $results.passed) { exit 1 }
exit 0