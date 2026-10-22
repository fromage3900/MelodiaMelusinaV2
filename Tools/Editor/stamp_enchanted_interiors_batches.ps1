<#
.SYNOPSIS
    Stamp the Enchanted Interiors pack for UE 5.8, in verified memory-bounded batches.

.DESCRIPTION
    The pack's packages are UE4.26 with no engine-version stamp, so UE5 loads and
    rebuilds every one of them when the registry scans Content/. Stamping them
    (load once, re-save) makes that go away - but a single 273 MB mesh needs
    7.7 GB to build, and the machine's commit limit is 71.8 GB.

    So: small batches, smallest first, with a memory guard between batches, and
    a FRESHNESS CHECK on the receipt before it is believed. A run that dies at
    startup leaves the previous run's receipt in place, and reading that as
    success is how six "successful" batches turned out to be one.

    Finished packages are MOVED back into Content/ (a move, not a copy: the same
    bytes, no second copy on disk).

.EXAMPLE
    .\Tools\Editor\stamp_enchanted_interiors_batches.ps1 -BatchSize 45 -MaxBatches 12
#>
[CmdletBinding()]
param(
    [string]$ScratchRoot = "C:\EnvironmentPortfolio\Staging\ECI_scratch",
    [string]$ProjectRoot = "C:\EnvironmentPortfolio\BS_GodFile",
    [string]$EditorCmd = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
    [string]$Tool = "C:\EnvironmentPortfolio\BS_GodFile\Tools\Editor\upgrade_ue4_assets_in_place.py",
    [int]$BatchSize = 45,
    [int]$MaxBatches = 12,
    [double]$MinHeadroomGB = 5.0,
    [double]$CommitLimitGB = 71.8
)

$ErrorActionPreference = "Continue"
$receipt = Join-Path $ScratchRoot "upgrade_report_b3.json"

function Get-CommitGB {
    try { return [math]::Round((Get-Counter '\Memory\Committed Bytes').CounterSamples[0].CookedValue / 1GB, 1) }
    catch { return 0 }
}

for ($i = 1; $i -le $MaxBatches; $i++) {
    $committed = Get-CommitGB
    $headroom = [math]::Round($CommitLimitGB - $committed, 1)
    Write-Host ("=== batch {0}/{1} (committed {2} GB, headroom {3} GB) ===" -f $i, $MaxBatches, $committed, $headroom)
    if ($headroom -lt $MinHeadroomGB) {
        Write-Host "headroom too low - stopping to protect the editor session"
        break
    }
    $env:ECV_PROJECT_ROOT = $ScratchRoot
    $env:ECV_FOLDER = "/Game/EnchantedInteriors"
    $env:ECV_SKIP_MB = "300"
    $env:ECV_SKIP_DIRS = "Materials"
    $env:ECV_SHARD_MIN = ""
    $env:ECV_SHARD_MAX = ""
    $env:ECV_MAX_FILES = "$BatchSize"
    $env:ECV_OUT = $receipt
    $started = Get-Date
    & $EditorCmd "$ScratchRoot\ECIScratch.uproject" -run=pythonscript -script="$Tool" `
        -unattended -nullrhi -nosplash -nopause -stdout 2>&1 | Out-Null
    if (-not (Test-Path $receipt)) {
        Write-Host "   no receipt - the run died at startup"
        Start-Sleep -Seconds 20
        continue
    }
    $age = ((Get-Date) - (Get-Item $receipt).LastWriteTime).TotalSeconds
    if ($age -gt 120 -or (Get-Item $receipt).LastWriteTime -lt $started) {
        Write-Host ("   receipt is stale ({0}s old) - the run died; not believing it" -f [math]::Round($age))
        Start-Sleep -Seconds 20
        continue
    }
    $j = Get-Content $receipt -Raw | ConvertFrom-Json
    Write-Host ("   processed={0} failed={1} already_stamped={2}" -f $j.summary.processed, $j.summary.failed, $j.already_stamped)
    if ($j.summary.processed -eq 0 -and $j.summary.failed -eq 0) {
        Write-Host "nothing left unstamped in this configuration"
        break
    }
    Start-Sleep -Seconds 15
}

Write-Host ""
Write-Host "=== moving the stamped remainder home ==="
$py = @'
import pathlib, shutil
src = pathlib.Path(r"%SRC%")
dst = pathlib.Path(r"%DST%")
moved = skipped = 0
for p in sorted(src.rglob("*.uasset")):
    try:
        stamped = b"++UE5+Release-5.8" in p.open("rb").read(4096)
    except Exception:
        stamped = False
    if not stamped:
        skipped += 1
        continue
    rel = p.relative_to(src)
    target = dst / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(p), str(target))
    moved += 1
print("  moved %d stamped packages home; %d left staged (unstamped)" % (moved, skipped))
'@
$py = $py.Replace("%SRC%", (Join-Path $ScratchRoot "Content\EnchantedInteriors")).Replace("%DST%", (Join-Path $ProjectRoot "Content\EnchantedInteriors"))
$tmp = Join-Path $env:TEMP "ecv_bringback.py"
Set-Content -Path $tmp -Value $py -Encoding UTF8
python $tmp
