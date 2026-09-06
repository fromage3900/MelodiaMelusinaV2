param(
  [switch]$Execute,
  [string]$Remote = "origin",
  [string]$ArchiveDate = "2026-09-05",
  [string[]]$KeepAdditional = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Snapshot-specific cleanup generated from the GitHub branch census on 2026-09-05.
# Dry-run is the default. -Execute archives every candidate tip to a remote tag
# BEFORE deleting its remote branch, so every deletion is reversible.

$Keep = @(
  'main',
  'integration/astra-game-state-transplant-2026-09-05',
  'fix/mh6-shell-promotion-20260904',
  'codex/game-state-2026-09-04-checkpoint',
  'codex/weapon-gallery-20260902',
  'rnd/2026-08-30-blender52-music-gn-studio',
  'docs/2026-08-29-character-p1-p2-canon-audit'
) + $KeepAdditional

$Candidates = @(
  'backup/pre-consolidation-2026-08-30',
  'claude/tonight-cymatic-ecology-interaction',
  'cleanup/integrate-batches-2026-09-03',
  'cleanup/sync-discovery-final',
  'codex/p0-closeout-history-2026-09-02',
  'codex/p0-closeout-lfs-2026-09-02',
  'codex/perforce-migration-handoff-2026-08-26',
  'collab/laptop/integration-batch-2026-09-02',
  'collab/laptop/main-reconciliation-2026-09-04',
  'collab/laptop/onboarding-closeout-2026-09-02',
  'collab/laptop/workstation-health',
  'copilot/fix-issue-in-algorithm',
  'copilot/fix-runners-and-review-logs',
  'copilot/git-status-check',
  'copilot/main',
  'copilot/new-feature-implementation',
  'copilot/review-recent-documents-on-git',
  'copilot/validate-source-control-claims',
  'cursor/branch-cleanup-executed-ca02',
  'cursor/docs-safe-batches-ca02',
  'cursor/fix-ci-workflows-529c',
  'cursor/git-health-checkpoint-c2b1',
  'cursor/model-lanes-agents-slim-f425',
  'cursor/nemotron-docs-batch-ca02',
  'cursor/nemotron-research-docs-2d2d',
  'cursor/perforce-docs-batch-ca02',
  'cursor/phone-party-trick-93f5',
  'cursor/recruiter-sendoffs-no-nvidia-ca02',
  'cursor/threejs-integration-d313',
  'cursor/zenforest-docs-batch-ca02',
  'docs/2026-08-31-mara-instrument-cymatics-plan',
  'docs/2026-09-02-endless-journey-paradigm',
  'docs/2026-09-02-grand-master-plan',
  'docs/2026-09-02-melusinashouseplan',
  'docs/2026-09-03-hyperpop-stem-research',
  'docs/2026-09-03-melusina-house-gn-phase2',
  'docs/2026-09-03-melusina-house-gn-phase3',
  'docs/2026-09-04-melusina-house-builder-roadmap',
  'docs/current-house-baton',
  'docs/house-handoff-discovery',
  'docs/monolith-concept-art-backlog-2026-08-26',
  'docs/p1-monolith-character-concepts-2026-08-28',
  'docs/sea-above-system-shader-breakdowns-2026-08-26',
  'docs/toolchain-consolidation-2026-08-31',
  'docs/university-prep-2026-09-03',
  'feat/2026-09-02-front-door-cymatic-sanctuary',
  'feat/2026-09-02-github-pages-atmosphere',
  'feat/2026-09-02-melodia-folio-threejs',
  'feat/2026-09-02-music-key-threejs',
  'feat/2026-09-02-runtime-persistence-closure',
  'feat/2026-09-04-melusina-house-gn-foundation',
  'feat/site-ink-breath-resonance',
  'feature/credits-20260813',
  'feature/echo-topo-chapter2',
  'feature/p0-closeout-2026-09-02',
  'feature/repo-lockin-20260813',
  'feature/sea-above-choralsheep-20260826',
  'feature/zenforest-glam-headless',
  'fix/blender-live-sync-source',
  'fix/house-handoff-path',
  'fix/laptop-sparse-discovery',
  'fix/laptop-sparse-discovery-current',
  'fix/portable-git-mcp',
  'fix/portable-root-launchers',
  'fix/portable-workstation-helpers',
  'fix/portable-workstation-helpers-current',
  'fix/site-status-workflow',
  'fix/sync-require-main',
  'fix/sync-safe-return-main',
  'fix/sync-safe-return-main-current',
  'fix/two-workstation-sync',
  'integrate/2026-09-02-b00-governance',
  'integrate/2026-09-02-b01-docs-fixtures',
  'integrate/2026-09-02-b02-runtime-source',
  'integrate/2026-09-02-b03-first-party-plugins',
  'integrate/2026-09-02-b04-houdini-engine',
  'integrate/2026-09-02-b05-authoring-toolchain',
  'integrate/2026-09-02-b06-character-gameplay-content',
  'integrate/2026-09-02-b07-remaining-content',
  'integrate/2026-09-02-b08-recovered-residue',
  'integration/2026-09-02-front-door-cymatic-sanctuary',
  'integration/house-handoff-20260904',
  'integration/house-handoff-current-20260904',
  'integration/laptop-house-recovery-20260904',
  'integration/promote-house-baseline-20260904',
  'pr/melusina-v22-sync',
  'recovery/laptop-main-20260904',
  'recovery/main-merged-20260904',
  'recovery/snapshot-20260903',
  'recovery/snapshot-20260903-1840',
  'recovery/unify-histories-20260904',
  'rescue/web-threejs-recovery-2026-09-05',
  'rescue/web-threejs-recovery-current-main',
  'triage/nemotron-research-p3'
)

function Invoke-Git {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  & git @Args
  if ($LASTEXITCODE -ne 0) {
    throw "git $($Args -join ' ') failed with exit code $LASTEXITCODE"
  }
}

function Get-RemoteHeadSha {
  param([string]$Branch)
  $out = & git ls-remote --heads $Remote "refs/heads/$Branch"
  if ($LASTEXITCODE -ne 0) { return $null }
  if (-not $out) { return $null }
  return (($out -split "\s+")[0]).Trim()
}

function Get-RemoteTagSha {
  param([string]$Tag)
  $out = & git ls-remote --tags $Remote "refs/tags/$Tag"
  if ($LASTEXITCODE -ne 0) { return $null }
  if (-not $out) { return $null }
  return (($out -split "\s+")[0]).Trim()
}

$repoRoot = (& git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $repoRoot) {
  throw "Run this from a clone of MelodiaMelusinaV2."
}

$dirty = (& git status --porcelain)
if ($dirty) {
  throw "Worktree is dirty. Commit/stash first; remote pruning is intentionally blocked."
}

Invoke-Git fetch $Remote --prune --tags

$mainSha = Get-RemoteHeadSha "main"
if (-not $mainSha) {
  throw "Could not resolve $Remote/main."
}

Write-Host ""
Write-Host "Melodia remote branch hygiene — 2026-09-05 snapshot"
Write-Host "Remote:      $Remote"
Write-Host "Main:        $mainSha"
Write-Host "Candidates:  $($Candidates.Count)"
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

  # Fetch the exact remote tip into a temporary remote-tracking ref if needed.
  Invoke-Git fetch $Remote "refs/heads/$branch:refs/remotes/$Remote/$branch"

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
      if ($remoteTagSha -ne $sha) {
        throw "Archive tag $tag already exists at $remoteTagSha, but branch $branch is $sha. Refusing deletion."
      }
    } else {
      $localTagSha = (& git rev-parse -q --verify "refs/tags/$tag" 2>$null)
      if ($LASTEXITCODE -eq 0 -and $localTagSha) {
        if ($localTagSha.Trim() -ne $sha) {
          throw "Local archive tag $tag points somewhere else. Refusing deletion."
        }
      } else {
        Invoke-Git tag $tag $sha
      }

      Invoke-Git push $Remote "refs/tags/$tag:refs/tags/$tag"
      $remoteTagSha = Get-RemoteTagSha $tag
      if ($remoteTagSha -ne $sha) {
        throw "Remote archive verification failed for $branch. Expected $sha, got $remoteTagSha."
      }
    }

    Invoke-Git push $Remote --delete $branch

    $stillThere = Get-RemoteHeadSha $branch
    if ($stillThere) {
      throw "Branch deletion verification failed: $branch still resolves to $stillThere"
    }

    $action = "ARCHIVED + DELETED"
  }

  $results += [pscustomobject]@{
    Branch = $branch
    Ahead = $ahead
    Behind = $behind
    Action = $action
  }
}

$results | Sort-Object Action, Branch | Format-Table -AutoSize

Write-Host ""
if (-not $Execute) {
  Write-Host "Dry run only. No refs changed."
  Write-Host "Review the table, then run:"
  Write-Host "  powershell -ExecutionPolicy Bypass -File Tools/prune_remote_branches_2026_09_05.ps1 -Execute"
} else {
  Write-Host "Done. Every deleted branch tip was preserved under refs/tags/archive/branches/$ArchiveDate/..."
  Write-Host "Restore example:"
  Write-Host "  git push $Remote refs/tags/archive/branches/$ArchiveDate/<old-branch>:refs/heads/<old-branch>"
}
