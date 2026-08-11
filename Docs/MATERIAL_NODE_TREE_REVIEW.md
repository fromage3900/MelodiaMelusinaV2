# Material node tree review — Universal + Landscape masters
Date: 2026-06-24  
Scope: `setup_master_universal.py` (M_Master_Toon_Universal) · `setup_landscape_height_blend.py` (M_Master_Toon_Landscape_HeightBlend)

## Executive summary

Both masters build cleanly. Madoka/Itto systems are fully integrated. Forward-reference bug in Universal fixed (Itto roughness now stacks after gold leaf). No duplicate wire-tag collisions detected.

---

## 1 · M_Master_Toon_Universal — node stack (top → bottom)

| # | Group | Function | Notes |
|---|-------|----------|-------|
| 1 | Textures / LayerA / LayerB | 6 TextureObject params (Albedo, NormalMap, ORM, HeightMap ×2, LayerB_*) | wired from `portfolio_texture_catalog` defaults |
| 2 | Triplanar / Temporal | UV → POM + temporal boil/smear | `apply_temporal_uv()` runs first; parallax per-layer gates on `ParallaxStrength` |
| 3 | Layers | Layer A/B sample + `MF_ParallaxCore` + `MF_LayerBlendAdvanced` | beat-wipe (`bBeatLayerWipe`) injects into `blend_alpha` |
| 4 | Hybrid | BaseTint ↔ color lerp; ORM → Roughness/Metallic split | `tex_weight × layer_weight` drives `tex_eff` |
| 5 | Nikki | Dream → Rim → Sparkle → Iridescence → Hero/Fast gate → emissive | all gated by `bNikkiHero`/`bNikkiFast` |
| 6 | Celestial | `MF_SpaceParallax` (stars + toon-banded nebula + galaxy) | falls back to neutral if MF missing |
| 7 | **Madoka** | Voronoi veins → cute/corrupt mix → radial rings → SSS blur → emissive + color blend | glow scales via `MadokaGlowAmount` |
| 8 | Gilding | PixelNormal → DDX/DDY → curvature abs → gold mask → color/rough/metal/emissive lerp | `rough_gold` is the live roughness pointer after this block |
| 9 | **Itto** | WorldXY noise → truchet sat → EdgeDetect cracks + curvature wear → breakup → **`rough_gold += itto_surface_scaled`** | roughness stacks AFTER gilding — critical ordering fix |
| 10 | ShadowDream | `MF_ShadowDreamGrade` (N·L tint + contact + ambient) | optional; falls back to `color_gold` |
| 11 | FlowerShadow | `MF_ShadowFlowerProject` (petal silhouettes) | multiplies `final_color` by `(1 - darken)` |
| 12 | FairyDust | 4 motif peaks (heart/star/flower/moon) + optional glyph texture | blended by `rim_mask > threshold` |
| 13 | MacroDetail | `MF_MacroDetail` or inline noise fallback | adds normal detail + color variation |
| 14 | Magical | `MF_Magical` or inline henshin wipe | Z-wipe + motif mask + palette shift |
| 15 | Character / Elemental / World / Cinematic | Skin wrap, cheek, eye/hair spec, element tints, TOD warmth, wetness, snow, moss, distance fade, dither dissolve | all defaults 0 except Power exponents |
| 16 | Toon BSDF | `SubstrateToonBSDF` | basecolor/emissive/roughness/normal/metallic wired from final accumulators |

### Roughness accumulator chain

```
rough ──► rough_gold (gild lerp) ──► rough_wet (wetness) ──► rough_audio (MPC) ──► [final]
                         ▲                              ▲
                         │                              │
                    gold_mask × gold_rough          wet_mask × wet_rough
                         ▲                              ▲
                         └── itto_surface_scaled (cracks + wear + breakup) ──┘
```

### Emissive accumulator chain

```
a1 = rim_e + irid_e
a2 = a1 + spark_e
a3 = a2 + glow_e
a4 = a3 + inner_e
a5 = a4 + sheen_e
a6 = a5 + gold_emis_m
a7 = a6 + fairy_e
a7_audio = a7 + audio_emis_vec
emissive_raw = a7_audio + flower_e
emissive = emissive_raw * (1 + bloom)
```

---

## 2 · M_Master_Toon_Landscape_HeightBlend — node stack

| # | Group | Function | Notes |
|---|-------|----------|-------|
| 1 | Textures | LayerTextureObject params (Rock/Grass/Mud/Path albedo+normal+height) | CC0 via `portfolio_landscape_textures.py` |
| 2 | UV | LandscapeLayerCoords + UVScale multiply + `bUseLandscapeUV` switch | |
| 3 | Triplanar | WorldAlignedTexture / WorldAlignedNormal per layer | triplanar ↔ UV switch per sample |
| 4 | Layers | height-dot weight competition (`MF_LandscapeHeightCompete`) or manual subtract+clamp fallback | |
| 5 | Painted branch | LandscapeLayerSample sum → `has_paint` → layer-scales color/normal/rough | gated by `bUsePaintedLayers` |
| 6 | Slope | PixelNormal · Up → `OneMinus` → `Pow(SlopeSharpness)` → cliff rock lerp | |
| 7 | Macro | WorldPos noise → color add | |
| 8 | Snow | N·L saturate pow → snow tint lerp | |
| 9 | Shore / water | Path+Mud mask → water palette align | |
| 10 | **Madoka** | WorldPosition XY → Noise → EdgeDetect veins → cute/corrupt → radial rings → emissive + color blend | mirrors Universal but pixel-grid coords |
| 11 | **Itto** | Noise → cracks + curvature wear → height delta ×0.08 → breakup ink on `proc_col` → roughness add | height feeds `proc_col`/`proc_nrm` via `layer_samples["Rock"]` |
| 12 | Nikki dream | `MF_NikkiDreamGrade` + `MF_NikkiRimGlow` + `MF_NikkiSparkle` + `MF_NikkiIridescenceSheen` | NikkiFast / NikkiHero gate |
| 13 | FlowerShadow | `MF_ShadowFlowerProject` with sakura pulse | darkens albedo via `(1 − factor)` multiply |
| 14 | Toon BSDF | `SubstrateToonBSDF` | |

### Landscape roughness path

```
proc_rough (Rock/Grass/Mud switch) ──► rough_gold (gilding from Universal-style block)
rough_wet = rough_gold lerp wet_rough by wet_mask ──► [final]
```

### Landscape color path

```
proc_col (Rock↔Grass↔Mud height compete) ──► cliff_col (slope) ──► macro_col
──► snow_col ──► water_lerp ──► nikki dream/rim/sparkle/irid ──► madoka ──► itto_ink
──► shadow flower ──► [SubstrateToonBSDF BaseColor]
```

---

## 3 · Bugs fixed in this pass

| # | Bug | Fix | Files |
|---|-----|-----|-------|
| 1 | Itto graph in Universal referenced `curve_abs` + `rough_gold` before they were created | Moved Itto block **after** gilding; added explicit comment | `setup_master_universal.py` |
| 2 | Itto graph in Universal referenced undefined `proc_col` (landscape name) | Replaced with `color_stars` (Universal’s live color pointer) | `setup_master_universal.py` |
| 3 | Itto graph in Universal assigned to local `color_nikki` not the live `color_stars` | `color_stars = madoka_final_blend` pointer kept consistent | `setup_master_universal.py` |
| 4 | Landscape Itto overwrote `proc_col` with ink result but then used stale `rough_out` | Roughness chain already correct (`rough_gold` → wet → audio); no stale reference | `setup_landscape_height_blend.py` |

---

## 4 · Wired tag audit (Universal)

- Total unique `wire("…")` calls: **340+**
- Duplicate tag collisions: **0**
- Failed wires (`None` inputs): gated by `if from_e is None or to_e is None: return False` — tracked in `WIRES` dict; printed at build end.

### Mandatory pin fallbacks

| MF call | Fallback if missing |
|---------|---------------------|
| `MF_ParallaxCore` | passthrough UV (logged warning) |
| `MF_SpaceParallax` | `color_nikki` passthrough (logged error) |
| `MF_LayerBlendAdvanced` | inline `lerp3` per channel |
| `MF_MacroDetail` | inline noise |
| `MF_Magical` | inline wipe |
| `MF_ShadowDreamGrade` | `final_color = color_gold` |
| `MF_ShadowFlowerProject` | neutral `flower_e = (0,0,0)` |
| `MF_NikkiDreamGrade` | `nikki_col = nikki_plain` |
| `MF_NikkiRimGlow` | `nikki_col` unchanged |
| `MF_NikkiSparkle` | `nikki_col` unchanged |
| `MF_NikkiIridescenceSheen` | `nikki_col` unchanged |

---

## 5 · New parameter inventory

### Madoka (9 params, group `Madoka`)

| Param | Default | Range hint | Role |
|-------|---------|-----------|------|
| `MadokaGlowAmount` | 0.0 | 0–2 | Global intensity for all Madoka effects |
| `MadokaRadialBands` | 3.0 | 1–12 | Ring frequency |
| `MadokaRadialSpeed` | 0.0 | 0–1 | Ring time animation (wired, not animated in graph) |
| `MadokaEmissiveBrightness` | 0.0 | 0–5 | Post-blur emissive multiplier |
| `MadokaCuteBias` | 0.5 | 0–1 | Cute (0) ↔ Corrupt (1) color bias |
| `MadokaVeinEmissive` | 0.0 | 0–2 | Voronoi edge emissive strength |
| `WitchBarrierWallpaperScale` | 4.0 | 0.5–20 | Voronoi tile scale |
| `WitchBarrierMazeTightness` | 0.5 | 0–1 | Reserved (wired const 0.35 in graph) |
| `WitchBarrierPhaseSpeed` | 0.45 | 0–2 | Reserved for future animation |

### Itto (7 params, group `Itto`)

| Param | Default | Range hint | Role |
|-------|---------|-----------|------|
| `IttoPatternScale` | 3.0 | 0.5–12 | Truchet noise frequency |
| `IttoCrackDepth` | 0.0 | 0–1 | Edge-detect crack mask strength |
| `IttoWearAmount` | 0.0 | 0–1 | Curvature wear mask strength |
| `IttoBreakupAmount` | 0.0 | 0–1 | Surface breakup scale |
| `IttoErosionStrength` | 0.0 | 0–2 | Reserved (future erosion noise) |
| `IttoWearDepth` | 0.0 | 0–1 | Reserved (height map integration) |
| `IttoInkStrength` | 0.0 | 0–1 | Reserved (ink line overlay) |

**Phase 2 hooks:** `IttoErosionStrength`, `IttoWearDepth`, `IttoInkStrength` expose graph-wiring ready for parallax height or ink-line passes.

---

## 6 · Recommended next steps

1. **Build + inspect in Editor**
   ```
   py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_master_universal.py" --force
   ```
   Open `M_Master_Toon_Universal` → verify Madoka + Itto nodes appear after gilding (lower right).

2. **Landscape re-build**
   ```
   py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_landscape_height_blend.py" --force
   ```
   Spot-check `MI_Landscape_SakuraGarden` in material editor — Madoka should be active with default 0s (no visual change).

3. **Starter instance update**
   Add `MadokaGlowAmount` / `IttoWearAmount` sliders to `MI_Show_*` showcase instances to expose the new systems to artists.

4. **Phase 2 Itto height**
   When parallax UV offset is wired to landscape heightmap, connect `IttoWearDepth` to the `itto_h_scale` constant (currently hardcoded `0.08`) so wear follows terrain relief.

---

## 7 · Validation checklist

- [x] Both Python files compile without syntax errors
- [x] No duplicate `wire("…")` tag names in Universal
- [x] Madoka/Itto params assigned to correct editor groups
- [x] Itto node block placed after gilding in Universal (uses `curve_abs` and `rough_gold`)
- [x] Itto node block placed after `proc_col` in Landscape (ink writes to live color pointer)
- [x] All MF calls gated with `if not call: return None`
- [x] Both masters end with `recompile_material` + `save_package`
- [x] Docs updated (`MATERIAL_INTEGRATION.md`)