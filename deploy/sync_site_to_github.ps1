# Sync the portfolio site to the my-site repo, which GitHub Pages builds and serves.
#
#   .\deploy\sync_site_to_github.ps1
#   .\deploy\sync_site_to_github.ps1 -Message "Add new Space Cathedral hero stills"
#   .\deploy\sync_site_to_github.ps1 -Deploy $false      # stage + diff only, no commit/push
#
# Source of truth is THIS repo's tracked site folders (wix/, components/, projects/, ...).
# The old my-site-clean/ staging copy is gone: it had decayed to 11 stray PNGs while the
# real edits happened in wix/, and it was gitignored, so nothing in it was ever reviewable.
#
# Pages serves fromage3900/my-site with build_type=workflow, so the deploy target is that
# repo's `main` branch and an Action publishes it. There is no gh-pages branch to write to.

param(
    [string]$Message = "Sync site updates",
    [string]$Target  = "C:\EnvironmentPortfolio\_github_deploy",
    [string]$Source  = "C:\EnvironmentPortfolio\my-site-clean",
    [bool]$Deploy    = $true
)

$ErrorActionPreference = "Stop"

# 2026-08-22: SOURCE OF TRUTH is my-site-clean/. That is the repo Pages actually
# serves (it carries the origin remote and is what edits are committed to). The
# old default walked up two parents from this script (BS_GodFile/) and copied
# BS_GodFile/wix -- a STALE copy that diverges from the live site. Three trees
# existed at one point (BS_GodFile/wix, _github_deploy, my-site-clean) and all
# three differed. my-site-clean wins. A drift guard below warns if the other
# two disagree with it, but never blocks a deploy on a warning.
$source = $Source
$dest   = $Target

Write-Host ""
Write-Host "  +----------------------------------------------+"
Write-Host "  |     Melodia Portfolio -- Deploy Pipeline      |"
Write-Host "  +----------------------------------------------+"
Write-Host ""
Write-Host "  Source : $source  (tracked site folders)"
Write-Host "  Target : $dest"
Write-Host "  Commit : $Message"
Write-Host ""

# --- Validate -------------------------------------------------------------
if (-not (Test-Path (Join-Path $source "wix"))) {
    Write-Host "  [FAIL] No wix/ under $source -- wrong source root."
    exit 1
}

if (-not (Test-Path (Join-Path $dest ".git"))) {
    Write-Host "  [FAIL] $dest is not a git clone of the site repo."
    Write-Host ""
    Write-Host "         Create it once with:"
    Write-Host "           git clone https://github.com/fromage3900/my-site.git `"$dest`""
    Write-Host ""
    Write-Host "         An earlier design used a git worktree here. It was left without a"
    Write-Host "         .git file, so every deploy since has silently copied into a dead"
    Write-Host "         directory. A plain clone is what this script now expects."
    exit 1
}

Push-Location $dest
try {
    $remote = (git remote get-url origin 2>$null)
    if ($LASTEXITCODE -ne 0 -or $remote -notlike "*my-site*") {
        Write-Host "  [FAIL] $dest origin is '$remote', expected the my-site repo."
        exit 1
    }
    git fetch origin main --quiet
    git checkout main --quiet
    git reset --hard origin/main --quiet
    Write-Host "  [OK] target synced to origin/main"
} finally {
    Pop-Location
}

# --- 0. Drift guard (warning only, never blocks) -------------------------
# Catches the old three-tree split before it bites. If BS_GodFile/wix/index.html
# or _github_deploy/wix/index.html disagree with the source, say so plainly.
function Get-FileSha256($Path) {
    if (-not (Test-Path $Path)) { return "<missing>" }
    (Get-FileHash -Algorithm SHA256 $Path).Hash.Substring(0, 12)
}
$srcIdx = Join-Path $source "wix/index.html"
$bgdIdx = "C:\EnvironmentPortfolio\BS_GodFile\wix\index.html"
$dstIdx = Join-Path $dest "wix/index.html"
$srcHash = Get-FileSha256 $srcIdx
$bgdHash = Get-FileSha256 $bgdIdx
$dstHash = Get-FileSha256 $dstIdx
if ($bgdHash -ne "<missing>" -and $bgdHash -ne $srcHash) {
    Write-Host "  [WARN] BS_GodFile\wix\index.html ($bgdHash) differs from source ($srcHash)."
    Write-Host "         Source of truth is my-site-clean. Ignore BS_GodFile/wix or resync it."
}
if ($dstHash -ne "<missing>" -and $dstHash -ne $srcHash) {
    Write-Host "  [WARN] $dest\wix\index.html ($dstHash) differs from source ($srcHash) -- will be overwritten."
}

# --- 1. Sync files --------------------------------------------------------
Write-Host ""
Write-Host "  -- Syncing files --"
# ONLY the site folders this repo actually tracks.
#
# "content" is deliberately absent. Windows paths are case-insensitive, so a
# `content` entry resolves to this project's UE `Content\` tree -- 26,591 asset
# files -- and the old sync list would have copied the entire game project into
# the published site. The site's own content/ (site-copy.json, site-plates.json),
# plus public/, application/ and tools/, live only in the my-site repo; they are
# not mirrored here, so this script must not try to write them.
$dirsToSync = @("wix", "components", "projects", "generated")

# --- 1b. Regenerate the honest, ledger-backed status (token-free auto-sync) --
# Runs the game-repo generator, then copies its output into the site source so
# the next deploy ships live standing. Requires Python 3 on PATH.
Write-Host ""
Write-Host "  -- Syncing live status --"
$scriptRoot = Split-Path -Parent $PSScriptRoot   # BS_GodFile/
$genPy = Join-Path $scriptRoot "Tools/sync_site_status.py"
$genStatus = & python $genPy 2>&1
$genStatus | ForEach-Object { Write-Host "    $_" }
$statusSrc = Join-Path $source "public/melodia/status/sync_status.json"
if (Test-Path $statusSrc) {
    $statusDst = Join-Path $dest "public/melodia/status/sync_status.json"
    New-Item -ItemType Directory -Path (Split-Path $statusDst) -Force | Out-Null
    Copy-Item $statusSrc $statusDst -Force
    Write-Host "  [OK] live status staged"
} else {
    Write-Host "  [WARN] generator did not produce public/melodia/status/sync_status.json (is Python on PATH?)"
}

foreach ($d in $dirsToSync) {
    if ($d -ieq "content") {
        Write-Host "  [FAIL] 'content' in `$dirsToSync resolves to the UE Content\ tree on Windows."
        exit 1
    }
}

foreach ($dir in $dirsToSync) {
    $srcPath = Join-Path $source $dir
    $dstPath = Join-Path $dest $dir
    if (-not (Test-Path $srcPath)) { continue }

    if (Test-Path $dstPath) { Remove-Item $dstPath -Recurse -Force }

    $count = 0
    Get-ChildItem -Path $srcPath -Recurse -File | ForEach-Object {
        $relPath = $_.FullName.Substring($srcPath.Length + 1)
        if ($relPath -like "*.git*" -or $relPath -like "*node_modules*" -or
            $relPath -like "*.DS_Store*" -or $relPath -like "Thumbs.db*") { return }
        $destFile = Join-Path $dstPath $relPath
        $destDir  = Split-Path -Parent $destFile
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        Copy-Item $_.FullName $destFile -Force
        $count++
    }
    Write-Host "  [OK] $dir/  ($count files)"
}

# --- 2. Commit & push -----------------------------------------------------
Write-Host ""
Push-Location $dest
try {
    git add -A
    $status = git status --porcelain
    if (-not $status) {
        Write-Host "  [OK] No changes to deploy"
        return
    }

    $changedCount = ($status | Measure-Object).Count
    Write-Host "  -- $changedCount file(s) changed --"
    git diff --cached --stat | Select-Object -Last 15

    if (-not $Deploy) {
        Write-Host ""
        Write-Host "  [DRY RUN] -Deploy `$false -- staged but not committed."
        Pop-Location
        exit 0
    }

    git commit -m $Message
    git push origin main
    Write-Host "  [OK] pushed to my-site main; the Pages Action publishes from there"
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "  LIVE at https://fromage3900.github.io/my-site/wix/index.html"
Write-Host "  (Pages build is an Action on my-site main -- allow ~1 min, then hard-refresh.)"
Write-Host ""
