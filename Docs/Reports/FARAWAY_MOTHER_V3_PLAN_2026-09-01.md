# Faraway Mother V3 — Expanded Plan: Walkways, Frills & Feminine Ornaments

**Date:** 2026-09-01
**Version:** 3.0 (Infinity Nikki Lens)
**Core thesis:** Fabric behaves as geography; landscape is draped anatomy; ornaments bridge the gap between textile, terrain and foliage.

---

## 1. Infinity Nikki Design Principles Applied

### 1.1 Outfit Abilities as Exploration Verbs

| Outfit | Ontology | Exploration Verb |
|--------|----------|------------------|
| **Shorelistener** | "the world is water" | Tide Seams / impossible-water attunement |
| **Hemkeeper** | "the world is fabric" | Tension / seam / fold interpretation |
| **Glasswing Courier** | "the world is air / adjacency" | Wayfold alignment and spatial continuity |
| **Mire Apothecary** | "the world is material state" | Catalyze / residue / membrane state changes |

### 1.2 Cloth Tier System (from Infinity Nikki interview)

| Tier | Method | Use For |
|------|--------|---------|
| **A — Rigid authored** | Bones / Control Rig / AnimDynamics | Structured bodices, stiff coat panels, equipment straps |
| **B — Chaos Cloth** | Chaos Cloth | Listening hem, soft skirts/capes with meaningful collision |
| **C — Shader/WPO** | World Position Offset | Distant cloth geography, banner fields, prayer strips, grass/fiber response |
| **D — Offline Houdini bake** | Vellum/VAT/cache | Kilometer-scale draped anatomy, impossible contraction events |

### 1.3 WPO vs Chaos Cost Ladder

```
Material/WPO → if insufficient → Niagara/instanced motion → if insufficient →
simple authored transform/spline → if insufficient → Chaos physics → if insufficient →
prebaked Houdini simulation/VAT → if insufficient → custom runtime solution
```

### 1.4 Niagara as Field Evidence

- Dust/fibers trace tension vectors
- Loose threads align before landscape fold responds
- Prayer-strip microfibers show delayed pull phase
- Particles reveal the field the player cannot otherwise see

---

## 2. Mathematical Foundation

### 2.1 Terrain Heightfield Generation

**Base heightfield equation (Houdini HeightField):**

```
H(x,y) = Σ [ A_i * sin(ω_i * x + φ_i) * cos(ω_i * y + ψ_i) ] + T(x,y) + W(x,y)
```

Where:
- `A_i` = amplitude of frequency band i
- `ω_i` = angular frequency (2π/λ)
- `φ_i, ψ_i` = phase offsets
- `T(x,y)` = tectonic uplift function
- `W(x,y)` = weathering/erosion function

**Fabric fold noise (for terrain surface):**

```
F(x,y) = |sin(x * f_fold)|^p_sharpness + turbulence(x,y, octaves=6)
```

Where:
- `f_fold` = fold frequency (0.01–0.1 for km scale)
- `p_sharpness` = fold sharpness exponent (2.0–8.0)
- `turbulence` = Perlin noise sum

**Complete terrain with fabric folds:**

```
Terrain(x,y) = H_base(x,y) * (1 - mask_fabric) + F(x,y) * mask_fabric * fold_depth
```

### 2.2 Multi-Frequency WPO Stack

**Layer 1 — Macro Swell (km scale):**

```
W_macro(x,y,t) = sin(x * 0.001 * 2π + t * 0.5) * cos(y * 0.001 * 2π + t * 0.3) * A_macro
```

- Wavelength: 1 km
- Amplitude: 50–100 m
- Frequency: 0.001 rad/m

**Layer 2 — Medium Folds (100m scale):**

```
W_med(x,y,t) = sin(x * 0.01 * 2π + noise(x,y) + t * 0.3) * cos(y * 0.008 * 2π + t * 0.2) * A_med
```

- Wavelength: 100 m
- Amplitude: 10–20 m
- Frequency: 0.01 rad/m

**Layer 3 — Micro Detail (1m scale):**

```
W_micro(x,y,t) = noise(x * 0.1, y * 0.1) * height_map_sample(x,y) * beat_pulse * A_micro
```

- Wavelength: 1 m
- Amplitude: 0.5–2 m
- Frequency: 0.1 rad/m

**Layer 4 — Wind Response (dynamic):**

```
W_wind(x,y,t) = dot(wind_dir, vec2(x,y)) * t * turbulence(x,y, t) * wind_strength
```

**Combined WPO:**

```
W_total = W_macro + W_med + W_micro + W_wind
```

### 2.3 Fabric Weave Mathematics (Copernicus)

**Satin core (warp/weft):**

```
weave(u,v) = sin(u * 2π * N_warp) * cos(v * 2π * N_weft)
twist(u,v) = sin((u + v) * 0.00008 + sin(uv * 15) * 2.5)
```

**Nacre (3-layer pearl):**

```
nacre(u,v) = sin(u * 0.018) * sin(v * 0.018) + sin(u * 0.009 + v * 0.009) * 0.5 + sin(u * 0.006 - v * 0.006) * 0.25
```

**Lace SDF motifs:**

```
floral(θ,r) = cos(θ * 5) * smoothstep(0.3, 0.7, r)
diamond(u,v) = 1 - (|u| + |v|) * 0.85
star(θ) = cos(θ * 4) * 0.5 + cos(θ * 8) * 0.3
```

### 2.4 Tension/Seam Graph

**Catenary curve (draped cloth between anchors):**

```
y(x) = a * cosh((x - x₀) / a) + y₀
```

Where `a` = tension parameter (lower = more sag).

**Seam generation:**

```
seam(t) = Σ [ B_i * t^i * (1-t)^(3-i) ]  (cubic Bézier)
```

With control points `B_i` derived from tension anchors.

---

## 3. Expanded Asset Categories

### 3.1 Walkways (Fabric Paths)

**Concept:** Paths that are simultaneously fabric and terrain — the player walks on draped cloth that has become geography.

| Asset | Description | Dimensions | Material |
|-------|-------------|------------|----------|
| `SM_FabricWalkway_Straight` | Straight fabric path segment | 200m × 20m × 0.5m | GildedLoom |
| `SM_FabricWalkway_Curved` | Curved fabric path (90° arc) | 200m radius × 20m | SilkWaterfall |
| `SM_FabricWalkway_Bridge` | Suspended fabric bridge | 500m × 15m | CelestialSilkJacquard |
| `SM_FabricWalkway_Ribbon` | Narrow ribbon path (player-width) | 1000m × 3m | NightSkyVelvet |
| `SM_FabricWalkway_Folded` | Folded fabric creating stairs | 100m × 20m × 30m | GildedAcanthusBrocade |

**Mathematical walkway generation:**

```
walkway_centerline(t) = spline(t, control_points)
walkway_width(t) = base_width * (1 + 0.3 * sin(t * frequency))
walkway_surface(u,v) = centerline(u) + normal(u) * (v - 0.5) * width(u)
walkway_height(u,v) = terrain_height(u,v) + fabric_drape(u,v) * fold_amplitude
```

### 3.2 Frills as Rocks (Fabric-Geology Hybrids)

**Concept:** Rock formations that are actually frozen fabric — frills, ruffles and pleats that have become stone.

| Asset | Description | Dimensions | Material |
|-------|-------------|------------|----------|
| `SM_FrillRock_Monolith` | Tall frill monolith | 50m × 20m × 80m | CarvedAlabasterWood |
| `SM_FrillRock_Cluster` | Cluster of small frill rocks | 30m × 30m × 15m | GildedAcanthusBrocade |
| `SM_FrillRock_Arch` | Frill arch (walk-through) | 40m × 15m × 50m | NightSkyVelvet |
| `SM_FrillRock_Spire` | Thin frill spire | 10m × 10m × 100m | CelestialSilkJacquard |
| `SM_FrillRock_Boulder` | Round frill boulder | 20m × 20m × 20m | NacreMusicBoxJewel |

**Frill rock generation (Houdini SOP):**

```
frill_profile(r, θ) = r * (1 + amplitude * sin(frequency * θ + phase))
frill_height(h) = h * (1 - h/H_max)^decay  (taper toward top)
frill_surface(r, θ, h) = frill_profile(r, θ) * frill_height(h)
```

**Pleat formation:**

```
pleat(x,y) = |sin(x * f_pleat)|^p_pleat * depth
pleat_rock(x,y,z) = base_rock(x,y,z) + pleat(x,y) * mask_rock_surface
```

### 3.3 Feminine Ornaments (Fabric-Terrain-Foliage Bridges)

**Concept:** Decorative elements that blend the three worlds — textile patterns that grow like plants, terrain features that drape like cloth, foliage that sparkles like jewelry.

| Asset | Description | Type | Material |
|-------|-------------|------|----------|
| `SM_Ornament_LaceTree` | Tree with lace canopy | Foliage-Fabric | AquaticLullabyLace |
| `SM_Ornament_PearlBush` | Bush with pearl-like berries | Foliage-Jewel | NacreMusicBoxJewel |
| `SM_Ornament_SilkVine` | Vine with silk ribbon leaves | Foliage-Fabric | CelestialSilkJacquard |
| `SM_Ornament_VelvetMoss` | Moss with velvet texture | Terrain-Fabric | NightSkyVelvet |
| `SM_Ornament_BrocadeFlower` | Flower with brocade petals | Foliage-Fabric | GildedAcanthusBrocade |
| `SM_Ornament_CrystalFrill` | Crystal formation with frill edges | Terrain-Fabric | GildedLoom |
| `SM_Ornament_LaceFence` | Fence of lace panels | Structure-Fabric | AquaticLullabyLace |
| `SM_Ornament_PearlChain` | Hanging pearl chain | Structure-Jewel | NacreMusicBoxJewel |

**Lace tree generation:**

```
trunk(r, θ, h) = r * (1 - h/H_tree) * (1 + 0.1 * sin(θ * 5))
canopy(r, θ, h) = lace_sdf(r, θ) * smoothstep(H_tree * 0.6, H_tree, h)
leaves(r, θ, h) = scatter(canopy, density=0.3) * pearl_mask(r, θ)
```

**Pearl bush:**

```
bush_base(r, θ, h) = r * (1 - h/H_bush)^2
pearl_positions = poisson_disk_sample(bush_surface, min_dist=0.5)
pearl(p) = sphere(r_pearl) * nacre_material(p)
```

**Silk vine:**

```
vine_path(t) = catenary(t, anchors) + wind_sway(t, wind_dir)
vine_ribbon(t, θ) = ribbon_width(t) * sin(θ * 2π) * silk_material
```

### 3.4 Expanded GN Builders (8 → 16)

**New builders for V3:**

| Builder | Function | Key Params |
|---------|----------|------------|
| `MEL_mother_walkway_straight` | Straight fabric walkway | Length, Width, Fold Depth |
| `MEL_mother_walkway_curved` | Curved fabric walkway | Radius, Angle, Width |
| `MEL_mother_frill_rock` | Frill rock formation | Height, Frill Count, Depth |
| `MEL_mother_frill_arch` | Frill arch | Span, Height, Thickness |
| `MEL_mother_lace_tree` | Lace canopy tree | Height, Canopy Size, Lace Density |
| `MEL_mother_pearl_bush` | Pearl bush | Size, Pearl Count, Density |
| `MEL_mother_silk_vine` | Silk vine | Length, Sag, Ribbon Width |
| `MEL_mother_brocade_flower` | Brocade flower | Petal Count, Size, Curl |

---

## 4. Houdini Execution Spec (V3)

### 4.1 Folder Structure

```
Exports/Houdini/FarawayMother/
  Walkways/
    SM_FabricWalkway_Straight.fbx
    SM_FabricWalkway_Curved.fbx
    SM_FabricWalkway_Bridge.fbx
    SM_FabricWalkway_Ribbon.fbx
    SM_FabricWalkway_Folded.fbx
  FrillRocks/
    SM_FrillRock_Monolith.fbx
    SM_FrillRock_Cluster.fbx
    SM_FrillRock_Arch.fbx
    SM_FrillRock_Spire.fbx
    SM_FrillRock_Boulder.fbx
  Ornaments/
    SM_Ornament_LaceTree.fbx
    SM_Ornament_PearlBush.fbx
    SM_Ornament_SilkVine.fbx
    SM_Ornament_VelvetMoss.fbx
    SM_Ornament_BrocadeFlower.fbx
    SM_Ornament_CrystalFrill.fbx
    SM_Ornament_LaceFence.fbx
    SM_Ornament_PearlChain.fbx

Content/EnvSandbox/Monoliths/FarawayMother/
  Prototype/LV_FarawayMother_Prototype.umap
  Walkways/
  FrillRocks/
  Ornaments/

Content/EnvSandbox/Landscapes/FarawayMother/
  LM_FarawayMother_Terrain.uasset
  LM_FarawayMother_Walkway_Heightfield.raw

Content/EnvSandbox/Materials/Masters/
  M_FabricMountain_Master.uasset
  M_FrillRock_Master.uasset
  M_Ornament_Master.uasset

Content/EnvSandbox/Materials/Functions/
  MF_FabricMountainWPO.uasset
  MF_FabricTensionMask.uasset
  MF_FrillRockFolds.uasset
  MF_OrnamentGrowth.uasset

Content/EnvSandbox/Materials/Instances/FarawayMother/
  Walkways/MI_FabricWalkway_*.uasset (5 instances)
  FrillRocks/MI_FrillRock_*.uasset (5 instances)
  Ornaments/MI_Ornament_*.uasset (8 instances)

Content/EnvSandbox/PCG/FarawayMother/
  PCG_Faraway_FabricRidge.uasset
  PCG_Faraway_DetailProps.uasset
  PCG_Faraway_WindZones.uasset
  PCG_Faraway_WalkwayScatter.uasset
  PCG_Faraway_FrillScatter.uasset
  PCG_Faraway_OrnamentScatter.uasset

Saved/Audit/houdini_faraway_mother/
  walkway_manifest.json
  frillrock_manifest.json
  ornament_manifest.json
```

### 4.2 HDA Cook Order (V3)

**Tier 0 — Foundation (existing):**
1. Corset (GildedAcanthusBrocade) — Subtle Sheen
2. Cradle (CarvedAlabasterWood) — Subtle Sheen

**Tier 1 — Mid (existing):**
3. Gown (CelestialSilkJacquard) — Moderate Sheen
4. Mantle (NightSkyVelvet) — Moderate Sheen

**Tier 2 — Complex (existing):**
5. Ornament (NacreMusicBoxJewel) — Strong Sheen
6. Veil (AquaticLullabyLace) — Strong Sheen + Alpha

**Tier 3 — Walkways (new):**
7. HDA_P1_TensionValley (walkway base)
8. HDA_P1_SeamGraph (walkway seams)
9. HDA_P1_BannerPrayerStripField (walkway edges)

**Tier 4 — Frill Rocks (new):**
10. HDA_P2_MoltLayerFamily (frill state variants)
11. HDA_P2_MoltRavine (frill terrain integration)

**Tier 5 — Ornaments (new):**
12. HDA_CH_WardrobeIntersectionAudit (lace tree canopy)
13. HDA_ENV_SemanticMaskPack (ornament placement masks)

### 4.3 Data Contract (V3)

**From Houdini → Unreal:**

```json
{
  "schema": "melodia_faraway_mother_v3",
  "asset_id": "SM_FabricWalkway_Straight",
  "category": "walkway",
  "generator": "HDA_P1_TensionValley_v001",
  "source": "Saved/Audit/copernicus/surreal_cobble_AshenGilded.hip",
  "outputs": {
    "mesh": "Exports/Houdini/FarawayMother/Walkways/SM_FabricWalkway_Straight.fbx",
    "textures": [
      "Content/Textures/FarawayMother_Suites/T_FarawayMother_Corset_GildedAcanthusBrocade_BC.png"
    ],
    "manifest": "Saved/Audit/houdini_faraway_mother/walkway_manifest.json"
  },
  "params": {
    "length": 200.0,
    "width": 20.0,
    "fold_depth": 0.5,
    "fold_frequency": 0.01,
    "tension": 0.7,
    "sag": 0.3
  },
  "materials": {
    "master": "M_Master_Nikki",
    "instance": "MI_FabricWalkway_Straight",
    "sheen_setup": "subtle"
  }
}
```

**From Unreal → Houdini:**

```json
{
  "schema": "melodia_faraway_mother_input_v3",
  "spline_path": "/Game/EnvSandbox/Maps/LV_FarawayMother_Prototype.Spline_Walkway_01",
  "terrain_heightfield": "/Game/EnvSandbox/Landscapes/FarawayMother/LM_FarawayMother_Terrain",
  "reveal_camera": "/Game/EnvSandbox/Maps/LV_FarawayMother_Prototype.CineCamera_Reveal",
  "tension_anchors": [
    {"position": [0, 0, 0], "break_probability": 0.0},
    {"position": [100, 0, 5], "break_probability": 0.1},
    {"position": [200, 0, 0], "break_probability": 0.0}
  ]
}
```

---

## 5. Material Stack (V3)

### 5.1 Master Materials

| Master | Purpose | Key Features |
|--------|---------|--------------|
| `M_FabricMountain_Master` | Base terrain | Landscape params, fabric fold WPO, tension mask |
| `M_FrillRock_Master` | Frill rocks | Pleat deformation, weathering, fabric-to-stone blend |
| `M_Ornament_Master` | Ornaments | Subsurface scattering, pearl iridescence, growth animation |

### 5.2 Material Functions

| Function | Purpose | Inputs |
|----------|---------|--------|
| `MF_FabricMountainWPO` | 4-layer WPO stack | UV, Time, CymaticAmplitude, BassIntensity, MidIntensity, BeatPulse, WindStrength, WindSpeed, WindDirection, FoldingAmount, HeightMap, MountainScale |
| `MF_FabricTensionMask` | Curvature-based stretch mask | World Position, Normal, Curvature |
| `MF_FrillRockFolds` | Pleat deformation | UV, Fold Frequency, Fold Depth, Sharpness |
| `MF_OrnamentGrowth` | Growth animation | Time, Growth Rate, Curl, Phase |
| `MF_PearlIridescence` | Pearl surface | View Angle, Light Direction, Base Color, Iridescence Strength |

### 5.3 Sheen Setups (from Infinity Nikki fabric research)

| Setup | SheenWidth | SheenBias | bUsesNormal | RoughnessMax | Metallic |
|-------|------------|-----------|-------------|--------------|----------|
| Subtle (Corset, Cradle) | 0.25 | 0.5 | False | 1.0 | 0.0 |
| Moderate (Gown, Mantle) | 0.75 | 0.5 | True | 0.8 | 0.1 |
| Strong (Ornament, Veil) | 1.5 | 0.5 | True | 0.6 | 0.05 |

---

## 6. Implementation Phases (V3)

### Phase 1: Terrain + Walkways (Session A)

1. Generate 8192×8192 heightfield with fabric fold noise
2. Export 16-bit RAW, import to UE Landscape
3. Create `M_FabricMountain_Master` with WPO stack
4. Create 5 walkway MIs
5. Place walkway spline actors in level
6. PCG scatter for walkway edges

### Phase 2: Frill Rocks (Session B)

1. Cook HDA_P2_MoltLayerFamily for frill state variants
2. Create `M_FrillRock_Master` with pleat deformation
3. Create 5 frill rock MIs
4. Place frill rock formations in level
5. PCG scatter for frill rock clusters

### Phase 3: Ornaments (Session C)

1. Cook HDA_CH_WardrobeIntersectionAudit for lace tree canopy
2. Create `M_Ornament_Master` with subsurface + iridescence
3. Create 8 ornament MIs
4. Place ornaments in level
5. PCG scatter for ornament distribution

### Phase 4: Integration + Reveal (Session D)

1. Camera reveal validation
2. Material state test (local interaction → distant response)
3. Performance capture (target 60 FPS on RTX 3070+)
4. Contact sheet render of all 18 new assets

---

## 7. Success Criteria (V3)

- [ ] 8 km × 8 km fabric terrain visible in LV_FarawayMother_Prototype
- [ ] 5 walkway segments placed and textured
- [ ] 5 frill rock formations placed and textured
- [ ] 8 ornament assets placed and textured
- [ ] WPO animation: macro swell + medium folds + micro detail
- [ ] All 6 original fabric suites integrated
- [ ] 16 GN builders placed and scaled
- [ ] 6 PCG graphs active
- [ ] 60 FPS on target hardware (RTX 3070+)
- [ ] No z-fade or WPO artifacts at distance
- [ ] Contact sheet render of all 18 assets

---

## 8. File Inventory (V3 Complete)

### To Create (New)

**Meshes (18):**
- `Content/EnvSandbox/Monoliths/FarawayMother/Walkways/SM_FabricWalkway_*.uasset` (5)
- `Content/EnvSandbox/Monoliths/FarawayMother/FrillRocks/SM_FrillRock_*.uasset` (5)
- `Content/EnvSandbox/Monoliths/FarawayMother/Ornaments/SM_Ornament_*.uasset` (8)

**Materials (18 instances + 3 masters + 5 functions):**
- `Content/EnvSandbox/Materials/Masters/M_FabricMountain_Master.uasset`
- `Content/EnvSandbox/Materials/Masters/M_FrillRock_Master.uasset`
- `Content/EnvSandbox/Materials/Masters/M_Ornament_Master.uasset`
- `Content/EnvSandbox/Materials/Functions/MF_FabricMountainWPO.uasset`
- `Content/EnvSandbox/Materials/Functions/MF_FabricTensionMask.uasset`
- `Content/EnvSandbox/Materials/Functions/MF_FrillRockFolds.uasset`
- `Content/EnvSandbox/Materials/Functions/MF_OrnamentGrowth.uasset`
- `Content/EnvSandbox/Materials/Functions/MF_PearlIridescence.uasset`
- `Content/EnvSandbox/Materials/Instances/FarawayMother/Walkways/MI_FabricWalkway_*.uasset` (5)
- `Content/EnvSandbox/Materials/Instances/FarawayMother/FrillRocks/MI_FrillRock_*.uasset` (5)
- `Content/EnvSandbox/Materials/Instances/FarawayMother/Ornaments/MI_Ornament_*.uasset` (8)

**PCG (6):**
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_FabricRidge.uasset`
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_DetailProps.uasset`
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_WindZones.uasset`
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_WalkwayScatter.uasset`
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_FrillScatter.uasset`
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_OrnamentScatter.uasset`

**Level:**
- `Content/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype.umap`

### To Modify

- `Source/MelodiaShader/Shaders/MelodiaNikkiCommon.ush` — add fabric WPO + frill fold helpers
- `deploy/surreal_arch/melodia_gn/mother.py` — add 8 new GN builders + export-to-UE function

### To Use As-Is

- `Saved/Audit/copernicus_cymatic/GildedLoom/` — gold fabric PBR
- `Saved/Audit/copernicus_cymatic/SilkWaterfall/` — silk PBR
- `Saved/Audit/copernicus_cymatic/CherryBlossomWood/` — organic PBR
- `Content/EnvSandbox/Materials/Instances/Glitter/` — glitter MIs
- `Source/.../MelodiaCymaticsSubsystem` — audio→geometry Chladni

---

*V3 Plan complete. 18 new assets across 3 categories. Mathematical formulas for terrain, WPO, weave, lace, frill and ornament generation. Houdini cook order with 5 tiers. Infinity Nikki design principles integrated throughout.*
