$logDir = 'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\gaea_setups\sea_above'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
& powershell -NoProfile -ExecutionPolicy Bypass -File 'C:\EnvironmentPortfolio\BS_GodFile\Tools\WorldGen\prepare_gaea_seaabove_export_native.ps1' `
    -Source 'C:\Program Files\QuadSpinner\Gaea 2\Examples\Canyon River with Sea.terrain' `
    -Destination "$logDir\CanyonRiverWithSea_SeaAbove.terrain" `
    -Report "$logDir\handoff_manifest.json" `
    > "$logDir\launcher_out.log" 2> "$logDir\launcher_err.log"
