# Multi-agent lanes

**Binding.** Several agents share this repository. This file is the contract that keeps
them from overwriting each other. It is enforced by `.githooks/pre-commit` and
`.githooks/pre-push`, not by goodwill.

**Companion:** [`BRANCH_WORKSTATION_POLICY.md`](BRANCH_WORKSTATION_POLICY.md) defines the branch
classes and the `green main → one bounded intent → one scoped branch → PR → main` spine, including
its §0 rule that a background agent must never move the checked-out branch under live editor state.
That rule was written 2026-09-08 and was still being violated on 2026-09-29. This file defines *how
multiple agents share that spine* without moving `HEAD` under each other.

## The one rule

> **`main` is not a place you work. It is a place work lands.**

| | |
|---|---|
| Agents | commit in a **lane**, never push, never open a PR |
| Integrator | owns `main`, owns the single-writer paths, lands lanes |
| `main` | advances only through the integrator |

## Do not create branches

Branches accumulate and get forgotten; that is how a checkout ends up 22 commits
behind on a branch whose PR merged days ago.

A lane pins its work with a **ref**, not a branch:

```
refs/agents/<lane>        # a ref: never appears in `git branch`, never accumulates
```

Git only lists `refs/heads/*` as branches, so a repo with any number of active lanes
still shows zero working branches. The canonical landing path creates **one temporary
remote branch per landing and preserves it by default** for recovery/provenance. Deleting
that branch or fast-forwarding the primary checkout requires explicit owner switches
(`-OwnerApprovedBranchDeletion`, `-OwnerApprovedPrimarySync`).

## Start a lane

```powershell
.\deploy\new_agent_lane.ps1 -Lane cline -Task houdini-deposition
.\deploy\new_agent_lane.ps1 -Lane pi -Task hybrid-combat -Paths Source/BS_GodFile -Globs "Docs/Production/**"
```

That creates `_worktrees\lane-<lane>` on a **detached HEAD** cut from `origin/main`,
pins `refs/agents/<lane>`, and registers the lane. It does not branch and does not touch
the primary checkout.

Then work there, in the lane worktree, not in `BS_GodFile`:

```powershell
cd ..\_worktrees\lane-cline
```

## After every commit, pin the ref

```powershell
git -C ..\_worktrees\lane-cline update-ref refs/agents/cline HEAD
```

This is what makes lane work durable without a branch. If the ref is not updated, the
commit is reachable only from the worktree's HEAD and can be lost to a prune.

## Hand it over — do not push

```powershell
.\deploy\land_agent_lane.ps1 -Lane cline -OwnerReviewedLocalState
.\deploy\land_agent_lane.ps1 -All -OwnerReviewedLocalState
.\deploy\land_agent_lane.ps1 -All -DryRun
```

The integrator computes `origin/main..refs/agents/<lane>`, pushes that ref to a temporary
branch, opens a PR, and rebase-merges it. The temporary branch is **preserved by default**;
branch deletion and primary fast-forward are opt-in owner approvals. Landing is fail-closed
when local UE/Houdini/Perforce state cannot be verified (`Tools/agent_lane_local_authority.py`).
Agents never push.

## What is refused, and by which hook

| Attempt | Result |
|---|---|
| `git commit` while `HEAD` is `main` | **refused** — `main` is not a working branch |
| commit by a lane to a single-writer path | **refused** — belongs to the integrator |
| commit by a lane to a path another live lane claims | **refused**, names the owning lane |
| `git push origin main` | **refused** (pre-existing policy, unchanged) |
| `git push` of anything outside `refs/heads/*` and `refs/tags/*` | **refused** — added 2026-09-30, closes a `refs/agents/*` bypass of the LFS gate |
| branch name outside the allow-list | **refused** (pre-existing policy, unchanged) |

## Single-writer paths

Only the integrator may write these. Put status changes in the PR body, not in the file:

```
CURRENT_STATE.md   AGENTS.md   CLAUDE.md   .gitignore   .gitattributes
specs/source_control_ownership.v1.json   deploy/run_verify.ps1
```

## Claims

A claim is live for 30 minutes after its last heartbeat. An agent that dies stops
blocking the repo on its own; nobody has to clean up by hand.

```powershell
python Tools/agent_lane_registry.py claim --lane cline --path Tools/world_compiler.py
python Tools/agent_lane_registry.py heartbeat --lane cline     # on every commit
python Tools/agent_lane_registry.py release --lane cline       # when done
python Tools/agent_lane_registry.py status                     # who holds what
python Tools/agent_lane_registry.py reap --confirm             # release expired claims
```

## Overrides

Both are explicit, greppable, and for deliberate reviewed changes only:

```powershell
$env:ALLOW_MAIN_COMMIT = '1'   # a deliberate integrator commit on main
$env:SKIP_LANE_GUARD   = '1'   # bypass the lane guard entirely
```

## Why this exists

Recorded so the lesson survives the session:

- Two agents committed onto `main` minutes apart; each commit moved `HEAD` under the
  other agent's working directory. Neither was doing anything wrong — there was simply
  one shared mutable ref and no rule about it.
- Untracked scratch is checkout-local. The 2026-09-27 and 2026-09-28 plans
  (`.hermes/plans/`) existed, were never committed, and are gone; `git log --all` has no
  trace of them. Plans now stay visible in `git status` so they get committed.
- A checkout was left on `feature/spout-beauty-2026-09-26` after its PR merged, so it
  could not see 22 commits of fixes, the sync tooling, or the docs it was citing.
  `Tools/guard_branch_lifecycle.py` now retires that branch name outright.
