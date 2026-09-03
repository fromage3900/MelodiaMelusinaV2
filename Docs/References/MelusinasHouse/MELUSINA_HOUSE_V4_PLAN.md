# Melusina's House V4 — Final Build Plan

> Parent: MELUSINA_HOUSE_V3_AUDIT.md — the honest defect list
> This file: the fix plan and execution order
> Status: STAGING

## V4 thesis

V3 proved the assembly works (31 groups appended, master evaluates to 24K verts). V4 fixes every defect the audit found:

1. Placement — every system gets a Transform with correct offset from plan
2. Scale — every system gets correct scale/height clamp
3. Topology — boolean junk deleted, loose verts removed, flat geometry fixed
4. Grounding — every system at z >= 0.00
5. Shingles — expand 63-instance proof onto 3 roofs
6. Materials — assign 6 materials by semantic naming
7. Path spine — allee ribbon + cherry allee + sando + bridge
8. Screenshots — render 3 views with materials

## Defect → Fix map

| # | Defect | System | Fix |
|---|---|---|---|
| 1 | All systems at origin | All 31 | Add Transform nodes in master join per-system |
| 2 | Height 3.35 vs 1.20 | Window_Round_M | Clamp to 1.20 in master transform |
| 3 | Height 10.19 vs 4.00 | NikkiQuarter | Scale 0.5 in master transform |
| 4 | Height 2.04 vs 1.00 | RailingBalusters | Clamp to 1.00 |
| 5 | Height 3.86 vs 2.35 | Door_Entry | Clamp to 2.35 |
| 6 | Height 4.60 vs 3.00 | NikkiBloom | Scale 0.5 in master transform |
| 7 | z=-1.05 | Door_Entry | Translate +1.05 in Z |
| 8 | z=-1.40 | NikkiBloom | Translate +1.40 in Z |
| 9 | z=-0.21 flat | WalkStraight | Add extrude thickness 0.15, translate +0.21 |
| 10 | z=-0.20 | Awning | Translate +0.20 |
| 11 | z=-0.12 | WalkCurve | Translate +0.12 |
| 12 | z=[0,0] flat | Window_Turret_S | Fix group: add height param, set to 0.5 |
| 13 | 93 loose verts | Door_Entry | Delete Loose + Merge by Distance |
| 14 | 93 loose verts | Rocaille_Clef | Delete Loose |
| 15 | 56 nonmanifold | CurvedWallShell_v2 | Merge by Distance 0.005 + delete interior |
| 16 | 30 ngons | CurvedWallShell_v2 | Delete interior faces from boolean |
| 17 | 80 tris | NikkiBloom | Re-cap topology |
| 18 | Roofs at z=0.5-3.0 | RoofMain/Wing/Porch | Translate to wall top z=3.42 |
| 19 | Tower at z=0-7.92 | TowerChimney | Translate to z=3.42, extend to 10.5 |
| 20 | Penrose at origin | PenroseCorridor | Translate to rear courtyard y=-10 |
| 21 | No shingle expansion | RoofMain/Wing/Porch | Expand 63-instance proof to all 3 roofs |
| 22 | No path spine | New | Allee ribbon + cherry allee + sando + bridge |
| 23 | No material assignment | All 29 objects | Assign by semantic naming |
| 24 | No guide curves | New | CRV_MH_Footprint, FrontFacade, etc. |
| 25 | No mannequin | New | 1.7m capsule in MH_GUIDES |

## V4 execution order

### Phase 1: Fix existing systems (Passes 4A-4E)

**Pass 4A: Fix core shell groups** (Facade, Roofs, Tower, Foundation)
- Fix CurvedWallShell_v2 boolean (merge distance, delete interior, remove ngons)
- Fix RoofMain/Wing/Porch placement (translate to z=3.42, add offsets)
- Fix TowerChimney height (extend to 10.5m) and placement
- Add GN_MH_01_FoundationPorch as a real group (not flat mesh)

**Pass 4B: Fix dressing systems** (Windows, Door, Railing, Awning)
- Fix Window_Turret_S zero height (rebuild with correct socket)
- Fix Window_Round_M height clamp
- Fix Door_Entry loose verts + height
- Fix RailingBalusters height
- Fix WalkStraight thickness (add extrude)
- Ground all (translate to z >= 0)

**Pass 4C: Fix garden systems** (Bloom, Quarter, Penrose, Walkways, Organ)
- Scale Bloom + Quarter to 0.5
- Place Penrose at rear courtyard
- Place Bloom at (-9, 6, 1.4), Quarter at (-16, -6, -1.05)
- Place Organ at east wing (10.5, -5, 0)
- Fix Rocaille_Clef loose verts
- Fix NikkiBloom cap topology

**Pass 4D: Fix interior systems** (Atrium, Library, Corridor, T, InteriorShell)
- Place interior rooms inside facade volume
- Cap ngon ceilings (triangulate or fill)
- Connect corridor-T-atrium volumetrically

**Pass 4E: Shingle expansion**
- Give 3 roof ribbons clean UV maps
- Expand 63-instance Sample UV Surface proof per-roof
- 3-5 scallop variants, unrealized, hue drift

### Phase 2: Build new systems (Passes 4F-4G)

**Pass 4F: Path spine + threshold kit**
- Allee ribbon (MEL_allee_ribbon, Length 10-12, S-Curve 1.2)
- Cherry allee (build_zen_cherry_allee, staggered trunks)
- Sando (build_zen_sando, paving 2.2m, lantern rhythm)
- Bridge (ZEN_BRIDGE + build_zen_water_edge)
- Teahouse (build_zen_teahouse, irimoya roof)

**Pass 4G: Material assignment**
- Create 6 materials (PearlPlaster, RoofBlue, GoldBrass, WoodWarm, LavenderFabric, AquaGlass)
- Assign by semantic naming convention
- Set interior emission on AquaGlass

### Phase 3: Final assembly + verification (Passes 4H-4J)

**Pass 4H: GN_MH_00_MasterAssembly V4**
- All fixed groups + new path/teahouse
- Placement transforms for every system
- 16 master controls + 4 path controls
- Show Interior / Show Set Dressing switches

**Pass 4I: Guide curves + mannequin**
- CRV_MH_Footprint (3 overlapping pods)
- CRV_MH_FrontFacade (concave-convex-concave)
- CRV_MH_Porch, CRV_MH_RoofMain/Wing/Porch, CRV_MH_Rocaille
- LOC_MH_Tower, CUT_MH_DoorsWindows
- 1.7m mannequin in MH_GUIDES

**Pass 4J: Screenshots + audit**
- Render front/three-quarter/side with materials
- Dusk variant (lantern emission)
- Final audit: zero FAIL, bounds = plan, topo clean

## Correct placement offsets (from plan + old scripts)

These are the verified correct world-space offsets for each system:

| System | X | Y | Z | Scale | Source |
|---|---|---|---|---|---|
| Facade Wall | 0 | 0 | 0 | 1.0 | Plan s3 |
| Roof Main | 0 | 0 | 3.42 | 1.0 | Plan s5 (on wall top) |
| Roof Wing | -2.5 | -1.0 | 3.1 | 1.0 | Old script placement |
| Roof Porch | 1.0 | 4.6 | 2.9 | 1.0 | Old script placement |
| Tower | 5.5 | -3.0 | 3.42 | 1.0 | Plan s7, right of facade |
| Door Entry | 0 | 0.94 | 0.0 | 1.0 | Center bay, wall top |
| Window Arch L | -4.4 | -0.47 | 1.8 | 1.0 | Shoulder bay |
| Window Round M | 2.6 | -0.33 | 1.8 | 1.0 | Center bay |
| Window Turret S | 5.5 | -3.0 | 6.0 | 1.0 | Tower level |
| Railing | 0 | 1.8 | 0.0 | 1.0 | Porch edge |
| Awning | 0 | 0.94 | 3.2 | 1.0 | Above door |
| Walkway Straight | 0 | 7.5 | 0.25 | 1.0 | Front approach |
| Walkway Curved | 7.0 | -4.0 | 0.05 | 1.0 | Feeds Penrose |
| Penrose Court | 0 | -10.0 | 0.0 | 1.0 | Rear courtyard |
| Nikki Bloom | -9.0 | 6.0 | 1.4 | 0.5 | West garden |
| Nikki Quarter | -16.0 | -6.0 | -1.05 | 0.5 | Far west |
| Baroque Organ | 10.5 | -5.0 | 0.0 | 1.0 | East wing |
| Musical Swell | 0 | 0 | 0 | 1.0 | Center test |
| Rocaille C/S/Shell/Pearl/Clef | 0 | 0.94 | 2.5 | 1.0 | Trim line |
| Atrium | 0 | 0 | 0 | 1.0 | Inside facade |
| Library | -3.0 | 0 | 0 | 1.0 | Left interior |
| Corridor East | 3.0 | 0 | 0 | 1.0 | Right interior |
| T Junction | 3.0 | -2.0 | 0 | 1.0 | Connects corridor |
| Interior Shell | 0 | 0 | 0 | 1.0 | Full interior |
| ShingleMain | 0 | 0 | 3.42 | 1.0 | On roof main |
| ShingleWing | -2.5 | -1.0 | 3.1 | 1.0 | On roof wing |
| ShinglePorch | 1.0 | 4.6 | 2.9 | 1.0 | On roof porch |

## Correct height clamps

| System | Current H | Target H | Method |
|---|---|---|---|
| Window_Round_M | 3.35 | 1.20 | Scale Z to 0.36 |
| NikkiQuarter | 10.19 | 4.00 | Scale 0.5 (makes it ~5.1, then clamp) |
| RailingBalusters | 2.04 | 1.00 | Scale Z to 0.49 |
| Door_Entry | 3.86 | 2.35 | Scale Z to 0.61 |
| NikkiBloom | 4.60 | 3.00 | Scale 0.5 (makes it ~2.3, ok) |

## Topology fix plan

**CurvedWallShell_v2 (facade):**
1. Add Merge by Distance (Distance=0.005) after boolean
2. Add Delete Geometry (select interior faces by normal direction)
3. Add a second Merge by Distance (0.001) to clean remaining seams
4. Expected result: 0 nonmanifold, 0 ngons, ~780 verts (down from 800)

**Door_Entry:**
1. Add Delete Loose (threshold 0.01)
2. Add Merge by Distance (0.001)
3. Expected result: ~280 verts (down from 379), 0 loose

**Rocaille_Clef:**
1. Add Delete Loose
2. Expected result: ~80 verts (down from 179), 0 loose

**Window_Turret_S:**
1. Rebuild the group entirely — the current one has z=[0,0]
2. Use Mesh Cube (0.5 x 0.15 x 0.5) → Bevel → Output

**WalkStraight:**
1. Add Extrude Mesh (Offset=0.15, Selection=True) after the existing plane
2. Add another Extrude for thickness
3. Should be a slab, not a plane

**Roof ngons (253 per roof):**
1. Change Extrude Mesh from Selection=True to Individual
2. OR add a separate triangulate step for the cap
3. Target: 0 ngons, all quads + tris

## Master control mapping (16 controls)

| Control | Drives | Group inputs |
|---|---|---|
| Facade Wave | Facade wave amplitude | GN_MH_02:Facade Wave |
| Wall Height | Facade wall height | GN_MH_02:Wall Height |
| Wall Thickness | Facade thickness | GN_MH_02:Wall Thickness |
| Roof Main Rise | Main roof height | GN_MH_03_RoofMain:Roof Rise |
| Roof Curl | Eave curl amount | GN_MH_03:Roof Curl |
| Eave Overhang | Eave extension | GN_MH_03:Eave Curl |
| Tower Height | Tower vertical | GN_MH_06:Tower Height |
| Tower Diameter | Tower width | GN_MH_06:Tower Diameter |
| Shingle Density | Shingle count | GN_MH_04:Density |
| Trim Density | Rocaille count | GN_MH_07:Density |
| Ornament Asymmetry | Trim omission | GN_MH_07:Asymmetry |
| Flower Density | Foliage count | GN_MH_10:Density |
| Random Seed | All random | All seed inputs |
| LOD Preview | Instance count | All instance inputs |
| Show Interior | Interior switch | GN_MH_00:Show Interior |
| Show Set Dressing | Dressing switch | GN_MH_00:Show Set Dressing |

## Path controls (4 additional)

| Control | Drives |
|---|---|
| Path Length | Allee ribbon length |
| S-Curve | Allee ribbon curvature |
| Canopy Spread | Cherry allee spread |
| Petal Density | Flower count |

## Verification gates

After each pass, verify:
1. Zero FAIL in Blender headless run
2. Bounds: every object z0 >= 0.00
3. Bounds: master within x=[0,13.2], y=[0,9.8], z=[0,10.5]
4. Topology: 0 nonmanifold, 0 loose verts (except open-edge systems)
5. Node count: master > 50 nodes (proving real assembly, not flat)

## File structure

```
Tools/house_mansion_v4_fix.py       — Phase 1: fix existing systems
Tools/house_mansion_v4_new.py       — Phase 2: new path/teahouse
Tools/house_mansion_v4_master.py    — Phase 3: final assembly
Tools/house_mansion_v4_audit.py     — Verification
Saved/MelusinasHouse/House_Mansion_v4_Master.blend — Final output
```

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Boolean fix destroys facade | Medium | High | Save backup blend first; test on copy |
| Scale clamp breaks child params | Medium | Medium | Test each system independently before assembly |
| Path spine too long for scene | Low | Medium | Use S-Curve to fold into available space |
| Shingle UV projection fails | Medium | High | Use proven 63-instance method; fix UV first |
| Interior doesn't fit inside facade | Medium | Medium | Scale interior to fit; facade is 13.2x9.8 |
| Too many verts for real-time | Low | Medium | Keep instances unrealized; LOD control |

