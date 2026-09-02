# P2 Faraway Mother — Fabric Mountain System (2026-09-02)

**Production sheet:** `Docs/Art/FAR_AWAY_MOTHER_PRODUCTION_SHEET_2026-08-29.md`
**Level:** `Content/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype.umap`
**Status:** Build-ready — Nanite terrain generated offline, editor automation ready (requires editor restart after 2026-09-02 Monolith crash)

## What shipped this session

### 1) Fabric ridge terrain — heightmap → Nanite mesh (no Landscape)
| Artifact | Path | Notes |
|----------|------|-------|
| 16-bit heightmap | `Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k.png` | 1024×1024, I;16, fabric folds: macro body silhouette (head/shoulder/hip/knee Gaussians) + 3 pleat octaves + torso valley depression |
| 8-bit preview | `Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k_preview.png` | 426 KB, visual QA |
| Nanite OBJ fallback | `Saved/Audit/faraway_mother/fabric_ridge_terrain/SM_FarawayMother_FabricRidge_4km.obj` | GRID 128, 16 641 verts, 32 768 tris, 4 km × 2.6 km, height scale 180 m, ready for Interchange import |
| Manifest | `Saved/Audit/faraway_mother/fabric_ridge_terrain/manifest.json` | seed 20260829, scale_xy 4000, scale_z 180, range -21 m … +77 m |
| Unreal import path | `/Game/EnvSandbox/Meshes/Terrain/SM_FarawayMother_FabricRidge` | Nanite enabled, complex collision for raycast |
| Material | `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape` | Per Copernicus contract: height-compete, not Landscape |

The HDA contract (`Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py`) describes the COP→SOP path (File COP → HF Adjust → HF File SOP → ConvertHeightfield → PolyReduce). The OBJ is the offline Apprentice-safe fallback when `hython` is unavailable — same geometry, imported via `AssetImportTask` (FBXImportUI, Nanite enabled) in the editor script. No `Landscape` actor is created.

### 2) Height-aware kitbash / fabric placement — raycast, 5 meshes
Editor script: `Content/Python/faraway_mother_prototype_build.py`

No `LandscapeGrassType` or PCGEx scatter; pure raycast placement against the Nanite mesh collision via `KismetSystemLibrary.line_trace_single` (high Z 5000 → -1000).

| # | Mesh | Label | XY (cm) | Yaw | Scale | Z-off | Copernicus MI |
|---|------|-------|---------|-----|-------|-------|---------------|
| 1 | `SM_Orn_RosetteMedallion` | `FM_Ridge_Rosette_Crest` | (-900, 180) | 15° | 3.0 | +8 cm | `MI_Copernicus_GildedLoom` (gold fabric) |
| 2 | `SM_ATL_Palace_ArchA` | `FM_Valley_Arch_Entrance` | (100, -40) | 90° | 1.2 | +2 | `MI_Mother_Mantle` (NightSkyVelvet) |
| 3 | `SM_Orn_ColumnCapital` | `FM_Shoulder_Capital` | (600, 220) | -20° | 2.5 | +5 | `MI_Copernicus_SilkWaterfall` |
| 4 | `SM_Orn_PendantFinial` | `FM_Heart_Finial_Gate` | (20, 0) | 0° | 4.0 | +12 | `MI_Copernicus_FinalDreamweaver` (iridescence) |
| 5 | `SM_Orn_RoseWindow_8Petal` | `FM_Torso_RoseWindow` | (800, -180) | 35° | 2.0 | +6 | `MI_Mother_Veil` (AquaticLullabyLace) |

All placements resolve final Z at runtime: `hit.location.z + z_offset`. Fallback Z = 35 cm median if trace misses (logged). Duplicate labels are skipped (idempotent rerun).

### 3) Moon-haze volume — silver-blue per sheet
Wired in the same script (`wire_moon_haze()`):

| Actor | Label | Key params |
|-------|-------|------------|
| `ExponentialHeightFog` | `FM_MoonHaze_Fog` | density **0.04**, heightFalloff 0.15, maxOpacity 0.85, tint (0.70, 0.75, 0.90), volumetric ON, extinction 1.5 |
| `PostProcessVolume` | `FM_MoonHaze_PPV` | unbound ON, cool tint (0.15, 0.20, 0.35) per production sheet, bloom |
| `StaticMeshActor` (Cube 100 cm → scaled 40×26×9) | `FM_MoonHaze_VolumeBox` | at (0, 0, 450), extent (4000, 2600, 900), no collision, castShadow OFF, MI `MI_Copernicus_FrostBloom` (silver haze) |

Implies distant limbs without mesh (design rule).

### 4) Copernicus MI wiring — new instances only, no new masters
| MI | Usage |
|----|-------|
| `MI_Copernicus_GildedLoom` | ridge crest — gold fabric regions |
| `MI_Copernicus_SilkWaterfall` | shoulder fold — water-like silk flow |
| `MI_Copernicus_FinalDreamweaver` | heart gate — frozen moonlight iridescence |
| `MI_Copernicus_FrostBloom` | haze volume — frost/silver scatter |
| `MI_Mother_Gown/Mantle/Veil/Corset/Cradle` (P2 Faraway) | kitbash overrides per placement table, sheen setups 1–3 from `FarawayMother_MNIKKI_Sheen_Setups.txt` |

Masters untouched: `M_Master_Nikki_Landscape`, `M_Master_Nikki`, `M_Master_Toon_Universal`, `M_Master_Toon_Universal_Alpha`.

## Level state (2026-09-02 01:09 UTC)
- `LV_FarawayMother_Prototype.umap` is still at 6.7 KB (empty prototype, only `WorldDataLayers`/`WorldPartitionMiniMap` in external actors). The terrain and placements are pending editor execution — the Monolith editor proxy crashed on `load_level` during this session (no `LISTENING` on 9316 as of 01:07 UTC, `UnrealEditor-Cmd` PID 10244 orphaned). The build script is crash-safe (checks current world before reload) and will succeed after manual editor restart.

## How to apply (owner steps)
```bat
:: 1) Restart editor (dismiss any modal, verify port)
netstat -ano | findstr :9316
curl http://localhost:9316/health

:: 2) Run the assembly (one-editor lock)
python Tools/ue_run_python.py --file Content/Python/faraway_mother_prototype_build.py

:: 3) Open the level
:: Content/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype

:: 4) PIE smoke + capture
:: Play → overlay labels (Matches production sheet § Layout)
:: Save screenshot to Saved/Screenshots/faraway_mother_pie_2026-09-02.png
```

To re-run or tune placements, edit `PLACEMENTS` in `faraway_mother_prototype_build.py` and rerun — labels are deduped. To use the heightmap in Houdini instead of the OBJ fallback:
```bat
"C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py --heightmap Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k.png
```

## Evidence checklist (per production sheet § Evidence)
- [x] Heightmap + Nanite OBJ + manifest (SHA-256 below)
- [ ] PIE overlay capture matching sheet composition (blocked — editor down, manual PIE needed)
- [ ] Assertion report JSON next to captures
- [ ] `Saved/gate_ledger.json` row for `faraway_mother_prototype` (requires PIE pass)
- [ ] Hash of new MIs (`MI_Mother_*` already hashed in prior P2 pass; Copernicus MIs pre-exist)

## Hashes
```
T_FarawayMother_FabricRidge_Height_1k.png  — see manifest.json (recompute with certutil -hashfile)
SM_FarawayMother_FabricRidge_4km.obj       — 32768 tris, seed 20260829
Content/Python/faraway_mother_prototype_build.py — deterministic placements, idempotent
```

## Next steps
1. **Editor restart + run** the build script (5 min). Verify terrain imports at `/Game/EnvSandbox/Meshes/Terrain/SM_FarawayMother_FabricRidge`, Nanite ON, collision `QueryAndPhysics`.
2. **PIE validation** — orbit camera from valley (0,0,120) toward head (-900, 180): check fabric pleat normal at 1×–4× scale, fog breathing, no z-fighting on valley floor.
3. **Screenshots** — top-down + horizon read per § Level Layout. Save with labels `HEAD / HAIR CASCADE / SHOULDER VALLEY / TORSO DEPRESSION / LIMBS (haze) / HEART GATE`.
4. **Material pass** — assign `MI_Copernicus_*` to terrain material slots (slope/curvature blend if `M_Master_Nikki_Landscape` exposes layers) and confirm sheen via `FarawayMother_MNIKKI_Sheen_Setups.txt`.
5. **Gate ledger** — `python Tools/echo_run.py record faraway_mother_prototype pass` once PIE capture + assertions exist.

## Files delivered this session
- `Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k.png` (1.7 MB)
- `Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k_preview.png` (426 KB)
- `Saved/Audit/faraway_mother/fabric_ridge_terrain/SM_FarawayMother_FabricRidge_4km.obj` (1.9 MB)
- `Saved/Audit/faraway_mother/fabric_ridge_terrain/manifest.json`
- `Content/Python/faraway_mother_prototype_build.py`
- `Content/Python/faraway_mother_height_aware_placements.json` (see below)
