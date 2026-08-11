# Sakura and Water PCG Expansion Review

## Purpose

This review turns the current Sakura PCG, universal PCG, Niagara, and water simulation evidence into a practical expansion plan. It supports the Sakura environment without taking over composition, hero asset placement, or final art direction.

## Current Evidence

| System | Evidence | Status |
| --- | --- | --- |
| Universal Niagara | `Saved/Audit/niagara_library_build.json` | 19 systems, no build errors; 8 new `NS_Uni_*` systems created. |
| VFX manifest | `Saved/Portfolio/VFX/universal_niagara_manifest.json` | 19 systems are `structural_ready_visual_tuning_required`. |
| Universal PCG | `Saved/Audit/pcg_universal_build.json` | Passed. Core graphs and style graphs exist. |
| Sakura PCG | `Saved/Audit/sakura_pcg_build.json` | Passed structurally, but latest headless generation produced 0 ISMs. |
| Water simulation | `Saved/Audit/ue_water_sim_audit.json` | Passed. `WaterBody_SakuraPond` exists and `MI_GrandWater_SakuraPond` is assigned. |

## Key Findings

### PCG

Universal PCG is further along than the older scene docs imply. The project already has:

- `PCG_FoliageDensity`
- `PCG_RockScatter`
- `PCG_ExclusionFalloff`
- `PCG_MeadowBloom`
- `PCG_BlossomPath`
- `PCG_LanternGrove`
- `PCG_GardenRuins`
- `PCG_Sakura_PetalDrift`
- `PCG_Zen_MossGroundcover`
- `PCG_Sakura_Showcase`

The immediate problem is not lack of graphs. It is reliability of generation context: latest Sakura PCG evidence reports `structural_pass=true`, `generated=true`, but `ism_total=0`. The log also reported surface sampler warnings. That means expansion should focus on tagged surfaces, stable volumes, and exclusion wiring before adding more layers.

### Sakura

Sakura PCG should remain a support system:

- PCG owns static groundcover, moss, tiny flowers, static petal cards, rocks, and path-side accents.
- Niagara owns motion: canopy drift, ground petal drift, gusts, pond shimmer, mist, fireflies, and water mist.
- User-owned composition remains protected: no automated hero prop placement, no final set dressing decisions, no art-directing `L_SakuraPath`.

### Water And Fluid

Water is already technically live:

- `WaterBody_SakuraPond` exists.
- `MI_GrandWater_SakuraPond` is assigned.
- The pond plane is hidden when the water body is active.

The expansion should treat "fluid systems" as three coordinated layers:

1. Material water: `M_Water_Master_Grand_v6` and `MI_GrandWater_*`.
2. Niagara water VFX: `NS_Uni_WaterMist`, `NS_Uni_RainRipples`, `NS_SakuraPondShimmer`.
3. PCG shoreline ecology: reeds, wet stones, moss clumps, flowers, pond-edge debris, and exclusion around water.

## Expansion Plan

### Phase 1: Stabilize Sakura PCG Surfaces

Goal: make headless/editor generation produce nonzero ISMs without increasing complexity.

Actions:

- Confirm the ground actor or landscape has `PCG_Ground`.
- Confirm `PCG_Exclude_Path` and `PCG_Exclude_Pond` exist and are correctly sized.
- Add a non-destructive audit that reports tagged ground surfaces, exclusion volumes, PCG volumes, selected graph paths, and ISM totals.
- Keep density conservative until `ism_total` is stable.

Acceptance:

- `sakura_pcg_build.json` reports `ism_total > 0`.
- `ism_total` is inside `ISM_BAND_SAKURA` after an editor generation pass.
- No scatter appears inside path, pond, or torii exclusion volumes.

### Phase 2: Add Static Sakura Detail Layers

Goal: add layers that support the scene without competing with Niagara.

Candidate layers:

- `PCG_Zen_MossGroundcover`: moss and soft grass around stones.
- `PCG_BlossomPath`: static petal cards on path shoulders.
- `PCG_Sakura_PetalDrift`: rename or clarify as static petal scatter if Niagara owns drifting motion.
- `PCG_MeadowBloom`: tiny flowers and botanical points.

Rules:

- Static petals should be low density and mostly grounded.
- Niagara ground petals remain the moving layer.
- Do not automate hero tree, torii, bridge, or lantern placement.

Acceptance:

- Each layer has a clear role and material assignment.
- PCG/Niagara responsibilities do not overlap.
- Captures show ground richness without hiding path readability.

### Phase 3: Water Edge PCG

Goal: create a reusable shoreline support lane for Sakura and future ponds/rivers.

Recommended graph:

- `PCG_WaterEdgeScatter`

Responsibilities:

- Shoreline stones.
- Moss clumps.
- Reeds or soft grass.
- Small wet-ground accents.
- Optional fallen petals near pond edge, static only.

Required tags:

- `PCG_Pond`
- `PCG_Exclude_Pond`
- `PCG_Ground`
- Optional `PCG_WaterEdge`

Acceptance:

- Water edge scatter respects pond exclusion.
- Scatter reinforces water/material contact instead of covering water.
- Works in `L_Template` or neutral pond test before Sakura composition use.

### Phase 4: Fluid Presentation Layer

Goal: make water feel alive without pretending PCG is simulation.

Use:

- `MI_GrandWater_SakuraPond` for pond surface.
- `NS_SakuraPondShimmer` for Sakura-specific sparkle.
- `NS_Uni_WaterMist` for pond/shore/waterfall mist.
- `NS_Uni_RainRipples` for rainy material showcases.

Do not use PCG for moving water. PCG should place static environmental supports only.

Acceptance:

- Water body remains material-assigned and visible.
- VFX is localized and does not obscure water shader quality.
- Water system can be demonstrated in `L_Template` before final Sakura shot use.

## Script Fix Applied

`Content/Python/setup_pcg_sakura.py` now forwards `--no-spawn` and `--rebuild` into the nested UnrealEditor-Cmd call. This prevents future "no-spawn" audits from accidentally running the default spawn path.

## Known Issues

| Issue | Evidence | Recommendation |
| --- | --- | --- |
| Latest Sakura PCG generation produced zero ISMs | `sakura_pcg_build.json`, PCG surface sampler warnings | Audit tagged surfaces and PCG volume placement before adding density. |
| `PCG_Sakura_Showcase.uasset` save failed once due file lock | Unreal run log, Error Code 32 | Close other editor/session handles before graph rebuilds. |
| Exclusion subgraph is currently passthrough | `pcg_universal_build.json` reports `tag_filter=false` | Implement or verify tag filter support before relying on exclusion behavior. |
| Water simulation can hide `KoiPond` | `setup_ue_water_simulation.py` behavior and audit | Treat water sim runs as yellow/red gated; run in editor when intentionally updating the scene. |

## Next Commands

Safe reports:

```text
python Content/Python/universal_niagara_manifest.py
python Content/Python/setup_pcg_sakura.py --no-spawn
```

Editor actions:

```text
py Content/Python/setup_pcg_sakura.py
py Content/Python/setup_ue_water_simulation.py
py Content/Python/validate_sakura_niagara.py
```

Use editor actions only when the Sakura scene can be opened and visually checked.
