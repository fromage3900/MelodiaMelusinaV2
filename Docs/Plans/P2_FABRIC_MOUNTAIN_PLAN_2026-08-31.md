# P2 Plan — Faraway Mother: Large-Scale Fabric Mountains

**Date:** 2026-08-31  
**Status:** Research complete — ready for implementation  
**Core thesis:** Fabric behaves like geography; landscape is draped anatomy.

---

## 1. Current State

### What Exists
| Asset | Location | Status |
|-------|----------|--------|
| 8 Faraway Mother GN builders | `deploy/surreal_arch/melodia_gn/mother.py` | Built, not placed in level |
| Faraway Mother HDAs | `Tools/Houdini/copernicus/hda_variants/` | 6 HDAs (faraway_p2_corset, cradle, gown, mantle, ornament, veil) |
| Copernicus fabric scripts | `Tools/Houdini/pearl_*.py` | AAA pearl/lace generators |
| PBR fabric maps (11 variants) | `Saved/Audit/copernicus_cymatic/` | GildedLoom, SilkWaterfall, CherryBlossomWood, etc. |
| WPO material functions | `Source/MelodiaShader/Shaders/MelodiaNikkiCommon.ush` | MF_NikkiSquishWPO, MF_ClothWindDrape |
| KelpSway WPO | `Content/EnvSandbox/Textures/` | LUT-driven WPO for underwater foliage |
| LV_FarawayMother_Prototype | `Content/EnvSandbox/Monoliths/FarawayMother/Prototype/` | Empty level, no PCG |

### What's Missing
- No VDM (Vector Displacement Mesh) support in project
- No large-scale fabric mountain geometry
- No WPO-driven fabric deformation at landscape scale
- No PCG graphs for fabric mountain scatter
- No material instances for fabric mountain terrain

---

## 2. Architecture: Fabric Mountain System

### 2.1 Geometry Layers (GN Builders → Houdini → UE)

```
Layer 1: Base Terrain (Houdini heightfield → UE Landscape)
    ↓
Layer 2: Fabric Folds (GN builders: fabric_ridge, shoulder_fold, valley_depression)
    ↓
Layer 3: Detail Scatter (PCG: rocks, coral, kelp, glitter)
    ↓
Layer 4: WPO Animation (Material functions: wind, breathing, wave)
```

### 2.2 WPO Strategy for Fabric Mountains

**Problem:** Kilometer-scale fabric needs to ripple, breathe, and respond to wind without tessellation overhead.

**Solution:** Multi-frequency WPO stack

| WPO Layer | Function | Frequency | Amplitude |
|-----------|----------|-----------|-----------|
| Macro swell | `sin(worldpos.x * 0.001 + time) * cos(worldpos.y * 0.001)` | 1 km wavelength | 50-100 m |
| Medium folds | `sin(worldpos.x * 0.01 + noise) * cos(worldpos.y * 0.008)` | 100 m wavelength | 10-20 m |
| Micro detail | `noise(worldpos * 0.1) * height_map_sample` | 1 m wavelength | 0.5-2 m |
| Wind response | `dot(wind_dir, worldpos.xz) * time * turbulence` | Dynamic | Scalable |

**Implementation:** Chain WPO in material function:
```
MF_FabricMountainWPO = 
    MacroSwell + MediumFolds + MicroDetail + WindResponse
```

### 2.3 Material Stack

**Base Material:** `M_Master_Nikki_Landscape` (already has landscape params)

**Fabric Override Parameters:**
- `FabricFoldStrength` — controls fold depth (0-1)
- `FabricFoldFrequency` — controls fold density (1-20)
- `FabricWindResponse` — controls wind sensitivity (0-1)
- `FabricTensionMask` — mask for stretched vs compressed areas
- `FabricWearAmount` — edge wear and fray

**Texture Maps from Copernicus Pipeline:**
| Map | Source Variant | Usage |
|-----|---------------|-------|
| BaseColor | GildedLoom | Gold fabric regions |
| Normal | SilkWaterfall | Water-like silk flow |
| Roughness | CherryBlossomWood | Organic variation |
| Height | GildedLoom | Fold relief |
| Emissive | DancingCrystals | Bioluminescent threads |
| Iridescence | FinalDreamweaver | Shifting colors |

---

## 3. Implementation Plan

### Phase 1: Houdini Heightfield → Landscape (Tonight)

1. **Generate base heightfield** in Houdini:
   - 8192×8192 resolution (8 km × 8 km at 1 uu/m)
   - Fabric fold noise: `abs(sin(x * freq)) ^ sharpness + turbulence`
   - Export as 16-bit RAW

2. **Import to UE Landscape:**
   - Create `LM_FarawayMother_Terrain` in `LV_FarawayMother_Prototype`
   - 8192×8192 resolution, 1 component, 63 sections
   - Assign `M_FabricMountain_Master`

3. **Material Instance:**
   - Create `MI_FabricMountain_Base` on `M_Master_Nikki_Landscape`
   - Wire Copernicus PBR maps (GildedLoom, SilkWaterfall, CherryBlossomWood)
   - Set WPO params: MacroSwell=0.3, MediumFolds=0.5, MicroDetail=0.2

### Phase 2: GN Builder Placement (Tonight)

Place 8 GN builders in level:

| Builder | Location | Scale | Purpose |
|---------|----------|-------|---------|
| MEL_mother_head_silhouette | (0, 0, 500) | 10× | Distant mountain silhouette |
| MEL_mother_hair_cascade | (2000, 0, 200) | 5× | Waterfall fabric cascade |
| MEL_mother_valley_depression | (0, 0, 0) | 8× | Central valley |
| MEL_mother_fog_volume | (0, 0, 100) | 20× | Atmospheric haze |
| MEL_mother_fabric_ridge | (-1000, 0, 300) | 6× | Fabric ridge terrain |
| MEL_mother_shoulder_fold | (500, 0, 150) | 4× | Shoulder fold |
| MEL_mother_heart_gate | (0, 0, 0) | 1× | Rhythm checkpoint |
| MEL_mother_landing_zone | (0, 500, 0) | 2× | Player landing area |

### Phase 3: PCG Scatter (Tomorrow)

Create PCG graphs for:
- `PCG_Faraway_FabricRidge` — scatter fabric ridge meshes along terrain
- `PCG_Faraway_DetailProps` — scatter rocks, coral, kelp, glitter
- `PCG_Faraway_WindZones` — define wind response zones

### Phase 4: WPO Animation (Tomorrow)

1. **Create `MF_FabricMountainWPO`:**
   - Input: World Position, Time, Wind Direction, Wind Strength
   - Output: WPO (float3), NormalOffset (float3)
   - Layers: MacroSwell + MediumFolds + MicroDetail + WindResponse

2. **Create `MF_FabricTensionMask`:**
   - Use curvature analysis to find stretched vs compressed areas
   - Output: mask for material variation

3. **Wire to `M_FabricMountain_Master`:**
   - Add WPO output to material property
   - Add tension mask to roughness/emissive

### Phase 5: Integration with Existing Systems

1. **Copernicus PBR Maps:**
   - Import GildedLoom, SilkWaterfall, CherryBlossomWood textures
   - Create material instances with fabric-specific params
   - Blend based on terrain slope/curvature

2. **Glitter Materials:**
   - Place glitter piles at key visual points
   - Use `MI_GlitterGold` for gold fabric regions
   - Use `MI_GlitterIridescent` for shifting color regions

3. **Jellyfish Integration:**
   - Place `BP_Jelly_SeaAbove` instances near fabric mountains
   - Scale: 0.0001 (current) or re-export at correct units
   - Add WPO to jelly bell for pulse animation

---

## 4. Technical Challenges + Solutions

| Challenge | Solution |
|-----------|----------|
| WPO at km scale causes z-fade | Use tessellation + WPO hybrid; tessellate near camera |
| Fabric fold noise tiling | Use world-space noise (not UV); multiple octaves |
| Landscape material complexity | Use material layers; blend by slope/curvature |
| GN builder performance | Use ISM (Instanced Static Mesh) for repeated elements |
| No VDM support | Use high-poly meshes + WPO instead of VDM |
| Memory for 8K textures | Use virtual textures; stream by distance |

---

## 5. File Inventory

### To Create
- `Content/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype.umap`
- `Content/EnvSandbox/Landscapes/FarawayMother/LM_FarawayMother_Terrain.uasset`
- `Content/EnvSandbox/Materials/Masters/M_FabricMountain_Master.uasset`
- `Content/EnvSandbox/Materials/Functions/MF_FabricMountainWPO.uasset`
- `Content/EnvSandbox/Materials/Instances/FarawayMother/MI_FabricMountain_Base.uasset`
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_FabricRidge.uasset`
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_DetailProps.uasset`

### To Modify
- `Source/MelodiaShader/Shaders/MelodiaNikkiCommon.ush` — add fabric WPO helpers
- `deploy/surreal_arch/melodia_gn/mother.py` — add export-to-UE function

### To Use As-Is
- `Saved/Audit/copernicus_cymatic/GildedLoom/` — gold fabric PBR
- `Saved/Audit/copernicus_cymatic/SilkWaterfall/` — silk PBR
- `Saved/Audit/copernicus_cymatic/CherryBlossomWood/` — organic PBR
- `Content/EnvSandbox/Materials/Instances/Glitter/` — glitter MIs

---

## 6. Success Criteria

- [ ] 8 km × 8 km fabric terrain visible in LV_FarawayMother_Prototype
- [ ] WPO animation: macro swell + medium folds + micro detail
- [ ] 8 GN builders placed and scaled
- [ ] Copernicus PBR maps blended on terrain
- [ ] Glitter materials placed at key points
- [ ] 60 FPS on target hardware (RTX 3070+)
- [ ] No z-fade or WPO artifacts at distance

---

*Generated 2026-08-31 from research of Faraway Mother HDAs, Copernicus scripts, and existing WPO systems.*
