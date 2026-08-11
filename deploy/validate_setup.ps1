# Setup Validation Script
# Quick health check for Environment Portfolio Platform
param(
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$root = Split-Path -Parent $deploy

Write-Host "========================================="
Write-Host " ENVIRONMENT PORTFOLIO SETUP CHECK"
Write-Host " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "========================================="
Write-Host ""

$issues = 0
$warnings = 0

# Load Config
$configPath = Join-Path $root "config\paths.json"
$uePath = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$blenderPath = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"

if (Test-Path $configPath) {
    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($config.paths.unreal) { 
            $uePath = Join-Path $config.paths.unreal "Engine\Binaries\Win64\UnrealEditor.exe" 
        }
        if ($config.paths.blender) { 
            $blenderPath = Join-Path $config.paths.blender "blender.exe" 
        }
        Write-Host "  Loaded config from: config\paths.json"
    } catch {
        Write-Host "  Could not load config, using defaults"
    }
} else {
    Write-Host "  Using default paths (config\paths.json not found)"
}

# Unreal Engine Check
Write-Host "Checking Unreal Engine 5.8..."
if (Test-Path $uePath) {
    Write-Host "  [OK] Unreal Engine 5.8 found"
} else {
    Write-Host "  [FAIL] Unreal Engine 5.8 NOT found at: $uePath"
    Write-Host "         Install from Epic Games Launcher"
    Write-Host "         Or update config\paths.json with your path"
    $issues++
}
Write-Host ""

# Blender Check
Write-Host "Checking Blender 5.1+..."
if (Test-Path $blenderPath) {
    Write-Host "  [OK] Blender 5.1 found"
} else {
    Write-Host "  [WARN] Blender 5.1 NOT found at: $blenderPath"
    Write-Host "         Download from: https://www.blender.org/download/"
    Write-Host "         Or update config\paths.json with your path"
    Write-Host "         (Required for Geometry mode only)"
    $warnings++
}
Write-Host ""

# Project File Check
Write-Host "Checking Project File..."
$projectFile = Join-Path $root "BS_GodFile.uproject"
if (Test-Path $projectFile) {
    Write-Host "  [OK] BS_GodFile.uproject found"
} else {
    Write-Host "  [FAIL] BS_GodFile.uproject NOT found"
    $issues++
}
Write-Host ""

# Port Checks
Write-Host "Checking Service Ports..."

# UE MCP (9316)
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:9316/health" -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        Write-Host "  [OK] UE MCP (9316) - RUNNING"
    }
} catch {
    Write-Host "  [WARN] UE MCP (9316) - Not running (Unreal Editor not open)"
    $warnings++
}

# VOICEVOX (50021)
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:50021/version" -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        Write-Host "  [OK] VOICEVOX (50021) - RUNNING"
    }
} catch {
    Write-Host "  [WARN] VOICEVOX (50021) - Not running (Optional for basic use)"
    $warnings++
}

Write-Host ""

# Git LFS Check
Write-Host "Checking Git LFS..."
try {
    $lfsVersion = git lfs version 2>$null
    if ($lfsVersion) {
        Write-Host "  [OK] Git LFS installed: $lfsVersion"
    } else {
        Write-Host "  [WARN] Git LFS not found - run: git lfs install"
        $warnings++
    }
} catch {
    Write-Host "  [WARN] Git not found or Git LFS not installed"
    $warnings++
}
Write-Host ""

# Python Check
Write-Host "Checking Python..."
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion) {
        Write-Host "  [OK] Python found: $pythonVersion"
    } else {
        Write-Host "  [WARN] Python not found (Required for some scripts)"
        $warnings++
    }
} catch {
    Write-Host "  [WARN] Python not found (Required for some scripts)"
    $warnings++
}
Write-Host ""

# Summary
Write-Host "========================================="
Write-Host " SETUP CHECK SUMMARY"
Write-Host "========================================="
Write-Host ""

if ($issues -eq 0 -and $warnings -eq 0) {
    Write-Host "All checks passed! You're ready to go!"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  Read QUICKSTART.md for your onboarding path"
    Write-Host "  Open BS_GodFile.uproject to start"
} elseif ($issues -eq 0) {
    Write-Host "Setup complete with $warnings warning(s)"
    Write-Host ""
    Write-Host "You can proceed, but some features may be limited."
    Write-Host "  Read QUICKSTART.md for your onboarding path"
} else {
    Write-Host "Setup incomplete: $issues issue(s) found"
    Write-Host ""
    Write-Host "Please fix the issues above before proceeding."
    Write-Host "  Read QUICKSTART.md for setup instructions"
}

Write-Host ""
Write-Host "========================================="
Write-Host " For detailed help: QUICKSTART.md"
Write-Host "========================================="