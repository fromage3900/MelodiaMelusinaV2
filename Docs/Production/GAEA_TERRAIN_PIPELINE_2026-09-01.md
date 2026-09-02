# Gaea Terrain Pipeline — 2026-09-01

Status: **Phase 1 COMPLETE** (texture intake verified). Phases 2–4 blocked on decisions D1/D2 (see §7).

## 0. Glacier landscape live in LV_SeaAbove_Prototype (2026-09-02, owner-directed)

- Owner decision: **Glacier** (`kjljbl;bjl;.terrain`, build `003`) is the level terrain, hosted in
  `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype` (the *EnvSandbox* copy — note the
  root `/Game/LV_SeaAbove_Prototype` duplicate still exists; external actors live under
  `__ExternalActors__/<respective map path>/`).
- `CanonicalLandscape` stub (0 components, no data) was deleted (owner-approved) and rebuilt via the new
  `UGaeaToolsLibrary::CreateLandscapeFromGaeaFiles` (see below): **256 components, 5 km × 5 km, scale
  (495.54, 495.54, 244.45), heightmap centered at Z≈0 (spans ±625.7 m)**.
- Verified by raycast: canyon/valley X-axis points match the r16 heightmap **to 0.0–0.7 m**;
  Y-axis matches with **no flip** (FlipYAxis=false correct; earlier "mismatch" was a flip in the
  analysis script, not in the terrain).
- Staging: `Saved/GaeaStaging/Glacier/` — `H_GroundTexture_Out.r16` + `definition.json` as-is; color EXRs →
  8-bit sRGB PNG (round-trip verified, max_err 0.002); mask EXRs → **resized to 1009²** PNGs.
  **Landmine #6: Gaea exports masks at 1024² but the heightmap r16 at 1009²** — the weightmap importer
  asserts `InData.Num() == W*H` and the mismatch **crashed the editor** (LandscapeImportHelper.cpp:364).
- Material `M_Glacier_Landscape_Layered` (D2a adopted): LandscapeLayerBlend Base/Snow/Water/Rock,
  each LandscapeLayerCoords → TextureSample (T_Glacier_SatMap/GroundTexture/Combine/ColorErosion).
  Bound on all 256 components.
- PCG: both volumes seated on terrain and regenerated (86 + 48 instances, counts match docs).
  `PCG_Colonnade` is volume-relative → terrain-aware. **`PCG_ResonanceCathedral`'s graph emits world-space
  Z≈0–15 m regardless of volume location** — it was moved by delta to seat instances at terrain (floor
  −146.5 m). True graph-level projection needs a PCG graph edit (editor UI / C++), not automation.
- Plugin changes (compiled, closed-editor build): `GaeaSubsystem.cpp` empty-`ImportResolutions` guard
  (crash 2026-09-01 ×2 from Create-button click with empty heightmap path), and new
  `GaeaToolsLibrary` (Python-callable importer; `UGaeaSubsystem`/`UImporterPanelSettings` are NOT
  exposed to Python glue).
- Still parked (owner approval required): 75 BC6H auto-imported `/Game/Gaea/Glacier/*.uasset` +
  15 Hills + Mountains copies; cathedral assembly (165 static meshes) still at Z≈130–140 m ≈ 280 m above
  the new terrain; NavMesh rebake owed.


## 1. Forensic root cause of the "black terrain" failure (resolved)

- The 3:57 PM batch's `T_Gaea_SeaAbove_SuperColor` black import was **not bad source data**.
  Pixel-level audit of the fresh export (see §3) shows healthy sRGB-encoded color:
  Mountains `SuperColor_Out.exr` mean 0.404, max 0.796; Hills `SatMap_Out` 0.419,
  `Combine_Out` 0.374, `ColorErosion_Out` 0.329.
- Real cause: the EXR sources are **sRGB-encoded display-referred color stored in float**
  (values quantized to 1/255 steps). The dead editor's auto-import treated them as linear
  HDR data → `BC6H` / `srgb:false` / `SAMPLERTYPE_LinearColor`, which crushes toward black
  in the shading pipeline. All 15 `Content/Gaea/Hills/*.uasset` produced this way are
  misconfigured (same defect, imported by the now-dead PID 39664).
- **Import contract from now on:** color maps must arrive as 8-bit sRGB PNG →
  `TC_Default` / `srgb:true` (DXT1). Data maps (height/masks) stay linear (`srgb:false`).

## 2. Export naming contract (Gaea Build Swarm 2.3.0.1)

| File | Meaning | UE treatment |
|---|---|---|
| `H_*_Out.png` | 16-bit heightmap (landscape intake) | linear, never sRGB |
| `<Node>_Out.exr` RGB (B,G,R FLOAT) | color map | convert → 8-bit PNG, sRGB import |
| `<Node>_Out.exr` Y (FLOAT) | mask / data (weightmap candidate) | linear, srgb:false |
| `definition.json` | `Resolution, ScaleX, ScaleY, Height, Unit` — **drives world scale** | required, never guessed |
| `report.txt` | build log (failed nodes listed) | audit |

`definition.json` (Mountains): Resolution 1009, 5000×5000 m, Height 1183.7 m.
GaeaUnrealTools scale formula (`GaeaSubsystem.cpp:179`): XY = `ScaleX·100/Resolution`
(≈495.5 cm/vertex → 5 km world), Z = `Height·100/512` (≈231.2).
Build location: `C:/Users/froma/OneDrive/Documents/sssssssssssssss.terrain`
(**OneDrive = prime RO re-flagger suspect** — watch log §6 shows 10 clean min so far).

## 3. Verified imports (Phase 1 evidence)

Converter: local float-EXR→8-bit PNG (values ×255, no re-grade; verified pixel-exact
round-trip: EXR px[0,0] (0.557,0.708,0.662) → PNG (169,180,142) ✓).
Imported via Monolith `editor_query import_texture`, saved to disk, verified writable:

| Asset | Source | Mean | Format | sRGB |
|---|---|---|---|---|
| `/Game/Gaea/Textures/T_Gaea_Mountains_SuperColor` | Mountains SuperColor_Out | 0.404 | DXT1 | yes |
| `/Game/Gaea/Textures/T_Gaea_Hills_SatMap` | Hills SatMap_Out | 0.419 | DXT1 | yes |
| `/Game/Gaea/Textures/T_Gaea_Hills_Combine` | Hills Combine_Out | 0.374 | DXT1 | yes |
| `/Game/Gaea/Textures/T_Gaea_Hills_ColorErosion` | Hills ColorErosion_Out | 0.329 | DXT1 | yes |
| `/Game/Gaea/Textures/W_Gaea_Mountains_Mask1` | Mixer_MaskOut1 | 0.865 | DXT1 | no |
| `/Game/Gaea/Textures/W_Gaea_Mountains_Mask2` | Mixer_MaskOut2 | 0.606 | DXT1 | no |
| `/Game/Gaea/Textures/W_Gaea_Mountains_Mask3` | Mixer_MaskOut3 | 0.290 | DXT1 | no |

In-editor channel stats confirm non-black (e.g. SuperColor R mean 102.97/255) and match
the PNG round-trip exactly. Weightmap masks span full 0–1.

## 4. Known landmines (do not repeat)

1. **Do not import Gaea color EXRs directly.** Linear/HDR defaults produce black terrain.
   Convert to 8-bit sRGB PNG first (script: `Saved/Recovery/gaea_pipeline_pre_2026-09-01/`
   + `Tools/` candidates §6) or re-export PNG from Gaea.
2. **`Content/Gaea/Hills/*.uasset` (15) and auto-imported `Content/Gaea/Mountains/*`**
   in the running editor are misconfigured BC6H copies. They are left unsaved/dirty
   deliberately; do NOT `Save All`. Cleanup requires owner approval (destructive-delete
   red line).
3. **Monolith save bug:** `save_packages` on a read-only target escalates to fatal editor
   crash (MonolithHttpServer.cpp:265 path). Pre-check writability before every save; verify
   disk timestamp + size after.
4. **GaeaUnrealTools material contract:** importer auto-discovers weightmap layer names via
   `UMaterialExpressionLandscapeLayerBlend` nodes in the assigned material
   (`ImporterPanelSettings.cpp:32`). The canonical master
   `M_Master_Toon_Landscape_HeightBlend` has no such nodes → Decision D2.
5. One editor only; port 9316 single listener verified (PID 46428 healthy at session start).

## 5. Scale facts (for Phase 3/4)

- Mountains: 5 km × 5 km, Z height 1183.7 m → Z-scale ≈ 231.2 (via plugin formula).
- Edit scale **only** via `definition.json` + reimport, never by freehand actor scale —
  mismatched component/resolution is the classic spike source.
- Landscape intake path: `UGaeaLandscapeComponent` (heightmap PNG + definition JSON +
  weightmap PNGs), `UGaeaSubsystem::CreateLandscapeActor` (Ctrl+Alt+P window).

## 6. Phase 0 evidence

- Hung editor PID 39664 already gone; PID 46428 alive + healthy (Monolith 0.20.3 on 9316).
- RO flag watch: 20 scans / 10 min over `Content/Gaea` (104 files), **zero flags** —
  `Saved/Recovery/gaea_pipeline_pre_2026-09-01/ro_flag_watch.log`.
- Manifests backed up to `Saved/Recovery/gaea_pipeline_pre_2026-09-01/`.
- EXR audit scripts (re-runnable): temp `opencode/gaeadata` — promote to `Tools/` in Phase 5.

## 7. Open decisions (blocking Phases 2–4)

- **D1 (target map):** which level hosts `CanonicalLandscape`? `LV_SeaAbove_Prototype`
  has 8 dirty external actors from the earlier session — touching that map means saving
  them or asking first. Alternative: fresh map under `Content/Gaea/`.
- **D2 (material seam):** (a) add a `LandscapeLayerBlend`-enabled child MI so the
  plugin's auto-layer discovery binds the Mixer masks natively [recommended], or
  (b) tint/param-driven Plan B without layer blend nodes.
- **D3 (Hills vs Mountains):** Mountains has the full contract (definition.json +
  heightmap PNG + 3 Mixer masks). Hills has textures only (no definition.json/heightmap
  PNG) — usable as MI albedo sources only.

## 8. Canonical recipe

The full working loop (source contract, conversion, editor lane, verification standard, landmine register)
is now canonical at [GAEA_LANDSCAPE_IMPORT_RECIPE_2026-09-02.md](GAEA_LANDSCAPE_IMPORT_RECIPE_2026-09-02.md).
