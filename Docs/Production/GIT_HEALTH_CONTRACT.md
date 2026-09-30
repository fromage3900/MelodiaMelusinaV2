# Git health contract

**Status:** binding repository-health policy.  
**Authority:** `origin/main` is canonical. This document describes source-control health, not gameplay/project status; `CURRENT_STATE.md` remains the sole project-status authority.

## Healthy means

A healthy Melodia repository satisfies all of these at once:

1. **Main is a landing target, never a workspace.** Agents work in detached lane worktrees pinned by `refs/agents/<lane>`. Direct work on `main` is refused locally.
2. **Every integration is bounded.** A PR has one intent, an effective diff that can be reviewed, and is no more than 8 commits behind current `origin/main`. Stale work is reconverged from current main; stale branches are not revived.
3. **No hidden authority bypass.** Local hooks, Echo CI, LFS checks, protected-asset guards, and branch lifecycle checks agree on the same integration rules.
4. **Binary history is deliberate.** Unreal/DCC/media assets remain LFS pointers where required, outgoing LFS batches stay within policy, and Perforce-owned/raw-export paths are not casually absorbed into Git.
5. **Proof follows the change.** Source-only/static changes require Echo. UE runtime claims additionally require the appropriate build/automation/PIE or packaged proof; static green never substitutes for runtime evidence.
6. **Old refs are provenance, not workspaces.** Merged/ancestor branches may be archived and pruned only after recoverability is established. Unique or open-PR branches are held for classification.
7. **One writer owns shared control files.** `CURRENT_STATE.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`, `.gitattributes`, source-control ownership, and verification entry points remain integrator-owned.

## Canonical integration path

```text
fresh origin/main
  -> detached agent lane + explicit path claims
  -> bounded commits; pin refs/agents/<lane> after every commit
  -> integrator computes origin/main..lane
  -> temporary remote integration branch
  -> PR
  -> Echo Offline static gates
  -> required runtime proof when the change claims runtime behavior
  -> rebase merge
  -> delete temporary branch
  -> fast-forward primary main
```

A lane/branch more than 8 commits behind main is not updated merely to preserve its identity. Preserve the intended delta, reconverge it onto current main, verify the effective diff, and retire the stale integration source.

## Daily health run

Run these before beginning multi-agent integration work and after a large landing:

```powershell
git fetch --prune origin
git status --short --branch
git rev-list --left-right --count main...origin/main
python Tools/agent_lane_registry.py status
python Tools/guard_branch_lifecycle.py --base origin/main --max-behind 8
python Tools/lfs_health_audit.py --game-paths-only
python Tools/health.py --offline --json
python Tools/art_gates.py --summary
python Tools/credits_gate.py
python Tools/validate_git_health_contract.py
```

For a candidate lane, additionally inspect:

```powershell
git log --oneline origin/main..refs/agents/<lane>
git diff --stat origin/main...refs/agents/<lane>
git diff --name-status origin/main...refs/agents/<lane>
```

Do not land if the effective diff contains unrelated history, unexpected binary assets, a second authority implementation, or single-writer files that were not deliberately handled by the integrator.

## PR promotion gates

A PR is eligible to land only when:

- it is based closely enough on current main to satisfy the lifecycle guard;
- its effective diff matches its stated intent;
- Echo Offline static gates pass on the PR head;
- LFS budget + pointer health pass;
- no protected/collapsed/deprecated path guard fails;
- no unresolved lane claim collision exists;
- runtime evidence required by the PR's claims is recorded;
- no newer main change invalidates the proof.

**Historical PRs and branches never count as current health failures merely because they are stale.** They matter only if reopened, reused, or carrying unique work that is about to be integrated. PR #201 is resolved historical provenance and must not be used as a health proxy.

## Branch/ref disposition

Use four states:

- **ACTIVE** — current lane or open integration PR with a bounded delta.
- **HOLD** — unique/unclassified work; do not merge or delete.
- **PROVENANCE** — superseded source/reference retained only for archaeology.
- **PRUNE-SAFE** — exact merged tip or ancestor of main with a verified archive tag.

Never infer PRUNE-SAFE from age or branch name.

## CI and GitHub-side enforcement

Echo's `Offline static gates` job is the canonical source-only merge gate. GitHub branch protection/rulesets should require that check for `main` so web/API merges cannot bypass local hooks. GitHub settings are external to the repository, so this requirement must be verified separately by an owner/admin.

Recommended `main` settings:

- require a pull request before merge;
- require `Offline static gates` to pass;
- block force pushes and branch deletion;
- prefer linear/rebase integration;
- keep the required check name unique across workflows.

Do not make editor-backed UE gates mandatory on every PR while the UE58 runner is intentionally manual/offline. Runtime-changing PRs instead remain draft/unmergeable by project policy until their explicit UE proof is attached.

## Failure response

When health fails, repair the smallest violated invariant:

- **Echo red:** diagnose the first real failing gate; do not weaken the gate.
- **stale branch:** reconverge bounded delta from fresh main; do not merge stale history forward.
- **LFS failure:** stop the integration and repair pointer/budget/ownership state before retrying.
- **claim collision:** one writer stops; do not race.
- **unexpected binary diff:** classify ownership and provenance before touching it.
- **dirty primary main:** preserve work first, then move it into a lane; never destructive-clean by reflex.
- **historical branch with unique work:** HOLD and document the salvage decision.

The objective is not zero branches. The objective is **zero ambiguous integration state**.
