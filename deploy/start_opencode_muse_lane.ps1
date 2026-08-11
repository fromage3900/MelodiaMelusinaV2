# Validate OpenCode (+ optional Muse) for Melodia companion IDE lane.
# Does NOT start Unreal Editor.
# See: Docs/PhoneOps/JCODE_SWARM_PIPELINE.md, Docs/Production/MUSE_CODE_LANE_2026-08-11.md
param(
    [switch]$SkipMuse,
    [switch]$RequireMuse,
    [switch]$LaunchOpenCode
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$repoRoot = Resolve-Path (Join-Path $deploy "..")
Set-Location $repoRoot

function Add-PathIfExists {
    param([string]$Dir)
    if (-not $Dir) { return }
    if (-not (Test-Path $Dir)) { return }
    $parts = $env:PATH -split ';'
    if ($parts -contains $Dir) { return }
    $env:PATH = "$Dir;$env:PATH"
    Write-Host "PATH prepend: $Dir"
}

# Common install locations (session PATH only)
Add-PathIfExists (Join-Path $env:LOCALAPPDATA "jcode\bin")
Add-PathIfExists (Join-Path $env:USERPROFILE ".jcode\bin")
Add-PathIfExists (Join-Path $env:APPDATA "npm")
Add-PathIfExists (Join-Path $env:LOCALAPPDATA "npm")
Add-PathIfExists (Join-Path $env:USERPROFILE ".local\bin")

$failed = @()

$jcodeCmd = Get-Command jcode -ErrorAction SilentlyContinue
if ($jcodeCmd) {
    Write-Host "jcode: OK ($($jcodeCmd.Source))"
    try {
        & jcode --version 2>&1 | Select-Object -First 2 | ForEach-Object { Write-Host "  $_" }
    } catch {
        Write-Host "  (version probe skipped)"
    }
} else {
    $failed += "jcode"
    Write-Host "jcode: MISSING on PATH"
    Write-Host "  Install: irm https://jcode.sh/install.ps1 | iex"
    Write-Host "  Or ensure %LOCALAPPDATA%\jcode\bin is on PATH"
}

$opencodeCmd = Get-Command opencode -ErrorAction SilentlyContinue
if ($opencodeCmd) {
    Write-Host "opencode: OK ($($opencodeCmd.Source))"
    try {
        & opencode --version 2>&1 | Select-Object -First 2 | ForEach-Object { Write-Host "  $_" }
    } catch {
        Write-Host "  (version probe skipped)"
    }
} else {
    $failed += "opencode"
    Write-Host "opencode: MISSING on PATH"
    Write-Host "  Install: npm i -g opencode-ai@latest"
    Write-Host "  Or: scoop install extras/opencode"
}

$museOk = $false
if (-not $SkipMuse) {
    $wsl = Get-Command wsl -ErrorAction SilentlyContinue
    if ($wsl) {
        $museCheck = & wsl -e bash -lc "command -v muse >/dev/null && muse --version" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $museOk = $true
            Write-Host "muse (WSL): OK"
            $museCheck | ForEach-Object { Write-Host "  $_" }
        } else {
            Write-Host "muse (WSL): not found or failed"
            Write-Host "  See Docs/Production/MUSE_CODE_LANE_2026-08-11.md"
            if ($RequireMuse) { $failed += "muse" }
        }
    } else {
        Write-Host "muse: WSL not available; skip Muse check"
        if ($RequireMuse) { $failed += "muse" }
    }
} else {
    Write-Host "muse: skipped (-SkipMuse)"
}

Write-Host ""
Write-Host "=== Melodia OpenCode / Muse lane ==="
Write-Host "Repo:     $repoRoot"
Write-Host "Lane map: jcode = parallel repo swarm"
Write-Host "          OpenCode-in-Rider = C++/PIE gameplay lane"
Write-Host "          Muse Code = Meta terminal agent (WSL)"
Write-Host "UE:       NOT started by this script"
Write-Host ""
Write-Host "Rider shortcuts (OpenCode plugin):"
Write-Host "  Ctrl+\              Launch OpenCode terminal (127.0.0.1:4096)"
Write-Host "  Ctrl+Alt+K          Add current file/selection to OpenCode context"
Write-Host "  Right-click editor  OpenCode: Add Context / Add File(s)"
Write-Host "  Tab in OpenCode     Switch build (edit) <-> plan (readonly)"
Write-Host ""
Write-Host "Suggested next:"
Write-Host "  1. Open BS_GodFile.uproject in Rider"
Write-Host "  2. Ctrl+\ -> OpenCode session"
Write-Host "  3. Optional Muse: wsl -e muse   (from repo via /mnt/c/.../BS_GodFile)"
Write-Host "  4. Swarm (separate): .\deploy\start_jcode_swarm.ps1"
Write-Host ""

$configHints = @(
    (Join-Path $repoRoot ".opencode"),
    (Join-Path $repoRoot ".opencode\opencode.jsonc"),
    (Join-Path $repoRoot ".opencode.json"),
    (Join-Path $repoRoot "Docs\Production\MUSE_CODE_LANE_2026-08-11.md"),
    (Join-Path $repoRoot "Docs\Handoffs\TONIGHT_FIRST_DREAM_OPENCODE_2026-08-11.md")
)
foreach ($p in $configHints) {
    if (Test-Path $p) {
        Write-Host "Found: $p"
    } else {
        Write-Host "Missing (optional): $p"
    }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host ("FAIL: missing tools: " + ($failed -join ", "))
    exit 1
}

Write-Host ""
Write-Host "PASS: required tools present (UE intentionally not launched)."

if ($LaunchOpenCode) {
    Write-Host "LaunchOpenCode set -- starting opencode in repo root (interactive)."
    & opencode
}
