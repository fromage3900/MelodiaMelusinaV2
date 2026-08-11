# AI Tool Quick Reference - Switch between MCP-compatible assistants
# Usage: powershell -File deploy\ai_tool_quickstart.ps1 [-Action status|start-opencode|sync-web] [-Model model_name] [-Provider openai|ollama|openrouter]

param(
    [string]$Action = "status",
    [string]$Model = "qwen2.5-coder:14b",
    [string]$Provider = "auto"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== AI Tool Router ===" -ForegroundColor Cyan
Write-Host "Action: $Action" -ForegroundColor Yellow
Write-Host "Provider: $Provider" -ForegroundColor Yellow
Write-Host "Model: $Model" -ForegroundColor Yellow
Write-Host ""

# Check Ollama status (local provider)
if ($Provider -eq "auto" -or $Provider -eq "ollama") {
    try {
        $ollamaStatus = ollama list 2>&1 | Select-String $Model
        if ($ollamaStatus) {
            Write-Host "[OK] Ollama model '$Model' is installed" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Model '$Model' not found in Ollama" -ForegroundColor Yellow
            Write-Host "Run: ollama pull $Model" -ForegroundColor Gray
        }
    } catch {
        Write-Host "[ERROR] Ollama not responding. Start with: ollama serve" -ForegroundColor Red
    }

    # Check Ollama service
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2
        Write-Host "[OK] Ollama service is running on port 11434" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Ollama service not reachable - start with: ollama serve" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Available Tools ===" -ForegroundColor Cyan

# List installed config files
$configFiles = @(
    @{ path = ".cursor\mcp.json"; name = "Cursor IDE (primary)" },
    @{ path = ".opencode.json"; name = "OpenCode (offline)" },
    @{ path = ".continue\config.json"; name = "Continue.dev extension" },
    @{ path = ".claude.json"; name = "Claude Code CLI" },
    @{ path = ".windsurf\mcp.json"; name = "Windsurf IDE" }
)

foreach ($entry in $configFiles) {
    $fullPath = Join-Path $ProjectRoot $entry.path
    if (Test-Path $fullPath) {
        Write-Host "  [OK] $($entry.path) - $($entry.name)" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $($entry.path) - $($entry.name)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Quick Commands ===" -ForegroundColor Cyan
Write-Host "  # LOCAL (requires ollama running):" -ForegroundColor DarkGray
Write-Host "  opencode --model ollama:$Model              # Start OpenCode with local model" -ForegroundColor Gray
Write-Host ""
Write-Host "  # CLOUD (requires API key in env):" -ForegroundColor DarkGray
Write-Host "  set OPENAI_API_KEY=your_key && opencode --model openai/gpt-4-turbo      # OpenAI GPT-4" -ForegroundColor Gray
Write-Host "  set OPENROUTER_API_KEY=your_key && opencode --model openrouter/anthropic/claude-3.5-sonnet  # OpenRouter" -ForegroundColor Gray
Write-Host "  set ANTHROPIC_API_KEY=your_key && opencode --model anthropic/claude-3-5-sonnet-20241022  # Claude" -ForegroundColor Gray
Write-Host ""
Write-Host "  # NO-MODEL (uses default cloud provider):" -ForegroundColor DarkGray
Write-Host "  opencode                                     # Start OpenCode without specific model" -ForegroundColor Gray
Write-Host ""
Write-Host "  npm run verify:all                         # Verify website" -ForegroundColor Gray
Write-Host "  python deploy\ai_tool_router.py --sync-website  # Sync to GitHub Pages" -ForegroundColor Gray
Write-Host "  python deploy\ai_tool_router.py --list-tools   # List MCP tools" -ForegroundColor Gray

if ($Action -eq "start-opencode") {
    if ($Provider -eq "auto") {
        # Try ollama first, fall back to default if not running
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2
            Write-Host ""
            Write-Host "Starting OpenCode with ollama:$Model..." -ForegroundColor Green
            opencode --model "ollama:$Model"
        } catch {
            Write-Host ""
            Write-Host "Ollama not available. Starting OpenCode with default model..." -ForegroundColor Yellow
            opencode
        }
    }
    elseif ($Provider -eq "ollama") {
        Write-Host ""
        Write-Host "Starting OpenCode with ollama:$Model..." -ForegroundColor Green
        opencode --model "ollama:$Model"
    }
    else {
        Write-Host ""
        Write-Host "Starting OpenCode with provider:$Provider..." -ForegroundColor Green
        opencode --model "$Provider/$Model"
    }
}

if ($Action -eq "sync-web") {
    Write-Host ""
    Write-Host "Syncing website to GitHub Pages..." -ForegroundColor Green
    & (Join-Path $PSScriptRoot "sync_site_to_github.ps1")
}