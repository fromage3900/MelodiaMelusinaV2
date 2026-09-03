"""
Kitbash Monetization Plan — EnvSandbox SDF VFX + Foliage Suite
==============================================================
Platform: Cursors Direct (with optional Fab/UE Marketplace)
Target: Procedural environment artists, VFX artists, world builders

---

INVENTORY — What we have to package
====================================

I. SDF Materials (3 tiers)
   Tier 1 — Core SDF Masters:
     - M_SDF_ParallaxPulse_Niagara — band-relief parallax (needs compile fix)
     - M_MusicalSDF_PulsingGeometry_Niagara — crystalline HLSL SDF, unlit
     - M_Niagara_Foliage — clean unlit sprite base (0 compile errors)
     - M_ToonFoliage — existing masked foliage master
   Tier 2 — Melusina Texture MIs (12):
     Cello, Crystal, Note, Treble, FloralBrickGrayScale, Leafcool,
     Stem1, Stembell, Grass, LandscapeGrayscale, Soil, Weave
   Tier 3 — Foliage Card MIs (5):
     Grass, Leaf1-3, Vine — wired to FoliageCards textures

II. Niagara Systems (10 Sakura + 6 new = 16 total)
   Original (Phase 0):
     NS_SakuraPetals, Petals_v2, GroundPetals, PetalGust,
     DreamSparkle, LanternMotes, PondShimmer, WaterPetals,
     WindRibbonGust, ConstellationDraw
   New SDF Systems:
     NS_SDF_ParallaxPulse, NS_SDF_PulsingGeometry
   New Foliage Systems:
     NS_SDF_Foliage_Grass, NS_SDF_Foliage_Bush, NS_SDF_Foliage_Vine
   Experimental:
     NS_SDF_ParallaxFish

III. Material Functions (1 new + existing):
     MF_FoliageWindWPO — wind animation skeleton (populate WPO graph)
     MF_SDF_BandRelief — existing SDF band generator
     MF_ParallaxCore, MF_RealParallax, MF_SpaceParallax — existing POM

IV. Global Control:
     NPC_SakuraDream — 6-parameter Niagara Parameter Collection
     ENV_SakuraVFX — EffectType with scalability settings

V. 14 Melusina Texture Families (88 textures total):
     Cello, Crystal, Note, Treble, FloralBrickGrayScale, Leafcool,
     Stem1, Stembell, Grass, LandscapeGrayscale, Soil, Weave,
     FoliageCards, Standalone

---

VDF ENVIRONMENT BLEND INTEGRATION — Review
============================================

Unreal Engine's Virtual Distance Field (VDF) system enables:
  - SDF-based material blending at pixel level
  - Seamless transitions between landscape and scattering
  - Distance-driven LOD for VFX particles

Integration approach for EnvSandbox:
  1. Use MF_SDF_BandRelief as weight generator for VDF blend
  2. VDF blends between base landscape (M_Master_Toon_Landscape_HeightBlend)
     and Sakura VFX scattering (grass, petals, foliage)
  3. SDF textures (Perlin, Voronoi, Marble) drive the distance field
     for organic transition patterns
  4. The MPC/NPC controls global blend strength via DreamIntensity param

Pre-requisites for VDF integration:
  [ ] Enable Virtual Texture support in Project Settings
  [ ] Create VDF blend material function (MF_VDF_Blend)
  [ ] Wire SDF textures as distance sources into landscape material
  [ ] Test with PCG_ExperimentalFoliage_Grass as scatter input
  [ ] Benchmark performance on mid-range GPU

Priority: POST-MVP — requires landscape material edits which are
outside the current Niagara/VFX scope.

---

KITBASH PRODUCT STRUCTURE — Cursors Direct
===========================================

Product Name: "Sakura Dream — SDF VFX + Foliage Kitbash"
Tagline: "Procedural Sakura environment suite for Unreal Engine 5.8"

Tiers:
  Basic ($15) — 10 Niagara systems + 5 MIs + documentation
  Standard ($30) — Basic + 12 Melusina MIs + 5 foliage MIs + 3 foliage systems
  Premium ($50) — Standard + SDF masters + NPC + EffectType + PCG graphs
  Studio ($100) — Premium + full source (MFs, SDF textures, Melusina textures)

Wix Website Sections (update plan):
  1. Hero — particle video showcase (DreamSparkle + PetalGust)
  2. Features grid — SDF parallax, Niagara sprites, WPO foliage
  3. Product tiers — 4 pricing cards with feature breakdown
  4. Tech specs — UE 5.8, Niagara, Substrate Toon
  5. Gallery — 6 system previews + 3 environment shots
  6. FAQ — installation, compatibility, refunds

Next Steps:
  [ ] Fix M_SDF_ParallaxPulse_Niagara compile error (float2*float3)
  [ ] Bake Melusina MIs directly to /Game/EnvSandbox for migration
  [ ] Create PCG scatter graphs for foliage systems
  [ ] Write Kitbash migration script (migrate all assets to clean prefix)
  [ ] Generate 1080p preview videos for all 16 Niagara systems
  [ ] Build Cursors Direct listing page with tier dropdown
  [ ] Link Wix store to Cursors Direct API
"""
