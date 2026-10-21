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
    [int]$TimeoutSec = 600
)

$ErrorActionPreference = "Continue"

$Root    = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$hython  = "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe"
$Gate    = Join-Path $PSScriptRoot "poitou_intheme_gate.py"
$V6Root  = "C:\Users\froma\agent-tools\poitou_houdini"
$Receipt = Join-Path $Root "Saved\Audit\PoitouConvergence_20261020\intheme_gate.json"

if (-not (Test-Path $hython)) { Write-Host "hython not found at $hython"; exit 2 }
if (-not (Test-Path $V6Root))  { Write-Host "v6 source root not found at $V6Root"; exit 2 }

$env:MELODIA_POITOU_V6_ROOT = $V6Root

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
    Write-Host "=== rebuilding the v6 HDA (this OVERWRITES the live v6 binary) ==="
    $builder = Join-Path $V6Root "build_poitou_hda.py"
    $r = Invoke-Isolated $hython @($builder) "poitou_v6_build" $TimeoutSec
    Write-Host $r.output
    if ($r.code -ne 0) { Write-Host "BUILD FAILED (exit $($r.code))"; exit $r.code }
}

Write-Host "=== Poitou in-theme gate (headless) ==="
$r = Invoke-Isolated $hython @($Gate) "poitou_intheme_gate" $TimeoutSec
$r.output -split "`n" | ForEach-Object { if ($_ -match "intheme_gate") { Write-Host $_ } }
if ($r.status -ne "OK") { Write-Host $r.status; exit 124 }
if (Test-Path $Receipt) { Write-Host "receipt: $Receipt" }
Write-Host "GATE EXIT = $($r.code)"
exit $r.code
