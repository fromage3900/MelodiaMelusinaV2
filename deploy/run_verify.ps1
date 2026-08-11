# Headless verify runner — always uses --factory-startup.
param(
    [ValidateSet("all", "world", "overhaul", "os")]
    [string]$Mode = "all"
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$blender = @(
    "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
    "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $blender) {
    Write-Error "Blender not found"
}

$script = Join-Path $deploy "_mcp_verify_all.py"
$args = @("--background", "--factory-startup", "--python", $script, "--", $Mode)
& $blender @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Verify OK (mode=$Mode)"
