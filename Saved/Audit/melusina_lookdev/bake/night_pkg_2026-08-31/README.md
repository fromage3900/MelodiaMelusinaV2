# Shorewake Dress — Night Bake Package (2026-08-31)

48-material restoration + bake maps + pearl-woven fabric kit for hand-paint in Substance
tonight, then UE import tomorrow. All QA checks pass (`night_pkg_manifest.json` → `all_pass: true`).

## What happened to the 48 materials (root cause)

`shorewake_bake_prep.py:91` exported the bake OBJ with `export_materials=False` (zero
`usemtl` groups), **and** the consolidated bake-source blend had degenerate face
assignments — all 206,780 polys referenced slot `SW_Dress_P01`. The dress was doubly
merged. The 48-slot state was intact in `Shorewake_48MAT_frozen_snapshot.blend`
(48/48 slots, 0 empty, 186,955 polys) — that is the source of everything here.

## Files

| File | What it is |
|---|---|
| `SM_ShorewakeDress_48MAT_v2_slotted.fbx` / `.obj` + `.mtl` | **The slotted bake mesh** — 48 material slots `SW_Dress_P01..P48`, merged geometry, same UV layout as all prior bakes |
| `T_DressShorewake_PanelID_4K.png` + `_legend.png` | 48 flat panel colors, luminance-ordered P01→P48. The masking map for the merged-paint workflow |
| `bake_of_record` (unchanged, in `bake/sbs/`) | sbsbaker 4K: `…_low_ambient-occlusion / normal-from-mesh / curvature / thickness-from-mesh / position` — still valid, bakes are UV-projected and UVs didn't change (verified: shared panel bbox drift ≤0.4% U / 3.7% V, caused by the consolidated re-mesh's added polys extending the bbox, not a layout change) |
| `T_Shorewake_PearlWeave_{Height,Normal,AO,Roughness}` | Tiling 2K pearl satin weave (64px thread pitch, pearl dimples) |
| `T_Shorewake_ChladniWeave_N` | Weave normal with the **n=5,m=7 Chladni standing-wave motif** ("sung fabric" — from the audio-reactive fabric-mountain fold table; texture-only, reads no audio) |
| `T_Shorewake_PearlSheen_{Iridescence,Strength}` | Spectral-hue per-plate iridescence (dress_shine_kit hex lattice + nikki aurora cells) + sheen weight mask (NikkiPearlSheen 0.4 / PastelStrength 0.65) |
| `T_Shorewake_Painterly_{BaseColor,Height}` | Tiling 2K painterly base — seafoam→teal brush strokes, gesso/impasto height, Chladni-guided stroke flow |
| `T_DressShorewake_Painterly_Drape_4K` | Painterly base projected through the slotted mesh UVs (dress-space, panel-aligned) |
| `T_DressShorewake_FoamCrest_Mask_4K` | Foam-crest / edge-wear mask driven by the dress curvature bake (garment-following) |
| `NIGHT_PKG_contact_sheet.png` | Visual index of the whole kit |
| `*_manifest.json` | Seed-locked manifests (`20260831`) + sha256 for every file |

## Substance tonight — two workflows (both supported)

**A. Merged paint (fast, recommended for tonight):** import the slotted FBX, use the
sbsbaker maps as the base set, add `PanelID` as a mask source. Per-panel control =
fill layer → black mask → ID color extraction (pick the panel's legend swatch).
You get 48-panel granularity on ONE texture set.

**B. Per-panel texture sets:** Substance will create 48 texture sets from the FBX slots
(`SW_Dress_P01..P48`). Heavier, but each panel is independently paintable. The 48 UE
material instances already exist at
`/Game/Melodia/Characters/Melusina/Textures/Clothes/SW_Dress_P01..P48.uasset`.

## Conventions

- Bake resolution 4K, margin 16px, UV space 0–1 (no island overlaps).
- Normal maps: **DirectX Y+** (pre-flipped for UE) for the sbsbaker set; the tiling
  weave/painterly normals are **OpenGL Y+** — flip G on import if mixing.
- Masks (ID, sheen strength, foam crest): linear, sRGB **off**.
- BaseColor / iridescence / legend: sRGB.
- Determinism: seed `20260831` everywhere; changing it requires regenerating manifests.

## Audio contract (red line respected)

Every texture is **texture-only**. No code reads audio; the single audio writer
(`MelodiaAudioReactivePresentationSubsystem` → `MPC_Melodia_Palette`) is untouched.
The Chladni motif and beat-phase-ready design mean the emission/sheen lanes can later
be driven by the existing cymatics/MPC consumers if wanted — with zero new writers.

## Scripts (all committed, rerunnable)

- `Tools/Houdini/sea_above_reef/shorewake_blend_inventory.py`
- `Tools/Houdini/sea_above_reef/shorewake_bake_slotted_export.py` (Blender 5.2.1)
- `Tools/Houdini/sea_above_reef/shorewake_panel_id_map.py`
- `Tools/Houdini/sea_above_reef/shorewake_pearl_weave_kit.py`
- `Tools/Houdini/sea_above_reef/shorewake_night_pkg_qa.py`
