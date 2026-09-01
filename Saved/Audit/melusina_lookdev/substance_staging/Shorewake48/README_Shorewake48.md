# Shorewake48 — Substance Painter staging (2026-09-01)

Automated `.spp` for the **original Shorewake dress** (48 material slots),
built by the same startup-module pipeline as FlowerSpring — see
`Docs/Production/FLOWERSPRING_SUBSTANCE_PIPELINE_2026-09-01.md` for the
pipeline + API gotchas (this build reused every fix and succeeded first run).

## What was built

`spp/Shorewake48.spp` — one project, **48 texture sets** (`SW_Dress_P01..P48`)
created from `bake/night_pkg_2026-08-31/SM_ShorewakeDress_48MAT_v2_slotted.fbx`
(186,955 polys, 1 UV layer, 48 slots, DirectX-normal convention).

Every set carries the same starter fill (shared dress-space UV layout):

| Channel | Map | Source |
|---|---|---|
| BaseColor | `T_DressShorewake_Painterly_Drape_4K.png` | night_pkg (projected through these exact UVs) |
| Normal | `SM_..._low_normal-from-mesh.png` (4K) | `bake/sbs/` bake-of-record, DirectX Y+ (UE-ready) |
| Height | `T_Shorewake_Painterly_Height.png` | night_pkg |
| Roughness | `T_Shorewake_PearlWeave_Roughness.png` | night_pkg |

Also imported as project resources (hand-paint masking, not channel-wired):
PanelID 4K (+legend), FoamCrest mask 4K, ChladniWeave_N, PearlSheen
Iridescence/Strength, PearlWeave Normal/Height/AO, bake AO / Curvature /
Thickness / Position / Normal.

Evidence: `painter_build_done.json` (`melodia.shorewake48_painter_build.v1`,
`all_saved=true`, 48/48 sets with 4/4 channels wired) + `painter_build_steps.log`.

## Per-panel control (workflow B from the night-pkg README)

Each panel is its own texture set — paint directly, or use the PanelID map
with the legend for ID-mask workflows. The 48 UE material instances already
exist at `/Game/Melodia/Characters/Melusina/Textures/Clothes/SW_Dress_P01..P48`.

## Notes

- Project normal format is **DirectX** (matches the sbsbaker set). The tiling
  weave/painterly normals in the kit are OpenGL Y+ — flip G when mixing.
- File is ~905 MB (4K bakes embedded). Export preset root: `export/Shorewake48/`.
- Rerun builder if needed: master at
  `Tools/Houdini/sea_above_reef/shorewake_painter_startup.py`; deploy as
  `.../Painter/python/startup/shorewake_build_plugin.py` (see pipeline doc §5).
