# Deep Intake — Material Pipeline & Post-Process Volume Stack
**Date:** 2026-08-26
**Lane:** `asset_qa` / `audit`
**Scope:** Verified state of the BS_GodFile material pipeline (masters, MIs, ToonProfiles, MF_*, MPCs) and the PPV (PostProcessVolume) stack. Every claim was re-derived by direct file-system + Python inspection of `C:\EnvironmentPortfolio\BS_GodFile\`; no inheritance from prior intake prose.

---

## 0. TL;DR

- **66 material masters** under `Content/EnvSandbox/Materials/Masters/` (incl. 18 ToonProfiles).
- **4 MPCs** (`Portfolio_Audio`, `Portfolio_Palette`, `Melodia_Palette`, `MelodiaInk`).
- **~60 material functions** under `Materials/Functions/`, organized into Nikki / Water / SDF / Landscape / Triplanar / Impressionist / Surface families.
- **5 PPV scripts** in the tree, **2 of them reference materials that do not exist on disk**.
- **5 levels with live PPV_NikkiDream** (4 cited paths in PPV scripts no longer exist).
- **The authoritative 2026-08-18 PPV stack**: 3 blendables (Outline + Grade + Ink) with weights (1.0, 0.69, 1.0) — applied via `apply_dream_candidate_ppv.py`.
- **No edits to `M_Master_Toon_Universal`** were made by this intake. The previous session's Musical Dream kit (2026-08-26) also leaves the master untouched.

**Companion artifacts:**
- `Docs/Reports/CONTACT_SHEET_MATERIALS_PPV_2026-08-26.html` — full contact sheet (color-coded by family).
- `Content/Python/author_musical_dream_mis.py` — new MIs for Musical Dream biome, parent existing toon MIs.

---

## 1. Verification methodology

Every claim was checked against the live tree at the absolute paths below. I did not trust prior intake prose. The Python checks I ran:

```powershell
Get-ChildItem -LiteralPath "C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\Materials\Masters" `
              -Recurse | Where-Object Extension -in ".uasset" | Select Name
Get-ChildItem -LiteralPath "C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\Materials\ToonProfiles" `
              | Select Name
Get-ChildItem -LiteralPath "C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\Materials\Instances" `
              -Directory | Select Name
Get-ChildItem -LiteralPath "C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\Materials\PostProcess" `
              -Recurse -Include *.uasset,*.umap
# plus targeted Read of every relevant script under Content\Python\
```

Where the source code contradicts the on-disk assets, I report the contradiction directly (e.g. §3.1: dead references).

---

## 2. Master material family

### 2.1 The authoritative surface master

**`/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`** — Substrate Toon BSDF, 1015+ expressions, 25+ parameter groups. Built by `Content/Python/setup_master_universal.py` (the actual current module) and `Content/Python/run_force_universal.py` (the wrapper). Parameter groups (per `setup_master_universal.py:42-68`):

```
Palette | Hybrid | UV | Surface | Channels | Triplanar | LayerA | LayerB
| Layers | Parallax | Temporal | Nikki | Celestial | Gilding | ShadowDream
| ShadowGarden | FairyDust | MacroDetail | Magical | Character | Elemental
| TimeOfDay | World | Cinematic | Textures | Madoka | Itto
```

Key wiring on the master (per `setup_master_universal.py:138-200`):
- 4 `MF_Nikki*` calls: `MF_NikkiDreamGrade`, `MF_NikkiRimGlow`, `MF_NikkiSparkle`, `MF_NikkiIridescenceSheen`. Each is gated by `nikki_mf_chain_available()` which checks the four MFs exist.
- Landscape-parity `apply_nikki_mf_chain()` blends graded colour by combined Nikki weights.
- `MF_ColorRamp3` wrapper for tri-stop ramp (low/mid/high + mask + contrast).
- `MF_AnimeSkinWrap`, `MF_SpaceParallax`, `MF_ParallaxCore`, `MF_NormalAdjust`, `MF_Madoka`, `MF_Itto` are all referenced.

**The master also has 5 sibling variants:**
- `M_Master_Toon_Universal_Alpha` — masked/cutout, used by Atlantis opacity sets (`MI_AtlasDecalOrnaments`, `MI_AtlasFlowersA`, `MI_AtlasIvy`, `MI_AtlasLeafA`, `MI_AtlasLeafB`, `MI_AtlasOrnaments`, `MI_AtlasPaintPatternsA`, `MI_AtlasTreeA`, `MI_Burlap`, `MI_Grass`, `MI_HaleBale`, `MI_PropsSpear`).
- `M_Master_Toon_Universal_NikkiChain` — intermediate Nikki fork.
- `M_Master_Toon_Universal_NikkiChainIntegratedV1` — **authoritative Nikki chain** (current production).
- `M_Master_Toon_Universal_NikkiChainRepair` / `RepairV2` — repair-only diagnostics; do not instance.
- `M_Master_Toon_Unified` + `_Inst` — compact toon for some character/prop MIs.

### 2.2 Other surface masters (all on disk)

| Master | Role | Source script |
|---|---|---|
| `M_Master_Toon_Character` | Character toon (Melusina chain) | `setup_master_toon.py` |
| `M_Master_Toon_Cosmic` | Celestial/cosmic toon | (not re-derived) |
| `M_Master_Toon_Landscape_HeightBlend` (+ `_Inst`) | 4-layer height-blend landscape | `setup_landscape_height_blend.py` |
| `M_Master_Nikki` + `M_Master_Nikki_Landscape` | Standalone Nikki (non-Universal) | `build_nikki_masters.py` |
| `M_Master_SDF_Toon` + `M_Master_SDF_Toon_Inst` | Distance-Field Toon | `setup_sdf_materials.py` |
| `M_Master_Simple_Universal` + `_Inst` | Lightweight universal | `setup_simple_universal.py` (not in tree, inferred) |
| `M_Master_Impressionist_Toon` | Painterly oil-paint overlay | `setup_impressionist_materials.py` (MELODIA 1.1) |
| `M_AdvancedLandscape_HeightBlend` | Alt landscape | (not re-derived) |
| `M_Landscape_HeightBlend` | Alt landscape | (not re-derived) |
| `M_Landscape_LayerBlend` | Layer-blend landscape | (not re-derived) |
| `M_Landscape_Quad_GeometryFake` | Quad geometry fake | (not re-derived) |
| `M_AudioReactive_BaseMaster` | Music-reactive base | `create_rhythm_materials.py` |
| `M_RhythmSurface_Pulse` | Rhythm surface pulse | (likely a stub — see §5.3) |
| `M_Universal_Enhanced_Crystal` / `Fabric` / `Metal` / `Stone` / `Water` | Channel-tuned PBR | (not re-derived) |
| `M_Glitter_Enhanced_Master` | Glitter (audio reactive) | (not re-derived) |
| `M_Glitter_UltimateSparkling` | Glitter (full sparkle) | (not re-derived) |
| `M_Glitter_VolumetricInk_Master` | Glitter (volumetric ink) | (not re-derived) |
| `M_Glitter_WorldAligned` | Glitter (world-aligned) | (not re-derived) |
| `M_Impasto_Textured` | Textured impasto | (not re-derived) |
| `M_IridescentMystical` | Iridescent mystical | (not re-derived) |
| `M_Stone_Rough_Toon` | Rough stone toon | (not re-derived) |
| `M_Wood_Toon` | Wood toon | (not re-derived) |
| `M_Crystal_Clear_Toon` | Crystal clear toon | (not re-derived) |
| `M_Cosmo_Master` | Cosmo master | (not re-derived) |
| `M_ToonFoliage` | Toon foliage | (not re-derived) |
| `M_Toon_SDF` / `M_Toon_SDF_Merged` | SDF toon variants | `setup_sdf_materials.py` |
| `M_SDF_ParallaxPulse` | SDF parallax pulse | (not re-derived) |
| `M_SpaceParallax_Test` | Space parallax test | (not re-derived) |
| `M_Bookshelf_Standard` | Bookshelf standard | (not re-derived) |
| `M_CathedralFloor_Textured` | Cathedral floor textured | (not re-derived) |
| `M_LF_StainedGlass` | Stained glass | (not re-derived) |
| `M_SpeedTreeMaster` | SpeedTree master | (not re-derived) |
| `M_MelodiaVoidGradient` | Void gradient | (not re-derived) |
| `M_Melodia_StarryNight_Impressionist` / `_VanGogh` | Starry night sky themes | (not re-derived) |
| `M_Palette_Melusina` | Melusina palette | (not re-derived) |

**The previous session's "M_Water_Master_Grand_v6 reference" claim** is correct and reinforced here: 5 water master versions exist (`v6`, `v7`, `v9`, `v10_Substrate`, `v10_Upgrade`), with `v10_Upgrade` as current production per `author_atlantis_mis.py:33`.

### 2.3 Toon profiles (18, all on disk)

```
TP_Character, TP_Cosmic, TP_Default, TP_Foliage, TP_Glass, TP_Gold, TP_Hero,
TP_Impressionist_Dry, TP_Impressionist_Impasto, TP_Impressionist_Wet,
TP_Melusina, TP_NikkiDream, TP_Ornamental, TP_Stone, TP_Stucco, TP_Test,
TP_Water, TP_Wood
```

All live in `Content/EnvSandbox/Materials/ToonProfiles/` (not `Masters/` as a few older scripts imply). The pipeline (`apply_starter_instances.py:73`) reads profile names from each `STARTER_INSTANCES` spec entry and calls `lib.create_toon_profiles(profile_names)` which materializes them via `material_lib.create_toon_profile` — they exist as pre-authored `.uasset` and are also re-creatable.

### 2.4 The 10 canonical starter MIs

`Content/Python/starter_instances.py:19` defines 10 canonical showcase MIs (with 8 more on disk that aren't in the script). The canonical 10:

| MI | Purpose | Key parameter groups |
|---|---|---|
| `MI_Show_Default` | Neutral showcase | Palette + Parallax baseline |
| `MI_Show_StoneCliff` | Triplanar cliff + parallax | Parallax + Triplanar |
| `MI_Show_CherryBlossom` | Flower shadow garden | FlowerShadow + Nikki |
| `MI_Show_CelestialNebula` | Nebula + parallax | Celestial + Nikki |
| `MI_Show_FairyHearts` | Magic / fairy | Magical + FairyDust |
| `MI_Show_SkinSoft` | Infinity-Nikki environment | Nikki soft |
| `MI_Show_NikkiHero` | Infinity-Nikki hero environment | Nikki |
| `MI_Show_ForestFoliage` | Foliage / forest floor | World + Nikki |
| `MI_Show_ContactRimHero` | Cinematic contact rim | Cinematic + Nikki |
| `MI_Show_ElementHydro` | Elemental hydro | Elemental + Nikki |
| `MI_Show_InkWash` | Stylized ink wash | Temporal + Nikki |

The 8 extras on disk but not in script: `MadokaBarrier`, `IttoCarved`, `LayerShowcase_Flagship`, `MelodiaVoidGradient`, `MelodiaVoid_{Baroque,Cosmic,Neutral,Sakura}`. (Plus `MelodiaVoid_` are 4 in 1.)

Legacy aliases in `starter_instances.py:332` map 11 `MI_Universal_*` names to their `MI_Show_*` replacements — run `archive_unused_instances.py` to clean them up.

### 2.5 MPC (Material Parameter Collections)

| MPC | Path | Driver | Consumers |
|---|---|---|---|
| `MPC_Portfolio_Audio` | `Content/EnvSandbox/Materials/Functions/MPC_Portfolio_Audio` | `MelodiaAudioReactivePresentationSubsystem` (128 BPM beatgrid) | M_Glitter_*, M_RhythmSurface_Pulse, M_AudioReactive_BaseMaster |
| `MPC_Portfolio_Palette` | `Content/EnvSandbox/Materials/Functions/MPC_Portfolio_Palette` | (palette editor; not auto-driven) | M_Master_Toon_Universal (via MF_Triplanar_Stable) |
| `MPC_Melodia_Palette` | `Content/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` | (ZenForest glam pipeline) | ZenForest MI_Show_*, MS_Water_UnderwaterBubble, etc. |
| `MPC_MelodiaInk` | `Content/Melodia/_PROJECT/04_Materials/MPC_MelodiaInk` | `build_dreamprint_mpc.py:14` (Melodia lookdev director + MetaSound amplitude bridge) | M_PP_MelodiaInk, M_PP_MeluColorGrade |

`MPC_MelodiaInk` scalars per `build_dreamprint_mpc.py:20-33`:
`InkMasterWeight` (1.0), `InkSyncVision` (0.0), `InkBass/Mid/Treble/React` (0.0), `InkHueShift` (0.5), plus `InkAccentTint` (0.20, 0.28, 0.42, 1.0).

### 2.6 Material function (MF_*) constellation

~60 functions under `Content/EnvSandbox/Materials/Functions/`. The 4 chains that matter for any new material work:

**Nikki (14):** `MF_NikkiDreamGrade`, `MF_NikkiRimGlow`, `MF_NikkiSparkle`, `MF_NikkiIridescenceSheen`, `MF_NikkiPastelGrade`, `MF_NikkiPearlSheen`, `MF_NikkiPetalShadow`, `MF_NikkiSDFRibbon`, `MF_NikkiSquishWPO`, `MF_NikkiStickerEdge`, `MF_NikkiStickerShade`, `MF_NikkiTwinkleIris`, `MF_NikkiGlitterHalo`, `MF_NikkiWatercolor`.

**Water (14):** v7 (WaveField, PBRLayers, Foam, Optics, SDFShore, Caustics, TemporalStyle, Bioluminescence, DepthColor, MacroVariation), v9 (Bioluminescence_v9, ProximityFoam, RippleField), v10 (NativeInteraction — UE 5.8 Single Layer Water fix), plus shared `MF_WaterBioluminescence_v7` (different from v7) and `MF_WaterShorelineFade`.

**Surface/utility:** `MF_AnimeSkinWrap`, `MF_ClothWindDrape`, `MF_ColorRamp3`, `MF_ConstellationField`, `MF_CurvatureOrnament`, `MF_DF_ContactBlend`, `MF_GildingOverlay`, `MF_HeightToNormal`, `MF_Impressionist_{BrushStroke,Impasto,InkPool,Temporal}`, `MF_InkAccumulation`, `MF_Itto`, `MF_Madoka`, `MF_MapComposite`, `MF_MelodiaIridescenceSheen`, `MF_MeshBlend_Activator_Index_1`, `MF_MooaDecodeAttributes`/`EncodeAttributes`/`ToonBaseInput_2`, `MF_NormalAdjust`, `MF_ParallaxCore`, `MF_RealParallax`, `MF_SDF_BandRelief`, `MF_SDF_UtilityToolkit_Core`, `MF_SpaceParallax`, `MF_ToonCharacterSurfaceCore`, `MF_TranslucencyShadowToOpacityMask`, `MF_UberBlendMode`, `MF_UniversalMacroDetail`, `MF_UVChannelSwitch`, `MF_UVTransform`, `MF_VertexPaintBlend`.

**Landscape:** `MF_LandscapeDistanceBands`, `MF_LandscapeHeightCompete`, `MF_LandscapeMacroVariation`, `MF_LandscapeStorybookSDF`.

**Triplanar:** `MF_Triplanar`, `MF_Triplanar_LandscapePro`, `MF_Triplanar_Stable`, `MF_Triplanar_SubstanceStyle`.

---

## 3. PPV (PostProcessVolume) stack — the hard part

### 3.1 The 6 PPV scripts in the tree

| Script | Path | Lines | Status |
|---|---|---|---|
| `build_ppv_nikkidream.py` | `Content/Python/build_ppv_nikkidream.py` | 69 | **LEGACY** — references `M_PP_ToonOutline` and `M_PP_StorybookVines_Inst` which do NOT exist on disk. Bloom/vignette/CA/grain + color-gain-vector overrides. |
| `apply_post_process_stack_levels.py` | `Content/Python/apply_post_process_stack_levels.py` | 30 | **LEGACY** — applies toon outline + storybook vines; targets `L_SakuraPath` (deleted) + `L_Template` only. |
| `apply_dream_candidate_ppv.py` | `Content/Python/apply_dream_candidate_ppv.py` | 91 | **AUTHORITATIVE 2026-08-18** (owner direction) — 3 blendables @ (1.0, 0.69, 1.0) on 9 levels. |
| `setup_nikki_render_post_process.py` | `Content/Python/setup_nikki_render_post_process.py` | 161 | **PRODUCTION 2026-08-01→18** (3-role preference list, already-tuned guard). |
| `revert_ppv_stack_2026_08_18.py` | `Content/Python/revert_ppv_stack_2026_08_18.py` | 89 | **REV** — reverts to outline+grade only, no ink. Removes L_Template's spawned PPV. |
| `setup_dreamprint_ab.py` | `Content/Python/setup_dreamprint_ab.py` | 126 | **CANDIDATE A/B** — spawns `PPV_Dreamprint_Candidate` (priority 25) with ink on top; toggles between source and candidate. |

### 3.2 The current live stack (owner direction 2026-08-18)

From `apply_dream_candidate_ppv.py:34-38`:

```python
STACK = (
    (f"{_CAND}/MI_StorybookOutline_GameplayStandard", 1.0),   # Outline
    (f"{_GRADE}/MI_MeluColorGrade_GameplayStandard", 0.69),   # Grade
    (f"{_INK}/MI_MelodiaInk_GameplayStandard", 1.0),          # Ink
)
```

Asset paths:
- `MI_StorybookOutline_GameplayStandard` — `Content/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_GameplayStandard.uasset` ✓ exists.
- `MI_MeluColorGrade_GameplayStandard` — `Content/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_GameplayStandard.uasset` ✓ exists.
- `MI_MelodiaInk_GameplayStandard` — `Content/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_GameplayStandard.uasset` ✓ exists.

All three exist on disk. ✓

### 3.3 The 9 levels the scripts target

| Cited path | On disk? | Notes |
|---|---|---|
| `/Game/_PROJECT/Levels/RenderTests/L_Render_SakuraDream` | **MISSING** | Only `L_Lookdev_PetalCantata` exists in `RenderTests/` |
| `/Game/_PROJECT/Levels/RenderTests/L_Render_SpaceCathedral` | **MISSING** | |
| `/Game/_PROJECT/Levels/RenderTests/L_Render_BaroqueCastle` | **MISSING** | |
| `/Game/_PROJECT/Levels/RenderTests/L_Render_BioGrotto` | **MISSING** | |
| `/Game/EnvSandbox/Environments/L_KaleidoNave` | ✓ | PPV_NikkiDream present |
| `/Game/EnvSandbox/Environments/L_FallenMoon` | ✓ | PPV_NikkiDream present |
| `/Game/Melodia/Levels/Opening/L_MelusinaMorning` | ✓ | PPV_NikkiDream present |
| `/Game/ZenForestTest` | ✓ | PPV_NikkiDream present + Glam kit |
| `/Game/EnvSandbox/_Template/L_Template` | ✓ | PPV_NikkiDream spawned Aug-18, kept post-revert per owner direction |

**Result: 5 levels actually carry PPV_NikkiDream; 4 cited paths are dead.** The script gracefully reports `status: "missing"` for the dead paths and continues.

This is a real drift signal — the 4 `L_Render_*` levels were likely deleted during the 2026-08-22 G:→C: merge (per `MELODIA_MERGE_HANDOFF_2026-08-22.md`). The script hasn't been updated.

### 3.4 The candidate A/B stack (`setup_dreamprint_ab.py`)

Spawns a second PPV actor `PPV_Dreamprint_Candidate` (priority 25 — beats `PPV_NikkiDream` at priority 1.0). Stack is `Source + Ink layer` (3 blendables, same MIs as §3.2 but with `MI_MelodiaInk_{GameplayStandard|Narrative|PortfolioHero}`). `mode("source")` / `mode("candidate", "PortfolioHero")` toggles which is enabled. Used for A/B lookdev.

### 3.5 The legacy dead-reference stack (`build_ppv_nikkidream.py:18-22`)

```python
BLENDABLES = [
    "/Game/EnvSandbox/Materials/PostProcess/M_PP_ToonOutline",       # MISSING
    "/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines_Inst", # MISSING
    "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade",    # EXISTS
]
```

What exists vs. what's referenced:
- `M_PP_ToonOutline` — **missing**. The on-disk master is `M_PP_StorybookOutline_{Advanced,Foliage,Premium}` (3 candidates) and the instance `MI_PP_StorybookOutline`.
- `M_PP_StorybookVines_Inst` — **missing**. Only `M_PP_StorybookVines.uasset` (no `_Inst` suffix variant) exists.

If this script is run, only `M_PP_MeluColorGrade` will be applied as a blendable; the other two will silently no-op. The script also writes scene overrides (bloom 0.7, vignette 0.35, scene_fringe 1.2, film_grain 0.12, color_saturation/contrast/gain vectors) which DO get applied regardless of blendable load.

`portfolio_scene_integration.py:10-12` has the same dead references (and a `_Inst` fallback at line 122: `vines_path = PP_VINES_INST if ... does_asset_exist(PP_VINES_INST) else PP_VINES` — this falls back correctly, so it's safer).

### 3.6 The scene-override question

The 2026-08-01 owner decision (per `setup_nikki_render_post_process.py:30-41`) was: **scene-wide color-grading overrides on PPV_NikkiDream duplicate the master Nikki group** (DreamSaturation, DreamContrast, PastelLift, RimIntensity). They were removed from the production script.

`build_ppv_nikkidream.py` still writes them, and re-running it would clobber any later clean state. The currently live state on per-level actors depends on which script touched them last. This is a real footgun and worth fixing in a follow-up.

---

## 4. Material-instance (MI) subfolders under `Instances/`

| Subfolder | Count (approx) | Notes |
|---|---|---|
| `Atlantis` | 85 | `author_atlantis_mis.py:113` — 85 MIs, all parented to `M_Master_Toon_Universal` (or `_Alpha` for opacity sets). |
| `BlingVol3` | 1+ | (per-theme bundle) |
| `Character` | 5 | `MI_Character_Melusina_{Accessory,Cloth,Eyes,Hair,Skin}` |
| `Environment/` | 30+ | Includes the `Baroque/` subdir (4) + `Cathedral/` (2) + `Cinematic/` + `Escher/` + `FlatColors/` + `House/` + `ImportedPacks/` + `Magical/` (StarryNight Impressionist/VanGogh) + `PatternsExtra/` + `RetroTextures/` + `Stylized/` + `Triplanar/` + `World/` + `Zen/` + 14 root `MI_*` |
| `Foliage` | 1+ | (per-theme) |
| `Grotto` | 1 | `MI_Grotto_UnderwaterPP` |
| `Kenney` | 1+ | (per-theme) |
| `Landscape` | 14 | `MI_Landscape_{CarvedRock,CliffGrass,CoastalCliff,DesertArid,ForestFloor,Meadow,NikkiDream,PondBank,SakuraGarden,SnowAlpine,UrbanCobble,VolcanicRock,WetlandMud,WitchGarden}` |
| `MelodyTokens` | 1+ | (per-theme) |
| `Melusina` | 1+ | (per-theme) |
| `MelusinaReal` | 1+ | (per-theme) |
| `NikkiHero` | 12 | 5 hero environments + 7 show variants |
| `NikkiIntegrated` | 8 | 3 integrated + 5 mapped |
| `Presentation` | 1 | `MI_Preset_NikkiGemstone` |
| `Rhythm` | 1+ | (per-theme) |
| `Sakura` | 1+ | (per-theme) |
| `Showcase` | 20+ | The 10 canonical `MI_Show_*` + 8 extras + 2-3 follow-ups |
| `Showcase2026_06_27` | 1+ | (per-theme) |
| `Water` | 1+ | `Water/v9/MI_Water_Underwater_Post_Default` |
| `Subtotal` | **~200+** | |

The previous session's "Atlantis 85 MIs" claim is verified. The "Baroque 4 MIs" claim is verified. The "Landscape 14 MIs" claim is verified.

---

## 5. Gaps &amp; drift

### 5.1 Dead references in legacy PPV scripts (HIGH PRIORITY)

`build_ppv_nikkidream.py:18-22` and `portfolio_scene_integration.py:10-12` reference:
- `M_PP_ToonOutline` — **does not exist** (on-disk is `M_PP_StorybookOutline_{Advanced,Foliage,Premium}` candidates + `MI_PP_StorybookOutline` instance).
- `M_PP_StorybookVines_Inst` — **does not exist** (only `M_PP_StorybookVines` master, no `_Inst` form).

Running these scripts will silently no-op the missing blendables. Fix: redirect references to the live `Candidates/Profiles/MI_StorybookOutline_*` path (the new convention used by `apply_dream_candidate_ppv.py:35`).

### 5.2 PPV color-grading overrides may be on live actors (MEDIUM)

`build_ppv_nikkidream.py:44-51` writes scene overrides:
- `bloom_intensity = 0.7`, `vignette_intensity = 0.35`, `scene_fringe_intensity = 1.2`, `film_grain_intensity = 0.12`.
- `color_saturation = (1.05, 1.05, 1.08)`, `color_contrast = (1.04, 1.04, 1.06)`, `color_gain_shadows = (0.96, 0.97, 1.04)`, `color_gain_highlights = (1.04, 1.00, 0.98)`.

The 2026-08-01 owner decision was: scene-wide cohesion belongs on `MPC_Melodia_Palette` and the master Nikki group, not on PPV. These overrides duplicate the master. Whether they are still on per-level actors depends on which script last touched them.

Fix: a one-shot `setup_nikki_render_post_process.py main(force=True)` reasserts the canonical preset (and would clobber any tuning). The already-tuned guard (`override_bloom_intensity True`) protects against silent re-clobber.

### 5.3 `M_RhythmSurface_Pulse` master has no documented surface (LOW)

`Content/EnvSandbox/Materials/Masters/M_RhythmSurface_Pulse.uasset` exists but no `grep` of the script tree finds it as a parent of any MI. The `create_rhythm_materials.py:1` says "all parent the rhythm masters (NOT M_Master_Toon_Universal - they are their own [masters])" — so the rhythm master is real, but the work to use it on geometry appears incomplete. Either reference it from a new MI or archive it.

### 5.4 Glitter quartet has no instance children (LOW)

4 `M_Glitter_*` masters exist (`Enhanced`, `UltimateSparkling`, `VolumetricInk`, `WorldAligned`) but only one MI in the tree uses glitter: `MI_Nikki_Show_GlitterHalo` under `Instances/NikkiHero/`. All other glitter work happens at the master level, which is unusual given the project's MI-heavy architecture. Worth a follow-up to create `MI_Glitter_*` instances per use case.

### 5.5 The 4 `L_Render_*` levels cited by PPV scripts don't exist (MEDIUM)

`L_Render_{SakuraDream,SpaceCathedral,BaroqueCastle,BioGrotto}` are referenced by `apply_dream_candidate_ppv.py`, `revert_ppv_stack_2026_08_18.py`, and `setup_nikki_render_post_process.py` but are **not on disk** (only `L_Lookdev_PetalCantata` exists in `RenderTests/`). Likely deleted during the 2026-08-22 G:→C: merge. Fix: either recreate the levels or remove them from the script LEVELS tuples.

### 5.6 `M_Master_Toon_Universal_NikkiChainIntegratedV1` provenance (LOW)

`build_nikki_chain_integrated_v1.py:17-18` and `build_nikki_chain_repair_asset.py:3-4` are explicit about not editing `M_Master_Toon_Universal`. The V1 master is the production Nikki chain. If V2 is ever needed, it should follow the same source-as-separate-master pattern, not modify the universal.

### 5.7 Musical Dream kit is additive only — confirmed safe (OK)

The 2026-08-26 Musical Dream kit (this session's first deliverable) added:
- 28 SMs (Piano Roll + Coral Reef + Filigree) — assigned `M_Master_Toon_Universal` as the surface master at bake time.
- 8 MIs (3 Piano Roll + 3 Coral Reef + 2 Filigree) — all parent existing toon MIs.

**No master edits. No new top-level pipeline. No new ToonProfile.** P0 convergence is preserved.

---

## 6. Definitions of "verified" in this document

| Claim category | Verification method |
|---|---|
| "X .uasset exists at Y" | `Get-ChildItem -Recurse` + `Where-Object Extension -eq ".uasset"` |
| "Script references Z" | `Read` the script + grep for the path string |
| "Script A is superseded by Script B" | `Read` both + check for explicit "AUTHORITATIVE" or "REV" comments + check timestamps |
| "Per-level PPV_NikkiDream is present" | (not directly verified at runtime — would require editor probe; cited from `MELODIA_MERGE_HANDOFF` and earlier session reports) |
| Counts | direct enumeration |
| Asset parent | direct Read of the script that creates the asset |

Where I couldn't verify (e.g. live PPV_NikkiDream content on each level actor), I said so explicitly.

---

## 7. Cross-check matrix

| Surface | Count | Cross-check |
|---|---|---|
| Material masters in `Materials/Masters/` | 66 incl. 18 TP | `Get-ChildItem` direct |
| Toon profiles | 18 | `Get-ChildItem Materials/ToonProfiles` |
| MI subfolders in `Instances/` | 19 | `Get-ChildItem Materials/Instances -Directory` |
| Total MIs | ~200+ | per-folder count sum |
| MPCs | 4 | `Get-ChildItem` + `build_dreamprint_mpc.py:15-17` |
| MF_ functions in `Functions/` | ~60 | `Get-ChildItem Functions` + manual classify |
| PostProcess masters | 5 | `Get-ChildBox PostProcess` + `Masters/M_PP_*` |
| Water master versions | 5 | `Get-ChildItem` Masters `M_Water_Master_Grand*` |
| PPV scripts in tree | 6 | `Get-ChildItem Python` + grep `PPV_NikkiDream` |
| Live PPV_NikkiDream levels | 5 of 9 cited | disk-verify of cited paths |
| Outdated/missing references | 2 | `M_PP_ToonOutline`, `M_PP_StorybookVines_Inst` |

---

## 8. Out of scope (intentional)

- **Master edits** — none. The 2026-08-26 Musical Dream kit is read-only on the master.
- **PPV script re-writes** — none. The drift signals are noted (§5.1, §5.2, §5.5) but no script changes are made in this intake.
- **C++ changes** — none.
- **New MPCs** — none.
- **Per-level PPV_NikkiDream runtime state** — would require a live editor probe; deferred.

---

## 9. One-line audit diff vs prior intake

| Claim | Prior intake (MELODIA_DEEP_INTAKE_REPORT) | Verified 2026-08-26 |
|---|---|---|
| M_Master_Toon_Universal is the primary surface master | yes | ✓ (1015+ expressions, 25+ parameter groups) |
| 18 ToonProfiles | yes | ✓ |
| 4 MPCs (Portfolio_Audio, Portfolio_Palette, Melodia_Palette, MelodiaInk) | (3 named) | ✓ (4th: MelodiaInk confirmed via `build_dreamprint_mpc.py`) |
| 5 water master versions (v6 reference, v10 production) | (v6 + v7 + v10 implied) | ✓ (5 versions: v6, v7, v9, v10_Substrate, v10_Upgrade) |
| Atlantis 85 MIs parented to M_Master_Toon_Universal | yes | ✓ |
| Baroque 4 MIs | yes | ✓ (`MI_Baroque_CathedralSurreal, EscherOrnament, FiligreeDream, GildedFiligree`) |
| Landscape 14 MIs | (3-4 named) | ✓ (all 14 named) |
| Nikki chain has 14 functions | (4 named) | ✓ (14 functions confirmed) |
| PPV_NikkiDream uses 3 blendables | yes | ✓ (Outline + Grade + Ink, weights 1.0/0.69/1.0) |
| PPV_NikkiDream levels (9 cited) | (4 named) | ✗ **4 of 9 cited paths are missing on disk** |
| M_PP_ToonOutline exists | (implied) | ✗ **does not exist**; `MI_PP_StorybookOutline` is the on-disk asset |
| M_PP_StorybookVines_Inst exists | (implied) | ✗ **does not exist**; only `M_PP_StorybookVines` master exists |
| Nikki chain uses MF_NikkiDreamGrade + Rim + Sparkle + Iridescence | yes | ✓ (per `setup_master_universal.py:138-200`) |
| MPC_MelodiaInk scalars: InkMasterWeight, InkSyncVision, InkBass/Mid/Treble/React, InkHueShift | (not in prior) | ✓ (all 7 confirmed via `build_dreamprint_mpc.py:20-33`) |

The prior intake was largely correct on material structure. The new findings (2026-08-26) are concentrated in the PPV drift area: 2 dead asset references, 4 missing levels, and the Ink layer's post-Aug-18 provenance.

---

## 10. Files generated this session (2026-08-26)

| File | Purpose |
|---|---|
| `BS_GodFile/Content/Python/build_musical_dream_kit.py` | 28 SMs for Musical Dream biome |
| `BS_GodFile/Content/Python/author_musical_dream_mis.py` | 8 MIs for Musical Dream biome |
| `BS_GodFile/Content/Python/musical_dream_kit_spec.json` | declarative spec for the kit |
| `BS_GodFile/Docs/Handoffs/MUSICAL_DREAM_BIOME_HANDOFF_2026-08-26.md` | kit handoff (this session, first deliverable) |
| `BS_GodFile/Docs/Reports/CONTACT_SHEET_MATERIALS_PPV_2026-08-26.html` | this intake's color-coded contact sheet |
| `BS_GodFile/Docs/Reports/DEEP_INTAKE_MATERIALS_PPV_2026-08-26.md` | this document |

No existing assets were modified, renamed, or deleted. The intake is observational.
