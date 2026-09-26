# deploy/setup_agent_lanes.ps1 -- one-time: register the verified model lanes with jcode.
#
#   $env:AWS_BEARER_TOKEN_BEDROCK = '<Bedrock Mantle API key>'   # never commit it
#   .\deploy\setup_agent_lanes.ps1 [-DryRun]
#
# Lanes verified live 2026-09-26 (see .jcode/swarm-prompt.md). The same key/env var is read by
# Tools/model_router.py (endpoint "bedrock") and .opencode/opencode.jsonc (provider "bedrock-mantle").
# Hermes: add the same base URL as a custom provider by hand (see the orchestrator plan).
param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
$Mantle = 'https://bedrock-mantle.us-east-1.api.aws/v1'
$Lanes = @(
    @{ Name = 'mantle-code';  Url = $Mantle; Model = 'qwen.qwen3-coder-next' },
    @{ Name = 'mantle-fast';  Url = $Mantle; Model = 'zai.glm-4.7-flash' },
    @{ Name = 'mantle-deep';  Url = $Mantle; Model = 'qwen.qwen3-235b-a22b-2507' },
    @{ Name = 'ollama-local'; Url = 'http://127.0.0.1:11434/v1'; Model = 'qwen3-coder:30b'; Local = $true }
)

if (-not (Get-Command jcode -ErrorAction SilentlyContinue)) { Write-Error 'jcode not on PATH (irm https://jcode.sh/install.ps1 | iex)' }
if (-not $DryRun -and -not $env:AWS_BEARER_TOKEN_BEDROCK) { Write-Error 'Set $env:AWS_BEARER_TOKEN_BEDROCK to the Bedrock Mantle API key first.' }

foreach ($lane in $Lanes) {
    $jcodeArgs = @('provider', 'add', $lane.Name, '--base-url', $lane.Url, '--model', $lane.Model, '--quiet')
    $jcodeArgs += $(if ($lane.Local) { '--no-api-key' } else { @('--api-key-env', 'AWS_BEARER_TOKEN_BEDROCK') })
    if ($DryRun) { Write-Host "jcode $($jcodeArgs -join ' ')"; continue }
    & jcode @jcodeArgs
    if ($LASTEXITCODE -ne 0) { Write-Error "jcode provider add $($lane.Name) failed ($LASTEXITCODE)" }
    Write-Host "added $($lane.Name) -> $($lane.Model)"
}

if ($DryRun) { exit 0 }
# Smoke the cloud lanes through the router (writes Saved/router_ledger.jsonl).
$repo = Split-Path $PSScriptRoot -Parent
foreach ($class in 'code', 'docs', 'deep') {
    python (Join-Path $repo 'Tools\model_router.py') chat $class --prompt 'Reply with the single word: ok' --json
}
