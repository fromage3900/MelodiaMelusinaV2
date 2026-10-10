# Current Melodia remote-branch retirement entrypoint (2026-10-10).
# Dry-run by default. Remote deletions require explicit selection, archive verification,
# current-main/branch-SHA equality, exact Git ancestry, clean checkout and owner lease signoff.
# The older dated prune_remote_branches_2026_09_06.ps1 is historical, not an execution entrypoint.
[CmdletBinding()]
param(
    [string]$ManifestPath = "",
    [string]$Remote = "origin",
    [string[]]$ApprovedBranches = @(),
    [switch]$Execute,
    [string]$ConfirmBatch = "",
    [switch]$WorkstationsCleared
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-CheckedGit {
    param([string[]]$GitArgs, [switch]$AllowFail)
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $lines = @(& git @GitArgs 2>&1 | ForEach-Object { [string]$_ })
        $exitCode = [int]$LASTEXITCODE
    } finally {
        $ErrorActionPreference = $saved
    }
    $output = $lines -join [Environment]::NewLine
    if (-not $AllowFail -and $exitCode -ne 0) {
        throw ("git {0} failed (exit {1}): {2}" -f ($GitArgs -join " "), $exitCode, $output)
    }
    return [pscustomobject]@{ Code = $exitCode; Text = $output }
}

function Get-RemoteSha {
    param([string]$Kind, [string]$Name)
    $ref = if ($Kind -eq "heads") { "refs/heads/$Name" } else { "refs/tags/$Name" }
    $result = Invoke-CheckedGit -GitArgs @("ls-remote", "--refs", $Remote, $ref)
    $lines = @($result.Text -split '\r?\n' | Where-Object { $_.Trim() })
    if ($lines.Count -eq 0) { return $null }
    if ($lines.Count -ne 1) { throw "Ambiguous remote ref: $ref" }
    $parts = $lines[0] -split '\s+'
    if ($parts.Count -ne 2 -or $parts[1] -ne $ref) {
        throw "Remote returned a non-exact ref for $ref"
    }
    return $parts[0]
}

$root = (Invoke-CheckedGit -GitArgs @("rev-parse", "--show-toplevel")).Text.Trim()
if (-not $root) { throw "Run inside MelodiaMelusinaV2." }
if ($Remote -ne "origin") { throw "Only the canonical origin remote is permitted." }
if (-not $ManifestPath) {
    $ManifestPath = Join-Path $root "specs/branch_retirement_census_2026-10-10.json"
}
if (-not [System.IO.Path]::IsPathRooted($ManifestPath)) {
    $ManifestPath = Join-Path $root $ManifestPath
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Retirement census does not exist: $ManifestPath"
}
$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema -ne "melodia.branch_retirement_census/v2") { throw "Unsupported census schema." }
if ($manifest.repository -ne "fromage3900/MelodiaMelusinaV2") { throw "Wrong repository." }
if ($manifest.destructive_action_performed -ne $false) { throw "Census is not a pre-retirement snapshot." }
if ($manifest.all_execution_approvals -ne $false) { throw "Census execution invariant violated." }
if (-not $manifest.entries -or -not $manifest.main_sha) { throw "Census lacks branch SHA pins." }

if ($Execute) {
    if (-not $ApprovedBranches -or $ApprovedBranches.Count -eq 0) {
        throw "Execute requires -ApprovedBranches with explicitly selected branch names."
    }
    if ($ConfirmBatch -ne ("RETIRE-" + $manifest.generated_date)) {
        throw "Execute requires -ConfirmBatch RETIRE-$($manifest.generated_date)."
    }
    if (-not $WorkstationsCleared) {
        throw "Execute requires -WorkstationsCleared after confirming all PC/laptop/Humber worktrees, agents, Perforce and active editors are clear."
    }
} elseif ($ApprovedBranches.Count -gt 0) {
    Write-Host "Dry run only; -ApprovedBranches does not delete anything without -Execute and other safeguards."
}

Push-Location $root
try {
    if ($Execute) {
        $localBranch = (Invoke-CheckedGit -GitArgs @("branch", "--show-current")).Text.Trim()
        if ($localBranch -ne "main") { throw "Execute requires a checked-out main, not $localBranch." }
        $dirty = (Invoke-CheckedGit -GitArgs @("status", "--porcelain")).Text.Trim()
        if ($dirty) { throw "Execute requires a clean working tree/index (no commit, stash, or reset is performed)." }
    }

    # Fetch changes remote-tracking refs only: no checkout, merge, rebase, reset or UE/P4 operation.
    Invoke-CheckedGit -GitArgs @("fetch", "--prune", $Remote) | Out-Null
    $remoteMain = Get-RemoteSha -Kind "heads" -Name "main"
    $localMain = (Invoke-CheckedGit -GitArgs @("rev-parse", "refs/remotes/origin/main")).Text.Trim()
    if (-not $remoteMain -or $remoteMain -ne $localMain) {
        throw "Local origin/main is not synchronized with the live remote; no deletion permitted."
    }
    # New housekeeping commits may advance main after this census PR merges. Require
    # the pinned census base to remain in current main history, not byte-equal HEAD.
    $baseReachable = Invoke-CheckedGit -GitArgs @("merge-base", "--is-ancestor", ([string]$manifest.main_sha), $remoteMain) -AllowFail
    if ($baseReachable.Code -ne 0) {
        throw "Census main SHA is no longer an ancestor of origin/main. Regenerate; no deletion permitted."
    }
    if ($Execute) {
        $checkoutHead = (Invoke-CheckedGit -GitArgs @("rev-parse", "HEAD")).Text.Trim()
        if ($checkoutHead -ne $remoteMain) { throw "Local main is not the exact audited origin/main." }
    }

    $candidates = @($manifest.entries | Where-Object { $_.disposition -eq "ANCESTOR_CANDIDATE_REVIEW" })
    $selected = if ($ApprovedBranches.Count -gt 0) { @($ApprovedBranches) } else { @($candidates | ForEach-Object { $_.branch }) }
    if ($selected.Count -ne (@($selected | Select-Object -Unique)).Count) {
        throw "Duplicate branch selection."
    }
    Write-Host ("Melodia retirement: mode={0}; remote={1}; baseline={2}; candidates={3}; selected={4}" -f $(if ($Execute) { "EXECUTE" } else { "DRY RUN" }), $Remote, $remoteMain.Substring(0,12), $candidates.Count, $selected.Count)
    $rows = @()
    foreach ($name in $selected) {
        if (-not $name -or $name -eq "main") { throw "Invalid protected branch selection." }
        $match = @($manifest.entries | Where-Object { $_.branch -ceq $name })
        if ($match.Count -ne 1) { throw "Branch not found exactly once in census: $name" }
        $entry = $match[0]
        if ($entry.disposition -ne "ANCESTOR_CANDIDATE_REVIEW" -or
            $entry.ahead_by -ne 0 -or
            $entry.open_pr -ne $null -or
            $entry.execution_approved -ne $false -or
            $entry.verified_main_sha -ne $manifest.main_sha) {
            throw "Branch has no eligible, zero-ahead ancestry proof: $name"
        }
        if ($name -match '^(backup|recovery|collab|lane)/') {
            throw "Never retire protected workstation/provenance classes in this script: $name"
        }
        $expected = [string]$entry.head_sha
        if ($expected -notmatch '^[a-f0-9]{40}$') { throw "Invalid pinned tip for $name" }
        $actual = Get-RemoteSha -Kind "heads" -Name $name
        if ($actual -ne $expected) { throw "Branch tip changed since census: $name (expected $expected, got $actual)" }

        # A zero-ahead compare is not enough unless its exact tip is an ancestor of current main.
        $ancestor = Invoke-CheckedGit -GitArgs @("merge-base", "--is-ancestor", $expected, $remoteMain) -AllowFail
        if ($ancestor.Code -ne 0) { throw "Exact ancestry not proven for $name (exit $($ancestor.Code))." }

        # Never invalidate a currently checked-out local branch, even in another worktree.
        $localRef = Invoke-CheckedGit -GitArgs @("show-ref", "--verify", "--quiet", "refs/heads/$name") -AllowFail
        if ($localRef.Code -eq 0) { throw "Local branch exists; owner must reconcile it first: $name" }
        $worktrees = (Invoke-CheckedGit -GitArgs @("worktree", "list", "--porcelain")).Text
        if ($worktrees.Contains("branch refs/heads/$name")) { throw "Checked-out worktree owns $name" }

        $tag = [string]$entry.archive_tag
        if ($tag -ne ("archive/branches/" + $manifest.generated_date + "/" + $name)) {
            throw "Unexpected archive-tag namespace: $tag"
        }
        $previous = Get-RemoteSha -Kind "tags" -Name $tag
        if ($previous -and $previous -ne $expected) { throw "Conflicting remote archive tag exists: $tag" }
        $action = if ($previous) { "REUSE EXACT ARCHIVE, THEN DELETE" } else { "ARCHIVE, VERIFY, THEN DELETE" }
        if ($Execute) {
            if (-not $previous) {
                $tagLocal = Invoke-CheckedGit -GitArgs @("rev-parse", "-q", "--verify", "refs/tags/$tag") -AllowFail
                if ($tagLocal.Code -eq 0) {
                    if ($tagLocal.Text.Trim() -ne $expected) { throw "Conflicting local archive tag: $tag" }
                } else {
                    Invoke-CheckedGit -GitArgs @("tag", $tag, $expected) | Out-Null
                }
                Invoke-CheckedGit -GitArgs @("push", $Remote, ("refs/tags/" + $tag + ":refs/tags/" + $tag)) | Out-Null
                if ((Get-RemoteSha -Kind "tags" -Name $tag) -ne $expected) {
                    throw "Archive tag did not resolve to expected tip; remote branch remains untouched: $name"
                }
            }
            # Force-with-lease protects against a concurrent agent pushing the branch after the check.
            $lease = "--force-with-lease=refs/heads/" + $name + ":" + $expected
            Invoke-CheckedGit -GitArgs @("push", $lease, $Remote, (":refs/heads/" + $name)) | Out-Null
            if (Get-RemoteSha -Kind "heads" -Name $name) {
                throw "Branch deletion could not be verified: $name"
            }
            $action = "ARCHIVED + RETIRED"
        }
        $rows += [pscustomobject]@{ Branch = $name; Ahead = 0; Behind = $entry.behind_by; Action = $action; Archive = $tag }
    }
    $rows | Format-Table Branch, Ahead, Behind, Action -AutoSize | Out-Host
    if (-not $Execute) {
        Write-Host "DRY RUN: no remote tags or branches changed."
        Write-Host "After explicit owner approval + workstation/P4 check, run with -Execute -ApprovedBranches <exact-name> -ConfirmBatch RETIRE-$($manifest.generated_date) -WorkstationsCleared."
    } else {
        Write-Host "Retired branch tips remain recoverable from verified remote archive tags."
    }
} finally {
    Pop-Location
}
