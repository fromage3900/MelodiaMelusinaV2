# Accessory Atelier

Internal WebGL product study. Not part of the recruiter site.

| Surface | Job |
|---|---|
| `floral-study.html` | Editorial house page — Chevalier palette, custom Three.js viewer |
| `index.html` | Cleaner product-viewer framing of the same Three.js runtime |
| `model-viewer.html` | Shared commerce embed — Google or Babylon, **one camera contract** |
| `catalog.js` | Shared silhouette list |
| `viewer-contract.js` | Shared facing + orbit + target + FOV |

## Integration rule

The atelier owns art direction (lighting, finish/lens swaps, editorial camera).
The embed proves the asset ships in a standard viewer. Engine is a toggle, not a second layout.

`viewer-contract.js` is the only camera authority for the embed. Do not re-frame per engine.

Do not bake `KHR_materials_variants` until a DCC pass authors them. Silhouette/finish pairs are currently **separate GLBs**.

Capture: `model-viewer.html?capture=1&hero=aviator-tortoise&engine=google` (or `engine=babylon`).
