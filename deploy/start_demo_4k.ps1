<#
.SYNOPSIS
  Launch the Melodia demo as a standalone game window with a 4K internal render.

.DESCRIPTION
  One command for the demo. Starts the standalone game (not PIE-in-viewport, which
  is pinned by the Monolith start_pie action) in a borderless window sized to the
  panel, with the scene rendered internally at 3840x2160 and vsync on.

  Resolution mapping (per-axis scale, clamped 100-200):
    2560x1440 panel -> 150% -> renders 3840x2160
    1920x1080 panel -> 200% -> renders 3840x2160
    3840x2160 panel -> 100% -> renders 3840x2160

  Frame rate fallback if the GPU cannot hold the frame: in the game console
  (Shift+`) run   r.ScreenPercentage 100

  NOTE: this starts a second Unreal process. Do not run it while the editor is
  open on this project unless you intend to - one editor at a time.

.PARAMETER DryRun
  Print the launch command and exit without starting anything.

.PARAMETER Width
  Internal render width. Default 3840.

.PARAMETER Height
  Internal render height. Default 2160.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File deploy/start_demo_4k.ps1 -DryRun
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File deploy/start_demo_4k.ps1
#>
[CmdletBinding()]
param(
  [switch] $DryRun,
  [switch] $ShowStats,
  [int] $Width = 3840,
  [int] $Height = 2160
)

$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
$Proj = Get-ChildItem $Repo -Filter '*.uproject' | Select-Object -First 1
if (-not $Proj) { throw "no .uproject found in $Repo" }

$Editor = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
if (-not (Test-Path $Editor)) {
  $Editor = (Get-ChildItem 'C:\Program Files\Epic Games' -Recurse -Filter 'UnrealEditor.exe' -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match 'UE_5\.8.*Win64' } | Select-Object -First 1).FullName
}
if (-not $Editor -or -not (Test-Path $Editor)) { throw 'UnrealEditor.exe not found' }

Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::AllScreens | Where-Object { $_.Primary } | Select-Object -First 1
if (-not $screen) { $screen = [System.Windows.Forms.Screen]::PrimaryScreen }
$panelW = $screen.Bounds.Width
$panelH = $screen.Bounds.Height

$pct = [math]::Round([math]::Min($Width / $panelW, $Height / $panelH) * 100.0)
$pct = [math]::Max(100, [math]::Min(200, $pct))

$execCmds = "r.ScreenPercentage $pct"
if ($ShowStats) { $execCmds += ",stat unit" }
$args = @(
  "`"$($Proj.FullName)`"",
  '-game',
  "-ResX=$panelW",
  "-ResY=$panelH",
  "-ExecCmds=`"$execCmds`"",
  '-log'
)

Write-Host ''
Write-Host '=== Melodia standalone demo launch ===' -ForegroundColor Cyan
Write-Host ("  project   : {0}" -f $Proj.Name)
Write-Host ("  editor    : {0}" -f $Editor)
Write-Host ("  panel     : {0}x{1}" -f $panelW, $panelH)
Write-Host ("  render    : {0}x{1}  (r.ScreenPercentage {2})" -f $Width, $Height, $pct)
Write-Host ("  cmd       : {0} {1}" -f $Editor, ($args -join ' '))
Write-Host ''

if ($DryRun) {
  Write-Host 'DRY RUN - nothing launched.' -ForegroundColor Yellow
  exit 0
}

$running = @(Get-Process UnrealEditor -ErrorAction SilentlyContinue)
if ($running.Count -gt 0) {
  Write-Host ("NOTE: an editor is already running (pid {0}). Starting a second Unreal" -f (($running | ForEach-Object { $_.Id }) -join ',')) -ForegroundColor Yellow
  Write-Host 'process is intentional here (standalone game), but close it first if you' -ForegroundColor Yellow
  Write-Host 'want to avoid two Unreal processes touching the same project.' -ForegroundColor Yellow
}

$p = Start-Process -FilePath $Editor -ArgumentList $args -PassThru
Write-Host ("LAUNCHED pid {0}" -f $p.Id) -ForegroundColor Green
Write-Host 'Log: Saved/Logs/BS_GodFile.log   (search for "SetRes" / "Window" to confirm the resolution)' -ForegroundColor DarkGray
Write-Host ("Fallback if frames dip: console (Shift+`) -> r.ScreenPercentage 100") -ForegroundColor DarkGray
