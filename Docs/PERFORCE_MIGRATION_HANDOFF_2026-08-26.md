# Perforce Migration Handoff — 2026-08-26

## Status

**PREP ONLY. Perforce is not live.**

This package makes the migration decision, safety rules, typemap, ignore rules, and read-only preflight available from GitHub on the Windows/Unreal PC. It does **not** provision Helix Core, move or delete assets, alter `BS_GodFile.uproject`, rewrite Git history, prune LFS, or change gameplay authority.

| Doc | Role |
|-----|------|
| [PERFORCE_MIGRATION_PLAN_2026-08-13.md](PERFORCE_MIGRATION_PLAN_2026-08-13.md) | Design authority — hybrid split, P0–P7 phases |
| [Handoffs/PERFORCE_SETUP_GUIDE_2026-08-26.md](Handoffs/PERFORCE_SETUP_GUIDE_2026-08-26.md) | Step-by-step Helix + Tailscale + hybrid seed |
| [INTEGRATION_ROADMAP_2026-08-26.md](INTEGRATION_ROADMAP_2026-08-26.md) | GitHub + P4 + phone/WSL + optional GitLab mirror |
| [PhoneOps/REMOTE_WSL_AGENT_STACK_2026-08-25.md](PhoneOps/REMOTE_WSL_AGENT_STACK_2026-08-25.md) | Private SSH overlay (Tailscale) — same transport family |

Machine-readable baseline: [Perforce/migration_baseline.json](../Perforce/migration_baseline.json) (update `main_sha` after each merge to `main`).

## Intended split (hybrid)

| System | Owns after acceptance | Current state |
| --- | --- | --- |
| **GitHub:** `fromage3900/MelodiaMelusinaV2` | `Source/`, `Tools/`, `Docs/`, `deploy/`, `Plugins/`, `Config/`, `specs/`, `.github/`, Echo CI | Code/docs reference; merge queue: #22 → Perforce batch → #15 |
| **Perforce:** planned `//melodia` | `Content/`, `Exports/`, raw art, other large lockable binaries | Not provisioned |
| **Git LFS** | Transitional protection for binaries still in Git | Keep until P6 acceptance |

**One path must have one owner.** Do not submit or edit the same path through Git/LFS and Perforce during transition.

## Remote baseline (audit 2026-08-26)

- Repository: `github.com/fromage3900/MelodiaMelusinaV2`
- GitHub `main` at audit: `23acba70` (refresh via `git rev-parse origin/main` after pulls)
- Prep branch: `cursor/perforce-docs-batch-ca02` (lands handoff + setup + tooling)
- Prior comparison baseline: `70f85d56`
- PR #15 V22 LFS payloads: present on remote; **not promoted** by this package alone
- P0 gameplay authority unchanged: wardrobe/equip → Glide → traversal → save/restart proof

## What to do on the Windows PC

Preserve uncommitted work first. **Never** run `git clean`, `git reset`, `git gc`, `git lfs prune`, or history rewrite.

After merging the Perforce prep PR to `main`:

```powershell
git fetch origin
git pull origin main
git config core.hooksPath .githooks
python Tools/perforce_migration_preflight.py
python Tools/perforce_migration_preflight.py --json
```

The preflight is read-only: Git provenance, dirty state, LFS pointers, whether `p4` is on PATH. It does not create workspaces, add/submit files, or delete anything.

If prep is not yet on `main`, read files from the prep branch without merging gameplay work:

```powershell
git fetch origin cursor/perforce-docs-batch-ca02
git show origin/cursor/perforce-docs-batch-ca02:Tools/perforce_migration_preflight.py > Tools/perforce_migration_preflight.py
python Tools/perforce_migration_preflight.py --json
```

Git LFS cannot hydrate bulk environment art that was never committed; use approved archive sources per onboarding docs.

## Safe migration sequence

1. **Preserve source checkouts** — record `git rev-parse HEAD`, branch, status, `git lfs status` before changes.
2. **P0 owner decide** — hybrid (recommended) vs stay-on-git; record in `_DECISION_LOG.md` or handoff note.
3. **Provision Helix** — depot `//melodia`, users, workspaces, verified backup.
4. **Typemap before first submit** — [Perforce/typemap.melodia.txt](../Perforce/typemap.melodia.txt).
5. **Seed staging workspace** — content roots only; hash-verify; Git copies untouched.
6. **Prove editor locking** — two sessions; second writer refused on `+l` types.
7. **Fix tooling seam** — [Tools/art_gates.py](../Tools/art_gates.py) must not rely on `git ls-files Content` after cutover; re-baseline art gates.
8. **Acceptance gate** — clean machine, `L_KaleidoNave`, P0 loop reproducible.
9. **Only after acceptance** — strip binary paths from Git (P6); update onboarding.

## Explicit holds

- No branch deletion, LFS prune, force push, or history rewrite.
- No merge of **#9** repo-lockin wholesale.
- No `.uproject` / `DefaultEngine.ini` changes without owner (`CLAUDE.md` never-touch).
- No public Perforce port exposure — Tailscale or private LAN only.
- No credentials in the repository.

When merged, this package version-controls the runbook and preflight. Server provisioning and acceptance evidence remain owner-controlled on the PC.
