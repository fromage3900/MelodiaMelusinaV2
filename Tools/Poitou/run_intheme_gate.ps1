# Wedge-proof runner for the Poitou in-theme gate.
#
#   .\Tools\Poitou\run_intheme_gate.ps1                 # gate only
#   .\Tools\Poitou\run_intheme_gate.ps1 -Build          # rebuild the v6 HDA first
#   .\Tools\Poitou\run_intheme_gate.ps1 -TimeoutSec 900
#
# Why the isolation: on 2026-08-28 a bare "hython --version" in a shared
# console hung for over 60 seconds and wedged the entire shell session. Every
# hython invocation in this repo now goes through Start-Process + a hard
# timeout + a forced kill, so a license-server hang can never take the console
# down again. The same pattern is used by
# Tools/Houdini/sea_above_reef/probe_hython_license.ps1 and
# Tools/Houdini/melodyslime_deconstructed/run_deconstructed.ps1.

[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$Measure,
    [int]$TimeoutSec = 600
)

$ErrorActionPreference = "Continue"

$Root    = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$hython  = "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe"
$ue      = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$Gate    = Join-Path $PSScriptRoot "poitou_intheme_gate.py"
$Builder = Join-Path $PSScriptRoot "build_poitou_hda.py"
$MeasureScript = Join-Path $Root "Tools\Editor\poitou_intheme_assets.py"
# The REPO is the build path.  The live v6 sources used to live in an
# external folder (C:\Users\froma\agent-tools\poitou_houdini) and the repo
# held a stale v5 builder, so building from the repo silently regressed the
# level.  2026-10-21: the repo is the single source of truth.
$V6Root  = $PSScriptRoot
$Receipt = Join-Path $Root "Saved\Audit\PoitouConvergence_20261020\intheme_gate.json"

if (-not (Test-Path $hython)) { Write-Host "hython not found at $hython"; exit 2 }
if (-not (Test-Path $V6Root))  { Write-Host "v6 source root not found at $V6Root"; exit 2 }

$env:MELODIA_POITOU_V6_ROOT = $V6Root
$env:MELODIA_POITOU_REPO = $Root

function Invoke-Isolated {
    param([string]$Exe, [string[]]$ArgList, [string]$Tag, [int]$Timeout)
    $out = Join-Path $env:TEMP "$Tag`_out.txt"
    $err = Join-Path $env:TEMP "$Tag`_err.txt"
    Remove-Item $out, $err -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath $Exe -ArgumentList $ArgList `
         -RedirectStandardOutput $out -RedirectStandardError $err `
         -PassThru -WindowStyle Hidden
    if ($p.WaitForExit($Timeout * 1000)) {
        $text = (Get-Content $out -Raw -ErrorAction SilentlyContinue) + `
                (Get-Content $err -Raw -ErrorAction SilentlyContinue)
        return @{ status = "OK"; code = $p.ExitCode; output = $text }
    }
    try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch {}
    return @{ status = "HANG (killed after ${Timeout}s)"; code = 124; output = "" }
}

if ($Build) {
    Write-Host "=== rebuilding the Poitou layout HDA from the repo builder ==="
    $r = Invoke-Isolated $hython @($Builder) "poitou_build" $TimeoutSec
    Write-Host $r.output
    if ($r.code -ne 0) { Write-Host "BUILD FAILED (exit $($r.code))"; exit $r.code }
}

if ($Measure) {
    Write-Host "=== measuring every instanced mesh against its divisor (headless UE) ==="
    $r = Invoke-Isolated $ue @("$Root\BS_GodFile.uproject", "-run=pythonscript",
        "-script=$MeasureScript", "-unattended", "-nopause", "-nosplash", "-nullrhi",
        "-stdout", "-FullStdOutLogOutput") "poitou_measure" ($TimeoutSec * 3)
    $r.output -split "`n" | ForEach-Object { if ($_ -match "intheme_assets") { Write-Host $_ } }
    if ($r.status -ne "OK") { Write-Host $r.status; exit 124 }
}

Write-Host "=== Poitou in-theme gate (headless) ==="
$r = Invoke-Isolated $hython @($Gate) "poitou_intheme_gate" $TimeoutSec
$r.output -split "`n" | ForEach-Object { if ($_ -match "intheme_gate") { Write-Host $_ } }
if ($r.status -ne "OK") { Write-Host $r.status; exit 124 }
if (Test-Path $Receipt) { Write-Host "receipt: $Receipt" }
Write-Host "GATE EXIT = $($r.code)"
exit $r.code
