param([int]$IntervalSec = 1200)
$log = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Echo\music_kit_loop.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
"LOOP_START $(Get-Date -Format o) interval=${IntervalSec}s pid=$PID" | Add-Content $log
while ($true) {
    Start-Sleep -Seconds $IntervalSec
    $line = 'AGENT_LOOP_TICK_MUSICKIT {"prompt":"Read BS_GodFile/Docs/MelodiaStudio/MUSIC_KIT_LEDGER_20260823.md tick log; execute the next unchecked backlog item end-to-end (implement -> headless verify with zero GN warnings -> EEVEE render x2 -> regenerate _contact_sheet.png -> append ledger lessons -> mirror deploy to Melodia_ClaireonTest copy-only -> sync live addons via _sync_addon_to_blender_5_2.py). Zero git writes. Append results as a new Tick section."}'
    Add-Content -Path $log -Value $line
    Write-Output $line
}
