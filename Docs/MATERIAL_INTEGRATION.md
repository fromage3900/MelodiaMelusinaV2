# Material integration (2026-06-19)

Session summary for portfolio masters, SDF expansion, compositing textures, and editor tooling.

## What landed

| Area | Result |
|------|--------|
| **Universal masters** | `M_Master_Toon_Universal`, `M_Master_SDF_Toon`, `M_Master_Toon_Unified` — 18/18 texture params wired, Substrate Toon, compile OK |
| **Starter instances** | 11 curated MI_Show_* under Instances/Showcase — one master capability each (see below); trimsheet layer/parallax demos live under Instances/Environment/Stylized/ |
| **Legacy MI_Universal_*** | 141+ presets deprecated; move to `Instances/_Archive/` via `archive_unused_instances.py` (no delete) |
| **SDF masters** | All 50 `_PROJECT` `M_SDF_*` ported to `EnvSandbox/Materials/Masters/` (incl. 9 aquatic) |
| **Aquatic instances** | `MI_SDF_AbyssalVent_Deep` … `MI_SDF_ThermalGlow_Vent` under `SDF/Instances/` |
| **Toon conversion** | Batches 1–4 via `run_phase_a_safe.py` (baroque, hybrid, aquatic, math/musical expansion) |
| **Storybook PP** | `M_PP_StorybookVines` + `_Inst` rebuilt; stack after `M_PP_ToonOutline` |
| **Blender Live Link** | Menu: **LiveLink → Start/Stop/Status** (not Window → Live Link); see `BLENDER_LIVELINK.md` |

## Master parameter organization (`M_Master_Toon_Universal`)

Groups in the Material Editor (rebuild master with `--force` after group renames):

| Group | Purpose |
|-------|---------|
| **Textures / LayerA / LayerB** | Albedo, normal, ORM, height, detail |
| **Triplanar / Temporal** | World-aligned UVs, ink boil/smear |
| **Parallax** | **`MF_ParallaxCore`** — modes 0/1/2 height UV offset; **`MF_NormalAdjust`** — `NormalStrength`, `NormalPower`, per-layer strengths; `ParallaxSteps` wired |
| **Nikki** | Infinity Nikki environment look stack: rim/glow shaping, sparkles, dreamy grading, iridescence, fabric sheen + quality switches |
| **Celestial** | **`MF_SpaceParallax`** — parallax stars/nebula/galaxy with toon-banded nebula; `StarMap` texture + `CelestialToonSteps`; legacy `ConstellationPhase` / `CelestialTwinkle` / `CelestialGalaxyArms` kept for MI compat (no graph wiring) |
| **Gilding** | Curvature gold leaf |
| **ShadowDream** | Soft N·L shadow color tint |
| **FlowerShadow** | Projected petal silhouettes in shadow (was `ShadowGarden`) |
| **Audio** | `MPC_Portfolio_Audio` reactivity — emissive, layer blend, roughness, BeatPhase hooks |
| **FairyDust** | Highlight motif styles (heart/star/flower/moon) |
| **Magical** | Henshin wipe, `MotifMask`, palette shift, transform glow |
| **Madoka** | Ethereal witch barrier: voronoi veins, cute/corrupt color blend, radial spectral rings, SSS fake glow; feeds emissive and base color |
| **Itto** | Heavy mythic carved: truchet ornament cracks, curvature wear mask, surface breakup, ink lines, height deltas added to landscape competition |
| **Character** | Skin wrap, cheek warmth, eye highlight, hair sheen |
| **Elemental / Cinematic** | Hydro/py/etc., contact rim, distance fade |

Key expansion params have inline `desc` tooltips when the master is rebuilt via `setup_master_universal.py`.

## Starter instances (11)

Canonical set on `M_Master_Toon_Universal` — one isolated capability each. Folder: `/Game/EnvSandbox/Materials/Instances/Showcase`. Source of truth: `Content/Python/starter_instances.py` (`STARTER_INSTANCES`, `STARTER_NAMES`).

| Instance | Theme | Purpose | Key params (editor group) |
|----------|-------|---------|---------------------------|
| `MI_Show_Default` | Default showcase | Neutral tint; identity normal/parallax baseline | `BaseTint`, `NormalStrength`, `TextureWeight` |
| `MI_Show_StoneCliff` | Stone | Triplanar cliff + **MF_ParallaxCore** POM + normal power | `ParallaxMode`, `ParallaxHeight`, `NormalStrength` (Parallax) |
| `MI_Show_CherryBlossom` | Flower shadow | Projected petal shadows + advanced sparkle on soft pink | `ShadowFlowerStrength`, `SparkleThreshold` (FlowerShadow + Nikki) |
| `MI_Show_CelestialNebula` | Nebula | **MF_SpaceParallax** constellation + Nikki sparkle/glow | `CelestialNebulaStrength`, `SparkleThreshold`, `StarMap` (Celestial + Nikki) |
| `MI_Show_FairyHearts` | Magic / fairy | Heart motif, fairy dust, henshin + Nikki rim/glow | `MagicalTransform`, `FairyDustIntensity`, `RimWidth` (Magical + Nikki) |
| `MI_Show_SkinSoft` | Nikki (environment) | Soft pastel + `bNikkiFast` path (contrast with Hero) | `PastelLift`, `bNikkiFast`, `DreamHueShift` (Nikki) |
| `MI_Show_NikkiHero` | Nikki (hero) | Full Nikki stack — rim/glow/sparkle/iridescence/sheen | `bNikkiHero`, `SparkleThreshold`, `IridescencePower` (Nikki) |
| `MI_Show_ForestFoliage` | Foliage | Mossy forest floor + dreamy Nikki grading | `MossConcavityStrength`, `DreamSaturation` (World + Nikki) |
| `MI_Show_ContactRimHero` | Cinematic | Contact rim + Nikki rim shaping + distance fade | `ContactRimStrength`, `RimWidth`, `DistanceFadeStrength` (Cinematic + Nikki) |
| `MI_Show_ElementHydro` | Elemental | Wet iridescent hydro glass (`ElementType=2`) | `ElementStrength`, `IridescencePower`, `WetnessStrength` (Elemental + Nikki) |
| `MI_Show_InkWash` | Stylized ink | Temporal boil + Nikki dream grade + smear | `TemporalStrength`, `DreamContrast`, `SmearStrength` (Temporal + Nikki) |

Legacy `MI_Universal_*` names map via `LEGACY_ALIASES` in `starter_instances.py` (e.g. `MI_Universal_DreamyPastel` → `MI_Show_SkinSoft`, `MI_Universal_NikkiHero` → `MI_Show_NikkiHero`).

**Landscape instances:** 11 presets (`MI_Landscape_Meadow` … `MI_Landscape_WetlandMud`). **Water instances:** 8 (`MI_GrandWater_*` incl. SakuraPond, SwampMurk, WaterfallSheet, FrozenPond).


## Universal repair lock (2026-07-01)

M_Master_Toon_Universal remains the single canonical universal master for portfolio mesh/surface materials. The 2026-07-01 repair rebuilt it in place through Content/Python/run_force_universal.py and confirmed 1041/1041 builder wires with no failures.

Focused fixes:
- Layer channels now blend sequentially A to B to C, gated by layer activation, so enabling an overlay no longer divides/dims Layer A when the overlay alpha is 0.
- Parallax UVs now apply ParallaxStrength once inside parallax_uv_offset; ParallaxStrength=0 is an identity UV path.
- Triplanar is controlled by TriplanarBlend (0=UV, 1=world-aligned) so all sampled channels blend consistently without a shared static-switch output.
- Normal flow still uses MF_NormalAdjust for global/per-layer strength and feeds the final Substrate Toon normal pin from the blended normal accumulator.
- Nikki behavior is preserved through the inline Nikki stack when the optional MF_Nikki* chain is unavailable.

Verification artifacts:
- Saved/Audit/universal_snapshot_before.json
- Saved/Audit/universal_build_last.json
- Saved/Audit/starter_instances.json
- Saved/Audit/universal_post_rebuild_validation.json
- Saved/Screenshots/universal_material_grid.png

## Infinity Nikki controls (environment)

These live on `M_Master_Toon_Universal` and are meant for **environment** materials (not skin shading). Defaults are neutral/off.

- **Nikki Rim & Glow**: `RimWidth`, `RimBias`, `RimClamp`, `InnerGlowWidth`, plus `bNikkiFast` / `bNikkiHero`.
- **Nikki Sparkle**: `SparkleThreshold`, `SparkleContrast`, `SparkleDriftSpeed`, `SparkleTwinkleSpeed`, optional gradient (`SparkleColorLow/High` + `SparkleColorLerp`), and `bSparkleAdvanced`.
- **Nikki Iridescence & Sheen**: grading (`DreamSaturation`, `DreamContrast`, `DreamShadowLift`, `DreamHighlightSoft`, `DreamHueShift`), iridescence shaping (`IridescencePower`, `IridescenceBias`, `IridescenceRoughnessAtten`), sheen shaping (`SheenWidth`, `SheenBias`, `bSheenUsesNormal`).

Quick recipes:
- **Soft pastel**: raise `PastelLift`, small `DreamSaturation`, negative `DreamContrast`, small `DreamShadowLift`.
- **Hero sparkle**: set `bNikkiFast=false`, `bNikkiHero=true`, enable `bSparkleAdvanced`, then tune `SparkleThreshold/Contrast` and twinkle/drift speeds.

## Blender Nikki Prototype Kit

SurrealArch now has a Blender-side prop prototype kit for quick lookdev before UE instance work: `Docs/MATERIAL_NIKKI_PROTOTYPE_KIT.md`. It wires `surreal_arch.nikki_mat_apply`, Melodia wrapper node groups (`MEL_NPR_LinearHalftone`, `MEL_NPR_Tiler`, `MEL_Mat_NikkiSurface`), the MM `nikki.json` tile recipe, and optional Higgsas surface grids. This is environment/prop scoped and explicitly skips Melusina and hair objects.

## Trimsheet instances (4)

Layer A/B blend presets on `M_Master_Toon_Universal`. Folder: `/Game/EnvSandbox/Materials/Instances/Environment/Stylized`. Source: `Content/Python/setup_trimsheet_instances.py`.

| Instance | Purpose | Key params |
|----------|---------|------------|
| `MI_Trimsheet_VariationCracks` | Crack overlay + stepped POM | `LayerBlend`, `ParallaxHeight`, `NormalPower` |
| `MI_Trimsheet_ParallaxPOM` | Parallax hero — full POM stack + normal power | `ParallaxStrength`, `ParallaxHeight`, `NormalStrength` |
| `MI_Universal_TrimsheetBlend` | Light blend starter | `LayerBlend`, `ParallaxMode`, `ParallaxStrength` |
| `MI_Trimsheet_HeavyWear` | Heavy wear + moss concavity | `LayerBlend`, `ParallaxMode`, `MossConcavityStrength` |

## SDF environment masters (top 5)

Procedural façade / stone kit — separate from `M_Master_Toon_Universal`. Folder: `/Game/EnvSandbox/Materials/Masters/` + `SDF/Instances/`. See `MATERIAL_MIGRATION.md` for full inventory.

| Master | Use case | Canonical params | Instance anchor |
|--------|----------|------------------|-----------------|
| `M_SDF_TrueParallax` | Façade relief / parallax panels | `BaseTint`, `AccentTint`, `SDF_BandScale`, `SDF_BandStrength` | `MI_Toon_SDF_Wall` |
| `M_SDF_GildedStucco` | Terrace / plaster walls | `BaseTint`, `AccentTint`, `SDF_BandScale` | `MI_Toon_SDF_Floor` |
| `M_Master_SDF_Toon` | Portfolio SDF + compositing textures | `BaseTint`, `AccentTint`, texture slots (Albedo/Normal/ORM) | `MI_SDF_*` family |
| `M_SDF_ReliefPanel` | Deep baroque relief bands | `BaseTint`, `AccentTint`, `DeepTint`, `BandScale`, `ReliefDepth`, `NoiseScale` | `MI_SDF_ReliefPanel_Baroque` |
| `M_SDF_HybridStone` | Worn stone + crack wear | `StoneTint`, `MossTint`, `GoldEdge`, `WearAmount`, `StoneTiling` | `MI_SDF_HybridStone_Worn` |

**Naming convention:** `*Tint` (color), `*Scale` / `*Tiling` (frequency), `*Strength` / `*Amount` / `*Depth` (intensity). Prefer these over one-off names when adding SDF instances.

## Python scripts (run order)

```text
python Content/Python/repair_crash_assets.py
python Content/Python/portfolio_texture_catalog.py          # disk audit, no editor
python Content/Python/integrate_compositing_textures.py
python Content/Python/run_phase_a_safe.py
```

**Starter pipeline (editor or headless):**

```text
py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_master_universal.py"                 # or --force to refresh groups
py Content/Python/apply_starter_instances.py              # create/update 13 MI_Show_*
py Content/Python/setup_trimsheet_instances.py          # create/update 4 trimsheet MIs
py Content/Python/archive_unused_instances.py             # optional: move legacy Environment MIs
py Content/Python/review_portfolio_masters.py             # masters + starter texture pass (editor)
py Content/Python/setup_template_showcase.py              # L_Template sphere row
```

Headless:

```text
set BS_STARTERS_ONLY=1
UnrealEditor-Cmd.exe BS_GodFile.uproject ^
  -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/apply_starter_instances.py" ^
  -unattended -nullrhi

py Content/Python/setup_trimsheet_instances.py          # headless, same flags
py Content/Python/review_portfolio_masters.py           # headless audit
```

Editor one-shot: `py ".../run_editor_integration.py"`

## Headless notes

- **Monolith** (optional, currently **disabled** in `BS_GodFile.uproject`): requires **GameplayStateTree** and a source rebuild of `Plugins/Monolith` for UE 5.8. Prebuilt DLLs crash at `UMonolithSettings::Get()` / `FMonolithConfigModule::StartupModule()` (null deref) — no `Plugins/Monolith/Source` in this repo. Re-enable only after rebuilding Monolith locally. Until then use **UnrealMCP :55557** or headless Python (`run_sakura_niagara_plan.py`).
- **Never run** `patch_portfolio_texture_paths.py` / `patch_portfolio_uasset_paths.py` (corrupts uassets).
- Close material tabs before batch saves to avoid Error 32 file locks.

## Audit reports (local, gitignored)

`Saved/Audit/`: `master_review.json`, `master_texture_loop.json`, `master_param_loop.json`, `master_param_loop_state.json`, `master_param_catalog_audit.json`, `compositing_integration.json`, `compositing_texture_defaults.json`, `starter_instances.json`, `dead_material_nodes.json`, `ensure_portfolio_instances.json`, `substrate_toon_conversion.json`, `storybook_outline_build.json`

## Not in git

- `/Game/Textures` compositing library (local SBS packs)
- `Content/Python/livelink_unreal.pyc` (3DRedbox client; copy from purchase)
- `Saved/`, `Intermediate/`, audit JSON outputs

## Loop progress

Napo loop paused (2026-06-20) → see `Docs/MATERIAL_SPECIALISTS_PLAN.md`.

### Tick #1 (2026-06-19) — universal master organization + starter curation

| Task | Status |
|------|--------|
| Parameter groups on `M_Master_Toon_Universal` (Nikki, FlowerShadow, Celestial, Magical, …) | Done — `GROUP_*` in `setup_master_universal.py` |
| Texture catalog audit (`portfolio_texture_catalog.py`) | Done — sparkle/sakura/magical defaults; Perlin demoted to fallback |
| Curate 10 starters (`starter_instances.py`) | Done — `MI_Show_*` under `Instances/Showcase` |
| Starters-only apply script | Done — `apply_starter_instances.py`, `BS_STARTERS_ONLY=1` / `--starters-only` |
| Archive helper for legacy MIs | Done — `archive_unused_instances.py` (no delete) |

Legacy `MI_Universal_*` (141+) under `Instances/Environment` are **not deleted**. Use `archive_unused_instances.py` to move them to `Instances/_Archive` when ready.

### Tick #2 (2026-06-19) — docs + headless apply

| Task | Status |
|------|--------|
| Deduplicate `MATERIAL_INTEGRATION.md` starter table | Done — single table aligned with `starter_instances.py` |
| Headless `apply_starter_instances.py` (UE 5.8, `-nullrhi`, Monolith off) | **OK** — 10/10 `created_or_updated`; audit `Saved/Audit/starter_instances.json` @ 2026-06-20T01:12:30Z; log `Saved/Logs/apply_starters_tick2.log` |
| `review_portfolio_masters.py` | Skipped — requires Unreal `unreal` module (not a disk-only script) |

If a future headless run fails with **Error 32** (file lock), close the editor and any open material tabs, then re-run; otherwise run `apply_starter_instances.py` from an open editor session.

### Tick #3 (2026-06-20) — master force rebuild

| Task | Status |
|------|--------|
| Headless `setup_master_universal.py` with `BS_MASTER_FORCE=1` | **OK** — rebuilt in-place; 656/656 wires; FlowerShadow group + param `desc` tooltips baked |
| Headless `--force` via argv | Fixed — UE-Cmd does not pass `-force` to `sys.argv`; use `BS_MASTER_FORCE=1` env |

**Next tick:** editor `setup_template_showcase.py` (11-sphere row incl. NikkiHero) + viewport check on nebula/cherry blossom starters.

### Napo loop ticks #2–#16 (2026-06-20) — automated 15m cadence

| Track | Highlights |
|-------|------------|
| Starters (11) | `MI_Show_NikkiHero` added; all showcases cross-polished with Nikki/parallax params |
| Trimsheets (4) | `MI_Trimsheet_ParallaxPOM` + parallax height/normal on all presets |
| Docs | SDF top-5 table, trimsheet table, Nikki environment guide |
| Audit | `master_review.json` stays `clean: true` across ticks |

See `Docs/MATERIAL_LIBRARY_NAPO_LOOP_PLAN.md` and `Docs/Research/UE58_MaterialNotes.md` for per-tick notes.

## Master texture loop (no `/Engine/` textures)

**Hard rule:** Never assign `DefaultTexture`, `WhiteSquareTexture`, or any `/Engine/` path on master texture parameters. All defaults come from `/Game/Textures` compositing catalog via [`portfolio_texture_catalog.py`](Content/Python/portfolio_texture_catalog.py).

| Mechanism | Purpose |
|-----------|---------|
| `material_lib.BANNED_TEXTURE_PATHS` + `sanitize_candidates()` | Block `/Engine/` at assign time |
| `apply_master_defaults(..., force=True)` | Force rewire from compositing catalog |
| `scan_master_texture_violations()` | Audit banned / unwired / wrong-role ORM |
| `run_master_material_loop_tick.py` | One idempotent loop pass (60s cadence) |

**Run (headless, editor closed):**

```text
set BS_MASTER_FORCE=1
py Content/Python/run_master_material_loop_tick.py
```

**Audit:** `Saved/Audit/master_texture_loop.json` — success when `summary.clean` is true (0 banned, 0 unwired).

### Texture loop tick #0 (2026-06-20)

| Master | Result |
|--------|--------|
| `M_Master_Toon_Universal` | 12/12 slots on `/Game/Textures` + alphas; 0 banned; compile OK |
| `M_Master_SDF_Toon` | 3/3 on compositing + SDF marble; 0 banned |
| `M_Master_Toon_Unified` | 3/3 on compositing + SDF marble; 0 banned |

ORM slots use SDF marble packs (not Perlin height noise). Normal slots use compositing `Perlin_10` (no `DefaultNormal`).

## Master parameter loop (group / desc / sort)

**Scope:** Non-texture metadata on `M_Master_Toon_Universal` (scalar, vector, static switch). Texture wiring stays in the texture loop. SDF masters (`M_SDF_*`, `M_Master_SDF_Toon`, `M_Master_Toon_Unified`) get a Palette + Toon subset audit only.

| Mechanism | Purpose |
|-----------|---------|
| `master_param_catalog.PARAM_REGISTRY` | Canonical param → `{group, desc, kind}` for universal master |
| `master_param_catalog.ALL_GROUPS` | Professional MI editor panel sort order |
| `scan_master_param_violations()` | Audit ungrouped, wrong_group, missing_desc, unknown, placeholders |
| `apply_master_param_organization()` | Fix group, tooltip desc, sort_priority (metadata only) |
| `is_master_organized()` | Success: 0 ungrouped, 0 wrong_group, missing_desc under threshold |
| `run_master_param_loop_tick.py` | One idempotent loop pass; rotates 10 focus slices |

**Run (editor open):**

```text
py Content/Python/run_master_param_loop_tick.py
```

**Run (headless, editor closed):**

```text
py Content/Python/run_master_param_loop_tick.py
```

(Outer launcher spawns `UnrealEditor-Cmd` when `unreal` is not importable.)

**One-shot organize + audit:**

```text
py Content/Python/master_param_catalog.py
```

**State / audit paths:**

- State: `Saved/Audit/master_param_loop_state.json` (`tick_index`, `last_focus`)
- Report: `Saved/Audit/master_param_loop.json`
- Catalog audit: `Saved/Audit/master_param_catalog_audit.json`

**Success criteria:** `summary.organized` is `true` on `M_Master_Toon_Universal` in `master_param_loop.json` (0 ungrouped, 0 wrong_group, missing_desc ≤ threshold). Log: `Saved/Logs/master_param_loop.log`.

**Focus rotation (10 ticks):** `audit_full` → `core_palette` → `layers_parallax` → `triplanar_temporal` → `nikki_character` → `celestial_shadow` → `magical_fairy` → `gilding_macro` → `world_elemental` → `cinematic_tod`.

## Master parameter loop (scalar / vector / switch organization)

**Scope:** All non-texture MI editor categories on `M_Master_Toon_Universal` — groups, tooltips, canonical naming. Textures stay on the 60s texture loop.

| Mechanism | Purpose |
|-----------|---------|
| `master_param_catalog.PARAM_REGISTRY` | Canonical group + tooltip per param |
| `scan_master_param_violations()` | Ungrouped, wrong group, missing desc |
| `apply_master_param_organization()` | In-place group/desc fixes per focus |
| `run_master_param_loop_tick.py` | Rotating 10-focus pass (180s cadence) |

**Run (headless, editor closed):**

```text
py Content/Python/run_master_param_loop_tick.py
```

**Audit:** `Saved/Audit/master_param_loop.json` — success when `summary.organized` is true (`organization_score` ≥ 0.95, 0 ungrouped, 0 wrong group).

**Focus rotation (tick % 10):** `audit_full` → `core_palette` → `layers_parallax` → `triplanar_temporal` → `nikki_character` → `celestial_shadow` → `magical_fairy` → `gilding_macro` → `world_elemental` → `cinematic_tod`.

### Param loop tick #0 (2026-06-20)

| Check | Universal master |
|-------|------------------|
| `summary.organized` | **true** |
| Ungrouped / wrong group | 0 / 0 |
| Numbered MI panels | `organize_master_groups.py` every tick (01–21 panel order) |
| Catalog | `master_param_catalog.py` — groups, sort_priority, tooltips |

**Loops running:** `AGENT_LOOP_TICK_master_texture` (60s) + `AGENT_LOOP_TICK_master_params` (180s). Close editor before headless ticks to avoid Error 32.

## Environment specialists (landscape + water)

| Master | Role | Build |
|--------|------|-------|
| `M_Master_Toon_Landscape_HeightBlend` | Toon terrain — triplanar Rock/Grass/Mud height competition + slope cliffs + snow + painted layer branch | `python Content/Python/setup_landscape_height_blend.py` |
| `M_Water_Master_Grand_v6` | **Canonical grand water** — Gerstner waves, caustics, depth/shoreline params, magical intensity | `python Content/Python/setup_master_water.py` |

**Do not use** `M_Master_Toon_Water` — deprecated duplicate. Expand grand water only.

**Water instances** (`Instances/Water/`): `MI_GrandWater_OceanDeep`, `RiverClear`, `PondStylized`, `SakuraPond`, `ShorelinePond`

**Landscape instances** (`Instances/Landscape/`): `MI_Landscape_CliffGrass`, `Meadow`, `SnowAlpine`, `SakuraGarden`, `ForestFloor`, `CoastalCliff`

**Sakura note:** `MI_Sakura_Water` on Universal is a stylized glass fallback. For the koi pond plane use **`MI_GrandWater_SakuraPond`** (grand water). See `Docs/MATERIAL_SPECIALISTS_PLAN.md`.

**Specialist run order** (headless-safe — `-DisablePlugins=Monolith` on all Cmd launches):

```text
python Content/Python/audit_grand_water.py              # optional pre-edit audit
python Content/Python/setup_material_functions.py --force
python Content/Python/expand_grand_water.py
python Content/Python/organize_water_groups.py
python Content/Python/setup_landscape_height_blend.py   # sets BS_MASTER_FORCE=1 headless
python Content/Python/organize_landscape_groups.py
python Content/Python/setup_landscape_layers.py         # LayerInfo Rock/Grass/Mud/Path
python Content/Python/setup_master_water.py
python Content/Python/setup_sakura_scene.py             # pond MI assign
python Content/Python/review_portfolio_masters.py       # universal audit only
```

**Audits:** `Saved/Audit/grand_water_graph_audit.json` · `grand_water_expand.json` · `landscape_height_blend.json` · `landscape_layers.json`

**Template validation:** `py Content/Python/setup_template_showcase.py` — adds `MI_Landscape_Meadow` ground slab + `MI_GrandWater_ShorelinePond` plane in `L_Template`.

## Japanese ornament textures + themed instances

**Source pack:** `/Game/Textures/70_Japanese_Ornament_Alphas_vfxMed` (52 `JRO_JP_Ornament*` alpha masks).

Wired into `M_Master_Toon_Universal` `MotifMask` / `FairyGlyphMask` defaults via `portfolio_texture_catalog.py` (`JAPANESE_ORNAMENT`).

**Theme instances** — `py Content/Python/apply_theme_instances.py` (all) or `py Content/Python/apply_zen_instances.py` (zen only)

| Folder | Instances |
|--------|-----------|
| `Instances/Environment/Baroque/` | `MI_Baroque_GildedFiligree`, `MI_Baroque_CathedralSurreal`, `MI_Baroque_EscherOrnament`, `MI_Baroque_FiligreeDream` |
| `Instances/Environment/Zen/` | `MI_Zen_MossGarden`, `MI_Zen_InkWash`, `MI_Zen_BambooMist`, `MI_Zen_Karesansui`, `MI_Zen_ToriiVermillion`, `MI_Zen_SakuraDrift`, `MI_Zen_LanternWarm`, `MI_Zen_TeaHouseCedar`, `MI_Zen_PondStill`, `MI_Zen_ShojiPaper`, `MI_Zen_TempleStep`, `MI_Zen_MoonlitGarden` |

**Audit:** `Saved/Audit/theme_instances.json` (full) · `Saved/Audit/zen_instances.json` (zen)

## Portfolio Materials AAA (2026-06-23)

Grand sign-off: `Saved/Audit/portfolio_materials_aaa.json` (`all_ok: true` target).

### Orchestration

| Script | Role |
|--------|------|
| `run_material_aaa_pipeline.py` | One-shot full rebuild + sync + audits |
| `run_material_aaa_loop_tick.py` | Rotating 10-task loop (15m `AGENT_LOOP_WAKE_material_aaa`) |
| `sync_all_material_instances.py` | Re-apply all MI families after master rebuilds |

### Instance families (sync order)

| Family | Count | Script | Notes |
|--------|-------|--------|-------|
| `MI_Show_*` | 11 | `apply_starter_instances.py` | Showcase starters |
| `MI_Sakura_*` | 10 | `setup_sakura_instances.py` | Blossom / path |
| `MI_Zen_*` | 15 | `apply_zen_instances.py` | JRO `MotifMask` / `FairyGlyphMask` / `SparkleMask` |
| ZenTrim trimsheet | 9 | `setup_trimsheet_instances.py` | Layer A=`Base4K`, Layer B=variation — see below |
| `MI_Landscape_*` | 7 | `setup_landscape_height_blend.py` | CC0 layers via `portfolio_landscape_textures.py` |
| `MI_GrandWater_*` | 5 | `setup_master_water.py` | Grand v6 |
| Baroque theme | 4 | `apply_theme_instances.py` | Ornament masks |

### ZenTrim trimsheet instances (Universal master — instances only)

Textures: `/Game/Textures/ZenTrim_<Variant>_*` · Catalog: `zen_trim_textures.py`

| Instance | Layer A | Layer B | LayerBlend |
|----------|---------|---------|------------|
| `MI_Trimsheet_VariationCracks` | Base4K | CrackedToHell | 0.42 |
| `MI_Trimsheet_ParallaxPOM` | Base4K | CrackedToHell | 0.35 |
| `MI_Universal_TrimsheetBlend` | Base4K | ColourShift | 0.25 |
| `MI_Trimsheet_HeavyWear` | Base4K | CrackedToHell | 0.68 |
| `MI_ZenTrim_Wet` | Base4K | Wet | 0.55 |
| `MI_ZenTrim_FlowersMid` | Base4K | FlowersMid | 0.38 |
| `MI_ZenTrim_FlowersLittle` | Base4K | FlowersLIttleBit | 0.22 |
| `MI_ZenTrim_FlowersLots` | Base4K | FlowersLOTS | 0.52 |
| `MI_ZenTrim_ColourShift` | Base4K | ColourShift | 0.48 |

Folder: `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/`

### AAA audits

| Report | Script |
|--------|--------|
| `portfolio_materials_aaa.json` | Merged sign-off |
| `zen_trimsheet_aaa_audit.json` | `audit_zen_trimsheet.py` |
| `landscape_aaa_audit.json` | `audit_landscape_aaa.py` |
| `grand_water_aaa_audit.json` | `audit_grand_water_aaa.py` |
| `master_review.json` | `review_portfolio_masters.py` |
| `landscape_cc0_textures.json` | `portfolio_landscape_textures.py` |
| `zen_trim_textures.json` | `zen_trim_textures.py` |

### Headless run (close editor first)

```text
set BS_MASTER_FORCE=1
python Content/Python/run_material_aaa_pipeline.py
python Content/Python/run_material_aaa_loop_tick.py
```

All Cmd launches: `-DisablePlugins=Monolith` `-nullrhi`
