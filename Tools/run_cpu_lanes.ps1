param(
    [string]$ProjectRoot = "C:\EnvironmentPortfolio\BS_GodFile",
    [string]$LogDir = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit"
)

$ErrorActionPreference = "Continue"
$Stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$LogFile = Join-Path $LogDir "cpu_lanes_$Stamp.log"
$DoneMarker = Join-Path $LogDir "cpu_lanes_done_$Stamp.marker"

function Write-Log([string]$Message) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding utf8
}

Push-Location $ProjectRoot
try {
    Write-Log "=== qwen3.8-27b lane (cpu) ==="
    & python Tools/run_math_models.py --model qwen3.8-27b --cpu --timeout 600 2>&1 | ForEach-Object { Write-Log $_ }
    Write-Log "qwen3.8-27b exit=$LASTEXITCODE"

    Write-Log "=== muse-glimmer-30b lane (cpu) ==="
    & python Tools/run_math_models.py --run-muse --cpu --timeout 600 2>&1 | ForEach-Object { Write-Log $_ }
    Write-Log "muse exit=$LASTEXITCODE"
}
finally {
    Pop-Location
}

Set-Content -LiteralPath $DoneMarker -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss") -Encoding ascii
Write-Log "DONE $DoneMarker"