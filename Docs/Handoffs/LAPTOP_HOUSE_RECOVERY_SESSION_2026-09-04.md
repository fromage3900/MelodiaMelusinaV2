# Melodia Studio / Melusina House — Session Notes (2026-09-04)

For picking up tomorrow on the main PC. Everything below is committed.

## Where things stand

**Addon (all three copies identical: P: SSOT, C: working, AppData live):**
- 268 builders registered, whole-dir diff = 0 diverged.
- House lineage converged: `melodia_house.py` = mh6 genome room shell + AAA kit
  (cornice/dentil/scallop/lissajous). `house_dress.py` = mh_* dressing builders,
  NOW explicitly imported in `__init__.py` (was a fragile transitive import).
- `melusina_house_v6.py` and `house_aaa.py` are deleted (folded into melodia_house.py).
- All builder IDs unchanged — stage scripts and the base blend are unaffected.

**Fixes landed today (all verified headless):**
1. Tower-wipe fix (v2.132): auto_update no longer deletes user-edited GN trees.
   `apply_geometry_nodes_to_object(force=False)` preserves; manual Generate = force.
2. `integration.py` wrapper forwards `**kwargs` — fixes "unexpected keyword argument
   'force'" in Generate. **This broke the live addon earlier today; restart Blender
   to pick it up.**
3. Universal music influence actually applies now:
   - `core._auto_apply_music_pass`: 5.2 NodeSocket has `.is_output`, not `.direction`
     (guard crashed silently on every group-nested builder before).
   - `melodia_city_gen.py`: all builders return `(tree, gin, gout)` so the wrapper
     auto-applies. Verified: influence=1 warps cell verts, 0 = passthrough.
   - NOTE: modifier inputs PIN interface defaults at attach time — set defaults
     BEFORE attaching a modifier when testing.
4. Bend fix in `melodia_house.py` (was melusina_house_v6): SetPosition used Position
   (replace mode, collapsed walls to sheets) — now Offset. mh6 walls hold full Depth.
5. Three-way merge restored P:-unique builders (`MEL_allee_ribbon` + presets,
   `MEL_harp_string_unit`) and adopted AppData's city_gen category.

**Known bugs NOT fixed (deliberately deferred):**
- mh6 empty-cutter collapse: Opening Columns=0 + Rows=0 collapses the wall to a plane
  (empty SDF grid subtracted destroys the field). A guard was attempted and REVERTED
  as unverified. Fix approach: Switch bypassing the boolean when no cutters; needs
  real testing. Do NOT set both openings to 0 in the meantime.
- 16 dead builders (mother_v3 x8, mother_tapestry_wall, 7 p4_*) never imported.
- 8 passthrough stubs (same files) with broken internal signatures.
- v2.132 auto-update user-edit detection uses node selection, which does not survive
  save/reload reliably.

## Melusina House base

- `C:/Users/brenn/melodiamelusinav2/Saved/MelusinasHouse/MelusinasHouse_V7_Base.blend`
- Build script: `C:/Users/brenn/melodiamelusinav2/Tools/house_v7_base_build.py`
  (reproducible headless: `blender --background --python <script>`)
- 85,520 verts. U-massing (3 cells, Show Roof=False), 3 SurrealRoof_HIP roofs,
  organ, piano walk, sheet rail, lanterns, trees, allee ribbon, cornice, pearls.
- Palette: M_MH_PearlPlaster_Pink / M_MH_Roof_IridescentBlue / M_MH_GoldBrass.
- Hero render: `Saved/Audit/melusinashouse/v7_base_hero.png`.

## The 3rd GN section — what convergence remains

House architecture layers are now: melodia_house (shells+trim) / house_dress
(dressing) / melodia_city_gen (city cells) / polyhedra_gn greybox kit. IDs stable.
Remaining convergence work (V0 of melusinahouse_v7_plan.md):
- Rewire `MEL_city_house_cell` to nest `MEL_mh6_room_shell` instead of
  `MEL_greybox_room_kit` for its exterior shell (params: W/D/H -> Width/Height,
  Depth = wall thickness). Proof-first: side-by-side bbox comparison.
- Or adopt the plan's curve-based grammar (GN_MH_02_CurvedWallShell) — owner call.
- Full plan: `C:/Users/brenn/melodiamelusinav2/melusinahouse_v7_plan.md` (V0-V5),
  authority map: `P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/Docs/ADDON_AUTHORITY_2026-09-03.md`.

## Lost asset — owner action needed

`Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend` lived on `G:\EnvironmentPortfolio\`
which is NOT mounted (drives: C, D, P only; D has no portfolio). Not on P: or C:.
If G: is a removable drive, replug it. Docs still reference that path.

## House versions on disk (this commit)

All `.blend` files in `C:/Users/brenn/melodiamelusinav2/Saved/MelusinasHouse/` are
committed (see .gitattributes/gitignore changes): v3 master through v6 lego, lookdev,
staged, garden, shell, round interiors, scallop variants, and MelusinasHouse_Base +
MelusinasHouse_V7_Base.

## Git state

- C: repo (melodiamelusinav2.git, main): all work committed through today.
- P: repo (MelodiaMelusinaV2.git, branch docs/2026-09-02-grand-master-plan):
  reconciled with origin/main today (merge e5a95132, no conflicts). My addon commits
  live on this branch, NOT main — tomorrow: push or merge to main as you prefer.
  Neither repo has been pushed.
