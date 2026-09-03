# Retake NikkiPriority UE material instance stills → nightshift + site.
param(
  [string]$ProjectRoot = "C:\EnvironmentPortfolio\BS_GodFile",
  [string]$UnrealCmd = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
  [ValidateSet("nikki", "top5", "proof")]
  [string]$Batch = "nikki",
  [string]$Only = "",
  [switch]$SkipWatermark
)

$ErrorActionPreference = "Stop"
$uproject = Join-Path $ProjectRoot "BS_GodFile.uproject"
$runner = Join-Path $ProjectRoot "Saved\Audit\_run_retake_material_stills.py"
$logDir = Join-Path $ProjectRoot "Saved\Logs"
$logPath = Join-Path $logDir "retake_material_stills.log"

if (-not (Test-Path -LiteralPath $uproject)) { throw "Missing uproject: $uproject" }
if (-not (Test-Path -LiteralPath $UnrealCmd)) { throw "UnrealEditor-Cmd not found: $UnrealCmd" }

New-Item -ItemType Directory -Force -Path (Split-Path $runner) | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$argvList = if ($Only) { "['retake_material_stills.py', '--only', '$Only']" } else { "['retake_material_stills.py', '--batch', '$Batch']" }

@"
import sys
from pathlib import Path
root = Path(r'$($ProjectRoot.Replace('\','/'))')
sys.path.insert(0, str(root / 'Content' / 'Python'))
sys.argv = $argvList
import retake_material_stills as m
raise SystemExit(m.main())
"@ | Set-Content -Path $runner -Encoding UTF8

Write-Host "[MIStill] Launching UnrealEditor-Cmd batch=$Batch only=$Only"
$proc = Start-Process -FilePath $UnrealCmd -ArgumentList @(
  $uproject,
  "/Game/EnvSandbox/_Template/L_MaterialPreview_Studio",
  "-ExecutePythonScript=$($runner.Replace('\','/'))",
  "-stdout",
  "-unattended",
  "-nosplash",
  "-AllowCommandletRendering",
  "-DisablePlugins=Monolith",
  "-log=$logPath"
) -PassThru -NoNewWindow -Wait
$code = $proc.ExitCode
Write-Host "[MIStill] Unreal exit=$code log=$logPath"

if (-not $SkipWatermark) {
  Write-Host "[MIStill] Burning fromage_art watermark onto nightshift MI plates"
  python (Join-Path $ProjectRoot "Tools\burn_fromage_watermark.py") `
    --targets nightshift `
    --glob "MI_*.png" `
    --glob "grid_*.png" `
    --inplace `
    --force | Out-Host
}

$audit = Join-Path $ProjectRoot "Saved\Audit\material_stills_retake.json"
if (Test-Path $audit) {
  $j = Get-Content -Raw $audit | ConvertFrom-Json
  Write-Host ("[MIStill] ok_count={0} fail_count={1}" -f $j.ok_count, $j.fail_count)
}

exit $code
