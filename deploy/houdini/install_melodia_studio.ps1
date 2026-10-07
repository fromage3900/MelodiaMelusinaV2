<#
.SYNOPSIS
    Activate the repo-backed Melodia Houdini Studio package for the current user.

.DESCRIPTION
    Gate 0A installer. It resolves the repository root from this script's own
    location, finds hython, asks Houdini where the user preference directory is,
    and writes ONE thin pointer file:

        <houdini user pref>/packages/melodia_studio_local.json
        { "package_path": "<repo>/deploy/houdini/packages" }

    The committed package definition (deploy/houdini/packages/melodia_studio.json)
    stays the single source of truth for HOUDINI_PATH, desktops, shelves and the
    MELODIA_* environment variables. Nothing machine-local is ever committed, and
    no committed file contains a drive letter or user name.

    This script never edits houdini.env and never touches the repo.

.PARAMETER CheckOnly
    Report what would be written without writing anything.

.PARAMETER Remove
    Delete the pointer this installer wrote, cleanly deactivating the package.
    The pointer is only removed if its content still points at this repository's
    package directory - a pointer written by something else is left untouched.
    houdini.env, factory desktops and the repository are never modified.

.PARAMETER Verify
    Run deploy/houdini/verify_melodia_studio.py through hython after installing.

.EXAMPLE
    .\deploy\houdini\install_melodia_studio.ps1 -Verify

.EXAMPLE
    .\deploy\houdini\install_melodia_studio.ps1 -Remove
#>
[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$Remove,
    [switch]$Verify
)

$ErrorActionPreference = 'Stop'

$PointerName = 'melodia_studio_local.json'
$HoudiniPackagesDirName = 'packages'

function Write-Step([string]$Message) { Write-Host "  $Message" -ForegroundColor DarkGray }
function Write-Ok([string]$Message)   { Write-Host "  OK   $Message" -ForegroundColor Green }
function Write-Warn2([string]$Message){ Write-Host "  WARN $Message" -ForegroundColor Yellow }

# --- 1. Repository root, derived from this file -----------------------------
# $PSScriptRoot = <repo>/deploy/houdini
$DeployDir = Split-Path -Parent $PSScriptRoot
$RepoRoot  = Split-Path -Parent $DeployDir
$RepoRoot  = [System.IO.Path]::GetFullPath($RepoRoot)

$CommittedPackage = Join-Path $RepoRoot 'deploy\houdini\packages\melodia_studio.json'
$PackageRoot      = Join-Path $RepoRoot 'deploy\houdini\melodia_studio'

if (-not (Test-Path $CommittedPackage)) {
    throw "Committed package definition not found: $CommittedPackage"
}
if (-not (Test-Path $PackageRoot)) {
    throw "Package content root not found: $PackageRoot"
}
if (-not (Test-Path (Join-Path $RepoRoot 'Content'))) {
    throw "$RepoRoot does not look like the Melodia repository (no Content directory)."
}

Write-Host "Melodia Houdini Studio installer" -ForegroundColor Cyan
Write-Step "repo root       : $RepoRoot"
Write-Step "committed pkg   : $CommittedPackage"

# --- 2. Locate hython without hardcoding a drive or version -----------------
function Find-Hython {
    if ($env:HFS) {
        $candidate = Join-Path $env:HFS 'bin\hython.exe'
        if (Test-Path $candidate) { return $candidate }
    }
    $roots = @()
    if ($env:ProgramFiles)      { $roots += $env:ProgramFiles }
    if (${env:ProgramFiles(x86)}) { $roots += ${env:ProgramFiles(x86)} }
    foreach ($root in $roots) {
        foreach ($vendor in @('Side Effects Software', 'SideFX', 'Side Effects Software Ltd')) {
            $vendorDir = Join-Path $root $vendor
            if (-not (Test-Path $vendorDir)) { continue }
            $found = Get-ChildItem -Path $vendorDir -Directory -Filter 'Houdini *' -ErrorAction SilentlyContinue |
                     Sort-Object Name -Descending
            foreach ($dir in $found) {
                $candidate = Join-Path $dir.FullName 'bin\hython.exe'
                if (Test-Path $candidate) { return $candidate }
            }
        }
    }
    return $null
}

$Hython = Find-Hython
if (-not $Hython) {
    throw "hython.exe not found. Set `$env:HFS to a Houdini install, or run from a shell where Houdini is on PATH."
}
Write-Step "hython          : $Hython"

# --- 3. Ask Houdini for the user preference directory -----------------------
# hython writes plugin/Arnold banners to stdout, so capture through a file.
$TempFile = [System.IO.Path]::GetTempFileName()
try {
    $env:MELODIA_HOME_CAPTURE = $TempFile
    & $Hython -c "import hou,os; open(os.environ['MELODIA_HOME_CAPTURE'],'w',encoding='utf-8').write(hou.homeHoudiniDirectory())" 2>$null | Out-Null
    $HomeHoudini = ''
    if (Test-Path $TempFile) { $HomeHoudini = [System.IO.File]::ReadAllText($TempFile).Trim() }
} finally {
    Remove-Item Env:MELODIA_HOME_CAPTURE -ErrorAction SilentlyContinue
    Remove-Item $TempFile -ErrorAction SilentlyContinue
}
if (-not $HomeHoudini) { throw "hou.homeHoudiniDirectory() returned nothing." }
$HomeHoudini = $HomeHoudini -replace '/', [System.IO.Path]::DirectorySeparatorChar
if (-not (Test-Path $HomeHoudini)) { throw "Houdini user preference directory does not exist: $HomeHoudini" }
Write-Step "user pref dir   : $HomeHoudini"

$PackagesDir = Join-Path $HomeHoudini $HoudiniPackagesDirName
$PointerPath = Join-Path $PackagesDir $PointerName

# --- 4. Build the thin pointer ---------------------------------------------
# The committed definition lives at <repo>/deploy/houdini/packages/melodia_studio.json
$PackagesPath = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot 'deploy\houdini\packages'))
if (-not (Test-Path (Join-Path $PackagesPath 'melodia_studio.json'))) {
    throw "Package definition not found under $PackagesPath"
}
$PackagesPathJson = ($PackagesPath -replace '\\', '/')
$PointerJson  = ([ordered]@{ package_path = $PackagesPathJson } | ConvertTo-Json) + "`n"

$Existed = Test-Path $PointerPath
$Current  = $null
if ($Existed) { $Current = [System.IO.File]::ReadAllText($PointerPath) }

$UpToDate = $Existed -and ($Current.TrimEnd() -ieq $PointerJson.TrimEnd())

Write-Step "pointer target  : $PointerPath"

if ($Remove) {
    # Safe undo: only ever delete a pointer this installer would have written.
    if ($CheckOnly) { throw "-Remove cannot be combined with -CheckOnly." }
    if (-not $Existed) {
        Write-Ok "nothing to remove - no pointer present"
    } else {
        $Owned = $false
        try {
            $Parsed = $Current | ConvertFrom-Json
            if ($Parsed -and ($Parsed.PSObject.Properties.Name -contains 'package_path')) {
                $Target = ([string]$Parsed.package_path) -replace '/', [System.IO.Path]::DirectorySeparatorChar
                $Owned  = ([System.IO.Path]::GetFullPath($Target) -ieq $PackagesPath)
            }
        } catch { $Owned = $false }
        if ($Owned) {
            Remove-Item -LiteralPath $PointerPath -Force
            Write-Ok "pointer removed - Melodia package deactivated"
        } else {
            Write-Warn2 "pointer present but not written by this installer - left untouched"
        }
    }
}
elseif ($UpToDate) {
    Write-Ok "pointer already up to date - nothing written"
} else {
    if ($CheckOnly) {
        Write-Warn2 "CheckOnly - would write pointer pointing at: $PackagesPathJson"
    } else {
        if (-not (Test-Path $PackagesDir)) {
            New-Item -ItemType Directory -Force -Path $PackagesDir | Out-Null
            Write-Step "created packages directory"
        }
        [System.IO.File]::WriteAllText($PointerPath, $PointerJson, (New-Object System.Text.UTF8Encoding($false)))
        if ($Existed) { Write-Ok "pointer rewritten (previous version replaced)" }
        else          { Write-Ok "pointer created" }
    }
}

# --- 5. Report neighbouring package files, never modify them ----------------
$HoudiniEnv = Join-Path $HomeHoudini 'houdini.env'
if (Test-Path $HoudiniEnv) { Write-Step "houdini.env left untouched: $HoudiniEnv" }

$Foreign = Get-ChildItem -Path $PackagesDir -Filter '*.json' -ErrorAction SilentlyContinue |
           Where-Object { $_.Name -ne $PointerName -and $_.Name -like '*melodia*' }
foreach ($f in $Foreign) {
    Write-Warn2 "pre-existing Melodia package file also present: $($f.Name) (left as-is)"
}

# --- 6. Optional verification ----------------------------------------------
if ($Verify) {
    if ($CheckOnly) { throw "-Verify cannot be combined with -CheckOnly (nothing was installed)." }
    if ($Remove)    { throw "-Verify cannot be combined with -Remove (the package was deactivated)." }
    $Verifier = Join-Path $RepoRoot 'deploy\houdini\verify_melodia_studio.py'
    if (-not (Test-Path $Verifier)) { throw "Verifier not found: $Verifier" }
    Write-Host "running verification..." -ForegroundColor Cyan
    & $Hython $Verifier
    if ($LASTEXITCODE -ne 0) { throw "Verification failed with exit code $LASTEXITCODE." }
} else {
    Write-Host ""
    Write-Host "Next: .\deploy\houdini\install_melodia_studio.ps1 -Verify" -ForegroundColor Yellow
}
