# deploy/land_agent_lane.ps1 -- the integrator. Lands lane work on main.
#
#   .\deploy\land_agent_lane.ps1 -Lane cline -OwnerReviewedLocalState
#   .\deploy\land_agent_lane.ps1 -All -OwnerReviewedLocalState
#   .\deploy\land_agent_lane.ps1 -All -DryRun
#
# This is the only path that moves `main`. Agents never push and never open a PR:
# they commit in their lane worktree and pin the tip with refs/agents/<lane>.
#
# How it lands, and why recovery stays safe by default:
#
#   1. compute the lane's bounded delta:  origin/main..refs/agents/<lane>
#   2. push that ref straight to a temporary remote branch name
#      (git push origin refs/agents/<lane>:refs/heads/docs/land-<lane>-<stamp>)
#      -- no local branch is ever created
#   3. open a PR, rebase-merge it, PRESERVE temporary branch by default
#   4. do not fast-forward primary unless owner explicitly opts in
#
# The temporary branch is retained by default for recovery/provenance. Step 2 works
# from the lane worktree, so the primary checkout is never used as a staging area.
#
# Local production authority is fail-closed: missing UE/Houdini/Perforce evidence is
# UNKNOWN, not clean. Decision policy lives in Tools/agent_lane_local_authority.py.
#
# `main` is protected by .githooks/pre-push, so a direct push is impossible from here
# too -- that is intentional and this script does not work around it.
[CmdletBinding()]
param(
    [string]$Lane = "",
    [switch]$All,
    [switch]$DryRun,
    [switch]$KeepRemoteBranch,
    [switch]$OwnerReviewedLocalState,
    [switch]$OwnerApprovedBranchDeletion,
    [switch]$OwnerApprovedPrimarySync,
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
$Authority = Join-Path $Root "Tools\agent_lane_local_authority.py"
$RepoSlug = "fromage3900/MelodiaMelusinaV2"
$ProductionPathspecs = @(
    ':(glob)Content/**',
    ':(glob)**/*.uasset',
    ':(glob)**/*.umap',
    ':(glob)**/*.hip',
    ':(glob)**/*.hiplc',
    ':(glob)**/*.hipnc',
    ':(glob)Saved/**'
)

if (-not (Test-Path $Registry)) { throw "Tools/agent_lane_registry.py is missing." }
if (-not (Test-Path $Authority)) { throw "Tools/agent_lane_local_authority.py is missing." }
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
    Invoke-Native git @('-C', $Root, 'fetch', 'origin') | Out-Null
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

function Test-ProcessNamePresent([string[]]$Names) {
    foreach ($name in $Names) {
        if (Get-Process -Name $name -ErrorAction SilentlyContinue) {
            return $true
        }
    }
    return $false
}

function Get-GitPorcelain([string]$RepoPath, [switch]$IgnoredOnly) {
    $args = @('-C', $RepoPath, 'status', '--porcelain', '--untracked-files=all')
    if ($IgnoredOnly) {
        $args += @('--ignored=matching')
        $args += $ProductionPathspecs
    }
    return (Invoke-Native git $args -AllowFail)
}

# This is a local-only safety check. GitHub CI cannot see C:, G:, Perforce or unsaved editor state.
# Probe facts are gathered here; fail-closed policy is Tools/agent_lane_local_authority.py.
function Assert-LocalAuthority([string]$LaneWorktree) {
    $primaryStatus = Get-GitPorcelain -RepoPath $Root
    $laneStatus = Get-GitPorcelain -RepoPath $LaneWorktree
    $primaryIgnored = Get-GitPorcelain -RepoPath $Root -IgnoredOnly
    $laneIgnored = Get-GitPorcelain -RepoPath $LaneWorktree -IgnoredOnly
    $gitFailed = ($primaryStatus.Code -ne 0) -or ($laneStatus.Code -ne 0) -or ($primaryIgnored.Code -ne 0) -or ($laneIgnored.Code -ne 0)

    $p4Available = [bool](Get-Command 'p4' -ErrorAction SilentlyContinue)
    $p4InfoOk = $false
    $p4InfoFailed = $false
    $p4InfoLines = @()
    $p4OpenedCode = 1
    $p4OpenedLines = @()
    $p4OpenedFailed = $false
    if ($p4Available) {
        $info = Invoke-Native p4 @('info') -AllowFail
        $p4InfoLines = @($info.Lines)
        $p4InfoOk = ($info.Code -eq 0) -and (@($info.Lines | Where-Object { $_ -match 'Server address:' }).Count -gt 0)
        $p4InfoFailed = -not $p4InfoOk
        $opened = Invoke-Native p4 @('opened', '-m', '1') -AllowFail
        $p4OpenedCode = $opened.Code
        $p4OpenedLines = @($opened.Lines)
        $openedText = $opened.Lines -join [Environment]::NewLine
        if ($openedText -match 'File\(s\) not opened') {
            $p4OpenedFailed = $false
        } elseif ($opened.Code -ne 0) {
            $p4OpenedFailed = $true
        }
    }

    $snapshot = [ordered]@{
        owner_reviewed_local_state = [bool]$OwnerReviewedLocalState
        uproject_present           = [bool](Test-Path (Join-Path $Root 'BS_GodFile.uproject'))
        unreal_running             = Test-ProcessNamePresent -Names @('UnrealEditor', 'UnrealEditor-Cmd')
        houdini_running            = Test-ProcessNamePresent -Names @('houdini', 'houdinifx', 'houdinicore', 'hython', 'happrentice')
        primary_git_porcelain      = @($primaryStatus.Lines | Where-Object { $_.Trim() })
        lane_git_porcelain         = @($laneStatus.Lines | Where-Object { $_.Trim() })
        primary_ignored_porcelain  = @($primaryIgnored.Lines | Where-Object { $_.Trim() })
        lane_ignored_porcelain     = @($laneIgnored.Lines | Where-Object { $_.Trim() })
        p4_available               = $p4Available
        p4_info_ok                 = $p4InfoOk
        p4_info_lines              = $p4InfoLines
        p4_opened_code             = $p4OpenedCode
        p4_opened_lines            = $p4OpenedLines
        git_status_failed          = $gitFailed
        p4_info_failed             = $p4InfoFailed
        p4_opened_failed           = $p4OpenedFailed
    }
    $snapshotJson = $snapshot | ConvertTo-Json -Compress -Depth 6
    $eval = Invoke-Native python @($Authority, 'evaluate', '--snapshot-json', $snapshotJson) -AllowFail
    $eval.Lines | ForEach-Object { Write-Host "    $_" }
    if ($eval.Code -ne 0) {
        throw "SAFE STOP: local production authority refused landing (exit $($eval.Code)). Missing or unverified UE/Houdini/Perforce evidence is UNKNOWN, not clean."
    }
    Write-Host "    local gate passed: owner attestation + bounded probes (NOT proof of C:/G: backup)" -ForegroundColor Green
}

function Invoke-LandOne([object]$LaneObj) {
    $id = [string]$LaneObj.lane
    $ref = [string]$LaneObj.branch
    $wt = [string]$LaneObj.worktree

    Write-Host "==> landing lane '$id'" -ForegroundColor Cyan
    if (-not $ref) { $ref = "refs/agents/$id" }

    $worktreeExists = Test-Path $wt
    $refExists = $false
    if ($worktreeExists) {
        $verify = Invoke-Native git @('-C', $wt, 'rev-parse', '--verify', '--quiet', $ref) -AllowFail
        $refExists = ($verify.Code -eq 0)
    }

    $missingArgs = @($Authority, 'missing-target')
    if (-not $All) { $missingArgs += '--named-lane' }
    if ($worktreeExists) { $missingArgs += '--worktree-exists' }
    if ($refExists) { $missingArgs += '--ref-exists' }
    $missingEval = Invoke-Native python $missingArgs -AllowFail
    $missingEval.Lines | ForEach-Object { Write-Host "    $_" }
    if ($missingEval.Code -eq 2) {
        throw "SAFE STOP: named lane target missing or unverifiable ($id / $ref). State is UNKNOWN; refusing soft-skip."
    }
    if ($missingEval.Code -eq 3) {
        Write-Host "    UNKNOWN: lane target missing under -All ($wt / $ref); not clean — skipping" -ForegroundColor Yellow
        return $false
    }
    if ($missingEval.Code -ne 0) {
        throw "SAFE STOP: lane target policy check failed (exit $($missingEval.Code))."
    }

    Invoke-Native git @('-C', $wt, 'fetch', 'origin') | Out-Null
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
        Write-Host "    DRY RUN: would push $ref ($($sha.Substring(0,8))) -> refs/heads/$temp, open PR, merge; preserve by default (delete/FF require owner switches)." -ForegroundColor Yellow
        return $false
    }

    Assert-LocalAuthority -LaneWorktree $wt

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

    if ($OwnerApprovedBranchDeletion -and -not $KeepRemoteBranch) {
        $del = Invoke-Native git @('-C', $wt, 'push', 'origin', '--delete', $temp) -AllowFail
        $del.Lines | ForEach-Object { Write-Host "    $_" }
    } else {
        Write-Host "    preserving remote landing branch $temp for recovery/provenance" -ForegroundColor Yellow
    }

    if ($OwnerApprovedPrimarySync) {
        Sync-Primary
    } else {
        Write-Host "    primary checkout not auto-synced; review C:/G:/P4 before syncing" -ForegroundColor Yellow
    }
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
