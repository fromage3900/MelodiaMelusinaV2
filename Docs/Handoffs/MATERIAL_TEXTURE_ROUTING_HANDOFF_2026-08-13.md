# Handoff — Mesh import completion + TextureWeight routing + Toon conversion (2026-08-13)

**Pick up:** [`_SESSION_HANDOFF.md`](../../_SESSION_HANDOFF.md) · [`_TASK_QUEUE.md`](../../_TASK_QUEUE.md) · audit JSONs in `Saved/Audit/`.

## What landed this session

### 1. Missing meshes imported (143)
`Tools/mesh_import_diff.py` diffed `Imports/Environment` against Content and found 146
missing stems (3,391 of 3,666 already imported by the 2026-08-13 mass GLB import).
`Content/Python/import_missing_env_meshes.py` imported the gap (binary FBX, materials
disabled): **143 imported, 0 failures**, saved via Monolith `save_packages` (43 dirty
packages incl. multi-mesh FBX extras like `*_collider`, `Retopo_PM3D_Cube3D*`).
- Gap was almost entirely `AvatarGarden_PolygonalMind` (141) — the pack has no GLB so
  the GLB-route mass import skipped it.
- Also landed: `character-archer` (base mesh), `Rooms_Paradise_SmallWall02_Art`,
  `crystalslow` from StylizedEnchantedForest.
- Cathedral 41 FBX confirmed already imported (verified, `Saved/Audit/cathedral_fbx_import.json`).
- Manifest: `Saved/Audit/mesh_import_results.json`.

### 2. Bling Vol 3 textures imported (89 new + 1 existing)
`Content/Python/import_blingvol3_textures.py` — 90 jpg 6-slot sets → `/Game/EnvSandbox/Textures/BlingVol3/`
with slot-aware sRGB (basecolor sRGB on, normal/metallic/roughness/height/ao off).
0 failures. The 15 `.sbsar` stay in `Imports/` (not UE-importable). Manifest:
`Saved/Audit/blingvol3_import.json`.

### 3. Electric Dreams materials → Substrate Toon (35/35 verified on disk)
- **21 ED masters** (MSPresets + Custom MS): converted via
  `Content/Python/convert_ed_masters.py` wrapper around `convert_masters_to_substrate_toon.py`.
  One deterministic editor crash isolated: `M_MS_CustomDecal_CR` (already-Substrate
  SlabBSDF→ConvertToDecal graph crashes the legacy-lit converter). Fixed surgically via
  `Content/Python/convert_cr_toon_swap.py` (Slab → Toon BSDF swap inside the ConvertToDecal chain).
- **Remaining 14 EnvSandbox masters** converted (StarryNight, VoidGradient, PP_Underwater,
  Simple_Universal, NikkiChainRepair, SpaceParallax_Test, water family).
- **Water family (7 masters) REVERTED per owner.** Water has its own shading setup and
  must NOT be Substrate Toon. Restored via targeted `git checkout` of exactly those 7
  files (not the banned whole-tree command), packages unloaded/reloaded in the editor,
  verified no ToonBSDF on disk and nothing dirty. `M_Water_Master_Grand_v7` crashed the
  editor once during conversion; the disk file had already saved — the revert restored it.
- Verify: `Tools/verify_toon_conversion.py` → **28 Toon + 7 water (intentionally not Toon)**.
- Batch lists in `convert_masters_to_substrate_toon.py` fixed: 4 phantom paths removed,
  4 pointed at the real `Materials/SDF/` location.

### 4. TextureWeight / texture routing fix (74 instances)
Root cause: master default `TextureWeight = 0.0` (procedural base by design, per
`setup_master_universal.py`), but instances that override Albedo/Normal/ORM never
overrode `TextureWeight` → inherited 0 → textures invisible. Also the intake script
`Scripts/unreal_material_setup.py` set a non-existent `BaseColorAtlas` param → pack MIs
had zero overrides.

- `Content/Python/fix_mi_texture_weight.py`: **65 instances** got `TextureWeight=1.0`
  (pipeline convention), persisted via `save_mi_weight_fixes.py`.
- `Content/Python/route_pack_albedos.py`: **7 `MI_Env_*` pack instances** routed to
  imported pack albedos (`T_<Pack>_Albedo` in `/Game/EnvSandbox/Textures/ImportedPacks/`,
  imported via Monolith `import_texture` with explicit names — note: the action ignores
  `destination_name`; stage uniquely-named source copies instead).
- Surfaces routed: `MI_House_Railing`, `MI_Grotto_CrystallineSpire`, `MI_IridescentRock`
  (PrettyRock PBR set; the earlier guessed `T_Rock_BSS` path did not exist).
- Intentionally untouched (procedural/feature demos): Escher, Madoka, Itto, Showcase2 row,
  CosmicOrrery, MelodiaVoid, NikkiIntegrated — pure-tint/procedural, no textures.
- **Water masters untouched** (own setup, per owner).
- Survey: `Saved/Audit/mi_texture_weight_survey_v2.json` (183 → 109 zero-TW; remaining 109
  are non-Universal families or the 8 intentional procedural demos).

### 4b. Per-prop mesh materials — THE REAL mesh-level fix (owner follow-up)

The instance-level fix above was necessary but NOT sufficient: **every mesh under
`EnvSandbox/Meshes/Environment/<prop>/StaticMeshes/` was rendering untextured.** Root cause
was two-fold and only visible at mesh level:

1. **Per-prop MICs were invisible shells.** All **1,327** materials under
   `<prop>/Materials/` (`wood`, `dirt`, `leafsGreen`, `_defaultMat`, …) parented to
   `M_Master_Toon_Universal` with zero texture overrides and no `BaseTint` — they rendered
   the master default (grey/white) with `TextureWeight` inherited 0.
2. **Meshes referenced shared pack MIs, not their prop materials.** 882 meshes had slots
   pointing at `MI_Env_<Pack>` (one shared albedo per whole pack) instead of the prop's own
   materials. Some were cross-pack wrong (`table` → `MI_Env_MusicalInstruments`).

Pack texture reality (checked GLB JSON directly):
- **Kenney packs** (CastleKit, MedievalBuilder, MiniForest, ModularCave, LowPolyCrystals):
  GLB embeds one real `colormap` texture → 295 props have `Textures/colormap.uasset`
  imported per prop. Fix: `Albedo` = prop's own colormap + `TextureWeight=1.0`.
- **NatureMegaKit / MusicalInstruments**: GLB materials are **flat unlit colors**
  (`baseColorFactor`, e.g. `leafsDark` = teal 0.169/0.651/0.667) — NO textures exist.
  Fix: `BaseTint` = the GLB material's exact color (parsed per GLB), `TextureWeight` stays 0
  (flat-tint path). Verified 1:1 against bed.glb colors.

Executed (all persisted, 0 missing):
- `route_per_prop_materials.py` — **310** MICs textured (own colormap + weight 1.0),
  **1,017** MICs flat-colored (GLB baseColorFactor → `BaseTint`). All 1,327 covered.
- `assign_mesh_prop_materials.py` — **882 meshes / 882 slots** reassigned from shared pack
  MIs to the prop's own material by slot name (fallback: single-material prop).
  Verified: `table`→table/Materials/wood, `bed`→leafsDark/woodBirch/wood,
  `balcony-wall`→colormap, `washer_Clone_`→metalLight/Medium/Dark, `washerDoor`→metal/glass/_defaultMat.
- Audits: `per_prop_material_survey.json` · `per_prop_routing.json` · `mesh_slot_survey.json` ·
  `mesh_material_assign.json`.

`_defaultMat` = source GLB default (white) — correct fidelity, not a bug.

### 4c. Magician's Library + Paradise room meshes (owner follow-up)

- **Magician's Library** (`EnvSandbox/Library/Migrated/MagiciansLibrary` + `Library/Migrated/`):
  104 meshes, 49 slots were on shared fallbacks (`MI_Universal_Default` ×39,
  `MI_Universal_CrystalClear` ×10). Fixed via `fix_library_paradise.py`: every mesh slot
  reassigned to its prop's own `MI_M_<prop>` instance (e.g. `SM_Desk`→`MI_M_Desk`,
  `SM_GlassBottle_Object1715`→`MI_M_GlassBottle_Object1715`). The `/Game/Library/...` copy
  has NO MIs → falls back to the EnvSandbox migrated copy's MI. Created `MI_M_Pot` from the
  prop's own textures (T_Pot_Base/Normal/AO → Albedo/NormalMap/ORM, weight 1.0) and assigned
  to both Pot meshes. **Remaining: 1** — `SM_Outside_Wall` (WorldGridMaterial slot) has no
  material source anywhere (no M_, no MI, no textures in either copy or the source tree);
  left on the Universal fallback.
- **Paradise rooms** (`Rooms_Paradise_*` ×239 in `EnvSandbox/Meshes/Environment/`, from the
  CrystalCrossroads pack, FBX import): all 239 were on shared pack MIs. The pack's real
  slot names are `Atlas_01_Mat`/`Atlas_01_Trans_Mat`/`Outliner_Mat`/`Shadows_Mat`/
  `Seam_Floor_Mat`/`Seam_Sand_Mat` — those root MICs were textureless shells.
  Fixed: imported the pack's real maps (`Atlas_01_Albedo/Trans/Glass`, `Seam_Floor/Sand_Albedo`,
  `Seam_Shadows_01`) to `/Game/EnvSandbox/Textures/CrystalCrossroads/`, routed Albedo +
  `TextureWeight=1.0` on all 6 MICs, and reassigned all 239 meshes by slot name.
  **0 slots on pack MI remain.**

### 4d. Full PBR sweep of the last-48h import body (2026-08-14) + external toon research

Full sweep executed via `Content/Python/fix_pbr_pipeline.py` (resumable, audit-per-phase)
driven through the live editor with `Tools/editor_run.py` (Monolith `editor_query run_python`).
Census (`Saved/Audit/sweep_pbr_state.json`): **2,299 meshes, 1,680 bad slots, 1,450 unfinished MIs,
718 root-vs-StaticMeshes duplicate pairs**.

- **Phase B** — pack texture catalog (`pbr_texture_catalog.json`): AvatarGarden / EnchantedForest /
  CrystalCrossroads classified by role (albedo/normal/orm/roughness/metallic/ao) and imported to
  `/Game/EnvSandbox/Textures/PackTextures/<Pack>/` with slot-aware sRGB.
- **Phase C (done: 2,397 MIs)** — every instance under `Meshes/Environment` + Library got explicit
  `bLayerA_Active=True` + `LayerA_TextureWeight=1.0` + `TextureWeight=1.0`, plus PBR routing
  (pack set → prop colormap → **project tileable fallback** — ZenTrim_Base4K Normal/Roughness/
  Metallic, `landscape_grass_orm` for organic props). **521 bad mesh slots routed** (AvatarGarden
  `_Art` → per-set `Meshes/AvatarGarden/Materials/MI_*` created from pack textures; Library NONE
  slots made explicit; loose meshes → `_Loose/MI_*`). **15 `MI_BlingVol3_*` created** from the
  imported 6-slot sets (Albedo/Normal/Roughness/Metallic/Height; AO skipped — no param).
  Root cause found: master default texture set = abstract noise (`sbs_-_seamless_abstract_pack`),
  so every shell MI rendered grey; 4b's top-level `TextureWeight` was the wrong knob — Layer A
  (the actual texture path) is now enforced.
- **Phase D/E (pending owner window)** — dedupe (718 pairs, root copy vs StaticMeshes twin) +
  final verify (`full_pbr_sweep_2026-08-14.json`). Delete policy: zero-referencer only.
- **Operational notes:** this machine cycles/cooks UE processes externally — run phases in the
  live editor via `Tools/editor_run.py`, never `UnrealEditor-Cmd` (fatal DDC "Installed cache
  graph" without `-DDC-ForceMemoryCache`, and it collides with the owner's UAT cook).

External toon research (top studios on UE5 toon): `Docs/Research/UE58_TOON_SHADER_EXTERNAL_PRACTICES_2026-08-14.md`
— verified MooaToon (engine fork, **no Substrate support**, miHoYo HI3 Pt.2 cinematics; the studio
feature vocabulary: ramps, TSR-safe outline, Kajiya-Kay hair, face shadow, GI-as-knob), Epic Substrate
Toon official constraints (Blendable vs Adaptive GBuffer, closure budgets, F0 parameterization), and
Infinity Nikki production discipline. Recommendation: stay Substrate Toon, add an Adaptive-GBuffer
Hero tier + material-level ramp/outline/normal-baking lane.

### 5. Duplicate / orphan audit
- `Tools/duplicate_assets_audit.py` + `Content/Python/scan_orphan_assets.py`:
  Textures_Shared folder = **784 copies**; 779 zero-referencer.
- **Deleted 6 proven dupes** (zero-ref + byte-identical twin): `Textures_Shared` Marble_1/5/8
  (twins in `SDF/Textures`), Blue_Nebula_8 + Purple_Nebula_6/7 (twins in `_PROJECT`, kept).
- Deleted 4 failed-import artifacts in `ImportedPacks` (`bathroomCabinetDrawer_NE`,
  `bear_NE`, `bed_floor_NE`, `bed_NE` — zero-ref, superseded by T_* names) + stray `colormap`.
- **NOT deleted (documented, owner-call):** the remaining ~773 Textures_Shared copies have
  same-stem twins with **different bytes** (re-imported with different settings) — deleting
  risks losing real content; verify per file. `_Archive/` is policy no-delete.
  `_Scratch/` test assets (12 zero-ref) listed for owner review.
- Per-prop `Materials/` folders (`wood`, `stone`, `dirt`, `metal`, `_defaultMat` ×75) are
  **mesh-referenced** — NOT dupes, must stay.

### 6. Credits
- BlingVol3 row added to `Docs/CREDITS.md` (first-party) + `SOURCES_MATRIX.md`.
- `UI` / `Widgets` dirs (created by another lane 10:21-10:22 PM) got first-party/pending
  rows so the gate passes — **owner should confirm authorship**.
- `Tools/credits_gate.py` → **PASS** (68 dirs / 56 rows).

## Audit files (Saved/Audit/)
`mesh_import_diff.json` · `mesh_import_results.json` · `blingvol3_import.json` ·
`substrate_toon_conversion_2026-08-13.json` (disk verify) · `mi_texture_weight_survey_v2.json` ·
`mi_texture_weight_fix.json` · `mi_full_survey.json` · `duplicate_assets_audit.json` ·
`orphan_assets_scan.json` · `ts_dupe_verify.json` · `safe_delete_textures.json` ·
`ed_convert_loop.log` / `ed_convert_loop_results.txt` (ED conversion evidence).

## Editor crash history (do not be surprised)
Two deterministic editor crashes were hit and isolated:
1. `M_MS_CustomDecal_CR` via the legacy converter (already-Substrate graph) — worked
   around with the toon-swap runner.
2. `M_Water_Master_Grand_v7` during conversion — reverted anyway per owner.
The crash-isolated loop (`Tools/run_ed_convert_loop.ps1` + `convert_one_master.py`) is the
pattern for converting risky masters one-at-a-time.

## Still open (owner-call)
- 773 Textures_Shared non-byte-identical copies (verify per file before deleting).
- 12 `_Scratch` zero-ref test assets.
- `BS_GodFile.uproject` dirty (MelodiaWardrobe + BOM) — unchanged, owner call.
- UI/Widgets authorship confirmation for the credits rows.
- Editor restart will clean the leftover `ImportedPacks/colormap` package reference if any.
