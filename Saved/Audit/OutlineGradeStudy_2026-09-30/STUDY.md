# Outline + Grade Study — 2026-09-30 (read-only pass, 17:52–18:22 ET)

Evidence files (same folder): `ppv_binary_reads*.json` (PPV actor packages parsed from disk; the parser was checked against the live Morning PPV), `material_params.json` (Monolith get_instance_parameters / get_material_parameters / compile stats), `outline_frozen_custom.hlsl` (the full V7 outline HLSL), `graph_M_PP_StorybookOutline_Frozen.json`, `*_nodes.txt`.

## 1. Outline systems inventory

| System | Asset(s) | Inputs | Where applied | State |
|---|---|---|---|---|
| PP ink V7 (live) | `M_PP_StorybookOutline_Frozen` → `MI_StorybookOutline_Frozen` (/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen) | SceneDepth (5-tap centre + 16 radial taps), WorldNormal, CustomStencil (raw), ShadingModelID, SubsurfaceColor (foliage detection), SceneColor via MF_PostProcessBlend, MPC_PPBlending | Morning PPV_NikkiDream, slot 0, w 1.0 | BL = **AfterTonemapping**, priority 0, 72 expressions, ~329 PS instructions |
| PP ink Premium candidate | `M_PP_StorybookOutline_Premium_Candidate` → `MI_StorybookOutline_Premium_Hero_Dream` | same as above | SeaAbove PPV_NikkiDream (the **PPV is disabled**, bEnabled=false) | MI values are slider junk: HalftoneAmount 277, MultiplyDarken −25, FoliageNormalInk −19.6, DayNightFactor 11.9 |
| Missing PP MIs | `MI_StorybookOutline_Premium_Hero`, `MI_Outline_PremiumV3_Hero`, `MI_StarryNight_Hero`, `MI_MeluColorGrade_PortfolioHero` | — | FallenMoon + KaleidoNave PPVs reference them | **Not on disk and not in git.** Those blendable slots resolve to null, so **FallenMoon and KaleidoNave have no PP ink at all** |
| Inverted hull | `/Game/Genshin_Shader_v1_1/M_Hull_Outline` (Masked, Unlit, 161 VS instructions) → `MI_HullOutline_Character_Heavy` (Thickness 1, LineWidth 1.2, dynamic width on), `_Thin` (0.4/0.4), `_Environment` (0.6/0.7), `_Hairline` (0.2/0.15) in /Game/Melodia/_PROJECT/04_Materials/Outline (edited today 13:49 and 16:30) | vertex normal extrusion | character mesh slots (Melusina, Sir, sheep). Env usage not proven | this is the thin line you see on hair and face |
| Melusina imported outline slots | `MI_Melusina_Outline_00x`, `MI_Melusina_Outline_Shader_star_0xx`, plus the halftone slots `MI_Melusina_Halftone_*` | Blender-imported shells | SK_Melusina slots 4/6/8/14/16/19/22/24/27/29/31/32 (+10/34 halftone) | legacy. Brows BP is off-limits |
| MooaToon | `MF_MooaToonBaseInput`, `MF_MooaEncodeAttributes`, `MF_MooaDecodeAttributes` (EnvSandbox/Materials/Functions, Art/…/MaterialFunctions, MaterialFunctions_Legacy), `M_MooaToon_*` family (Content/_PROJECT/04_Materials/MooaToon, ~35 masters incl. `M_MooaToon_Halftone_*`), `M_HybridLandscape_MooaToonSDF` | GBuffer attribute encode/decode (surface side). **None of these is a screen-space outline** | surface masters only | The "Moatoon MF" hybrid is only possible on the surface side (per-material outline ID/width encoded into the GBuffer / CustomData). The PP side has to be ours |
| Quarantined | `M_PP_ToonOutline`, `M_PP_StorybookVines(_Inst)` in _QuarantinePostProcess_20260801 | — | stale unlabeled PPVs in L_SakuraPath/L_Template (Decision 037a) | not in the four target levels |
| Other | ACF `M_OutlineOverlay` (gameplay highlight), VRM4U MToon outline, `MF_NikkiStickerEdge` (surface fresnel edge) | — | not in the render levels | ignore tonight |

### V7 ink HLSL, node by node (MaterialExpressionCustom_0)
1. Texel-snapped or un-jittered centre UV (`JitterCompensation` lerp), clamped to the view rect (the 08-01 fix is in).
2. Centre depth = 5-tap average. `distRatio = RefDistance/depth`. `widthPx = clamp(OutlineWidth*distRatio*InkBlurRadius, max(MinWidthPx,1), MaxWidthPx)`, rounded to whole pixels. This is the distance-scaled thickness.
3. **16 radial taps, 8 directions × 2 rings**, rotated by a per-pixel hash. `dt = depth(tap) − dC`. **`if (dt > rejectThresh) dt = 0` with `rejectThresh = max(dC*DepthRelativeThreshold,1)*5`.** A silhouette whose background is more than 5× the threshold behind it (island edge against sky or distant terrain, crystal against sky) is **thrown away**. Only small depth steps ever ink.
4. Silhouette = (lerp(dMax, mean, ≥0.5) / (dC*DepthRelativeThreshold)) × DepthWeight × EdgeStrength. Crease = (1 − N·N) / CreaseThreshold × NormalWeight × EdgeStrength.
5. Analytic smoothstep AA band (AAWidth/widthPx).
6. Foliage = SubsurfaceColor > 0.005, scaled by `saturate(FoliageDepthInkStrength)`, `saturate(FoliageNormalInkStrength)` and the foliage distance fade.
7. Falloff (FalloffStart/End) × taper.
8. Stencil: 1–3 = style colours, **4 = hero skip** (Sir, Melusina use their hulls instead).
9. Dream rim, iridescence, atmospheric fade.
10. **Halftone: `if HalftoneAmount>0` the edge is turned into a dot screen.** Then paper grain ×0.12 and paper colour. Output is float4(ink, edge) into MF_PostProcessBlend.

### Live MI_StorybookOutline_Frozen values vs the master
OutlineWidth **−0.124** (master 1.5; clamped to MinWidth, so 1 px) · DepthRelativeThreshold **5.588** (master 0.015, **372×**) · DepthWeight 0.563 · NormalWeight 0.776 · FoliageDepthInkStrength **−3.817** (saturates to 0, so foliage silhouettes are off) · FoliageNormalInk 0.368 · FoliageFade 39→1906 · FalloffStart/End 3000/8000 · DistanceFadeStrength 495.7 (start 2971, end 20000) · **HalftoneAmount 0.744**, scale 4.04 · EdgeStrength 1.10 · StenciRange 1–255 (+IncludeStencilInRange).

## 2. Colour-grade stack per level

All four PP masters are **BL_SceneColorAfterTonemapping at priority 0**. Their execution order therefore depends on array order, which is not a contract.

| Level | PPV | Priority / unbound / enabled | Blendables (in order, weight) | Engine overrides |
|---|---|---|---|---|
| Morning | PPV_NikkiDream | 0.701 / yes / yes | Outline_Frozen 1.0 · StarryNight_Frozen 1.0 · MeluColorGrade_Frozen 0.69 · MelodiaInk_Frozen 1.0 | **none** (so engine defaults: vignette 0.4, bloom 0.675, histogram AE) |
| Morning | Ultra_Dynamic_Sky2 PostProcessComponent | 1.0 / yes | — | AE Histogram, bias 0, min −10, max 20 EV (beats the PPV) |
| Morning | OceanologyLake UnderwaterPostProcess | 99 / bound | transient UnderwaterDistortion MID | underwater only |
| FallenMoon | PPV_NikkiDream | 10 / yes / yes | **Premium_Hero (MISSING) 1.0** · MeluColorGrade_Frozen 1.0 · **StarryNight_Hero (MISSING) 0.0** | bloom 1.0, vignette 0, grain 0, fringe 0. Colour structs are stored but their override flags are off |
| FallenMoon | MoonPost | 0 / yes | — | AE **Basic**, bias 8.52, min −2.56, max 10.64, physical-camera flag, FilmSlope 0.648, FilmWhiteClip 0.106, ShadowsMax 0.259, Contrast R 0.94, Local Exposure Fusion (detail 3.29, highlight 0.33), bloom 0.62 FFT, Lumen HitLighting. **Its AE fields are overridden by the UDS component (priority 1 > 0)** |
| KaleidoNave | PPV_NikkiDream | 10 / yes / yes | **Outline_PremiumV3_Hero · MeluColorGrade_PortfolioHero · StarryNight_Hero: all MISSING** | bloom 1.0, vignette 0 |
| KaleidoNave | NavePost | 0 / yes | — | bloom 0.85 |
| SeaAbove | PPV_NikkiDream | 1 / yes / **DISABLED** | Premium_Hero_Dream 1.0 | — |

### Grade material (M_PP_MeluColorGrade_Frozen, Custom_2, reads MPC_Melodia_Palette ×7 plus SceneTexture PostProcessInput)
MI_MeluColorGrade_Frozen: GradeStrength 0.81, Contrast 0.79, **ShadowLift −0.088** (crushes the shrub undersides), HighlightSoft 0.51, Saturation 0.23, SplitStrength 0.51, NikkiHeroGradeStrength 0.53, Dream* (Sat 1.04, Contrast 1.06, ShadowLift 0.025, HighlightSoft 0.24, SplitTone 0.22), **VignetteBaseIntensity 0.5**, falloff 2.03 (this stacks on the engine's 0.4), DreamTint/Shadow/Highlight = violet/magenta/yellow.

### Halftone / dot pass
There are two sources:
- **(a) M_PP_MelodiaInk_Frozen**: a fullscreen print pass (AfterTonemapping, 4 SceneTextures, 14 MPC_MelodiaInk params). The MI sets InkHalftone 1, InkDotPitch 0.034, InkDotScale 0.95, InkStrength 0.65, hatch 1 (density 6), grain 1, smear 1. **This is the dot screen over the whole frame.**
- **(b) The outline MI HalftoneAmount 0.744**, which breaks the ink line itself into dots.

Neither pass masks the sky or the characters.

## 3. Prior decisions that matter
- **037**: foliage ink is tuned on the instance, never the master. Blendables are always instances.
- **040–042**: the PPV must not carry a second grade. Scene grade lives in the grade MI + MPC. The grade's vignette was exposed as VignetteBaseIntensity.
- **041**: UDS instant exposure on begin play = true.
- OUTLINE_FINALIZATION 09-14/15: the drift is in instance VALUES, not the math. Keep a value-range guard. Stencil 4 = hero ward (Sir). r.AntiAliasingMethod: DefaultFeatureAntiAliasing=1 (FXAA) was committed, then TSR was found live. Temporal AA makes the fullscreen depth ink crawl.
- The MelodiaInk "ambush" (hatch 802) is fixed, and its values are sane today.
- Premium_Hero / StarryNight_Hero were moved to Frozen and _Archive on 08-22 and later. The FallenMoon and Kaleido PPVs were never repointed.

## 4. Why the environment ink doesn't read (ranked)
1. **DepthRelativeThreshold 5.588.** A depth step has to be 559% of the pixel depth. Environment silhouettes never qualify.
2. **The reject rule `dt > 5×threshold → 0`.** Even at master values it discards exactly the big silhouettes (island rims, crystals and flowers against sky or distant ground). This is an algorithm bug, not a value.
3. **FoliageDepthInkStrength −3.8** saturates to 0, so foliage (flowers, shrubs flagged by SubsurfaceColor) gets no silhouette.
4. OutlineWidth is negative, so the line is 1 px. After tonemapping, at 1080p, that is sub-visible. The halftone at 0.744 then dots it out, and MelodiaInk's dot screen adds noise on top.
5. FalloffEnd 8000 is small for island-scale vistas (islands sit at 5–30k uu).
6. The characters read because their **hull outlines** draw real geometry, independent of the PP ink.

Nanite, masked materials and stencil are not the cause: StencilRange isn't used for masking, and only stencil 4 skips.

## FINAL STATE, 2026-09-30 19:20 ET (closeout)
Applied (small calls, no node deletes, no save_packages; every Ctrl+S by the owner):
- `MI_StorybookOutline_Render2026_FallenMoon`: SceneExposureEV 3.0 to 0 (18:45, saved 19:13:53).
- L_MelusinaMorning `PPV_NikkiDream`: blendables Render2026 outline 1.0 / StarryNight_Frozen 1.0 / Render2026 grade 0.69 / Render2026 ink 1.0; vignette override 0.1; local-exposure highlight contrast override 0.8 (18:45, saved 19:13:53, actor `6/2U/SXESN1EMPQO4ZW3Q2U4IED`).
- L_FallenMoon priority-10 `PPV_NikkiDream`: auto-exposure bias override +1.5 EV (method Histogram) (19:14, saved 19:14:46, actor `7/DL/RANDXO0WWWH6YVA16F9F10`). Visual not yet checked.
- Recaptures skipped (owner: final renders later).
Committed: **41c464a07** on main (19:16:58 ET, owner-approved ALLOW_MAIN_COMMIT, hooks passed, not pushed): the 10 Render2026/Candidates assets + the Morning PPV actor.
Not in git: the Fallen Moon PPV actor. `Content/__ExternalActors__/EnvSandbox/*` is gitignored (.gitignore:231), so it's saved on disk only. The same applies to any Sea Above/Kaleido PPV edits.
Also note: only 10 Render2026-related assets exist, not 11 (6 in Render2026/ + 4 at the Candidates paths).
Open: see GEM_LOOKDEV_PLAN.md and CLOSEOUT_2026-09-30.md.
