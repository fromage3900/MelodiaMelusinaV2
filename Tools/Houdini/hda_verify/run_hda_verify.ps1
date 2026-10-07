<#
.SYNOPSIS
  run_hda_verify.ps1 - one command for the whole HDA verification lane.

.DESCRIPTION
  Runs the gates in order and lands both receipts in one run folder:
    Gate 0  hda_audit.py    offline inventory (existence, stubs, mirrors, sha256)
    Gate 2  hda_verify.py   hython install + cook + geometry expectations

  Gates are independent scripts that share only hda_registry.v1.json, so a gate
  can be run on its own without this wrapper.

  Pass/fail is read from the receipt each gate writes (hda_inventory.json /
  hda_verify_report.json -> "overall"), not from a process exit code: this
  PowerShell build never populates Process.ExitCode for Start-Process children,
  and the receipt is the evidence we would trust anyway. A gate that produces no
  receipt counts as failed.

.EXAMPLE
  .\Tools\Houdini\hda_verify\run_hda_verify.ps1
  .\Tools\Houdini\hda_verify\run_hda_verify.ps1 -Gate 0
  .\Tools\Houdini\hda_verify\run_hda_verify.ps1 -Only melodia_crystal_cathedral
#>
[CmdletBinding()]
param(
    [ValidateSet(0, 2, "all")]
    [string]$Gate = "all",

    [string]$Hython = "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe",

    # Shared run id so both receipts land in the same folder.
    [string]$RunId = (Get-Date -Format "yyyyMMdd_HHmmss"),

    [string[]]$Only = @(),

    [int]$TimeoutSec = 900,

    # Where receipts land; kept under Saved/Audit like every other gate receipt.
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
# hda_verify/ -> Houdini/ -> Tools/ -> repo root
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
if (-not $OutDir) { $OutDir = Join-Path $root "Saved\Audit\hda_verify\$RunId" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if (-not (Test-Path $Hython)) {
    Write-Host "[hda_verify] hython not found at: $Hython" -ForegroundColor Red
    Write-Host "[hda_verify] Gate 0 still runs with any python; Gate 2 needs hython."
    $Hython = $null
}

function Read-Overall {
    param([string]$Receipt)
    if (-not (Test-Path $Receipt)) { return $null }
    try { return (Get-Content $Receipt -Raw | ConvertFrom-Json).overall }
    catch { return $null }
}

function Invoke-Gate {
    # NOTE: $GateArgs, not $Args - $args is a PowerShell automatic variable.
    param([string]$Label, [string]$Script, [string[]]$GateArgs, [string]$Receipt)

    Write-Host "[hda_verify] --- $Label ---" -ForegroundColor Cyan
    $log = Join-Path $OutDir "stdout_$Label.txt"

    if ($Hython) {
        $exe = $Hython
    } else {
        $exe = (Get-Command python -ErrorAction SilentlyContinue).Source
        if (-not $exe) { throw "no interpreter: hython and python both unavailable" }
    }

    $psi = Start-Process -FilePath $exe -ArgumentList (@($Script) + $GateArgs) `
        -NoNewWindow -PassThru -RedirectStandardOutput $log -RedirectStandardError "$log.err"

    # WaitForExit() takes MILLISECONDS.
    if (-not $psi.WaitForExit($TimeoutSec * 1000)) {
        $psi.Kill()
        Write-Host "[hda_verify] $Label TIMED OUT after ${TimeoutSec}s" -ForegroundColor Red
        return 124
    }

    # Echo the gate output, dropping Houdini's startup banner ("00:00:00  359MB | ...").
    Get-Content $log -ErrorAction SilentlyContinue |
        Where-Object { $_ -notmatch '^\d{2}:\d{2}:\d{2}\s' } |
        ForEach-Object { Write-Host $_ }

    # Judge from the evidence file; exit codes are unreliable here (see .DESCRIPTION).
    $overall = Read-Overall -Receipt $Receipt
    if ($null -eq $overall) {
        Get-Content "$log.err" -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
        Write-Host "[hda_verify] $Label produced NO RECEIPT -> treating as FAILED" -ForegroundColor Red
        return 1
    }
    if ($overall -eq "FAIL") { return 1 }
    if ($overall -eq "WARN") {
        Write-Host "[hda_verify] $Label finished with warnings (receipt: $overall)" -ForegroundColor Yellow
    }
    return 0
}

$failed = 0
$receipt0 = Join-Path $OutDir "hda_inventory.json"
$receipt2 = Join-Path $OutDir "hda_verify_report.json"

if ($Gate -in @("0", "all")) {
    $code = Invoke-Gate -Label "gate0_audit" `
        -Script (Join-Path $PSScriptRoot "hda_audit.py") `
        -GateArgs @("--out-dir", $OutDir) -Receipt $receipt0
    if ($code -ne 0) { $failed = 1; Write-Host "[hda_verify] Gate 0 FAILED (code $code)" -ForegroundColor Red }
    else { Write-Host "[hda_verify] Gate 0 PASS" -ForegroundColor Green }
}

if ($Gate -in @("2", "all")) {
    if (-not $Hython) {
        Write-Host "[hda_verify] Gate 2 SKIPPED - no hython" -ForegroundColor Yellow
        $failed = 1
    } else {
        $g2 = @("--out-dir", $OutDir)
        foreach ($id in $Only) { $g2 += @("--only", $id) }
        $code = Invoke-Gate -Label "gate2_cook" `
            -Script (Join-Path $PSScriptRoot "hda_verify.py") -GateArgs $g2 -Receipt $receipt2
        if ($code -ne 0) { $failed = 1; Write-Host "[hda_verify] Gate 2 FAILED (code $code)" -ForegroundColor Red }
        else { Write-Host "[hda_verify] Gate 2 PASS" -ForegroundColor Green }
    }
}

Write-Host "[hda_verify] receipts: $OutDir"
exit $failed
