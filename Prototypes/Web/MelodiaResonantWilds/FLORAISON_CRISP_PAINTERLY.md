# Floraison Crisp — optional painterly treatment (v16 candidate)

This experiment is a source-level port of the anisotropic Kuwahara study from `fromage3900/my-site` commit `d2c3379e9efdf878111e29560a2db5dc701250c0`. It **does not** replace the canonical NPR hard RGB cel shaders, Bloom/OutlinePass, gameplay or 100-GLB catalog.

The historical full-strength look used `paint=1&rad=3&anis=1.5&edge=3.7&shadow=0.12&ink=0.67&scale=0.5`. The earlier implementation blurred the entire scene by first rendering into a **half-resolution** target and upscaling the result. This new pass uses the same variance-weighted directional stroke idea but samples the full-size compositor output, locks real cel/ink edges to the original pixels, and disables the final FXAA blur while paint is running.

### Compare locally on this branch

Serve `Prototypes/Web/MelodiaResonantWilds/` as usual; the flags are not currently live on `my-site`.

- **Hard cel only:** `?npr=v2&botany=1&pov=1&grove=full&kuwahara=0`
- **Floraison crisp:** `?npr=v2&botany=1&pov=1&grove=full&kuwahara=1&tune=1&look=floraison&sharp=0.95`
- **Historical settings, with crisp edge protection:** `?npr=v2&botany=1&pov=1&kuwahara=1&tune=1&look=custom&paint=1&rad=3&anis=1.5&edge=3.7&shadow=0.12&ink=0.67&sharp=0.95&scale=0.5`. **Important:** `scale=0.5` is ignored; no half-resolution upscale is performed.
- **A/B, same materials without paint:** `?npr=v2&kuwahara=1&paint=0&postfx=0`
- **Phone candidate:** `?botany=1&pov=1&lite=1&kuwahara=1&rad=2&paint=0.62&sharp=0.95`. On coarse pointers the shader clamps radius to 2; painting is opt-in rather than a mobile default.

### Ownership, ordering and performance

The actual render stack is **hard RGB cel / Chladni materials → canonical RenderPass + optional Outline + Bloom → OutputPass → full-res directional Kuwahara → display**. With paint active, an extra FXAA pass is disabled to retain flower silhouettes and thin ink lines. `?postfx=0` disables bloom/outlines while leaving the optional paint compositor available. Painterly is off by default even though Nikki world postfx may be on.

There are up to **49 samples plus local derivatives per output pixel** at radius 3; **this has a real performance cost on phones**. The radial cap of 2 on coarse pointer devices reduces work; low-end quality is still an opt-in test. Browser screenshots and real iPhone Safari performance QA must pass before an owner publishes it.

### Release gates

`node tools/check_crisp_painterly.mjs`, `node tools/check_cloud_intake.mjs`, `node tools/check_world_stack.mjs`, and the Cloud Intake Playwright scenarios for Floraison crisp, mobile crisp and paint-off A/B. Reject WebGL shader console warnings, black frames, missing HUD text, blurred outlines, FPS drops or overheating. This is not an automatic publishing authorization.
