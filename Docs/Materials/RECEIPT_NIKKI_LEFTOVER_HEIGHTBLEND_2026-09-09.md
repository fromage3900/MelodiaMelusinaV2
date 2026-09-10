# Receipt - Nikki leftover validate + HeightBlend reparent list - 2026-09-09

**Status:** VALIDATE PASS + parent lists FILLED (read-back only)  
**Owner lane:** Melodia study bot (docs) · **Live fill:** New Bot 2026-09-09 (~20:07 ET)  
**Index:** [Docs/Materials/README.md](README.md) · **Labels:** [LABEL_MAP_2026-09-09.md](LABEL_MAP_2026-09-09.md)  
**Authority:** `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape` (**SHIP**)  
**Legacy:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend` (**LEGACY**)  
**Source:** Monolith `validate_material` + `list_material_instances` (NO save_packages / NO recompile)

## A) Fresh validate (FILLED)

| Check | Result |
|-------|--------|
| `validate_material` `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape` (`fix_issues=false`) | **PASS** — **hard errors: 0**; warnings: **126** (islands / unused_parameter mainly); info: 1 |
| Parent of `MI_Glacier_Landscape_Layered` | **Nikki** (confirmed) |
| Sea Above / Glacier PIE | still owner smoke |
| Scratch `_Scratch/M_Master_Nikki_Landscape` | SCRATCH — not authority |

## B) Reparent progress (live Asset Registry)

| Bucket | Count |
|--------|-------|
| On **Nikki** authority | **9** |
| Still on **HeightBlend** | **28** |
| Prior audit claim | 19/37 core — live count differs; **prefer this registry list** |

### On Nikki (9) — keep / SHIP consumers

1. `/Game/Gaea/Glacier/Materials/MI_Glacier_Landscape_Layered`
2. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CarvedRock`
3. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow`
4. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_NikkiDream`
5. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_PondBank`
6. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_SnowAlpine`
7. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_UrbanCobble`
8. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_VolcanicRock`
9. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_WetlandMud`

### Still on HeightBlend (28) — reparent → Nikki or explicitly defer

New Bot registry (`list_material_instances` parent = `M_Master_Toon_Landscape_HeightBlend`):

| Path / family | Suggested action |
|---------------|------------------|
| `MI_Master_Toon_Landscape_HeightBlend_Inst` | reparent or retire with master |
| MelusinaReal HeightBlend Grass / Grayscale / Soil | reparent → Nikki or LEGACY-keep until MelusinaReal pass |
| `MI_Landscape_CliffGrass`, `CoastalCliff`, `DesertArid`, `ForestFloor`, `Grass_Tilable_*`, `SakuraGarden`, `WitchGarden` | **reparent → Nikki** (core landscape) |
| `MI_SakuraLandscape` (×2 paths incl. Masters/) | reparent → Nikki; move Masters/ copy to Instances (path hygiene) |
| Gaea Cadence / Fugue / Sakura substrates | owner call: reparent vs Gaea-specific defer |
| SeaAbove CanonicalLandscape + LiquidCathedral substrates | **reparent → Nikki** (Sea Above should match Glacier) |
| Showcase2 Landscape ×3 | **defer showcase** (owner) |
| Terrain Baroque / Cosmic / Sakura / Space substrates | owner triage |
| `Zen_RakedSand` | owner triage |
| `_Scratch` / `Test_Landscape` | **SCRATCH** — ignore |

Exact 28 soft-paths: live Monolith dump 2026-09-09 (New Bot). If a name above is abbreviated, prefer registry path over this summary.

## C) Still open (not blockers for this receipt)

- [ ] Owner Ctrl+S after any intentional reparent batch
- [ ] PIE confirm Sea Above / Glacier after reparents
- [ ] HeightBlend master quarantine only after consumers clear (LABEL_MAP LEGACY)

## Hard rules

- No Monolith `save_packages` / `recompile_material` from agents.
- Owner Ctrl+S for package saves.
- One concern per PR off **main**.
