# Import Cascadeur animation FBX files directly onto SK_Melusina_Skeleton.
# Run with the Unreal Editor closed. This wrapper never performs retargeting.

param(
    [switch]$ReplaceExisting
)

$ErrorActionPreference = 'Stop'

$UE = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Project = (Resolve-Path (Join-Path $PSScriptRoot '..\BS_GodFile.uproject')).Path
$Script = (Resolve-Path (Join-Path $PSScriptRoot '..\Content\Python\import_cascadeur_anim.py')).Path
$Report = Join-Path (Split-Path $Project) 'Saved\Melodia\cascadeur_import_report.json'

if (-not (Test-Path -LiteralPath $UE)) { throw "UE 5.8 commandlet not found: $UE" }
if (-not (Test-Path -LiteralPath $Project)) { throw "Project not found: $Project" }
if (-not (Test-Path -LiteralPath $Script)) { throw "Importer not found: $Script" }

if (Get-Process -Name UnrealEditor -ErrorAction SilentlyContinue) {
    throw 'Close UnrealEditor before running the headless Cascadeur import.'
}

if ($ReplaceExisting) {
    $env:CASCADEUR_REPLACE_EXISTING = '1'
} else {
    Remove-Item Env:CASCADEUR_REPLACE_EXISTING -ErrorAction SilentlyContinue
}

Write-Host "Importing Cascadeur animations from the project inbox..."
& $UE $Project `
    '-run=pythonscript' `
    "-script=$Script" `
    '-unattended' '-nop4' '-nosplash' '-stdout' '-FullStdOutLogOutput'

if ($LASTEXITCODE -ne 0) {
    throw "Unreal commandlet failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path -LiteralPath $Report)) {
    throw "Importer did not produce a report: $Report"
}

Get-Content -LiteralPath $Report
