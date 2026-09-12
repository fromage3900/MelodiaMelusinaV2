# Grok research fold-in — 2026-08-11

Four parallel Cursor research agents (read-only, **no git branches**, no PRs). Folded into LIVEOPS + MOBILE_SCAN SOPs on `cursor/v2-game-foundation-098b`.

| Agent | URL | Branch |
|-------|-----|--------|
| Study V2 repo health | https://cursor.com/agents/bc-9c80f257-a1f1-598f-bd90-a228d84ba342 | none |
| Explore collab and 50MB LFS | https://cursor.com/agents/bc-afb59bb0-1a6b-59e0-a344-5842b8ad12fd | none |
| Explore Universal BP physics | https://cursor.com/agents/bc-2b434383-bd2f-587b-8cd3-cbe3ef951069 | none |
| Review JRPG template BPs | https://cursor.com/agents/bc-f78d98a8-d053-5afb-8ca7-0911cce21356 | none |

## Durable conclusions (already mostly shipped on foundation PR)

1. **V2 health = partial** — fine for docs/code agents; not a clean claim surface without ledger + fixed onboarding. Onboarding tiers + LFS audit + `git_safe_push` range checks landed on this PR.
2. **`lightweight` ≠ 50 MB** — measured ~1.9 GB. Use `docs50` / `slice50` / `placement50`; `gameplay` is the ~2 GB path.
3. **Phone = text only** — no broad `git lfs pull`, no mesh/mocap LFS pushes from iOS.
4. **Universal placement binaries live in EnvSandbox** — cloud often has **0** EnvSandbox `.uasset`s. HOLD until Windows `git lfs pull`; Python builders ≠ binary proof.
5. **JRPG authority stays stock** — keep/wire `BP_BattleUI` + `BP_BattleController`; Melodia overlays only. Detail: [`JRPG_BP_REPLACEMENT_PRIORITY_2026-08-11.md`](JRPG_BP_REPLACEMENT_PRIORITY_2026-08-11.md). Never Python-load skill BPs.
6. **Echo `runtime` stays OPEN** until real `OnKeyDown` + ledger row — research agreed with evidence standard.

## Windows-only (cannot run from this cloud agent)

This foundation agent has `usePrivateWorker: false` — no Cursor PC subagent path. On the UE box:

```powershell
git fetch origin
git checkout cursor/v2-game-foundation-098b
git pull
git lfs pull --include="Content/EnvSandbox/**,Content/TurnBasedJRPGTemplate/**"
python Tools/lfs_health_audit.py --manifest specs/collab_slices/placement50.json
python Tools/sculpt_intake_check.py --limit-mb 50
# Rokoko one-time:
powershell -ExecutionPolicy Bypass -File Tools\setup_rokoko_livelink_plugins.ps1
# Editor open:
#   import import_rokoko_mocap as r; r.main(import_only=False)
```

## Not folded as new process

- PCG ~49% scale / VolumeSampler zero-emit findings → keep in EnvSandbox audit track; not sculpt/mocap SOP.
- MeshBlend → RVT/DF → owner art-direction; never-touch materials still apply.

## SuperGrok share (2026-08-11) — landed on this branch

Share: https://grok.com/share/bGVnYWN5LWNvcHk_c7761e0a-252b-44bf-b4de-4940025d6de0  
Grok could not push (GitHub contents write 403). Cursor foundation branch absorbed:

| Path | Content |
|------|---------|
| `Docs/Handoffs/PIE_2026-08-11.md` | Owner PIE (empty highway, Sir CTRL, UI alpha, Kaleido dead triggers) |
| `Docs/PhoneOps/HIGHEST_LEVERAGE_NOW.md` | RT-001…007 / PH-* |
| `Docs/PhoneOps/MOBILE_LANES.md` | Drive / Live Link / Polycam lane split |
| `Docs/Research/STYLIZED_ENV_PACK_SHORTLIST_2026-08-11.md` | Cute/mystical/underwater Fab shortlist |
| README / CURRENT_STATE / PhoneOps INDEX+BACKLOG | Front door + Echo + this-week focus |
