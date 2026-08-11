# BS_GodFile --- Project Status Dashboard
# Usage: ./deploy/status.ps1

$ROOT   = Split-Path $PSScriptRoot -Parent
$DEPLOY = $PSScriptRoot

function Write-Section($title) {
    Write-Host ""
    Write-Host "--- $title ---" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   BS_GodFile -- Project Status Dashboard  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Agent Loops
Write-Section "AGENT LOOPS"
$stops = Get-ChildItem -Path $DEPLOY -Filter "*_LOOP_STOP" -File -ErrorAction SilentlyContinue
if ($stops.Count -eq 0) {
    Write-Host "  [OK]  All loops running (no STOP files)" -ForegroundColor Green
} else {
    foreach ($s in $stops) {
        Write-Host "  [STOP] $($s.Name)" -ForegroundColor Red
    }
}

$pids = Get-ChildItem -Path $DEPLOY -Filter "*.pid" -File -ErrorAction SilentlyContinue
foreach ($p in $pids) {
    Write-Host "  [PID]  $($p.Name)" -ForegroundColor Yellow
}

# Git Status (text files only)
Write-Section "GIT STATUS (text/scripts only)"
Push-Location $ROOT
$textDirty = git status --short 2>$null | Where-Object {
    $_ -notmatch '\.uasset' -and $_ -notmatch '\.umap' -and
    $_ -notmatch '\.blend'  -and $_ -notmatch '\.png'  -and
    $_ -notmatch '\.fbx'    -and $_ -notmatch '\.jpg'  -and
    $_ -notmatch 'Backups/'
} | Select-Object -First 30

if ($textDirty.Count -eq 0) {
    Write-Host "  [OK]  Clean working tree (text files)" -ForegroundColor Green
} else {
    foreach ($line in $textDirty) {
        $color = if ($line -match '^\s*D') { "Red" } elseif ($line -match '^\s*A') { "Green" } else { "Yellow" }
        Write-Host "  $line" -ForegroundColor $color
    }
}
Pop-Location

# Recent Commits
Write-Section "RECENT COMMITS (last 5)"
Push-Location $ROOT
$commits = git log --oneline -5 2>$null
foreach ($c in $commits) { Write-Host "  $c" -ForegroundColor Gray }
Pop-Location

# Protected File Health
Write-Section "PROTECTED FILES"
Push-Location $ROOT
$PROTECTED = @(".gitignore", ".gitattributes", "Config/DefaultEngine.ini", "deploy/run_verify.ps1")
$allStatus = git status --short 2>$null
foreach ($p in $PROTECTED) {
    if ($allStatus | Where-Object { $_ -match [regex]::Escape($p) }) {
        Write-Host "  [WARN] DIRTY: $p" -ForegroundColor Red
    } else {
        Write-Host "  [OK]   $p" -ForegroundColor Green
    }
}
Pop-Location

# Service Discovery (Decision 2026-08-06: Added health checks for background services)
Write-Section "SERVICE DISCOVERY"
$services = @(
    @{ Name = "Monolith MCP"; Port = 9316; Url = "http://127.0.0.1:9316/health" },
    @{ Name = "LiveLink"; Port = 9876; Url = "http://127.0.0.1:9876" },
    @{ Name = "VOICEVOX"; Port = 50021; Url = "http://127.0.0.1:50021/version" },
    @{ Name = "Ollama"; Port = 11434; Url = "http://127.0.0.1:11434" }
)

foreach ($s in $services) {
    try {
        $response = Invoke-WebRequest -Uri $s.Url -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        Write-Host "  [UP]   $($s.Name) (:$($s.Port))" -ForegroundColor Green
    } catch {
        Write-Host "  [DOWN] $($s.Name) (:$($s.Port))" -ForegroundColor Red
    }
}

# AI Rule Files
Write-Section "AI RULE FILES"
$rules = @("CLAUDE.md", ".cursor\rules\agent-boundaries.md", ".kiro\steering\agent-boundaries.md", ".windsurf\rules.md")
foreach ($r in $rules) {
    $path = Join-Path $ROOT $r
    if (Test-Path $path) {
        Write-Host "  [OK]  $r" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $r" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Run ./deploy/safe-session.ps1 for details" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
