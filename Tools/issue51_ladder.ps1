# Tools/issue51_ladder.ps1 -- Issue #51 closing ladder helpers (preflight, packaged proof).
#
#   .\Tools\issue51_ladder.ps1 preflight [-AllowEditor]   exclusive-tree checks; exit 1 on any blocker
#   .\Tools\issue51_ladder.ps1 package                   BuildCookRun -> G:\melodia_packages\P0_Closeout_<date> (no -map=)
#   .\Tools\issue51_ladder.ps1 launch [-Seconds 90]      boot the packaged exe outside the editor, scan its log
#
# Receipts land in Saved\Audit\issue51_ladder_<date>\ (preflight.json, package.log, launch.json).
# The restart rung is Tools\issue51_restart_proof.py (needs the editor, so run preflight -AllowEditor).
param(
    [Parameter(Position = 0, Mandatory = $true)][ValidateSet('preflight', 'package', 'launch')][string]$Mode,
    [switch]$AllowEditor,
    [int]$Seconds = 90,
    [string]$PackageRoot = 'G:\melodia_packages'
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$Uproject = Join-Path $Root 'BS_GodFile.uproject'
$Uat = 'C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat'
$Stamp = Get-Date -Format 'yyyyMMdd'
$Audit = Join-Path $Root "Saved\Audit\issue51_ladder_$Stamp"
$Archive = Join-Path $PackageRoot "P0_Closeout_$Stamp"
New-Item -ItemType Directory -Force -Path $Audit | Out-Null

function Write-Receipt($Name, $Object) {
    $Object | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 (Join-Path $Audit $Name)
}

if ($Mode -eq 'preflight') {
    $blockers = @()
    $editors = @(Get-Process -Name 'UnrealEditor', 'UnrealEditor-Cmd' -ErrorAction SilentlyContinue)
    if ($AllowEditor) {
        if ($editors.Count -gt 1) { $blockers += "$($editors.Count) editor processes (need exactly one)" }
    } elseif ($editors.Count -gt 0) {
        $blockers += "editor running (pids $($editors.Id -join ','))"
    }
    $live = @(Get-Process -Name 'LiveCodingConsole' -ErrorAction SilentlyContinue)
    if (-not $AllowEditor -and $live.Count -gt 0) { $blockers += 'LiveCodingConsole running' }
    $proxies = @(Get-Process -Name 'monolith_proxy' -ErrorAction SilentlyContinue)
    if ($proxies.Count -gt 1) { $blockers += "$($proxies.Count) monolith_proxy processes (another session attached?)" }
    $locked = @()
    if (-not $AllowEditor) {
        foreach ($dll in Get-ChildItem (Join-Path $Root 'Binaries\Win64') -Filter 'UnrealEditor-BS_GodFile*.dll' -ErrorAction SilentlyContinue) {
            try { $s = [IO.File]::Open($dll.FullName, 'Open', 'ReadWrite', 'None'); $s.Close() } catch { $locked += $dll.Name }
        }
        if ($locked) { $blockers += "locked DLLs: $($locked -join ', ')" }
    }
    $free = @{}
    foreach ($d in 'C', 'G') {
        $drive = Get-PSDrive -Name $d -ErrorAction SilentlyContinue
        if ($drive) { $free[$d] = [math]::Round($drive.Free / 1GB, 1) }
    }
    if ($free['C'] -lt 20) { $blockers += "C: only $($free['C']) GB free" }
    if (-not $free.ContainsKey('G')) { $blockers += 'G: not mounted (package target)' }
    elseif ($free['G'] -lt 10) { $blockers += "G: only $($free['G']) GB free" }
    $head = (git -C $Root rev-parse --short HEAD).Trim()
    $branch = (git -C $Root rev-parse --abbrev-ref HEAD).Trim()
    $result = [ordered]@{ ok = ($blockers.Count -eq 0); mode = $(if ($AllowEditor) { 'editor' } else { 'closed-editor' });
        branch = $branch; head = $head; free_gb = $free; blockers = $blockers; at = (Get-Date -Format s) }
    Write-Receipt 'preflight.json' $result
    if ($branch -ne 'main') { Write-Host "NOTE: on '$branch' -- closing receipts must come from current main" -ForegroundColor Yellow }
    if ($blockers) { $blockers | ForEach-Object { Write-Host "BLOCKER $_" -ForegroundColor Red }; exit 1 }
    Write-Host "preflight OK ($branch @ $head)" -ForegroundColor Green
    exit 0
}

if ($Mode -eq 'package') {
    New-Item -ItemType Directory -Force -Path $Archive | Out-Null
    $log = Join-Path $Audit 'package.log'
    # No -map=: MapsToCook in DefaultGame.ini decides, same as the 09-03 package_launch row.
    & $Uat BuildCookRun "-project=$Uproject" -noP4 -platform=Win64 -clientconfig=Development `
        -build -cook -stage -pak -iostore -archive "-archivedirectory=$Archive" -unattended -utf8output *>&1 |
        Tee-Object -FilePath $log | Select-String -Pattern 'BUILD SUCCESSFUL|AutomationTool exiting|Error:' | ForEach-Object { $_.Line }
    $code = $LASTEXITCODE
    Write-Receipt 'package.json' ([ordered]@{ exit_code = $code; archive = $Archive; log = $log; at = (Get-Date -Format s) })
    if ($code -ne 0) { Write-Host "package FAILED ($code) -- see $log" -ForegroundColor Red; exit 1 }
    Write-Host "package OK -> $Archive" -ForegroundColor Green
    exit 0
}

# launch
$exe = Join-Path $Archive 'Windows\BS_GodFile.exe'
if (-not (Test-Path $exe)) { Write-Host "no packaged exe at $exe -- run 'package' first" -ForegroundColor Red; exit 2 }
$gameLog = Join-Path $Archive 'Windows\BS_GodFile\Saved\Logs\BS_GodFile.log'
if (Test-Path $gameLog) { Remove-Item $gameLog }
$proc = Start-Process -FilePath $exe -ArgumentList '-windowed', '-ResX=1600', '-ResY=900', '-log' -PassThru
Start-Sleep -Seconds $Seconds
$alive = -not $proc.HasExited
if ($alive) { Stop-Process -Id $proc.Id -Force }
$text = if (Test-Path $gameLog) { Get-Content $gameLog -Raw } else { '' }
$checks = [ordered]@{
    log_exists       = [bool]$text
    process_survived = $alive
    fatals           = ([regex]::Matches($text, 'Fatal error|Assertion failed|Unhandled Exception')).Count
    io_store_mounted = $text -match 'BS_GodFile-Windows\.utoc'
    main_menu_loaded = $text -match 'LoadMap.*L_MelodiaMainMenu'
    menu_ui_added    = $text -match 'OrreryMainMenuGameMode'
}
$ok = $checks.log_exists -and $checks.process_survived -and $checks.fatals -eq 0 -and $checks.main_menu_loaded
$result = [ordered]@{ ok = $ok; exe = $exe; seconds = $Seconds; checks = $checks; game_log = $gameLog; at = (Get-Date -Format s) }
Write-Receipt 'launch.json' $result
$checks.GetEnumerator() | ForEach-Object { Write-Host ("  {0,-16} {1}" -f $_.Key, $_.Value) }
if ($ok) { Write-Host 'launch PASS' -ForegroundColor Green; exit 0 }
Write-Host 'launch FAIL' -ForegroundColor Red
exit 1
