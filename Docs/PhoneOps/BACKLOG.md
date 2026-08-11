# Backlog (Now / Next / Later)

Simple queue for phone agents. Prefer updating this file over inventing parallel TODO files. Source truth: `NEXT_ACTIONS.md`, `NEXT_HIGHEST_LEVERAGE_TASK.md`, `CURRENT_STATE.md`.

## Now

1. On Windows UE box: install jcode, run `.\deploy\start_jcode_swarm.ps1`, paste `.jcode/coordinator-bootstrap.md`, complete **Recipe A** then **Recipe B** (see `JCODE_SWARM_PIPELINE.md` acceptance checklists).
2. Finish Git LFS push of pending Content; confirm `origin/main` advances past 2026-07-24 tip.
3. Maintain `Docs/PhoneOps/` as the mobile entry.
4. Generic look-dev capture pass on `L_Template` when UE desktop/MCP is available.
5. MelodiaCore GS-001 / GS-002 when in gameplay lane.

## Next

1. Validate material-system repairs (Universal A/B/C layers, landscape Nikki scale, water parameter groups) via audits — no master rewrites. Kiro remaining tasks live under `.kiro/specs/material-library-improvements/`.
2. Decide `_github_deploy/` vs `my-site-clean/` promotion; until then keep package-to-website handoff on `_github_deploy/generated/`.
3. Wire `MF_VertexPaintBlend` into Universal as **switch-gated, default-off** after `_Scratch/` prototype (CURRENT_STATE).
4. Continue Baroque `*Ex` PCG spline unblock (CorniceEx pattern; BalconyEx subgraph / NaveVaultEx hatch still open). See also `.junie/plans/pcg-universal-expansion.md`.
5. AssetPassport seed set (NPC, room/env, gameplay, material/VFX) + no-mutation validator.
6. Recover or stub missing `Docs/ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md` (referenced by NEXT_HIGHEST; absent on main).
7. Triage open surreal draft PR #80 vs closed duplicate slice PRs before starting new surreal phone agents.

## Later / Backlog

- Zen Tier B/C modules (Goju-no-to, Tahoto, Honden, Sakura Torii variants) + genome → `.world.json` export.
- Material Maker Layer 1–3 surreal PBR engine + UE function translator.
- Houdini HDAs aligned to `surreal_arch_world_v1`.
- Interactive shoreline foam / character-driven water ripples.
- Ornament store screenshots + Gumroad (`store_live` stays false until then).
- Pillar hero captures for portfolio landscapes when editor is free.
- Full (non–Live Coding) MonolithEditor rebuild so capture PSO fix sticks across restarts.

## Explicitly not Now

- Sakura level composition / hero placement (human-owned).
- Deletes, master architecture rewrites, external publish.
- Writes under `Content/_PROJECT/`.

## How to update from phone

```text
Reconcile Docs/PhoneOps/BACKLOG.md with NEXT_ACTIONS.md and CURRENT_STATE.md.
Move finished items out; do not add speculative work. Commit + PR.
```
