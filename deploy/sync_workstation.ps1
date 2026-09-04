# Melodia two-workstation Git/LFS synchronizer.
#
# Safe by design:
# - never reset, clean, rebase, stash, force-push, or auto-merge divergent work
# - fetches remote state first
# - only updates the current branch with a fast-forward-only merge
# - hydrates Git LFS separately via an explicit profile
# - writes a machine-local report under Saved\Workstation\
#
# Examples:
#   .\deploy\sync_workstation.ps1
#   .\deploy\sync_workstation.ps1 -Mode Sync
#   .\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile House
#   .\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile Gameplay
#   .\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile Full
# Explicit feature-branch check only:
#   .\deploy\sync_workstation.ps1 -Target Current
[CmdletBinding()]
param(
    [ValidateSet("Check", "Sync")]
    [string]$Mode = "Check",

    [ValidateSet("Main", "Current")]
    [string]$Target = "Main",

    [ValidateSet("None", "Core", "House", "Gameplay", "Full")]
    [string]$LfsProfile = "None",

    [string]$Remote = "origin",

    [switch]$SkipFetch,

    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ReportDirectory = Join-Path $ProjectRoot "Saved\Workstation"
$MachineName = if ([string]::IsNullOrWhiteSpace($env:COMPUTERNAME)) { "machine" } else { $env:COMPUTERNAME }
$ReportPath = Join-Path $ReportDirectory "$MachineName-sync-report.json"

New-Item -ItemType Directory -Path $ReportDirectory -Force | Out-Null

function Invoke-Git {
    param(
        [Parameter(Mandatory=$true)]
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    $lines = @()
    $code = 0
    try {
        $lines = @(& git -C $ProjectRoot @Arguments 2>&1 | ForEach-Object { [string]$_ })
        $code = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    } catch {
        $lines = @($_.Exception.Message)
        $code = 1
    }

    $result = [pscustomobject]@{
        Code = $code
        Lines = $lines
        Text = ($lines -join [Environment]::NewLine).Trim()
    }

    if ($VerboseOutput -and $result.Text) {
        Write-Host ("git " + ($Arguments -join " ")) -ForegroundColor DarkGray
        Write-Host $result.Text -ForegroundColor DarkGray
    }

    if (-not $AllowFailure -and $code -ne 0) {
        throw ("git " + ($Arguments -join " ") + " failed with exit " + $code + [Environment]::NewLine + $result.Text)
    }

    return $result
}

function Test-RemoteRef {
    param([string]$Ref)
    $r = Invoke-Git -Arguments @("show-ref", "--verify", "--quiet", $Ref) -AllowFailure
    return $r.Code -eq 0
}

function Get-AheadBehind {
    param(
        [string]$Left,
        [string]$Right
    )

    $r = Invoke-Git -Arguments @("rev-list", "--left-right", "--count", "$Left...$Right") -AllowFailure
    if ($r.Code -ne 0) {
        return [pscustomobject]@{ Ahead = $null; Behind = $null }
    }

    $parts = @($r.Text -split "\s+" | Where-Object { $_ -ne "" })
    if ($parts.Count -lt 2) {
        return [pscustomobject]@{ Ahead = $null; Behind = $null }
    }

    return [pscustomobject]@{
        Ahead = [int]$parts[0]
        Behind = [int]$parts[1]
    }
}

function Get-LfsInclude {
    param([string]$Profile)

    switch ($Profile) {
        "Core" {
            return "Content/Melodia/Levels/**,Content/Melodia/PCG/**,Content/TurnBasedJRPGTemplate/Blueprints/Battle/**"
        }
        "House" {
            return "Docs/References/MelusinasHouse/**,RawArt/MelusinasHouse/**"
        }
        "Gameplay" {
            return "Content/Melodia/Levels/**,Content/Melodia/PCG/**,Content/MelodiaIntegration/**,Content/Characters/**,Content/Melodia/Characters/**,Content/TurnBasedJRPGTemplate/Blueprints/Battle/**,Content/TurnBasedJRPGTemplate/Blueprints/EnemyExplorePawns/**,Content/EnvSandbox/Environments/**,Content/EnvSandbox/PCG/**,Content/EnvSandbox/Monoliths/**"
        }
        default {
            return ""
        }
    }
}

function Get-LfsState {
    $r = Invoke-Git -Arguments @("lfs", "ls-files", "--long") -AllowFailure
    if ($r.Code -ne 0) {
        return [pscustomobject]@{
            Available = $false
            Total = 0
            Hydrated = 0
            Missing = 0
            SampleMissing = @()
            Raw = $r.Text
        }
    }

    $hydrated = @($r.Lines | Where-Object { $_ -match "^[0-9a-fA-F]+\s+\*\s+" })
    $missing = @($r.Lines | Where-Object { $_ -match "^[0-9a-fA-F]+\s+-\s+" })

    return [pscustomobject]@{
        Available = $true
        Total = $r.Lines.Count
        Hydrated = $hydrated.Count
        Missing = $missing.Count
        SampleMissing = @($missing | Select-Object -First 20)
        Raw = $r.Text
    }
}

function Write-Section {
    param(
        [string]$Name,
        [string]$Value,
        [ConsoleColor]$Color = [ConsoleColor]::Gray
    )
    Write-Host ("{0,-18} {1}" -f $Name, $Value) -ForegroundColor $Color
}

$gitVersion = Invoke-Git -Arguments @("--version") -AllowFailure
if ($gitVersion.Code -ne 0) {
    throw "Git is not available on PATH."
}

$top = Invoke-Git -Arguments @("rev-parse", "--show-toplevel")
$expectedRoot = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd([char]"\", [char]"/")
$actualRoot = [IO.Path]::GetFullPath($top.Text).TrimEnd([char]"\", [char]"/")
if ($actualRoot -ne $expectedRoot) {
    throw "This script must run from the Melodia repository. Git root is '$($top.Text)', expected '$ProjectRoot'."
}

$remoteUrlResult = Invoke-Git -Arguments @("remote", "get-url", $Remote) -AllowFailure
if ($remoteUrlResult.Code -ne 0) {
    throw "Remote '$Remote' does not exist."
}
$remoteUrl = $remoteUrlResult.Text
$remoteLooksCorrect = $remoteUrl -match "fromage3900[/:]MelodiaMelusinaV2(\.git)?$"
if (-not $remoteLooksCorrect) {
    throw "Remote '$Remote' points to '$remoteUrl', not fromage3900/MelodiaMelusinaV2."
}

$hooksPath = (Invoke-Git -Arguments @("config", "--get", "core.hooksPath") -AllowFailure).Text
if ($Mode -eq "Sync" -and $hooksPath -ne ".githooks") {
    Invoke-Git -Arguments @("config", "core.hooksPath", ".githooks") | Out-Null
    $hooksPath = ".githooks"
}

$lfsVersion = Invoke-Git -Arguments @("lfs", "version") -AllowFailure
$lfsAvailable = $lfsVersion.Code -eq 0

$currentBranch = (Invoke-Git -Arguments @("branch", "--show-current")).Text
$headBefore = (Invoke-Git -Arguments @("rev-parse", "HEAD")).Text
$statusBefore = @(Invoke-Git -Arguments @("status", "--short") | Select-Object -ExpandProperty Lines)
$dirty = $statusBefore.Count -gt 0

if (-not $SkipFetch) {
    Write-Host "Fetching $Remote..." -ForegroundColor Cyan
    Invoke-Git -Arguments @("fetch", "--prune", $Remote) | Out-Null
}

$remoteBranchRef = "refs/remotes/$Remote/$currentBranch"
$hasRemoteBranch = -not [string]::IsNullOrWhiteSpace($currentBranch) -and (Test-RemoteRef $remoteBranchRef)

if ($Target -eq "Main") {
    $trackingRef = "$Remote/main"
} else {
    if (-not $hasRemoteBranch) {
        throw "Target=Current requires a same-name remote branch for '$currentBranch'. Push the branch first or use -Target Main."
    }
    $trackingRef = "$Remote/$currentBranch"
}

$hasTrackingRef = Test-RemoteRef "refs/remotes/$trackingRef"

if (-not $hasTrackingRef) {
    throw "Could not find remote tracking ref '$trackingRef' after fetch."
}

$branchDelta = Get-AheadBehind -Left "HEAD" -Right $trackingRef
$mainDelta = Get-AheadBehind -Left "HEAD" -Right "$Remote/main"

$switchedToMain = $false
$uniqueCommitsToMain = $null

# Safe normalization: when normal workstation sync targets main, a clean stale
# branch with ZERO commits unique to origin/main can be switched back to main.
# Any unique commit blocks the switch so unpublished work cannot disappear.
if ($Target -eq "Main" -and $currentBranch -ne "main" -and -not $dirty) {
    $uniqueResult = Invoke-Git -Arguments @("rev-list", "--count", "$Remote/main..HEAD") -AllowFailure
    if ($uniqueResult.Code -eq 0 -and $uniqueResult.Text -match "^\d+$") {
        $uniqueCommitsToMain = [int]$uniqueResult.Text
    }

    if ($Mode -eq "Sync" -and $uniqueCommitsToMain -eq 0) {
        Write-Host "Current branch '$currentBranch' has no commits unique to $Remote/main; switching safely to main..." -ForegroundColor Cyan
        Invoke-Git -Arguments @("switch", "main") | Out-Null
        $switchedToMain = $true
        $currentBranch = (Invoke-Git -Arguments @("branch", "--show-current")).Text
        $remoteBranchRef = "refs/remotes/$Remote/$currentBranch"
        $hasRemoteBranch = Test-RemoteRef $remoteBranchRef
        $trackingRef = "$Remote/main"
        $branchDelta = Get-AheadBehind -Left "HEAD" -Right $trackingRef
        $mainDelta = Get-AheadBehind -Left "HEAD" -Right "$Remote/main"
    }
}

$state = "unknown"
$recommended = ""

if ($dirty) {
    $state = "dirty"
    $recommended = "Commit the current machine's intended work to its lane branch and push it before switching machines. This script will not hide or overwrite dirty work."
} elseif ($Target -eq "Main" -and $currentBranch -ne "main") {
    $state = "wrong-branch"
    if ($uniqueCommitsToMain -gt 0) {
        $recommended = "Cross-workstation baseline requires main, but '$currentBranch' has $uniqueCommitsToMain commit(s) not reachable from origin/main. Preserve/push those commits before switching branches."
    } else {
        $recommended = "Cross-workstation baseline requires branch 'main'. This machine is on '$currentBranch'. Run -Mode Sync for a safe automatic return when the branch has zero unique commits."
    }
} elseif ($branchDelta.Ahead -gt 0 -and $branchDelta.Behind -gt 0) {
    $state = "diverged"
    $recommended = "Do not pull/rebase/reset automatically. Push the local commits to a recovery/collab branch if needed, then compare the two lines and reconcile explicitly."
} elseif ($branchDelta.Ahead -gt 0) {
    $state = "ahead"
    $recommended = "This machine has commits the remote does not. Push the current branch before expecting the other machine to see them."
} elseif ($branchDelta.Behind -gt 0) {
    $state = "behind"
    $recommended = "This machine can fast-forward safely if the worktree remains clean."
} else {
    $state = "synced"
    $recommended = "Git commit state matches the selected remote ref."
}

$fastForwardApplied = $false

if ($Mode -eq "Sync" -and $state -eq "behind") {
    Write-Host "Fast-forwarding $currentBranch from $trackingRef..." -ForegroundColor Cyan
    Invoke-Git -Arguments @("merge", "--ff-only", $trackingRef) | Out-Null
    $fastForwardApplied = $true

    $branchDelta = Get-AheadBehind -Left "HEAD" -Right $trackingRef
    if ($branchDelta.Ahead -eq 0 -and $branchDelta.Behind -eq 0) {
        $state = "synced"
        $recommended = "Fast-forward completed. Git commit state now matches $trackingRef."
    } else {
        $state = "needs-review"
        $recommended = "Fast-forward did not reach an equal state; inspect branch history before doing more work."
    }
}

$lfsPullAttempted = $false
$lfsPullSucceeded = $null
$lfsInclude = Get-LfsInclude -Profile $LfsProfile

if ($Mode -eq "Sync" -and $LfsProfile -ne "None") {
    if (-not $lfsAvailable) {
        $lfsPullSucceeded = $false
        $state = "lfs-unavailable"
        $recommended = "Install Git LFS before hydrating binary assets."
    } elseif ($state -in @("dirty", "diverged", "needs-review", "wrong-branch", "ahead")) {
        $lfsPullSucceeded = $false
        $recommended += " LFS hydration was skipped because Git state is not safe."
    } else {
        $lfsPullAttempted = $true
        Write-Host "Hydrating LFS profile '$LfsProfile'..." -ForegroundColor Cyan
        if ($LfsProfile -eq "Full") {
            $pull = Invoke-Git -Arguments @("lfs", "pull", $Remote) -AllowFailure
        } else {
            $pull = Invoke-Git -Arguments @("lfs", "pull", $Remote, "--include=$lfsInclude") -AllowFailure
        }
        $lfsPullSucceeded = $pull.Code -eq 0
        if (-not $lfsPullSucceeded) {
            $state = "lfs-error"
            $recommended = "Git refs may be synchronized, but LFS hydration failed. Inspect the report before opening Unreal/Blender."
        }
    }
}

$headAfter = (Invoke-Git -Arguments @("rev-parse", "HEAD")).Text
$statusAfter = @(Invoke-Git -Arguments @("status", "--short") | Select-Object -ExpandProperty Lines)
$lfsState = Get-LfsState

$report = [ordered]@{
    schema = "melodia.workstation_sync_report.v1"
    generated_at = (Get-Date).ToString("o")
    machine = $MachineName
    project_root = $ProjectRoot
    mode = $Mode
    remote = $Remote
    remote_url = $remoteUrl
    branch = $currentBranch
    target = $Target
    tracking_ref = $trackingRef
    has_same_name_remote_branch = $hasRemoteBranch
    head_before = $headBefore
    head_after = $headAfter
    hooks_path = $hooksPath
    dirty_before = $dirty
    status_before = $statusBefore
    status_after = $statusAfter
    branch_ahead = $branchDelta.Ahead
    branch_behind = $branchDelta.Behind
    main_ahead = $mainDelta.Ahead
    main_behind = $mainDelta.Behind
    sync_state = $state
    recommended_action = $recommended
    switched_to_main = $switchedToMain
    unique_commits_to_main = $uniqueCommitsToMain
    fast_forward_applied = $fastForwardApplied
    lfs = [ordered]@{
        version = $lfsVersion.Text
        available = $lfsAvailable
        profile = $LfsProfile
        include = $lfsInclude
        pull_attempted = $lfsPullAttempted
        pull_succeeded = $lfsPullSucceeded
        total_tracked = $lfsState.Total
        hydrated = $lfsState.Hydrated
        missing = $lfsState.Missing
        sample_missing = $lfsState.SampleMissing
    }
    report_path = $ReportPath
}

$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8

Write-Host ""
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host " MELODIA TWO-WORKSTATION SYNC " -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta
Write-Section "Machine" $MachineName
Write-Section "Branch" $currentBranch
Write-Section "Target" $Target
Write-Section "Tracking" $trackingRef
Write-Section "HEAD" $headAfter
$stateColor = if ($state -eq "synced") { [ConsoleColor]::Green } elseif ($state -eq "ahead") { [ConsoleColor]::Yellow } else { [ConsoleColor]::Red }
Write-Section "Git state" $state $stateColor
Write-Section "Ahead / behind" "$($branchDelta.Ahead) / $($branchDelta.Behind)"
Write-Section "vs origin/main" "$($mainDelta.Ahead) / $($mainDelta.Behind)"
Write-Section "Dirty" ([string]$dirty)
Write-Section "Switched to main" ([string]$switchedToMain)
if ($null -ne $uniqueCommitsToMain) { Write-Section "Unique vs main" ([string]$uniqueCommitsToMain) }
Write-Section "LFS profile" $LfsProfile
Write-Section "LFS hydrated" "$($lfsState.Hydrated) / $($lfsState.Total)"
$lfsColor = if ($lfsState.Missing -eq 0) { [ConsoleColor]::Green } else { [ConsoleColor]::Yellow }
Write-Section "LFS missing" ([string]$lfsState.Missing) $lfsColor
Write-Host ""
Write-Host "Recommended: $recommended" -ForegroundColor Yellow
Write-Host "Report: $ReportPath" -ForegroundColor Gray

$healthyStates = @("synced")
$exitCode = if ($state -in $healthyStates) { 0 } else { 1 }
exit $exitCode
