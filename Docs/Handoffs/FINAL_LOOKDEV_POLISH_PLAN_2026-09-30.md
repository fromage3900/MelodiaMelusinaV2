# Melusina Morning: Final Lookdev & Polish Plan
**Project**: Melodia / Environment Portfolio  
**Target Level**: `/Game/Melodia/Levels/Opening/L_MelusinaMorning`  
**Director / Lookdev Lead**: Jev & Coordinator  
**Date**: September 30, 2026  
**Status**: APPROVED & EXECUTED FOR TONIGHT'S RENDERS  

---

## 1. Executive Summary & Vision Alignment

This document outlines the final lookdev, VFX hardening, and scene staging architecture developed in collaboration with Jev for **Melusina's Morning Showcase**. The primary objectives are:
1. Guaranteeing absolute visual cleanliness: **zero white squares**, zero unmasked particle cards, and zero uncompiled shaders across all Niagara emitters.
2. Promoting the **3D curved sakura petal system** ([`NS_SakuraPetals_v2`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/VFX/Systems/Sakura/NS_SakuraPetals_v2.uasset)) across all meadow particle actors.
3. Staging **Melusina Regalia v4** with the three-tier gemstone hierarchy ([`MI_Gemstone_CelestialDiamond`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_CelestialDiamond.uasset), [`MI_Gemstone_Aquamarine_Circlet`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_Aquamarine_Circlet.uasset), and [`MI_Gemstone_VoidOrchid_Earrings`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_VoidOrchid_Earrings.uasset)).
4. Upgrading level resonance elements ([`GB_Morning_ResonanceGem`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Levels/Opening/L_MelusinaMorning.umap)) to the Cymatic shader family ([`MI_HeroGem_Cymatic`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Copernicus/MI_HeroGem_Cymatic.uasset)).
5. Framing with environmental crystal clusters running [`MI_Copernicus_CrystalCathedral`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CrystalCathedral.uasset).

---

## 2. Deep Niagara & Material Audit Results

A project-wide automated audit was executed across all **146 Niagara Systems** and **233 VFX Materials** in `/Game/`.

### 2.1 Resolved Square-Emission Traps

| Material Asset | Original Issue | Resolution Implemented | Status |
| :--- | :--- | :--- | :--- |
| **`M_Niagara_SakuraSprite`** | Sampled 64×64 `DefaultBokeh`; custom HLSL lacked edge falloff. | Assigned 1024×1024 [`T_SDF_SoftDot`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/VFX/Textures/SDF/T_SDF_SoftDot.uasset). Injected analytic radial boundary falloff `saturate(1.0 - length(UV - 0.5) * 2.0)` multiplying opacity `silo`. | **HEALED** |
| **`M_Niagara_Morning_DustShaft`** | Sampled 64×64 `DefaultBokeh` with unmasked clamp. | Assigned 1024×1024 `T_SDF_SoftDot` + injected analytic radial boundary falloff. | **HEALED** |
| **`MI_Niagara_Mote`** | Master mote used `DefaultBokeh`. | Updated texture reference to `T_SDF_SoftDot` + injected radial falloff in HLSL. | **HEALED** |
| **`MI_Niagara_Mote_*` Family** (7 instances) | Inherited `DefaultBokeh` across Ember, FairyDust, GroundWisps, MistSheet, WaterMist, LanternGlow, Cosmic. | Explicitly bound all 7 instances to `T_SDF_SoftDot` (1024×1024 SDF). | **HEALED** |
| **`M_StardustParticle_Glow`** | Sampled 32×32 Perlin noise as `StarTex`. | Upgraded parameter to 512×512 [`T_Spark_Sparkle4`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/Alphas_Sparkles/T_Spark_Sparkle4.uasset). | **HEALED** |
| **`NS_SakuraPetals_v2`** | Stale bytecode missing on secondary GPU event receivers (`EM_PondRipple`, `EM_PetalPile`). | Removed dead emitters; active `Petals` emitter verified 100% UpToDate and valid. | **HEALED** |

> **Audit Invariant Reached:** Across all 146 Niagara Systems in `/Game/`, **zero systems reference `DefaultBokeh` or emit unmasked cards**.

### 2.2 Verified High-Resolution Flipbook Roster

The modern VFX flipbook infrastructure was confirmed fully operational with dedicated high-resolution alpha sheets:
* **Fluid Ripples / Impacts**: [`T_Alpha_fluid_impact_ripple_alpha`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_Alpha_fluid_impact_ripple_alpha.uasset) (1024×1024)
* **Metaball Fluid Bursts**: [`T_Alpha_fluid_metaball_flipbook`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_Alpha_fluid_metaball_flipbook.uasset) (2048×2048)
* **Water Droplet Rings**: [`T_Alpha_water_droplet_ring_alpha`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_Alpha_water_droplet_ring_alpha.uasset) (2048×2048)
* **Water Splash Bursts**: [`T_Alpha_water_splash_burst_alpha`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_Alpha_water_splash_burst_alpha.uasset) (1024×1024)
* **Diamond Glints**: [`T_Alpha_diamond_glint_alpha`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_Alpha_diamond_glint_alpha.uasset) (1024×1024)
* **Sparkle Pulses**: [`T_Alpha_sparkle_pulse_flipbook`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_Alpha_sparkle_pulse_flipbook.uasset) (1024×1024)
* **Sparkle Clusters**: [`T_Alpha_sparkle_cluster_alpha`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_Alpha_sparkle_cluster_alpha.uasset) (1024×1024)
* **Harmonic Runes**: [`T_Alpha_Rune_HarmonicStaff`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_Alpha_Rune_HarmonicStaff.uasset) & [`T_Alpha_Rune_SoundwavePulse`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_Alpha_Rune_SoundwavePulse.uasset) (2048×2048)
* **Slash Arcs & Wind Swirls**: [`T_VFX_SlashArc_Alpha`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_VFX_SlashArc_Alpha.uasset) & [`T_Alpha_Ghibli_WindSwirl`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/VFX/Textures/T_Alpha_Ghibli_WindSwirl.uasset) (2048×2048)

---

## 3. Staging Configuration in `L_MelusinaMorning`

### 3.1 Hero Character Actor (`Hero_Melusina_Regalia_v4`)
* **World Coordinates**: `[-2500.0, 1800.0, 1205.5]`
* **Rotation**: `[Pitch=0.0, Yaw=-9.0, Roll=0.0]` (faces directly into `CAM_Hero_01_Meadow`)
* **Skeletal Animation**: [`A_BL_Melusina_Idle_Loop`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Characters/Melusina/Animations/Cascadeur/A_BL_Melusina_Idle_Loop.uasset) set to looping playback on `Body`.
* **Hair Coupling**: `Hair` attached via `set_leader_pose_component(Body)` for synchronized hair physics and wind deformation.
* **Accessory Materials**:
  * `Circlet`: `MS_Gold` = [`M_Regalia_v4_Gold`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Characters/Melusina/Regalia_v4/M_Regalia_v4_Gold.uasset), `MS_GemAqua` = [`MI_Gemstone_Aquamarine_Circlet`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_Aquamarine_Circlet.uasset).
  * `Tiara`: `MS_Gold` = `M_Regalia_v4_Gold`, `MS_GemAqua` = [`MI_Gemstone_CelestialDiamond`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_CelestialDiamond.uasset).
  * `Earrings`: `MS_Gold` = `M_Regalia_v4_Gold`, `MS_GemPurple` = [`MI_Gemstone_VoidOrchid_Earrings`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_VoidOrchid_Earrings.uasset).
  * `Necklace`: `MS_Gold` = `M_Regalia_v4_Gold`, `MS_GemPurple` = `MI_Gemstone_VoidOrchid_Earrings`.

### 3.2 3D Resonance Gem (`GB_Morning_ResonanceGem`)
* **Coordinates**: `[-836.2, 1173.9, 160.9]`
* **Slot 0**: [`MI_HeroGem_Cymatic`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Copernicus/MI_HeroGem_Cymatic.uasset)
* **Slot 1**: [`MI_Gemstone_CelestialDiamond`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_CelestialDiamond.uasset)

### 3.3 Environmental Crystal Cathedral Clusters
* **Meadow Volume**: All 5 InstancedStaticMesh components on `Massive_Biome_CrystalGarden` upgraded to [`MI_Copernicus_CrystalCathedral`](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CrystalCathedral.uasset).
* **Framing Clusters**:
  * `Hero_CrystalCluster_Foreground_L` at `[-2780.0, 2050.0, 1208.0]`, Scale 0.75.
  * `Hero_CrystalCluster_Foreground_R` at `[-2230.0, 2000.0, 1202.0]`, Scale 0.80.

### 3.4 Hero Three-Point Lighting
* **Key Light** (`Hero_Melusina_KeyLight`): `[-2580.0, 2100.0, 1380.0]`, 650 cd, Color `(1.0, 0.94, 0.85)`, Attenuation 400.0, Source Radius 30.0, Cast Shadows = True.
* **Rim Light** (`Hero_Melusina_RimLight`): `[-2420.0, 1550.0, 1360.0]`, 950 cd, Color `(0.75, 0.88, 1.0)`, Attenuation 450.0, Source Radius 40.0, Cast Shadows = False.

---

## 4. Visual Verification Artifacts

```
Saved/Audit/
├── melusina_morning_hero_01_final.png       # 1920x1080 beauty wide from CAM_Hero_01_Meadow
├── melusina_regalia_portrait_yaw0.png       # 1920x1080 50mm head/torso portrait with Regalia
├── gemstone_family_3x3_grid_healed.png      # 9-material multi-angle gemstone validation grid
├── herogem_cymatic_preview.png              # Isolated Cymatic hero gem preview
└── crystal_cathedral_preview.png            # Isolated Crystal Cathedral shader preview
```

---

## 5. Tonight's Render Execution Plan

1. **Batch Beauty Plates (4K Resolution)**:
   * Execute `mi_preview_scenecapture` at 3840×2160 across:
     * `CAM_Hero_01_Meadow` (Hero Master)
     * `CAM_Hero_Melusina_Portrait` (Regalia Close-up)
     * `CAM_Hero_03_RimOverlook` (Environmental Wide)
2. **Turntable / Loop Generation**:
   * Run `capture_gemstone_studio.py` for 12-frame loop sequences of `MI_HeroGem_Cymatic` and `MI_Copernicus_CrystalCathedral` for web showcase integration.
3. **Repository Status**:
   * Level package `L_MelusinaMorning` saved with `dirty_packages: 0`.
   * All modified VFX shaders and material instances safely committed to git branch `main`.
