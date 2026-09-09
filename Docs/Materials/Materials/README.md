# Melodia materials index (find me on git)

**Canonical entry point for material wiring.** Updated 2026-09-09.

If you only open one folder: `Docs/Materials/`.

## Finalization plan (tonight)
- [MATERIALS_NIKKI_OCEAN_SDF_FINALIZATION_2026-09-09.md](../Plans/MATERIALS_NIKKI_OCEAN_SDF_FINALIZATION_2026-09-09.md)

## Three masters / surfaces (equal love)

| Lane | Authority asset | Living docs |
|------|-----------------|-------------|
| **A — Nikki landscape** | **`/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape`** (owner authority as of 2026-09-03 convergence). Legacy Living Storybook: `M_Master_Toon_Landscape_HeightBlend` (retire after remaining MI reparents). | [landscape_authority_convergence_2026-09-03.json](../../Saved/Audit/landscape_authority_convergence_2026-09-03.json) (Saved/Audit — local), [LANDSCAPE_LIVING_STORYBOOK_MASTER.md](../LANDSCAPE_LIVING_STORYBOOK_MASTER.md) (legacy HeightBlend contract), [LANDSCAPE_MASTER_REPAIR_2026-08-29.md](../Handoffs/LANDSCAPE_MASTER_REPAIR_2026-08-29.md) |
| **B — Oceanology** | `/Game/EnvSandbox/Materials/Masters/M_Water_Oceanology_Melodia` (+ `MI_Oceanology_Melodia_Hero`) | [OCEANOLOGY_ENABLE_STATE_2026-08-27.md](../Handoffs/OCEANOLOGY_ENABLE_STATE_2026-08-27.md), [OCEANOLOGY_WATER_PLACEMENT_AND_CYMATIC_INTEGRATION_2026-09-02.md](../OCEANOLOGY_WATER_PLACEMENT_AND_CYMATIC_INTEGRATION_2026-09-02.md) |
| **C — SDF masters** | Blessed parents `/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon`, `/Game/EnvSandbox/Materials/Masters/M_Toon_SDF`; ornament family under `Masters/SDF/` | [sdf_parents_fix.json](../sdf_parents_fix.json), [SDF_UTILITY_RETRO_GRAPHICS_CHEATS_PLAN_2026-08-09.md](../SDF_UTILITY_RETRO_GRAPHICS_CHEATS_PLAN_2026-08-09.md) |

## Cymatics bus (shared)
- MPC: `/Game/Melodia/Cymatics/MPC_Cymatics_Driver` (verified populated 2026-09-03)
- Landscape tap: `CymaticsLandscapeAmount` on Nikki landscape (default 0 = zero-delta)

## Receipts
- [RECEIPT_LANDSCAPE_NIKKI_2026-09-09.md](RECEIPT_LANDSCAPE_NIKKI_2026-09-09.md)
- `RECEIPT_OCEANOLOGY_2026-09-09.md` (New Bot)
- `RECEIPT_SDF_MASTERS_2026-09-09.md` (New Bot)
- `RECEIPT_ALL_MATERIALS_MERGED_2026-09-09.md` (gate for UE restart)

## Hard rules
- One concern per PR / isolated batch from **main**.
- Read-back or compile stats beat tool return values.
- No Monolith `save_packages`. Owner Ctrl+S for editor packages.
- Do not run graph-clearing landscape rebuild scripts against the active master.
- UE Live Link / Rokoko restart waits until all three receipts + ALL_MATERIALS_MERGED exist on **main**.
