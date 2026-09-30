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

# Native tools write progress to stderr; with ErrorActionPreference='Stop' PowerShell turns
# that into a terminating error and aborts mid-run. Same helper as new_agent_lane.ps1.
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
$Registry = Join-Path $Root "Tools\agent_lane_registry.py"
$RepoSlug = "fromage3900/MelodiaMelusinaV2"

if (-not (Test-Path $Registry)) { throw "Tools/agent_lane_registry.py is missing." }
if (-not $Lane -and -not $All) { throw "Pass -Lane <id> or -All." }

$env:GH_TOKEN = (& gh auth token 2>$null)
$env:GIT_TERMINAL_PROMPT = "0"
if (-not $env:GH_TOKEN) { throw "gh is not authenticated; run: gh auth login" }

function Get-Lanes {
    $common = (& git -C $Root rev-parse --git-common-dir).Trim()
    $base = if ([System.IO.Path]::IsPathRooted($common)) { $common } else { Join-Path $Root $common }
    $lanesPath = Join-Path $base "agents\lanes"
    if (-not (Test-Path $lanesPath)) { return @() }
    Get-ChildItem $lanesPath -Filter *.json | ForEach-Object {
        Get-Content $_.FullName -Raw | ConvertFrom-Json
    }
}

function Sync-Primary {
    Invoke-Native git @('-C', $Root, 'fetch', '--prune', 'origin') -AllowFail | Out-Null
    $branch = (Invoke-Native git @('-C', $Root, 'branch', '--show-current')).Lines[0].Trim()
    if ($branch -ne "main") {
        Write-Host "    NOTE: primary is on '$branch', not main; not fast-forwarding." -ForegroundColor Yellow
        return
    }
    $merge = Invoke-Native git @('-C', $Root, 'merge', '--ff-only', 'origin/main') -AllowFail
    $merge.Lines | ForEach-Object { Write-Host "    $_" }
    if ($merge.Code -ne 0) {
        Write-Host "    WARN: primary could not fast-forward; resolve by hand." -ForegroundColor Yellow
    }
}

function Invoke-LandOne([object]$LaneObj) {
    $id = [string]$LaneObj.lane
    $ref = [string]$LaneObj.branch
    $wt = [string]$LaneObj.worktree

    Write-Host "==> landing lane '$id'" -ForegroundColor Cyan
    if (-not $ref) { $ref = "refs/agents/$id" }

    if (-not (Test-Path $wt)) {
        Write-Host "    SKIP: lane worktree is gone ($wt)" -ForegroundColor Yellow
        return $false
    }
    $verify = Invoke-Native git @('-C', $wt, 'rev-parse', '--verify', '--quiet', $ref) -AllowFail
    if ($verify.Code -ne 0) {
        Write-Host "    SKIP: ref $ref does not exist" -ForegroundColor Yellow
        return $false
    }

    Invoke-Native git @('-C', $wt, 'fetch', '--prune', 'origin') -AllowFail | Out-Null
    $count = (Invoke-Native git @('-C', $wt, 'rev-list', '--count', "origin/main..$ref")).Lines[0].Trim()
    if ([int]$count -eq 0) {
        Write-Host "    nothing to land (lane delta is empty)" -ForegroundColor DarkGray
        return $false
    }
    Write-Host "    delta: $count commit(s) not on origin/main"

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $temp = "docs/land-$id-$stamp"
    $sha = (Invoke-Native git @('-C', $wt, 'rev-parse', $ref)).Lines[0].Trim()

    if ($DryRun) {
        Write-Host "    DRY RUN: would push $ref ($($sha.Substring(0,8))) -> refs/heads/$temp, PR, merge, delete." -ForegroundColor Yellow
        return $false
    }

    # Push the lane REF as a temporary branch. No local branch is created at any point.
    $push = Invoke-Native git @('-C', $wt, 'push', 'origin', "$ref`:refs/heads/$temp")
    $push.Lines | ForEach-Object { Write-Host "    $_" }

    $prBody = "Landed by deploy/land_agent_lane.ps1 from $ref at $sha. The authoring agent did not push and did not open this PR."
    $prOut = Invoke-Native gh @('pr', 'create', '--repo', $RepoSlug, '--base', 'main', '--head', $temp,
        '--title', "lane($id): land $count commit(s)", '--body', $prBody)
    $prUrl = $prOut.Lines | Select-Object -Last 1
    Write-Host "    PR $prUrl"
    $prNumber = (Invoke-Native gh @('pr', 'list', '--repo', $RepoSlug, '--head', $temp,
        '--state', 'open', '--json', 'number', '--jq', '.[0].number')).Lines[0].Trim()
    if (-not $prNumber) { throw "could not resolve the PR number for $temp" }

    # Give CI a moment; the branch-lifecycle guard runs on pull_request.
    Start-Sleep -Seconds 5
    $merge = Invoke-Native gh @('pr', 'merge', $prNumber, '--repo', $RepoSlug, '--rebase') -AllowFail
    $merge.Lines | ForEach-Object { Write-Host "    $_" }
    if ($merge.Code -ne 0) {
        Write-Host "    merge did not complete; inspect https://github.com/$RepoSlug/pull/$prNumber" -ForegroundColor Yellow
        return $false
    }

    if (-not $KeepRemoteBranch) {
        $del = Invoke-Native git @('-C', $wt, 'push', 'origin', '--delete', $temp) -AllowFail
        $del.Lines | ForEach-Object { Write-Host "    $_" }
    }

    Sync-Primary
    Write-Host "    landed $($sha.Substring(0,8)) on main" -ForegroundColor Green
    return $true
}

# NOTE: PowerShell variable names are case-INsensitive, so a loop variable named `$lane`
# is the very same variable as the `-Lane` parameter. That collision silently blanked the
# lane id and worktree on the first run of this script. Distinct names, deliberately.
$laneObjs = @(Get-Lanes)
if ($All) {
    $targets = $laneObjs
} else {
    $targets = @($laneObjs | Where-Object { [string]$_.lane -eq $Lane })
    if ($targets.Count -eq 0) {
        throw "lane '$Lane' is not registered. Run .\deploy\new_agent_lane.ps1 -Lane $Lane"
    }
}
if ($targets.Count -eq 0) { throw "no lanes registered" }

$landed = 0
foreach ($laneObj in $targets) {
    if (Invoke-LandOne -LaneObj $laneObj) { $landed++ }
}
Write-Host ""
Write-Host "landed $landed lane(s)." -ForegroundColor Green

$state = (Invoke-Native git @('-C', $Root, 'rev-parse', '--short', 'HEAD')).Lines[0].Trim()
$origin = (Invoke-Native git @('-C', $Root, 'rev-parse', '--short', 'origin/main')).Lines[0].Trim()
$dirty = @((Invoke-Native git @('-C', $Root, 'status', '--porcelain')).Lines)
Write-Host "primary: HEAD=$state origin/main=$origin dirty=$($dirty.Count)"
