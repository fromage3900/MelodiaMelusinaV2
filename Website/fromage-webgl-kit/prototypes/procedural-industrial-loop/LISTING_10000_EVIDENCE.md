# $10,000 Procedural Industrial Homepage Listing — Proof Mapping

**Listing:** https://www.upwork.com/freelance-jobs/apply/artist-animate-and-build-the-the-loop-animation-the-company-homepage_~022096976272432704858/  
**Checked:** 2026-09-10  
**Prototype:** `tools/fromage-webgl-kit/prototypes/procedural-industrial-loop/`  
**Current decision:** BUILD / VERIFY / CAPTURE — DO NOT APPLY YET

## Why this prototype exists

The listing asks for production-quality execution of an already-defined industrial animation system: supplied CAD, strict mechanical motion laws, solver-inspired information visualization, staged approvals, and a 16-second seamless web hero loop.

This prototype demonstrates the relevant **system thinking** without copying their prototype, CAD, brand specification, colors, or proprietary scene.

## Requirement mapping

| Listing requirement | Generic proof in this prototype | Status |
|---|---|---|
| Procedural/system-driven motion | Absolute-time procedural choreography | SOURCE IMPLEMENTED |
| One axis at a time | Timeline assigns one primary motion per active segment | SOURCE IMPLEMENTED |
| Constant speed | Shared deterministic timeline performs linear channel sampling | SOURCE IMPLEMENTED |
| Dead stops / no easing | Explicit linear segments plus hard holds | SOURCE IMPLEMENTED |
| Seamless ~16s loop | 16s mirrored return schedule + numeric endpoint delta | SOURCE IMPLEMENTED / RUNTIME VERIFY |
| Machined/systemic geometry | Modular box/cylinder industrial station grammar | SOURCE IMPLEMENTED |
| Monochrome base | Neutral grey base mode | SOURCE IMPLEMENTED |
| Color only for information | Structural/Flow/Thermal illustrative modes | SOURCE IMPLEMENTED |
| Scientific/technical visual sensibility | Discrete field-value color bands | SOURCE IMPLEMENTED / ART QA NEEDED |
| Seeded procedural variation | Three deterministic assembly seeds | SOURCE IMPLEMENTED / RUNTIME VERIFY |
| Runtime diagnostics | FPS, DPR, draw calls, triangles, geometry count, phase, loop delta | SOURCE IMPLEMENTED / VALUES UNMEASURED |
| CAD import | Not part of browser clean-room prototype | NOT PROVEN |
| DCC scene/outliner delivery | Browser hierarchy is named; Blender/Houdini production scene not yet built | PARTIAL |
| 2560×1080 master render | Not rendered yet | NOT PROVEN |
| ProRes/equivalent master | Not rendered yet | NOT PROVEN |
| <5 MB web video | Not encoded yet | NOT PROVEN |
| AV1/VP9 delivery | Not encoded yet | NOT PROVEN |
| Staged approval artifacts | Prototype can supply geometry/base/visual-mode screenshots after runtime QA | READY TO PROVE |

## Reusable commercial primitive produced

`src/animation/createDeterministicTimeline.js`

The prototype now consumes a generic absolute-time channel sampler rather than owning bespoke interpolation code. This is reusable for:

- industrial one-axis choreography;
- product-use animation;
- exploded assembly states;
- scroll-scrubbed technical presentation;
- locator/callout motion;
- deterministic loop construction.

This matters commercially because future jobs can reuse the motion-law primitive while changing geometry, timing, and art direction.

## Runtime values to fill after QA

Do not estimate these from source. Replace the blanks only with observed values.

```text
BROWSER / VERSION: __________
DESKTOP VIEWPORT: __________
PHONE VIEWPORT: __________
SEED 01 FPS: __________
SEED 02 FPS: __________
SEED 03 FPS: __________
DPR: __________
DRAW CALLS: __________
TRIANGLES: __________
GEOMETRIES: __________
LOOP Δ AT ENDPOINTS: __________
CONSOLE ERRORS: __________
16S CAPTURE PATH / URL: __________
BASE STILL: __________
STRUCTURAL STILL: __________
FLOW STILL: __________
THERMAL STILL: __________
WEB ENCODE TESTED: YES / NO
ENCODE FORMAT / SIZE: __________
```

## Honest proposal angle after runtime proof

The useful claim is not “I already recreated your project.” It is:

> I built a small procedural mechanical proof specifically around the motion law in your brief: absolute-time, piecewise-linear transforms, one active axis at a time, hard stops, no easing, and discrete solver-inspired visualization states. My production approach would preserve those constraints while moving the supplied CAD through a controlled DCC/render pipeline.

Do not use that language until the prototype has been runtime-checked.

## DCC production path if shortlisted

```text
CLIENT CAD + NAMING SPEC
→ Blender or Houdini import / cleanup
→ preserve supplied object naming
→ validate scale, normals, topology and material grouping
→ procedural hierarchy / motion controller
→ geometry approval turntable
→ neutral light-on-light single-station lookdev
→ structural / flow / thermal visualization materials
→ full assembly
→ 16s deterministic master animation
→ high-quality master render
→ AV1 / VP9 web encode tests
→ <5 MB target validation
→ source scene + staged evidence package
```

## What to build only if application advances

Do not spend time today implementing these unless the buyer responds or the proof itself needs them:

- real CAD import;
- production Blender/Houdini scene;
- 2560×1080 offline master;
- ProRes master;
- AV1/VP9 compression ladder;
- exact client-specified solver palettes;
- their supplied code prototype integration.

## Questions / answers worth preparing

1. **Software / procedural approach** — Blender or Houdini for CAD cleanup and procedural hierarchy; deterministic transform logic rather than animation curves with easing.
2. **Constant-speed/dead-stop method** — linear interpolation or stepped/linear animation curves only; disable Bezier easing, overshoot, spring behavior, secondary settle, camera drift, and organic procedural noise.
3. **Staged approval comfort** — geometry/outliner first, one-station material/lighting proof second, full population only after approval.
4. **Web delivery** — render master first, then test VP9/AV1 encodes against the actual <5 MB visual-quality threshold rather than assuming a bitrate will survive.

## Application gate

Application becomes `PROPOSAL READY` only after:

- runtime-clean browser proof;
- one full 16-second capture;
- three seed stills;
- BASE + STRUCTURAL + FLOW + THERMAL stills;
- recorded diagnostics;
- loop-endpoint equality observed;
- honest portfolio links chosen for spec-following / technical-art execution;
- listing rechecked as still active/current.

Until then: **BUILD / VERIFY / CAPTURE — DO NOT APPLY.**
