# Receipt - Materials clean-env stubs + TextureWeight - 2026-09-09

**Status:** LIVE PASS + **owner Ctrl+S confirmed** (dirty packages 0)  
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
| Load fail (DemoRoom / `*_BS` / missing) | **82** (many were CSV naming; later recovered) |
| Later DemoRoom/house/GPU recover + stub | **+75** slots (`Button_BS.Button` pattern) |

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

- [x] Owner Ctrl+S confirmed (TW + stubs + sheep VFX)
- [x] TextureWeight=0 census - see [RECEIPT_TEXTUREWEIGHT_SCAN_2026-09-09.md](RECEIPT_TEXTUREWEIGHT_SCAN_2026-09-09.md)
- [ ] Melusina V2Test slots → proper character MIs (not stubs)
- [x] DemoRoom `*_BS` naming quirk documented (package vs object); +75 stubbed
- [ ] LABEL_MAP ENGINE_DEFAULT row → LEGACY cleared after Ctrl+S

## LABEL_MAP fold (same evening)

Updated [LABEL_MAP_2026-09-09.md](LABEL_MAP_2026-09-09.md) with New Bot landscape/SDF/VFX deprecate audit: Enhanced QUARANTINE, HeightBlend 28 LEGACY pointer (#158), _PROJECT VFX DUPLICATE + sheep MI retarget owed, WorldGrid PARTIAL after stub assign.

## Evening follow-on (New Bot live)

- TextureWeight Universal/Wool scan: **2128** scanned, **34** set to `1.0` (sheep coats skipped). Receipt: [RECEIPT_TEXTUREWEIGHT_SCAN_2026-09-09.md](RECEIPT_TEXTUREWEIGHT_SCAN_2026-09-09.md); full list local `Saved/Audit/TEXTUREWEIGHT_SCAN_2026-09-09.*`.
- DemoRoom `*_BS` SCRATCH naming: ENGINE CSV used package name as object; correct form `Package.Object` (e.g. `Button_BS.Button`). **+75** slots stubbed after rename fix.
- Melusina V2Test **33** None rows still owner-parked (real character MIs, not stubs).
- Sheep VFX WoolMote/BeatStar parents already Melodia/_PROJECT; Owner Ctrl+S confirmed for TW + stub + sheep VFX packs.
