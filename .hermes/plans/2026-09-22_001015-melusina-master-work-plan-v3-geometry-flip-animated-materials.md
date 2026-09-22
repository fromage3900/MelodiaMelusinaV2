# Melusina Master Work Plan v3 — Geometry Gate → FLIP Finalize → Hython/Copernicus Animated Materials

> **For Hermes:** Execute in order. Wave G is the GATE — Waves F and H start only after it.
> F and H run in PARALLEL once G closes (F's overnight bake and H's hython cooks never
> touch the same files). Supersedes the execution order in
> `.hermes/plans/2026-09-21_232652-melusina-master-work-plan-v2.md` — its loose-end
> register and rules remain binding. Deep convergence detail (Phases A–F) stays in
> `.hermes/plans/2026-09-21_232320-melusina-vfx-waterhair-flip-convergence.md`.
> Evidence standard: measured JSON (+ PNG where visual), fresh mtimes, never prose.

## State at plan time (verified 2026-09-21 23:30 – 2026-09-22 00:10)

- WIP banked twice: live 00:05, `.blend1` 23:36, BANKED copy 16:49. Persistent
  dirty-flag = asset-library links, not data risk.
- Live: GN angel wings (dials restored), 3 clockwork regalia rings (Scene Time,
  verified turning), water globs on all 3 render-hair strands (36/26/51 spheres,
  per-modifier dials), horns dials fixed + skull lift, 83 texture datablocks relinked.
- FLIP: bake copy `harp_bow_pipeline/Melodina_FLIP_bake_gen1.blend` (2.39 GB);
  addon `flip_fluids_addon` installed+enabled; **op ids resolved**:
  `flip_fluid_operators.flip_fluid_add` (add modifiers),
  `flip_fluid_operators.bake_fluid_simulation_cmd` (headless bake),
  `flip_fluid_operators.reset_bake`, `...cancel_bake_fluid_simulation`.
- Missing textures (unrecoverable, old G: layout gone): `t_me_chladni_*` (harp),
  SM_table/Teacup/Plate/CinnBun set, `bow_heights.bmp`/`bow_normals.bmp`, ~14 misc.
- Hython: `C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe`
  — editor-open safe, numpy+PIL; Copernicus loom 29 variants, 9 maps each;
  COPs bake chain proven on the dress; **Apprentice caps COP saves at 1080** —
  animated sequences go through the numpy lane, never COP File-COP (dead headless).

## WAVE G — Geometry polish / bevel / staging (the gate)

- **G1 Bevel audit (measured, per asset).** Socket probe per asset: count edges
  with face angle > 30° that are not beveled/smoothed. Assets: `FX_AngelWings_Carrier`
  (feather blades), `FX_ClockworkRing_*` ×3 (trimCurve end caps are the only hard
  edges), glob hosts (icospheres = already curved). Fix where needed with GN
  `Bevel Edges` / shade-smooth in the wrapper trees — dial state lives on node
  inputs; NEVER rebuild wrapper trees (erases dials). Audit JSON per asset.
- **G2 Staging.** All FX under `FX_Hero`; naming `FX_*`; no stray Scene-Collection
  objects (two retopo strays already hidden — purge decision owner-gated);
  transforms applied only where no armature constraint; origins at pivot of motion.
- **G3 Polish pass with owner eye.** Wing span/rise vs dress silhouette, ring
  radii/tilts/speeds final, glob density/scale/size-var final. Bank + full
  evidence renders (SOLID OpenGL, never EEVEE Rendered viewport).
- **Gate:** owner eyeball + `bevel_audit.json` + `staging.json` in
  `Saved/Audit/melusina_vfx_20260921/`.

## WAVE F — FLIP fluids finalize (runs parallel with H after G)

- **F1 Smoke bake (10 frames, res 24).** Headless:
  `blender -b Melodina_FLIP_bake_gen1.blend --factory-startup -P flip_smoke_bake.py`;
  script enables only `flip_fluids_addon`, uses `flip_fluid_add` on
  `FF_MelusinaHair_Domain` (domain), `FF_MelusinaHair_Drip` (flow/inflow),
  hair strands (obstacle/effector); domain res 24, frames 1–10, cache
  `KitbashExport/flip_cache_melusina_waterhair_smoke/` (recreate dir); bake via
  `bake_fluid_simulation_cmd`. Verify: `.bobj.gz` files on disk, fresh mtimes,
  frame count — "success: true" alone is nothing.
- **F2 Emitter rigging.** FF_Drip must ride the hair: parent to tip bones or
  mesh-sequence from evaluated strand tips. Verify per-frame world positions of
  emitter vs strand tips (JSON deltas < tolerance) before any long bake.
- **F3 Full bake.** Res 72, frames 1–240, cache `KitbashExport/flip_cache_melusina_waterhair/`,
  background + notify, overnight. G: has ~90 GB free; check again before launch.
- **F4 Mesh import + material.** FLIP mesh sequence into `FLIPMeshes` collection,
  material from the `Water (Advance).002` family (one water writer), foam accents
  from house GN foam; procedural globs stay as the always-on accent layer —
  FLIP is the hero liquid burst, not a second ambient system.
- **F5 Evidence + optional UE handoff.** PNG+JSON per milestone; alembic path
  documented for `Cinematics/MelusinaWaterHair` precedent (owner-gated).

## WAVE H — hython + Copernicus animated materials (runs parallel with F after G)

Assets: angel wings, clockwork rings ×3, water globs (elixir glass optional).

- **H1 One hython generator:** `Tools/Houdini/copernicus/animated_materials_20260922.py`
  (numpy lane — no Apprentice cap, editor-open safe). Perfect-loop flipbooks:
  - Wings: cymatic feather shimmer — chladni nodes drifting (freqs 10–90,
    smoothstep(0.82,0.97) veins per loom recipe), 48-frame loop @1024²,
    sequences: BaseColor, Iridescence, Emissive.
  - Rings: TwinklingGears palette brass iridescence sweep, UV angle offset per
    ring index (outer/mid/inner counter-phase), 3 × 48 frames @512².
  - Globs: PearlWeave/SingingSilk-derived flowing nacre (Normal + Emissive),
    32 frames @512².
- **H2 Naming + location:** `<asset>_<map>_<frame:04d>.png` under
  `Content/EnvSandbox/Textures/MelusinaAnimated/20260922/` (Saved/Audit PNGs are
  pre-commit-blocked; contact sheets go to `_ContactSheets/` with `git add -f`).
- **H3 Blender wiring.** Image-sequence texture nodes on the existing materials
  (water family for globs; new brass + shard materials for rings/wings), frame
  rate matched to the Scene Time drive; loop = seamless (period check in the
  generator, asserted, not eyeballed).
- **H4 COPs garnish (optional, owner-gated).** Dress-bake chain (AO/curvature
  from the real wing mesh) — respect every H22 truth: File-COP dead headless,
  custom attribs FLOAT-only, ROP res via setres, delete stale PNGs before
  proving a fresh cook, 1080 Apprentice cap.
- **H5 Evidence.** Per sequence: frame count + sha1 of first/last + file-size
  sanity; one contact sheet; one material-preview render (Workbench, SOLID-safe)
  showing an animated material on its asset.

## Standing rules (unchanged, binding)

- Never headless the live GUI file; bakes run on copies; `--factory-startup`
  defeats zombie addons (LiquiFeel GUI-only).
- One writer per surface: FLIP = hero liquid; Goo bake = jiggle; GN globs = accent;
  `Water (Advance).002` family = the water material writer in Blender.
- GN dial state lives on node inputs AND modifier `properties.inputs` (5.x) —
  never rebuild a wrapper tree; always `update_tag()` after dial writes.
- Bank + verify on disk at every wave boundary.
- No emails/messages anywhere; owner eyes ground truth.

## Next GOs

1. GO for Wave G execution (bevel audit first — read-only).
2. GO for F1 smoke bake once G closes.
3. GO for H1 generator authoring once G closes.
4. Chladni re-render for the harp (house cymatic solver) — separate lane, owner-gated.
