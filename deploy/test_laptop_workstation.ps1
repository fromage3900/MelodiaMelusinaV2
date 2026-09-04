# Melodia laptop workstation acceptance runner.
#
# Default mode is a low-memory Smoke suite. Higher-cost lanes are explicit:
#   Smoke     hardware/setup validation + offline contracts
#   Fast      Smoke + run_tests.ps1 -Suite Fast
#   Contracts Smoke + run_tests.ps1 -Suite Contracts
#   Build     closed-editor C++/plugin build + binary validation
#   Sync      Git/LFS two-workstation sync preflight
#   UE        NullRHI Unreal automation tests
#   All       every lane above
#
# Every run records Git provenance and results under Saved\Workstation\, which is
# ignored by the repository. The runner never stages, commits, pushes, deletes,
# or installs anything.
[CmdletBinding()]
param(
    [ValidateSet("Smoke", "Fast", "Contracts", "Build", "Sync", "UE", "All")]
    [string]$Suite = "Smoke",

    [ValidateRange(1, 8)]
    [int]$MaxParallelActions = 1,

    [switch]$RequireClean,

    [switch]$VerboseOutput
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ProjectFile = Join-Path $ProjectRoot "BS_GodFile.uproject"
$ReportDirectory = Join-Path $ProjectRoot "Saved\Workstation"
$MachineName = if ([string]::IsNullOrWhiteSpace($env:COMPUTERNAME)) { "machine" } else { $env:COMPUTERNAME }
$ReportPath = Join-Path $ReportDirectory "$MachineName-laptop-tests.json"
$script:Results = [System.Collections.Generic.List[object]]::new()
$script:HadFailure = $false
$script:BeforeStatus = @()
$script:GitState = [ordered]@{}

function Limit-Output {
    param(
        [string]$Value,
        [int]$Maximum = 12000
    )

    if ($null -eq $Value) {
        return ""
    }
    if ($Value.Length -le $Maximum) {
        return $Value
    }
    return "[truncated; showing the final $Maximum characters]" + [Environment]::NewLine + $Value.Substring($Value.Length - $Maximum)
}

function Add-Result {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail,
        [double]$DurationSeconds = 0,
        [string]$Output = ""
    )

    $record = [ordered]@{
        name = $Name
        passed = $Passed
        detail = $Detail
        duration_seconds = [math]::Round($DurationSeconds, 2)
        output = Limit-Output $Output
    }
    [void]$script:Results.Add([pscustomobject]$record)

    if (-not $Passed) {
        $script:HadFailure = $true
    }

    $status = if ($Passed) { "PASS" } else { "FAIL" }
    $color = if ($Passed) { "Green" } else { "Red" }
    Write-Host ("  [{0,-4}] {1}: {2}" -f $status, $Name, $Detail) -ForegroundColor $color
    if ($VerboseOutput -and -not [string]::IsNullOrWhiteSpace($Output)) {
        Write-Host (Limit-Output $Output 4000) -ForegroundColor Gray
    }
}

function Invoke-External {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory = $ProjectRoot
    )

    $command = Get-Command $FilePath -ErrorAction SilentlyContinue
    if ($null -eq $command -and -not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
        Add-Result -Name $Name -Passed $false -Detail "executable not found: $FilePath"
        return $false
    }

    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    $lines = @()
    $exitCode = 0
    try {
        Push-Location $WorkingDirectory
        try {
            $lines = @(& $FilePath @Arguments 2>&1 | ForEach-Object { [string]$_ })
            $exitCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
        } finally {
            Pop-Location
        }
    } catch {
        $exitCode = 1
        $lines = @($_.Exception.Message)
    }
    $watch.Stop()

    $output = $lines -join [Environment]::NewLine
    $passed = $exitCode -eq 0
    $detail = if ($passed) { "exit 0 in $([math]::Round($watch.Elapsed.TotalSeconds, 2))s" } else { "exit $exitCode in $([math]::Round($watch.Elapsed.TotalSeconds, 2))s" }
    Add-Result -Name $Name -Passed $passed -Detail $detail -DurationSeconds $watch.Elapsed.TotalSeconds -Output $output
    return $passed
}

function Invoke-Python {
    param(
        [string]$Name,
        [string[]]$Arguments
    )

    if ($null -eq $script:PythonExe) {
        Add-Result -Name $Name -Passed $false -Detail "Python runtime not found"
        return $false
    }
    return Invoke-External -Name $Name -FilePath $script:PythonExe -Arguments $Arguments
}

function Invoke-ProjectPowerShell {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [string[]]$ScriptArguments
    )

    if ($null -eq $script:PowerShellExe) {
        Add-Result -Name $Name -Passed $false -Detail "PowerShell runtime not found"
        return $false
    }
    if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) {
        Add-Result -Name $Name -Passed $false -Detail "script not found: $ScriptPath"
        return $false
    }

    $arguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $ScriptPath)
    $arguments += $ScriptArguments
    return Invoke-External -Name $Name -FilePath $script:PowerShellExe -Arguments $arguments
}

function Test-InteractiveEditorClosed {
    $processes = @(Get-Process -Name "UnrealEditor", "UnrealEditor-Cmd" -ErrorAction SilentlyContinue)
    if ($processes.Count -eq 0) {
        Add-Result -Name "Closed-editor precondition" -Passed $true -Detail "no UnrealEditor process is running"
        return $true
    }

    $names = ($processes | Select-Object -ExpandProperty ProcessName) -join ", "
    Add-Result -Name "Closed-editor precondition" -Passed $false -Detail "close the editor before this lane; running process(es): $names"
    return $false
}

function Test-RequiredPaths {
    $requiredPaths = @(
        "BS_GodFile.uproject",
        ".vsconfig",
        "Config",
        "Source",
        "Plugins",
        "Content\Melodia\Levels",
        "Content\Melodia\PCG",
        "deploy",
        "Tools",
        "specs"
    )

    foreach ($relativePath in $requiredPaths) {
        $absolutePath = Join-Path $ProjectRoot $relativePath
        $present = Test-Path -LiteralPath $absolutePath
        Add-Result -Name "Required path $relativePath" -Passed $present -Detail $(if ($present) { "present" } else { "missing from the UE-capable checkout" })
    }
}

function Invoke-GitBaseline {
    if ($null -eq $script:GitExe) {
        Add-Result -Name "Git executable" -Passed $false -Detail "git is not on PATH"
        return
    }

    $head = (& $script:GitExe -C $ProjectRoot rev-parse HEAD 2>&1 | Out-String).Trim()
    $branch = (& $script:GitExe -C $ProjectRoot branch --show-current 2>&1 | Out-String).Trim()
    $status = @(& $script:GitExe -C $ProjectRoot status --short 2>&1)
    $script:BeforeStatus = $status

    $script:GitState = [ordered]@{
        head = $head
        branch = $branch
        status_before = $status
    }

    $validHead = $head -match "^[0-9a-f]{40}$"
    Add-Result -Name "Git provenance" -Passed $validHead -Detail "branch=$branch; HEAD=$head"
}

function Invoke-GitChecks {
    if ($null -eq $script:GitExe) {
        return
    }

    $lfsOutput = @(& $script:GitExe -C $ProjectRoot lfs version 2>&1)
    $lfsCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    Add-Result -Name "Git LFS availability" -Passed ($lfsCode -eq 0) -Detail $(if ($lfsCode -eq 0) { ($lfsOutput -join " ").Trim() } else { "git lfs version failed" }) -Output ($lfsOutput -join [Environment]::NewLine)

    $lfsFiles = @(& $script:GitExe -C $ProjectRoot lfs ls-files --long 2>&1)
    $lfsFilesCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    Add-Result -Name "Git LFS inventory" -Passed ($lfsFilesCode -eq 0) -Detail "$($lfsFiles.Count) tracked LFS record(s)" -Output (($lfsFiles | Select-Object -First 20) -join [Environment]::NewLine)

    $diffOutput = @(& $script:GitExe -C $ProjectRoot diff --check 2>&1)
    $diffCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    Add-Result -Name "Git whitespace check" -Passed ($diffCode -eq 0) -Detail $(if ($diffCode -eq 0) { "git diff --check is clean" } else { "whitespace errors reported" }) -Output ($diffOutput -join [Environment]::NewLine)
}

function Invoke-BaseChecks {
    Write-Host ""
    Write-Host "=== [Laptop base preflight] ===" -ForegroundColor Cyan
    Invoke-GitBaseline
    Test-RequiredPaths
    Invoke-GitChecks

    $inspectScript = Join-Path $ProjectRoot "deploy\inspect_workstation.ps1"
    Invoke-ProjectPowerShell -Name "Hardware/toolchain inspection" -ScriptPath $inspectScript -ScriptArguments @()

    $validator = Join-Path $ProjectRoot "deploy\validate_setup.ps1"
    Invoke-ProjectPowerShell -Name "Portable setup validation" -ScriptPath $validator -ScriptArguments @("-SkipServices", "-CheckLfsHydration")
}

function Invoke-SmokeSuite {
    Write-Host ""
    Write-Host "=== [Laptop Smoke suite] ===" -ForegroundColor Cyan
    Invoke-Python -Name "Offline contract floor" -Arguments @("Tools/run_contract_tests.py", "--offline")
    Invoke-Python -Name "Melodia MCP offline suite" -Arguments @("Tools/test_melodia_mcp.py")
    Invoke-Python -Name "Wardrobe transaction contract" -Arguments @("Tools/test_melodia_wardrobe_transaction_contract.py")
    Invoke-Python -Name "Wardrobe catalog contract" -Arguments @("Tools/test_melodia_wardrobe_catalog_contract.py")
    Invoke-Python -Name "Source-control ownership contract" -Arguments @("Tools/test_validate_source_control_ownership.py")
    Invoke-Python -Name "Package-launch contract" -Arguments @("Tools/test_melodia_package_launch_contract.py")
}

function Invoke-FastSuite {
    $arguments = @("-Suite", "Fast")
    if ($VerboseOutput) {
        $arguments += "-VerboseOutput"
    }
    Invoke-ProjectPowerShell -Name "Existing Fast Python/GMM/P0 suite" -ScriptPath (Join-Path $ProjectRoot "run_tests.ps1") -ScriptArguments $arguments
}

function Invoke-ContractsSuite {
    $arguments = @("-Suite", "Contracts")
    if ($VerboseOutput) {
        $arguments += "-VerboseOutput"
    }
    Invoke-ProjectPowerShell -Name "Existing ECHO/progression/contracts suite" -ScriptPath (Join-Path $ProjectRoot "run_tests.ps1") -ScriptArguments $arguments
}

function Invoke-BuildSuite {
    Write-Host ""
    Write-Host "=== [Laptop closed-editor build suite] ===" -ForegroundColor Cyan
    if (-not (Test-InteractiveEditorClosed)) {
        return
    }

    $buildBat = Join-Path $script:UnrealRoot "Engine\Build\BatchFiles\Build.bat"
    if (-not (Test-Path -LiteralPath $buildBat -PathType Leaf)) {
        Add-Result -Name "UE Build.bat" -Passed $false -Detail "not found at $buildBat"
        return
    }

    $buildArguments = @("BS_GodFileEditor", "Win64", "Development", "-Project=$ProjectFile", "-NoUBA", "-MaxParallelActions=$MaxParallelActions")
    Invoke-External -Name "Closed-editor UE plugin build" -FilePath $buildBat -Arguments $buildArguments
    $validator = Join-Path $ProjectRoot "deploy\validate_setup.ps1"
    Invoke-ProjectPowerShell -Name "Compiled plugin binary validation" -ScriptPath $validator -ScriptArguments @("-SkipServices", "-CheckLfsHydration", "-RequirePluginBinaries")
}

function Invoke-SyncSuite {
    Write-Host ""
    Write-Host "=== [Laptop workstation sync suite] ===" -ForegroundColor Cyan
    $syncScript = Join-Path $ProjectRoot "deploy\sync_workstation.ps1"
    Invoke-ProjectPowerShell -Name "Two-workstation Git/LFS sync check" -ScriptPath $syncScript -ScriptArguments @("-Mode", "Check", "-LfsProfile", "None")

    $addonInstaller = Join-Path $ProjectRoot "deploy\install_melodia_studio.ps1"
    Invoke-ProjectPowerShell -Name "Blender live addon provenance" -ScriptPath $addonInstaller -ScriptArguments @("-CheckOnly")
}

function Invoke-UESuite {
    Write-Host ""
    Write-Host "=== [Laptop UE NullRHI automation suite] ===" -ForegroundColor Cyan
    if (-not (Test-InteractiveEditorClosed)) {
        return
    }

    $editorCmd = Join-Path $script:UnrealRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
    if (-not (Test-Path -LiteralPath $editorCmd -PathType Leaf)) {
        Add-Result -Name "UnrealEditor-Cmd" -Passed $false -Detail "not found at $editorCmd"
        return
    }

    $commonArguments = @($ProjectFile, "-unattended", "-nop4", "-NullRHI", "-log")
    Invoke-External -Name "UE automation: Melodia" -FilePath $editorCmd -Arguments ($commonArguments + @("-ExecCmds=Automation RunTests Melodia;Quit"))
    Invoke-External -Name "UE automation: WardrobeGlide" -FilePath $editorCmd -Arguments ($commonArguments + @("-ExecCmds=Automation RunTests Melodia.Integration.WardrobeGlide;Quit"))
}

function Invoke-PostChecks {
    if ($null -eq $script:GitExe) {
        return
    }

    $afterStatus = @(& $script:GitExe -C $ProjectRoot status --short 2>&1)
    $script:GitState.status_after = $afterStatus
    $newStatus = @($afterStatus | Where-Object { $_ -notin $script:BeforeStatus })
    $noNewSpill = $newStatus.Count -eq 0
    Add-Result -Name "No new tracked working-tree spill" -Passed $noNewSpill -Detail $(if ($noNewSpill) { "tests did not add tracked changes" } else { "$($newStatus.Count) new status line(s)" }) -Output ($newStatus -join [Environment]::NewLine)

    if ($RequireClean) {
        $clean = $afterStatus.Count -eq 0
        Add-Result -Name "Clean working tree" -Passed $clean -Detail $(if ($clean) { "clean" } else { "pre-existing or test-created changes remain" }) -Output ($afterStatus -join [Environment]::NewLine)
    }
}

$script:GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if ($null -eq $script:GitCommand) {
    $script:GitCommand = Get-Command git -ErrorAction SilentlyContinue
}
$script:GitExe = if ($null -ne $script:GitCommand) { $script:GitCommand.Source } else { $null }

$script:PowerShellCommand = Get-Command powershell.exe -ErrorAction SilentlyContinue
if ($null -eq $script:PowerShellCommand) {
    $script:PowerShellCommand = Get-Command pwsh -ErrorAction SilentlyContinue
}
$script:PowerShellExe = if ($null -ne $script:PowerShellCommand) { $script:PowerShellCommand.Source } else { $null }

$script:UnrealRoot = $env:MELODIA_UNREAL_ROOT
if ([string]::IsNullOrWhiteSpace($script:UnrealRoot)) {
    $script:UnrealRoot = "C:\Program Files\Epic Games\UE_5.8"
}

$bundledPython = Join-Path $script:UnrealRoot "Engine\Binaries\ThirdParty\Python3\Win64\python.exe"
if (Test-Path -LiteralPath $bundledPython -PathType Leaf) {
    $script:PythonExe = $bundledPython
} else {
    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    }
    if ($null -eq $pythonCommand) {
        $pythonCommand = Get-Command py.exe -ErrorAction SilentlyContinue
    }
    $script:PythonExe = if ($null -ne $pythonCommand) { $pythonCommand.Source } else { $null }
}

New-Item -ItemType Directory -Path $ReportDirectory -Force | Out-Null

Write-Host "=========================================" -ForegroundColor Magenta
Write-Host " MELODIA LAPTOP WORKSTATION TEST RUNNER " -ForegroundColor Magenta
Write-Host " Suite:   $Suite" -ForegroundColor Gray
Write-Host " Root:    $ProjectRoot" -ForegroundColor Gray
Write-Host " UE root: $script:UnrealRoot" -ForegroundColor Gray
Write-Host " Python:  $script:PythonExe" -ForegroundColor Gray
Write-Host "=========================================" -ForegroundColor Magenta

Invoke-BaseChecks

switch ($Suite) {
    "Smoke" {
        Invoke-SmokeSuite
    }
    "Fast" {
        Invoke-SmokeSuite
        Invoke-FastSuite
    }
    "Contracts" {
        Invoke-SmokeSuite
        Invoke-ContractsSuite
    }
    "Build" {
        Invoke-BuildSuite
    }
    "Sync" {
        Invoke-SyncSuite
    }
    "UE" {
        Invoke-UESuite
    }
    "All" {
        Invoke-SmokeSuite
        Invoke-FastSuite
        Invoke-ContractsSuite
        Invoke-BuildSuite
        Invoke-SyncSuite
        Invoke-UESuite
    }
}

Invoke-PostChecks

$passed = @($script:Results | Where-Object { $_.passed }).Count
$failed = @($script:Results | Where-Object { -not $_.passed }).Count
$finalStatus = if ($script:HadFailure) { "failed" } else { "passed" }

$report = [ordered]@{
    schema = "melodia.laptop_workstation_test_report.v1"
    generated_at = (Get-Date).ToString("o")
    machine = $MachineName
    suite = $Suite
    max_parallel_actions = $MaxParallelActions
    require_clean = [bool]$RequireClean
    unreal_root = $script:UnrealRoot
    python_executable = $script:PythonExe
    project_root = $ProjectRoot
    git = $script:GitState
    status = $finalStatus
    passed = $passed
    failed = $failed
    results = @($script:Results)
    report_path = $ReportPath
}

$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8

Write-Host ""
Write-Host "=========================================" -ForegroundColor Magenta
Write-Host " RESULT: $finalStatus ($passed passed, $failed failed)" -ForegroundColor $(if ($script:HadFailure) { "Red" } else { "Green" })
Write-Host " Evidence: $ReportPath" -ForegroundColor Gray
Write-Host "=========================================" -ForegroundColor Magenta

exit $(if ($script:HadFailure) { 1 } else { 0 })
