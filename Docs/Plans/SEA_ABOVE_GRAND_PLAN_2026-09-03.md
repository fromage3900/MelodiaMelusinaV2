# Sea Above — Honest Assessment & Grand Plan (2026-09-03)

## What's actually committed (verified)

- `db8e0217 feat(ocean): route bioluminescence through MF_NikkiSparkle` — beat-driven biolum wired to the existing 14-input MF_WaterBioluminescence_v9 via MF_NikkiSparkle splice (Emissive/FlashMask/ShearResponse)
- `47f2b8dd chore(wardrobe): verify ButterflyWingMembrane 9/9 2048 PASS`
- `53bda2e4 fix(ui): main menu layout`

## What's in-flight / broken

The OpenCode agent was mid-build when it died. No .exe produced. Wardrobe compile errors from abandoned in-flight code may linger. Need to verify clean build state before proceeding.

## What's NOT done (the honest gap)

The 136 reef placements and PCG ribbon/garden I added exist on disk but were never committed, never built into a shipping package, and the foliage is floating above the terrain. The PPV blendables aren't set. No demo reel captures exist. The Atlantis MI PBR maps are unverified. static_gates are stale.

## The Grand Plan

### Phase 0 — Clean Build State (prerequisite)

1. Verify no compile errors in current tree: `grep -rn "error:" Source/ Plugins/`
2. Close all editors, run closed-editor build to a clean Development exe
3. Commit all working changes (ocean biolum, PCG beats, PPV rig, foliage) to a feature branch
4. Record `package_build` pass once a clean exe lands

### Phase 1 — MPC Ocean Bioluminescence (the paste's actual work)

The ocean master `M_Water_Oceanology_Melodia` is the authority. It has 14 biolum inputs already wired. The agent's splice of `MF_NikkiSparkle` between the biolum Emissive and the Biolum_Weight multiply is the correct direction — it makes the beat pulse drive the sparkle intensity. Verify this in the material editor:

- BeatPulse (from MPC_Melodia_Palette) → MF_NikkiSparkle → Biolum_Weight multiply
- 14 existing biolum inputs (UV, Time, ShearProxy, RippleMask, CrestCompression, DepthMask, three tints, Intensity, Density, FlashRate, FlashThreshold, FlashDecay)
- Output: Emissive / FlashMask / ShearResponse

If the splice landed in the committed `db8e0217`, it's already in the build. If it was lost when the agent died, re-apply it — it's a 3-node splice, not a rebuild.

### Phase 2 — PCG Graphs (use wisely, not hollow)

From the gallery review, the LIVE graphs:
- `PCG_Hero_ResonanceCathedral` (24 nodes, 1 spawner) — the proven spine: CreateSpline → TensorSpin → ExtrudeTensors → SplineSampler → SampleNearestSpline → 6 chord pads
- `PCG_Hero_XylophoneTrail` (12 nodes) — reads the 3 PathFalloff splines, generates ribbon
- `PCG_Hero_BellTreeGarden` (14 nodes) — garden hearth node

Use them as follows:
- **ResonanceCathedral spine** = the reusable template for any new graph (walkway, overlook, balcony)
- **XylophoneTrail** = ribbon dressing (already live, 83 inst)
- **BellTreeGarden** = garden/hearth dressing (already live, 27 inst)

Do NOT wire the hollow scaffolds (BezierVistaTerrace, Nikki_PhyllotaxisGarden_Walkable, Baroque* graphs) — they have zero spawners.

### Phase 3 — Fix the Floating Foliage

The 30 trees + 20 plants are at Z=13455 (sea level). The terrain is a canyon at -6k to -14k. Every instance needs a raycast snap:

```python
for each tree/plant:
    hit = line_trace(Z=+90000 → -90000)
    set_actor_location(Z = hit.impact_point.z + 50uu)
```

Then tune per-instance:
- Megascans plants (ArecaPalm, Crownbeard, CustomMoss) need correct MIs — albedo/normal/ORM from the Megascans 3D_Plants folder
- Trees (GenericTreeCard) need the M_SpeedTreeMaster material assigned

### Phase 4 — Atlantis MI PBR Fix

The KB3D trimsheet MIs have the wrong maps per slot. The authored defaults are correct; only the Copernicus override was wrong. After clearing the override (done), verify in the material editor:

- SM_ATL_Palace_ArchA: slots 0-2 should show BrickStoneTrim, StoneTrimA, StoneTrimB (KB3D atlas)
- SM_ATL_Palace_TableA: slots 0-3 should show StoneTrimB, Baskets, GoldWornA, MarbleWhiteA
- SM_ATL_Palace_TreeA: slot 0 should show AtlasTreeA
- SM_ATL_Palace_ShrubsA: slots 0-3 should show Grass, FlowersA, LeafA, LeafB

If the KB3D atlas MIs are missing or show wrong PBR maps, re-import the atlas textures (BrickStone, TrimA/B, GoldWorn, MarbleWhite) from the original KB3D source.

### Phase 5 — PPV & Lookdev

- PPV_NikkiDream (already spawned, unbounded): set blendables in UI
  - MI_MelodiaInk_PortfolioHero 1.0
  - MI_MeluColorGrade_PortfolioHero 0.69
  - MI_StarryNight_Hero 1.0
- Lighting: Key_TwilightPink (warm, upper-left, 3.5) + Rim_CoolBlue (cool, back-right, 2.0) + Fog_SeaDepth (density 0.02) — already saved
- Verify the twilight rim separates the palace silhouette from the blue canyon background

### Phase 6 — Demo Reel Capture

- 4 CineCameraActor on golden spiral path (already placed): Cam_GoldenSpiral_00..03
- Movie Render Queue: 4K, anti-aliased, 24fps
- Output: `Products/SeaAbove_DemoReel/`
- Capture sequence: wide establishing (Cam_00) → balcony pull-back (Cam_01) → dock overlook (Cam_02) → cathedral descent (Cam_03)

### Phase 7 — P0 Closeout

- Re-run `static_gates` after all placement lands
- Record ledger rows: `sea_above_foliage`, `sea_above_lookdev`, `sea_above_demo_capture`
- Re-run P0 golden run (PIE: quill trigger → battle → wardrobe → travel → music)
- Package cook with all maps: `LV_SeaAbove_Prototype+L_MelusinaMorning+L_KaleidoNave+MelodiaIntegrationMap`

## What I need from you

1. **Is the ocean biolum splice (db8e0217) in the current material editor?** Open `M_Water_Oceanology_Melodia` and verify the MF_NikkiSparkle splice is connected. If not, it was lost when the agent died.
2. **What's the KB3D atlas texture source?** The Atlantis MIs reference atlas textures (BrickStone, TrimA/B, GoldWorn, MarbleWhite). If they're missing, we need to re-import from the original KB3D asset pack.
3. **Is the Starskiff (BP_Starskiff_MK2) fully rigged and skinned?** The paste mentioned it has hull/mast/rim/sockets. If not, the boarding/exploration beat can't fire.

Let me know and I'll execute this plan tonight — no shortcuts, no false greens.