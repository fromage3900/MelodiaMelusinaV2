param(
    [switch]$InstallPonytail,
    [switch]$RequireJev,
    [switch]$SkipOpenCodeProbe
)

$ErrorActionPreference = "Stop"

$deploy = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $deploy "..")).Path
Set-Location $repoRoot

$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Pass([string]$Message) { Write-Host "PASS  $Message" -ForegroundColor Green }
function Warn([string]$Message) { $warnings.Add($Message); Write-Host "WARN  $Message" -ForegroundColor Yellow }
function Fail([string]$Message) { $failures.Add($Message); Write-Host "FAIL  $Message" -ForegroundColor Red }

function Require-Path([string]$Path, [string]$Label) {
    if (Test-Path -LiteralPath $Path) { Pass "$Label -> $Path"; return $true }
    Fail "$Label missing -> $Path"
    return $false
}

Write-Host "=== Melodia Rider Engineering Cockpit ==="
Write-Host "Repo: $repoRoot"
Write-Host ""

# ---------------------------------------------------------------------------
# Git identity / branch lock preflight
# ---------------------------------------------------------------------------
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Fail "git is not available on PATH"
} else {
    $branch = (& git branch --show-current 2>$null).Trim()
    $head = (& git rev-parse HEAD 2>$null).Trim()
    $status = @(& git status --porcelain 2>$null)

    if ($branch) { Pass "git branch: $branch" } else { Warn "git branch is detached/unknown" }
    if ($head) { Pass "git HEAD: $head" } else { Fail "could not resolve git HEAD" }
    if ($status.Count -eq 0) {
        Pass "working tree clean"
    } else {
        Warn ("working tree has {0} porcelain entries; cockpit agents must not change branch/reset/clean implicitly" -f $status.Count)
    }
}

# ---------------------------------------------------------------------------
# Project canonical files
# ---------------------------------------------------------------------------
Require-Path (Join-Path $repoRoot "AGENTS.md") "AGENTS front door" | Out-Null
Require-Path (Join-Path $repoRoot "CURRENT_STATE.md") "status authority" | Out-Null
Require-Path (Join-Path $repoRoot "qodana.yaml") "Qodana authority" | Out-Null
Require-Path (Join-Path $repoRoot ".opencode\opencode.jsonc") "OpenCode project config" | Out-Null
Require-Path (Join-Path $repoRoot "Docs\Production\RIDER_UE58_CANONICAL_WORKFLOW.md") "Rider runbook" | Out-Null
Require-Path (Join-Path $repoRoot "Docs\Production\RIDER_PONYTAIL_ENGINEERING_COCKPIT.md") "cockpit runbook" | Out-Null
Require-Path (Join-Path $repoRoot "Docs\Production\JEV_CANONICAL_WORKFLOW.md") "Jev runbook" | Out-Null

# ---------------------------------------------------------------------------
# Rider / OpenCode
# ---------------------------------------------------------------------------
$riderCandidates = @(
    (Get-Command rider64.exe -ErrorAction SilentlyContinue),
    (Get-Command rider.exe -ErrorAction SilentlyContinue),
    (Get-Command rider -ErrorAction SilentlyContinue)
) | Where-Object { $_ }

if ($riderCandidates.Count -gt 0) {
    Pass "Rider command available: $($riderCandidates[0].Source)"
} else {
    Warn "Rider command not on PATH; Toolbox-installed Rider may still be usable from GUI"
}

if (-not $SkipOpenCodeProbe) {
    $openCode = Get-Command opencode -ErrorAction SilentlyContinue
    if ($openCode) {
        Pass "OpenCode available: $($openCode.Source)"
        try {
            $version = (& opencode --version 2>&1 | Select-Object -First 1)
            if ($version) { Write-Host "      $version" }
        } catch {
            Warn "OpenCode exists but version probe failed"
        }
    } else {
        Fail "OpenCode missing from PATH"
    }
} else {
    Warn "OpenCode probe skipped by request"
}

# ---------------------------------------------------------------------------
# Ponytail local vendor dependency
# ---------------------------------------------------------------------------
$ponyRoot = Join-Path $repoRoot "Tools\vendor\ponytail-ue58"
$ponyPlugin = Join-Path $ponyRoot ".opencode\plugins\ponytail.mjs"
$ponyAgents = Join-Path $ponyRoot "AGENTS.md"
$ponyRepo = "https://github.com/prielgaier/ponytail-ue58.git"

if (-not (Test-Path -LiteralPath $ponyRoot) -and $InstallPonytail) {
    $parent = Split-Path $ponyRoot -Parent
    New-Item -ItemType Directory -Force -Path $parent | Out-Null

    Write-Host "Installing machine-local Ponytail UE5.8 vendor checkout..."
    & git clone --depth 1 $ponyRepo $ponyRoot
    if ($LASTEXITCODE -ne 0) {
        Fail "Ponytail clone failed"
    }
}

if (Test-Path -LiteralPath $ponyRoot) {
    Pass "Ponytail vendor checkout present"
    Require-Path $ponyPlugin "Ponytail OpenCode plugin" | Out-Null
    Require-Path $ponyAgents "Ponytail Unreal rules" | Out-Null

    if (Test-Path -LiteralPath (Join-Path $ponyRoot ".git")) {
        try {
            $remote = (& git -C $ponyRoot remote get-url origin 2>$null).Trim()
            if ($remote) { Pass "Ponytail origin: $remote" }
        } catch {
            Warn "Ponytail checkout exists but origin could not be read"
        }
    }
} else {
    Fail "Ponytail machine-local checkout missing. Rehydrate explicitly with: .\deploy\verify_rider_cockpit.ps1 -InstallPonytail"
}

# Verify tracked OpenCode config references the expected Ponytail plugin.
$openCodeConfig = Join-Path $repoRoot ".opencode\opencode.jsonc"
if (Test-Path -LiteralPath $openCodeConfig) {
    $text = Get-Content -LiteralPath $openCodeConfig -Raw
    if ($text -match "ponytail-ue58/.opencode/plugins/ponytail\.mjs") {
        Pass "OpenCode config references Ponytail plugin"
    } else {
        Fail "OpenCode config no longer references canonical Ponytail plugin path"
    }

    if ($text -match '"monolith"') {
        Pass "OpenCode config exposes Monolith"
    } else {
        Fail "OpenCode config does not expose Monolith"
    }
}

# ---------------------------------------------------------------------------
# Unreal editor / single-writer safety
# ---------------------------------------------------------------------------
$editors = @(Get-Process UnrealEditor -ErrorAction SilentlyContinue)
if ($editors.Count -eq 0) {
    Pass "Unreal Editor closed (safe for full native build)"
} elseif ($editors.Count -eq 1) {
    Pass "exactly one Unreal Editor process running (PID $($editors[0].Id))"
} else {
    Fail "multiple Unreal Editor processes detected: $($editors.Id -join ', ')"
}

# ---------------------------------------------------------------------------
# Qodana tracked contract
# ---------------------------------------------------------------------------
$qodanaPath = Join-Path $repoRoot "qodana.yaml"
if (Test-Path -LiteralPath $qodanaPath) {
    $q = Get-Content -LiteralPath $qodanaPath -Raw
    if ($q -match "(?m)^ide:\s*QDJB\s*$") { Pass "Qodana IDE mode = QDJB" } else { Fail "qodana.yaml lost ide: QDJB" }
    if ($q -match "qodana\.recommended") { Pass "Qodana profile = qodana.recommended" } else { Fail "qodana.yaml lost qodana.recommended profile" }
}

# ---------------------------------------------------------------------------
# Jev availability
# ---------------------------------------------------------------------------
$jevKeyPresent = -not [string]::IsNullOrWhiteSpace($env:TYPESAFE_API_KEY)
if ($jevKeyPresent) {
    Pass "TYPESAFE_API_KEY present in process environment (value not printed)"
} elseif ($RequireJev) {
    Fail "TYPESAFE_API_KEY missing but -RequireJev was requested"
} else {
    Warn "TYPESAFE_API_KEY not present; deterministic fallback/test lanes may work but this is not jev-live evidence"
}

# ---------------------------------------------------------------------------
# RiderLink / UnrealLink reminder
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "RiderLink:"
Write-Host "  Rider/UnrealLink should manage RiderLink for the project/engine."
Write-Host "  Verify in Rider: Settings -> Languages & Frameworks -> Unreal Engine."
Write-Host "  A source test is not live-editor proof until the RiderLink/UE test session actually runs."

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "Canonical cockpit:"
Write-Host "  Rider intelligence/UHT -> Ponytail/OpenCode -> Jev when judgment is needed"
Write-Host "  -> Qodana -> UBT -> RiderLink -> Monolith/PIE -> package/restart evidence"
Write-Host ""

if ($warnings.Count -gt 0) {
    Write-Host "Warnings:"
    $warnings | ForEach-Object { Write-Host "  - $_" }
}

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "COCKPIT: FAIL ($($failures.Count) blocking issue(s))" -ForegroundColor Red
    $failures | ForEach-Object { Write-Host "  - $_" }
    exit 1
}

Write-Host ""
Write-Host "COCKPIT: PASS" -ForegroundColor Green
exit 0
