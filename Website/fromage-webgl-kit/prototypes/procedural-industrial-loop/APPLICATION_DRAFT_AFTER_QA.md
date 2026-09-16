# Industrial Homepage Listing — Application Draft After QA

**Status:** READY AFTER ONE NORMAL-BROWSER SANITY CHECK  
**Date:** 2026-09-10  
**Submission evidence authority:** Cursor final capture package preserved in Melodia PR #176.  
**Source authority:** `fromage3900/my-site` `main`.

## Short proposal draft

Hi — your motion brief stood out because the constraints are unusually clear: constant-speed mechanical motion, one axis at a time, dead stops, no easing/overshoot, a restrained monochrome base, and color reserved for information visualization.

I work across real-time 3D, procedural systems, Blender/Houdini, and Three.js. To make sure I understood the motion law rather than just saying I could follow it, I built a small independent procedural mechanical study using original geometry. It uses an absolute-time 16-second timeline, linear transform segments, explicit hard holds, deterministic seeded assemblies, and separate Structural / Flow / Thermal visualization styles.

Live Interactive Viewer (Deterministic 16s Loop):
- https://anyone-accessing-leaves-glasgow.trycloudflare.com/tools/fromage-webgl-kit/prototypes/procedural-industrial-loop/

Attached:

- uninterrupted 16-second BASE loop, Seed 01;
- monochrome BASE hero still;
- Structural / Flow / Thermal stills.

The study is intentionally generic and does not reproduce your CAD, prototype, branding, or scene. I would apply the same controlled approach to your supplied assets: preserve naming and hierarchy, validate CAD cleanup first, approve one station/material treatment before full population, then build the deterministic master animation and test the final AV1/VP9 encode against the actual `<5 MB` target.

The motion proof is scrub-safe and returns to its authored start state at the 16-second boundary. I am comfortable working in staged approvals and would prefer to lock geometry/hierarchy and the single-station look before expanding the full scene.

## Suggested answers to likely screening questions

### What software / pipeline would you use?

For supplied CAD, I would use Blender or Houdini for import cleanup, hierarchy control, naming validation, normals/topology/material grouping, and procedural assembly. The browser study uses Three.js because it makes the deterministic motion law easy to expose and test interactively; the production master can remain DCC/render-first if that best matches the supplied pipeline and delivery specification.

### How would you guarantee constant-speed motion and dead stops?

I would avoid eased Bezier motion for the required mechanical actions. Each moving property is driven by explicit linear timing segments with absolute start/end states. Holds are authored as actual constant-value intervals. That makes the motion scrub-safe and makes it straightforward to verify that only the intended axis changes during each segment.

### How would you approach the solver-inspired color states?

I would treat Structural / Flow / Thermal as controlled visualization languages, not decorative gradients. Base geometry remains restrained; color appears only when communicating a state or scalar field. I would first match the approved palette and hierarchy on one station, then propagate the system after approval.

### How would you hit the web-delivery target?

I would separate master quality from delivery compression: render/approve the clean master first, then test VP9 and AV1 encodes against the actual visual-quality threshold and `<5 MB` requirement. I would not assume a bitrate or codec setting is sufficient without measuring the resulting file.

## Attachments

Use the final evidence set from Cursor's PR #176 transfer package:

1. `industrial_loop_base_16s.mp4`
2. `industrial_base_hero.png`
3. `industrial_structural.png`
4. `industrial_flow.png`
5. `industrial_thermal.png`

Optional: `industrial_seed_variation.png`.

## Before submitting

- perform one normal local-browser sanity check of current `my-site/main`;
- verify the listing is still active;
- make sure all five attachments open correctly;
- do not quote headless FPS as a buyer-facing performance claim;
- do not claim client CAD import, ProRes delivery, or `<5 MB` AV1/VP9 delivery as already completed;
- submission remains a human decision.
