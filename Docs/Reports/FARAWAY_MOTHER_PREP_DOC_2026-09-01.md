# Faraway Mother — Consolidated Prep Document

**Date:** 2026-09-01
**Status:** Offline research complete — ready for editor session
**Core thesis:** Fabric behaves like geography; landscape is draped anatomy.

---

## 1. Asset Inventory

### 1.1 PBR Textures (6 Suites, ~50 maps each)

| Suite | Prefix | Maps Available |
|-------|--------|----------------|
| **Corset** | `T_FarawayMother_Corset_GildedAcanthusBrocade` | AO, BC, H, M, N, ORM, R |
| **Cradle** | `T_FarawayMother_Cradle_CarvedAlabasterWood` | AO, BC, H, M, N, ORM, R |
| **Gown** | `T_FarawayMother_Gown_CelestialSilkJacquard` | AO, BC, H, M, N, ORM, R, Sheen |
| **Mantle** | `T_FarawayMother_Mantle_NightSkyVelvet` | AO, BC, H, M, N, ORM, R, Sheen |
| **Ornament** | `T_FarawayMother_Ornament_NacreMusicBoxJewel` | AO, BC, H, M, N, ORM, R, Sheen |
| **Veil** | `T_FarawayMother_Veil_AquaticLullabyLace` | Alpha, AO, BC, H, Mask, M, N, ORM, R |

**Location:** `Content/Textures/FarawayMother_Suites/` (PNG + `.uasset` pairs)

### 1.2 HDA Variants (Copernicus)

| HDA | File | Resolution | Outputs |
|-----|------|------------|---------|
| Corset | `faraway_p2_corset_cop.hip` | 1024×1024 | BC, N, Rough, Emission |
| Cradle | `faraway_p2_cradle_cop.hip` | 1024×1024 | BC, N, Rough, Emission |
| Gown | `faraway_p2_gown_cop.hip` | 1024×1024 | BC, N, Rough, Emission |
| Mantle | `faraway_p2_mantle_cop.hip` | 1024×1024 | BC, N, Rough, Emission |
| Ornament | `faraway_p2_ornament_cop.hip` | 1024×1024 | BC, N, Rough, Emission |
| Veil | `faraway_p2_veil_cop.hip` | 1024×1024 | BC, N, Rough, Emission, Alpha Mask |

**Location:** `Tools/Houdini/copernicus/hda_variants/`

**Cook method:** `hython copernicus_dress_bake.py --hip <file> --bake-set T_FarawayMother_<Suite>`

**Output path:** `Saved/Audit/melusina_lookdev/houdini_variants/`

### 1.3 GN Builders (Blender 5.2 Geometry Nodes)

| Builder | Function | Key Params |
|---------|----------|------------|
| `MEL_mother_head_silhouette` | Mountain ridge with moonlit face profile | Width, Height, Depth, Noise Scale |
| `MEL_mother_hair_cascade` | Ribbon waterfall cascade for maternal hair | Length, Width, Strand Count, Curl |
| `MEL_mother_valley_depression` | Terrain depression with fog fill | Radius, Depth, Fog Level, Steepness |
| `MEL_mother_fog_volume` | Volumetric haze implying distant mass | Width, Height, Depth, Density, Tint |
| `MEL_mother_fabric_ridge` | Fabric normal-mapped terrain ridge | Width, Height, Fold Depth, Fold Count |
| `MEL_mother_shoulder_fold` | Shoulder/chest fold terrain | Width, Length, Fold Count, Asymmetry |
| `MEL_mother_heart_gate` | Rhythm checkpoint gate | Width, Height, Arch Point, Pillar Count |
| `MEL_mother_moonlight_rig` | Lighting rig for moonlit key | Key Intensity, Key Angle, Fill, Rim |

**Location:** `deploy/surreal_arch/melodia_gn/mother.py` (816 lines)

### 1.4 Material Setup (Sheen)

| Suite | Setup | SheenWidth | SheenBias | bUsesNormal | Mask |
|-------|-------|------------|-----------|-------------|------|
| Corset | 1-Subtle | 0.25 | 0.5 | False | None |
| Cradle | 1-Subtle | 0.25 | 0.5 | False | None |
| Gown | 2-Moderate | 0.75 | 0.5 | True | T_FarawayMother_Gown_Sheen |
| Mantle | 2-Moderate | 0.75 | 0.5 | True | T_FarawayMother_Mantle_Sheen |
| Ornament | 3-Strong | 1.5 | 0.5 | True | T_FarawayMother_Ornament_Sheen |
| Veil | 3-Strong | 1.5 | 0.5 | True | T_FarawayMother_Veil (Alpha) |

**Base Material:** `M_Master_Nikki` (already has landscape + sheen params)

### 1.5 WPO (World Position Offset)

**Script:** `Content/Python/build_mf_fabric_mountain_wpo.py` (216 lines, committed)

**Layers:**
- Macro swell: Chladni standing-wave × BassIntensity (1km wavelength, 50-100m amplitude)
- Medium folds: sin/cos noise × MidIntensity (100m wavelength, 10-20m amplitude)
- Micro detail: Copernicus height map × BeatPulse (1m wavelength, 0.5-2m amplitude)
- Wind response: MF_ClothWindDrape × RhythmPulse (dynamic)

**Run via:** Monolith `run_python Content/Python/build_mf_fabric_mountain_wpo.py`

---

## 2. Houdini Execution Spec

### 2.1 Folder Structure

```
Exports/Houdini/FarawayMother/
  Corset/SM_Faraway_Corset_*.fbx
  Cradle/SM_Faraway_Cradle_*.fbx
  Gown/SM_Faraway_Gown_*.fbx
  Mantle/SM_Faraway_Mantle_*.fbx
  Ornament/SM_Faraway_Ornament_*.fbx
  Veil/SM_Faraway_Veil_*.fbx

Saved/Audit/houdini_faraway_mother/
  corset_manifest.json
  cradle_manifest.json
  gown_manifest.json
  mantle_manifest.json
  ornament_manifest.json
  veil_manifest.json

Saved/Audit/melusina_lookdev/houdini_variants/
  T_FarawayMother_Corset_BaseColor.png
  T_FarawayMother_Corset_Normal.png
  ... (24 PNGs total)
```

### 2.2 HDA Cook Order

1. **Tier 0 — Foundation:** Corset + Cradle (Subtle Sheen) — simplest, no sheen mask
2. **Tier 1 — Mid:** Gown + Mantle (Moderate Sheen) — sheen mask required
3. **Tier 2 — Complex:** Ornament + Veil (Strong Sheen) — Veil has alpha/translucency

### 2.3 Data Contract

**From Houdini → Unreal:**
- Static Mesh per suite (FBX)
- PBR texture set (BC, N, ORM, AO, H, M, R, Sheen, Alpha)
- Manifest JSON (seed, version, outputs, hash)

**From Unreal → Houdini:**
- Spline inputs (valley boundary, route curve, tension anchors)
- Camera reveal positions
- Terrain heightfield (for projection)

### 2.4 Ownership Boundary

**Houdini owns:** Geometry, masks, UVs, LODs, scatter candidates, reveal alignment
**Unreal owns:** World Partition, Data Layers, PCG runtime scatter, rhythm, StateTree, Niagara, MetaSounds, camera, lighting

---

## 3. Editor Session Preparation

### 3.1 Pre-Session (Offline, Now)

- [ ] Verify all 6 HDA `.hip` files exist and parse correctly
- [ ] Verify all PBR textures exist in `Content/Textures/FarawayMother_Suites/`
- [ ] Create folder structure in `Content/EnvSandbox/Monoliths/FarawayMother/`
- [ ] Create folder structure in `Content/EnvSandbox/Landscapes/FarawayMother/`
- [ ] Create folder structure in `Content/EnvSandbox/Materials/Instances/FarawayMother/P2/`
- [ ] Create folder structure in `Content/EnvSandbox/PCG/FarawayMother/`
- [ ] Create folder structure in `Exports/Houdini/FarawayMother/`
- [ ] Create folder structure in `Saved/Audit/houdini_faraway_mother/`

### 3.2 Session A — Houdini Cook (Evening)

- [ ] Open Houdini 22.0.368
- [ ] Verify Houdini Engine UE5.8 session
- [ ] Cook HDA_P2_Corset (1024×1024)
- [ ] Cook HDA_P2_Cradle (1024×1024)
- [ ] Cook HDA_P2_Gown (1024×1024)
- [ ] Cook HDA_P2_Mantle (1024×1024)
- [ ] Cook HDA_P2_Ornament (1024×1024)
- [ ] Cook HDA_P2_Veil (1024×1024, includes Alpha)
- [ ] Export FBX meshes to `Exports/Houdini/FarawayMother/`
- [ ] Write manifest JSON per suite

### 3.3 Session B — Unreal Assembly (Following Day)

- [ ] Create `LV_FarawayMother_Prototype`
- [ ] Create `LM_FarawayMother_Terrain` (8192×8192)
- [ ] Import HDA meshes from `Exports/Houdini/FarawayMother/`
- [ ] Create `M_FabricMountain_Master` material
- [ ] Create 6 MIs (one per suite) with sheen setups
- [ ] Wire WPO: `MF_FabricMountainWPO` + `MF_FabricTensionMask`
- [ ] Place 8 GN builders in level
- [ ] Create 3 PCG graphs (FabricRidge, DetailProps, WindZones)

### 3.4 Session C — Reveal & Polish

- [ ] Camera reveal validation (HDA_P3_HorizonMouthComposer logic)
- [ ] Material state test (local interaction → distant response)
- [ ] Performance capture (target 60 FPS on RTX 3070+)

---

## 4. Contact Sheet Render Spec

**Script:** `Tools/BlenderScripts/faraway_mother_contact_sheet.py`

**Output:** `Saved/Audit/FarawayMother_ContactSheet.png` (1920×1080)

**Layout:** 3×2 grid of fabric swatches, each with:
- PBR textures applied (BC, N, Rough, Metallic)
- Text label with suite name
- Area key light + fill light
- Cycles render at 128 samples

**Run:**
```
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python Tools/BlenderScripts/faraway_mother_contact_sheet.py
```

---

## 5. Success Criteria

- [ ] 6 fabric suites rendered as contact sheet
- [ ] All 6 HDAs cooked through Houdini Engine
- [ ] 8 GN builders placed and scaled in level
- [ ] 6 MIs created with correct sheen setups
- [ ] WPO animation: macro swell + medium folds + micro detail
- [ ] Copernicus PBR maps blended on terrain
- [ ] Level sequence showcase (45s, 6 segments)

---

*Prep complete. Awaiting editor session to execute.*
