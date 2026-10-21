<#
.SYNOPSIS
  Melodia demo display setup: 4K render, vsync on, borderless, standalone launch.

.DESCRIPTION
  "4K always" on any machine:
    * internal render is always 3840x2160 -> r.ScreenPercentage = 3840*2160/(panelW*panelH)*100
      (150 on 2560x1440, 200 on 1920x1080, 100 on a 4K panel)
    * presentation is borderless fullscreen (fills whatever panel exists)
    * vsync on, frame rate limit 0 (vsync governs)
    * the Play button launches a standalone process (LastExecutedPlayModeType=PlayMode_InNewProcess)

  Writes only the per-user config layer under Saved/Config/WindowsEditor/ - never the
  project's tracked Config/*.ini. Backs up every file it touches.

  IMPORTANT: run this while the editor is CLOSED. A running editor holds the same
  settings in memory and rewrites these files on exit, reverting the patch.

.PARAMETER Apply
  Actually write. Without it the script only reports what it would change.

.PARAMETER TargetWidth
  Internal render width. Default 3840.

.PARAMETER TargetHeight
  Internal render height. Default 2160.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File deploy/set_demo_4k.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File deploy/set_demo_4k.ps1 -Apply
#>
[CmdletBinding()]
param(
  [switch] $Apply,
  [int] $TargetWidth = 3840,
  [int] $TargetHeight = 2160
)

$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
$CfgDir = Join-Path $Repo 'Saved\Config\WindowsEditor'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::AllScreens | Where-Object { $_.Primary } | Select-Object -First 1
if (-not $screen) { $screen = [System.Windows.Forms.Screen]::PrimaryScreen }
$panelW = $screen.Bounds.Width
$panelH = $screen.Bounds.Height

$pct = [math]::Round([math]::Min($TargetWidth / $panelW, $TargetHeight / $panelH) * 100.0)
$pct = [math]::Max(100, [math]::Min(200, $pct))

Write-Host ''
Write-Host '=== Melodia demo display setup ===' -ForegroundColor Cyan
Write-Host ("  panel          : {0}x{1} ({2})" -f $panelW, $panelH, $screen.DeviceName)
Write-Host ("  internal render: {0}x{1}  ->  r.ScreenPercentage {2}" -f $TargetWidth, $TargetHeight, $pct)
Write-Host ("  presentation   : borderless fullscreen, vsync ON, limit 0")
Write-Host ("  play mode      : PlayMode_InNewProcess (standalone window)")
Write-Host ''

function Read-Text([string]$path) {
  if (Test-Path $path) { return [IO.File]::ReadAllText($path) }
  return ""
}
function Write-Text([string]$path, [string]$text) {
  $dir = Split-Path -Parent $path
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))
}
function Set-IniKey([string]$text, [string]$key, [string]$value, [string]$section = '') {
  # replaces the key inside a section (or anywhere when no section given); appends if missing
  $lines = $text -split "`r?`n"
  $out = New-Object System.Collections.Generic.List[string]
  $inSection = ($section -eq '')
  $written = $false
  foreach ($line in $lines) {
    $trim = $line.Trim()
    if ($trim -match '^\[(.+)\]\s*$') { $inSection = ($matches[1] -eq $section) }
    if ($inSection -and $trim -match ("^" + [regex]::Escape($key) + "\s*=")) {
      $out.Add("$key=$value"); $written = $true; continue
    }
    $out.Add($line)
  }
  if (-not $written) {
    if ($section -ne '') {
      $idx = -1
      for ($i = 0; $i -lt $out.Count; $i++) { if ($out[$i].Trim() -match '^\[(.+)\]\s*$' -and $matches[1] -eq $section) { $idx = $i; break } }
      if ($idx -ge 0) { $out.Insert($idx + 1, "$key=$value") }
      else { $out.Add("[$section]"); $out.Add("$key=$value") }
    } else {
      $out.Add("$key=$value")
    }
  }
  return ($out -join "`r`n")
}

$changes = @()

# ---- 1. GameUserSettings: resolution, borderless, vsync -------------------------
$gusPath = Join-Path $CfgDir 'GameUserSettings.ini'
$gus = Read-Text $gusPath
if ($gus.Length -eq 0) { $gus = "[/Script/BS_GodFile.MelodiaGameUserSettings]`r`n" }
$gus = Set-IniKey $gus 'ResolutionSizeX' "$TargetWidth" '[/Script/BS_GodFile.MelodiaGameUserSettings]'
$gus = Set-IniKey $gus 'ResolutionSizeY' "$TargetHeight" '[/Script/BS_GodFile.MelodiaGameUserSettings]'
$gus = Set-IniKey $gus 'LastUserConfirmedResolutionSizeX' "$TargetWidth" '[/Script/BS_GodFile.MelodiaGameUserSettings]'
$gus = Set-IniKey $gus 'LastUserConfirmedResolutionSizeY' "$TargetHeight" '[/Script/BS_GodFile.MelodiaGameUserSettings]'
$gus = Set-IniKey $gus 'FullscreenMode' '1' '[/Script/BS_GodFile.MelodiaGameUserSettings]'
$gus = Set-IniKey $gus 'LastConfirmedFullscreenMode' '1' '[/Script/BS_GodFile.MelodiaGameUserSettings]'
$gus = Set-IniKey $gus 'PreferredFullscreenMode' '1' '[/Script/BS_GodFile.MelodiaGameUserSettings]'
$gus = Set-IniKey $gus 'bUseVSync' 'True' '[/Script/BS_GodFile.MelodiaGameUserSettings]'
$gus = Set-IniKey $gus 'bUseDynamicResolution' 'False' '[/Script/BS_GodFile.MelodiaGameUserSettings]'
$gus = Set-IniKey $gus 'FrameRateLimit' '0.000000' '[/Script/BS_GodFile.MelodiaGameUserSettings]'
$changes += "GameUserSettings.ini      -> res ${TargetWidth}x${TargetHeight}, FullscreenMode=1 (borderless), bUseVSync=True, FrameRateLimit=0"

# ---- 2. EditorPerProjectUserSettings: standalone launch -------------------------
$epuPath = Join-Path $CfgDir 'EditorPerProjectUserSettings.ini'
$epu = Read-Text $epuPath
if ($epu.Length -eq 0) { $epu = "[/Script/UnrealEd.LevelEditorPlaySettings]`r`n" }
$epu = Set-IniKey $epu 'LastExecutedPlayModeType' 'PlayMode_InNewProcess' '[/Script/UnrealEd.LevelEditorPlaySettings]'
$epu = Set-IniKey $epu 'NewWindowWidth' "$TargetWidth" '[/Script/UnrealEd.LevelEditorPlaySettings]'
$epu = Set-IniKey $epu 'NewWindowHeight' "$TargetHeight" '[/Script/UnrealEd.LevelEditorPlaySettings]'
$changes += "EditorPerProjectUserSettings.ini -> LastExecutedPlayModeType=PlayMode_InNewProcess, NewWindow ${TargetWidth}x${TargetHeight}"

# ---- 3. Engine.ini [SystemSettings]: the 4K internal render ---------------------
$engPath = Join-Path $CfgDir 'Engine.ini'
$eng = Read-Text $engPath
if ($eng.Length -eq 0) { $eng = "" }
$eng = Set-IniKey $eng 'r.ScreenPercentage' "$pct" '[SystemSettings]'
$changes += "Engine.ini [SystemSettings] -> r.ScreenPercentage=$pct  (renders ${TargetWidth}x${TargetHeight})"

Write-Host '=== changes ===' -ForegroundColor Cyan
foreach ($c in $changes) { Write-Host "  $c" }
Write-Host ''

if (-not $Apply) {
  Write-Host 'DRY RUN - nothing written. Re-run with -Apply (editor must be closed).' -ForegroundColor Yellow
  exit 0
}

$editors = @(Get-Process UnrealEditor -ErrorAction SilentlyContinue)
if ($editors.Count -gt 0) {
  Write-Host ("WARNING: UnrealEditor is running (pid {0})." -f (($editors | ForEach-Object { $_.Id }) -join ',')) -ForegroundColor Yellow
  Write-Host 'A running editor rewrites these files on exit and will revert the patch.' -ForegroundColor Yellow
  Write-Host 'Close the editor first, then re-run with -Apply.' -ForegroundColor Yellow
  exit 2
}

foreach ($p in @($gusPath, $epuPath, $engPath)) {
  if (Test-Path $p) {
    Copy-Item $p "$p.bak_$Stamp"
  }
}
Write-Text $gusPath $gus
Write-Text $epuPath $epu
Write-Text $engPath $eng

Write-Host 'APPLIED.' -ForegroundColor Green
Write-Host ("  backups: *.bak_{0}" -f $Stamp)
Write-Host ''
Write-Host 'Next: launch the editor, press Play (it now opens a standalone window),' -ForegroundColor Cyan
Write-Host 'or press the Play dropdown and choose "Standalone Game" explicitly.' -ForegroundColor Cyan
Write-Host ("Fallback if the frame rate dips: console command  r.ScreenPercentage 100") -ForegroundColor DarkGray
