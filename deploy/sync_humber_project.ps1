# Melodia Humber canonical project synchronizer.
#
# Purpose:
#   One entry point for a Humber workstation:
#     1) sync Git main safely
#     2) hydrate HumberSemester LFS
#     3) connect to the owner's reachable P4 depot
#     4) create/verify a machine-specific P4 client
#     5) preview and optionally apply creative-content sync
#
# Safety:
#   - no reset/rebase/clean/stash/force operations
#   - no p4 reconcile/submit/unshelve
#   - no password handling
#   - Content/Python stays Git-owned
#
# Examples:
#   .\deploy\sync_humber_project.ps1 -Mode Check
#   .\deploy\sync_humber_project.ps1 -Mode Sync -P4Port "100.64.0.10:1666" -P4User "brennan"
#   .\deploy\sync_humber_project.ps1 -Mode Sync -P4Port "home-pc.tailnet.ts.net:1666" -P4User "brennan" -ApplyP4
[CmdletBinding()]
param(
    [ValidateSet("Check","Sync")]
    [string]$Mode = "Check",

    [string]$P4Port = $env:MELODIA_P4PORT,

    [string]$P4User = $env:MELODIA_P4USER,

    [string]$P4Client = "",

    [switch]$ApplyP4,

    [switch]$SkipGitLfs
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ReportDir = Join-Path $ProjectRoot "Saved\Workstation"
$Machine = if ($env:COMPUTERNAME) { $env:COMPUTERNAME } else { "machine" }
$ReportPath = Join-Path $ReportDir ($Machine + "-humber-canonical-sync.json")
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null

function Command-Exists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-P4 {
    param(
        [string[]]$Arguments,
        [switch]$AllowFailure
    )
    $base = @()
    if (-not [string]::IsNullOrWhiteSpace($P4Port)) { $base += @("-p", $P4Port) }
    if (-not [string]::IsNullOrWhiteSpace($P4User)) { $base += @("-u", $P4User) }
    if (-not [string]::IsNullOrWhiteSpace($P4Client)) { $base += @("-c", $P4Client) }

    $lines = @(& p4 @base @Arguments 2>&1 | ForEach-Object { [string]$_ })
    $code = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    $result = [pscustomobject]@{
        Code = $code
        Lines = $lines
        Text = ($lines -join [Environment]::NewLine).Trim()
    }
    if (-not $AllowFailure -and $code -ne 0) {
        throw ("p4 " + ($Arguments -join " ") + " failed with exit " + $code + [Environment]::NewLine + $result.Text)
    }
    return $result
}

function New-P4ClientSpec {
    $root = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd("\")
    return @"
Client: $P4Client
Owner: $P4User
Host: $Machine
Description:
    Melodia Humber workstation client managed by deploy/sync_humber_project.ps1.
Root: $root
Options: noallwrite noclobber nocompress unlocked nomodtime normdir
SubmitOptions: submitunchanged
LineEnd: local
View:
    //Melodia/Content/... //$P4Client/Content/...
    -//Melodia/Content/Python/... //$P4Client/Content/Python/...
    //Melodia/Exports/... //$P4Client/Exports/...
    //Melodia/RawArt/... //$P4Client/RawArt/...
"@
}

$report = [ordered]@{
    schema = "melodia.humber_canonical_sync.v1"
    generated_at = (Get-Date).ToString("o")
    machine = $Machine
    project_root = $ProjectRoot
    mode = $Mode
    git = [ordered]@{}
    p4 = [ordered]@{
        requested_port = $P4Port
        user = $P4User
        client = $P4Client
        available = $false
        reachable = $false
        login_valid = $false
        client_ready = $false
        preview_clean = $false
        apply_requested = [bool]$ApplyP4
        apply_completed = $false
        hold_reason = ""
    }
}

# ---- Git / LFS ----
if (-not (Command-Exists "git")) {
    throw "Git is not available on PATH."
}

$top = (& git -C $ProjectRoot rev-parse --show-toplevel 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "This script must run from a valid Melodia Git checkout." }

$expected = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd("\","/")
$actual = [IO.Path]::GetFullPath($top).TrimEnd("\","/")
if ($expected -ne $actual) {
    throw "Git root '$actual' does not match project root '$expected'."
}

$remote = (& git -C $ProjectRoot remote get-url origin 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $remote -notmatch "fromage3900[/:]MelodiaMelusinaV2(\.git)?$") {
    throw "origin is missing or does not point to fromage3900/MelodiaMelusinaV2. Found '$remote'."
}

$dirtyBefore = @(& git -C $ProjectRoot status --short)
$branchBefore = (& git -C $ProjectRoot branch --show-current | Out-String).Trim()
$headBefore = (& git -C $ProjectRoot rev-parse HEAD | Out-String).Trim()

$report.git.remote = $remote
$report.git.branch_before = $branchBefore
$report.git.head_before = $headBefore
$report.git.dirty_before = $dirtyBefore

if ($dirtyBefore.Count -gt 0) {
    $report.git.state = "HOLD_DIRTY"
    $report.p4.hold_reason = "Git worktree is dirty; canonical sync refuses to hide or overwrite local work."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "HOLD: Git worktree is dirty." -ForegroundColor Red
    $dirtyBefore | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    Write-Host "Report: $ReportPath"
    exit 2
}

if ($Mode -eq "Sync") {
    $syncScript = Join-Path $ProjectRoot "deploy\sync_workstation.ps1"
    $syncArgs = @("-Mode","Sync","-Target","Main")
    if (-not $SkipGitLfs) {
        $syncArgs += @("-LfsProfile","HumberSemester")
    } else {
        $syncArgs += @("-LfsProfile","None")
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $syncScript @syncArgs
    if ($LASTEXITCODE -ne 0) {
        $report.git.state = "HOLD_GIT_SYNC"
        $report.p4.hold_reason = "Git/LFS synchronization did not reach a safe synced state."
        $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
        Write-Host "HOLD: Git/LFS sync failed. P4 was not touched." -ForegroundColor Red
        exit 3
    }
} else {
    & git -C $ProjectRoot fetch --prune origin
    if ($LASTEXITCODE -ne 0) { throw "git fetch origin failed." }
}

$branchAfter = (& git -C $ProjectRoot branch --show-current | Out-String).Trim()
$headAfter = (& git -C $ProjectRoot rev-parse HEAD | Out-String).Trim()
$delta = (& git -C $ProjectRoot rev-list --left-right --count HEAD...origin/main | Out-String).Trim()
$dirtyAfter = @(& git -C $ProjectRoot status --short)

$report.git.branch_after = $branchAfter
$report.git.head_after = $headAfter
$report.git.delta_vs_origin_main = $delta
$report.git.dirty_after = $dirtyAfter
$report.git.state = if ($branchAfter -eq "main" -and $delta -match "^0\s+0$" -and $dirtyAfter.Count -eq 0) { "SYNCED" } else { "HOLD_NOT_CANONICAL" }

if ($report.git.state -ne "SYNCED") {
    $report.p4.hold_reason = "Git is not clean main == origin/main."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "HOLD: Git is not canonical after sync." -ForegroundColor Red
    Write-Host "Branch: $branchAfter  delta: $delta  dirty: $($dirtyAfter.Count)"
    exit 4
}

# ---- Perforce ----
if (-not (Command-Exists "p4")) {
    $report.p4.hold_reason = "p4 CLI is not available on PATH."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "Git/LFS canonical: PASS" -ForegroundColor Green
    Write-Host "P4: HOLD (CLI unavailable)" -ForegroundColor Yellow
    Write-Host "Report: $ReportPath"
    exit 5
}
$report.p4.available = $true

if ([string]::IsNullOrWhiteSpace($P4Port)) {
    $report.p4.hold_reason = "No reachable P4 endpoint supplied. Set MELODIA_P4PORT or pass -P4Port host:1666."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "Git/LFS canonical: PASS" -ForegroundColor Green
    Write-Host "P4: HOLD (no P4Port)" -ForegroundColor Yellow
    Write-Host "Report: $ReportPath"
    exit 6
}

if ($P4Port -match "^(localhost|127\.0\.0\.1):") {
    $report.p4.hold_reason = "A loopback P4 endpoint cannot reach the home depot from Humber."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "P4: HOLD — do not use localhost from Humber." -ForegroundColor Red
    exit 7
}

if ([string]::IsNullOrWhiteSpace($P4User)) {
    $report.p4.hold_reason = "No P4 user supplied. Set MELODIA_P4USER or pass -P4User."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "P4: HOLD (no P4 user)" -ForegroundColor Yellow
    exit 8
}

if ([string]::IsNullOrWhiteSpace($P4Client)) {
    $safeMachine = ($Machine -replace "[^A-Za-z0-9_-]", "_")
    $P4Client = "Melodia_Humber_$safeMachine"
    $report.p4.client = $P4Client
}

$info = Invoke-P4 -Arguments @("info","-s") -AllowFailure
$report.p4.info = $info.Text
if ($info.Code -ne 0) {
    $report.p4.hold_reason = "Cannot reach P4 server at $P4Port."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "Git/LFS canonical: PASS" -ForegroundColor Green
    Write-Host "P4: HOLD — endpoint unreachable: $P4Port" -ForegroundColor Red
    Write-Host $info.Text
    exit 9
}
$report.p4.reachable = $true

$login = Invoke-P4 -Arguments @("login","-s") -AllowFailure
$report.p4.login_status = $login.Text
if ($login.Code -ne 0) {
    $report.p4.hold_reason = "P4 endpoint is reachable, but login ticket is missing or expired. Owner login required."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "P4: HOLD — server reachable; login required." -ForegroundColor Yellow
    exit 10
}
$report.p4.login_valid = $true

$latest = Invoke-P4 -Arguments @("changes","-m","1","//Melodia/...") -AllowFailure
if ($latest.Code -ne 0) {
    $report.p4.hold_reason = "Server is reachable but //Melodia depot is not readable."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "P4: HOLD — //Melodia not readable." -ForegroundColor Red
    exit 11
}
$report.p4.latest_change = $latest.Text

# Create/update the dedicated client spec deterministically.
$spec = New-P4ClientSpec
$specResult = $spec | & p4 -p $P4Port -u $P4User client -i 2>&1
$specCode = $LASTEXITCODE
$report.p4.client_spec_result = ($specResult | Out-String).Trim()
if ($specCode -ne 0) {
    $report.p4.hold_reason = "Could not create/update dedicated Humber P4 client."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "P4: HOLD — client configuration failed." -ForegroundColor Red
    exit 12
}
$report.p4.client_ready = $true

# Verify Content/Python is excluded.
$wherePython = Invoke-P4 -Arguments @("where","//Melodia/Content/Python/...") -AllowFailure
$report.p4.content_python_where = $wherePython.Text
$pythonExcluded = ($wherePython.Code -ne 0) -or ($wherePython.Text -match "not in client view|excluded|^-")
if (-not $pythonExcluded) {
    $report.p4.hold_reason = "Content/Python appears mapped in P4; ownership contract violation."
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "P4: HOLD — Content/Python is not safely excluded." -ForegroundColor Red
    Write-Host $wherePython.Text
    exit 13
}

$previewTargets = @("//Melodia/Content/...","//Melodia/Exports/...","//Melodia/RawArt/...")
$previewLines = @()
$previewFailed = $false
foreach ($target in $previewTargets) {
    $r = Invoke-P4 -Arguments @("sync","-n",$target) -AllowFailure
    $previewLines += @("### $target") + $r.Lines
    if ($r.Code -ne 0) { $previewFailed = $true }
}

$pythonLeak = @($previewLines | Where-Object { $_ -match "(?i)Content[/\\]Python" })
$report.p4.preview_count = $previewLines.Count
$report.p4.preview_sample = @($previewLines | Select-Object -First 80)
$report.p4.preview_python_leaks = $pythonLeak

if ($previewFailed -or $pythonLeak.Count -gt 0) {
    $report.p4.hold_reason = if ($pythonLeak.Count -gt 0) { "P4 preview contains Git-owned Content/Python." } else { "One or more P4 preview commands failed." }
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "P4: HOLD — preview not clean." -ForegroundColor Red
    exit 14
}
$report.p4.preview_clean = $true

if ($ApplyP4) {
    if ($Mode -ne "Sync") {
        throw "-ApplyP4 requires -Mode Sync."
    }
    foreach ($target in $previewTargets) {
        $r = Invoke-P4 -Arguments @("sync",$target) -AllowFailure
        if ($r.Code -ne 0) {
            $report.p4.hold_reason = "P4 sync failed while applying $target."
            $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
            Write-Host "P4: PARTIAL/HOLD — sync failed for $target." -ForegroundColor Red
            exit 15
        }
    }
    $report.p4.apply_completed = $true
}

$report.p4.hold_reason = ""
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8

Write-Host ""
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host " MELODIA HUMBER CANONICAL SYNC " -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "Git/main:     PASS ($headAfter)" -ForegroundColor Green
Write-Host "Git LFS:      $(if ($SkipGitLfs) { 'SKIPPED' } else { 'HumberSemester synced' })"
Write-Host "P4 endpoint:  PASS ($P4Port)" -ForegroundColor Green
Write-Host "P4 client:    PASS ($P4Client)" -ForegroundColor Green
Write-Host "P4 preview:   PASS" -ForegroundColor Green
Write-Host "P4 applied:   $($report.p4.apply_completed)"
Write-Host "Report:       $ReportPath"

exit 0
