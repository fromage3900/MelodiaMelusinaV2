# Resonant Wilds — NPR Shader Lab V2 (stacked draft)

This is a **Three.js r170, vanilla ES-modules** experiment, not a renderer/framework migration.

## Preview modes

| URL flags | Result |
|---|---|
| (none) | Existing cel V1 + Chladni / caustics; existing avatar/shrine |
| `?render=legacy` | Original Lambert environment / old toon ramp; Chladni and new caustics off |
| `?npr=v2` | Coloured RGB ramps on toon materials, including terrain, animated characters, and compatible GLBs |
| `?npr=v2&avatar=chibi&shrine=glb` | Comparison scene: recovered chibi + Higgsfield shrine with selective deep-plum ink |
| `?npr=v2&kuwahara=1&avatar=chibi&shrine=glb` | Above, with edge-directed anisotropic Kuwahara painterly filter |
| `?kuwahara=1` | Test painterly filter independently of new colour ramps |
| `?npr=v2&kuwahara=0` | NPR V2 only; no full-screen GPU cost |

## Shading

- `js/cel.js`: six reusable palettes + default: skin, fabric, foliage, stone, metal, crystal.
- Texture is **three RGBA ramp pixels, nearest filtered**, used as a lighting multiplier by Three's MeshToonMaterial. Surface base colour, instancing tints, albedo texture maps, outfit dyeing, emissive intensity and alpha are retained. This is *MToon-inspired*, not a copy of pixiv's source or a complete MToon implementation. These are **chromatic lighting bands**, not absolute per-pixel shadow-colour overrides.
- `js/chibi.js`: explicitly tags skin/hair/cloth/musical metal, avoiding blanket per-material tint.
- `js/activities.js`: routes all procedural POI meshes through the shared environment material constructor for style convergence.
- `js/asset-loader.js`: maps named GLB material parts to palette roles; adds selective BackSide ink to three hero silhouettes only, never every component. Ink is marked `userData.melodiaInk` so a recursive traversal doesn't re-process the hull.
- Other existing animated chibi/Choral Sheep outlines remain unchanged in topology.

## Painterly abstraction

`js/painterly.js` is a new WebGL1-compatible GLSL image-processing pass.

1. Render the world to a reduced-resolution `WebGLRenderTarget`.
2. Estimate a **local structure tensor** from horizontal/vertical RGB derivatives.
3. Orient an elliptical sampling footprint along the minor-eigenvector (edge tangent), with its elongation controlled by coherence.
4. Compute four quadrant-window means and variances using bounded taps, then blend by inverse variance (preserves contrast edges).
5. Mix the filtered result with the unfiltered render.

The directional Kuwahara method follows the *ideas* in Kyprianidis, Kang and Döllner, “Image and Video Abstraction by Anisotropic Kuwahara Filtering” (2009). Implementation is a new compact shader for this project, **not copied source** from another repository. Unlike the paper's complete formulation, this P0 uses 4 rectangular sectors in the rotated elliptical frame rather than continuous polynomial-weight sectors, prioritizing simple, bounded GPU cost.

- Disabled by default, including on phones. Enable only via `?kuwahara=1`.
- Desktop: half internal resolution, radius 3, strength 0.65 (max 49 samples + derivatives per filtered pixel).
- Coarse/touch devices: 0.35 internal resolution, radius 2, strength 0.45.
- HUD labels are on a separate 2D canvas and stay crisp.
- Renderer dynamic DPR and resize logic remains authoritative; the intermediate texture is resized accordingly.
- Disable with `?kuwahara=0` or remove the flag.

## Original references

- https://github.com/pixiv/three-vrm (MToon design study; independent implementation)
- https://github.com/cortiz2894/stylized-components (stylized water/foliage direction; no source copied)
- https://www.kyprianidis.com/p/pg2009/ (anisotropic Kuwahara paper)
- https://threejs.org/docs/pages/MeshToonMaterial.html (Three.js gradientMap shader contract)

## Gate to merge

- Both repo branches pass the cloud static checks, headless WebGL start / chibi / GLB / mobile / NPR V2 / painterly states.
- No console GL program errors; check the full-screen pass renders real pixels, not only its presence.
- Compare in live desktop browser: rim/ink readability, skin tone preservation, underwater vs shoreline colours, shadow ramps not washed out.
- Check mobile Safari movement/audio and base-vs-V2 FPS/memory: `?kuwahara=1` is intentionally experimental and should never silently enable at mobile launch.
- Only after this, promote an opt-in/shader release to main. The reference paper and code do not justify claiming visual perfection or a full MToon renderer.

## Live-look tuning (cloud branch only)

Open `?npr=v2&kuwahara=1&avatar=chibi&shrine=glb&tune=1` for a small collapsible overlay. The shader updates **without reloading or altering gameplay**.

Preset links: `&look=soft` (watercolour), `&look=storybook` (balanced), `&look=dream` (dramatic). Sliders set `paint` (blend), `rad` (1–3), `anis` (edge tangent elongation), `edge` (variance power / edge selection), `shadow` (RGB ramp tint), `ink` (selective outline alpha) and `scale` (intermediate render resolution). Each change updates the URL for repeatable visual review. The copy control writes that URL when clipboard access is permitted.

This panel loads only with `tune=1`. Mobile opens it collapsed and caps its rendering scale at 0.5. The original `?npr=v2&kuwahara=1` viewer receives no panel and no added browser interaction. A zero painterly-strength setting bypasses the postprocess render target entirely.

Tuning acceptance: cloud Chromium validates seven uniforms/controls, shareable URL and reload persistence. This does not prove the filter is visually ideal or that mobile sustained FPS is sufficient.
