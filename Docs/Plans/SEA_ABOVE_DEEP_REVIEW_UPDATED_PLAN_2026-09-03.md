# Sea Above — Deep Review & Updated Plan (2026-09-03)

## Honest state of the project

### DONE (verified, on disk)
- 136 SA_HM reef/abyss/jelly placements — reload-verified
- PCG ribbon (83 inst) + garden (27 inst) — reload-verified
- PPV_NikkiDream spawned + unbounded
- Twilight lighting rig (Key + Rim + Fog)
- 4 CineCameraActor on golden spiral path
- 30 trees + 20 plants scattered (BUT floating at wrong Z)
- Atlantis MI override bug fixed (29 actors — overrides cleared)
- Island ring manifest (22 pts)
- Foliage manifest (86 pts)

### BROKEN / UNFINED (what needs real work)

1. **Trees/plants floating at Z=13455** — terrain is at -6k to -14k. Foliage is 6-7km above the ground. Must raycast-snap every instance to the real terrain surface.

2. **Atlantis MI PBR maps wrong** — I only cleared the buggy Copernicus override. The actual KB3D trimsheet materials (BrickStoneTrim, GoldWornA, MarbleWhiteA, etc.) have WRONG albedo/normal/ORM maps per slot. Each mesh has 1-5 material slots that need correct PBR texture assignments. This is the core lookdev problem.

3. **Trimsheet MIs need per-instance tuning** — the KB3D atlas materials need correct tiling, UV channel assignments, and PBR map weights per mesh instance. Not just "clear the override."

4. **PPV blendables not set** — FWeightedBlendable not exposed in this Python build. Must be set in editor UI.

5. **Demo reel captures not done** — no Movie Pipeline output, no portfolio shots.

6. **Melusina EEVEE renders not upgraded** — beauty 7/10, glam 8.5/10.

7. **P0 package_build gate not verified** — your earlier cook needs confirmation.

8. **static_gates not re-run** — stale since placement work.

## Corrected execution order

### Phase 1: Fix the foliage (terrain snap + PBR)
1. Raycast-snap all 30 trees + 20 plants to the real terrain surface (Z=-6k to -14k, not 13455).
2. Review each Atlantis mesh's material slots and assign correct KB3D PBR maps per slot (not a single override).
3. Tune trimsheet MI parameters (tiling, UV channel, PBR weights) per instance.

### Phase 2: Lookdev pass
4. Set PPV blendables in editor UI (MelodiaInk 1.0, MeluColorGrade 0.69, StarryNight 1.0).
5. Verify lighting rig reads correctly with the PPV.
6. Block the golden spiral camera path for capture.

### Phase 3: Demo reel capture
7. Movie Pipeline capture on the 4 golden spiral cams (4K, 24fps).
8. Upgrade Melusina EEVEE renders (beauty 7→8.5, glam 8.5→9).
9. Portfolio assembly (interior + exterior hero shots).

### Phase 4: P0 closeout
10. Verify your earlier cook produced an executable.
11. Re-run static_gates.
12. Record ledger rows.
13. Re-run P0 golden run.

## Key insight I missed

The Atlantis kit uses **trimsheet atlas materials** — each mesh has multiple material slots that share a single atlas texture but need different UV tiling and PBR map weights per slot. Clearing the override restored the authored materials, but the actual PBR maps (albedo, normal, ORM) may still be wrong per slot because the atlas UVs need per-slot tuning. This is a per-mesh, per-slot authoring task, not a bulk override task.

## Immediate next step

Restart editor. Load LV_SeaAbove_Prototype. Verify the 136 SA_HM + 30 trees + 20 plants are visible. Then begin Phase 1: raycast-snap all foliage to terrain, then fix the Atlantis PBR maps slot-by-slot.