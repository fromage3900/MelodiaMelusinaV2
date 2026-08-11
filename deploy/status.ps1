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

# Service Discovery (ports and optional/required semantics come from Config/paths.json)
Write-Section "SERVICE DISCOVERY"
$configPath = Join-Path $ROOT "Config\paths.json"
$config = if (Test-Path $configPath) {
    Get-Content $configPath -Raw | ConvertFrom-Json
} else {
    $null
}
$ports = if ($config) { $config.ports } else { $null }

function Get-Port($name, $fallback) {
    if ($ports -and $ports.PSObject.Properties[$name]) {
        return [int]$ports.$name
    }
    return $fallback
}

function Test-TcpPort($port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect("127.0.0.1", $port, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne(700)) { return $false }
        $client.EndConnect($async)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Test-Http($uri) {
    try {
        $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    } catch {
        return $false
    }
}

$services = @(
    @{ Name = "Monolith MCP"; Port = Get-Port "ue_mcp" 9316; Uri = "http://127.0.0.1:$(Get-Port "ue_mcp" 9316)/health"; Probe = "http" },
    @{ Name = "LiveLink"; Port = Get-Port "livelink" 9876; Uri = $null; Probe = "tcp" },
    @{ Name = "Blender MCP"; Port = Get-Port "blender_mcp" 9317; Uri = "http://127.0.0.1:$(Get-Port "blender_mcp" 9317)/health"; Probe = "http" },
    @{ Name = "VOICEVOX"; Port = Get-Port "voicevox" 50021; Uri = "http://127.0.0.1:$(Get-Port "voicevox" 50021)/version"; Probe = "http" },
    @{ Name = "Melusina Voice"; Port = Get-Port "melusina_voice" 50022; Uri = $null; Probe = "tcp" },
    @{ Name = "Ollama"; Port = Get-Port "ollama" 11434; Uri = "http://127.0.0.1:$(Get-Port "ollama" 11434)"; Probe = "http" },
    @{ Name = "Quantum"; Port = Get-Port "quantum" 8008; Uri = "http://127.0.0.1:$(Get-Port "quantum" 8008)/health"; Probe = "http" }
)

foreach ($s in $services) {
    $up = if ($s.Probe -eq "http") { Test-Http $s.Uri } else { Test-TcpPort $s.Port }
    if ($up) {
        Write-Host "  [UP]   $($s.Name) (:$($s.Port))" -ForegroundColor Green
    } else {
        Write-Host "  [DOWN] $($s.Name) (:$($s.Port), optional)" -ForegroundColor Yellow
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
