# Melusina AAA Polish Recipe — v22 session (2026-08-13)

Target: the open Blender 5.2 session (v22, final rig, SIR_VISIBLE lineage). The
headless-load attempts on the 1.7 GB portfolio stage blends hang the importer,
so this recipe is applied in-session (GUI or Blender MCP when reachable). All
inputs are August-2026 files only.

## 1. Material pass (per part)

| Part | Setting | Values |
|---|---|---|
| **Skin** | Principled BSDF: Subsurface | Subsurface 0.06, Radius (0.5, 0.8, 1.2), base from `G:\MelodiaMelusina\ACTUALCOMPILEDMELUSINATEXTURES` staging (or `Imports\MelusinaTextures` maps) |
| **Hair** | Principled: Sheen + Clearcoat | Sheen 0.7, SheenTint warm, Clearcoat 0.4, Roughness 0.25 — matches UE `ToonRamp_Hair` look |
| **Outfit** | Fabric (gingham/linen) | `Downloads\fabric-gingham-pbr-198-1024.zip`, `fabric-linen-slub-pbr-51-1024.zip`, `fabric-plush-cut-pile-pbr-73-1024.zip` (Poliigon PBR) |
| **Coat/Collar/Ruffles/Tie** | unused sirmelo sets | `G:\sirmelo\coat_*`, `collar_*`, `ruffles_*`, `tie_*` (7 maps each) |
| **Metals/accessories** | Gold + plum accent | Gold base #C9A86A, Roughness 0.35, Metallic 1.0; plum accents #2E2438 |
| **Eyes** | Cornea/iris | Existing cornea setup + `sirmelo_*` eye maps; add clearcoat on cornea |

## 2. Lighting rig (AAA studio)
- **Key**: warm gold light (#F0E6D2), 45° L, intensity tuned for the toon ramp
- **Fill**: cool violet (#463A54) at 30% key — the ShadowDreamTint palette family
- **Rim**: gold (#C9A86A), back 45°, thin
- **HDRI**: Poly Haven (staged `Imports\Environment\PolyHaven`) — soft studio dome, low strength
- Optional dream accent: pink point light (#FFD9EB) behind/below for the DreamTint vibe

## 3. Camera / composition
- Hero: 3/4 bust, 85mm, eye line at upper third
- Close-ups: face (hair sheen), hands/outfit fabric, accessories (gold/plum)
- "Photo spot" framing per the RoomDressing docs (silhouette + one light story + one sparkle accent)

## 4. Render
- Cycles, 3840×2160, 512 samples, OptiX denoise, filmic view transform
- Output: `Saved/Portfolio/Melusina/` (feeds the `generated/` passport/plate pipeline via `Imports\Portfolio\lookdev` scripts)

## 5. Notes
- v16/v17/v18 SIR_VISIBLE blends hang headless Blender (1.7 GB scene files) — apply in-session only
- AvatarGarden (140 ASCII FBX) conversion deferred: ASCII FBX hangs Blender's FBX importer (per-file triage or Assimp conversion needed)
- UE side is DONE: 1,542 MIs on the toon spine with ShadowDreamTint/DreamTint, 1,759+ meshes on pack MIs

## Violin rig (v22)

- The violin rig source is the `SM_Violin_BSS1`–`SM_Violin_BSS21` blend chain inside the InstrumentScans zip (`Products/_Staging/AssetSourceMap_20260712/Melodia_Violin_InstrumentScans.zip`); BSS21 is the newest rig iteration
- The rig lives in Blender for v22 renders
- Its real PBR maps are the `Violin/BezierDetails_*` + `Violin/Foot_*` 7-map sets (14 textures total, 4K) located in the same zip at `Violin/` — pending UE import
