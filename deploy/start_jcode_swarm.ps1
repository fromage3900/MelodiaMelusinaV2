# Launch jcode in the MelodiaMelusinaV2 repo (interactive swarm coordinator session).
# Prerequisite: jcode installed + logged in. See .jcode/README.md
param(
    [switch]$SkipSkillsInstall,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$repoRoot = Resolve-Path (Join-Path $deploy "..")

Set-Location $repoRoot

$jcodeCmd = Get-Command jcode -ErrorAction SilentlyContinue
if (-not $jcodeCmd) {
    Write-Host @"
jcode not found on PATH.

Install (Windows):
  irm https://jcode.sh/install.ps1 | iex

Then:
  jcode login --provider <claude|openai|copilot|gemini|...>
  copy .jcode\config.example.toml `$env:USERPROFILE\.jcode\config.toml
  .\deploy\install_jcode_melodia_skills.ps1
  .\deploy\start_jcode_swarm.ps1
"@
    exit 1
}

$swarmPrompt = Join-Path $repoRoot ".jcode\swarm-prompt.md"
$mcpJson = Join-Path $repoRoot ".jcode\mcp.json"
$bootstrap = Join-Path $repoRoot ".jcode\coordinator-bootstrap.md"

if (-not (Test-Path $swarmPrompt)) {
    Write-Error "Missing $swarmPrompt"
}
if (-not (Test-Path $mcpJson)) {
    Write-Error "Missing $mcpJson"
}

$userConfigDir = Join-Path $env:USERPROFILE ".jcode"
$userConfig = Join-Path $userConfigDir "config.toml"
$exampleConfig = Join-Path $repoRoot ".jcode\config.example.toml"
if (-not (Test-Path $userConfig)) {
    New-Item -ItemType Directory -Force -Path $userConfigDir | Out-Null
    if (Test-Path $exampleConfig) {
        Copy-Item $exampleConfig $userConfig
        Write-Host "Created $userConfig from config.example.toml (enable swarm/memory)."
    }
} else {
    Write-Host "Using existing $userConfig (ensure [features] swarm = true)."
}

if (-not $SkipSkillsInstall) {
    $skillsScript = Join-Path $deploy "install_jcode_melodia_skills.ps1"
    if (Test-Path $skillsScript) {
        & $skillsScript -RepoRoot $repoRoot
    }
}

Write-Host ""
Write-Host "=== Melodia jcode swarm ==="
Write-Host "Repo:     $repoRoot"
Write-Host "Policy:   .jcode\swarm-prompt.md"
Write-Host "MCP:      .jcode\mcp.json (Monolith proxy -- needs UE open for editor tools)"
Write-Host "Bootstrap: paste contents of .jcode\coordinator-bootstrap.md into the root session"
Write-Host "Quit:     /quit in jcode (interactive; no separate stop script)"
Write-Host ""

if ($NoLaunch) {
    Write-Host "NoLaunch set -- not starting jcode."
    if (Test-Path $bootstrap) {
        Write-Host "Bootstrap file: $bootstrap"
    }
    exit 0
}

# Interactive TUI in repo root (default per plan)
& jcode
