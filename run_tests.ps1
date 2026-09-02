param(
    [ValidateSet("All", "GMM", "P0", "Contracts", "Fast")]
    [string]$Suite = "All",
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonDir = Join-Path $ProjectRoot "Content\Python"
$BundledPython = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe"

$Python = if (Test-Path -LiteralPath $BundledPython) {
    $BundledPython
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    (Get-Command python).Source
} else {
    throw "No Python runtime found. Expected UE bundled Python at $BundledPython."
}

$env:PYTHONPATH = "$PythonDir;$ProjectRoot"
$OverallFailed = $false
$TestResults = [System.Collections.Generic.List[PSCustomObject]]::new()

function Run-TestSuite {
    param(
        [string]$Name,
        [scriptblock]$Action
    )
    Write-Host "`n=== [$Name] ===" -ForegroundColor Cyan
    $Sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        & $Action
        $Code = $LASTEXITCODE
        $Sw.Stop()
        if ($Code -eq 0) {
            Write-Host "  -> PASS: $Name ($([math]::Round($Sw.Elapsed.TotalSeconds, 2))s)" -ForegroundColor Green
            $TestResults.Add([PSCustomObject]@{ Suite = $Name; Status = "PASS"; Duration = "$([math]::Round($Sw.Elapsed.TotalSeconds, 2))s" })
        } else {
            Write-Host "  -> FAIL: $Name (exit code $Code, $([math]::Round($Sw.Elapsed.TotalSeconds, 2))s)" -ForegroundColor Red
            $script:OverallFailed = $true
            $TestResults.Add([PSCustomObject]@{ Suite = $Name; Status = "FAIL"; Duration = "$([math]::Round($Sw.Elapsed.TotalSeconds, 2))s" })
        }
    } catch {
        $Sw.Stop()
        Write-Host "  -> ERROR: $Name - $_" -ForegroundColor Red
        $script:OverallFailed = $true
        $TestResults.Add([PSCustomObject]@{ Suite = $Name; Status = "ERROR"; Duration = "$([math]::Round($Sw.Elapsed.TotalSeconds, 2))s" })
    }
}

Write-Host "==========================================" -ForegroundColor Magenta
Write-Host " Melodia Test Automation Runner ($Suite) " -ForegroundColor Magenta
Write-Host " Python: $Python" -ForegroundColor Gray
Write-Host " Root:   $ProjectRoot" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Magenta

# 1. GMM Suite
if ($Suite -in @("All", "GMM", "Fast")) {
    Run-TestSuite -Name "GMM Simulation & Contract Tests" -Action {
        Push-Location $PythonDir
        try {
            & $Python -m unittest discover -s gmm/tests -p "test_*.py" $(if ($VerboseOutput) { "-v" } else { "" })
        } finally {
            Pop-Location
        }
    }
}

# 2. P0 Content & Integration Suite
if ($Suite -in @("All", "P0", "Fast")) {
    Run-TestSuite -Name "P0 Content & Integration Tests" -Action {
        Push-Location $PythonDir
        try {
            & $Python -m unittest discover -s Tests -p "test_*.py" $(if ($VerboseOutput) { "-v" } else { "" })
        } finally {
            Pop-Location
        }
    }
}

# 3. ECHO & Progression Contract Suite
if ($Suite -in @("All", "Contracts")) {
    Run-TestSuite -Name "ECHO Pipeline Contracts" -Action {
        Push-Location $ProjectRoot
        try {
            & $Python Tools/test_echo_contract.py
            if ($LASTEXITCODE -ne 0) { return }
            & $Python Tools/test_melodia_progression_contract.py
            if ($LASTEXITCODE -ne 0) { return }
            & $Python Tools/test_melodia_first_dream_route_contract.py
        } finally {
            Pop-Location
        }
    }
}

# 4. Adversarial Challenger Suite (if in Contracts or All)
if ($Suite -in @("Contracts")) {
    Run-TestSuite -Name "Adversarial Challenger Suite" -Action {
        Push-Location $ProjectRoot
        try {
            & $Python -m unittest Tools/test_adversarial_challenger.py
        } finally {
            Pop-Location
        }
    }
}

Write-Host "`n==========================================" -ForegroundColor Magenta
Write-Host " Test Summary" -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta
foreach ($Res in $TestResults) {
    $Color = if ($Res.Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host " - $($Res.Suite): $($Res.Status) ($($Res.Duration))" -ForegroundColor $Color
}

if ($OverallFailed) {
    Write-Host "`nRESULT: FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`nRESULT: ALL TESTS PASSED" -ForegroundColor Green
    exit 0
}
