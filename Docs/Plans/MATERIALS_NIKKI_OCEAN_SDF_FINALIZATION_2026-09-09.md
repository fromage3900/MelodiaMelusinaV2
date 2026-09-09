# Nikki landscape + Oceanology + SDF masters — finalization (2026-09-09)

**Pair:** Melodia bot (this chat) + New Bot  
**Gate before UE restart / Rokoko Live Link verify:** three isolated batches merged to **main**, each with a findable receipt under `Docs/Materials/`, plus `RECEIPT_ALL_MATERIALS_MERGED_*.md`.

## Why now
Owner asked for the same care as Melusina/Shorewake lookdev: Nikki landscape, Melodia Oceanology material, and SDF masters — methodical, documented, easy to find on git, then UE restart.

## Worktree truth (start here — do not dump)
Current branch: `feat/choral-sheep-root-c-material-proof-2026-09-08` with mixed dirty state (sheep coats, SDF ornament masters, Melusina ABP, **uproject LiveLink/Smartsuit flips**, etc.).

**Before any materials PR:**
1. Do **not** mix sheep Root-C, Rokoko LiveLink, and materials in one commit.
2. Park Rokoko: LiveLink/Smartsuit `.uproject` + `Plugins/Smartsuit` stay out of materials PRs (separate later PR after materials gate).
3. Prefer branching each materials batch from latest **main** (or a clean `materials/2026-09-09-*` stack), cherry-picking only the files that belong.

## Batch plan (healthy isolated merges)

### Batch 1 — Nikki landscape (`materials/nikki-landscape-2026-09-09`)
**Authority:** `M_Master_Toon_Landscape_HeightBlend` (+ Nikki convergence scripts/docs).  
**Do:**
- Audit compile/errors (Path layer history, triplanar pro defaults-off).
- Confirm Living Storybook contract still matches `LANDSCAPE_LIVING_STORYBOOK_MASTER.md`.
- Run read-only audits (`audit_landscape*.py` / validate_material) — no graph-clear rebuilds.
- If wiring gaps: fix in editor with backups under archive naming; document parameter map.
- PR includes: relevant `.uasset`/scripts **only if changed**, plus `Docs/Materials/RECEIPT_LANDSCAPE_NIKKI_2026-09-09.md` linking the living master doc.

**Done when:** zero hard material errors on landscape master; receipt lists authority path, instances touched, validate stats, and “do not run” scripts.

### Batch 2 — Oceanology material (`materials/oceanology-2026-09-09`)
**Authority:** Oceanology NextGen plugin + Melodia bridge (`MelodiaOceanologyWaterBridgeSubsystem`, cymatic bus, SLW horizon eater).  
**Do:**
- Reconcile enable state vs `OCEANOLOGY_ENABLE_STATE_2026-08-27.md` (EngineVersion metadata trap).
- Document material/MPC/SLW parameters Melodia owns vs plugin-owned.
- Confirm coexistence with Sea Above false-ocean rules (no second water authority).
- PR: bridge/code/docs only as needed; `Docs/Materials/RECEIPT_OCEANOLOGY_2026-09-09.md`.

**Done when:** receipt states plugin load verdict on 5.8, material/MPC knobs Melodia tunes, PIE smoke checklist, and “plugin off = no-op” still true.

### Batch 3 — SDF masters (`materials/sdf-masters-2026-09-09`)
**Authority:** blessed parents `M_Master_SDF_Toon`, `M_Toon_SDF`; utility toolkit; ornament SDF under `Content/EnvSandbox/Materials/Masters/SDF/` (currently dirty in worktree — triage carefully).  
**Do:**
- Diff dirty SDF masters vs HEAD; keep only intentional ornament/wiring changes.
- Reaffirm `sdf_parents_fix.json` blessed parents; no accidental reparent of Nikki hero / V9–V10 water.
- Receipt `Docs/Materials/RECEIPT_SDF_MASTERS_2026-09-09.md` with parent map + instance list.

**Done when:** blessed parents unchanged (or explicitly versioned), dirty SDF set explained, validate clean on touched masters.

### Merge gate
After Batches 1–3 on main:
- Write `Docs/Materials/RECEIPT_ALL_MATERIALS_MERGED_2026-09-09.md` (links the three receipts + git SHAs).
- Update this plan status to **COMPLETE**.
- **Then** clear UE restart for LiveLink/Smartsuit/Rokoko (separate PR for `.uproject` + Smartsuit plugin if not already on main).

## Lane split
| Who | Owns |
|-----|------|
| **Melodia bot** | Index + plan ownership; Batch 1 landscape audit/doc; coordinate merges; ALL_MATERIALS receipt; hold Rokoko until gate |
| **New Bot** | Batch 2 Oceanology enable/material inventory + receipt draft; Batch 3 SDF dirty triage vs HEAD + receipt draft; PR descriptions; watch CI |

Sync by pinging the other bot with PR URLs and receipt paths. No UE restart until Melodia bot confirms the ALL_MATERIALS receipt is on main.

## Out of scope
- Shorewake PearlWoven Phase 1–4 (separate)
- Rokoko Live Link verify / Meet2 capture
- Sheep Root-C material proof (finish or park on its own branch)

## Findability contract
Anyone cloning main should find materials truth in under 30 seconds:
1. Open `Docs/Materials/README.md` (this index)
2. Follow the three receipts + living docs linked above


## Authority correction (2026-09-09)
Active landscape master is `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape` per `Saved/Audit/landscape_authority_convergence_2026-09-03.json`. HeightBlend is legacy.



---

## Status footer (2026-09-09)

**GATE COMPLETE** via PR #156 (0441cbb) — ALL_MATERIALS receipt on main; Live Link / Rokoko soft-freeze lifted.

Follow-on cleanup (Batch 4 wiring, flipbook Lane D, deprecate/label): [MATERIALS_WIRING_FLIPBOOK_CLEANUP_2026-09-09.md](MATERIALS_WIRING_FLIPBOOK_CLEANUP_2026-09-09.md).
