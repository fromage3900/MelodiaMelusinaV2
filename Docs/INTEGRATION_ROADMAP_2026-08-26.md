# Integration roadmap — 2026-08-26

**Scope:** infrastructure preparation only. No gameplay, Blueprint, or architecture changes.

This doc ties together the recommended **top-tier solo/small-team UE workflow** for MelodiaMelusinaV2: what to use, what to defer, and what not to do.

**Binding rules:** [_AGENT_WORKING_AGREEMENT.md](../_AGENT_WORKING_AGREEMENT.md) · [GIT_BATCH_DISCIPLINE.md](GIT_BATCH_DISCIPLINE.md) · [ECHO_PIPELINE_2026-08-09.md](ECHO_PIPELINE_2026-08-09.md)

---

## Recommended stack

| Layer | Choice | Why for Melodia |
|-------|--------|-----------------|
| **Content SCM** | Perforce Helix Core Free (**hybrid**) | Measured LFS/lock failures ([PERFORCE_MIGRATION_PLAN_2026-08-13.md](PERFORCE_MIGRATION_PLAN_2026-08-13.md)); Epic-native UE provider |
| **Code / docs / CI** | **GitHub** (`MelodiaMelusinaV2`) | Echo pipeline, hooks, self-hosted runner, branch protection, phone/cloud agents already invested |
| **Private reachability** | **Tailscale** | One overlay for SSH (phone/WSL), Perforce `:1666`, self-hosted runner — no public ports |
| **Phone agents** | Cursor Cloud + WSL tmux | [PhoneOps/REMOTE_WSL_AGENT_STACK_2026-08-25.md](PhoneOps/REMOTE_WSL_AGENT_STACK_2026-08-25.md) |
| **Evidence / gates** | Echo ledger + `record_gate.py` | Do not replace with Perforce Swarm for gameplay certification |
| **Interim (before P4 live)** | UE `GitSourceControl` + LFS locks | ~1 hour; disposable if Perforce lands (Aug-13 cheap wins) |

```text
Phone / Cursor Cloud ──► GitHub (code, docs, CI, PRs)
Tailscale ──────────────► Windows PC ──► WSL tmux agents ──► Git
Tailscale ──────────────► Helix //melodia (Content, Exports, RawArt) [planned]
UE Editor ──────────────► Monolith :9316 (one instance, serialized)
```

---

## Perforce prep (current phase)

| Artifact | Path |
|----------|------|
| Design plan | [PERFORCE_MIGRATION_PLAN_2026-08-13.md](PERFORCE_MIGRATION_PLAN_2026-08-13.md) |
| Execution handoff | [PERFORCE_MIGRATION_HANDOFF_2026-08-26.md](PERFORCE_MIGRATION_HANDOFF_2026-08-26.md) |
| Setup guide | [Handoffs/PERFORCE_SETUP_GUIDE_2026-08-26.md](Handoffs/PERFORCE_SETUP_GUIDE_2026-08-26.md) |
| Typemap / ignore | [Perforce/typemap.melodia.txt](../Perforce/typemap.melodia.txt), [Perforce/p4ignore.txt](../Perforce/p4ignore.txt) |
| Read-only preflight | `python Tools/perforce_migration_preflight.py [--json]` |

**Status:** PREP landed in repo; **P4 not live** until owner completes P0 decide + P1–P7 on PC.

**P0 gate (~30 min, owner):** Record hybrid vs stay-on-git in `_DECISION_LOG.md`.

---

## GitLab — optional, not default

**Do not move primary off GitHub** unless you intend to rebuild Echo, hooks, and agent docs.

| Tier | Use | When |
|------|-----|------|
| **P8a — mirror** | Read-only push mirror of `main` for backup/visibility | Owner wants off-GitHub copy; credentials stay outside repo |
| **P8b — CI DR** | GitLab CI runs static/docs jobs only (duplicate of `echo_gates.yml`) | GitHub outage tolerance |
| **Not recommended** | Full GitLab primary + LFS | Duplicates LFS billing pain; splits PhoneOps and cloud agent paths |

Mirror setup (owner-only, no secrets in repo):

1. Create empty GitLab project (private).
2. GitHub → Settings → Repository → Mirroring, or `git remote add gitlab …` push mirror on release tags only.
3. Document mirror URL in `_DECISION_LOG.md`, not in committed tokens.

---

## Azure DevOps / Bitbucket

Enterprise alternatives only. No action unless hiring into that toolchain. SourceLink in .NET tooling already supports them; Melodia's authority remains GitHub + planned P4.

---

## Critical pre-P4 tooling seam

Before seeding `//melodia`, plan and implement:

1. **[Tools/art_gates.py](../Tools/art_gates.py)** — offline gates currently use `git ls-files` for Content paths. After migration, switch to `p4 files` or a scoped workspace walk ([PERFORCE_MIGRATION_PLAN P5](PERFORCE_MIGRATION_PLAN_2026-08-13.md)).
2. **Re-baseline** `specs/art_gates_baseline.json` and prove a planted violation still fails.
3. Same pattern for any script keyed on `git ls-files Content` (e.g. audit tooling cited in Aug-13 plan).

A gate that silently passes on zero assets is not a gate.

---

## Merge queue (2026-08-26)

Branch protection requires **one approving review**; cloud agents cannot merge.

| Order | PR / batch | Content |
|-------|------------|---------|
| 1 | **#22** | Doc batches (cleanup, monolith, nemotron, zenforest) |
| 2 | **Perforce batch** | This prep package + integration roadmap |
| 3 | **#15** | Melusina V22 textures/animations (LFS) |
| — | **#9** | **Do not merge wholesale** |

---

## PC checklist (after merges)

```powershell
git fetch --prune
git pull origin main
python Tools/perforce_migration_preflight.py --json
```

**Do not run yet:** `p4 typemap`, depot seed, `.uproject` provider enable, `git lfs prune`.

---

## Related

- [PhoneOps/INDEX.md](PhoneOps/INDEX.md) — phone/cloud front door
- [LIVEOPS_GIT_SOP_2026-08-11.md](LIVEOPS_GIT_SOP_2026-08-11.md) — trunk + Echo discipline
- [Handoffs/BRANCH_CLEANUP_2026-08-25.md](Handoffs/BRANCH_CLEANUP_2026-08-25.md) — stale branch hygiene
