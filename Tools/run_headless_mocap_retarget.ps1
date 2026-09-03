# Headless retarget: A_Src_* -> A_Mocap_* via RTG_Mocap_to_Melusina
# Close the Unreal editor first — Slate modals break interactive batch retarget.

$ErrorActionPreference = 'Stop'
$UE = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$Proj = 'C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject'
$Script = 'G:/EnvironmentPortfolio/BS_GodFile/Content/Python/headless_retarget_mocap.py'

if (-not (Test-Path $UE)) { throw "UE 5.8 Cmd not found: $UE" }
if (-not (Test-Path $Proj)) { throw "Missing project: $Proj" }

Write-Host "Retargeting mocap (editor must be CLOSED)..."
& $UE $Proj `
  "-run=pythonscript" `
  "-script=$Script" `
  -unattended -nop4 -nosplash

$Report = 'C:\EnvironmentPortfolio\BS_GodFile\Saved\Melodia\retarget_report.json'
if (Test-Path $Report) {
  Write-Host "Report: $Report"
  Get-Content $Report -TotalCount 40
} else {
  Write-Warning "No retarget_report.json yet — check Unreal log."
}
