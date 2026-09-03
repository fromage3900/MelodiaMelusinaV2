# Stage 22 Finalization Report

Date: 2026-06-27

## Scope

Stage 22 is the curated Material Instance showcase library for the three core masters:

- `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`
- `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend`
- `/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6`

This pass intentionally avoids broad SDF reorganization and legacy `_PROJECT` deletion. Earlier material audit docs mark `_PROJECT` as retained source-library content, while the final-pass note only authorizes targeted cleanup of accidental imported/generated material bloat.

## Core Master Compile Evidence

All three core masters compile according to Monolith `get_compilation_stats`:

| Master | Compiled | Blend | VS Instr | PS Instr | Samplers | Expressions |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `M_Master_Toon_Universal` | true | Opaque | 174 | 1099 | 14 | 701 |
| `M_Master_Toon_Landscape_HeightBlend` | true | Opaque | 153 | 461 | 9 | 280 |
| `M_Water_Master_Grand_v6` | true | Translucent | 377 | 546 | 3 | 67 |

`validate_material` still reports structural warnings on Universal and Landscape (mostly island/unused parameters and duplicate static switches inherited from the large authoring graphs), but no compile failure on the three core masters.

## Showcase Instances

Created/tuned under `/Game/EnvSandbox/Materials/Instances/Showcase2026_06_27/`:

| Family | Instance | Purpose |
| --- | --- | --- |
| Universal | `MI_Showcase2_Universal_Baseline` | zero-override baseline |
| Universal | `MI_Showcase2_Universal_DisplacementParallax` | displacement plus parallax self-shadow showcase |
| Universal | `MI_Showcase2_Universal_IttoSpiral` | Itto spiral/ink/wear showcase with stronger readable tint/ramp overrides |
| Universal | `MI_Showcase2_Universal_MadokaPulse` | Madoka audio-reactive pulse showcase |
| Universal | `MI_Showcase2_Universal_SharpToonBands` | sharp palette ramp/toon-band showcase |
| Landscape | `MI_Showcase2_Landscape_Baseline` | baseline ground blend with stock texture overrides for inherited `_PROJECT` slots |
| Landscape | `MI_Showcase2_Landscape_RealNormals` | per-layer normal-strength showcase |
| Landscape | `MI_Showcase2_Landscape_MacroVariation` | macro variation and height-compete showcase |
| Water | `MI_Showcase2_Water_CalmPond` | low Gerstner, calm pond read |
| Water | `MI_Showcase2_Water_DeepShallow` | deep/shallow color and opacity showcase |
| Water | `MI_Showcase2_Water_OceanSwell` | stronger Gerstner swell and caustics showcase |

## Tuned During Finalization

- `MI_Showcase2_Universal_MadokaPulse`: enabled `MadokaBlendAmount`, `MadokaGlowAmount`, `MadokaAudioReactiveAmount`, and `RhythmPulse`.
- `MI_Showcase2_Universal_IttoSpiral`: enabled `IttoBlendAmount`, `IttoSpiralIntensity`, `IttoInkStrength`, `IttoCrackDepth`, `IttoWearAmount`, `IttoPatternScale`, and readable Itto/palette color overrides.
- `MI_Showcase2_Universal_SharpToonBands`: enabled `PaletteRampStrength`, increased `RampSharpness`, and set explicit ramp colors.
- `MI_Showcase2_Universal_DisplacementParallax`: increased `DisplacementStrength`, enabled `ParallaxStrength`, and set a warmer base tint.
- `MI_Showcase2_Landscape_RealNormals`: added explicit `RockNormalStrength`, `GrassNormalStrength`, and `MudNormalStrength`.
- `MI_Showcase2_Landscape_MacroVariation`: increased `MacroStrength`, `HeightBlendStrength`, and `SlopeSharpness`.
- All three Landscape showcase instances override inherited `Grass_Albedo` and `Mud_Height` away from `_PROJECT` paths.

## Preview Evidence

All 11 showcase instances rendered through Monolith `render_preview` to:

`Saved/Monolith/previews/MI_Showcase2_*_256.png`

Pixel-stat smoke test showed no blank/all-black/all-white previews. Final sampled stats:

| Preview | Mean RGB | Lum Std |
| --- | --- | ---: |
| `MI_Showcase2_Landscape_Baseline_256.png` | `39.5,40,39.7` | 40.6 |
| `MI_Showcase2_Landscape_MacroVariation_256.png` | `38.8,39.4,39.4` | 40.7 |
| `MI_Showcase2_Landscape_RealNormals_256.png` | `39.5,40,39.7` | 40.6 |
| `MI_Showcase2_Universal_Baseline_256.png` | `41.2,96.8,68` | 55.8 |
| `MI_Showcase2_Universal_DisplacementParallax_256.png` | `60.8,106.6,82.7` | 67.9 |
| `MI_Showcase2_Universal_IttoSpiral_256.png` | `78,101.9,94` | 64.3 |
| `MI_Showcase2_Universal_MadokaPulse_256.png` | `74.5,76.4,80.9` | 65.8 |
| `MI_Showcase2_Universal_SharpToonBands_256.png` | `98.5,107.4,113.7` | 72 |
| `MI_Showcase2_Water_CalmPond_256.png` | `48.4,61.1,82` | 43.5 |
| `MI_Showcase2_Water_DeepShallow_256.png` | `48.6,92.1,102.6` | 54.6 |
| `MI_Showcase2_Water_OceanSwell_256.png` | `50.5,102.9,114.4` | 60.3 |

## Cleanup Performed

Removed dry-run-confirmed untracked imported/generated paths outside the retained `_PROJECT` library, including:

- accidental `Content/Art/Meshes`
- accidental imported pack folders under `Content/Assets`, `Content/Characters`, `Content/Core`, `Content/Environment`, `Content/Genshin_Shader_v1_1`
- stray root `Content/MaterialFunctions`, `Content/MaterialLayerBlends`, and `Content/Materials/MI_ToonLayer.uasset`
- `Plugins/Monolith_OLD_BROKEN`
- generated loop pid/log/stop files under `deploy`

One untracked imported texture remains locked by the editor:

- `Content/Art/Textures/Base/T_Grass_D.uasset`

Delete it after closing Unreal Editor or releasing the asset handle.

## Remaining Non-Stage-22 Work

- Stage 19 SDF reorganization is still incomplete. There are many dirty/untracked SDF assets and dirty SDF packages in the editor.
- Some SDF materials showed compile failures in the active log before this pass; this is outside the curated core-master stage-22 scope.
- The full worktree is not clean. Stage-22 assets are ready to stage/commit separately, but unrelated edits from earlier material/PCG/deploy work should be reviewed before any broad commit.
- `validate_material` warnings on Universal/Landscape should be treated as future graph-hygiene work, not stage-22 blockers, because both masters compile and the showcase instances render.
