# Offline audit — WorldGrid + Flipbook Lane D inventory — 2026-09-09

**Status:** OFFLINE (filesystem + docs; live editor re-verify still open)  
**Date:** 2026-09-09  
**Index:** [Docs/Materials/README.md](README.md) · [LABEL_MAP](LABEL_MAP_2026-09-09.md) · [Cleanup plan](../Plans/MATERIALS_WIRING_FLIPBOOK_CLEANUP_2026-09-09.md)

## Flipbook Lane D (filesystem)

| Family | png | uasset | Atlases present |
|--------|-----|--------|-----------------|
| CelestialSilk | 154 | 154 | Atlas_6x5 BaseColor / Iridescence / Roughness + AtlasCompact_6x5 BaseColor |
| CymaticPulse | 154 | 154 | same pattern |
| BrassPatina | 154 | 154 | same pattern |
| Brass shared | — | — | `T_Brass_Flipbook_30_Atlas_4x4` (png+uasset) — **16 cells; rename to `_16_`** |
| PearlWoven / SurrealBrick | prior PASS | frames on disk | see [FLIPBOOK_STATUS_2026-09-02.md](../FLIPBOOK_STATUS_2026-09-02.md) |

### Missing / duplicate
- `M_SurrealFabric_Flipbook` master: **MISSING**
- `MF_FlipbookScrub`: **spec only** (`specs/materials/MF_FlipbookScrub.v1.json`)
- Niagara flipbook **DUPLICATE** — both exist:
  - **Authority:** `Content/Melodia/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` (+ Water MI)
  - **Archive candidate:** `Content/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` (+ Water MI)

## Engine / WorldGrid (text + handoffs)

Historical / documented hits (need live editor re-verify on Melodia showcase levels):
- `SM_Outside_Wall` WorldGrid slot (`MATERIAL_TEXTURE_ROUTING_HANDOFF_2026-08-13`)
- Sea Above reef ingest meshes were WorldGrid at ingest (`NIAGARA_HOUDINI_FX_REVIEW_2026-08-30`); P0 baseline claimed Gaea / LiquidCathedral reparents
- `Saved/Audit/study_library_paradise.json` previously showed many `WorldGridMaterial` name slots (file may be local-only / not always present)

Engine placeholder textures in T3D baselines (WeightMapPlaceholder etc.) are normal for landscape masters — **not** the same as mesh WorldGrid defaults.

## Next (editor open)
1. Live mesh audit: Melodia + EnvSandbox showcase levels for remaining WorldGridMaterial
2. Create `M_SurrealFabric_Flipbook` + `MF_FlipbookScrub` (new assets only; no graph-clear)
3. Batch 4 validate on SHIP authorities — **no** Monolith `save_packages` / `recompile_material`; owner Ctrl+S

## Hard rules
- No Monolith `save_packages` / `recompile_material` from agents
- Owner Ctrl+S only
