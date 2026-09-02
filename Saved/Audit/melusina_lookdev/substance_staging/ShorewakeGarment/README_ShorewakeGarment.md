# ShorewakeGarment — merge 48 panels → 10 labeled garment materials (2026-09-02)

The Shorewake dress arrived as **48 arbitrary USDZ panels** (`SW_Dress_P01..P48`)
holding no semantic meaning. This staging kit re-labels them by **silhouette
geometry** into **10 garment layers / merged materials**, then wires the
refreshed, per-layer fabric maps into a Substance project.

## The 48 → 10 merge

The 48 panels were clustered purely from their assembled vertex clouds relative
to the global dress axis (x≈0.0, y≈0.155, z −0.16..1.50 m = ~1.66 m dress) by:

- **radial spread** from the dress axis (cylindrical r)
- **z-elevation band** (top/bottom/span)
- **width×depth**, **azimuth**, **wrap-across-the-±180°-seam**, and size

The full per-panel feature dump + rationale is in
[`garment_layers_manifest.json`](../../night_pkg_2026-08-31/garment_layers_manifest.json).
Visual proof of the merge (front / three-quarter / back, each panel flat-colored
by its garment group) is in
`Saved/Audit/melusina_lookdev/silhouette_out/GARMENT_MERGE_*.png`.

| Garment material | Panels merged | Reads-as |
|---|---|---|
| `M_Bodice_Torso` | P47 (46k v) | widest bust/torso shell |
| `M_Bodice_Front` | P30,31,33,34,35,36–44 (14) | front chest/yoke panels |
| `M_Bodice_Side` | P29, P45 | side torso panels |
| `M_Bodice_Upper` | P02, P46 | upper bodice band |
| `M_Collar` | P32 | wrapping collar/neckline band |
| `M_Shoulder_Trim` | P03–P10, P13, P14 (10) | shoulder/armhole cap trim |
| `M_Shoulder_Ornament` | P15–P28 (14) | tiny cap cluster — studs/beads |
| `M_Sleeve` | P11, P12 | sleeve/arm panel |
| `M_Underskirt` | P01 | mid skirt/slip |
| `M_Skirt_Full` | P48 (69k v) | full-length outer skirt |

## Refreshed fabric maps (per garment layer) — `../garment_refresh/`

`shorewake_garment_refresh.py` (seed `20260902`) produces an **8-map set per
garment layer** (80 maps total, 2048 tiling) instead of one shared set:

- charmeuse satin on the bodice + skirt families (long float, high sheen)
- **pearl floral lace** on the collar (masked opacity)
- **eyelet trim** on shoulder trims, **bead-dot grid** on shoulder ornaments
- painterly pearl albedo + crest-weighted iridescence + sheen strength
- height-derived normal (OpenGL Y+), cavity AO, roughness w/ wash crawl

Layers with Metal maps (bodice/collar/trim/ornament) carry a metallic hint on
lace crests. `M_Collar`/`M_Shoulder_*` also ship an opacity/coverage variant
for masked alpha materials.

`../garment_refresh/animated/` — `shorewake_animated_flipbook.py` (same seed)
bakes a **seamless 8-frame animated flipbook** (BaseColor/Normal/Iridescence/
Sheen/Roughness/Height per frame, 48 maps) plus morph-aware normals
(`T_Shorewake_Morph_{Bloom,Swirl}_Normal.png`) to drive the dress's authored
morph targets (Bloom/Swirl/ShimmerWave) texture-side.

## The Substance project

- **Merged mesh:** `meshes/SM_ShorewakeDress_48MAT_garment.obj` (+`.mtl`) —
  48 blocks renumbered to the 10 garment materials (rename-only; UV space
  unchanged).
- **Painter builder:** deploy `shorewake_garment_painter.py` (master in
  `Tools/Houdini/sea_above_reef/`) to
  `C:/Program Files/Adobe/Adobe Substance 3D Painter/resources/python/startup/`
  then launch Painter. It opens `ShorewakeGarment.spp` with **10 texture sets**
  and wires each layer's refreshed maps onto BaseColor / Normal / Height /
  Roughness / Metal, importing the rest (iridescence, sheen, PanelID, bake
  maps) as hand-paint resources.
- Normal convention: **OpenGL Y+** (matches the refreshed kit).
- The 48→10 mapping is recorded in `garment_merge_obj_manifest.json`.

On export for UE, flip normal G (OpenGL→DirectX) or set export to DirectX.

## Audit / evidence (echo contract)

- `garment_layers_manifest.json` — feature dump + per-panel rationale (seed 20260902)
- `silhouette_out/GARMENT_MERGE_{FRONT,THREE_QUARTER,BACK}.png` — color merge proof
- `garment_refresh/garment_refresh_manifest.json` — 80 refresh maps + sha256 (seed 20260902)
- `garment_refresh/animated/animated_manifest.json` — 50 animated maps + sha256
- scripts all committed, deterministic, headless (venv python / Blender 5.2 / hython)

Each manifest is written by `reef_common.write_manifest` with a recorded seed +
sha256 for every file. No `.uasset` hand-edits; texture/MI work goes through
Interchange or `unreal` Python.