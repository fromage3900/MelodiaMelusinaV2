param(
    [ValidateSet("MelodiaBuild", "ValidateContracts", "CookPackage", "Gauntlet", "PublishArtifact", "ManifestOnly")]
    [string]$Target = "MelodiaBuild",
    [string]$ProjectFile = (Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) "BS_GodFile.uproject"),
    [string]$UATBat = "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat",
    [string]$ArchiveDir = (Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) "Products\Builds\BuildGraph"),
    [bool]$CreateHordeArtifact = $false,
    [switch]$Resume
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent | Split-Path -Parent
$graph = Join-Path $root "BuildGraph\MelodiaBuildGraph.xml"

# UE 5.8's AutomationTool singleton is controlled by this environment switch,
# not by a -NoMutex command-line flag. It must be inherited by nested UAT nodes.
$env:uebp_UATMutexNoWait = "1"

if (-not (Test-Path -LiteralPath $graph)) { throw "BuildGraph script missing: $graph" }
if (-not (Test-Path -LiteralPath $ProjectFile)) { throw "Project file missing: $ProjectFile" }
if (-not (Test-Path -LiteralPath $UATBat)) { throw "RunUAT missing: $UATBat" }

$resumeArgs = @()
if ($Resume) { $resumeArgs += "-Resume" }

& $UATBat BuildGraph `
    -NoMutex `
    -Script="$graph" `
    -Target="$Target" `
    -Set:ProjectFile="$ProjectFile" `
    -Set:ProjectRoot="$root" `
    -Set:UATBat="$UATBat" `
    -Set:ArchiveDir="$ArchiveDir" `
    -Set:CreateHordeArtifact="$($CreateHordeArtifact.ToString().ToLowerInvariant())" `
    @resumeArgs

if ($LASTEXITCODE -ne 0) {
    throw "BuildGraph failed with exit code $LASTEXITCODE"
}
