# deploy/new_agent_lane.ps1 -- start an agent lane.
#
#   .\deploy\new_agent_lane.ps1 -Lane cline -Task houdini-deposition
#   .\deploy\new_agent_lane.ps1 -Lane pi -Task hybrid-combat -Paths Source/BS_GodFile
#
# What this does, and deliberately does NOT do:
#
#   * creates ONE git worktree for this lane, on a DETACHED HEAD cut from origin/main
#   * pins the tip with a ref under refs/agents/<lane> -- a ref, not a branch, so it
#     never appears in `git branch` and never accumulates
#   * registers the lane and its claimed paths with Tools/agent_lane_registry.py
#
#   * it does NOT create a branch
#   * it does NOT touch the primary checkout
#   * -Reuse NEVER resets an existing refs/agents/<lane> to origin/main
#
# Why detached: several agents share this repository. Branches accumulate and get
# forgotten; refs do not. The lane's work is durable because the ref is updated on
# every commit (see docs), and it is landed by the integrator, never by the agent.
#
# See Docs/Production/MULTI_AGENT_LANES.md.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Lane,
    [string]$Task = "",
    [string[]]$Paths = @(),
    [string[]]$Globs = @(),
    [string]$Base = "origin/main",
    [string]$Tier = "",
    [switch]$Reuse
)

$ErrorActionPreference = "Stop"

# Native tools (git, python) write progress to stderr. With $ErrorActionPreference='Stop',
# PowerShell promotes that to a terminating error and aborts the script mid-way -- which is
# exactly what happened on the first run here. All native calls therefore go through this
# helper: stderr becomes captured output, and only the exit code decides success.
function Invoke-Native {
    param([string]$Exe, [string[]]$Arguments, [switch]$AllowFail)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $lines = @(& $Exe @Arguments 2>&1 | ForEach-Object { [string]$_ })
        $code = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    } finally {
        $ErrorActionPreference = $prev
    }
    if (-not $AllowFail -and $code -ne 0) {
        throw "$Exe $($Arguments -join ' ') failed (exit $code)`n$($lines -join [Environment]::NewLine)"
    }
    return [pscustomobject]@{ Code = $code; Lines = $lines }
}

$Root = Split-Path -Parent $PSScriptRoot
$Worktrees = Join-Path (Split-Path -Parent $Root) "_worktrees"
$Registry = Join-Path $Root "Tools\agent_lane_registry.py"
$Authority = Join-Path $Root "Tools\agent_lane_local_authority.py"
$LaneSlug = ($Lane -replace '[^A-Za-z0-9\-_]', '-').ToLower()
$LanePath = Join-Path $Worktrees "lane-$LaneSlug"
$LaneRef = "refs/agents/$LaneSlug"

if (-not (Test-Path $Registry)) {
    throw "Tools/agent_lane_registry.py is missing; run this from the repository root."
}
if (-not (Test-Path $Authority)) {
    throw "Tools/agent_lane_local_authority.py is missing; run this from the repository root."
}

Write-Host "==> lane '$LaneSlug'  task='$Task'  base=$Base" -ForegroundColor Cyan
Invoke-Native git @('-C', $Root, 'fetch', 'origin') | Out-Null
$BaseSha = (Invoke-Native git @('-C', $Root, 'rev-parse', $Base)).Lines[0].Trim()
Write-Host "    base sha $BaseSha"

$ReusingExistingLane = Test-Path $LanePath
if ($ReusingExistingLane) {
    if (-not $Reuse) {
        throw @"
Lane worktree already exists: $LanePath
Re-run with -Reuse to reuse it without resetting refs/agents/$LaneSlug.
Removing a lane worktree requires explicit owner approval (do not auto-clean recovery lanes).
"@
    }
    Write-Host "    reusing existing worktree" -ForegroundColor Yellow
} else {
    New-Item -ItemType Directory -Path $Worktrees -Force | Out-Null
    # GIT_LFS_SKIP_SMUDGE avoids pulling gigabytes of LFS payload into a lane that may
    # not need it. Text/code lanes are the common case.
    $env:GIT_LFS_SKIP_SMUDGE = "1"
    $add = Invoke-Native git @('-C', $Root, 'worktree', 'add', '--detach', $LanePath, $BaseSha)
    $add.Lines | ForEach-Object { Write-Host "    $_" }
    Write-Host "    worktree $LanePath (detached at $($BaseSha.Substring(0,8)))"
}

# Reuse must never reset an existing lane ref to origin/main.
if ($ReusingExistingLane) {
    $probe = Invoke-Native git @('-C', $LanePath, 'rev-parse', '--verify', '--quiet', $LaneRef) -AllowFail
    $RefSha = ""
    $HeadSha = ""
    if ($probe.Code -eq 0) {
        $RefSha = (Invoke-Native git @('-C', $LanePath, 'rev-parse', $LaneRef)).Lines[0].Trim()
        $HeadSha = (Invoke-Native git @('-C', $LanePath, 'rev-parse', 'HEAD')).Lines[0].Trim()
    }
    $reuseArgs = @(
        $Authority, 'reuse',
        '--lane-ref', $LaneRef
    )
    if ($probe.Code -eq 0) {
        $reuseArgs += @('--ref-exists', '--ref-sha', $RefSha, '--head-sha', $HeadSha)
    }
    $reuseEval = Invoke-Native python $reuseArgs -AllowFail
    $reuseEval.Lines | ForEach-Object { Write-Host "    $_" }
    if ($reuseEval.Code -ne 0) {
        throw "SAFE STOP: lane reuse refused by Tools/agent_lane_local_authority.py (exit $($reuseEval.Code)). Preserve worktree HEAD, $LaneRef and reflog; do not reinitialize."
    }
    Write-Host "    preserved existing lane ref $LaneRef ($($RefSha.Substring(0,8)))" -ForegroundColor Yellow
} else {
    Invoke-Native git @('-C', $LanePath, 'update-ref', $LaneRef, $BaseSha) | Out-Null
    $initArgs = @($Registry, "init", "--lane", $LaneSlug,
                  "--worktree", $LanePath, "--branch", $LaneRef)
    if ($Tier) { $initArgs += @("--tier", $Tier) }
    (Invoke-Native python $initArgs).Lines | ForEach-Object { Write-Host "    $_" }
}

if ($Paths.Count -gt 0 -or $Globs.Count -gt 0) {
    $claimArgs = @($Registry, "claim", "--lane", $LaneSlug)
    foreach ($p in $Paths) { $claimArgs += @("--path", $p) }
    foreach ($g in $Globs) { $claimArgs += @("--glob", $g) }
    $claim = Invoke-Native python $claimArgs -AllowFail
    $claim.Lines | ForEach-Object { Write-Host "    $_" }
    if ($claim.Code -ne 0) {
        throw "claim was refused; another live lane owns one of those paths."
    }
}

Write-Host ""
Write-Host "Lane ready. Work here, not in the primary checkout:" -ForegroundColor Green
Write-Host "    cd '$LanePath'"
Write-Host ""
Write-Host "Pin your work after each commit so it cannot be lost:" -ForegroundColor Green
Write-Host "    git -C '$LanePath' update-ref $LaneRef HEAD"
Write-Host ""
Write-Host "Then hand it to the integrator (do not push, do not PR):" -ForegroundColor Green
Write-Host "    .\deploy\land_agent_lane.ps1 -Lane $LaneSlug"
