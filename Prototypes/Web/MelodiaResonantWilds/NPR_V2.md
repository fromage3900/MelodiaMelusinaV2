# Resonant Wilds — cel-shading NPR V2

## Rendering decision (2026-10-28)

**Anisotropic Kuwahara is retired and removed from the renderer.** It softened fine chibi detail and shadow boundaries and required a reduced-resolution offscreen pass. We chose material-directed hard RGB cel lighting, selective deep-plum inverted-hull outlines, and the existing musical Chladni/caustic shaders instead. This is an intentional art-direction and performance choice, not a pending toggle.

The filter module `js/painterly.js` was deleted; the game renders directly to its canvas at the device/quality DPR. The retired `?kuwahara=1` parameter is ignored so old shared links still work. No runtime postprocess target is allocated. New previews must not advertise it as supported.

## Preview modes

- `?render=legacy` — original Lambert terrain and original toon gradient, Chladni and caustics off.
- Default (no flags) — existing three-band cel V1 + musical Chladni and caustics.
- `?npr=v2` — hard chromatic shadow/mid/light ramps for skin, cloth, foliage, stone, metal and crystal. The Three.js r170 stock red-channel gradient function is overridden only in V2 so the ramp reads RGB correctly.
- `?npr=v2&avatar=chibi&shrine=glb` — animated chibi, GLB shrine, selective ink outlines, full canvas resolution.
- `?npr=v2&avatar=chibi&shrine=glb&tune=1` — optional collapsible **five-control cel-lighting tuner**.
- Presets: `&look=soft`, `&look=storybook` and `&look=dream` for increasing shadow hardness and ink definition.

## Shader and editing controls

`js/cel.js` contains material palettes, `getGradientIrradiance` RGB-band shader replacement, direct-light cutoffs and shared uniforms. V2 adjusts `hard` (transition hardness), `cut` (shadow cutoff), `dark` (shadow-band depth), `shadow` (RGB shadow colour strength) and `ink` (outline opacity). Shared uniforms update compiled materials without reloading. These are stylized direct-light bands, not fully physically accurate light/shadow occlusion.

`js/world.js` composes its independent Chladni/ripple hook with the NPR material hook. `js/asset-loader.js` assigns material roles and selective BackSide ink to hero GLB parts. `js/chibi.js` tags the chibi's skin, cloth, hair and accessories.

`js/npr-tuner.js` is loaded only with `tune=1`, updates the 5 GPU material controls and persists them in a shareable URL. Legacy painterly parameters are removed when a new tuning URL is generated.

## Validation and release gate

Static asset checks reject the removed filter and any stale service-worker asset entry. Cloud Chromium/WebGL tests cover legacy, defaults, mobile, chibi/GLB, V2 hard bands, old `kuwahara=1` links still running **without** the pass, and live-control persistence.

Before merging, inspect real iPhone Safari touch/audio/performance and shadow placement on Melusina's face, hair and cloth. Do not mistake Chrome SwiftShader smoke tests for real mobile GPU QA. No production deployment until the release PRs are reviewed.

## Reference

- Three.js r170 MeshToonMaterial gradientMap architecture (stock uses red-channel lighting);
- pixiv three-vrm MToon design ideas, independently implemented;
- earlier experimental Kuwahara study is retained in git history, not in the shipping renderer.
