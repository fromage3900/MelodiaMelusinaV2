$ErrorActionPreference = 'Stop'
$logDir = 'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\gaea_setups\sea_above'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$source = 'C:\Program Files\QuadSpinner\Gaea 2\Examples\Canyon River with Sea.terrain'
$destination = "$logDir\CanyonRiverWithSea_SeaAbove.terrain"
$report = "$logDir\handoff_manifest.json"
if (-not (Test-Path -LiteralPath $source)) { throw "Missing Gaea source graph: $source" }
& powershell -NoProfile -ExecutionPolicy Bypass -File 'C:\EnvironmentPortfolio\BS_GodFile\Tools\WorldGen\prepare_gaea_seaabove_export_native.ps1' `
    -Source $source `
    -Destination $destination `
    -Report $report `
    > "$logDir\launcher_out.log" 2> "$logDir\launcher_err.log"
if ($LASTEXITCODE -ne 0) { throw "Sea Above Gaea prep failed with exit code $LASTEXITCODE; see $logDir\launcher_err.log" }
if (-not (Test-Path -LiteralPath $destination)) { throw "Sea Above prep produced no destination graph: $destination" }
if (-not (Test-Path -LiteralPath $report)) { throw "Sea Above prep produced no handoff manifest: $report" }
