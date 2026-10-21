<#
.SYNOPSIS
    Move the upgraded Enchanted Interiors packages back into the live project.

.DESCRIPTION
    The pack was upgraded in a scratch project (C:\EnvironmentPortfolio\Staging\
    ECI_scratch) so the UE5 registry scan would not rebuild 1696 meshes inside the
    owner's live editor session.

    This MOVES (not copies) the packages that the upgrade has already stamped with
    the UE 5.8 engine version, so:
      * the owner's editor will not rebuild them (a stamped package is not loaded
        by the registry scan, an unstamped UE4 one is)
      * C: free space does not double - the same bytes move from the scratch tree
        to the live tree
      * packages the upgrade has not reached yet stay in the scratch tree and
        stay out of Content/

    "Already stamped" is detected by file modification time (the upgrade writes
    the package, the original copy keeps its import time) and, when a JSON report
    exists, by the report's processed list.

.EXAMPLE
    .\Tools\Editor\bring_back_enchanted_interiors.ps1
#>

[CmdletBinding()]
param(
    [string]$ScratchRoot = "C:\EnvironmentPortfolio\Staging\ECI_scratch",
    [string]$ProjectRoot = "C:\EnvironmentPortfolio\BS_GodFile",
    [string]$Report = "C:\EnvironmentPortfolio\Staging\ECI_scratch\upgrade_report.json",
    [datetime]$StampedAfter = [datetime]"2026-10-21 22:55",
    [switch]$IncludeMaterials,
    [switch]$Copy
)

$ErrorActionPreference = "Stop"

$scratchContent = Join-Path $ScratchRoot "Content\EnchantedInteriors"
$destRoot = Join-Path $ProjectRoot "Content\EnchantedInteriors"
if (-not (Test-Path $scratchContent)) { throw "scratch pack not found: $scratchContent" }
New-Item -ItemType Directory -Force -Path $destRoot | Out-Null

# Packages the JSON report knows about (if it is JSON and not the log tail).
$processed = @()
if (Test-Path $Report) {
    $raw = Get-Content $Report -Raw
    if ($raw.TrimStart().StartsWith("{")) {
        try {
            $rep = $raw | ConvertFrom-Json
            if ($rep.processed) { $processed = @($rep.processed | ForEach-Object { $_.package }) }
        } catch { $processed = @() }
    }
}

$moved = 0; $bytes = 0; $kept = 0; $keptBytes = 0

# Precise test: a package the upgrade rewrote carries the UE 5.8 engine-version
# stamp in its package header. A UE4.26 package has an EMPTY engine version,
# which is exactly what makes UE5 load and rebuild it. mtime is not reliable
# here (the originals kept their 2025 import timestamps).
function Test-Stamped([string]$Path) {
    try {
        $fs = [IO.File]::Open($Path, 'Open', 'Read', 'ReadWrite')
        $buf = New-Object byte[] 4096
        $read = $fs.Read($buf, 0, 4096)
        $fs.Close()
        $txt = [Text.Encoding]::ASCII.GetString($buf, 0, $read)
        return ($txt -match '\+\+UE5\+Release-5\.8')
    } catch { return $false }
}

foreach ($f in Get-ChildItem $scratchContent -Recurse -File) {
    $rel = $f.FullName.Substring($scratchContent.Length + 1)
    $isMaterial = $rel -like "Materials\*"
    $stamped = (Test-Stamped $f.FullName)
    if ($processed.Count -gt 0 -and -not $isMaterial) {
        $stamped = $stamped -or ($processed -contains ("/Game/EnchantedInteriors/" + ($rel -replace '\\', '/')))
    }
    if (-not $stamped -and -not ($IncludeMaterials -and $isMaterial)) {
        $kept++; $keptBytes += $f.Length
        continue
    }
    $dst = Join-Path $destRoot $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    try {
        if ($Copy) { Copy-Item $f.FullName $dst -Force } else { Move-Item $f.FullName $dst -Force }
        $moved++; $bytes += $f.Length
    } catch {
        # the upgrade commandlet may hold the file it is currently writing - leave it
        $kept++; $keptBytes += $f.Length
    }
}

Write-Host ("moved back : {0} files, {1} MB" -f $moved, [math]::Round($bytes / 1MB, 1))
Write-Host ("left staged: {0} files, {1} MB" -f $kept, [math]::Round($keptBytes / 1MB, 1))
Write-Host ("live pack  : {0} files" -f (Get-ChildItem $destRoot -Recurse -File).Count)
Write-Host ("C: free    : {0} GB" -f [math]::Round((Get-PSDrive C).Free / 1GB, 1))
