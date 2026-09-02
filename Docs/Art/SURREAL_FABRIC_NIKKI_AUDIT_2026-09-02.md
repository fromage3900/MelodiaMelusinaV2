# Surreal Fabric vs Infinity Nikki 10 Principles — Audit (2026-09-02)

**Scope:** Faraway Mother fabric mountains + Melodia fabric masters/MIs. Checked against `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md` §10 principles. Workspace `C:/EnvironmentPortfolio/BS_GodFile`.

## Method
Disk scan: `ls -R Content/EnvSandbox/Materials/Masters` (125 masters), `ls _PROJECT/04_Materials` (165 masters), `find MI_*` 1114 instances, `MF_FabricMountainWPO.uasset` exists, `M_Master_FarawayMother_Fabric` missing, `LV_FarawayMother_Prototype` prototype build script + LOD pipeline JSON.

## Principle-by-principle

| # | Nikki principle | Verdict | Evidence | Gap |
|---|-----------------|---------|----------|-----|
| 1 | Layered specialization, not one giant system | ✅ PASS | MF_FabricMountainWPO 4-layer stack (Macro 50m + Medium 10m + Micro + Wind) wired via MPC Cymatics. Mirrors Nikki cost ladder. | Wind layer aliased to MF_ClothWindDrape — verify amplitude clamping at km scale |
| 2 | Small versatile master family, not variant explosion | ❌ FAIL | 125 masters in EnvSandbox/Masters + 165 in _PROJECT = ~290 masters. Nikki target = 4 (`M_Melodia_Fabric_Master`, TranslucentTextile, SeaGlass, OrganicLaminate). FarawayMother LOD JSON points to phantom `M_Master_FarawayMother_Fabric` (0 bytes on disk, `ls` miss) — compile would fail. MI count 1114:1 master ratio. | Must remap phantom to existing fabric master or create ONE wrapper in small family. |
| 3 | Mix skeletal / Chaos / WPO by garment category | ⚠️ PARTIAL | Tier C (WPO) implemented for terrain. Tiers A/B/D not bound per garment — all 5 kitbash placements use opaque MIs with no cloth-tier tag. No Chaos asset, no VAT, no AnimDynamics for structured bodices. | Add per-placement tier metadata |
| 4 | Particles respond physically to character | ⚠️ SCAFFOLDED | Niagara `NS_Melusina_ChaosDrift` referenced in C++ bridge, dust/fibers design in V3 plan, but no Faraway Mother Niagara placed in level (only fog volume box). | Spawn tension-vector Niagara (Tier C instance) |
| 5 | WPO cheap, Chaos only where collision fidelity matters | ✅ PASS (terrain) / ⚠️ PARTIAL (wardrobe) | Terrain correctly uses WPO only (no Chaos on km mesh). Wardrobe hero pieces (Veil/Gown) should get Chaos but currently share cheap WPO path. | Flag Veil (TranslucentTextile) as Chaos candidate |
| 6 | Streaming as engineering system | ⚠️ PARTIAL | Nanite terrain 32k tris, World Partition level, but no Data Layers for fabric/mantle variants, no VT/RVT, no HLOD config. Heightmap 1024 → OBJ fallback, no 8k VT streaming. | Add DL_FarawayMother_Fabric, verify Nanite + WP streaming budget |
| 7 | Readable lighting/fog, fashion retains headroom | ❌ FAIL | `FM_MoonHaze_Fog` density 0.04, tint correct, but `FM_MoonHaze_PPV` is empty stub (no bloom/exposure restraint, no SceneColorTint set — `pass` block). Bloom would blow sheer fabrics. No exposure bias, no LUT restraint. | Restrained PPV: bloom 0.15, exposure bias +0.5, vignette 0.25 |
| 8 | Photographic / cinematic presentation built-in | ❌ FAIL | No CineCameraActor, no LevelSequence, no warm/cool A/B. Portfolio capture (`capture_to_portfolio.py`) points at Sakura path, not FarawayMother. LOD report notes `apply_in_engine` requires editor but no camera rig. | Add FarawayMother cine rig + capture profile |
| 9 | Precompute expensive relationships | ✅ PASS | Toksvig variance, POM 32→0, Bayer dither, thin-film LUT all precomputed offline (51 maps, 12 sidecars, `specs/lookdev/*.json`). Heightmap manifest hashed. | Phantom master breaks precompute — instances would not cook |
|10 | Scale by screen importance | ✅ PASS | 4-tier LOD 0-15/15-50/50-200/200m+ with Rim 1.0→1.8, WPO 1.0→0.0, res 1024→128. Matches ShellFur screen-size principle. | Wire LOD MIs to ISM or HLOD — currently JSON-only, not bound to meshes |

## Hard counts (disk truth)
- Masters (EnvSandbox/Masters): **125** (.uasset, -Archive excluded) — TOO MANY vs Nikki 4.
- Masters (_PROJECT): **165**
- Fabric-relevant masters: `M_Master_Nikki_Landscape`, `M_Master_Nikki`, `M_Master_Toon_Universal`, `M_Universal_Enhanced_Fabric` (the viable small family). `M_Master_FarawayMother_Fabric` **MISSING** (referenced by 4 LOD MIs + 12 sidecars).
- MIs overall: **~1114** (CR likedescriptor explosion)
- FarawayMother P2 MIs: **6** (`MI_Mother_Gown/Mantle/Veil/Corset/Cradle/Ornament` in `Instances/FarawayMother/P2/`) — correctly small per-monolith family.
- Copernicus PBR MIs: **39** (includes 6 Faraway variants: CelestialSilk, AquaLace, GildedRidge, etc.) — shared inputs to small family, not new masters ✅.
- `MF_FabricMountainWPO`: **exists** (`Functions/MF_FabricMountainWPO.uasset` + `.ush` helpers).
- Cloth tiers wired: **0/N** (no tier tags).
- Lighting headroom: **no** (PPV stub).
- Capture rig: **none** for FarawayMother.

## What this polish fixes (4 changes, Nikki-aligned)
1. **Master-family consolidation (P2)** — Remap 4 FarawayMother LOD instances from phantom `M_Master_FarawayMother_Fabric` to verified `M_Universal_Enhanced_Fabric` (existing small-family fabric master). Document 4-master family instead of adding 126th master. Verified by `specs/lookdev/optical_material_instances.v1.json` patch + `ls` no-new-master.
2. **Cloth tiers per garment (P3)** — New doc `Docs/Art/FARAWAY_MOTHER_CLOTH_TIERS_2026-09-02.md` + annotate `faraway_mother_prototype_build.py` PLACEMENTS with `CLOTH_TIERS` dict (WPO for terrain/ridge, Chaos for Veil/Gown hero, Rigid for Rosette/Capital). Rule: garment piece with gameplay meaning gets expensive solution.
3. **Readable lighting headroom (P7)** — Harden `MOON_HAZE` + `wire_moon_haze()` to set restrained PPV: bloom 0.15, exposure bias +0.5, vignette 0.25, color temp 6500K → preserves sheer fabric read under moonlight.
4. **Photographic tooling + screen-importance wiring (P8+P10)** — New `Content/Python/build_faraway_mother_capture_rig.py` spawns `CineCameraActor_FarawayMother_Hero` + `LevelSequence` with 3 shots (valley / ridge / heart gate), Data Layer binding, and portfolio capture profile for FarawayMother at Nikki bar.

Evidence after fixes: this audit + `FARAWAY_MOTHER_CLOTH_TIERS` + patched JSON + patched prototype_build.py + new capture rig script. Editor materialization (`apply_in_engine`) remains live-editor-gated.
