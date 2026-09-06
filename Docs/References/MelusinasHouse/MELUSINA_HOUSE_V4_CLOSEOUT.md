# Melusina's House V4 — Closeout Document

> Generated: 2026-09-03
> Final blend: `Saved/MelusinasHouse/House_Mansion_v4_FINAL.blend`
> Screenshots: `Saved/Audit/melusinashouse/v4_mansion_{front,three_quarter,side}.png`

## What was built

V4 is the first version where the house is a real editable assembly, not a pile of flat meshes.

**GN_MH_00_MasterAssembly** — 31 nodes, 28 systems joined, 16 master controls exposed.

**28 systems in the master:**
- GN_MH_02 Facade Wall (800v, 3-bay wave, boolean openings, bevel)
- GN_MH_03 Roof Main/Wing/Porch (5692v each, placed at z=3.42/3.1/2.9)
- GN_MH_05 Door Entry + 3 Window variants (arch/round/turret)
- GN_MH_06 Tower (scaled to 10.5m, placed at right of facade)
- GN_MH_07 Rocaille trim (C/S/shell/pearl/clef)
- GN_MH_08 Railing Balusters (height clamped to 1.0)
- GN_MH_09 Awning/Drape (sine sag)
- GN_MH_10 Foliage Scatter
- GN_MH_11 Interior Shell
- GN_MH_13 Penrose Court (placed at rear courtyard)
- GN_MH_14 Walkways (straight + curved, thickness added)
- GN_MH_15 Nikki Bloom + Quarter (0.5 scale, placed west)
- GN_MH_16 Baroque Organ (placed east wing)
- GN_MH_17 Bevel Pass
- GN_MH_18 Musical Swell (ET semitone)
- GN_MH_19-22 Interior rooms (Atrium/Library/Corridor/T)

**6 materials created:** PearlPlaster Pink, Roof IridescentBlue, GoldBrass, WoodWarm, LavenderFabric, AquaGlass (with emission).

**Guides:** CRV_MH_Footprint, CRV_MH_FrontFacade, 1.7m mannequin in MH_GUIDES.

## Verified metrics

```
Master evaluates: 24,654 verts / 24,266 faces
GN groups: 32
Systems joined: 28
Materials: 6
Collections: MH_GN_OUTPUT, MH_GUIDES, MH_SOURCE_KIT, MH_MATERIALS, MH_LIGHTING
```

## Remaining problems (honest)

1. **Bounds too wide.** x=[-17.10, 13.75] = 30.85m (plan: 13.2m). NikkiQuarter at x=-16 and BaroqueOrgan at x=10.5 extend past edges. These were placed per the old expansion script offsets, which assumed a larger scene.

2. **1,198 verts below ground.** NikkiBloom at z=-1.40, WalkStraight at z=-0.21, Awning at z=-0.20. The z-fixes in the final script were applied as group-level transforms but some groups have internal geometry that extends below their origin.

3. **No shingle expansion.** The shingle expansion group was built but not included in the final master join (it was a separate pass that didn't get integrated). The roofs are bare.

4. **No path spine.** Allee ribbon, cherry allee, sando, bridge, teahouse — not in final build. These were planned but the final script focused on fixing existing systems.

5. **Materials not fully assigned.** Only the master object has material assignment. Individual systems in the join don't have per-system materials because Join Geometry merges everything into one output.

6. **Interior not visible.** Interior rooms are inside the facade but Show Interior defaults to False, and even when True, they're occluded by the facade shell.

## What V4 proves

- GN_MH_00_MasterAssembly works as a real editable join
- 28 systems can coexist in one node graph
- Placement transforms correctly position systems
- Height clamps fix oversize systems
- Merge by Distance cleans boolean junk
- The house reads as one structure, not scattered parts

## What V5 would need

1. **Tighten bounds.** Move NikkiQuarter to x=-8, BaroqueOrgan to x=7. Keep within 13.2 x 9.8.
2. **Ground everything.** After placement transforms, add a final "bbox floor" check that shifts any geometry below z=0 up to 0.
3. **Integrate shingles.** Add the shingle expansion group to the master join, driven by roof surface.
4. **Add path spine.** Allee ribbon + cherry allee + sando + bridge per Nikki lens.
5. **Per-system materials.** Use Set Material nodes before the join, with semantic naming.
6. **Interior visibility.** Add a "cutaway" boolean or transparency toggle for the facade when Show Interior is True.
7. **Nikki lens compliance.** The 90-second walk, 7 photo beats, wardrobe hooks.

## Files delivered

```
Tools/house_mansion_v4_final.py          — Master assembly script (18,894 bytes)
Tools/house_mansion_v4_fix_shell.py      — Pass 4A: shell fixes
Tools/house_mansion_v4_fix_dressing.py   — Pass 4B: dressing fixes
Tools/house_mansion_v4_fix_garden.py     — Pass 4C: garden fixes
Tools/house_mansion_v4_fix_interior.py   — Pass 4D: interior fixes
Tools/house_mansion_v4_shingles.py       — Pass 4E: shingle expansion
Tools/house_mansion_v4_screenshots.py    — Render script
Docs/References/MelusinasHouse/
  MELUSINA_HOUSE_V3_PLAN.md              — V3 plan (13,066 bytes)
  MELUSINA_HOUSE_V3_AUDIT.md             — V3 audit (7,114 bytes)
  MELUSINA_HOUSE_V4_PLAN.md              — V4 plan (10,933 bytes)
  MELUSINA_HOUSE_V4_CLOSEOUT.md          — This file
Saved/MelusinasHouse/
  House_Mansion_v4_FINAL.blend           — Final master (24,654 verts)
  House_Mansion_v4_Shell.blend           — Shell systems only
  House_Mansion_v4_Dressing.blend        — Dressing systems only
  House_Mansion_v4_Garden.blend          — Garden systems only
  House_Mansion_v4_Interior.blend        — Interior systems only
  House_Mansion_v4_Shingles.blend        — Shingle expansion only
Saved/Audit/melusinashouse/
  v4_mansion_front.png                   — Front view (520KB)
  v4_mansion_three_quarter.png           — Three-quarter view (360KB)
  v4_mansion_side.png                    — Side view (524KB)
```

## Architecture decisions that held

1. **Append + transform > rebuild.** Loading original groups and adding Transform nodes at the end preserved all the original work while fixing placement.
2. **Height clamps via scale.** Rather than rebuilding window/door groups, scaling Z in a Transform node at the end of the group achieved the correct height without breaking internal topology.
3. **Merge by Distance for boolean junk.** Adding a single Merge by Distance node (0.005) after the bevel in the facade group removed the nonmanifold seams without rebuilding the boolean.
4. **Group-level fixes are composable.** Each fix (placement, scale, merge) was a single node inserted at the end of the group, making them easy to apply and reverse.

## Architecture decisions that failed

1. **Join Geometry merges materials.** When 28 systems join into one output, per-system materials are lost. Need Set Material before join, or use Geometry to Instance and realize at the end.
2. **Group origin vs geometry origin.** Some groups have geometry that extends far below their origin (NikkiBloom, WalkStraight). A z-offset on the group doesn't fix internal below-ground geometry. Need a "bbox floor" node.
3. **Scale 0.5 on tall groups.** NikkiQuarter at 10.19m scaled 0.5 = 5.1m, still taller than plan (4.0m). Need explicit height clamp, not just scale.

