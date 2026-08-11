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

Write-Host "=== GMM contract and simulation tests ===" -ForegroundColor Cyan
Write-Host "Python: $Python"
Push-Location $PythonDir
try {
    & $Python -m unittest discover -s gmm/tests -p "test_*.py" -v
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -eq 0) {
        Write-Host "Result: All GMM tests passed" -ForegroundColor Green
    } else {
        Write-Host "Result: GMM tests FAILED (exit code $ExitCode)" -ForegroundColor Red
    }
} finally {
    Pop-Location
}

exit $ExitCode
