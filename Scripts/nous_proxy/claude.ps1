# Claude shim with UTF-8 MCP config repair & Melodia Multi-Model Picker
# Supports: Nous Claude, Gemini 4 Argon, Nous Free Tier, OpenCode CLI, Antigravity (agy), Stock Claude

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$REAL = "$env:USERPROFILE\.local\bin\claude.exe"
$NOUS_PROXY_PORT = if ($env:NOUS_PROXY_PORT) { $env:NOUS_PROXY_PORT } else { "47821" }
$savedDir = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Claireon"
$prefFile = Join-Path $savedDir "preferred_harness_target.txt"

# Check if this is a Claireon launch from Unreal Engine (has --strict-mcp-config)
$isClaireon = $Arguments -contains "--strict-mcp-config"
if (-not $isClaireon) {
    # Non-Claireon terminal call - pass straight through
    & $REAL @Arguments
    exit $LASTEXITCODE
}

# -----------------------------------------------------------------------------
# 1. Inspect and Repair --mcp-config JSON file (Transcode UTF-16LE -> UTF-8)
# -----------------------------------------------------------------------------
$repairedArgs = @()
$i = 0
while ($i -lt $Arguments.Count) {
    $arg = $Arguments[$i]
    if ($arg -eq "--mcp-config" -and ($i + 1) -lt $Arguments.Count) {
        $cfgPath = $Arguments[$i + 1]
        if (Test-Path $cfgPath) {
            try {
                $rawBytes = [System.IO.File]::ReadAllBytes($cfgPath)
                # Check for UTF-16LE BOM (0xFF, 0xFE)
                if ($rawBytes.Length -ge 2 -and $rawBytes[0] -eq 0xFF -and $rawBytes[1] -eq 0xFE) {
                    $decoded = [System.Text.Encoding]::Unicode.GetString($rawBytes)
                    [System.IO.File]::WriteAllText($cfgPath, $decoded, [System.Text.UTF8Encoding]::new($false))
                }
                # Validate JSON parse using universal ConvertFrom-Json
                $utf8Text = [System.IO.File]::ReadAllText($cfgPath, [System.Text.Encoding]::UTF8)
                $null = $utf8Text | ConvertFrom-Json
                $repairedArgs += $arg
                $repairedArgs += $cfgPath
            } catch {
                $fallback = "C:\EnvironmentPortfolio\BS_GodFile\.mcp.json"
                if (Test-Path $fallback) {
                    Write-Host "[claude shim] Repaired MCP config with fallback: $fallback" -ForegroundColor Yellow
                    $repairedArgs += $arg
                    $repairedArgs += $fallback
                }
            }
        } else {
            $fallback = "C:\EnvironmentPortfolio\BS_GodFile\.mcp.json"
            if (Test-Path $fallback) {
                $repairedArgs += $arg
                $repairedArgs += $fallback
            }
        }
        $i += 2
    } else {
        $repairedArgs += $arg
        $i++
    }
}

# -----------------------------------------------------------------------------
# 2. Check & Auto-Refresh Hermes / Nous OAuth Credentials
# -----------------------------------------------------------------------------
$hermesDir = Join-Path $env:LOCALAPPDATA "hermes"
$authJson = Join-Path $hermesDir "auth.json"
$hermesExe = Join-Path $hermesDir "bin\hermes.exe"
if ((Test-Path $authJson) -and (Test-Path $hermesExe)) {
    try {
        $authData = Get-Content $authJson -Raw | ConvertFrom-Json
        $expStr = $authData.providers.nous.agent_key_expires_at
        if ($expStr) {
            $expDate = [DateTime]::Parse($expStr).ToUniversalTime()
            if ($expDate -le [DateTime]::UtcNow.AddMinutes(2)) {
                Write-Host "[claude shim] Refreshing expired Nous token..." -ForegroundColor Cyan
                & $hermesExe auth refresh nous *>$null
            }
        }
    } catch {
        # Non-fatal
    }
}

# -----------------------------------------------------------------------------
# 3. Interactive Multi-Model / CLI Picker Menu
# -----------------------------------------------------------------------------
$defaultTarget = "1"
if (Test-Path $prefFile) {
    $savedPref = (Get-Content $prefFile -Raw).Trim()
    if ($savedPref) { $defaultTarget = $savedPref }
}

$choice = $env:CLAIREON_TARGET
if (-not $choice) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "             MELODIA / CLAIREON AI HARNESS (UNREAL ENGINE 5.8)                  " -ForegroundColor White
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "  [0] Gemini 4 Argon          (gemini-4-argon via Google API key)            " -ForegroundColor DarkGreen
    Write-Host "  [1] Nous Sonnet 5            (anthropic/claude-sonnet-5 via Nous Portal)     " -ForegroundColor Green
    Write-Host "  [2] Nous Opus 5              (anthropic/claude-opus-5 via Nous Portal)       " -ForegroundColor Green
    Write-Host "  [3] Step 5 Preview Free      (stepfun/step-5-preview:free - agentic flagship)" -ForegroundColor Yellow
    Write-Host "  [4] OpenCode CLI             (opencode TUI with Melodia project & MCP tools) " -ForegroundColor Magenta
    Write-Host "  [5] Antigravity CLI (agy)    (Google Antigravity CLI with Melodia project)   " -ForegroundColor Blue
    Write-Host "  [6] Stock Claude Direct      (Native Anthropic API key, proxy bypassed)      " -ForegroundColor DarkCyan
    Write-Host "  [7] Custom Model ID          (Enter custom Nous model ID)                    " -ForegroundColor Gray
    Write-Host "  [8] Longcat 2.5 Free         (meituan/longcat-2.5-preview:free - unlimited)  " -ForegroundColor Yellow
    Write-Host "  [9] Step 3.7 Flash Free      (stepfun/step-3.7-flash:free - fast spare)       " -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Cyan

    $timeoutSeconds = 5
    Write-Host "Select target [0-9] (Default: [$defaultTarget] in $timeoutSeconds`s, press 0-9 or Enter): " -NoNewline -ForegroundColor White

    $canCheckKey = $false
    try {
        $canCheckKey = -not [Console]::IsInputRedirected
    } catch {
        $canCheckKey = $false
    }

    $selectedKey = $null
    if ($canCheckKey) {
        for ($s = $timeoutSeconds; $s -gt 0; $s--) {
            for ($sub = 0; $sub -lt 10; $sub++) {
                try {
                    if ([Console]::KeyAvailable) {
                        $keyInfo = [Console]::ReadKey($true)
                        if ($keyInfo.Key -eq [ConsoleKey]::Enter) {
                            $selectedKey = $defaultTarget
                            break
                        }
                        $char = $keyInfo.KeyChar.ToString()
                        if ($char -match '^[0-9]$') {
                            $selectedKey = $char
                            break
                        }
                    }
                } catch {
                    break
                }
                Start-Sleep -Milliseconds 100
            }
            if ($selectedKey) { break }
            Write-Host "`b`b`b`b`b`b`b$($s)s): " -NoNewline
        }
    } else {
        # Non-interactive or redirected input - use default target immediately
        $selectedKey = $defaultTarget
    }

    if (-not $selectedKey) {
        $selectedKey = $defaultTarget
    }
    Write-Host "$selectedKey" -ForegroundColor Green
    $choice = $selectedKey

    # Persist preference
    try {
        if (-not (Test-Path $savedDir)) { New-Item -ItemType Directory -Force $savedDir | Out-Null }
        Set-Content -Path $prefFile -Value $choice -Encoding UTF8 -NoNewline
    } catch {}
}

# -----------------------------------------------------------------------------
# 4. Route and Launch Selected Target
# -----------------------------------------------------------------------------
switch ($choice) {
    "0" {
        # Gemini 4 Argon: same translating proxy, gemini upstream (Google OpenAI-compat surface).
        $gemKey = $env:GEMINI_API_KEY
        if (-not $gemKey) {
            $gemKeyFile = Join-Path $env:LOCALAPPDATA 'hermes\gemini_api_key.txt'
            if (Test-Path $gemKeyFile) {
                try { $gemKey = (Get-Content $gemKeyFile -Raw).Trim() } catch { $gemKey = '' }
            }
        }
        if (-not $gemKey) {
            Write-Host "[claude shim] GEMINI_API_KEY not found. Run Scripts\nous_proxy\set_gemini_key.ps1 once, then retry." -ForegroundColor Red
            exit 1
        }
        $env:NOUS_MODEL = 'gemini-4-argon'
        & (Join-Path $PSScriptRoot "ensure_proxy.ps1")
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:$NOUS_PROXY_PORT/set_upstream" -Method Post `
                -ContentType 'application/json' `
                -Body '{"upstream":"gemini","model":"gemini-4-argon"}' -TimeoutSec 10 | Out-Null
            Write-Host "[claude shim] Proxy upstream -> gemini (gemini-4-argon)" -ForegroundColor DarkGreen
        } catch {
            Write-Host "[claude shim] set_upstream failed: $_. Restarting proxy..." -ForegroundColor Red
            $conn = Get-NetTCPConnection -LocalPort $NOUS_PROXY_PORT -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($conn) { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 500 }
            & (Join-Path $PSScriptRoot "ensure_proxy.ps1")
            try {
                Invoke-RestMethod -Uri "http://127.0.0.1:$NOUS_PROXY_PORT/set_upstream" -Method Post `
                    -ContentType 'application/json' `
                    -Body '{"upstream":"gemini","model":"gemini-4-argon"}' -TimeoutSec 10 | Out-Null
            } catch {
                Write-Host "[claude shim] set_upstream still failing: $_" -ForegroundColor Red
                exit 1
            }
        }
        $env:ANTHROPIC_BASE_URL = "http://127.0.0.1:$NOUS_PROXY_PORT"
        $env:ANTHROPIC_AUTH_TOKEN = "nous-proxy"
        $env:ANTHROPIC_API_KEY = ""
        $env:ANTHROPIC_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "nous"
        $env:ANTHROPIC_SMALL_FAST_MODEL = "nous"
        Write-Host "[claude shim] Launching Claude Code -> Gemini 4 Argon (gemini-4-argon)..." -ForegroundColor DarkGreen
        & $REAL @repairedArgs
    }
    "1" {
        $env:NOUS_MODEL = 'anthropic/claude-sonnet-5'
        & (Join-Path $PSScriptRoot "ensure_proxy.ps1")
        $env:ANTHROPIC_BASE_URL = "http://127.0.0.1:$NOUS_PROXY_PORT"
        $env:ANTHROPIC_AUTH_TOKEN = "nous-proxy"
        $env:ANTHROPIC_API_KEY = ""
        $env:ANTHROPIC_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "nous"
        $env:ANTHROPIC_SMALL_FAST_MODEL = "nous"
        Write-Host "[claude shim] Launching Claude Code -> Nous Sonnet 5 ($env:NOUS_MODEL)..." -ForegroundColor Green
        & $REAL @repairedArgs
    }
    "2" {
        $env:NOUS_MODEL = 'anthropic/claude-opus-5'
        & (Join-Path $PSScriptRoot "ensure_proxy.ps1")
        $env:ANTHROPIC_BASE_URL = "http://127.0.0.1:$NOUS_PROXY_PORT"
        $env:ANTHROPIC_AUTH_TOKEN = "nous-proxy"
        $env:ANTHROPIC_API_KEY = ""
        $env:ANTHROPIC_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "nous"
        $env:ANTHROPIC_SMALL_FAST_MODEL = "nous"
        Write-Host "[claude shim] Launching Claude Code -> Nous Opus ($env:NOUS_MODEL)..." -ForegroundColor Green
        & $REAL @repairedArgs
    }
    "3" {
        $env:NOUS_MODEL = 'stepfun/step-5-preview:free'
        & (Join-Path $PSScriptRoot "ensure_proxy.ps1")
        $env:ANTHROPIC_BASE_URL = "http://127.0.0.1:$NOUS_PROXY_PORT"
        $env:ANTHROPIC_AUTH_TOKEN = "nous-proxy"
        $env:ANTHROPIC_API_KEY = ""
        $env:ANTHROPIC_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "nous"
        $env:ANTHROPIC_SMALL_FAST_MODEL = "nous"
        Write-Host "[claude shim] Launching Claude Code -> Step 5 Preview Free ($env:NOUS_MODEL)..." -ForegroundColor Yellow
        & $REAL @repairedArgs
    }
    "4" {
        Write-Host "[claude shim] Launching OpenCode CLI..." -ForegroundColor Magenta
        & opencode
    }
    "5" {
        Write-Host "[claude shim] Launching Antigravity CLI (agy)..." -ForegroundColor Blue
        $agyExe = "C:\Users\froma\AppData\Local\agy\bin\agy.exe"
        if (Test-Path $agyExe) {
            & $agyExe
        } else {
            & agy
        }
    }
    "6" {
        Write-Host "[claude shim] Launching Stock Claude Code directly (Stock Anthropic API)..." -ForegroundColor Cyan
        Remove-Item env:ANTHROPIC_BASE_URL -ErrorAction SilentlyContinue
        Remove-Item env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue
        & $REAL @repairedArgs
    }
    "7" {
        $custom = Read-Host "Enter Nous model ID (e.g. stepfun/step-5-preview:free, upstage/solar-mini4:free)"
        if (-not $custom) { $custom = 'stepfun/step-5-preview:free' }
        $env:NOUS_MODEL = $custom
        & (Join-Path $PSScriptRoot "ensure_proxy.ps1")
        $env:ANTHROPIC_BASE_URL = "http://127.0.0.1:$NOUS_PROXY_PORT"
        $env:ANTHROPIC_AUTH_TOKEN = "nous-proxy"
        $env:ANTHROPIC_API_KEY = ""
        $env:ANTHROPIC_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "nous"
        $env:ANTHROPIC_SMALL_FAST_MODEL = "nous"
        Write-Host "[claude shim] Launching Claude Code -> Custom Model ($env:NOUS_MODEL)..." -ForegroundColor Green
        & $REAL @repairedArgs
    }
    "8" {
        $env:NOUS_MODEL = 'meituan/longcat-2.5-preview:free'
        & (Join-Path $PSScriptRoot "ensure_proxy.ps1")
        $env:ANTHROPIC_BASE_URL = "http://127.0.0.1:$NOUS_PROXY_PORT"
        $env:ANTHROPIC_AUTH_TOKEN = "nous-proxy"
        $env:ANTHROPIC_API_KEY = ""
        $env:ANTHROPIC_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "nous"
        $env:ANTHROPIC_SMALL_FAST_MODEL = "nous"
        Write-Host "[claude shim] Launching Claude Code -> Longcat 2.5 Free ($env:NOUS_MODEL)..." -ForegroundColor Yellow
        & $REAL @repairedArgs
    }
    "9" {
        $env:NOUS_MODEL = 'stepfun/step-3.7-flash:free'
        & (Join-Path $PSScriptRoot "ensure_proxy.ps1")
        $env:ANTHROPIC_BASE_URL = "http://127.0.0.1:$NOUS_PROXY_PORT"
        $env:ANTHROPIC_AUTH_TOKEN = "nous-proxy"
        $env:ANTHROPIC_API_KEY = ""
        $env:ANTHROPIC_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "nous"
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "nous"
        $env:ANTHROPIC_SMALL_FAST_MODEL = "nous"
        Write-Host "[claude shim] Launching Claude Code -> Step 3.7 Flash Free ($env:NOUS_MODEL)..." -ForegroundColor Yellow
        & $REAL @repairedArgs
    }
    Default {
        & $REAL @repairedArgs
    }
}

exit $LASTEXITCODE
