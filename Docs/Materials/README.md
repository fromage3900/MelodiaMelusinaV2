# Melodia materials index (find me on git)

**Canonical entry point for material wiring.** Updated 2026-09-09 (post ALL_MATERIALS gate).

If you only open one folder: `Docs/Materials/`.

## Plans
- **Follow-on (active):** [MATERIALS_WIRING_FLIPBOOK_CLEANUP_2026-09-09.md](../Plans/MATERIALS_WIRING_FLIPBOOK_CLEANUP_2026-09-09.md) — Batch 4 wiring, flipbook Lane D, deprecate/label clean-env
- Prior soft-freeze (COMPLETE via #156): [MATERIALS_NIKKI_OCEAN_SDF_FINALIZATION_2026-09-09.md](../Plans/MATERIALS_NIKKI_OCEAN_SDF_FINALIZATION_2026-09-09.md)

## Label legend

| Label | Meaning |
|-------|---------|
| **SHIP** | Production authority |
| **LEGACY** | Retire after consumers reparented |
| **QUARANTINE** | Do not ship |
| **SCRATCH** | Ignore |
| **DUPLICATE** | Pick one authority; archive the other |

Full map: [LABEL_MAP_2026-09-09.md](LABEL_MAP_2026-09-09.md). Process: label → redirect → archive → delete.

## Four masters / surfaces

| Lane | Authority asset | Living docs |
|------|-----------------|-------------|
| **A - Nikki landscape** | **`/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape`** (owner authority as of 2026-09-03 convergence). Legacy Living Storybook: `M_Master_Toon_Landscape_HeightBlend` (retire after remaining MI reparents). | [landscape_authority_convergence_2026-09-03.json](../../Saved/Audit/landscape_authority_convergence_2026-09-03.json) (Saved/Audit - local), [LANDSCAPE_LIVING_STORYBOOK_MASTER.md](../LANDSCAPE_LIVING_STORYBOOK_MASTER.md) (legacy HeightBlend contract), [LANDSCAPE_MASTER_REPAIR_2026-08-29.md](../Handoffs/LANDSCAPE_MASTER_REPAIR_2026-08-29.md) |
| **B - Oceanology** | `/Game/EnvSandbox/Materials/Masters/M_Water_Oceanology_Melodia` (+ `MI_Oceanology_Melodia_Hero`) | [OCEANOLOGY_ENABLE_STATE_2026-08-27.md](../Handoffs/OCEANOLOGY_ENABLE_STATE_2026-08-27.md), [OCEANOLOGY_WATER_PLACEMENT_AND_CYMATIC_INTEGRATION_2026-09-02.md](../OCEANOLOGY_WATER_PLACEMENT_AND_CYMATIC_INTEGRATION_2026-09-02.md) |
| **C - SDF masters** | Blessed parents `/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon`, `/Game/EnvSandbox/Materials/Masters/M_Toon_SDF`; ornament family under `Masters/SDF/` | [sdf_parents_form.json](../sdf_parents_form.json), [SDF_UTILITY_RETRO_GRAPHICS_CHEATS_PLAN_2026-08-09.md](../SDF_UTILITY_RETRO_GRAPHICS_CHEATS_PLAN_2026-08-09.md) |
| **D - Flipbook** | Niagara: `/Game/Melodia/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` (authority). Cloth/fabric: `M_SurrealFabric_Flipbook` **MISSING** (create). Shared MF: `MF_FlipbookScrub` (spec only). | [FLIPBOOK_STATUS_2026-09-02.md](../FLIPBOOK_STATUS_2026-09-02.md), [MF_FlipbookScrub.v1.json](../../specs/materials/MF_FlipbookScrub.v1.json) |

## Cymatics bus (shared)
- MPC: `/Game/Melodia/Cymatics/MPC_Cymatics_Driver` (verified populated 2026-09-03)
- Landscape tap: `CymaticsLandscapeAmount` on Nikki landscape (default 0 = zero-delta)

## Receipts
- [RECEIPT_LANDSCAPE_NIKKI_2026-09-09.md](RECEIPT_LANDSCAPE_NIKKI_2026-09-09.md)
- [RECEIPT_OCEANOLOGY_2026-09-09.md](RECEIPT_OCEANOLOGY_2026-09-09.md) (#151 → `26794063`)
- [RECEIPT_SDF_MASTERS_2026-09-09.md](RECEIPT_SDF_MASTERS_2026-09-09.md) (#152 → `da667673`)
- [RECEIPT_ALL_MATERIALS_MERGED_2026-09-09.md](RECEIPT_ALL_MATERIALS_MERGED_2026-09-09.md) (**GATE PASS** — Live Link / Rokoko restart unlocked; caveats in receipt)
- `RECEIPT_WIRING_BATCH4_*.md` (pending Phase A)
- `RECEIPT_FLIPBOOK_*.md` (pending Phase B)
- `RECEIPT_MATERIALS_CLEAN_ENV_*.md` (pending Phase C)
- [RECEIPT_OFFLINE_WORLDGRID_FLIPBOOK_2026-09-09.md](RECEIPT_OFFLINE_WORLDGRID_FLIPBOOK_2026-09-09.md) (offline inventory)

## Hard rules
- One concern per PR / isolated batch from **main**.
- Read-back or compile stats beat tool return values.
- No Monolith `save_packages` / `recompile_material`. Owner Ctrl+S for editor packages.
- Do not run graph-clearing landscape rebuild scripts against the active master.
- Soft-freeze for Live Link / Rokoko satisfied via ALL_MATERIALS on main; remaining polish is Batch 4 + Lane D + clean-env (this index).

