# PLAN — Tonight's Morning renders: quickest wins (Jev `jev-1.13.0`, live 2026-09-24 ~19:57)

**Goal (bounded, tonight):** an upgraded S2 hero-cam sheet for `L_MelusinaMorning` — draft v2 —
with the day's procedurally-generated content visible (island biome, crystal garden, WestRim rocks,
glitter) and **no placeholder assets in final tiles**; then, if the night holds, the one pipeline
quick win (C2 rainbow meadow via PCGEx collections) as a v3 tile.
**Placement:** satisfies the "close out with the updated render setups" item; sits inside the
2026-09-23 hero-render plan and the convergence plan's C2. **Status authority:** `CURRENT_STATE.md`.

## Jev audit (live, one call — log `Prototypes/JevMorningRenderPlan/audit_log.json`)
- First block: **S2_V2_RECAPTURE_FIRST 0.76** (RAINBOW_MEADOW_C2_FIRST 0.24; PLAZA 0.00;
  PIPELINE_STORY 0.00), confidence 0.68. The recapture outranks C2 for tonight — C2 is the
  first pipeline win *after* v2 ships, not before it.
- Riskiest: **EDITOR_STABILITY_AND_LOCK 0.81** (C2_SCRIPTING_GAPS 0.18) — today's OOM crash,
  an unlogged exit, and another live session make the editor, not the art, the volatile piece.
- Needs owner: **noul 0.82** — final framing, placeholder handling, and the upload eyeball are yours.
- Readiness: **1.9 / 4** — cameras + draft + new content live; recapture path proven; three open defects.

## What exists (verified tonight)
- Hero cams already in the level: `CAM_Hero_01 Meadow`, `CAM_Hero_02 Spiral Ascent`,
  `CAM_Hero_03 Rim Overlook`, `CAM_Hero_04 House`; capture raw dirs `…/S2/raw`, `…/S2/raw_house`.
- Draft v1: `Saved/Portfolio/ContactSheets_20260924/S2/S2_Melusina_HeroCams_DRAFT_v1.jpg` (05:06).
  Defects (vision-verified) to clear before anything ships:
  1. white placeholder mannequin + black animal **in frame** (tiles Meadow / House);
  2. rock underside reads purple / incomplete (tile Rim Overlook);
  3. cyan-emissive house frame overbright (tile House);
  4. capture header: texture streaming was **still settling** — capture only after it settles.
- New since the draft: biome 992 / crystals 205 / WestRim art rocks 25 (greybox gone) / glitter 57 /
  golden spiral treads. World Compiler boards recaptured today
  (`Saved/Audit/Screens/wc_morning_rainbow_bloom_*_2026-09-24.png`) — usable with zero editor risk.
- Capture path: PIE capture with fill light (proven). **MRQ stills remain untested here** — the
  night does not bet on them.

## Steps (each ends in a gate; additive only; one editor, one holder)

### R0 — Editor, carefully (the 0.81 risk)
- Exactly one editor. Before relaunch: one check of `Get-Process UnrealEditor` + port 9316; the
  MultiWorld probe session is live on the machine — if it holds the editor, wait or coordinate;
  never two. Announce before starting PIE.
- Relaunch the project; wait for Monolith `:9316`. **No bulk texture-heavy loads** (today's OOM
  came from building the pack's textures — do not repeat; logic-only loads).
- **Gate:** editor up, `L_MelusinaMorning` loaded, Monolith answering, no foreign dirty packages.

### R1 — Defect pass (minimal, provable writes)
- Identify the two placeholder actors visible in tiles 1/4 (white humanoid, black animal) by
  class/label; do not delete — hide, move out of frame, or swap for an owner-approved stand-in.
- Tile 3 purple underside: locate the exact rock mesh actor in the rim view; fix only if it is a
  one-line MI repair; otherwise flag to owner and reframe.
- Tile 4 cyan emissive: find the MI actually on the frame mesh; bring emissive to a photographic level.
- **Gate:** each fix re-read via reflection + a still from the affected cam; save only touched packages.

### R2 — Recapture (the deliverable)
- Let streaming fully settle after the level is idle (the draft's own header names this trap),
  then run the four cams with the proven PIE capture + fill light.
- Raws to `…/S2/raw_v2/`; assemble `S2_Melusina_HeroCams_DRAFT_v2.jpg` (same 2×2 + captions).
- **Gate:** four tiles, no placeholders, no purple, sane emissive, settled textures → owner eyeball.

### R3 — C2 rainbow meadow (pipeline quick win — only if the night holds)
- Build the PCGEx mesh collection(s) with per-entry rainbow MIs (the canonical meadow's
  14 weighted Short/Tall × band-MI pattern), wire the biome core to read collection entries;
  per convergence plan: **save + `reload_packages` before regenerating** (pins rebuild only then),
  prove with a live thin A/B (no stale cache), 0 PCG errors.
- One meadow cam recapture as the v3 tile showing the seven-band palette.
- **Gate:** instance count/scale/yaw unchanged (992 baseline), materials follow the collection.

### R4 — Pipeline story tile (zero editor risk, from disk)
- Compose: 09-24 WC boards + `Saved/Audit/massive_morning_20260924/` stills + counts
  (one graph → 992/205/25) + greybox→art before/after. One captioned tile or small side sheet.

## Owner items (noul 0.82)
1. Placeholder handling call (hide / swap / reframe) — taste, not engineering.
2. Final framing per cam — the sheet is owner-framed by design.
3. Eyeball v2 before any upload.
4. The plaza-structures path (kit bake + UE host) stays parked unless you call it — the kit is
   still a greybox shell and would sink the AAA-only bar tonight.

## Guards
- AAA-only in shipped sheets; placeholders never final. One editor; no level edits while the owner
  decorates; no new systems; single writer on every surface; MRQ not bet on.
- Massive World credit already staged in `Docs/CREDITS.md` (G0 cleared).
- Working tree holds uncommitted crystal-garden files (foundry-canon meshes) — do not switch
  branches tonight; captures only.

## Evidence paths
- Sheet: `Saved/Portfolio/ContactSheets_20260924/S2/` (v1 today; v2 tonight; `raw_v2/`).
- Fix receipts: `Saved/Audit/morning_render_fixes_20260924/` (per-fix JSON + stills).
- Jev log: `Prototypes/JevMorningRenderPlan/audit_log.json`.