<#
.SYNOPSIS
  Stage a viewport capture (or any image) into the live portfolio site's
  editor_capture gallery, then optionally deploy.

.DESCRIPTION
  Blender/UE capture scripts write a dated PNG into
  my-site-clean/generated/assets/editor_capture/. This wrapper lets you also
  drop an already-rendered PNG and have it registered in the manifest the same
  way, so the gallery page lists it. Nothing is committed or pushed here —
  that stays a human step (review the shot, then sync_site_to_github.ps1).

.EXAMPLE
  .\capture_portfolio.ps1 -Image "C:\shots\hero.png" -Caption "Space Cathedral hero still"
  .\capture_portfolio.ps1 -CaptureAll        # register every PNG already in editor_capture/
#>
param(
    [string]$Image   = "",
    [string]$Caption = "Editor capture",
    [switch]$CaptureAll
)

$ErrorActionPreference = "Stop"
$DEST = "C:\EnvironmentPortfolio\my-site-clean\generated\assets\editor_capture"
$MANIFEST = Join-Path $DEST "manifest.json"

New-Item -ItemType Directory -Path $DEST -Force | Out-Null

function Add-Manifest($file, $cap) {
    $rows = @()
    if (Test-Path $MANIFEST) {
        try { $rows = Get-Content $MANIFEST -Raw | ConvertFrom-Json -AsHashtable } catch { $rows = @() }
    }
    $rows = @([ordered]@{
        caption   = $cap
        file      = [System.IO.Path]::GetFileName($file)
        taken_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        source    = "Editor capture (staged locally)"
    }) + $rows
    $rows = $rows | Select-Object -First 20
    $rows | ConvertTo-Json -Depth 4 | Set-Content $MANIFEST -Encoding UTF8
    Write-Host "  [OK] manifest -> $($rows.Count) rows"
}

if ($CaptureAll) {
    Get-ChildItem $DEST -Filter *.png | Where-Object { $_.Name -ne "manifest.json" } | ForEach-Object {
        Add-Manifest $_.FullName $Caption
    }
    Write-Host "  [OK] registered all captures"
} elseif ($Image -and (Test-Path $Image)) {
    $dst = Join-Path $DEST ([System.IO.Path]::GetFileName($Image))
    Copy-Item $Image $dst -Force
    Add-Manifest $dst $Caption
    Write-Host "  [OK] staged $dst"
} else {
    Write-Host "  [usage] -Image <png> -Caption <text>  |  -CaptureAll"
    exit 1
}

Write-Host ""
Write-Host "  Next: review the shot, then run .\deploy\sync_site_to_github.ps1 to publish."
