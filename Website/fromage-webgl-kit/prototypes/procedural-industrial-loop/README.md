# Procedural Industrial System Loop

**Status:** ARCHIVED REUSABLE PROOF / NOT AN ACTIVE STRIKE

This clean-room Three.js prototype remains useful evidence for deterministic browser animation, procedural composition, capture discipline and restrained technical presentation. The original high-value Upwork listing that motivated it is no longer active; no proposal/application state is maintained here.

## What is proven

The current browser build was sanity-checked on a real GPU-backed Chrome session.

Observed on the checked build:

```text
loopDelta      0
canonical seed 1
draw calls     110
triangles      74,030
geometries     54
blocking console errors 0
```

The project contains a deterministic 16-second absolute-time mechanical loop, three seeded layout variants, fixed-camera presentation, capture-state URLs and BASE / STRUCTURAL / FLOW / THERMAL component-coding views.

**Important truth boundary:** Structural / Flow / Thermal are illustrative per-component colour codings. They are **not** FEA, CFD, thermal simulation, solver output or spatial data fields.

## Evidence retained

`evidence/` contains the useful proof artifacts rather than proposal paperwork:

- `industrial_loop_base_16s.mp4` — 16-second H.264 loop;
- `industrial_base_hero.png`;
- `industrial_structural.png`;
- `industrial_flow.png`;
- `industrial_thermal.png`;
- `attachment_capture_log.json` — machine-readable capture record.

These artifacts are reusable capability evidence for future procedural/technical-presentation work.

## Runtime design

The motion schedule is intentionally simple and deterministic:

```text
00–02  Station A translate +X
02–04  Station B rotate +Y
04–06  Station C translate +Y
06–08  hold
08–10  Station C reverse
10–12  Station B reverse
12–14  Station A reverse
14–16  hold / loop boundary
```

Pose is sampled from absolute timeline time rather than accumulated frame motion. Reusable timeline logic lives at:

`../../src/animation/createDeterministicTimeline.js`

## Run locally

Serve the repo over HTTP, then open:

```text
/tools/fromage-webgl-kit/prototypes/procedural-industrial-loop/
```

Useful deterministic capture form:

```text
?capture=1&seed=1&mode=base&t=4
```

## Reuse boundary

Good future claims:

- deterministic mechanical browser animation;
- seeded procedural composition;
- fixed-camera art direction;
- repeatable capture/state control;
- realtime WebGL delivery awareness.

Do not claim from this proof alone:

- client CAD import/cleanup;
- engineering simulation/solver integration;
- real structural/flow/thermal computation;
- ProRes delivery;
- AV1/VP9 byte-budget guarantees;
- a specific buyer’s production requirements.

Do not expand this prototype unless a qualified paid lead specifically requires a missing capability. Git history preserves the original proposal/strike paperwork if it is ever needed for archaeology.
