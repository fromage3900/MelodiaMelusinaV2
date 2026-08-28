<#
.SYNOPSIS
    Downloads OPTIONAL public reference repositories for Starskiff research.

.DESCRIPTION
    These repositories are not Melodia dependencies. They are cloned into a local
    _ExternalReference folder so their implementation can be studied without
    polluting Plugins/ or Content/.

    - Jay2645/BuoyancySystem: MIT, UE4-era buoyancy/boat reference.
    - MrRobinOfficial/Unreal-NebulousVehicle: MIT, WIP Chaos Vehicle reference.

    Do not copy third-party code into Melodia without preserving required license
    notices/attribution. Do not commit _ExternalReference.
#>

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ExternalRoot = Join-Path $RepoRoot "_ExternalReference"

New-Item -ItemType Directory -Force -Path $ExternalRoot | Out-Null

$references = @(
    @{
        Name = "BuoyancySystem"
        Url  = "https://github.com/Jay2645/BuoyancySystem.git"
    },
    @{
        Name = "Unreal-NebulousVehicle"
        Url  = "https://github.com/MrRobinOfficial/Unreal-NebulousVehicle.git"
    }
)

foreach ($reference in $references) {
    $destination = Join-Path $ExternalRoot $reference.Name

    if (Test-Path $destination) {
        Write-Host "[skip] $($reference.Name) already exists at $destination"
        continue
    }

    Write-Host "[clone] $($reference.Url)"
    git clone --depth 1 $reference.Url $destination
}

Write-Host ""
Write-Host "Reference repositories are in: $ExternalRoot"
Write-Host "Study them; do not enable them as Melodia plugins tonight."
Write-Host "Epic BP_BuoyancyExample is already inside Engine > Plugins > Water Content > Blueprints."
