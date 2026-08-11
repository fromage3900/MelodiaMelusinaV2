# PowerShell Safety Session Pre-Flight Check
# Run this before starting any AI tool session on BS_GodFile.
# Usage: ./deploy/safe-session.ps1
# Returns exit code 1 if any safety condition is blocking.

$ROOT = Split-Path $PSScriptRoot -Parent
$DEPLOY = $PSScriptRoot
$RED    = [System.ConsoleColor]::Red
$YELLOW = [System.ConsoleColor]::Yellow
$GREEN  = [System.ConsoleColor]::Green
$CYAN   = [System.ConsoleColor]::Cyan
$RESET  = [System.ConsoleColor]::Gray

$blocking = $false

Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  BS_GodFile — AI Session Pre-Flight Safety Check  " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ── 1. Check Loop STOP files ──────────────────────────────────────────────────
Write-Host "[ 1 ] Agent Loop STOP files:" -ForegroundColor Cyan
$stopFiles = Get-ChildItem -Path $DEPLOY -Filter "*_LOOP_STOP" -File -ErrorAction SilentlyContinue
if ($stopFiles.Count -eq 0) {
    Write-Host "      ✅  No STOP files — loops are clear." -ForegroundColor Green
} else {
    foreach ($f in $stopFiles) {
        Write-Host "      🛑  $($f.Name)" -ForegroundColor Red
        $blocking = $true
    }
    Write-Host "      ⚠️  Clear STOP files before any /Game/EnvSandbox/ writes." -ForegroundColor Yellow
}
Write-Host ""

# ── 2. Check protected files are clean ───────────────────────────────────────
Write-Host "[ 2 ] Protected file status (git dirty check):" -ForegroundColor Cyan
$PROTECTED = @(
    ".gitignore",
    ".gitattributes",
    "Config/DefaultEngine.ini",
    "Config/DefaultGame.ini",
    "deploy/run_verify.ps1"
)
Push-Location $ROOT
$dirty = git status --short 2>$null | Where-Object { $_ -match '^\s*[MA D]' }
$dirtyProtected = @()
foreach ($p in $PROTECTED) {
    $match = $dirty | Where-Object { $_ -match [regex]::Escape($p) }
    if ($match) { $dirtyProtected += $p }
}
Pop-Location
if ($dirtyProtected.Count -eq 0) {
    Write-Host "      ✅  All protected files are clean." -ForegroundColor Green
} else {
    foreach ($f in $dirtyProtected) {
        Write-Host "      ⚠️  DIRTY (uncommitted): $f" -ForegroundColor Yellow
    }
    Write-Host "      Run: git checkout HEAD -- <file>  to restore" -ForegroundColor Yellow
}
Write-Host ""

# ── 3. Check git status summary (non-uasset) ─────────────────────────────────
Write-Host "[ 3 ] Uncommitted non-binary changes:" -ForegroundColor Cyan
Push-Location $ROOT
$textDirty = git status --short 2>$null | Where-Object {
    $_ -notmatch '\.uasset' -and
    $_ -notmatch '\.umap' -and
    $_ -notmatch '\.blend' -and
    $_ -notmatch '\.png' -and
    $_ -notmatch '\.fbx'
} | Select-Object -First 20
Pop-Location
if ($textDirty.Count -eq 0) {
    Write-Host "      ✅  No uncommitted text/script changes." -ForegroundColor Green
} else {
    foreach ($line in $textDirty) {
        Write-Host "      📝  $line" -ForegroundColor Gray
    }
}
Write-Host ""

# ── 4. Last commit ────────────────────────────────────────────────────────────
Write-Host "[ 4 ] Last commit:" -ForegroundColor Cyan
Push-Location $ROOT
$lastCommit = git log --oneline -1 2>$null
Pop-Location
Write-Host "      📌  $lastCommit" -ForegroundColor Gray
Write-Host ""

# ── 5. Pre-commit hook status ─────────────────────────────────────────────────
Write-Host "[ 5 ] Safety hook:" -ForegroundColor Cyan
$hook = "$ROOT\.git\hooks\pre-commit"
if (Test-Path $hook) {
    Write-Host "      ✅  pre-commit hook installed." -ForegroundColor Green
} else {
    Write-Host "      ⚠️  pre-commit hook MISSING — run deploy/install-hooks.ps1" -ForegroundColor Yellow
}
Write-Host ""

# ── 6. AI rule files ──────────────────────────────────────────────────────────
Write-Host "[ 6 ] AI tool rule files:" -ForegroundColor Cyan
$ruleFiles = @{
    "CLAUDE.md"                          = "Claude (auto-load)"
    ".cursor\rules\agent-boundaries.md"  = "Cursor (auto-load)"
    ".kiro\steering\agent-boundaries.md" = "Kiro (auto-load)"
    ".windsurf\rules.md"                 = "Windsurf (auto-load)"
}
foreach ($kv in $ruleFiles.GetEnumerator()) {
    $path = Join-Path $ROOT $kv.Key
    if (Test-Path $path) {
        Write-Host "      ✅  $($kv.Value): $($kv.Key)" -ForegroundColor Green
    } else {
        Write-Host "      ❌  MISSING: $($kv.Key)  ($($kv.Value))" -ForegroundColor Red
    }
}
Write-Host ""

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
if ($blocking) {
    Write-Host "  ⛔  BLOCKED — resolve issues above before proceeding." -ForegroundColor Red
    exit 1
} else {
    Write-Host "  ✅  All clear — safe to start AI session." -ForegroundColor Green
    exit 0
}
