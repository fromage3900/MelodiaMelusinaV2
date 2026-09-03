# Run the MUAL UE source pilot in a closed Unreal commandlet.
# This script never promotes into a BlendSpace or montage; use the guarded
# live-promotion command only after the pilot report and PIE evidence pass.

param(
    [string]$Fbx = '',
    [string]$Manifest = '',
    [string]$PieReport = ''
)

$ErrorActionPreference = 'Stop'
$UE = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Project = (Resolve-Path (Join-Path $PSScriptRoot '..\BS_GodFile.uproject')).Path
$Script = (Resolve-Path (Join-Path $PSScriptRoot '..\Content\Python\mual_ue_source_pilot.py')).Path
$Report = Join-Path (Split-Path $Project) 'Saved\Audit\melusina_ue_source_pilot.json'

if (-not (Test-Path -LiteralPath $UE)) { throw "UE 5.8 commandlet not found: $UE" }
if (-not (Test-Path -LiteralPath $Project)) { throw "Project not found: $Project" }
if (-not (Test-Path -LiteralPath $Script)) { throw "Pilot script not found: $Script" }
if (Get-Process -Name UnrealEditor -ErrorAction SilentlyContinue) {
    throw 'Close UnrealEditor before running the headless MUAL source pilot; concurrent project mutation is unsafe.'
}

if ($Fbx) { $env:MUAL_PILOT_FBX = $Fbx } else { Remove-Item Env:MUAL_PILOT_FBX -ErrorAction SilentlyContinue }
if ($Manifest) { $env:MUAL_PILOT_MANIFEST = $Manifest } else { Remove-Item Env:MUAL_PILOT_MANIFEST -ErrorAction SilentlyContinue }
if ($PieReport) { $env:MUAL_PIE_SMOKE_REPORT = $PieReport } else { Remove-Item Env:MUAL_PIE_SMOKE_REPORT -ErrorAction SilentlyContinue }

Write-Host 'Running MUAL UE staging import and RTG audit (promotion remains disabled)...'
& $UE $Project `
    '-run=pythonscript' `
    "-script=$Script" `
    '-unattended' '-nop4' '-nosplash' '-stdout' '-FullStdOutLogOutput'

if ($LASTEXITCODE -ne 0) { throw "MUAL UE commandlet failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $Report)) { throw "Pilot did not produce a report: $Report" }
Get-Content -LiteralPath $Report
