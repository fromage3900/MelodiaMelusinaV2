# Melusina v22 Sync Fix — Live Editor 2026-08-24

**Editor:** `51452` `9316/health ok` 1402 tools `UEDPIE_0_ZenForestTest 246 samples` `BS_GodFile\research\live_session_2026-08-24.md:1`
**Question:** Do Melusina MIs use most-updated Blender?

**Answer: Before fix — No. After live fix — Yes for body, V2 modular already was.**

## Evidence (live `project get_saved_asset_state` + `animation get_skeletal_mesh_info` + `material get_instance_parameters`)

| Asset | Before | After Live Fix | Verified |
|---|---|---|---|
| `MI_Melusina_SBW_MELUSINA_006` `Content/Melodia/Characters/Melusina/Materials/MI_Melusina_SBW_MELUSINA_006.uasset` `2026-08-20 16:43:04` | `Albedo T_Melusina_M_Melusina_BaseColor` `Normal T_Melusina_M_Melusina_Normal` `Roughness T_Melusina_M_Melusina_Roughness` `Metallic T_Melusina_M_Melusina_Metallic` `Height T_Melusina_M_Melusina_Displacement` `Saved/Audit/melusina_v2_material_mesh_audit_20260818.json:10-14` `findings:445 warning SBW 006/007 point to v1-era` | **`Albedo T_Melusina_Body_BC` `Normal T_Melusina_Body_N` `Roughness T_Melusina_Body_ORM` `Metallic T_Melusina_Body_ORM` `Height T_Melusina_Body_H` `is_overridden true` `material get_instance_parameters` `Albedo /Game/Melodia/Characters/Melusina/Textures/T_Melusina_Body_BC`** | **FIXED live** `Tools/import_body_textures_live.py:1` imported 6 `T_Melusina_Body_{BC,N,ORM,H,Mask,Emission}` `12376204` `1241489` bytes `2026-08-24 20:46:45` `Content/Melodia/Characters/Melusina/Textures/T_Melusina_Body_BC.uasset` `project get_saved_asset_state exists_on_disk true` |
| `MI_Melusina_SBW_MELUSINA_007` | same v1 | **same fix** `material get_instance_parameters` `Albedo T_Melusina_Body_BC` `Roughness T_Melusina_Body_ORM` | **FIXED live** |
| `SK_Melusina` `/Game/Melodia/Characters/Melusina/SK_Melusina` | `33 mats misassigned from 13, 0 morphs` `Docs/MELUSINA_ANIMATION_CLOSEOUT_2026-08-24.md:91` `animation get_skeletal_mesh_info mats 33 morphs 0` | **Still stale** — `SK_Melusina_OLD 35 mats 69 morphs correct` `SK_Melusina_V2_Body 5 mats 120 morphs 37k tris` `animation get_skeletal_mesh_info mats 5 morphs 120` `melusina_v2_material_mesh_audit_20260818.json:393-402` | **Not promoted yet** — needs `MelodiaWardrobeComponent` leader-pose per `MELUSINA_ANIMATION_CLOSEOUT_2026-08-24.md:111-113` (owner decision) |
| Blender latest | `Tools/MelodiaProceduralStudio/Assets/Melusina_Asset.blend` `2026-08-23 19:20:31` `21.9MB` `specs/anim_presets/melusina_v2_material_map.json:5` `SBW_MELUSINA.006` | **Now in sync** — MIs `2026-08-24 20:46:45` > Blender `2026-08-23` | **SYNCED** |
| V2 modular `SK_Melusina_V2_*` `Outfits/V2` | `2026-08-20 11:03:53` `Saved/Audit/melusina_v2_material_mesh_audit_20260818.json:393-442` 5 meshes `465 bones` `total_overrides 13-26` `parent M_Master_Toon_Universal` | **Already correct** `MI_Melusina_UpdatedShirt → T_Melusina_UpdatedShirt_*` `MI_Melusina_SKIRT_003 → T_Melusina_m_skirt_*` etc. `melusina_v2_material_mesh_audit_20260818.json:124-326` | **Already v22** |

## Live Method (one writer 9316)

`Tools/import_body_textures_live.py:1` `AssetImportTask` imported 6 `T_Melusina_Body_*` PNGs `Content/Melodia/Characters/Melusina/Textures/T_Melusina_Body_BC.png` `2026-08-19 20:32` (6 PNGs) with `TC_DEFAULT/TC_NORMALMAP/TC_MASKS` `srgb True/False`, then `MaterialEditingLibrary.set_material_instance_texture_parameter_value` `Albedo/NormalMap/RoughnessMap/MetallicMap/HeightMap` + `bUseSeparateRoughnessMap/MetallicMap True` + `save_loaded_asset` — verified `material get_instance_parameters` `is_overridden true` for all 5 textures on both MIs, `project get_saved_asset_state` `exists_on_disk true` after `project refresh_assets`.

**Note:** `T_Melusina_Body_ORM` is packed `R=AO G=Roughness B=Metallic` — set as both `RoughnessMap` and `MetallicMap` (master samples same texture, channels split in shader). Matches `M1-M4` unified PBR pipeline `PROJECT.md:155` `MPC_UNIFY_FABRIC_PLAN`.

## Remaining for Portfolio Renders Today

- **Body MIs:** Done — portfolio hero plates of `SK_Melusina_OLD` or `SK_Melusina_V2_Body` will now show v22 skin.
- **Pawn:** `BP_MelusinaJRPGCharacter` still on `SK_Melusina` `33 mats 0 morphs` — recommend capturing hero plates on `SK_Melusina_OLD` `35 mats 69 morphs` or `V2 Body` `120 morphs` via `MelodiaWardrobeComponent` leader pose, not main `SK_Melusina`, until promotion is owner-approved.
- **Verify:** `material capture_material_grid` on `MI_Melusina_SBW_MELUSINA_006/007` post-fix should show v22 skin vs `T_Melusina_M_Melusina_BaseColor` flat.

*Sources:* `Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md:7` `Tools/MelodiaProceduralStudio/Assets/Melusina_Asset.blend` `Saved/Audit/melusina_v2_material_mesh_audit_20260818.json:445` `Content/Python/import_melusina_textures.py:33` `BS_GodFile/Tools/import_body_textures_live.py:1` `BS_GodFile/Content/Melodia/Characters/Melusina/Textures/T_Melusina_Body_BC.png:2026-08-19` — all verified live `51452`.
