# Material System Rebuild Guide (2026-08-14)

This is the exact ordered procedure to reconstruct the material surface from
scratch, including the new Nikki feature expansion and the rhythm family.
Every step is script-driven and idempotent (safe to re-run).

## Prerequisites

- One Unreal editor (`Get-Process UnrealEditor` → exactly one), Monolith on :9316.
- Scripts live in `Content/Python/`; run via Monolith `run_python` with
  `import importlib, <mod> as m; importlib.reload(m); m.main()` (module cache trap).
- Never `git clean` / `checkout -- .`; never `delete_asset` without zero-ref proof.

## Phase A — Masters

```python
# 1. Universal master (the big generalist)
import setup_master_universal            # rebuilds M_Master_Toon_Universal
import organize_master_groups            # numbered parameter groups

# 2. Landscape + water
import setup_landscape_height_blend      # M_Master_Toon_Landscape_HeightBlend
import setup_master_water                # M_Water_Master_Grand_v6 (or v7/v9/v10 builders)

# 3. Nikki family (original surgery + 2026-08-14 feature expansion)
import expand_nikki_masters              # M_Master_Nikki / _Landscape (sticker/twinkle/pastel/ShadowDream)
import expand_nikki_features             # 7 NEW feature gates (SDF Ribbon, Pearl, Watercolor,
                                         #   Sticker Edge, Glitter Halo, Petal Shadow, Squish WPO)
                                         #   rebuild_functions=False after first run
```

After Nikki: verify `material_query get_compilation_stats` on both Nikki masters
(`is_compiled: true`, no cycle errors).

## Phase B — Functions

```python
import setup_material_functions          # 16 canonical MFs
# Nikki-specific MFs are built by expand_nikki_masters / expand_nikki_features.
```

## Phase C — Instances

```python
# 4. Policy sweep (Nikki-quality variance across all Universal instances)
import apply_instance_parameter_policy   # reads specs/instance_parameter_policy.json

# 5. Pink/blue dream ramp (master defaults + instance override pass)
import apply_pinkblue_dream              # ShadowDreamStrength 0.3 + pink/lavender/sky ramps

# 6. Flat-color family + material-type tuning
import consolidate_flat_materials        # 37 shared MI_Flat_* (1,017 dupes -> shared)
import tune_flat_materials               # roughness/metallic per material type

# 7. Mesh routing passes (order matters)
import route_art_mesh_textures           # 279 AvatarGarden _Art meshes -> pack atlases
import route_retro_materials             # 105 retro meshes (first pass)
import reroute_retro_materials           # GLB ground-truth material->texture map
import route_cathedral_materials         # 41 Cathedral -> GothicCastle stone PBR
import fix_loose_mesh_materials          # flat-root meshes -> shared/colormap MIs
import fix_loose_mesh_materials2         # Library SM_* + colliders/helpers
import fix_loose_mesh_materials3         # Room* CrystalCrossroads + AG Palette/Foam
import fix_loose_mesh_materials4         # final Room* + AG flat tints
import fix_loose_mesh_materials5         # last mirror/outside-wall cases
import fix_library_mirror_materials      # /Game/Library mirror -> EnvSandbox MIs
import route_library_mi_textures         # (probe) Library MI_M_* texture names
import reparent_library_mis              # Library MI_M_* -> Universal + route T_*_Base/AO/Normal
import route_kit_fallback_materials      # Ornament/GoldTrim, Celestial/Space, WP terrains

# 8. Neutral-map sweep (kill inherited noise defaults on textured MIs)
import route_neutral_maps                # 1,255 MIs -> real-or-neutral Normal/ORM/Height/Rough/Metallic

# 9. Rhythm battle-surface family (new 2026-08-14)
import create_rhythm_materials           # 5 MI_Rhythm_* (pulse + audio-reactive)

# 10. Nikki feature showcase instances
import create_nikki_feature_shows        # 7 MI_Nikki_Show_* (one feature ON each)
```

## Phase D — Deletion (only with zero-referencer proof + owner sign-off)

```python
import delete_dead_mis                   # 558 dead _Loose/AvatarGarden MIs (manifest kept)
```

## Phase E — Verification (always after any pass)

```python
import audit_mi_runtime                  # expect 441+/439/0 no_parent
import audit_layer_a_state               # expect textured_bad only authored-lookdev
import survey_mesh_slots                 # 882 meshes / slot truth
# editor-side: material_query get_compilation_stats on every touched master
```

## Folder reorg (2026-08-14, redirector-safe)

```python
import reorg_material_folders            # SDF masters -> Masters/SDF/; landscape quarantine -> _Scratch/
```

Uses `EditorAssetLibrary.rename_loaded_asset` after clearing the LFS read-only bit
(chmod before load; disk iteration beats `list_assets` for rename loops).

## Key traps (learned 2026-08-14)

1. **Graph cycles**: when splicing a feature chain, read the pre-stage color from
   the PASTEL switch output, never from the ShadowDream switch output (cycle).
2. **MF-call → material property crashes the editor.** Route the MF output through a
   StaticSwitchParameter, then connect the SWITCH to MP_WORLD_POSITION_OFFSET.
3. **Tag discipline**: the original Nikki surgery tags `NikkiX:`; feature script tags
   `NikkiFeat:`. Cleanup must only remove its own tag or it deletes the core chain.
4. **LFS read-only**: rename_asset fails "Not checked-out or writable" until the
   disk file is chmod'd AND the package re-loaded.
5. **Module cache**: always `importlib.reload` after editing Content/Python scripts.
