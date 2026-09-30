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

$Root = Split-Path -Parent $PSScriptRoot
$Worktrees = Join-Path (Split-Path -Parent $Root) "_worktrees"
$LaneSlug = ($Lane -replace '[^A-Za-z0-9\-_]', '-').ToLower()
$LanePath = Join-Path $Worktrees "lane-$LaneSlug"
$LaneRef = "refs/agents/$LaneSlug"

if (-not (Test-Path (Join-Path $Root "Tools\agent_lane_registry.py"))) {
    throw "Tools/agent_lane_registry.py is missing; run this from the repository root."
}

Write-Host "==> lane '$LaneSlug'  task='$Task'  base=$Base" -ForegroundColor Cyan
& git -C $Root fetch --prune origin 2>&1 | Out-String | Write-Verbose
$BaseSha = (& git -C $Root rev-parse $Base).Trim()
Write-Host "    base sha $BaseSha"

if (Test-Path $LanePath) {
    if (-not $Reuse) {
        throw "Lane worktree already exists: $LanePath`nRe-run with -Reuse to reuse it, or remove it with: git worktree remove '$LanePath'"
    }
    Write-Host "    reusing existing worktree" -ForegroundColor Yellow
} else {
    New-Item -ItemType Directory -Path $Worktrees -Force | Out-Null
    # GIT_LFS_SKIP_SMUDGE avoids pulling gigabytes of LFS payload into a lane that may
    # not need it. Text/code lanes are the common case.
    $env:GIT_LFS_SKIP_SMUDGE = "1"
    & git -C $Root worktree add --detach $LanePath $BaseSha 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -ne 0) { throw "git worktree add failed ($LASTEXITCODE)" }
    Write-Host "    worktree $LanePath (detached at $($BaseSha.Substring(0,8)))"
}

& git -C $LanePath update-ref $LaneRef $BaseSha 2>&1 | Out-Null

$initArgs = @("Tools/agent_lane_registry.py", "init", "--lane", $LaneSlug,
              "--worktree", $LanePath, "--branch", $LaneRef)
if ($Tier) { $initArgs += @("--tier", $Tier) }
& python @initArgs

if ($Paths.Count -gt 0 -or $Globs.Count -gt 0) {
    $claimArgs = @("Tools/agent_lane_registry.py", "claim", "--lane", $LaneSlug)
    foreach ($p in $Paths) { $claimArgs += @("--path", $p) }
    foreach ($g in $Globs) { $claimArgs += @("--glob", $g) }
    & python @claimArgs
    if ($LASTEXITCODE -ne 0) { throw "claim was refused; another live lane owns one of those paths." }
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
