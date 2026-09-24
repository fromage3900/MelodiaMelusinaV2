# BUILD RECEIPT — MelusinaSmartMaterial

**When:** '"$STAMP"' (America/Toronto)  
**Out root:** `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\MelusinaSmartMaterial`

## Created

| Path | Purpose |
|---|---|
| `STUDY_SimpleDiffuse.md` | On-disk SD SBSAR + VNP SPSM study + Melusina mapping |
| `MELUSINA_SMART_MATERIAL_SPEC.md` | Proprietary Melusina layer stack + params |
| `BUILD_RECEIPT.md` | This file |
| `build_recipe\PAINTER_CLICKPATH.md` | <15 min Create Smart Material steps |
| `PHASE1_HITS.txt` / `.json` | Search hit list |
| `resources\cymatic\` | Hardlinks to FrozenFracture maps |
| `resources\references\` | vertex_paint.py, paint_guide, SimpleDiffuse_V2.sbsar |
| `study_extract\` | Strings / copies of SD + VNP |
| `exports\Melodia_Melusina_Handpaint_REF.spsm` | **Reference only** — copy of Very Normal Paint SM |
| `exports\README.md` | Clarifies REF ≠ Melusina |

## Source assets studied

- `C:\Users\froma\OneDrive\Documents\Adobe\Adobe Substance 3D Painter\assets\materials\SimpleDiffuse_V2.sbsar`
- `...\assets\smart-materials\Very Normal Paint SM.spsm` (+ `_1`)
- HandpaintPrep `vertex_paint.py`, `02_ZenLantern\substance\paint_guide.md`
- `Bakes_Cymatic\FrozenFracture\T_Cymatic_FrozenFracture_*.png`

## What user must click

Open ZenLantern in Painter → follow `build_recipe\PAINTER_CLICKPATH.md` → **Create smart material** on folder `SMS_Melusina_Handpaint` → save real `.spsm` into `exports\`.

## Blockers / honesty

- SimpleDiffuse is a **compressed SBSAR** — no layer XML extracted; param surface from product docs + alg_meta identity.
- Very Normal Paint `.spsm` is **HDF5** — folder titles recovered from strings; no full rewrite of binary into Melusina IP.
- **No fake Melusina `.spsm` bytes authored.** Click-path is the real deliverable; REF spsm is VNP for comparison only.
- Software present: Substance 3D Painter + Designer under `C:\Program Files\Adobe\`.

## Naming

Smart material: **`SMS_Melusina_Handpaint`** only (Melodia / Melusina / Companions conventions).
