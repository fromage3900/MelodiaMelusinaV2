# Melusina Material Audit Report — LIVE (Monolith) — Substrate Toon Compliance
**Generated:** 2026-08-06T23:35:52.016110
**Audit Mode:** ONLINE
**Monolith Reachable:** True
**Mesh:** `/Game/Melodia/Characters/Melusina/SK_Melusina`
**Parent Master:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**Toon Profile:** `/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina`

## Overall Summary
| Metric | Value |
|--------|-------|
| Total Slots | 33 |
| Material Instances (assigned) | 33 |
| Empty | 0 |
| Slots OK | 18 |
| Slots with Warnings | 11 |
| Slots with Errors | 4 |
| Grade | **FAIL** |
| Total Issues | 26 |

## Live Slot Assignments (from SK_Melusina.materials)

| Slot | Slot Name | MI Assigned | Role | Status | Issues |
|------|-----------|-------------|------|--------|--------|
| 0 | `Gradient__Radial__002` | `M_Master_Toon_Universal` | unknown | **WARN** | MI MISMATCH: got 'M_Master_Toon_Universal' expected 'MI_Melusina_Gradient__Radial__002'; Could not read parameters: Failed to load material instance at '/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal' |
| 1 | `SBW_MELUSINA_006` | `MI_Melusina_SBW_MELUSINA_006` | body main | **PASS** | — |
| 2 | `SBW_MELUSINA_007` | `MI_Melusina_SBW_MELUSINA_007` | body main | **PASS** | — |
| 3 | `sleeve_003` | `MI_Melusina_sleeve_003` | sleeve | **PASS** | — |
| 4 | `Outline_Shader_*_024` | `MI_Melusina_Outline_Shader_star_024` | outline shader | **PASS** | — |
| 5 | `Metal_2__Matcap__002` | `MI_Melusina_Material_023` | celestial/space effect (catch-all) | **WARN** | MI MISMATCH: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Metal_2__Matcap__002' |
| 6 | `Outline_005` | `MI_Melusina_Material_023` | celestial/space effect (catch-all) | **WARN** | MI MISMATCH: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Outline_005' |
| 7 | `Material_021` | `MI_Melusina_Material_023` | celestial/space effect (catch-all) | **WARN** | WRONG MI ASSIGNED: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Material_021' — celestial catch-all replaced dedicated material |
| 8 | `Outline_004` | `MI_Melusina_Material_023` | celestial/space effect (catch-all) | **WARN** | MI MISMATCH: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Outline_004' |
| 9 | `Material_013` | `MI_Melusina_Material_013` | body/clothing | **PASS** | — |
| 10 | `Halftone_Circles___Circles__3_Inputs__001` | `MI_Melusina_Material_023` | celestial/space effect (catch-all) | **WARN** | MI MISMATCH: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Halftone_Circles___Circles__3_Inputs__001' |
| 11 | `Material_022` | `MI_Melusina_Material_023` | celestial/space effect (catch-all) | **WARN** | WRONG MI ASSIGNED: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Material_022' — celestial catch-all replaced dedicated material |
| 12 | `Material_023` | `MI_Melusina_Material_023` | celestial/space effect (catch-all) | **PASS** | — |
| 13 | `bow_002` | `MI_Melusina_bow_002` | bow accessory | **PASS** | — |
| 14 | `Outline_Shader_*_029` | `MI_Melusina_Material_023` | celestial/space effect (catch-all) | **WARN** | WRONG MI ASSIGNED: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Outline_Shader_star_034' — outline slot got celestial catch-all |
| 15 | `Material_024` | `MI_Melusina_Material_023` | celestial/space effect (catch-all) | **WARN** | WRONG MI ASSIGNED: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Material_024' — celestial catch-all replaced dedicated material |
| 16 | `skirtpanel_002` | `MI_Melusina_skirtpanel_002` | skirt front panel | **PASS** | — |
| 17 | `Outline_Shader_*_025` | `MI_Melusina_Outline_Shader_star_025` | outline shader | **WARN** | MI MISMATCH: got 'MI_Melusina_Outline_Shader_star_025' expected 'MI_Melusina_Outline_Shader_star_029' |
| 18 | `SHAWL_001` | `MI_Melusina_SHAWL_001` | shawl/shoulder wrap | **PASS** | — |
| 19 | `frontpanel_001` | `MI_Melusina_frontpanel_001` | front panel (bodice) | **FAIL** | Broken texture reference: RoughnessMap -> /Game/frontpanel_Roughness.frontpanel_Roughness; Broken texture reference: Albedo -> /Game/frontpanel_BaseColor.frontpanel_BaseColor; Broken texture reference: NormalMap -> /Game/frontpanel_Normal.frontpanel_Normal |
| 20 | `Outline_Shader_*_023` | `MI_Melusina_Outline_Shader_star_023` | outline shader | **PASS** | — |
| 21 | `GLOVES_001` | `MI_Melusina_GLOVES_001` | gloves | **WARN** | bUseSeparateRoughnessMap not overridden to True; bUseSeparateMetallicMap not overridden to True |
| 22 | `Outline_Shader_*_030` | `MI_Melusina_Outline_Shader_star_030` | outline shader | **PASS** | — |
| 23 | `Material_017` | `MI_Melusina_Material_017` | boots | **PASS** | — |
| 24 | `Material_006` | `Material_006` | unknown | **FAIL** | MI MISMATCH: got 'Material_006' expected 'MI_Melusina_Material_006'; bUseSeparateRoughnessMap not overridden to True; bUseSeparateMetallicMap not overridden to True |
| 25 | `Outline_Shader_*_028` | `MI_Melusina_Outline_Shader_star_028` | outline shader | **PASS** | — |
| 26 | `Material_007` | `Material_007` | unknown | **FAIL** | MI MISMATCH: got 'Material_007' expected 'MI_Melusina_Material_007'; bUseSeparateRoughnessMap not overridden to True; bUseSeparateMetallicMap not overridden to True |
| 27 | `Outline_Shader_*_027` | `MI_Melusina_Outline_Shader_star_027` | outline shader | **PASS** | — |
| 28 | `Iridescence_002` | `Iridescence_002` | unknown | **FAIL** | MI MISMATCH: got 'Iridescence_002' expected 'MI_Melusina_Iridescence_002'; bUseSeparateRoughnessMap not overridden to True; bUseSeparateMetallicMap not overridden to True |
| 29 | `Outline_Shader_*_026` | `MI_Melusina_Outline_Shader_star_026` | outline shader | **PASS** | — |
| 30 | `Outline_Shader_*_032` | `MI_Melusina_Outline_Shader_star_032` | outline shader | **PASS** | — |
| 31 | `SKIRT_003` | `MI_Melusina_SKIRT_003` | skirt main | **PASS** | — |
| 32 | `Halftone_3_Inputs_-_Lines___Circles_002` | `MI_Melusina_Halftone_3_Inputs_-_Lines___Circles_002` | halftone pattern overlay | **PASS** | — |

## Water Hair Material (Separate Mesh: SK_MelusinaHair)
**MI:** `MI_Melusina_WaterHair` at `/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair`
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v7.M_Water_Master_Grand_v7`
**Status:** WARN
- No texture overrides — may be using parent defaults

## Recommendations
1. Fix 13 slot(s) with wrong MI assignments: [(0, 'M_Master_Toon_Universal'), (5, 'MI_Melusina_Material_023'), (6, 'MI_Melusina_Material_023'), (7, 'MI_Melusina_Material_023'), (8, 'MI_Melusina_Material_023'), (10, 'MI_Melusina_Material_023'), (11, 'MI_Melusina_Material_023'), (14, 'MI_Melusina_Material_023'), (15, 'MI_Melusina_Material_023'), (17, 'MI_Melusina_Outline_Shader_star_025'), (24, 'Material_006'), (26, 'Material_007'), (28, 'Iridescence_002')]
2. Fix broken texture references on 1 slot(s): [(19, 'MI_Melusina_frontpanel_001')]
3. Set bUseSeparateRoughnessMap=True on 4 slot(s): ['MI_Melusina_GLOVES_001', 'Material_006', 'Material_007', 'Iridescence_002']
4. Set bUseSeparateMetallicMap=True on 4 slot(s): ['MI_Melusina_GLOVES_001', 'Material_006', 'Material_007', 'Iridescence_002']
5. Verify TP_Melusina toon profile is properly applied at the M_Master_Toon_Universal level
6. Run fix_up_redirectors.py and Map Check after any editor session
7. Slot 0 (Gradient__Radial__002) uses master directly — consider creating a proper MI
8. Slots 24/26/28 use raw Materials from _SkeletonFixSpike/ — consider converting to MIs

## Priority Order for Fixes
| Slot | MI | Priority | Reason |
|------|-----|----------|--------|
| 7 | `MI_Melusina_Material_023` | **HIGH** | Wrong MI assigned |
| 11 | `MI_Melusina_Material_023` | **HIGH** | Wrong MI assigned |
| 14 | `MI_Melusina_Material_023` | **HIGH** | Wrong MI assigned |
| 15 | `MI_Melusina_Material_023` | **HIGH** | Wrong MI assigned |
| 19 | `MI_Melusina_frontpanel_001` | **HIGH** | Broken texture references |
| 21 | `MI_Melusina_GLOVES_001` | **MEDIUM** | Missing static switch override |
| 24 | `Material_006` | **MEDIUM** | Missing static switch override |
| 26 | `Material_007` | **MEDIUM** | Missing static switch override |
| 28 | `Iridescence_002` | **MEDIUM** | Missing static switch override |

## Per-Slot Parameter Details

### Slot 0 (1-based: 1) — `M_Master_Toon_Universal`
**Status:** WARN
**Slot Name:** `Gradient__Radial__002`
**Role:** unknown
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**Issues:**
- MI MISMATCH: got 'M_Master_Toon_Universal' expected 'MI_Melusina_Gradient__Radial__002'
- Could not read parameters: Failed to load material instance at '/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal'

### Slot 1 (1-based: 2) — `MI_Melusina_SBW_MELUSINA_006`
**Status:** PASS
**Slot Name:** `SBW_MELUSINA_006`
**Role:** body main
**Family:** body
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_M_Melusina_BaseColor.T_Melusina_M_Melusina_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_M_Melusina_Normal.T_Melusina_M_Melusina_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_M_Melusina_Roughness.T_Melusina_M_Melusina_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_M_Melusina_Metallic.T_Melusina_M_Melusina_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_M_Melusina_Displacement.T_Melusina_M_Melusina_Displacement`

### Slot 2 (1-based: 3) — `MI_Melusina_SBW_MELUSINA_007`
**Status:** PASS
**Slot Name:** `SBW_MELUSINA_007`
**Role:** body main
**Family:** body
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 14
**Textures:**
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_M_Melusina_Metallic.T_Melusina_M_Melusina_Metallic`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_M_Melusina_Roughness.T_Melusina_M_Melusina_Roughness`
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_M_Melusina_BaseColor.T_Melusina_M_Melusina_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_M_Melusina_Normal.T_Melusina_M_Melusina_Normal`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_M_Melusina_Displacement.T_Melusina_M_Melusina_Displacement`

### Slot 3 (1-based: 4) — `MI_Melusina_sleeve_003`
**Status:** PASS
**Slot Name:** `sleeve_003`
**Role:** sleeve
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 10
**Textures:**
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_sleeve_Metallic.T_Melusina_m_sleeve_Metallic`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_sleeve_Roughness.T_Melusina_m_sleeve_Roughness`
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_sleeve_BaseColor.T_Melusina_m_sleeve_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_sleeve_Normal.T_Melusina_m_sleeve_Normal`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_sleeve_Displacement.T_Melusina_m_sleeve_Displacement`

### Slot 4 (1-based: 5) — `MI_Melusina_Outline_Shader_star_024`
**Status:** PASS
**Slot Name:** `Outline_Shader_*_024`
**Role:** outline shader
**Family:** outline
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_BaseColor.T_Melusina_Outline_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Normal.T_Melusina_Outline_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Roughness.T_Melusina_Outline_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Metallic.T_Melusina_Outline_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Displacement.T_Melusina_Outline_Displacement`

### Slot 5 (1-based: 6) — `MI_Melusina_Material_023`
**Status:** WARN
**Slot Name:** `Metal_2__Matcap__002`
**Role:** celestial/space effect (catch-all)
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 24
**Textures:**
  - `TriplanarDetailMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
  - `StarMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
**Issues:**
- MI MISMATCH: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Metal_2__Matcap__002'

### Slot 6 (1-based: 7) — `MI_Melusina_Material_023`
**Status:** WARN
**Slot Name:** `Outline_005`
**Role:** celestial/space effect (catch-all)
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 24
**Textures:**
  - `TriplanarDetailMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
  - `StarMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
**Issues:**
- MI MISMATCH: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Outline_005'

### Slot 7 (1-based: 8) — `MI_Melusina_Material_023`
**Status:** WARN
**Slot Name:** `Material_021`
**Role:** celestial/space effect (catch-all)
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 24
**Textures:**
  - `TriplanarDetailMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
  - `StarMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
**Issues:**
- WRONG MI ASSIGNED: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Material_021' — celestial catch-all replaced dedicated material

### Slot 8 (1-based: 9) — `MI_Melusina_Material_023`
**Status:** WARN
**Slot Name:** `Outline_004`
**Role:** celestial/space effect (catch-all)
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 24
**Textures:**
  - `TriplanarDetailMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
  - `StarMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
**Issues:**
- MI MISMATCH: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Outline_004'

### Slot 9 (1-based: 10) — `MI_Melusina_Material_013`
**Status:** PASS
**Slot Name:** `Material_013`
**Role:** body/clothing
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Material_007_BaseColor.T_Melusina_Material_007_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Material_007_Normal.T_Melusina_Material_007_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Material_007_Roughness.T_Melusina_Material_007_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Material_007_Metallic.T_Melusina_Material_007_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Material_007_Displacement.T_Melusina_Material_007_Displacement`

### Slot 10 (1-based: 11) — `MI_Melusina_Material_023`
**Status:** WARN
**Slot Name:** `Halftone_Circles___Circles__3_Inputs__001`
**Role:** celestial/space effect (catch-all)
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 24
**Textures:**
  - `TriplanarDetailMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
  - `StarMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
**Issues:**
- MI MISMATCH: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Halftone_Circles___Circles__3_Inputs__001'

### Slot 11 (1-based: 12) — `MI_Melusina_Material_023`
**Status:** WARN
**Slot Name:** `Material_022`
**Role:** celestial/space effect (catch-all)
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 24
**Textures:**
  - `TriplanarDetailMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
  - `StarMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
**Issues:**
- WRONG MI ASSIGNED: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Material_022' — celestial catch-all replaced dedicated material

### Slot 12 (1-based: 13) — `MI_Melusina_Material_023`
**Status:** PASS
**Slot Name:** `Material_023`
**Role:** celestial/space effect (catch-all)
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 24
**Textures:**
  - `TriplanarDetailMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
  - `StarMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`

### Slot 13 (1-based: 14) — `MI_Melusina_bow_002`
**Status:** PASS
**Slot Name:** `bow_002`
**Role:** bow accessory
**Family:** accessory
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 10
**Textures:**
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_bow_Metallic.T_Melusina_m_bow_Metallic`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_bow_Roughness.T_Melusina_m_bow_Roughness`
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_bow_BaseColor.T_Melusina_m_bow_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_bow_Normal.T_Melusina_m_bow_Normal`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_bow_Displacement.T_Melusina_m_bow_Displacement`

### Slot 14 (1-based: 15) — `MI_Melusina_Material_023`
**Status:** WARN
**Slot Name:** `Outline_Shader_*_029`
**Role:** celestial/space effect (catch-all)
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 24
**Textures:**
  - `TriplanarDetailMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
  - `StarMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
**Issues:**
- WRONG MI ASSIGNED: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Outline_Shader_star_034' — outline slot got celestial catch-all

### Slot 15 (1-based: 16) — `MI_Melusina_Material_023`
**Status:** WARN
**Slot Name:** `Material_024`
**Role:** celestial/space effect (catch-all)
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 24
**Textures:**
  - `TriplanarDetailMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
  - `StarMap` → `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K.T_NASA_StarMap_4K`
**Issues:**
- WRONG MI ASSIGNED: got 'MI_Melusina_Material_023' expected 'MI_Melusina_Material_024' — celestial catch-all replaced dedicated material

### Slot 16 (1-based: 17) — `MI_Melusina_skirtpanel_002`
**Status:** PASS
**Slot Name:** `skirtpanel_002`
**Role:** skirt front panel
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 10
**Textures:**
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_skirtpanel_004_Metallic.T_Melusina_skirtpanel_004_Metallic`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_skirtpanel_004_Roughness.T_Melusina_skirtpanel_004_Roughness`
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_skirtpanel_004_BaseColor.T_Melusina_skirtpanel_004_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_skirtpanel_004_Normal.T_Melusina_skirtpanel_004_Normal`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_skirtpanel_004_Displacement.T_Melusina_skirtpanel_004_Displacement`

### Slot 17 (1-based: 18) — `MI_Melusina_Outline_Shader_star_025`
**Status:** WARN
**Slot Name:** `Outline_Shader_*_025`
**Role:** outline shader
**Family:** outline
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_BaseColor.T_Melusina_Outline_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Normal.T_Melusina_Outline_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Roughness.T_Melusina_Outline_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Metallic.T_Melusina_Outline_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Displacement.T_Melusina_Outline_Displacement`
**Issues:**
- MI MISMATCH: got 'MI_Melusina_Outline_Shader_star_025' expected 'MI_Melusina_Outline_Shader_star_029'

### Slot 18 (1-based: 19) — `MI_Melusina_SHAWL_001`
**Status:** PASS
**Slot Name:** `SHAWL_001`
**Role:** shawl/shoulder wrap
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_SHAWL_BaseColor.T_MelusinaC_SHAWL_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_SHAWL_Normal.T_MelusinaC_SHAWL_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_SHAWL_Roughness.T_MelusinaC_SHAWL_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_SHAWL_Metallic.T_MelusinaC_SHAWL_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_shawl_Displacement.T_Melusina_m_shawl_Displacement`

### Slot 19 (1-based: 20) — `MI_Melusina_frontpanel_001`
**Status:** FAIL
**Slot Name:** `frontpanel_001`
**Role:** front panel (bodice)
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 10
**Textures:**
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_frontpanel_Metallic.T_MelusinaC_frontpanel_Metallic`
  - `RoughnessMap` → `/Game/frontpanel_Roughness.frontpanel_Roughness`
  - `Albedo` → `/Game/frontpanel_BaseColor.frontpanel_BaseColor`
  - `NormalMap` → `/Game/frontpanel_Normal.frontpanel_Normal`
  - `HeightMap` → `/Game/frontpanel_Displacement.frontpanel_Displacement`
**Issues:**
- Broken texture reference: RoughnessMap -> /Game/frontpanel_Roughness.frontpanel_Roughness
- Broken texture reference: Albedo -> /Game/frontpanel_BaseColor.frontpanel_BaseColor
- Broken texture reference: NormalMap -> /Game/frontpanel_Normal.frontpanel_Normal
- Broken texture reference: HeightMap -> /Game/frontpanel_Displacement.frontpanel_Displacement

### Slot 20 (1-based: 21) — `MI_Melusina_Outline_Shader_star_023`
**Status:** PASS
**Slot Name:** `Outline_Shader_*_023`
**Role:** outline shader
**Family:** outline
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_BaseColor.T_Melusina_Outline_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Normal.T_Melusina_Outline_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Roughness.T_Melusina_Outline_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Metallic.T_Melusina_Outline_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Displacement.T_Melusina_Outline_Displacement`

### Slot 21 (1-based: 22) — `MI_Melusina_GLOVES_001`
**Status:** WARN
**Slot Name:** `GLOVES_001`
**Role:** gloves
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** False
**bUseSeparateMetallicMap:** False
**Total Parameter Overrides:** 13
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_gloves_BaseColor.T_Melusina_m_gloves_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_gloves_Normal.T_Melusina_m_gloves_Normal`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_gloves_Displacement.T_Melusina_m_gloves_Displacement`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_gloves_Metallic.T_Melusina_m_gloves_Metallic`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_gloves_Roughness.T_Melusina_m_gloves_Roughness`
**Issues:**
- bUseSeparateRoughnessMap not overridden to True
- bUseSeparateMetallicMap not overridden to True

### Slot 22 (1-based: 23) — `MI_Melusina_Outline_Shader_star_030`
**Status:** PASS
**Slot Name:** `Outline_Shader_*_030`
**Role:** outline shader
**Family:** outline
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_BaseColor.T_Melusina_Outline_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Normal.T_Melusina_Outline_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Roughness.T_Melusina_Outline_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Metallic.T_Melusina_Outline_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Displacement.T_Melusina_Outline_Displacement`

### Slot 23 (1-based: 24) — `MI_Melusina_Material_017`
**Status:** PASS
**Slot Name:** `Material_017`
**Role:** boots
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 5
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_boot_BaseColor.T_Melusina_m_boot_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_boot_Normal.T_Melusina_m_boot_Normal`

### Slot 24 (1-based: 25) — `Material_006`
**Status:** FAIL
**Slot Name:** `Material_006`
**Role:** unknown
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** False
**bUseSeparateMetallicMap:** False
**Total Parameter Overrides:** 8
**Textures:**
  - `DiffuseColorMap` → `/Game/Melodia/Characters/Melusina/_SkeletonFixSpike/m_hatruffle_BaseColor.m_hatruffle_BaseColor`
  - `Albedo` → `/Game/Melodia/Characters/Melusina/_SkeletonFixSpike/m_hatruffle_BaseColor.m_hatruffle_BaseColor`
**Issues:**
- MI MISMATCH: got 'Material_006' expected 'MI_Melusina_Material_006'
- bUseSeparateRoughnessMap not overridden to True
- bUseSeparateMetallicMap not overridden to True

### Slot 25 (1-based: 26) — `MI_Melusina_Outline_Shader_star_028`
**Status:** PASS
**Slot Name:** `Outline_Shader_*_028`
**Role:** outline shader
**Family:** outline
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_BaseColor.T_Melusina_Outline_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Normal.T_Melusina_Outline_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Roughness.T_Melusina_Outline_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Metallic.T_Melusina_Outline_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Displacement.T_Melusina_Outline_Displacement`

### Slot 26 (1-based: 27) — `Material_007`
**Status:** FAIL
**Slot Name:** `Material_007`
**Role:** unknown
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** False
**bUseSeparateMetallicMap:** False
**Total Parameter Overrides:** 9
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_Material_004_BaseColor.T_MelusinaC_Material_004_BaseColor`
  - `DiffuseColorMap` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_Material_004_BaseColor.T_MelusinaC_Material_004_BaseColor`
**Issues:**
- MI MISMATCH: got 'Material_007' expected 'MI_Melusina_Material_007'
- bUseSeparateRoughnessMap not overridden to True
- bUseSeparateMetallicMap not overridden to True

### Slot 27 (1-based: 28) — `MI_Melusina_Outline_Shader_star_027`
**Status:** PASS
**Slot Name:** `Outline_Shader_*_027`
**Role:** outline shader
**Family:** outline
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_BaseColor.T_Melusina_Outline_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Normal.T_Melusina_Outline_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Roughness.T_Melusina_Outline_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Metallic.T_Melusina_Outline_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Displacement.T_Melusina_Outline_Displacement`

### Slot 28 (1-based: 29) — `Iridescence_002`
**Status:** FAIL
**Slot Name:** `Iridescence_002`
**Role:** unknown
**Family:** effect
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** False
**bUseSeparateMetallicMap:** False
**Total Parameter Overrides:** 13
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_belt_BaseColor.T_MelusinaC_belt_BaseColor`
  - `DiffuseColorMap` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_belt_BaseColor.T_MelusinaC_belt_BaseColor`
**Issues:**
- MI MISMATCH: got 'Iridescence_002' expected 'MI_Melusina_Iridescence_002'
- bUseSeparateRoughnessMap not overridden to True
- bUseSeparateMetallicMap not overridden to True

### Slot 29 (1-based: 30) — `MI_Melusina_Outline_Shader_star_026`
**Status:** PASS
**Slot Name:** `Outline_Shader_*_026`
**Role:** outline shader
**Family:** outline
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_BaseColor.T_Melusina_Outline_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Normal.T_Melusina_Outline_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Roughness.T_Melusina_Outline_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Metallic.T_Melusina_Outline_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Displacement.T_Melusina_Outline_Displacement`

### Slot 30 (1-based: 31) — `MI_Melusina_Outline_Shader_star_032`
**Status:** PASS
**Slot Name:** `Outline_Shader_*_032`
**Role:** outline shader
**Family:** outline
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_BaseColor.T_Melusina_Outline_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Normal.T_Melusina_Outline_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Roughness.T_Melusina_Outline_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Metallic.T_Melusina_Outline_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Outline_Displacement.T_Melusina_Outline_Displacement`

### Slot 31 (1-based: 32) — `MI_Melusina_SKIRT_003`
**Status:** PASS
**Slot Name:** `SKIRT_003`
**Role:** skirt main
**Family:** clothing
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 21
**Textures:**
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_SKIRT_Metallic.T_MelusinaC_SKIRT_Metallic`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_SKIRT_Roughness.T_MelusinaC_SKIRT_Roughness`
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_SKIRT_BaseColor.T_MelusinaC_SKIRT_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_SKIRT_Normal.T_MelusinaC_SKIRT_Normal`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_m_skirt_Displacement.T_Melusina_m_skirt_Displacement`

### Slot 32 (1-based: 33) — `MI_Melusina_Halftone_3_Inputs_-_Lines___Circles_002`
**Status:** PASS
**Slot Name:** `Halftone_3_Inputs_-_Lines___Circles_002`
**Role:** halftone pattern overlay
**Family:** halftone
**Parent:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal`
**bUseSeparateRoughnessMap:** True
**bUseSeparateMetallicMap:** True
**Total Parameter Overrides:** 8
**Textures:**
  - `Albedo` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Halftone_Circles_and_Circles_3_Inputs_BaseColor.T_Melusina_Halftone_Circles_and_Circles_3_Inputs_BaseColor`
  - `NormalMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Halftone_Circles_and_Circles_3_Inputs_Normal.T_Melusina_Halftone_Circles_and_Circles_3_Inputs_Normal`
  - `RoughnessMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Halftone_Circles_and_Circles_3_Inputs_Roughness.T_Melusina_Halftone_Circles_and_Circles_3_Inputs_Roughness`
  - `MetallicMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Halftone_Circles_and_Circles_3_Inputs_Metallic.T_Melusina_Halftone_Circles_and_Circles_3_Inputs_Metallic`
  - `HeightMap` → `/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Halftone_Circles_and_Circles_3_Inputs_Displacement.T_Melusina_Halftone_Circles_and_Circles_3_Inputs_Displacement`

---
*Audit performed live via Monolith MCP. Re-run to refresh.*
