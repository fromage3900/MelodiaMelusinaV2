# Contact Sheet Audit — 2026-09-02

Regenerated against **CURRENT (post-cook)** texture outputs of the Melodia hero cymatic
flipbook sweep. Source script: `Tools/generate_contact_sheets.py` (extended; existing
sections preserved, new sections appended, tolerant of empty/missing dirs).

All sheets written to `Saved/Audit/contact_sheets/`. Every sheet verified to exist and
be non-zero.

---

## 1. Hero Cymatic Flipbook Sweep — 9 variant sheets (648 tiles total)

Source dir: `Saved/Audit/copernicus_cymatic/<variant>/`, files
`T_Cymatic_<variant>_<map>.<frame>.png` @ 1024x1024.
Layout per sheet: 8 frames (rows) x 9 maps (cols) = **72 tiles**, thumb 128.
Maps: BaseColor, Normal, Roughness, Metallic, Height, ORM, Emissive, Iridescence, Opacity.
Manifest: `Saved/Audit/copernicus_cymatic/qa_melodia_flipbooks_2026-09-02.json` (9 variants, 8 frames).

| Sheet | Tiles | Bytes |
|---|---|---|
| contact_sheet_Flipbooks_MelodiaHeroGem.png | 72 | 2,054,313 |
| contact_sheet_Flipbooks_MelodiaGoldSilk.png | 72 | 1,743,806 |
| contact_sheet_Flipbooks_MelodiaMotherPearl.png | 72 | 1,123,815 |
| contact_sheet_Flipbooks_MelodiaSapphireGlass.png | 72 | 995,330 |
| contact_sheet_Flipbooks_MelodiaRoseVelvet.png | 72 | 1,273,245 |
| contact_sheet_Flipbooks_MelodiaMoonlace.png | 72 | 1,615,268 |
| contact_sheet_Flipbooks_MelodiaForestEmerald.png | 72 | 1,588,388 |
| contact_sheet_Flipbooks_MelodiaAmethystVein.png | 72 | 2,256,677 |
| contact_sheet_Flipbooks_MelodiaAuroraGlass.png | 72 | 1,033,969 |
| **Total** | **648** | |

## 2. Eigenplate — 2 tiles

Source dir: `Saved/Audit/eigenplate/` (2 maps). Thumb 160.

| Sheet | Tiles | Bytes |
|---|---|---|
| contact_sheet_Eigenplate.png | 2 (Height, Normal) | 29,600 |

## 3. Klein Veil — 9 tiles

Source dir: `Saved/Audit/klein_veil/` (9 maps). Thumb 160.

| Sheet | Tiles | Bytes |
|---|---|---|
| contact_sheet_KleinVeil.png | 9 | 194,987 |

## 4. VDM Fabric — 4 tiles

Source dir: `Saved/Audit/vdm_fabric/` (only the 4 baked `T_FarawayMother_Fabric_VDM_A/B/C/KleinVeil.png`
images included; .exr/.npy/_template.py and .json files excluded). Thumb 160.

| Sheet | Tiles | Bytes |
|---|---|---|
| contact_sheet_VDM_Fabric.png | 4 | 119,037 |

## 5. LOD Textures — 179 tiles (REBUILT, still current)

Source: `specs/lookdev/optical_lod_manifest.v1.json` (11 assets x 4 LODs x 4 maps = **176**)
+ `Saved/Audit/lookdev/optical_lods/shared/` (3: BayerDither 8x8, BlueNoise 64x64,
Iridescence ThinFilm LUT) = **179 tiles**. Per-asset LOD dirs held 0 PNGs on disk (textures
referenced via manifest); shared glob grabbed the 3 present. Rebuilt 2026-09-02 and count
unchanged from prior run.

| Sheet | Tiles | Bytes |
|---|---|---|
| contact_sheet_LOD_textures_179.png | 179 | 2,229,241 |
| contact_sheet_LOD_textures_179.html | (interactive) | 58,205 |

## 6. Existing / unchanged sections (regenerated, inputs present)

| Sheet | Source | Bytes |
|---|---|---|
| contact_sheet_Copernicus_MIs_39.png | Content/EnvSandbox/Materials/Instances/Copernicus | 77,600 |
| contact_sheet_Copernicus_ALL_90.png | Content/EnvSandbox/Materials/Instances/Copernicus | 79,385 |
| contact_sheet_Brass_8x9_72.png | Content/EnvSandbox/Textures/Copernicus/Brass* | 483,950 |
| contact_sheet_FarawayMother_placements.png | Content/Python/faraway_mother_height_aware_placements.json | 57,278 |

---

## Source-dir survey (all target dirs)

| Dir | Exists | PNG count |
|---|---|---|
| Saved/Audit/copernicus_cymatic | yes | 9 hero variants x 99 (72 frames + 27 single-frame leftover maps) + 50 variant dirs total |
| Saved/Audit/eigenplate | yes | 2 |
| Saved/Audit/klein_veil | yes | 9 |
| Saved/Audit/vdm_fabric | yes | 4 (baked VDM PNGs) |
| Saved/Audit/lookdev/optical_lods/shared | yes | 3 |

No target dir was empty or missing — all were non-empty and covered. Generator skips and
notes any empty/missing dir gracefully if the sweep re-runs after cleanup.

Summary: **18 PNG sheets** written/regenerated (7 pre-existing standalone + 9 flipbook +
Eigenplate + KleinVeil + VDM + LOD rebuild), covering **648 flipbook + 2 + 9 + 4 + 179 = 842 tiles**
from current texture outputs.