# Accessory Atelier

Internal WebGL product study. Not part of the recruiter site.

| Surface | Job |
|---|---|
| `floral-study.html` | Editorial house page — Chevalier palette, custom Three.js viewer |
| `index.html` | Cleaner product-viewer framing of the same Three.js runtime |
| `model-viewer.html` | Shared commerce embed — Google or Babylon, one camera contract |
| `../models/eyewear/*.glb` | DCC silhouettes with `KHR_materials_variants` (Tortoise / Champagne) |
| `../dcc/author_eyewear_variants.py` | Bakes vertex-color finishes into variant materials |
| `catalog.js` / `viewer-contract.js` | Shared silhouette list and camera |

The atelier owns art direction (lighting, runtime finish/lens swaps, editorial camera).
The embed proves the DCC GLB ships in a standard viewer. Engine is a toggle, not a second layout.

Capture: `model-viewer.html?capture=1&hero=aviator&variant=Tortoise&engine=google`
