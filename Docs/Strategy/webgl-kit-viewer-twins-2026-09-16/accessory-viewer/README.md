# Accessory Atelier

Internal WebGL product study. Not part of the recruiter site.

| Surface | Job |
|---|---|
| `floral-study.html` | Editorial house page — Chevalier palette, custom Three.js viewer |
| `index.html` | Cleaner product-viewer framing of the same Three.js runtime |
| `model-viewer.html` | Google `<model-viewer>` commerce/AR embed of the **same GLBs** |
| `babylon-viewer.html` | Babylon.js Viewer engine-check of the **same GLBs** |
| `catalog.js` | Shared silhouette list so the viewers cannot drift |

## Integration rule

The atelier owns art direction (lighting, finish/lens swaps, editorial camera).
`model-viewer` proves the asset also ships as a standard commerce embed.
Babylon is a second-engine check, not a second lighting language.

Do not bake `KHR_materials_variants` until a DCC pass authors them. Silhouette/finish pairs are currently **separate GLBs**.

Capture: `model-viewer.html?capture=1&hero=aviator-tortoise` (same query on `babylon-viewer.html`) freezes auto-rotate. The GLB sits temple-down in Y-up. Google’s embed uses `orientation="0deg 90deg 0deg"`. Babylon’s glTF loader writes a quaternion on `__root__`; the check clears it and applies `-PI/2` X, then reframes.
