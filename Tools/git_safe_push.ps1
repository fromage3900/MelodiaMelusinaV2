# git_safe_push.ps1 - pre-push guard for metered LFS billing
# Usage: Tools/git_safe_push.ps1 [-LimitMB 512] [-Remote v2] [-Branch main]
# Aborts before pushing if the staged LFS batch is too large.

param(
    [int]$LimitMB = 512,
    [string]$Remote = "origin",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "==> [git_safe_push] LFS batch guard (limit $LimitMB MB)" -ForegroundColor Cyan

if (-not (Test-Path ".git")) {
    Write-Error "Not a git repository (no .git found). Run from BS_GodFile root."
}

# 1. Show what is staged
Write-Host "--- staged changes ---"
git status --short | ForEach-Object { "  $_" }
$stagedCount = (git status --short | Measure-Object -Line).Lines
if ($stagedCount -eq 0) {
    Write-Host "Nothing staged. Pushing committed ref only." -ForegroundColor Yellow
}

# 2. Estimate LFS objects the push would upload (dry-run against remote)
Write-Host "--- LFS objects pending upload (dry-run) ---"
$dry = git lfs push --dry-run $Remote $Branch 2>&1
$pushLines = $dry | Where-Object { $_ -match "^push " }
$totalBytes = 0
foreach ($line in $pushLines) {
    $oid = ($line -split " ")[1]
    $objPath = ".git\lfs\objects\" + $oid.Substring(0,2) + "\" + $oid.Substring(2,2) + "\" + $oid
    if (Test-Path $objPath) {
        $totalBytes += (Get-Item $objPath).Length
    }
}
$totalMB = [Math]::Round($totalBytes / 1MB, 1)
Write-Host "Pending LFS objects: $($pushLines.Count)  (~$totalMB MB)" -ForegroundColor Cyan

if ($totalMB -gt $LimitMB) {
    Write-Host ""
    Write-Error "ABORT: LFS batch is $totalMB MB (> $LimitMB MB limit).`nThis would bill metered storage. Split the work or raise -LimitMB explicitly."
}

# 3. Warn if website/build outputs are staged (unnecessary pushes)
$junk = git status --short | Where-Object { $_ -match "_\w+deploy|DerivedDataCache|Intermediate|Saved/" }
if ($junk) {
    Write-Host "WARNING: possible build/deploy outputs staged:" -ForegroundColor Yellow
    $junk | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    Write-Host "Consider excluding them before pushing."
}

Write-Host "==> [git_safe_push] OK: batch within limit. Proceed with push." -ForegroundColor Green
