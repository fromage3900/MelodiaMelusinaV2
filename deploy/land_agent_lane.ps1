# deploy/land_agent_lane.ps1 -- the integrator. Lands lane work on main.
#
#   .\deploy\land_agent_lane.ps1 -Lane cline
#   .\deploy\land_agent_lane.ps1 -All
#   .\deploy\land_agent_lane.ps1 -All -DryRun
#
# This is the only path that moves `main`. Agents never push and never open a PR:
# they commit in their lane worktree and pin the tip with refs/agents/<lane>.
#
# How it lands, and why the branch count stays at zero for you:
#
#   1. compute the lane's bounded delta:  origin/main..refs/agents/<lane>
#   2. push that ref straight to a temporary remote branch name
#      (git push origin refs/agents/<lane>:refs/heads/docs/land-<lane>-<stamp>)
#      -- no local branch is ever created
#   3. open a PR, rebase-merge it, delete the temporary branch
#   4. fast-forward the primary checkout to origin/main
#
# The temporary branch lives for seconds and is deleted in the same run. Step 2 works
# from the lane worktree, so the primary checkout is never used as a staging area.
#
# `main` is protected by .githooks/pre-push, so a direct push is impossible from here
# too -- that is intentional and this script does not work around it.
[CmdletBinding()]
param(
    [string]$Lane = "",
    [switch]$All,
    [switch]$DryRun,
    [switch]$KeepRemoteBranch,
    [int]$MaxWaitSeconds = 120
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Registry = Join-Path $Root "Tools\agent_lane_registry.py"
$RepoSlug = "fromage3900/MelodiaMelusinaV2"

if (-not (Test-Path $Registry)) { throw "Tools/agent_lane_registry.py is missing." }
if (-not $Lane -and -not $All) { throw "Pass -Lane <id> or -All." }

$env:GH_TOKEN = (& gh auth token 2>$null)
$env:GIT_TERMINAL_PROMPT = "0"
if (-not $env:GH_TOKEN) { throw "gh is not authenticated; run: gh auth login" }

function Get-Lanes {
    $dir = Join-Path $Root ".agents\lanes"
    if (-not (Test-Path $dir)) { return @() }
    Get-ChildItem $dir -Filter *.json | ForEach-Object {
        Get-Content $_.FullName -Raw | ConvertFrom-Json
    }
}

function Sync-Primary {
    & git -C $Root fetch --prune origin 2>&1 | Out-String | Write-Verbose
    $branch = (& git -C $Root branch --show-current).Trim()
    if ($branch -ne "main") {
        Write-Host "    NOTE: primary is on '$branch', not main; not fast-forwarding." -ForegroundColor Yellow
        return
    }
    & git -C $Root merge --ff-only origin/main 2>&1 | ForEach-Object { Write-Host "    $_" }
}

function Invoke-LandOne($lane) {
    $id = [string]$lane.lane
    $ref = [string]$lane.branch
    $wt = [string]$lane.worktree

    Write-Host "==> landing lane '$id'" -ForegroundColor Cyan
    if (-not $ref) { $ref = "refs/agents/$id" }

    if (-not (Test-Path $wt)) {
        Write-Host "    SKIP: lane worktree is gone ($wt)" -ForegroundColor Yellow
        return $false
    }
    if (-not (& git -C $wt rev-parse --verify --quiet $ref)) {
        Write-Host "    SKIP: ref $ref does not exist" -ForegroundColor Yellow
        return $false
    }

    & git -C $wt fetch --prune origin 2>&1 | Out-String | Write-Verbose
    $count = (& git -C $wt rev-list --count "origin/main..$ref").Trim()
    if ([int]$count -eq 0) {
        Write-Host "    nothing to land (lane delta is empty)" -ForegroundColor DarkGray
        return $false
    }
    Write-Host "    delta: $count commit(s) not on origin/main"

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $temp = "docs/land-$id-$stamp"
    $sha = (& git -C $wt rev-parse $ref).Trim()

    if ($DryRun) {
        Write-Host "    DRY RUN: would push $ref ($($sha.Substring(0,8))) -> refs/heads/$temp, PR, merge, delete." -ForegroundColor Yellow
        return $false
    }

    # Push the lane REF as a temporary branch. No local branch is created at any point.
    & git -C $wt push origin "$ref`:refs/heads/$temp" 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -ne 0) { throw "push of $ref failed ($LASTEXITCODE)" }

    $prUrl = (& gh pr create --repo $RepoSlug --base main --head $temp `
        --title "lane($id): land $count commit(s)" `
        --body "Landed by deploy/land_agent_lane.ps1 from ``$ref`` at ``$sha``.`n`nThe agent that authored this did not push and did not open this PR." 2>&1 | Select-Object -Last 1)
    Write-Host "    PR $prUrl"
    $prNumber = (& gh pr list --repo $RepoSlug --head $temp --state open --json number --jq '.[0].number').Trim()
    if (-not $prNumber) { throw "could not resolve the PR number for $temp" }

    # Give CI a moment; the branch-lifecycle guard runs on pull_request.
    Start-Sleep -Seconds 5
    & gh pr merge $prNumber --repo $RepoSlug --rebase 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    merge did not complete; inspect https://github.com/$RepoSlug/pull/$prNumber" -ForegroundColor Yellow
        return $false
    }

    if (-not $KeepRemoteBranch) {
        & git -C $wt push origin --delete $temp 2>&1 | ForEach-Object { Write-Host "    $_" }
    }

    Sync-Primary
    Write-Host "    landed $($sha.Substring(0,8)) on main" -ForegroundColor Green
    return $true
}

$targets = if ($All) { Get-Lanes } else {
    $found = Get-Lanes | Where-Object { $_.lane -eq $Lane }
    if (-not $found) { throw "lane '$Lane' is not registered. Run .\deploy\new_agent_lane.ps1 -Lane $Lane" }
    $found
}
if (-not $targets) { throw "no lanes registered" }

$landed = 0
foreach ($lane in $targets) {
    if (Invoke-LandOne $lane) { $landed++ }
}
Write-Host ""
Write-Host "landed $landed lane(s)." -ForegroundColor Green

$state = (& git -C $Root rev-parse --short HEAD).Trim()
$origin = (& git -C $Root rev-parse --short origin/main).Trim()
$dirty = @(& git -C $Root status --porcelain)
Write-Host "primary: HEAD=$state origin/main=$origin dirty=$($dirty.Count)"
