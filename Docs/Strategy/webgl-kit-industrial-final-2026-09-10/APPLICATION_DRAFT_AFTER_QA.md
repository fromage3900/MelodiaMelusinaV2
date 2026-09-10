# Industrial Homepage Listing — Application Draft After QA

**Status:** READY TO PASTE  
**Evidence:** `EVIDENCE.md`, `LISTING_10000_EVIDENCE.md`, `evidence/`

## Short proposal draft

Hi — your motion brief stood out because the constraints are unusually clear: constant-speed mechanical motion, one axis at a time, dead stops, no easing/overshoot, a restrained monochrome base, and color reserved for information visualization.

I work across real-time 3D, procedural systems, Blender/Houdini, and Three.js. To make sure I understood the motion law rather than just saying I could follow it, I built a small independent procedural mechanical study using original geometry. It uses an absolute-time 16-second timeline, linear transform segments, explicit hard holds, deterministic seeded assemblies, and separate Structural / Flow / Thermal visualization styles.

Attached:

- uninterrupted 16s BASE loop (Seed 01)
- monochrome BASE hero still
- Structural / Flow / Thermal stills

The study is intentionally generic and does not reproduce your CAD, prototype, branding, or scene. I would apply the same controlled approach to your supplied assets: preserve naming and hierarchy, validate CAD cleanup first, approve one station/material treatment before full population, then build the deterministic master animation and test the final AV1/VP9 encode against the actual `<5 MB` target.

Relevant runtime proof from the demo:

- browser / viewport: Chrome; 1920×1080 capture
- triangles / draw calls: 16948 tris / 81 draws
- approximate FPS: ~23–32 in headless capture; higher expected on desktop GPU
- loop endpoint delta: 0.000000
- 16-second capture: `industrial_loop_base_16s.mp4`

I’m comfortable working in staged approvals and would prefer to lock geometry/hierarchy and the single-station look before expanding the full scene.

## Suggested answers to likely screening questions

### What software / pipeline would you use?

For supplied CAD, I would use Blender or Houdini for import cleanup, hierarchy control, naming validation, normals/topology/material grouping, and procedural assembly. The browser study uses Three.js because it makes the deterministic motion law easy to expose and test interactively; the production master can remain DCC/render-first if that best matches the supplied pipeline and delivery specification.

### How would you guarantee constant-speed motion and dead stops?

I would avoid eased Bezier motion for the required mechanical actions. Each moving property is driven by explicit linear/stepped timing segments with absolute start/end states. Holds are authored as actual constant-value intervals. That makes the motion scrub-safe and makes it straightforward to verify that only the intended axis changes during each segment.

### How would you approach the solver-inspired color states?

I would treat Structural / Flow / Thermal as controlled visualization languages, not decorative gradients. Base geometry remains restrained; color appears only when communicating a state or scalar field. I would first match the approved palette and hierarchy on one station, then propagate the system after approval.

### How would you hit the web-delivery target?

I would separate master quality from delivery compression: render/approve the clean master first, then test VP9 and AV1 encodes against the actual visual-quality threshold and `<5 MB` requirement. I would not assume a bitrate or codec setting is sufficient without measuring the resulting file.

## Before submitting

- attach the five primary media files from `evidence/`;
- verify the listing is still active;
- do not claim CAD import, ProRes, or AV1/VP9 `<5 MB` delivery yet.
