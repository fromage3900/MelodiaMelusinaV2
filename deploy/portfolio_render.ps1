# deploy/portfolio_render.ps1
# Unifies the 12 disparate python scripts to render the portfolio shots headlessly.
# Usage: ./portfolio_render.ps1

$ErrorActionPreference = "Stop"

$ROOT_DIR = Split-Path $PSScriptRoot -Parent
$UPROJECT = Join-Path $ROOT_DIR "BS_GodFile.uproject"
$UNREAL_CMD = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$OUTPUT_DIR = Join-Path $ROOT_DIR "Products\Portfolio\$(Get-Date -Format 'yyyy-MM-dd')"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Running Portfolio Render Pipeline " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# The script that parses portfolio_schema.json and runs the Movie Pipeline
$PYTHON_SCRIPT = Join-Path $ROOT_DIR "Content\Python\run_portfolio_capture.py"

if (-not (Test-Path $PYTHON_SCRIPT)) {
    Write-Host "[WARN] run_portfolio_capture.py not found. Ensure pipeline scripts exist." -ForegroundColor Yellow
} else {
    $EXEC_CMD = "& `"$UNREAL_CMD`" `"$UPROJECT`" -ExecutePythonScript=`"$PYTHON_SCRIPT`" -NoUI -NoSound"
    Write-Host "Executing headless renders..." -ForegroundColor Yellow
    Invoke-Expression $EXEC_CMD
}

Write-Host "=========================================" -ForegroundColor Green
Write-Host " Render sequence complete." -ForegroundColor Green
Write-Host " Check $OUTPUT_DIR for results." -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
