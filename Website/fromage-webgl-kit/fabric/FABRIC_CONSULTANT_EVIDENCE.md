# Fabric Technical-Art Consultant — Existing Evidence Map

**Status:** SOURCE EVIDENCE PRESENT / RUNTIME + PROVENANCE VERIFY  
**Date:** 2026-09-10  
**Commercial target:** Three.js fabric technical-art consulting, garment/material lookdev, and knitwear configurator work.

This file records what the current repository already proves, what it only suggests, and what still needs direct runtime/provenance evidence before being used in a proposal.

## Existing source evidence

The portfolio already contains a reusable browser-side fabric/material inspection system rather than a blank prototype.

### Fabric preset manifest

`wix/melodia-3d-viewport.js` currently defines named fabric families with texture resources and material-response parameters, including:

- Royal Velvet;
- Gilded Brocade;
- Sheer Silk / Chiffon;
- Baroque Lace;
- Gold Embroidery;
- Celestial Weave;
- Melusina Shirt Silk.

The manifest references combinations of:

- base-color texture;
- normal texture;
- ORM-style packed texture;
- optional sheen texture metadata;
- roughness multiplier;
- metalness multiplier;
- sheen-color metadata.

This is useful evidence of organized material-family thinking, but the commercial lane must not assume every referenced texture is owner-authored or redistributable until provenance is checked.

### Browser material construction

The existing viewer builds runtime material variants including:

- PBR presentation with `MeshStandardMaterial`;
- normal-map response;
- roughness-map response;
- metalness-map response;
- AO-map response;
- editable preset-level roughness and metalness scalar values in source;
- emissive tint used as a lightweight artistic sheen approximation;
- clay inspection;
- wireframe inspection;
- normal inspection;
- roughness inspection;
- metallic inspection;
- AO inspection;
- toon presentation.

### Existing lighting / presentation proof

The current viewer contains a dedicated multi-light setup with ambient, key, fill, rim, and bounce lights plus an inspection pedestal / turntable presentation surface.

This supports a useful consulting claim: the system evaluates material response under an authored realtime light rig rather than displaying unlit texture swatches.

## What this proves today

After a real browser smoke test, the existing system can honestly support claims such as:

- experience organizing multiple PBR textile/material families for realtime use;
- browser-side material lookdev in Three.js;
- texture-resource organization for base color / normal / packed material channels;
- material inspection modes for topology and channel debugging;
- realtime lighting evaluation of stylized textile response;
- experience moving garment/material assets toward interactive 3D presentation.

Do not upgrade these to stronger claims until evidence exists.

## Important approximation / limitation notes

The current implementation is an artistic realtime approximation, not a measured textile renderer.

Specifically:

- `MeshStandardMaterial` is not a fiber-level cloth BRDF;
- the current sheen treatment uses a lightweight artistic approximation rather than measured anisotropic/fiber scattering;
- packed ORM usage should be audited carefully because channel conventions can differ between tools/exporters;
- texture color-space and modern Three.js material handling should be reviewed when extracting a clean-room commercial version;
- no measured physical swatch-to-BRDF pipeline is currently proven;
- no spectrophotometer/colorimeter workflow is currently proven;
- no automated camera-to-tileable-fabric acquisition system is currently proven;
- no claim of physically exact color or fiber reproduction should be made.

## CLO capability

Brennan has used CLO 3D. Treat this as real owner experience.

The strongest evidence package will be an original garment created or edited in CLO, then moved through a documented web pipeline:

```text
CLO source
→ geometry / UV export
→ Blender cleanup + optimization
→ material / texture preparation
→ GLB export
→ Three.js validation
→ optional configurator state
```

Use concrete evidence—CLO source/screenshot, exported geometry, cleaned Blender file, GLB and browser capture—rather than relying on a generic software-name claim.

## Provenance audit required before commercial reuse

For every existing fabric texture/preset, classify it as:

```text
OWNER_AUTHORED
CC0 / COMMERCIAL-REUSE LICENSED
THIRD_PARTY_RESTRICTED
UNKNOWN
MELODIA_SPECIFIC
```

Only the first two classes may enter the reusable commercial kit, with license/source records retained where relevant.

Unknown provenance is a blocker for reuse, not for learning from the architecture.

## Smallest missing commercial proof

Do **not** rebuild the Fabric Lab.

After runtime/provenance audit, add only the smallest missing clean-room capability needed to answer current buyer requirements. Preferred order:

1. original CLO garment or neutral owned swatch asset;
2. clean-room material presets with known provenance;
3. close-up and grazing-angle inspection views;
4. runtime controls for roughness / normal strength / sheen-like response;
5. base-color / stitch preset switching;
6. compact state readout;
7. local JSON state export for configurator proof.

Stop once the current listing can be answered honestly.

## Consultant-facing evaluation checklist

When reviewing a garment/material pipeline, inspect:

### Geometry
- silhouette quality at target camera distance;
- topology density versus deformation / close-up need;
- correct normals / tangents;
- UV scale and distortion;
- draw-call / material-slot count;
- garment thickness strategy;
- unnecessary hidden geometry.

### Texture resources
- base-color correctness and color space;
- normal orientation / strength;
- roughness response under grazing light;
- packed-channel convention;
- tiling frequency and visible repetition;
- texture dimensions relative to screen-space need;
- compression artifacts.

### Material model
- diffuse/specular balance;
- roughness range;
- fiber/sheen approximation;
- normal strength;
- double-sided rendering requirement;
- transparency/alpha cost when relevant;
- shader complexity versus visual gain.

### Lighting / validation
- neutral soft studio light;
- grazing-angle light;
- close-up camera;
- whole-garment camera;
- consistent exposure;
- mobile / lower-DPR check;
- representative browser/device performance.

### Delivery
- predictable GLB hierarchy/naming;
- minimal material count;
- documented texture set;
- compressed web payload where justified;
- reproducible export settings;
- host integration contract separated from visual asset pipeline.

## Three questions to ask the fabric consultancy client

1. **What is the visual target and error tolerance?** Is success an artistically convincing ecommerce image, a close visual match to photographed fabric, or a physically measured reproduction target?
2. **What physical input data do you actually have per swatch?** Controlled photographs, scanner captures, measured color values, weave/stitch dimensions, manufacturer maps, or only casual phone/reference photos?
3. **Where will the final materials run?** Vanilla Three.js, React Three Fiber, desktop/mobile ecommerce, fixed showroom hardware, or another renderer—and what are the actual texture/payload/performance limits?

## Next single action

Audit the existing fabric texture provenance, then choose one original CLO garment / clean-room material set for runtime proof. Do not build a second fabric application.
