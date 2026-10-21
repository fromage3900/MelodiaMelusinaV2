<#
.SYNOPSIS
    Final closeout for the Enchanted Interiors pack: bring it home, version it, relaunch.

.DESCRIPTION
    Runs after the scratch-project upgrade has stamped the pack for UE 5.8:
      1. moves every stamped package back into Content/EnchantedInteriors (a move,
         not a copy, so C: free space does not double)
      2. adds the pack to Perforce in its own changelist and submits it (Perforce is
         the owner of bulk binary in this project; git ignores Content/*)
      3. relaunches the editor on the live P0 level with revision control disabled

.EXAMPLE
    .\Tools\Editor\closeout_enchanted_interiors_pack.ps1
#>

[CmdletBinding()]
param(
    [string]$ProjectRoot = "C:\EnvironmentPortfolio\BS_GodFile",
    [string]$ScratchRoot = "C:\EnvironmentPortfolio\Staging\ECI_scratch",
    [string]$HoldRoot = "C:\EnvironmentPortfolio\Staging\ECI_hold",
    [string]$Level = "/Game/EnvSandbox/Poitou/L_Poitou_v2",
    [switch]$SkipP4,
    [switch]$SkipRelaunch
)

$ErrorActionPreference = "Stop"

Write-Host "=== 1/4 bring the stamped pack back ==="
& "$ProjectRoot\Tools\Editor\bring_back_enchanted_interiors.ps1" -ScratchRoot $ScratchRoot -ProjectRoot $ProjectRoot -IncludeMaterials

$pack = Join-Path $ProjectRoot "Content\EnchantedInteriors"
$files = Get-ChildItem $pack -Recurse -File -ErrorAction SilentlyContinue
Write-Host ("pack in Content/: {0} files, {1} MB" -f $files.Count,
    [math]::Round((($files | Measure-Object Length -Sum).Sum / 1MB), 1))

if (-not $SkipP4) {
    Write-Host ""
    Write-Host "=== 2/4 add the pack to Perforce ==="
    $desc = "Melodia: Enchanted Interiors (Kitbash3D, UE4.26+) brought in and converted. " +
            "80 material instances authored on M_Master_Toon_Universal at the pack's own " +
            "material paths (basecolor->Albedo, normal->NormalMap, arm->ORM, emissive->EmissiveColor, " +
            "opacity->Opacity), so all meshes resolve their slots with no mesh re-save. " +
            "Packages stamped for UE 5.8 so the registry scan no longer loads and rebuilds them. " +
            "The two 7.7 GB Necromancer's Lair niche meshes and the roof stay out of Content/ " +
            "until the Windows pagefile is raised."
    $spec = (p4 --field "Description=$desc" change -o) | p4 change -i
    if ($spec -match 'Change (\d+) created') {
        $cl = $matches[1]
        Write-Host ("changelist {0} created" -f $cl)
        p4 add -c $cl "//Melodia/main/Content/EnchantedInteriors/..." 2>&1 | Select-Object -Last 2
        $opened = (p4 opened -c $cl 2>&1 | Where-Object { $_ -match '^//' } | Measure-Object).Count
        Write-Host ("opened for add: {0} files" -f $opened)
        if ($opened -gt 0) {
            p4 submit -c $cl 2>&1 | Select-Object -Last 3
        }
    } else {
        Write-Host ("could not create a changelist: {0}" -f $spec)
    }
}

if (-not $SkipRelaunch) {
    Write-Host ""
    Write-Host "=== 4/4 relaunch the editor on $Level ==="
    $ue = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
    Start-Process -FilePath $ue -ArgumentList "$ProjectRoot\BS_GodFile.uproject", $Level
    Write-Host "editor launch issued"
}

Write-Host ""
Write-Host "=== remaining staged outside Content/ (need the pagefile) ==="
if (Test-Path $HoldRoot) {
    Get-ChildItem $HoldRoot -Recurse -File | ForEach-Object {
        Write-Host ("   {0}  ({1} MB)" -f $_.Name, [math]::Round($_.Length / 1MB, 1)) }
}
$leftover = Join-Path $ScratchRoot "Content\EnchantedInteriors"
if (Test-Path $leftover) {
    $left = Get-ChildItem $leftover -Recurse -File
    Write-Host ("   plus {0} files still in the scratch project ({1} MB)" -f $left.Count,
        [math]::Round((($left | Measure-Object Length -Sum).Sum / 1MB), 1))
}
