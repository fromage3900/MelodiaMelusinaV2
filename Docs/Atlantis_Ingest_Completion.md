# Atlantis Ingest Pipeline — Completion Report

**Date**: 2026-08-16 (staging/meshes) + 2026-08-17 (materials/verify)
**Pack**: atlantis (KitBash3D)
**Goal**: Import 333 Atlantis mesh uassets + author MaterialInstanceConstants from toon crosswalk

## What Was Done (2026-08-16)

### 1. Staging Path Fix
- **File**: `ingest_aaa_underwater_packs.py:59`
- **Change**: Staging path updated from `Source/` to `Split/`
- **Impact**: Script now reads FBX files from `Imports/KitBash3D_Atlantis/Split/` (79 FBX files, split per-node)

### 2. Mesh Import — 333 uassets saved
- **Status**: Successfully imported despite UE 5.8 FBX SDK `SlowTask` crash
- **Crash**: `Out-of-order slow task construction/destruction` (from `libfbxsdk.dll`) — occurs during FBX processing but assets land on disk; re-runs skip via `does_asset_exist()`
- **Count**: 333 static mesh uassets in `Content/EnvSandbox/Meshes/Atlantis/`
- **FBX files**: 79 groups, 2,767 objects, all matched naming convention

### 3. Crosswalk — 83 material → MI mappings (authoritative)
- **File**: `Imports/KitBash3D_Atlantis/atlantis_toon.material_map.json`
- **Entries**: 83 material names mapped to `/Game/EnvSandbox/Materials/Instances/Atlantis/MI_MaterialName`
- **Note**: earlier docs said 85; the manifest itself has 83 keys, each with a texture set on disk (83 basecolor sets). 83 is the real number.

---

## Materials Pipeline — DONE 2026-08-17

### 4. Textures — 424/424 imported
- **Script**: `Content/Python/import_atlantis_textures.py`
- **Dest**: `/Game/EnvSandbox/Textures/Atlantis/` (424 `.uasset` on disk)
- **sRGB policy** (BlingVol3 proven): basecolor/emissive = ON; normal/metallic/roughness/height/opacity/refraction = OFF
- **Edge case fixed**: `KB3D_ATL_WaterClean_refraction.inverted.png` — dotted stem is an invalid UE object name; the importer auto-sanitized it to `KB3D_ATL_WaterClean_refraction_inverted`. sRGB was then corrected to OFF via `fix_atlantis_refraction_srgb.py` (evidence: `Saved/Audit/atlantis_refraction_srgb_fix.json`).

### 5. Masked variant master — `M_Master_Toon_Universal_Alpha` CREATED
- **Script**: `Content/Python/wire_atlantis_opacity_master.py` (evidence: `Saved/Audit/atlantis_opacity_master_wire.json`)
- **Why**: `M_Master_Toon_Universal` is BLEND_OPAQUE with a SubstrateToonBSDF that has no opacity input — it cannot cut out. The variant duplicates it with `blend_mode = BLEND_MASKED`, `two_sided = true`, plus a gated opacity chain:
  - `bUseOpacityMap` (static switch, default **False** — zero change to existing instances)
  - `OpacityMap` (texture object param)
  - `OpacityStrength` (scalar, default 1.0)
  - Chain: `switch ? (OpacityMap * OpacityStrength) : Constant(1.0)` → **MP_OPACITY_MASK** (same route `M_ToonFoliage` uses — the masked-toon precedent confirmed by probe)
- Compiled clean, saved. Idempotent on re-run.

### 6. MaterialInstanceConstants — 83/83 authored + verified
- **Script**: `Content/Python/author_atlantis_mis.py` (evidence: `Saved/Audit/atlantis_mi_author.json` — `all_ok: true`)
- **Parents**: 70 → `M_Master_Toon_Universal`; 12 opacity sets (AtlasDecalOrnamets, AtlasFlowersA, AtlasIvy, AtlasLeafA, AtlasLeafB, AtlasOrnaments, AtlasPaintPatternsA, AtlasTreeA, Burlap, Grass, HaleBale, PropsSpear) → `M_Master_Toon_Universal_Alpha`; WaterClean → `M_Water_Master_Grand_v10_Upgrade` (v10, NOT v6 — the user-corrected canonical water master)
- **Conventions** (proven 08-13/14/15): `bLayerA_Active=True`, `LayerA_TextureWeight=1.0`, `TextureWeight=1.0` on every toon MI
- **Opacity sets** additionally: `bUseOpacityMap=True`, `OpacityStrength=1.0`, `OpacityMap=<set>_opacity`
- **Channel map** (reflection-confirmed, expression-level — Substrate masters report empty parameter_value arrays): Albedo / NormalMap / MetallicMap / RoughnessMap / HeightMap / EmissiveMap / OpacityMap (variant only)
- **Water channel map**: BaseColorTexture / BaseNormalTexture / BaseRoughnessTexture / BaseHeightTexture; metallic + refraction channels intentionally skipped (dielectric water master)
- Verify-by-reread: every MI re-read after save; texture + scalar + switch (global association) overrides checked — 83/83 match

### 7. Mesh resolution — 333/333 meshes, 1213 slots, 0 unresolved
- **Script**: `Content/Python/resolve_atlantis_meshes.py` (evidence: `Saved/Audit/atlantis_mesh_resolve.json`)
- **Matching**: slot names carry the `KB3D_ATL_` prefix; strip prefix then exact-match against crosswalk keys (token fallback)
- Re-read slot count per mesh after apply — all verified

## Evidence Ledger

| Manifest | Path |
|---|---|
| Texture import | `Saved/Audit/atlantis_texture_import.json` |
| sRGB fix | `Saved/Audit/atlantis_refraction_srgb_fix.json` |
| Master probe 1 | `Saved/Audit/atlantis_material_surface_probe.json` |
| Master probe 2 | `Saved/Audit/atlantis_surface_probe2.json` |
| Opacity wire | `Saved/Audit/atlantis_opacity_master_wire.json` |
| MI authoring | `Saved/Audit/atlantis_mi_author.json` |
| Mesh resolve | `Saved/Audit/atlantis_mesh_resolve.json` |

## Next Steps (Open)

1. **Visual smoke**: drop an Atlantis mesh into a level and confirm toon render (opaque + masked sets) — needs owner/GUI session
2. **Niagara VFX instances** (if any exist for Atlantis) — uninvestigated
3. Full pipeline review, owner-call inventory, and PPV dreamprint status: see `Docs/Handoffs/ATLANTIS_MATERIALS_AND_MASTER_PIPELINE_2026-08-17.md`

---
*Documented for future agents handling bulk Atlantis/KitBash3D imports.*