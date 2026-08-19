# Surreal Animated PBR System — Redesign Plan

## Failure Analysis of Existing `MM_Master_SurrealAnimatedPBR_Dynamic`

### Critical Gaps Found

| # | Issue | Severity | Evidence |
|---|-------|----------|----------|
| 1 | **No Base Utility Layer** | CRITICAL | No subgraphs for noise, mask shaping, triplanar, tile-safe blending, gradient remapping |
| 2 | **Style Trees are flat colorize+blend** | HIGH | Nikki=1 colorize+1 noise; Madoka=1 voronoi+1 warp+2 colorize; Itto=1 truchet+1 colorize |
| 3 | **No reusable noise library** | HIGH | Perlin used once (sparkle). No Worley, Gradient noise, Domain Warp subgraphs |
| 4 | **No seed system** | CRITICAL | No shared seed parameter; all variation is unseeded |
| 5 | **Animation is minimal** | HIGH | Only 3 translate nodes use `$time`. No flow map, no noise evolution, no global anim controller |
| 6 | **PBR split is weak** | MEDIUM | Roughness=height→colorize→mars→bias. Metallic=veins→stars→bias. No micro-detail layering |
| 7 | **Madoka emissive not first-class** | HIGH | Emissive is post-hoc blend of sparkle+nebula, not integrated into the Madoka tree |
| 8 | **Itto ignores height** | MEDIUM | Height lane uses moon+Itto cracks+Madoka warp, no proper Itto curvature/detail |
| 9 | **Celestial lacks spherical projection** | MEDIUM | Uses flat UV transform, no spherical/cylindrical mapping for "space-surface" look |
| 10 | **No curvature simulation** | MEDIUM | No curvature-based wear anywhere (critical for Itto) |
| 11 | **Parameters not all 0-1 normalized** | LOW | `TileRepeat` max=8, `WitchBarrierWallpaperScale` max=12, `ExportResolution` is exponent |
| 12 | **Single monolithic graph** | MEDIUM | No subgraphs = no reusability, hard to maintain |

---

## New Architecture: 3-Layer System

```
┌──────────────────────────────────────────────────────────┐
│                    LAYER 3: STYLE TREES                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  NIKKI   │  │  MADOKA  │  │  ITTO    │  │CELESTIAL │  │
│  │ (Soft)   │  │(Ethereal)│  │ (Mythic) │  │ (NASA)   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├──────────────────────────────────────────────────────────┤
│                    LAYER 2: PBR ENGINE                      │
│  Albedo │ Roughness │ Metallic │ Normal │ AO │ Height │   │
│  Emissive │ Opacity │ SSS                                    │
├──────────────────────────────────────────────────────────┤
│                    LAYER 1: BASE UTILITY                     │
│  Noise Lib │ Mask Ops │ Triplanar │ Gradient │ Seed Sys   │
│  Domain Warp │ Flow Gen │ Tile Safe Blend                    │
├──────────────────────────────────────────────────────────┤
│                    INPUT / PREPROCESS                        │
│  Source │ Remote Params │ Animation Controller              │
└──────────────────────────────────────────────────────────┘
```

---

## Layer 1: Base Utility Subgraphs (New)

### SG_Noise_Library (subgraph)
| Node | Type | Parameters | Purpose |
|------|------|------------|---------|
| Perlin_Base | perlin | scale_x, scale_y, iterations, persistence, seed=$GlobalSeed | Main organic noise |
| Worley_Cells | voronoi | scale, randomness, seed=$GlobalSeed+1 | Cell breakup, sparkle mask |
| Gradient_Noise | perlin | scale_x=4, scale_y=4, gradient=True, seed=$GlobalSeed+2 | Directional flow |
| DomainWarp_Base | warp | amount, eps, seed=$GlobalSeed+3 | Distortion modulation |
| Fractal_Sum | perlin | 4-octave sum, persistence=0.5, seed=$GlobalSeed+4 | Detail layering |

**Outputs:** Noise_Grayscale, Noise_Gradient, Noise_Cellular, Noise_Warped

### SG_Mask_Shaping (subgraph)
| Node | Type | Parameters | Purpose |
|------|------|------------|---------|
| Levels | tones | value, contrast, pivot | Contrast stretch |
| S_Curve | tones | value=0.5, contrast=0.3, curve=smoothstep | Soft threshold |
| Slope_Bias | custom (mm) | input, bias, slope | Terrain-style blending |
| Curvature | edge_detect | size, threshold | Wear/edge mask |
| Distance_Field | shape | shape=circle, radius, edge | Radial falloff |

**Outputs:** Mask_Hard, Mask_Soft, Mask_Edge, Mask_Radial

### SG_Triplanar (subgraph)
| Node | Type | Parameters | Purpose |
|------|------|------------|---------|
| UV_Channels | separate | input → 3 UV sets | X/Y/Z projection |
| Blend_Weights | normal_map | blend_mode=triplanar | Normal-weighted blend |
| Transform_X | transform | rotate=90 | YZ plane |
| Transform_Y | transform | rotate=0 | XZ plane |
| Transform_Z | transform | rotate=0 | XY plane |
| Blend_Triplanar | blend | blend_type=add, weight=normal | Final blend |

**Outputs:** Color_Triplanar, Normal_Triplanar, Height_Triplanar

### SG_Gradient_Remap (subgraph)
| Node | Type | Parameters | Purpose |
|------|------|------------|---------|
| Colorize | colorize | gradient (multi-point) | Value→Color mapping |
| Grayscale_Remap | colorize | gradient black→white (adjustable) | Contrast mapping |
| Channel_Split | separate | input → R/G/B | Per-channel processing |

**Outputs:** Remapped_Color, Remapped_Gray, Channel_R/G/B

### SG_Seed_System (remote-driven)
```
$GlobalSeed        = 0.5  (0-1 mapped to int range)
$ChannelSeed       = $GlobalSeed + 0.01 * ChannelIndex
$VariationSeed     = $GlobalSeed + 0.001 * PixelHash
```
All noise nodes receive `seed = floor($GlobalSeed * 65535)` via expression.

### SG_Flow_Generator (subgraph)
| Node | Type | Parameters | Purpose |
|------|------|------------|---------|
| Gradient_Flow | perlin gradient | scale=16, seed=$GlobalSeed+5 | Base flow direction |
| Time_Warp | translate | $time * $AnimSpeed | Advection |
| Blur_Flow | blur | sigma=2 | Smooth flow field |

**Outputs:** FlowVector_UV, FlowStrength

---

## Layer 2: PBR Engine (Rewritten Lane 06)

### PBR Split Architecture

```
                            ┌──→ Albedo_Blend (0.85 orig + 0.15 desat)
                            │
        ┌──→ Roughness ─────┤──→ Rough_Base (colorize from height)
        │                   │──→ Rough_Micro (high-freq noise blend)
        │                   │──→ Rough_Macro (mars data blend)  
        │                   └──→ Rough_Bias (tones: $RoughnessBias)
        │
        ├──→ Metallic ──────┤──→ Met_Base ($MetallicAmount constant)
        │                   │──→ Met_Mask (edge/vein overlay)
        │                   │──→ Met_Detail (sparkle/highlight mask)
        │                   └──→ Met_Final (multiply stack)
        │
Final ──┼──→ Normal ───────┤──→ Norm_Base (normal_map from height)
        │                   │──→ Norm_Detail (detail noise normal)
        │                   │──→ Norm_Warp (domain warp overlay)
        │                   └──→ Norm_Strength (scale by $NormalStrength)
        │
        ├──→ AO ────────────┤──→ AO_Base (blurred height)
        │                   │──→ AO_Detail (cavity mask)
        │                   └──→ AO_Strength (tones: $AOStrength)
        │
        ├──→ Height ────────┤──→ H_Base (colorize from final)
        │                   │──→ H_Detail (from style trees)
        │                   └──→ H_Scale (multiply: $HeightScale)
        │
        ├──→ Emissive ──────┤──→ E_Nikki (sparkle glow)
        │                   │──→ E_Madoka (barrier veins + glow)
        │                   │──→ E_Celestial (nebula + stars)
        │                   └──→ E_Blend (max blend stack)
        │
        └──→ SSS ───────────┤──→ SSS_Base (desat albedo)
                            └──→ SSS_Amount (scale: $SSSAmount)
```

### New PBR Parameters
| Parameter | Range | Default | Purpose |
|-----------|-------|---------|---------|
| $RoughnessBias | 0-1 | 0.55 | Global roughness offset |
| $RoughnessContrast | 0-1 | 0.3 | Micro-detail roughness contrast |
| $MetallicAmount | 0-1 | 0.05 | Global metallic level |
| $NormalStrength | 0-2 | 0.8 | Normal map intensity |
| $NormalDetail | 0-1 | 0.3 | Detail normal blend weight |
| $AOStrength | 0-1 | 0.7 | Ambient occlusion intensity |
| $AORadius | 1-10 | 3 | AO blur radius |
| $HeightScale | 0-1 | 0.25 | Displacement strength |
| $SSSAmount | 0-1 | 0.12 | Subsurface scattering amount |
| $EmissiveIntensity | 0-5 | 1.0 | Global emissive brightness |

---

## Layer 3a: Nikki Style Tree (Rewritten Lane 08)

### Target Material: Soft Fashion / Synthetic Clean

```
Input Source
    │
    ├──→ DreamGrade (gradient: warm pastel, 4-point)
    │       │
    │       ├──→ Blend_Sparkle (screen, 0.35)
    │       │       │
    │       │       └──← Perlin_Sparkle (32px) → Translate ($time * $AnimSpeed * $SparkleDriftSpeed)
    │       │
    │       ├──→ S_Curve_Soft (tones: smoothstep, contrast=0.2)
    │       │
    │       └──→ Blend_FabricMicro (overlay, 0.15)
    │               │
    │               └──← Noise_Fabric (perlin, scale=64, 2 iterations, seed)
    │
    ├──→ Blend_DirectionalFlow (soft light, 0.25)
    │       │
    │       └──← Gradient_Flow (perlin gradient, scale=8) → Time_Warp
    │
    └──→ Blend_Nikki (lerp, amount=$StyleNikki)
```

### New Nodes Added
- **Noise_Fabric**: Perlin at 64px scale, 2 iterations → fine textile microbreakup
- **Gradient_Flow**: Noise-based directional field → fabric grain direction
- **S_Curve_Soft**: Tones node with 0.2 contrast → non-destructive soft contrast
- **Blend_FabricMicro**: Overlay blend at 0.15 → subtle sheen variation

### Nikki-Specific Parameters
| Parameter | Range | Default | Purpose |
|-----------|-------|---------|---------|
| $NikkiPastelLift | 0-1 | 0.22 | Brightness lift for dreamy look |
| $NikkiSparkleAmount | 0-1 | 0.35 | Sparkle intensity |
| $NikkiFabricDetail | 0-1 | 0.15 | Fabric micro-breakup strength |
| $NikkiFlowStrength | 0-1 | 0.25 | Directional flow intensity |
| $NikkiSaturation | 0-2 | 0.8 | Color saturation control |

---

## Layer 3b: Madoka Style Tree (Rewritten Lane 22)

### Target Material: Magical / Ethereal / Light-Field

```
Input (from Nikki)
    │
    ├──→ Voronoi_Maze (scale=$WallpaperScale, randomness=$MazeTightness)
    │       │
    │       └──→ Rotate ($time * $AnimSpeed * $BarrierPhaseSpeed * 360)
    │               │
    │               └──→ Warp (amount=0.08)
    │                       │
    │                       ├──→ [COLOR LAYER]
    │                       │       ├──→ Colorize_Cute (pink→lavender gradient)
    │                       │       ├──→ Colorize_Corrupt (red→dark gradient)
    │                       │       └──→ Blend_MadokaColors (lerp 0.5)
    │                       │
    │                       ├──→ [SSS LAYER - NEW]
    │                       │       ├──→ Blur_SSS (gaussian, sigma=8)
    │                       │       └──→ Blend_Glow (screen, 0.3)
    │                       │
    │                       ├──→ [RADIAL FIELD - NEW]
    │                       │       ├──→ Distance_Field (shape=circle, center animated)
    │                       │       ├──→ Gradient_Radial (multi-band, 3 stops)
    │                       │       └──→ Blend_Radial (add, 0.4)
    │                       │
    │                       ├──→ [EMISSIVE - NEW FIRST-CLASS]
    │                       │       ├──→ Colorize_Emissive (bright cyan→magenta)
    │                       │       ├──→ Glow_Blur (blur, sigma=4, screen blend)
    │                       │       └──→ Edge_EmissiveVeins (edge_detect, blend screen)
    │                       │
    │                       └──→ Edge_MadokaVeins (edge_detect, size=2)
    │
    ├──→ Blend_Madoka (lerp, amount=$StyleMadoka)
    └──→ Blend_Emissive_Madoka (max, amount=$StyleMadoka * $EmissiveIntensity)
```

### New Nodes Added
- **Blur_SSS**: Gaussian blur sigma=8 → fake subsurface scattering glow
- **Distance_Field**: Shape node centered on animated UV offset → radial energy
- **Gradient_Radial**: Multi-band gradient from distance → spectral rings
- **Colorize_Emissive**: Bright emissive colors (cyan→magenta)
- **Glow_Blur**: Screen-blurred glow approximation
- **Separate emissive output path**: Emissive now wired independently to material port 3

### Madoka-Specific Parameters
| Parameter | Range | Default | Purpose |
|-----------|-------|---------|---------|
| $MadokaGlowAmount | 0-1 | 0.3 | SSS fake glow intensity |
| $MadokaRadialBands | 1-6 | 3 | Number of spectral rings |
| $MadokaRadialSpeed | 0-2 | 0.2 | Ring animation speed |
| $MadokaEmissiveBrightness | 0-5 | 2.0 | Primary emissive strength |
| $MadokaCuteBias | 0-1 | 0.5 | Cute vs corrupt color blend |
| $MadokaVeinEmissive | 0-1 | 0.35 | Vein emissive contribution |

---

## Layer 3c: Itto Style Tree (Rewritten Lane 23)

### Target Material: Heavy / Mythic / Stone + Wood + Ornament

```
Input (from Madoka)
    │
    ├──→ [BASE PATTERN LAYER]
    │       ├──→ Truchet (size=$IttoPatternScale)
    │       ├──→ Translate ($time * 0.05)
    │       └──→ Colorize_Itto (stone gradient: dark→light→dark)
    │
    ├──→ [CURVATURE WEAR - NEW]
    │       ├──→ Edge_Curvature (edge_detect on height, size=4)
    │       ├──→ Levels_Curvature (tones: contrast=0.5, pivot=0.3)
    │       ├──→ Noise_Wear (perlin, scale=16, seed, multiply)
    │       └──→ Blend_Wear (multiply, 0.4)
    │
    ├──→ [HIGH-FREQUENCY BREAKUP - NEW]
    │       ├──→ Perlin_Detail (scale=128, iterations=2, persistence=0.4)
    │       ├──→ Worley_Cracks (voronoi, scale=8, randomness=0.7)
    │       ├──→ Blend_Breakup (overlay, 0.25)
    │       └──→ Edge_Cracks (edge_detect on voronoi, size=1)
    │
    ├──→ [DIRECTIONAL EROSION - NEW]
    │       ├──→ Gradient_Erosion (perlin gradient, scale=6)
    │       ├──→ Translate_Erosion (animated, $time * 0.02)
    │       └──→ Blend_Erosion (multiply, 0.2)
    │
    ├──→ [HEIGHT DETAIL - NEW, STRONG]
    │       ├──→ Height_Base (from Height lane)
    │       ├──→ Height_Cracks (voronoi edge, scaled by $IttoCrackDepth)
    │       ├──→ Height_Wear (curvature mask, scaled by $IttoWearDepth)
    │       └──→ Height_Blend (add, stack)
    │
    ├──→ Edge_IttoInk (edge_detect, size=2, blend=overlay)
    └──→ Blend_Itto (lerp, amount=$StyleItto)
```

### New Nodes Added
- **Edge_Curvature**: Large edge_detect (size=4) → smooth curvature mask
- **Levels_Curvature**: Tones contrast 0.5, pivot 0.3 → wear threshold
- **Noise_Wear**: Perlin at 16px → organic wear variation
- **Perlin_Detail**: 128px, 2 octaves → micro-breakup
- **Worley_Cracks**: Voronoi at 8px, randomness 0.7 → crack patterns
- **Gradient_Erosion**: Perlin gradient at 6px → directional erosion flow
- **Translate_Erosion**: Slow animated drift → water/weather flow
- **Height_Cracks/Wear**: Dedicated height outputs for displacement

### Itto-Specific Parameters
| Parameter | Range | Default | Purpose |
|-----------|-------|---------|---------|
| $IttoWearAmount | 0-1 | 0.4 | Curvature wear strength |
| $IttoBreakupAmount | 0-1 | 0.25 | High-freq breakup strength |
| $IttoErosionStrength | 0-1 | 0.2 | Directional erosion intensity |
| $IttoCrackDepth | 0-1 | 0.4 | Crack height displacement |
| $IttoWearDepth | 0-1 | 0.15 | Wear height displacement |
| $IttoPatternScale | 1-12 | 3 | Base ornament pattern scale |
| $IttoInkStrength | 0-1 | 0.6 | Edge ink line darkness |

---

## Layer 3d: Celestial / NASA Tree (Rewritten Lane 14)

### Target: Space-Surface Materials with Spherical Projection

```
Input (from Itto)
    │
    ├──→ [SPHERICAL PROJECTION - NEW]
    │       ├──→ UV_To_Sphere (custom: normalize UV→sphere coords)
    │       ├──→ Transform_Sphere (scale by $CelestialScale)
    │       └──→ Blend_Projection (multiply by sphere mask)
    │
    ├──→ [NEBULA LAYER]
    │       ├──→ Image_Hubble (carina nebula)
    │       ├──→ Transform_Nebula ($CelestialNebulaScale, repeat)
    │       ├──→ Translate_Nebula (animated: $time * $AnimSpeed * $CelestialNebulaScale)
    │       └──→ Colorize_Nebula (emissive tones: blue→purple→pink)
    │
    ├──→ [STAR FIELD - NEW, PROPER]
    │       ├──→ Image_StarMask (pre-baked CSV-derived mask)
    │       ├──→ Transform_Stars (scale=1, repeat)
    │       ├──→ Translate_Stars (drift: $time * $CelestialDrift)
    │       ├──→ Twinkle_Stars (sin($time * 2 + UV_hash) * $CelestialTwinkle)
    │       └──→ Blend_Stars (screen, 0.8)
    │
    ├──→ [CMB NOISE - NEW]
    │       ├──→ Perlin_CMB (scale=2, iterations=4, persistence=0.8)
    │       ├──→ Tones_CMB (contrast=0.7, pivot=0.5)
    │       └──→ Blend_CMB (multiply, 0.15)
    │
    ├──→ [PLANETARY DATA]
    │       ├──→ Image_MoonElev → Height blend (moon terrain)
    │       ├──→ Image_MarsRough → Roughness blend (mars surface)
    │       └──→ Blend_PlanetaryData (lerp by mask)
    │
    ├──→ [TIME/ORBIT - NEW]
    │       ├──→ Orbital_Phase (sin($time * $OrbitSpeed))
    │       ├──→ Rotate_Orbit ($time * $OrbitSpeed * 360 / $OrbitPeriod)
    │       └──→ Blend_Orbit (time-varying mask)
    │
    └──→ Blend_Celestial (blend_type=9, amount=$StyleCelestial)
```

### New Nodes Added
- **UV_To_Sphere**: Custom expression mapping (UV→lat/lon sphere coords)
- **Transform_Sphere**: Scale for spherical projection
- **Twinkle_Stars**: Sin-based brightness oscillation with per-pixel phase
- **Perlin_CMB**: Very low-frequency high-iteration noise → CMB approximation
- **Orbital_Phase**: Global orbit time parameter
- **Rotate_Orbit**: Full UV rotation driven by time
- **Colorize_Nebula**: Emissive-purposed gradient for nebula glow

### Celestial-Specific Parameters
| Parameter | Range | Default | Purpose |
|-----------|-------|---------|---------|
| $CelestialScale | 0.5-4 | 1.0 | Spherical projection scale |
| $CelestialNebulaScale | 0-2 | 0.42 | Nebula tiling frequency |
| $CelestialTwinkle | 0-1 | 0.5 | Star brightness oscillation |
| $CelestialDrift | 0-1 | 0.1 | Starfield drift speed |
| $CelestialOrbitSpeed | 0-2 | 0.05 | Orbital rotation speed |
| $CelestialOrbitPeriod | 1-360 | 60 | Days per full orbit |
| $CelestialCMBAmount | 0-1 | 0.15 | Cosmic background strength |
| $CelestialEmissiveBoost | 0-5 | 1.5 | Nebula emissive brightness |

---

## Animation Control Layer (Global)

### Architecture
```
                    ┌──→ $AnimSpeed (0-2, default 0.15)
                    │
$BakeTime/$time ────┼──→ $AnimOffset (0-1, default 0)
                    │
                    ├──→ Phase_Slow = fract($time * $AnimSpeed * 0.1 + $AnimOffset)
                    ├──→ Phase_Med  = fract($time * $AnimSpeed + $AnimOffset)
                    ├──→ Phase_Fast = fract($time * $AnimSpeed * 3 + $AnimOffset)
                    │
                    ├──→ Wave_Slow  = sin($time * $AnimSpeed * 0.5 + $AnimOffset * 6.28)
                    ├──→ Wave_Med   = sin($time * $AnimSpeed * 2 + $AnimOffset * 6.28)
                    └──→ Wave_Fast  = sin($time * $AnimSpeed * 6 + $AnimOffset * 6.28)
```

### Animated Systems
| System | Anim Input | Method |
|--------|------------|--------|
| Nikki Sparkle Drift | Phase_Med * $SparkleDriftSpeed | Translate X |
| Nikki Gradient Flow | Phase_Slow * $NikkiFlowStrength | Translate UV |
| Madoka Barrier Rotation | Phase_Med * $BarrierPhaseSpeed * 360 | Rotate, CX/CY |
| Madoka Radial Rings | Wave_Med * $MadokaRadialSpeed | Distance field offset |
| Madoka Emissive Pulse | Wave_Fast * 0.5 + 0.5 | Emissive brightness modulate |
| Itto Crack Drift | Phase_Slow * 0.05 | Translate X |
| Itto Erosion Flow | Phase_Slow * 0.02 | Gradient erosion offset |
| Celestial Nebula | Phase_Med * $CelestialNebulaScale | Translate X |
| Celestial Stars | Phase_Med * $CelestialDrift | Translate XY |
| Celestial Twinkle | sin($time * 2 + pixel_hash) * $CelestialTwinkle | Per-pixel brightness |
| Celestial Orbit | Phase_Slow * 360 / $OrbitPeriod | Full UV rotation |
| Global Domain Warp | Phase_Med * 0.05 | Post-warp all inputs |

### Bake Mode (Static Export)
When $BakeTime is used instead of $time, all Phase/Wave expressions freeze to a single frame value. The bake script sets $BakeTime=0.5 (mid-phase) for neutral export.

---

## Dependency Map

```
SourceImage
    │
    ├──→ Transform_Scale (TileRepeat)
    ├──→ Tones_Prep
    └──→ Buffer_Prep
            │
            ├──→ Kaleidoscope → Mirror → Transform_Repeat → Shape_Seam → Blend_Seam
            │                                                           │
            │                                                      [Tiled Source]
            │                                                           │
            ├───────────────────────────────────────────────────────────┤
            │                                                           │
            ├──→ [NIKKI TREE]                                          │
            │       ├──→ DreamGrade ←──────────────────────────────────┘
            │       ├──→ Perlin_Sparkle → Translate → Blend_Sparkle ──┘
            │       ├──→ Noise_Fabric → Blend_FabricMicro ────────────┘
            │       ├──→ Gradient_Flow → Blend_DirectionalFlow ───────┘
            │       └──→ Blend_Nikki (StyleNikki)
            │               │
            ├──→ [MADOKA TREE]                                         
            │       ├──→ Voronoi_Maze → Rotate → Warp ─────────────────
            │       │       ├──→ [Color] Colorize_Cute/Corrupt → Blend ┐
            │       │       ├──→ [SSS] Blur → Blend_Glow              │
            │       │       ├──→ [Radial] Distance → Gradient → Blend  │
            │       │       ├──→ [Emissive] Colorize_Emissive → Glow   │
            │       │       └──→ Edge_Veins ───────────────────────────┤
            │       └──→ Blend_Madoka (StyleMadoka)                    │
            │               │                                          │
            ├──→ [ITTO TREE]                                           │
            │       ├──→ Truchet → Translate → Colorize ───────────────┤
            │       ├──→ [Curvature] Edge → Levels → Noise → Blend     │
            │       ├──→ [Breakup] Perlin_Detail → Worley → Edge ──────┤
            │       ├──→ [Erosion] Gradient → Translate → Blend ───────┤
            │       ├──→ Edge_IttoInk                                  │
            │       └──→ Blend_Itto (StyleItto)                        │
            │               │                                          │
            ├──→ [CELESTIAL TREE]                                      │
            │       ├──→ [Sphere] UV_To_Sphere → Transform            │
            │       ├──→ [Nebula] Hubble → Transform → Translate      │
            │       ├──→ [Stars] StarMask → Transform → Twinkle       │
            │       ├──→ [CMB] Perlin_CMB → Tones                     │
            │       ├──→ [Planets] Moon/Mars images                    │
            │       ├──→ [Orbit] Phase → Rotate                        │
            │       └──→ Blend_Celestial (StyleCelestial)              │
            │               │                                          │
            │          [Final Color]                                    │
            │               │                                          │
            ├───────────────┴──────────────────────────────────────────┤
            │                                                           │
            ├──→ [HEIGHT] Colorize → Moon ─┬── Itto ─┬── Madoka → Buffer
            │                               │         │
            │                     Truchet_Cracks  Voronoi
            │
            ├──→ [ROUGHNESS] Colorize → Mars_Blend → Tones_Bias
            ├──→ [METALLIC] Met_Base → Veins → Stars → Tones
            ├──→ [NORMAL] Height → normal_map → detail_blend → ConvertDX
            ├──→ [AO] Height → Blur → Colorize → Tones
            ├──→ [EMISSIVE] Max(Style emissives) * $EmissiveIntensity
            ├──→ [OPACITY] Tones from Madoka warp
            └──→ [SSS] DreamGrade + Desat blend → Tones
                    │
               [Material Node]
                    │
               [Export Nodes] (Static only)
```

---

## Implementation Sequence

### Phase 1: Core Infrastructure
1. Add $GlobalSeed to Remote_MasterParams
2. Create SG_Noise_Library subgraph nodes (Perlin, Worley, Gradient, Domain Warp)
3. Create SG_Mask_Shaping subgraph nodes (Levels, S_Curve, Slope_Bias, Curvature, Distance_Field)
4. Create SG_Gradient_Remap utility
5. Add animation phase expressions to global remote

### Phase 2: PBR Engine Rework
6. Rewrite Roughness chain (base + micro + macro + bias)
7. Rewrite Metallic chain (base + mask + detail + final)
8. Rewrite Normal chain (base + detail + warp + strength)
9. Add SSS chain with proper $SSSAmount
10. Add separate emissive path from each style tree

### Phase 3: Style Tree Expansion
11. Expand Nikki tree (fabric noise, directional flow, S-curve)
12. Expand Madoka tree (SSS glow, radial fields, first-class emissive)
13. Expand Itto tree (curvature wear, high-freq breakup, erosion, strong height)
14. Expand Celestial tree (spherical projection, star twinkle, CMB, orbital motion)

### Phase 4: Static Export + Validation
15. Update validate_mm_graph.py with new required nodes
16. Run full validation
17. Generate static export variants

---

## Optimization & Tiling Safety Notes

### Performance Budget
| Component | Node Count | GPU Cost | Notes |
|-----------|------------|----------|-------|
| Input + Preprocess | 5 | Low | Single-pass scale/tones |
| Tile System | 6 | Low-Med | Kaleidoscope is the heaviest |
| Base Utility (shared) | 12 | Medium | Subgraphs only evaluated once |
| Nikki Tree | 8 | Low | Mostly Perlin + blends |
| Madoka Tree | 14 | Medium | Voronoi + warp + blurs |
| Itto Tree | 16 | Medium | Voronoi + edges + multiple blends |
| Celestial Tree | 14 | Med-High | 4 image samples + transforms |
| PBR Engine | 22 | Medium | Normal map + blurs |
| **Total Dynamic** | **~97** | **Medium** | Manageable for 2K/4K export |
| **Total Static** | **~105** | **Medium** | +export nodes |

### Tiling Safety
1. **All noise nodes use tileable variants** (Material Maker Perlin/Voronoi are inherently tileable with power-of-2 scales)
2. **Image nodes set `clamp=true`** for non-tileable NASA refs (nebula, elevation maps)
3. **Kaleidoscope + Mirror + Transform_Repeat** chain ensures seamless tiling of source
4. **Shape_Seam** provides circular blend mask for source seam hiding
5. **SeamBlend** parameter lets artist blend between tiled and original
6. **All parameter-driven transforms** use `repeat=true` where appropriate

### Memory Considerations
- NASA reference images should be 2K max for dynamic use (4K for static export)
- Blue Marble 4K is only used as SourceImage → scaled down by TileRepeat
- Blur nodes (AO, SSS): sigma ≤ 8 to keep kernel sizes reasonable
- Normal map: `param2=0` (buffer off) for final export quality per MM docs

---

## Full Parameter List (UI-Ready)

### Global Controls (Remote_MasterParams)
```
GROUP "Animation"
  BakeTime          [0-1]        default: 0      # Bake frame for static export
  AnimSpeed         [0-2]        default: 0.15   # Global animation speed
  AnimOffset        [0-1]        default: 0       # Global animation phase offset

GROUP "Style Blending"
  StyleNikki        [0-1]        default: 0.5     # Nikki tree blend weight
  StyleMadoka       [0-1]        default: 0       # Madoka tree blend weight
  StyleItto         [0-1]        default: 0       # Itto tree blend weight
  StyleCelestial    [0-1]        default: 0       # Celestial tree blend weight

GROUP "Tiling"
  TileRepeat        [0.5-8]      default: 2       # Source image tile count
  SeamBlend         [0-1]        default: 0.35    # Seam hiding blend amount
  GlobalSeed        [0-1]        default: 0.5     # Master random seed

GROUP "Nikki"
  NikkiPastelLift   [0-1]        default: 0.22    # Dreamy brightness lift
  NikkiSparkleAmount [0-1]       default: 0.35    # Sparkle intensity
  NikkiFabricDetail [0-1]        default: 0.15    # Fabric micro-breakup
  NikkiFlowStrength [0-1]        default: 0.25    # Directional flow
  NikkiSaturation   [0-2]        default: 0.8     # Color saturation

GROUP "Madoka"
  MadokaGlowAmount  [0-1]        default: 0.3     # SSS fake glow
  MadokaRadialBands [1-6]        default: 3       # Spectral rings
  MadokaRadialSpeed [0-2]        default: 0.2     # Ring animation
  MadokaEmissiveBrightness [0-5] default: 2.0     # Emissive strength
  MadokaCuteBias    [0-1]        default: 0.5     # Cute vs corrupt
  MadokaVeinEmissive [0-1]       default: 0.35    # Vein glow
  WitchBarrierWallpaperScale [1-12] default: 4    # Maze pattern scale
  WitchBarrierMazeTightness [0-1] default: 0.5   # Voronoi randomness
  WitchBarrierPhaseSpeed [0-2]   default: 0.45   # Barrier rotation speed

GROUP "Itto"
  IttoPatternScale  [1-12]       default: 3       # Ornament pattern
  IttoCrackDepth    [0-1]        default: 0.4     # Crack displacement
  IttoWearAmount    [0-1]        default: 0.4     # Curvature wear
  IttoBreakupAmount [0-1]        default: 0.25    # Surface breakup
  IttoErosionStrength [0-1]     default: 0.2     # Erosion intensity
  IttoWearDepth     [0-1]        default: 0.15    # Wear displacement
  IttoInkStrength   [0-1]        default: 0.6     # Ink line darkness

GROUP "Celestial"
  CelestialScale    [0.5-4]      default: 1.0     # Spherical projection
  CelestialNebulaScale [0-2]    default: 0.42    # Nebula frequency
  CelestialTwinkle  [0-1]        default: 0.5     # Star twinkle
  CelestialDrift    [0-1]        default: 0.1     # Starfield drift
  CelestialOrbitSpeed [0-2]     default: 0.05    # Orbit rotation
  CelestialOrbitPeriod [1-360]  default: 60      # Days/orbit
  CelestialCMBAmount [0-1]      default: 0.15    # CMB noise
  CelestialEmissiveBoost [0-5]  default: 1.5     # Nebula emissive

GROUP "PBR"
  HeightScale       [0-1]        default: 0.25    # Displacement strength
  NormalStrength    [0-2]        default: 0.8     # Normal intensity
  NormalDetail      [0-1]        default: 0.3     # Detail normal blend
  RoughnessBias     [0-1]        default: 0.55    # Roughness offset
  RoughnessContrast [0-1]        default: 0.3     # Roughness micro-detail
  MetallicAmount    [0-1]        default: 0.05    # Global metallic
  AOStrength        [0-1]        default: 0.7     # AO intensity
  AORadius          [1-10]       default: 3       # AO blur radius
  SSSAmount         [0-1]        default: 0.12    # Subsurface scattering
  EmissiveIntensity [0-5]        default: 1.0     # Global emissive brightness

GROUP "Export"
  ExportResolution  [8-12]       default: 11      # 8=256, 11=2048, 12=4096
```

---

## Subgraph Implementation Plan

Each subgraph will be a separate `.ptex` file in `Tools/MaterialMaker/Subgraphs/`:

```
Tools/MaterialMaker/Subgraphs/
├── SG_Noise_Library.ptex
│     Inputs:  seed, scale_x, scale_y
│     Outputs: Perlin, Worley, Gradient, DomainWarped, FractalSum
│
├── SG_Mask_Shaping.ptex
│     Inputs:  input_mask, contrast, pivot, edge_size
│     Outputs: Hard, Soft, Edge, Curvature, Radial
│
├── SG_Triplanar.ptex
│     Inputs:  color, normal, height
│     Outputs: Color_Blended, Normal_Blended, Height_Blended
│
├── SG_Gradient_Remap.ptex
│     Inputs:  input, gradient_preset
│     Outputs: Remapped_Color, Remapped_Gray
│
├── SG_Flow_Generator.ptex
│     Inputs:  seed, scale, speed, strength
│     Outputs: FlowVector, FlowStrength, FlowTime
│
└── SG_Spherical_Projection.ptex
      Inputs:  uv_in, scale, rotate
      Outputs: Spherical_UV, Sphere_Mask, LatLon_Coords
```

These subgraphs are referenced via Material Maker's `node: type=graph` mechanism with `filename` pointing to the subgraph `.ptex`.

---

## Migration Path from Current Version

1. ✅ Validate current graph passes structural checks (it does - see validate_mm_graph.py)
2. 🔄 Add GlobalSeed parameter to Remote (Phase 1)
3. 🔄 Build subgraph files (Phase 1)
4. 🔄 Expand style trees with new node chains (Phase 3)
5. 🔄 Rewrite PBR lane with micro-detail layering (Phase 2)
6. 🔄 Add animation control layer expressions (Phase 1)
7. 🔄 Generate new static + dynamic variants
8. 🔄 Update validation script with new node requirements
9. 🔄 Run full validation pipeline
