# Receipt - Materials clean-env stubs + TextureWeight - 2026-09-09

**Status:** LIVE PASS (unsaved until owner Ctrl+S)  
**Index:** [Docs/Materials/README.md](README.md) · **Labels:** [LABEL_MAP_2026-09-09.md](LABEL_MAP_2026-09-09.md)  
**Plan:** [MATERIALS_WIRING_FLIPBOOK_CLEANUP_2026-09-09.md](../Plans/MATERIALS_WIRING_FLIPBOOK_CLEANUP_2026-09-09.md) Phase C

## Stub MIs (SHIP lookdev defaults)

| MI | Parent | Maps | TextureWeight |
|----|--------|------|---------------|
| `/Game/Melodia/Materials/Lookdev/MI_Melodia_Stub_Toon` | `M_Master_Toon_Universal` | PearlWeave albedo/normal/ORM/rough/height/metallic | **1** (override) |
| `/Game/Melodia/Materials/Lookdev/MI_Melodia_Stub_Fabric` | `M_Master_Toon_Universal` | RoseVelvet full set | **1** (override) |

Also present: `MI_Universal_Lookdev_PearlWeave`, `RoseVelvet`, `CymaticOrchid` (TW=1 + maps).

## Why TextureWeight matters

On Universal / Chorus Wool masters, `TextureWeight` (group `01 | Base Surface`) defaults to **0** and multiplies `LayerA/B/C_TextureWeight`. Inherited **0** zeros layer texture contribution — coats/meshes look flat until overridden (~1+).

Sheep coats: owner PCB template **1.3944** applied to all 12 `MI_ChoralSheep_Coat_PC*`; Body left **≈0.944**.

## Static mesh engine-default cleanup (live)

Source inventory: `Saved/Audit/ENGINE_DEFAULT_SM_SLOTS_2026-09-09.csv` (New Bot scan: 2515 SM, 51 WorldGrid, 187 None).

| Result | Count |
|--------|------:|
| Assigned Stub_Toon / Stub_Fabric | **123** |
| Skipped Melusina V2Test character meshes | (keep for real character MIs) |
| Skipped scratch `_GENERATED/froma` | 1 |
| Load fail (DemoRoom / `*_BS` / missing) | **82** |

Spot-check after assign (mesh_query):

- `SM_Piano_Keybed` → Stub_Toon
- `SM_P4_Cathedral_Grand` → Stub_Toon
- `windmill` → Stub_Toon
- `SM_FarawayMother_FabricRidge` → Stub_Fabric
- `choralsheephi` → Stub_Fabric

## Hard rules

- No Monolith `save_packages` / `recompile_material`.
- Owner **Ctrl+S** for dirty mesh + lookdev + sheep coat packages.
- Retirement: label → redirect → archive → delete (never cold-delete).

## Still open

- [ ] Owner Ctrl+S
- [ ] TextureWeight=0 census on remaining Universal-family MIs (New Bot)
- [ ] Melusina V2Test slots → proper character MIs (not stubs)
- [ ] DemoRoom/`*_BS` load failures triage
- [ ] LABEL_MAP ENGINE_DEFAULT row → LEGACY cleared after Ctrl+S
