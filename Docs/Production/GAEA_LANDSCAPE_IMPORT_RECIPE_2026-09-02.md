# Gaea Landscape Import Recipe — CANONICAL — 2026-09-02

Status: **PROVEN** (Glacier → LV_SeaAbove_Prototype, raycast-verified 2026-09-02). This is the
authority for Gaea → UE Landscape import. Do not re-derive; extend the tools if gaps appear.

Authority chain: `GAEA_TERRAIN_PIPELINE_2026-09-01.md` (forensics + Phase-1 texture intake)
→ this recipe (the full working loop). Related: `GAEA_TERRAIN_PIPELINE_2026-09-01.md` §0 (session log).

---

## 1. Source contract (Gaea Build Swarm 2.3.0.1)

| File | Meaning | Handling |
|---|---|---|
| `H_<Node>_Out.r16` | 16-bit raw heightmap at **build resolution** (e.g. 1009² — may be prime) | copy as-is; the plugin reads r16 natively |
| `<Node>_Out.exr` RGB (FIT_RGBF) | sRGB-encoded display-referred color in float | convert → 8-bit sRGB PNG (`×255 + 0.5`, no re-grade) |
| `<Node>.exr` / `<Node>_Out.exr` Y (FIT_FLOAT / RGBAF) | data/mask | convert → 8-bit grayscale PNG, **resized to heightmap resolution** |
| `definition.json` | `Resolution, ScaleX, ScaleY, Height, Unit` — **drives world scale** | copy as-is; never guess |
| `report.txt/json` | build log | audit only |

**Scale formula** (GaeaSubsystem.cpp:179): `XY = ScaleX·100/Resolution`, `Z = Height·100/512`.
Glacier: 5000 m, H=1251.6, Res=1009 → scale (495.5401, 495.5401, 244.4531). Heightmap is
centered vertically: world Z = `(h/65535 − 0.5) · Height` (spans ±H/2).

**Y orientation:** `FlipYAxis=false` is correct — world +Y maps directly to heightmap +row
(empirically verified to 0.3 m: terrain at (0,±2000 m) matched unflipped predictions).

## 2. Conversion lane — `Tools/gaea_glacier_convert.py`

- Reads EXR via **UE 5.8's bundled FreeImage.dll** (ctypes; imageio-freeimage has no py3.14 wheel):
  `FIF_EXR=29` (verified via `GetFormatFromFIF`), types `FIT_FLOAT=6 / FIT_RGBF=11 / FIT_RGBAF=12`,
  scanlines are **BGR(A), bottom-up** (reverse row + swap channels).
- Color → `T_<Terrain>_<Node>.png` (RGB, verified round-trip max_err 0.002).
- Masks → `W_<Terrain>_<Layer>.png` (L, **resized 1024→1009 LANCZOS** — see landmine #2).
- Staging: `Saved/GaeaStaging/<Terrain>/` — **outside `Content/`** so editor auto-import cannot
  re-ingest EXRs as BC6H (landmine #3). Also emits `contract.json` (layers, weightmap order, scale).
- Modes: `analyze` (height stats, basin finder, per-point heights) / `convert` / `verify`.

## 3. Editor lane

1. **Textures**: Monolith `material_query import_texture` — color: DXT1, `srgb=true`,
   `lod_group=TEXTUREGROUP_World` → `/Game/Gaea/<Terrain>/Textures/`. Masks are NOT imported as
   textures (weightmap files feed the landscape importer directly).
2. **Material**: a material carrying `UMaterialExpressionLandscapeLayerBlend` nodes whose layer
   names match the importer's `LayerNames` (count N), with N−1 weightmaps. Glacier:
   `M_Glacier_Landscape_Layered` layers `Base/Snow/Water/Rock`.
3. **Landscape**: `UGaeaToolsLibrary::CreateLandscapeFromGaeaFiles(HeightmapFile, DefinitionFile,
   WeightmapFiles[full paths], LayerNames, LayerInfoFolderPath, LandscapeMaterial, Location,
   bFlipYAxis=false, bWorldPartition=false)` — callable from Python (`unreal.GaeaToolsLibrary.*`).
   Internally: spawns `ALandscape`, imports height+weightmaps (ExpandCentered), mints
   `ULandscapeLayerInfoObject`s in LayerInfoFolderPath, attaches `UGaeaLandscapeComponent`
   (stores paths for reimport), assigns material. Glacier result: **256 components, ±2497.5 m,
   ±625.7 m Z**.

## 4. Verification standard

1. Raycast vs offline r16 prediction at ≥2 flip-agnostic points (y=0), tolerance **< 1 m**
   (`mesh_query query_raycast`).
2. Layer/material: every `LandscapeComponent.get_material(0)` is the assigned material.
3. Persistence: `save_dirty_packages` then **on-disk proof** — new `__ExternalActors__/<map>/**`
   uasset (size ≈ MBs for terrain), stub package gone. Monolith save returns lie; mtime is truth.
4. Round-trip: converter `verify` (max_err < 0.005).

## 5. Landmine register (all encountered)

1. **Empty `ImportResolutions`** — clicking Create with an invalid heightmap path asserts
   (`GaeaSubsystem.cpp:813` family). Fixed by guard in both `GaeaSubsystem.cpp` and
   `GaeaToolsLibrary.cpp` (2026-09-02, closed-editor build). Crashed the editor ×2 on 09-01.
2. **Weightmap size ≠ heightmap size** — Gaea exports masks at 1024² but the r16 at 1009²;
   `LandscapeImportHelper.cpp:364` asserts `InData.Num() == W*H` → **fatal**. Converter resizes.
3. **Direct EXR import** → linear/HDR defaults → BC6H `srgb:false` → black terrain
   (15 Hills + 46 Mountains + 75 Glacier auto-imported copies; cleanup parked, owner approval).
4. **Staging in `Content/`** — editor auto-import fires within minutes (22:53 drop → 22:58 BC6H
   ingestion). Always stage in `Saved/`.
5. **`save_packages` on read-only target** → fatal editor crash (MonolithHttpServer.cpp:265 path);
   pre-check writability, verify mtime after.
6. **Duplicate map packages** — `/Game/LV_SeaAbove_Prototype` (root) vs
   `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype` (live; external actors
   confirm). Reconciliation parked (owner).
7. **Monolith HTTP wedge** — after modal loops the listener stops accepting while the game thread
   lives; only recovery is editor restart. Editor restart loses in-memory deletions → re-verify
   external-actor packages after any restart.
8. **Two editors** — a wedged instance can survive `Stop-Process`; verify `Get-Process UnrealEditor`
   count == 1 AND a fresh 9316 LISTENING PID before continuing.

## 6. Automation API added (GaeaUnrealTools, built 2026-09-02)

- `UGaeaToolsLibrary::CreateLandscapeFromGaeaFiles(...)` — see §3.
- `UGaeaToolsLibrary::GetGaeaLandscapeScale(ScaleX, ScaleY, Height, Resolution)`.
- `UGaeaToolsLibrary::GetGaeaLandscapeLocationZ(Height)`.
- `UGaeaSubsystem::CreateLandscapeActor` — guarded against empty descriptor.
- Note: `UGaeaSubsystem` / `UImporterPanelSettings` are NOT exposed to Python glue; use the library.
