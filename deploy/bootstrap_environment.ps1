# Bootstrap the documented local development environment.
#
# The default mode is a dry, dependency-aware check. Installation is opt-in:
#   .\deploy\bootstrap_environment.ps1 -CreateVenvs
#   .\deploy\bootstrap_environment.ps1 -InstallWebsiteDependencies
#
# Unreal, Marketplace plugins, Blender, VOICEVOX, and secrets are intentionally
# never installed by this script.
param(
    [string]$WebsiteRoot,
    [switch]$CreateVenvs,
    [switch]$InstallPythonTooling,
    [switch]$InstallQuantumTooling,
    [switch]$InstallWebsiteDependencies,
    [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$website = if ($WebsiteRoot) {
    [IO.Path]::GetFullPath($WebsiteRoot)
} elseif ($env:MELODIA_WEBSITE_ROOT) {
    [IO.Path]::GetFullPath($env:MELODIA_WEBSITE_ROOT)
} else {
    Join-Path (Split-Path -Parent $projectRoot) "my-site-clean"
}

function Invoke-Step {
    param(
        [string]$Label,
        [scriptblock]$Action
    )
    Write-Host "`n==> $Label" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function Find-Python311 {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            & py -3.11 --version *> $null
            if ($LASTEXITCODE -eq 0) { return @("py", "-3.11") }
        } catch {}
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $version = & python --version 2>&1 | Out-String
        if ($version -match "3\.11") { return @("python") }
    }
    throw "Python 3.11 was not found. Install it before creating project environments."
}

function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments = $true)][object[]]$Arguments)
    if ($pythonCommand.Count -eq 1) {
        & $pythonCommand[0] @Arguments
    } else {
        & $pythonCommand[0] $pythonCommand[1] @Arguments
    }
}

if (-not $SkipValidation) {
    Invoke-Step "Validate core paths and tools" {
        & (Join-Path $PSScriptRoot "validate_setup.ps1") -CheckWebsite
    }
}

$pythonCommand = Find-Python311
$venvTargets = @(
    @{
        Name = "UEBlueprintMCP"
        Root = Join-Path $projectRoot "Plugins\UEBlueprintMCP\Python"
        Requirements = "requirements.txt"
    }
)
if ($InstallQuantumTooling) {
    $venvTargets += @{
        Name = "Quantum"
        Root = Join-Path $projectRoot "Content\Python\quantum"
        Requirements = "requirements.txt"
    }
}

if ($CreateVenvs -or $InstallPythonTooling -or $InstallQuantumTooling) {
    foreach ($target in $venvTargets) {
        $venv = Join-Path $target.Root ".venv"
        if (-not (Test-Path $venv)) {
            Invoke-Step "Create $($target.Name) Python 3.11 environment" {
                Invoke-Python "-m" "venv" $venv
            }
        } else {
            Write-Host "  Existing environment: $venv"
        }

        if ($InstallPythonTooling -or ($target.Name -eq "Quantum" -and $InstallQuantumTooling)) {
            $pip = Join-Path $venv "Scripts\python.exe"
            $requirements = Join-Path $target.Root $target.Requirements
            if (-not (Test-Path $requirements)) {
                throw "Requirements file missing: $requirements"
            }
            Invoke-Step "Install $($target.Name) Python requirements" {
                & $pip -m pip install --upgrade pip
                & $pip -m pip install -r $requirements
            }
        }
    }
} else {
    Write-Host "`n==> Python environments" -ForegroundColor Cyan
    Write-Host "  Dry mode: use -CreateVenvs to create local .venv folders."
}

if ($InstallWebsiteDependencies) {
    $package = Join-Path $website "package.json"
    $lock = Join-Path $website "package-lock.json"
    if (-not (Test-Path $package)) {
        throw "Website package.json not found at $website"
    }
    if (-not (Test-Path $lock)) {
        throw "Website package-lock.json is required for npm ci: $lock"
    }
    Invoke-Step "Install website dependencies with npm ci" {
        Push-Location $website
        try {
            & npm ci
        } finally {
            Pop-Location
        }
    }
} else {
    Write-Host "`n==> Website dependencies" -ForegroundColor Cyan
    Write-Host "  Dry mode: use -InstallWebsiteDependencies after choosing the website checkout."
}

Write-Host "`nBootstrap checks complete." -ForegroundColor Green
Write-Host "No Unreal, Marketplace, Blender, VOICEVOX, or secret configuration was installed."
Write-Host "Machine credentials must be supplied outside tracked files; never copy .mcp.json."
