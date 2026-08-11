# Sync my-site-clean to GitHub Pages (worktree) + auto-deploy
# One-way sync: my-site-clean is source of truth
# Run this to make all changes live in one command:
#   .\deploy\sync_site_to_github.ps1
#   .\deploy\sync_site_to_github.ps1 -Message "Add new Space Cathedral hero stills"

param(
    [string]$Message = "Sync site updates"
)

$ErrorActionPreference = "Stop"

# --- Paths ----------------------------------------------------------------
$scriptRoot = Split-Path -Parent $PSScriptRoot
$source     = Join-Path $scriptRoot "my-site-clean"
if (Test-Path "C:\EnvironmentPortfolio\_github_deploy") {
    $dest = "C:\EnvironmentPortfolio\_github_deploy"
} else {
    $dest = "G:\EnvironmentPortfolio\_github_deploy"
}

# --- Header ---------------------------------------------------------------
Write-Host ""
Write-Host "  +----------------------------------------------+"
Write-Host "  |     Melodia Portfolio -- Deploy Pipeline     |"
Write-Host "  +----------------------------------------------+"
Write-Host ""
Write-Host "  Source : my-site-clean/"
Write-Host "  Target : _github_deploy/ (worktree)"
Write-Host "  Commit : $Message"
Write-Host ""

# --- Validate -------------------------------------------------------------
if (-not (Test-Path $source)) {
    Write-Host "  [FAIL] Source directory not found: $source"
    exit 1
}
if (-not (Test-Path $dest)) {
    Write-Host "  [FAIL] Worktree not found: $dest"
    Write-Host "         Expected a git worktree at G:\EnvironmentPortfolio\_github_deploy"
    exit 1
}

# --- 1. Sync files --------------------------------------------------------
Write-Host "  ── Syncing files ──"
$dirsToSync = @("wix", "content", "generated", "public", "application", "components", "projects", "tools")

foreach ($dir in $dirsToSync) {
    $srcPath = Join-Path $source $dir
    $dstPath = Join-Path $dest $dir

    if (Test-Path $srcPath) {
        if (Test-Path $dstPath) {
            Remove-Item $dstPath -Recurse -Force
        }
        Get-ChildItem -Path $srcPath -Recurse -File | ForEach-Object {
            $relPath = $_.FullName.Substring($srcPath.Length + 1)
            if ($relPath -like "*.git*" -or $relPath -like "*node_modules*" -or $relPath -like "*.DS_Store*" -or $relPath -like "Thumbs.db*") {
                return
            }
            $destFile = Join-Path $dstPath $relPath
            $destDir = Split-Path -Parent $destFile
            if (-not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            Copy-Item $_.FullName $destFile -Force
        }
        Write-Host "  [OK] $dir/"
    }
}

# Sync root files
Get-ChildItem $source -File | Where-Object {
    $_.Name -ne "package-lock.json" -and $_.Name -notlike "*.git*"
} | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $dest $_.Name) -Force
}

# --- 2. Commit & push -----------------------------------------------------
Write-Host ""
Write-Host "  ── Deploying ──"

Push-Location $dest
try {
    git add -A
    $status = git status --porcelain
    if ($status) {
        git commit -m $Message
        git push origin main
        $changedCount = ($status | Measure-Object).Count
        Write-Host "  [OK] $changedCount files changed, committed, and pushed to main"
    } else {
        Write-Host "  [OK] No changes to deploy"
    }
} finally {
    Pop-Location
}

# --- 3. Done --------------------------------------------------------------
Write-Host ""
Write-Host "  LIVE at https://fromage3900.github.io/my-site/wix/index.html"
Write-Host ""