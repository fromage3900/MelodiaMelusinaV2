# Collaborator Environment & Git Source Control — Implementation TODO

**Status:** In Progress (2026-08-05) — updated 2026-08-07 by project health review.

## Phase 0 — Git Reconciliation (P0)
- [~] Commit 5 dirty files in BS_GodFile — **escalated to 80+ modified files** (see `_SESSION_HANDOFF.md`); deferred to batched commit when owner has time to review
- [~] Fetch origin/main — **cannot proceed**: `github.com:443` network-blocked (see `_ROADBLOCKS_2026-07-31.md` §b)
- [~] Merge/rebase local 4 commits onto origin/main — **blocked on fetch above**
- [~] Attempt push (may be network-blocked) — **confirmed network-blocked**: local `main` diverged from `origin/main` but push fails; local commits (`6154cc1e`, `ec20b015`, `62eab10d`) are safe on disk

## Workstream A — Git Infrastructure ✅ COMPLETE
- [x] A1: Remove broken `my-site-clean` gitlink from index
- [x] A2: Remove broken `_github_deploy` gitlink from index
- [x] A3: Create `BS_GodFile/.githooks/` (pre-commit, pre-push, post-checkout)
- [x] A4: Enable `core.hooksPath`
- [x] A5: Fix `unreal_build.yml` stale G:\ path → C:\EnvironmentPortfolio\
- [x] A6: Retarget all Blender 5.1 references → 5.2 (C7 in _ROADBLOCKS — fixed 2026-08-07)

## Workstream B — Collaborator Documentation ✅ COMPLETE
- [x] B1: Rewrite `COLLABORATOR_SETUP.md` with Tier 1/2/3 onboarding
- [x] B2: Update `CONTRIBUTING.md` with `collab/[role]/[feature]` naming
- [x] B3: Link asset naming conventions to PIPELINE.md

## Workstream C — Validation & Automation
- [~] C1: Fix `collaborator_onboarding.sh` path bugs (BS_GodFile/ prefix) — **needs verification**: file now tracked as `deploy/collaborator_onboarding.sh`; `deploy/validate_collaborator_setup.sh` was modified 2026-08-05
- [~] C2: Enhance `validate_setup.ps1` — tier detection, Blender 5.1→5.2 — **Blender ref retargeted everywhere** (5.2 confirmed); verify no `validate_setup.ps1` still exists with stale refs
- [~] C3: Create `deploy/recover_orphans.py` scaffold — **not yet created**; blocked on Phase 0 git reconciliation (needs stable git first)

## Workstream D — Documentation Sync ✅ 2/4 complete
- [x] D1: Update `_ROADBLOCKS_2026-07-31.md` — git recovered, 2026-08-05 state added; C7/C14/G:paths marked resolved 2026-08-07
- [~] D2: Fix root `README.md` mojibake — **not yet verified**; root `README.md` content unknown, needs check
- [x] D3: Fix `Docs/QUEUE.md` C9 contradiction — resolution note present at line 96
- [~] D4: Update `_DECISION_LOG.md` — **confirmed through 035**; Decisions 036–045 need appending (referenced in GEMINI 08-06 handoff + BLUEPRINT_WIRING_CONTRACT, not yet in the log)

## Workstream E — Website Deploy (separate my-site repo)
- [~] E1: Add GitHub Pages deploy workflow to `my-site-deploy/` repo — **deferred**, separate repo
- [~] E2: Verify Pages config (user confirmation) — **needs user input**

## Workstream F — 0.1% Workflow Automation (NEW) ✅ COMPLETE
- [x] F1: Create `deploy/verify_critical_workflows.sh` — one-command runner for rare-but-critical gates
- [x] F2: Add git hooks for LFS/size validation (pre-commit)

## Tooling Health Gate (added 2026-08-07)
- [ ] G1: Add `pyproject.toml` with ruff config + pre-commit hook
- [ ] G2: Add trufflehog pre-commit hook / CI scan
- [ ] G3: Add lychee dead-link check to CI
- [ ] G4: Add git-sizer periodic check
- [ ] G5: Add markdownlint + codespell to pre-commit + CI
- [ ] G6: Expand pre-commit to flag 0-byte files + junk artifacts
- [ ] G7: Document tooling in `Docs/TOOLING_INVENTORY_2026-08-07.md`
