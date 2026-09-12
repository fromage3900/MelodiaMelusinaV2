# P2 Faraway Mother — Audio-Reactive Surreal Fabric Mountain System

**Date:** 2026-08-31  
**Status:** Research complete — implementation plan ready  
**Core thesis:** Fabric mountains that breathe, pulse, and ripple with the music — geography as living anatomy.

---

## 1. Research Summary

### Available Systems

| System | Location | Status | Audio Reactive? |
|--------|----------|--------|-----------------|
| UMelodiaCymaticsSubsystem | Source/MelodiaIntegration/ | Implemented, read-only | YES — reads MPC BeatPulse/BassIntensity |
| UMelodiaAudioReactivePresentationSubsystem | Source/MelodiaIntegration/ | Implemented | YES — publishes MPC_Melodia_Palette |
| MF_ClothWindDrape | Content/Python/ | Implemented | NO — manual wind params |
| MF_NikkiSquishWPO | Source/MelodiaShader/ | Implemented | NO — manual squish |
| T_SeaAbove_KelpSway_LUT | Content/Textures/ | Implemented | NO — LUT-driven |
| 8 Faraway Mother GN Builders | deploy/surreal_arch/melodia_gn/mother.py | Built, not placed | NO |
| 11 Copernicus PBR fabric variants | Saved/Audit/copernicus_cymatic/ | Baked | NO |
| 5 Glitter material instances | Content/EnvSandbox/Materials/Instances/Glitter/ | Created | NO |
| HDA_P1_SeamGraph | Tools/Houdini/copernicus/hda_variants/ | Present | NO |
| PCG graphs (127+) | Content/EnvSandbox/PCG/ | Built | NO |

### Key Insight

The **Cymatics subsystem already reads audio** and produces Chladni standing-wave patterns. We can use this to drive WPO on fabric mountains — making the mountains literally pulse and deform with the music.

---

## 2. Architecture: Audio-Reactive Fabric Mountains

### 2.1 Signal Flow

```
Music Clock (128 BPM)
    ↓
UMelodiaAudioReactivePresentationSubsystem
    ↓ publishes
MPC_Melodia_Palette (BeatPulse, BassIntensity, RhythmPulse, MidIntensity)
    ↓ read by
UMelodiaCymaticsSubsystem
    ↓ produces
Chladni standing-wave amplitude (n,m modes driven by audio bands)
    ↓ drives
MF_FabricMountainWPO (new material function)
    ↓ applied to
M_FabricMountain_Master → MI_FabricMountain_Base
    ↓ renders
Fabric mountains that breathe, pulse, and ripple with music
```

### 2.2 WPO Stack (4 Layers)

| Layer | Source | Frequency | Amplitude | Audio Source |
|-------|--------|-----------|-----------|--------------|
| **Macro swell** | Cymatics Chladni (n=2,m=3) | 1 km wavelength | 50-100 m | BassIntensity |
| **Medium folds** | Cymatics Chladni (n=5,m=7) | 100 m wavelength | 10-20 m | MidIntensity |
| **Micro detail** | Copernicus height maps | 1 m wavelength | 0.5-2 m | BeatPulse |
| **Wind response** | MF_ClothWindDrape | Dynamic | Scalable | RhythmPulse |

### 2.3 Cymatics-Driven WPO Formula

```hlsl
// In MF_FabricMountainWPO material function:

// Read Cymatics values (available via MPC or direct subsystem call)
float cymaticAmp = SampleCymaticAmplitude(worldPos.x / MOUNTAIN_SCALE, worldPos.y / MOUNTAIN_SCALE);
int n, m;
GetCymaticMode(n, m);  // driven by BassIntensity, MidIntensity

// Macro swell: Chladni standing wave
float macroSwell = cymaticAmp * BassIntensity * MACRO_AMPLITUDE;

// Medium folds: higher-frequency Chladni
float mediumFolds = sin(worldPos.x * MEDIUM_FREQ + time * MEDIUM_SPEED) 
                  * cos(worldPos.y * MEDIUM_FREQ * 0.8) 
                  * MidIntensity * MEDIUM_AMPLITUDE;

// Micro detail: Copernicus height map sample
float microDetail = tex2D(HeightMap, worldPos.xy * MICRO_TILE).r * BeatPulse * MICRO_AMPLITUDE;

// Wind response: existing cloth WPO
float3 windOffset = MF_ClothWindDrape(UV, Time, WindStrength * RhythmPulse, ...);

// Combine
float3 finalWPO = float3(0, 0, macroSwell + mediumFolds + microDetail) + windOffset;
```

---

## 3. Implementation Plan

### Phase 1: Cymatics-Driven Material Function (Tonight)

**Create `MF_FabricMountainWPO`:**

1. **Read Cymatics values:**
   - Add `MF_CymaticSampler` material function that reads from `UMelodiaCymaticsSubsystem`
   - Expose: `CymaticAmplitude`, `ModeN`, `ModeM`, `BeatPulse`, `BassIntensity`

2. **Build WPO layers:**
   - Macro: `CymaticAmplitude * BassIntensity * sin(worldPos.x * 0.001 + time)`
   - Medium: `sin(worldPos.x * 0.01 + noise) * cos(worldPos.y * 0.008) * MidIntensity`
   - Micro: `tex2D(HeightMap, worldPos.xy) * BeatPulse`
   - Wind: `MF_ClothWindDrape(UV, Time, WindStrength * RhythmPulse, ...)`

3. **Create `M_FabricMountain_Master`:**
   - Parent: `M_Master_Nikki_Landscape`
   - Add WPO output from `MF_FabricMountainWPO`
   - Add Copernicus PBR map inputs (BaseColor, Normal, Roughness, Height, Emissive, Iridescence)
   - Add audio-reactive scalar params (FabricPulse, FabricBass, FabricMid, FabricRhythm)

4. **Create `MI_FabricMountain_Base`:**
   - Wire Copernicus PBR maps (GildedLoom, SilkWaterfall, CherryBlossomWood)
   - Set audio-reactive defaults: FabricPulse=1.0, FabricBass=0.5, FabricMid=0.3, FabricRhythm=0.8

### Phase 2: GN Builder Audio Integration (Tonight)

**Modify 8 GN builders to be audio-reactive:**

| Builder | Audio Modulation |
|---------|-----------------|
| MEL_mother_head_silhouette | Scale Z by BassIntensity * 2.0 |
| MEL_mother_hair_cascade | Curl frequency by RhythmPulse * 3.0 |
| MEL_mother_valley_depression | Depth by MidIntensity * 1.5 |
| MEL_mother_fog_volume | Density by BeatPulse * 0.8 |
| MEL_mother_fabric_ridge | Fold depth by BassIntensity * 2.5 |
| MEL_mother_shoulder_fold | Fold count by MidIntensity * 2.0 |
| MEL_mother_heart_gate | Glow intensity by RhythmPulse * 4.0 |
| MEL_mother_landing_zone | Scale by BeatPulse * 1.2 |

### Phase 3: Landscape + WPO (Tomorrow)

**Create 8 km × 8 km fabric terrain:**

1. **Houdini heightfield:**
   - 8192×8192 resolution
   - Fabric fold noise: `abs(sin(x * freq)) ^ sharpness + turbulence`
   - Export as 16-bit RAW

2. **UE Landscape:**
   - Create `LM_FarawayMother_Terrain`
   - Import heightmap
   - Assign `M_FabricMountain_Master`

3. **WPO verification:**
   - Mountains pulse with BeatPulse
   - Fabric folds ripple with BassIntensity
   - Micro detail shimmers with RhythmPulse

### Phase 4: PCG Scatter + Glitter (Tomorrow)

**Create audio-reactive PCG graphs:**

1. **PCG_Faraway_FabricRidge:**
   - Scatter fabric ridge meshes along terrain ridges
   - Density driven by Cymatics amplitude
   - Scale by BassIntensity

2. **PCG_Faraway_DetailProps:**
   - Scatter rocks, coral, kelp, glitter
   - Glitter placement at high-curvature points (fabric fold peaks)
   - Glitter scale by BeatPulse

3. **PCG_Faraway_WindZones:**
   - Define wind response zones based on terrain slope
   - Steeper = more wind response
   - Driven by RhythmPulse

### Phase 5: Advanced Houdini Integration (This Week)

**Use advanced Houdini pipelines:**

1. **HDA_P1_SeamGraph:**
   - Fiber-direction textures for fabric anisotropy
   - Tension field from Cymatics amplitude
   - Seam masks for fabric panel boundaries

2. **Copernicus fabric generation:**
   - Generate new PBR sets for Faraway Mother
   - Use `copernicus_fabric_sheen.py` for velvet/silk
   - Use `copernicus_dress_bake.py` for gown/mantle

3. **VDM (Vector Displacement Mesh):**
   - Not available in project — use high-poly + WPO instead
   - Bake fabric fold normals to tangent space
   - Use parallax occlusion mapping for depth

---

## 4. Material Stack

### Master Material: `M_FabricMountain_Master`

**Parent:** `M_Master_Nikki_Landscape`

**Parameters:**

| Param | Type | Default | Audio Source |
|-------|------|---------|--------------|
| FabricPulse | Scalar | 1.0 | BeatPulse |
| FabricBass | Scalar | 0.5 | BassIntensity |
| FabricMid | Scalar | 0.3 | MidIntensity |
| FabricRhythm | Scalar | 0.8 | RhythmPulse |
| MacroAmplitude | Scalar | 50.0 | BassIntensity |
| MediumAmplitude | Scalar | 10.0 | MidIntensity |
| MicroAmplitude | Scalar | 1.0 | BeatPulse |
| WindStrength | Scalar | 0.5 | RhythmPulse |
| FoldDepth | Scalar | 1.5 | BassIntensity |
| FoldFrequency | Scalar | 6.0 | MidIntensity |
| IridescenceStrength | Scalar | 0.8 | BeatPulse |
| EmissivePulse | Scalar | 2.0 | RhythmPulse |

**Texture Maps (from Copernicus):**

| Map | Source Variant | Usage |
|-----|---------------|-------|
| BaseColor | GildedLoom | Gold fabric regions |
| Normal | SilkWaterfall | Water-like silk flow |
| Roughness | CherryBlossomWood | Organic variation |
| Height | GildedLoom | Fold relief for parallax |
| Emissive | DancingCrystals | Bioluminescent threads |
| Iridescence | FinalDreamweaver | Shifting colors |
| Metallic | GlitterGold | Metallic thread accents |
| AO | CavernWeave | Cavity shadows |

### Material Function: `MF_FabricMountainWPO`

**Inputs:**
- UV (Vector2)
- Time (Scalar)
- WindStrength (Scalar)
- WindSpeed (Scalar)
- WindDirection (Vector3)
- FoldingAmount (Scalar)
- DrapeMask (Scalar)
- CymaticAmplitude (Scalar) — from MPC
- BassIntensity (Scalar) — from MPC
- MidIntensity (Scalar) — from MPC
- BeatPulse (Scalar) — from MPC
- RhythmPulse (Scalar) — from MPC
- HeightMap (Texture2D)
- NormalMap (Texture2D)

**Outputs:**
- WPO (Vector3)
- NormalOffset (Vector3)

---

## 5. File Inventory

### To Create
- `Content/EnvSandbox/Materials/Functions/MF_FabricMountainWPO.uasset`
- `Content/EnvSandbox/Materials/Masters/M_FabricMountain_Master.uasset`
- `Content/EnvSandbox/Materials/Instances/FarawayMother/MI_FabricMountain_Base.uasset`
- `Content/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype.umap`
- `Content/EnvSandbox/Landscapes/FarawayMother/LM_FarawayMother_Terrain.uasset`
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_FabricRidge.uasset`
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_DetailProps.uasset`
- `Content/EnvSandbox/PCG/FarawayMother/PCG_Faraway_WindZones.uasset`
- `Content/EnvSandbox/Textures/FarawayMother/T_Faraway_Heightfield.raw`
- `Content/EnvSandbox/Textures/FarawayMother/T_Faraway_CymaticMask.uasset`

### To Modify
- `Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsSubsystem.h` — add WPO output
- `deploy/surreal_arch/melodia_gn/mother.py` — add audio-reactive params
- `Content/Python/build_mf_cloth_wind_drape.py` — extend for audio reactivity

### To Use As-Is
- `Saved/Audit/copernicus_cymatic/GildedLoom/` — gold fabric PBR
- `Saved/Audit/copernicus_cymatic/SilkWaterfall/` — silk PBR
- `Saved/Audit/copernicus_cymatic/CherryBlossomWood/` — organic PBR
- `Saved/Audit/copernicus_cymatic/DancingCrystals/` — emissive PBR
- `Saved/Audit/copernicus_cymatic/FinalDreamweaver/` — iridescence PBR
- `Content/EnvSandbox/Materials/Instances/Glitter/` — glitter MIs
- `Source/.../MelodiaCymaticsSubsystem` — audio→geometry Chladni
- `Source/.../MelodiaAudioReactivePresentationSubsystem` — audio→MPC

---

## 6. Technical Challenges + Solutions

| Challenge | Solution |
|-----------|----------|
| Cymatics not exposed to materials | Add MPC params for CymaticAmplitude, ModeN, ModeM |
| WPO at km scale causes z-fade | Tessellation + WPO hybrid; tessellate near camera |
| GN builders not audio-reactive | Add audio params to builder inputs; drive from MPC |
| No VDM support | Use high-poly + parallax occlusion + WPO |
| 8K textures memory pressure | Virtual textures; stream by distance |
| Audio latency | Use Quartz sub-frame phase tracking (already implemented) |
| Material function complexity | Split into sub-functions: MacroWPO, MediumWPO, MicroWPO, WindWPO |

---

## 7. Success Criteria

- [ ] Fabric mountains pulse with BeatPulse (visible Z displacement)
- [ ] Fabric folds ripple with BassIntensity (medium-frequency WPO)
- [ ] Micro detail shimmers with RhythmPulse (high-frequency normal perturbation)
- [ ] Wind response scales with RhythmPulse (cloth flutter)
- [ ] 8 GN builders placed and audio-reactive
- [ ] Copernicus PBR maps blended on terrain by slope/curvature
- [ ] Glitter placed at fabric fold peaks, pulsing with BeatPulse
- [ ] 60 FPS on RTX 3070+ (with tessellation + WPO)
- [ ] No z-fade or WPO artifacts at distance
- [ ] Truly surreal: "fabric behaves like geography/anatomy"

---

## 8. Implementation Order

1. **Tonight:** Create `MF_FabricMountainWPO` + `M_FabricMountain_Master` + `MI_FabricMountain_Base`
2. **Tonight:** Modify GN builders for audio reactivity
3. **Tomorrow:** Generate Houdini heightfield → Landscape
4. **Tomorrow:** Create PCG scatter graphs
5. **This Week:** Advanced Houdini integration (seam graphs, Copernius fabric)
6. **This Week:** Optimization (virtual textures, tessellation, LOD)

---

*Generated 2026-08-31 from deep research of Cymatics, Audio-Visual Synesthesia, WPO systems, GN builders, and Copernicus pipeline.*
