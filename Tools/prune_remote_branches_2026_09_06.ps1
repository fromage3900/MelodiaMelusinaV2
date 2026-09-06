param(
  [switch]$Execute,
  [string]$Remote = "origin",
  [string]$ArchiveDate = "2026-09-06",
  [string[]]$KeepAdditional = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Second-pass branch cleanup generated from the 2026-09-06 GitHub census.
# Dry-run is the default. Every deletion is preceded by a verified remote archive tag.

$Keep = @(
  'main',
  'docs/stale-session-start-fix-2026-09-06',
  'recovery/harvest-small-branches-2026-09-06'
) + $KeepAdditional

$Candidates = @(
  'backup/pre-consolidation-2026-08-30',
  'claude/tonight-cymatic-ecology-interaction',
  'cleanup/golden-scorecard-2026-09-06',
  'cleanup/lookdev-plan-2026-09-06',
  'cleanup/scrub-spec-2026-09-06',
  'codex/game-state-2026-09-04-checkpoint',
  'codex/weapon-gallery-20260902',
  'collab/laptop/main-reconciliation-2026-09-04',
  'copilot/fix-runners-and-review-logs',
  'copilot/new-feature-implementation',
  'docs/2026-08-29-character-p1-p2-canon-audit',
  'docs/2026-09-02-grand-master-plan',
  'feature/grandmaster-melodia-studio',
  'feature/ue58-runner-registration',
  'fix/mh6-fix-promotion-20260904',
  'fix/prune-script-ps51',
  'integration/astra-game-state-transplant-2026-09-05',
  'pr/melusina-v22-sync',
  'recovery/astra-docs-2026-09-06',
  'recovery/blender-music-gn-docs-2026-09-06',
  'recovery/canon-docs-2026-09-06',
  'recovery/small-tools-2026-09-06',
  'rescue/web-threejs-recovery-2026-09-05',
  'rnd/2026-08-30-blender52-music-gn-studio'
)

function Invoke-Git {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  & git @Args
  if ($LASTEXITCODE -ne 0) { throw "git $($Args -join ' ') failed with exit code $LASTEXITCODE" }
}

function Get-RemoteHeadSha {
  param([string]$Branch)
  $out = & git ls-remote --heads $Remote "refs/heads/$Branch"
  if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
  return (($out -split "\s+")[0]).Trim()
}

function Get-RemoteTagSha {
  param([string]$Tag)
  $out = & git ls-remote --tags $Remote "refs/tags/$Tag"
  if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
  return (($out -split "\s+")[0]).Trim()
}

$repoRoot = (& git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $repoRoot) { throw "Run this from a clone of MelodiaMelusinaV2." }
$dirty = (& git status --porcelain)
if ($dirty) { throw "Worktree is dirty. Commit or stash first; pruning is intentionally blocked." }

Invoke-Git fetch $Remote --prune --tags
$mainSha = Get-RemoteHeadSha "main"
if (-not $mainSha) { throw "Could not resolve $Remote/main." }

Write-Host ""
Write-Host "Melodia remote branch hygiene - 2026-09-06 second pass"
Write-Host "Remote:      $Remote"
Write-Host "Main:        $mainSha"
Write-Host "Candidates:  $($Candidates.Count)"
Write-Host "Keep:        $($Keep.Count)"
Write-Host "Mode:        $(if ($Execute) {'ARCHIVE + DELETE'} else {'DRY RUN'})"
Write-Host ""

$results = @()
foreach ($branch in $Candidates) {
  if ($Keep -contains $branch) {
    $results += [pscustomobject]@{ Branch=$branch; Ahead=""; Behind=""; Action="KEEP" }
    continue
  }
  $sha = Get-RemoteHeadSha $branch
  if (-not $sha) {
    $results += [pscustomobject]@{ Branch=$branch; Ahead=""; Behind=""; Action="ALREADY GONE" }
    continue
  }

  # PowerShell 5.1-safe braced/subexpression interpolation around refspec colons.
  Invoke-Git fetch $Remote "refs/heads/$($branch):refs/remotes/$($Remote)/$($branch)"
  $counts = (& git rev-list --left-right --count "$Remote/main...$Remote/$branch").Trim()
  if ($LASTEXITCODE -ne 0) {
    $behind = "?"
    $ahead = "?"
  } else {
    $parts = $counts -split "\s+"
    $behind = $parts[0]
    $ahead = $parts[1]
  }

  $tag = "archive/branches/$ArchiveDate/$branch"
  $action = "ARCHIVE -> $tag ; DELETE"
  if ($Execute) {
    $remoteTagSha = Get-RemoteTagSha $tag
    if ($remoteTagSha) {
      if ($remoteTagSha -ne $sha) { throw "Archive tag $tag already exists at $remoteTagSha, but branch $branch is $sha. Refusing deletion." }
    } else {
      $localTagSha = (& git rev-parse -q --verify "refs/tags/$tag" 2>$null)
      if ($LASTEXITCODE -eq 0 -and $localTagSha) {
        if ($localTagSha.Trim() -ne $sha) { throw "Local archive tag $tag points somewhere else. Refusing deletion." }
      } else {
        Invoke-Git tag $tag $sha
      }
      Invoke-Git push $Remote "refs/tags/$($tag):refs/tags/$($tag)"
      $remoteTagSha = Get-RemoteTagSha $tag
      if ($remoteTagSha -ne $sha) { throw "Remote archive verification failed for $branch. Expected $sha, got $remoteTagSha." }
    }
    Invoke-Git push $Remote --delete $branch
    $stillThere = Get-RemoteHeadSha $branch
    if ($stillThere) { throw "Branch deletion verification failed: $branch still resolves to $stillThere" }
    $action = "ARCHIVED + DELETED"
  }
  $results += [pscustomobject]@{ Branch=$branch; Ahead=$ahead; Behind=$behind; Action=$action }
}

$results | Sort-Object Action, Branch | Format-Table -AutoSize
Write-Host ""
if (-not $Execute) {
  Write-Host "Dry run only. No refs changed."
  Write-Host "If the table is expected, execute:"
  Write-Host "  powershell -ExecutionPolicy Bypass -File Tools/prune_remote_branches_2026_09_06.ps1 -Execute"
} else {
  Write-Host "Done. Deleted branch tips are preserved under refs/tags/archive/branches/$ArchiveDate/..."
  Write-Host "Restore example:"
  Write-Host "  git push $Remote refs/tags/archive/branches/$ArchiveDate/<old-branch>:refs/heads/<old-branch>"
}
