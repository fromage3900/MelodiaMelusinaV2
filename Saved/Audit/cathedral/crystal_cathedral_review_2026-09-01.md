# Crystal Cathedral — Review of Existing Houdini Cathedral Plans

**Date:** 2026-09-01 01:00 UTC
**Scope:** All houdini + copernicus + PCG cathedral assets on disk
**Hython:** 22.0.368

## Existing Cathedral Houdini Plans — Inventory

### 1. Houdini Fractal Cathedral (NEW — hython 22.0.368)
- **Tool:** `Tools/Houdini/cathedral/build_fractal_cathedral.py` (5.8K, 116 lines, numpy + hython)
- **Meshes:** `Saved/Audit/cathedral/`
  - `SM_P4_Cathedral_Fractal.obj` — 1364 verts / 657 faces / 96KB — depth 4, span 10m, height 20m, 8 bays, fractal arch subdivision + diagonal vault ribs + floor, Chladni wobble (tracery 0.85)
  - `SM_P4_Cathedral_RoseWindow.obj` — 782 verts / 50 faces / 43KB — Chladni rose `cos(8πu)cos(6πv)-cos(6πu)cos(8πv)` disc, radius 4.2m
  - `SM_P4_Cathedral_Deep.obj` — 1216 verts / 589 faces / 85KB — depth 5 variant
  - `SM_P4_Cathedral_Grand.obj` — duplicate of Fractal for UE import alias
- **Manifest:** `cathedral_fractal_manifest.json` — schema `melodia.cathedral_fractal.v1`, seed 20260901, nanite true, scale meters→cm ×100
- **GN Bridge:** `MEL_p4_fractal_cathedral` (god_molts) — 8 inputs (Recursion Depth, Arch Span, Vault Height, Tracery Density, Bay Count, Buttress Depth, Rose Mode N/M), passthrough until Blender smoke
- **Copernicus:** `FractalCathedral` 9-map PBR — 4.2M (BaseColor 598K, Height 838K, ORM 1009K, Iridescence 379K)
- **Status:** PRESENT, hython-verified, editor-open safe, ready for UE import

### 2. PCG Cathedral Grammar (Python — Monolith/PIE)
- **Tool:** `Content/Python/build_cathedral_grammar.py` (native PCG, not houdini)
- **Architecture:** Real recursive grammar — `_rule_buttress` recurses with `BUTTRESS_SCALE_STEP=0.5` (fractal), `_rule_pinnacle` terminal, `_rule_bay` spawns floor/wall/vault + 2 buttress seeds
- **Params:** BAY_W 8m, BAY_LEN 6m, WALL_H 10m, PIER 1.2×1.0×8.0m, scale step 0.5
- **Outputs:** `PCG_CathedralGrammar_*` in `/Game/EnvSandbox/PCG/Styles/Baroque` (Cube 100cm scaled per point)
- **Smoke:** `build_nave(bay_count=1, buttress_depth=2)` M1, `build_nave(bay_count=8, buttress_depth=4)` M3
- **Relation to Houdini:** Houdini mesh is static OBJ (nanite), PCG is runtime scatter — complementary, not competing. Houdini = hero mesh, PCG = population/kit.

### 3. Liquid Cathedral — Gaea WorldGen
- **File:** `Docs/WorldGen/GAEA_SETUP_LIQUID_CATHEDRAL_2026-08-24.json`
- **Source:** Aster 12km Yoshino, window 5000×3000m, Gaea 2.2.3 Canyon River with Sea (18 nodes), resolution 4097, 52 erosion iters, canyon 85m, waterline 36m
- **Outputs:** `LiquidCathedral_4097.obj` + height16 + flow/slope/curvature masks, UE target Mesh Terrain, water separate, PCG profile cathedral
- **Relation:** Basin/terrain that cathedral sits on — not the cathedral itself. Houdini cathedral meshes are dressings on this terrain.

### 4. Kitbash Cathedral — 41 Static Meshes
- **Source:** `KitbashExport/CathedralKit` → `Content/EnvSandbox/Meshes/Cathedral/` (4.0M)
- **Meshes:** SM_Cathedral_Altar, BeatMedallion, Bed, BifrostBridge, Buttress, Chandelier, Chapel, ChapterHouse, CombatFloor, Crypt, CryptVault, EscherBelvedere, EscherBridge, EscherPenrose, EscherWaterfall, Garland, HarmonicOrb, LancetWindow, MusicOrb, ... 41/41 imported 2026-08-13
- **Relation:** Kit pieces for set dressing — houdini fractal cathedral is the hero nave that kit pieces populate.

### 5. Copernicus Crystal / Glitter Family (Houdini Copernicus — hython)
- **Variants:**
  - `DancingCrystals` — 153 frames (anim), crystal facets + Chladni
  - `GlitterCrystal` — 153 frames, `GlitterGold/Holographic/Iridescent/Rainbow` — 117-153 frames each, glitter + iridescence
  - `FrostBloom` — 9 maps, frost + bloom petals (new P4, 2026-09-01)
- **Maps:** 9-map PBR (BaseColor/Normal/ORM/Height/Roughness/Metallic/Emissive/Opacity/Iridescence) — same contract as FractalCathedral
- **Tool:** `Tools/Houdini/copernicus/copernicus_cymatic_parallax.py` — 29 variants, 9-map, `cymatic_chladni` + `warped_fbm` + palette `mix`
- **Relation to Cathedral:** No crystal cathedral yet — this is the material opportunity. Crystal variants prove the houdini-copernicus path can drive faceted iridescence at 1024/2048.

## Gap — No Crystal Cathedral Houdini Mesh Yet

All cathedral houdini plans are **stone/gothic** (FractalCathedral stone/gold/glow palette). Zero have crystal facets. The P4 `MEL_p4_fractal_cathedral` description mentions "fractal arch" but not crystal growth. The 8 new cymatics (PearlWeave, FrostBloom) touch crystal but not cathedral.

## Crystal Cathedral Proposal — Expand, Don't Rebuild

**Follow Emerging Toolchain §9:** Extend PRESENT houdini mesh, don't duplicate.

**Idea:** Crystal growth on fractal ribs — same nave (1364 verts) but:
- Vault ribs extrude as crystal shards (prismatic pillars, 6-12 facets, height = Chladni amplitude × 1.5m + fBm)
- Rose window becomes faceted crystal rosette (hexagonal tiling + iridescence from GlitterCrystal palette)
- Buttresses terminate in crystal pinnacles (scale 0.5 recursion, but crystal material)
- Floor gains crystal geode inlays (Voronoi cells)

**Houdini Path (hython, same file):**
- Add `build_crystal_cathedral.py` — imports `build_fractal_cathedral` as base, adds `crystal_shards` pass: for each rib quad, spawn 3-5 prisms with `crystal_shape` (from copernicus), height driven by `cymatic_chladni(n=8,m=6)` + `warped_fbm`
- Palette from `GlitterCrystal`/`DancingCrystals`: crystal (220,240,255), facet (180,200,255), iridescence 0.7-0.9, metallic 0.1, emissive crystal glow
- 9-map bridge same as FractalCathedral — crystal Height/Iridescence/Emissive already proven at 1024
- Output: `SM_P4_Cathedral_Crystal.obj` + `SM_P4_Cathedral_Crystal_Rose.obj` — same scale/bays, nanite true

**GN Bridge:**
- New builder `MEL_p4_crystal_cathedral` (god_molts) — 9 inputs: extends fractal 8 + Crystal Density 0-1 + Facet Count 3-12
- Or extend `MEL_p4_fractal_cathedral` with Crystal Density toggle — prefers new builder to avoid breaking 1364v baseline

**Copernicus Bridge:**
- Crystal cathedral uses `FractalCathedral` + `GlitterCrystal` palette mix — no new variant needed, or add `CrystalCathedral` as 30th variant (crystal + gothic stone)

**Validation:**
- hython `--crystal 0.7 --facets 8` → OBJ + manifest `melodia.cathedral_crystal.v1`
- `cross_path_validation.py --check hython --variant GlitterCrystal` already PASS — crystal path proven
- UE import: same `Saved/Audit/cathedral/` → Monolith `import_asset` → `static_gates` clean

**Next Command:**
```bash
hython Tools/Houdini/cathedral/build_crystal_cathedral.py --crystal 0.7 --facets 8 --bays 8
```

**Files to Create:**
- `Tools/Houdini/cathedral/build_crystal_cathedral.py` (crystal shard pass)
- `deploy/surreal_arch/melodia_gn/p4_crystal_cathedral.py` (GN builder)
- `Saved/Audit/cathedral/crystal_cathedral_manifest.json` + OBJs (disk, manifest committed)
