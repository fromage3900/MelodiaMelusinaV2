# Material specialists pivot plan (post–Universal spine)

Universal (`M_Master_Toon_Universal`) is the **mesh/surface spine**. These masters stay **specialist** — do not fold into Universal.

## Phased expansion checklist

### Track A — Grand water ✅

| Step | Script / asset | Done when |
|------|----------------|-----------|
| A1 Graph audit | `audit_grand_water.py` → `grand_water_graph_audit.json` | Params, blend mode, WPO flagged |
| A2 Groups + MFs | `organize_water_groups.py`, `MF_WaterDepthColor`, `MF_WaterShorelineFade`, `expand_grand_water.py` | 12+ grouped params, depth/shoreline wired |
| A3 Instances | `setup_master_water.py` — 5 MIs incl. `ShorelinePond`, tuned `SakuraPond` | `grand_water_expand.json` green |
| A4 Scene + VFX | `setup_sakura_scene.py`, `NS_SakuraPondShimmer` touchpoints, `SCENE_SakuraPath.md` | Pond = grand water in docs + scene audit |

### Track B — Landscape height blend (Phase 1) ✅

| Step | Script / asset | Done when |
|------|----------------|-----------|
| B1 MF extract | `MF_LandscapeHeightCompete` in `setup_material_functions.py` | Master uses MF with inline fallback |
| B2 Params + groups | `NormalStrength`, `Wetness`, `PathWear`, `organize_landscape_groups.py` | Grouped params in editor |
| B3 Instances | 6 MIs: CliffGrass, Meadow, SnowAlpine, SakuraGarden, ForestFloor, CoastalCliff | `landscape_height_blend.json` |
| B4 Template | `setup_template_showcase.py` — meadow ground slab in `L_Template` | Viewport validates triplanar blend |

### Track C — Landscape layer painting (Phase 2) ✅

| Step | Script / asset | Done when |
|------|----------------|-----------|
| C1 LayerInfo | `setup_landscape_layers.py` — `Rock/Grass/Mud/Path` under `Materials/Landscape/` | Assets created + audit JSON |
| C2 Weight branch | `bUsePaintedLayers` + full splat color/normal/roughness | Procedural fallback when paint sum ≈ 0 |
| C3 Workflow | This doc + `MATERIAL_INTEGRATION.md` run order | Paint guide documented |

### Track D — Professional + Nikki on landscape ✅

| Step | Deliverable |
|------|-------------|
| D1–D2 | Full 4-layer paint blend, `bUseLandscapeUV`, per-layer roughness, `MI_Landscape_PondBank` |
| E1–E3 | `MF_NikkiDreamGrade/RimGlow/Sparkle/IridescenceSheen` wired on landscape master |
| F1–F4 | Water shoreline emissive + `MPC_SakuraDream` pulse; Sakura scene terrain/bank proxies |
| Loop | `run_specialist_terrain_loop_tick.py` — sentinel `AGENT_LOOP_WAKE_specialist_terrain` |

**Nikki recipes (landscape):**
- `MI_Landscape_SakuraGarden` — `PastelLift` 0.22, `DreamSaturation` 0.18, ground sparkle, low iridescence
- `MI_Landscape_PondBank` — high `Wetness` + `ShoreWetnessBoost`, cool `RimColor`, pairs with `MI_GrandWater_SakuraPond`

---

## Survey summary

### Water
| Asset | Status | Notes |
|-------|--------|-------|
| `M_Water_Master_Grand_v6` | **Canonical** — expanded params | Gerstner, caustics, depth color, shoreline UV, magical intensity |
| `setup_master_water.py` | 5 instances + caustic wiring | `MI_GrandWater_*` under `Instances/Water/` |
| `M_Master_Toon_Water` | **Deprecated** | Do not expand |
| `MI_Sakura_Water` | On **Universal** + `TP_Glass` | Prop fallback only — not koi pond |
| `NS_SakuraPondShimmer` | Pairs with `MI_GrandWater_SakuraPond` | VFX tuned to grand water roughness/magical |

### Landscape
| Asset | Status | Notes |
|-------|--------|-------|
| `M_Master_Toon_Landscape_HeightBlend` | Python-built, full graph | Height competition + painted layer branch |
| `setup_landscape_height_blend.py` | 6 instances | incl. `ForestFloor`, `CoastalCliff`, `SakuraGarden` |
| `setup_landscape_layers.py` | LayerInfo assets | Rock / Grass / Mud / Path paint layers |
| `M_Master_Impressionist_Toon_Landscape` | Painterly specialist | Separate — keep |
| `M_HybridLandscape_MooaToonSDF` | Melodia deferred | Not in repo |

**Sakura terrain:** Scene stays mesh greybox until CC0 terrain; `MI_Landscape_SakuraGarden` ready for future landscape actor.

### Other specialists (keep separate)
- **SDF family** (`M_SDF_*`, `M_Master_SDF_Toon`) — architectural procedural
- **Impressionist** (`M_Master_Impressionist_Toon` + landscape variant) — oil/painterly
- **Post-process** (`M_PP_ToonOutline`, `M_PP_StorybookVines`)
- **Niagara sprite MIs** (`MI_Niagara_*`) — particle materials, not surface masters

### Universal coverage (what it should NOT do)
- Translucent water with Gerstner WPO + caustics
- Landscape `bUsedWithLandscape` height-blend across splat layers
- Full-screen PP / Niagara sprite shading

---

## Folder map

| Folder | Contents |
|--------|----------|
| `Instances/Water/` | `MI_GrandWater_*` |
| `Instances/Landscape/` | `MI_Landscape_*` |
| `Instances/Sakura/` | `MI_Sakura_*` (Universal mesh props) |
| `Instances/Showcase/` | `MI_Show_*` starter presets |
| `Materials/Landscape/` | LayerInfo assets `Rock`, `Grass`, `Mud`, `Path` |

---

## Paint workflow (Phase 2)

1. Run `python Content/Python/setup_landscape_layers.py`
2. Create Landscape actor → assign `MI_Landscape_Meadow` (or `SakuraGarden`)
3. Paint **Rock**, **Grass**, **Mud**, **Path** using LayerInfo from `/Game/EnvSandbox/Materials/Landscape/`
4. Set `bUsePaintedLayers=true` on the MI when weights exist
5. Empty / unpainted landscape uses procedural height competition (no break)

---

## Track E — Zen AAA ✅

| Step | Script / asset | Done when |
|------|----------------|-----------|
| E1 Specs | `zen_instances.py` — 15 `MI_Zen_*` | Motif/Fairy/Sparkle keys per preset |
| E2 Apply | `apply_zen_instances.py` → `build_theme_instances()` | JRO masks + catalog albedo wired |
| E3 Audit | `audit_zen_trimsheet.py` | `zen_trimsheet_aaa_audit.json` zen section green |

**Folder:** `Instances/Environment/Zen/` · **Pack:** `/Game/Textures/70_Japanese_Ornament_Alphas_vfxMed`

---

## Track F — ZenTrim trimsheet AAA ✅

**Instances only** — master `M_Master_Toon_Universal` Layer A/B lerp unchanged.

| Step | Script / asset | Done when |
|------|----------------|-----------|
| F1 Catalog | `zen_trim_textures.py` — 7 variants × 7 channels | All `/Game/Textures/ZenTrim_*` resolve |
| F2 Instances | `setup_trimsheet_instances.py` — 9 MIs | Layer A=`Base4K`, Layer B=variation maps wired |
| F3 Audit | `audit_zen_trimsheet.py` trimsheet section | All Layer A/B params resolve |

**Variants:** Base4K, ColourShift, CrackedToHell, FlowersLIttleBit, FlowersLOTS, FlowersMid, Wet

**Folder:** `Instances/Environment/Stylized/`

---

## Portfolio AAA loop

`run_material_aaa_loop_tick.py` — 10 rotating tasks → `material_aaa_loop_state.json`

Sentinel: `AGENT_LOOP_WAKE_material_aaa` (15m fallback heartbeat while napping)

---

## Script run order

See `Docs/MATERIAL_INTEGRATION.md` § Environment specialists for the full headless pipeline.
