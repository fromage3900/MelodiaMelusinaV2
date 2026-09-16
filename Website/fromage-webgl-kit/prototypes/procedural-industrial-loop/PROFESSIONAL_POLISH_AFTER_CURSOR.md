# Procedural Industrial Loop — Professional Polish After Cursor

**Date:** 2026-09-10  
**Status:** HOLD UNTIL CURSOR MONOCHROME PATCH IS APPLIED TO `my-site`  
**Purpose:** one final buyer-facing polish pass for the $10k industrial homepage listing. This is not a redesign and must not overwrite Cursor's in-flight monochrome/capture work.

## Current builder architecture

The industrial proof is already structurally credible:

```text
procedural station grammar
→ named station / component hierarchy
→ deterministic seeded assembly
→ absolute-time timeline helper
→ one-axis linear mechanical phases + hard holds
→ BASE / STRUCTURAL / FLOW / THERMAL material states
→ runtime diagnostics
→ capture/evidence layer
```

The remaining work is presentation hierarchy, not new technical scope.

## Professional-polish priorities

### P0 — Make BASE read like machined product visualization

Keep BASE strictly greyscale. Create separation with **value, roughness, metalness, edge response and shadow**, not hue.

Recommended role hierarchy:

- primary body: light warm-neutral machined finish, medium roughness;
- structural/machine elements: darker neutral metal, tighter highlights;
- secondary shell/panels: slightly lighter or softer matte response;
- moving actuator: strongest local value/roughness contrast so motion reads immediately;
- floor/background: quieter than every machine surface.

Avoid chrome, black crush, glossy-car-paint response, bloom, colored rim lights and dramatic HDRI reflections.

### P0 — Strengthen silhouette and composition

The fixed camera is a strength because it proves motion-law obedience. Do not add orbiting/cinematic camera motion.

For the capture seed:

- choose one strongest seed and freeze it as the primary evidence composition;
- keep all three stations legible without tangent collisions;
- preserve a clear foreground/midground rhythm;
- leave deliberate negative space around the moving elements;
- avoid cropping base plates, actuator travel or the system rail;
- use a restrained 3/4 elevated industrial-product angle;
- ensure the moving axis reads from the first frame without explanatory text.

Other seeds remain proof of procedural variation; they do not all need equal beauty.

### P0 — Separate presentation UI from engineering/debug UI

Default buyer-facing presentation should feel like a finished visualization, not a dev dashboard.

In normal interactive mode, keep only:

- timeline scrubber;
- play/pause;
- seed selector;
- BASE / STRUCTURAL / FLOW / THERMAL mode selector;
- one compact status line for current phase/time.

Move raw FPS/DPR/draw-call/triangle/geometry numbers behind a `Diagnostics` disclosure or query flag.

In `?capture=1`:

- no intro paragraph;
- no control panel;
- no debug numbers;
- no browser-demo framing;
- canvas fills the intended 16:9 frame;
- optional tiny mode label only if it helps distinguish evidence stills;
- capture should default to the strongest seed and BASE unless query params explicitly override it.

Do not hide evidence from internal QA; simply separate it from the hero capture.

### P0 — Deterministic capture URLs

If Cursor's capture implementation does not already support these, prefer a tiny query-param contract rather than manual setup:

```text
?capture=1&seed=1&mode=base&t=0
?capture=1&seed=1&mode=structural&t=6
?capture=1&seed=1&mode=flow&t=6
?capture=1&seed=1&mode=thermal&t=6
```

A capture URL should resolve to the same composition/state every time. Do not add a full capture application.

### P1 — Add restrained industrial scale cues

Only if the scene still reads as abstract blocks after the Cursor polish, add a small number of geometry cues that suggest a designed system without implying fake engineering data:

- flange/ring transitions;
- recessed panel seams;
- feet/mounts;
- collars around actuator rods;
- simple fastener-like details;
- cable/pipe support brackets;
- repeated alignment grooves.

These should improve scale and fabrication readability, not turn the proof into a detailed CAD model.

Do **not** add fake pressure values, fake compliance labels, fake engineering certifications, nonsensical gauges or client-like logos.

### P1 — Visualization-mode clarity

STRUCTURAL / FLOW / THERMAL are illustrative technical-art states, not simulations.

Professional treatment:

- BASE geometry/material hierarchy remains visible beneath the information color;
- color is reserved for encoded state only;
- avoid rainbow/noisy palettes;
- use 4–5 discrete perceptual bands with clear low→high ordering;
- optional tiny `ILLUSTRATIVE FIELD` legend in interactive mode;
- captures should remain understandable without implying calculated FEA/CFD/thermal results.

### P1 — Performance sanity, not premature optimization

Cursor's automated capture report showed approximately 3.5k triangles but ~95 draw calls. That imbalance is worth noting, but do not rewrite the architecture solely to chase a benchmark before local runtime testing.

First run the scene in a normal local desktop browser. If it is smooth there, preserve the named hierarchy because that hierarchy itself is relevant to staged industrial production.

If performance is visibly poor, optimize in this order:

1. share/reuse material instances instead of creating one material per part;
2. share repeated geometries;
3. instance only genuinely repeated static details;
4. reduce shadow-casting lights/objects where unnecessary;
5. cap DPR appropriately;
6. only then consider mesh merging.

Do not destroy meaningful part naming or animation hierarchy for an arbitrary draw-call target.

## Copy polish

Replace internal language such as `clean-room proof` in buyer-facing UI/copy with:

- `independent mechanical proof`;
- `procedural mechanical study`;
- `deterministic industrial motion study`.

Keep the stronger internal/IP language in evidence docs where useful.

## Capture package definition

The professional submission package should contain only:

1. `industrial_loop_base_16s.mp4` — uninterrupted full loop, strongest seed;
2. `industrial_base_hero.png` — strongest monochrome still;
3. `industrial_structural.png`;
4. `industrial_flow.png`;
5. `industrial_thermal.png`;
6. optional `industrial_seed_variation.png` or a 3-up seed sheet;
7. proposal copy;
8. one technical note or live demo URL if available.

Do not attach a giant debug/contact sheet unless requested.

## Acceptance gate before proposal

Mark this lane `PROPOSAL READY` only when all are true:

- Cursor patch is applied to `my-site` and source authority is no longer split;
- normal local browser has zero blocking console errors;
- full 16s BASE loop has been observed/captured;
- 0s and 16s resolve to the same pose;
- one active mechanical axis per active phase is visually obvious;
- BASE remains greyscale;
- information color appears only in labelled illustrative modes;
- hero frame has no debug UI;
- desktop capture looks intentionally composed;
- proposal does not claim CAD import, ProRes, AV1/VP9 <5 MB delivery or real engineering simulation unless separately proven.

## Stop condition

Once the acceptance gate is green, **send the proposal**. Do not add more machinery, procedural systems, shaders, post FX, camera motion or framework abstractions before submission.

## Next single action

Apply Cursor's monochrome/capture patch to `my-site`, then compare one `?capture=1` hero frame against this checklist. Fix only visible P0 failures.