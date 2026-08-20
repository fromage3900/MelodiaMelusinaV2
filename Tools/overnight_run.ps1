# Overnight run - single entry point for Tier 0-3 headless checks (+ optional Tier 4 editor).
#
# Usage (from repo root or BS_GodFile):
#   powershell -File BS_GodFile/Tools/overnight_run.ps1
#   powershell -File BS_GodFile/Tools/overnight_run.ps1 -PreflightOnly
#   powershell -File BS_GodFile/Tools/overnight_run.ps1 -ContentGen -WithEditor
#
# Does NOT: auto record gates, blessing evolution, PIE --loop, or ollama pull.
param(
    [switch]$PreflightOnly,
    [switch]$ContentGen,
    [switch]$WithEditor,
    [switch]$SkipTier1,
    [switch]$SkipTier3
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$RepoRoot = Split-Path $ProjectRoot -Parent
$DeployDir = Join-Path $ProjectRoot "deploy"
$AuditDir = Join-Path $ProjectRoot "Saved\Audit"
$DateStamp = Get-Date -Format "yyyy-MM-dd"
$LogFile = Join-Path $AuditDir "overnight_run_$DateStamp.log"

$script:Tier01Failed = $false
$script:Tier4Warnings = @()

function Write-Log {
    param([string]$Message)
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding utf8
}

function Invoke-PythonStep {
    param(
        [string]$Name,
        [string[]]$Arguments,
        [switch]$Required,
        [string]$WorkingDirectory = $ProjectRoot
    )

    Write-Log "=== $Name ==="
    Write-Log ("python " + ($Arguments -join " "))
    Push-Location $WorkingDirectory
    try {
        & python @Arguments 2>&1 | ForEach-Object {
            Write-Log $_
        }
    }
    finally {
        Pop-Location
    }

    $rc = $LASTEXITCODE
    if ($rc -ne 0) {
        $msg = "$Name failed (exit $rc)"
        if ($Required) {
            Write-Log "FAIL: $msg"
            $script:Tier01Failed = $true
        }
        else {
            Write-Log "WARN: $msg"
        }
    }
    else {
        Write-Log "OK: $Name"
    }
}

function Test-MonolithReachable {
    try {
        $body = '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"monolith_status","arguments":{}}}'
        $req = [System.Net.HttpWebRequest]::Create("http://127.0.0.1:9316/mcp")
        $req.Method = "POST"
        $req.ContentType = "application/json"
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
        $req.ContentLength = $bytes.Length
        $stream = $req.GetRequestStream()
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Close()
        $resp = $req.GetResponse()
        $resp.Close()
        return $true
    }
    catch {
        return $false
    }
}

function Test-OllamaModelPresent {
    param([string]$ModelName)
    try {
        $raw = & ollama list 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) {
            return $false
        }
        return ($raw -match [regex]::Escape($ModelName))
    }
    catch {
        return $false
    }
}

$null = New-Item -ItemType Directory -Force -Path $AuditDir
Write-Log "overnight_run.ps1 start (PreflightOnly=$PreflightOnly ContentGen=$ContentGen WithEditor=$WithEditor)"
Write-Log "ProjectRoot=$ProjectRoot RepoRoot=$RepoRoot Log=$LogFile"

# --- Tier 0: offline preflight (required) ---
Write-Log "--- Tier 0: offline preflight ---"
Invoke-PythonStep -Name "ollama_health" -Arguments @("Tools/ollama_health.py", "--write-evidence") -Required
Invoke-PythonStep -Name "validate_mcp_registration" -Arguments @("Tools/validate_mcp_registration.py") -Required
Invoke-PythonStep -Name "test_melodia_mcp" -Arguments @("Tools/test_melodia_mcp.py") -Required
# Soft: contract suite + workspace health still incomplete; do not block overnight
Invoke-PythonStep -Name "run_contract_tests" -Arguments @("Tools/run_contract_tests.py")
Invoke-PythonStep -Name "echo_run validate-spec" -Arguments @("Tools/echo_run.py", "validate-spec", "specs/echo_pipeline.json") -Required
Invoke-PythonStep -Name "health.py" -Arguments @("Tools/health.py", "--json")

if ($PreflightOnly) {
    Write-Log "PreflightOnly set - skipping Tier 1+"
    Write-Log "--- STOP instructions ---"
    Write-Log "  New-Item $DeployDir\STOP_ALL -ItemType File -Force"
    Write-Log "  .\deploy\start_hermes_daemon.ps1 -Stop"
    if ($script:Tier01Failed) {
        Write-Log "OVERNIGHT RUN FAILED (Tier 0)"
        exit 1
    }
    Write-Log "OVERNIGHT RUN OK (Tier 0 only)"
    exit 0
}

if (-not $SkipTier1) {
    # --- Tier 1: Qwen + Muse MCP fleet (MATH + P0 economy scenarios) ---
    Write-Log "--- Tier 1: model fleet (Qwen + Muse Glimmer MCP) ---"
    Invoke-PythonStep -Name "run_model_fleet" -Arguments @(
        "Tools/run_model_fleet.py",
        "--models", "qwen2.5-coder:7b,qwen2.5-coder:14b,muse-glimmer-30b",
        "--timeout", "180"
    )
}

# --- Tier 2: optional content generation ---
if ($ContentGen) {
    Write-Log "--- Tier 2: content generation (single pass) ---"
    Invoke-PythonStep -Name "daemon_content_gen" -Arguments @(
        "scripts/daemon_content_gen.py", "--once"
    ) -WorkingDirectory $RepoRoot
}
else {
    Write-Log "--- Tier 2: skipped (use -ContentGen for single pass, or start fleet separately) ---"
    Write-Log "  Fleet: .\deploy\start_ollama_fleet.ps1"
    Write-Log "  Stop:  New-Item .\deploy\STOP_ALL -ItemType File -Force"
}

if (-not $SkipTier3) {
    # --- Tier 3: Hermes RunOnce ---
    Write-Log "--- Tier 3: Hermes RunOnce ---"
    Invoke-PythonStep -Name "hermes_daemon run-once" -Arguments @(
        "deploy/hermes_daemon.py", "--run-once"
    ) -Required
}

# --- Tier 4: optional editor-backed (warn-only on failure / editor down) ---
if ($WithEditor) {
    Write-Log "--- Tier 4: editor-backed gates ---"
    if (-not (Test-MonolithReachable)) {
        $msg = "Monolith :9316 not reachable - skipping Tier 4 (editor down)"
        Write-Log "WARN: $msg"
        $script:Tier4Warnings += $msg
    }
    else {
        Invoke-PythonStep -Name "echo_run status" -Arguments @("Tools/echo_run.py", "status")
        Invoke-PythonStep -Name "echo_run static_gates" -Arguments @("Tools/echo_run.py", "run", "static_gates")
        Invoke-PythonStep -Name "playtest preflight" -Arguments @("Tools/playtest_harness.py", "preflight")
        Invoke-PythonStep -Name "overnight_persona_pie_loop --once" -Arguments @(
            "Tools/overnight_persona_pie_loop.py", "--once"
        )
    }
}
else {
    Write-Log "--- Tier 4: skipped (pass -WithEditor when UE + Monolith :9316 are up) ---"
}

Write-Log "--- STOP instructions ---"
Write-Log "  New-Item $DeployDir\STOP_ALL -ItemType File -Force"
Write-Log "  .\deploy\start_hermes_daemon.ps1 -Stop"

if ($script:Tier4Warnings.Count -gt 0) {
    Write-Log "Tier 4 warnings:"
    foreach ($w in $script:Tier4Warnings) {
        Write-Log "  $w"
    }
}

if ($script:Tier01Failed) {
    Write-Log "OVERNIGHT RUN FAILED (Tier 0/1 required step failed)"
    exit 1
}

Write-Log "OVERNIGHT RUN OK"
exit 0
