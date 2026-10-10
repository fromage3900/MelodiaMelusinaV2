# Branch retirement checkpoint — 2026-10-10

**Status:** review-only / `0` remote branches deleted, `0` archive tags created.  
**Canonical authority:** [Branch & Workstation Policy](BRANCH_WORKSTATION_POLICY.md) and [Git Health Contract](GIT_HEALTH_CONTRACT.md).  
**Snapshot:** `specs/branch_retirement_census_2026-10-10.json` (`melodia.branch_retirement_census/v2`).  
**Command:** `Tools/prune_remote_branches.ps1` (dry-run default).  
**Retired historical command:** `Tools/prune_remote_branches_2026_09_06.ps1` (now fail-closed).

## What changed

The [2026-09-25 World Atlas census](../WorldAtlas/BRANCH_RETIREMENT_CENSUS_2026-09-25.md) enumerated 98 branches; that file remains valid only for historical context. The 2026-10-10 GitHub refresh originally found **165 remote branches including `main`**. Creating this review branch added a temporary 166th branch, so the new machine-readable snapshot records **165 non-main branch refs, inclusive of this temporary housekeeping branch at snapshot time**. That in-flight branch is **not** a retirement candidate. Exact SHA pins and a conservative HOLD disposition are retained for every unreviewed ref.

The new census records:
- **11 `ANCESTOR_CANDIDATE_REVIEW`**: GitHub `main...head` compare confirmed `ahead_by=0` for exactly these refs; they are first-batch review candidates, not deletion approvals;
- **3 `ACTIVE_PR_HOLD`**: #438 Pi/AIRI, #439 ornament release packaging, #440 GitHub bounty scout;
- **21 `PROVENANCE_HOLD`**, **8 `WORKSTATION_OR_ASSET_HOLD`**, **29 `HISTORICAL_HOLD`**, **44 `HISTORICAL_CANONIZED_UNVERIFIED`**, **49 `UNREVIEWED_HOLD`**.

Do not confuse a merged PR with branch-tip reachability. In particular `chore/houdini-checkpoint-reconcile-20261007`, `lane/sir-melodious-flight`, `feature/canon-ui-svg-source-20261004` and recovery/workstation refs need specific provenance rules even if their meaningful work has been landed through a different commit.

## First review batch: proven ancestor tips, still owner-gated

These have *zero* unique commits relative to the recorded `main` SHA `c71503b9b715b30d96786543df2ec1566b3a4bb5`. The retirement command rechecks exact SHA and ancestry against the **current** `origin/main` before acting. Their historical branch names must not be interpreted as active production authority.

| Exact branch | 2026-10-10 behind count | Note |
|---|---:|---|
| `feature/runtime-animation-convergence` | 262 | Old animation work already reachable from main; check local editor/worktrees |
| `feature/piano-cymatic-ripples-20261003` | 95 | No branch-only commits |
| `feature/piano-hue-flash-sound-20261004` | 84 | No branch-only commits |
| `feature/seasonal-biomes-hue-strobe-20261004` | 76 | No branch-only commits |
| `feature/oceanology-stock-param-drive-20261003` | 95 | No branch-only commits |
| `converge/research-sweep06-20261004` | 73 | No branch-only commits |
| `feature/melusina-jev-weapon-bridge-20260928` | 313 | No branch-only commits |
| `feature/archery-waveharp-slice` | 214 | No branch-only commits |
| `fix/morning-ofpa-drift-2026-10-01` | 286 | No branch-only commits |
| `integration/merge-origin-main` | 162 | Former integration ref; require explicit workstation/agent verification |
| `feature/hybrid-combat-bridge-2026-09-28` | 375 | Old hybrid prototype; don't confuse with unique `converge/hybrid-flow-367-20261001` (+18 / -271) |

**Do not move into this batch without a new comparison:** `feature/golden-piano-keys-reactive-wiring-20261003` (+2), `feature/hermes-h1-router-lease-2026-10-01` (+13), `feature/local-main-recovery-20261004` (+4), `converge/hybrid-flow-367-20261001` (+18), `cleanup/scm-closeout-20261005` (+4 and a large binary/protected-file surface), and `feature/universe-foundry-ue-staging-20260922`. Their unique work or P4/LFS history must be deliberately reconciled; never bulk merge or delete.

## Runbook (one bounded owner-approved batch)

From a clean, freshly synchronized Windows clone (UE editor closed, Perforce locks and other agents checked, `main` checked out):

```powershell
python Tools/git_ok.py
python Tools/agent_lane_registry.py status
git status --short --branch
git worktree list --porcelain
git fetch --prune origin
python Tools/branch_health.py --json branch_health_current.json

# SAFE: only reads Git ancestry and remote refs; shows archive/delete proposal.
.\Tools\prune_remote_branches.ps1
```

The new script allows normal **forward-only** movement of `origin/main` after this PR merges, but refuses if the snapshot's pinned main SHA ceases to be an ancestor (history replacement). It refuses on candidate branch-tip changes, unproven ancestry, a local branch/worktree checkout, a conflicting archive tag or any non-candidate/held disposition.

Only **after reviewing the exact per-branch list, LFS/Perforce provenance, and concurrent workstation/agent activity**, a chosen single branch could be retired with all explicit opt-ins:

```powershell
.\Tools\prune_remote_branches.ps1 -Execute -ApprovedBranches "feature/piano-cymatic-ripples-20261003" -ConfirmBatch "RETIRE-2026-10-10" -WorkstationsCleared
```

That example is a future manual owner action, **not** an action already taken or authorized by creating this PR. The script creates/pushes a lightweight `archive/branches/2026-10-10/<branch>` tag, reads it back from the remote, then deletes the exact branch tip with `--force-with-lease`. A different remote SHA aborts the deletion. Restore example:

```powershell
git push origin "refs/tags/archive/branches/2026-10-10/feature/piano-cymatic-ripples-20261003:refs/heads/feature/piano-cymatic-ripples-20261003"
```

Note that Git branch-tip preservation does not back up unpublished local files, stashes, Perforce changelists, or binary blobs held only in another workstation. Those require separate machine-level checks.

## Stop the graveyard growing

Keep the existing mechanisms as the single workflow:
1. Agents: `deploy/new_agent_lane.ps1` creates detached worktrees and `refs/agents/<lane>` pins (not permanent remote branches).
2. Integrator: `deploy/land_agent_lane.ps1` lands one bounded delta and removes its temporary PR branch.
3. Integrator: `Tools/guard_branch_lifecycle.py` rejects stale PR integration (default 8 commits behind).
4. Production: `main` remains the single runtime authority; preserve intentional `collab/laptop/longterm`, recovery and operational refs.
5. Maintenance: refresh this census only when it resolves ambiguity or a concrete Git blocker. Do **not** optimize branch count for its own sake.

## Proof limits

- **GitHub:** remote branch-tip census, selected compare results and currently open PRs verified on 2026-10-10.
- **Static:** tools/source written, but PowerShell execution and Windows worktree/Perforce checks **not run from this chat**.
- **Live Unreal:** not accessed or modified.
- **Remote deletion:** none performed.
- **Next gate:** review PR checks, test the dry-run on the actual Windows clone, approve at most a small candidate batch, then execute manually in an owner-controlled session.
