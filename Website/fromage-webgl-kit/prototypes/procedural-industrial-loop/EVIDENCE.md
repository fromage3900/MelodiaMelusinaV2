# Procedural Industrial System Loop — Evidence

**Status:** FINAL SOURCE ON `my-site/main` / ONE NORMAL-BROWSER SANITY CHECK BEFORE SEND  
**Date:** 2026-09-10

This prototype is an independent capability proof for procedural/system-driven industrial animation. It is not a reconstruction of any prospective client's CAD, prototype, branding, or proprietary animation.

## Canonical source now on `my-site/main`

The current source includes:

- Three deterministic layout seeds; Seed 01 is canonical for submission.
- 16-second absolute-time loop driven by `src/animation/createDeterministicTimeline.js`.
- Strict piecewise-linear motion with one primary axis active at a time.
- Explicit hard holds and mirrored return to the authored start state.
- Fixed 28-degree camera; no cinematic camera motion.
- Greyscale BASE presentation only.
- Shared BODY / SHELL / ACCENT / MACHINE / ACTUATOR material families.
- RoomEnvironment reflection response, ACES tone mapping, restrained studio lighting, and limited soft shadow casting.
- Rounded fabricated housings plus sparse collars, service trays, feet, brackets/fastener cues.
- BASE / STRUCTURAL / FLOW / THERMAL modes; color is reserved for information-bearing visualization modes.
- Structural / Flow / Thermal fields remain illustrative, not FEA/CFD/thermal simulation.
- Deterministic capture-state query contract, for example:
  - `?capture=1&seed=1&mode=base&t=4`
  - `?capture=1&seed=1&mode=structural&t=5.2`
  - `?capture=1&seed=1&mode=flow&t=5.2`
  - `?capture=1&seed=1&mode=thermal&t=5.2`
- Buyer-facing controls for timeline, seed, and visualization mode.
- Diagnostics moved behind a disclosure; capture mode is chrome-free/full-bleed.
- Programmatic `window.__industrialLoop` state/setter surface for repeatable capture QA.
- Safe assembly rebuild removes children through `sceneRoot.remove(...)` rather than mutating the children array directly.

## Motion schedule

```text
00–02  Station A actuator translates +X at constant speed
02–04  Station B actuator rotates +Y at constant angular speed
04–06  Station C actuator translates +Y at constant speed
06–08  hard hold
08–10  Station C reverses at constant speed
10–12  Station B reverses at constant angular speed
12–14  Station A reverses at constant speed
14–16  hard hold / loop boundary
```

The pose is sampled from absolute timeline time, not accumulated frame-to-frame motion. The shared timeline's source-level endpoint delta is therefore expected to be zero.

## Preserved observed evidence from Cursor final pass

Cursor's exact final capture build is safely preserved in Melodia branch `cursor/industrial-final-polish-9850` / PR #176 because that cloud agent could not push `my-site` directly.

Its preserved runtime receipt records:

- no console errors observed;
- canonical Seed 01;
- 81 draw calls;
- 16,948 triangles;
- `LOOP Δ = 0`;
- full 16-second BASE MP4 and WebM;
- BASE hero still;
- STRUCTURAL / FLOW / THERMAL stills;
- Seed 01/02/03 captures and 3-up variation;
- mobile-width capture.

These numbers describe Cursor's captured final build. The source has now been promoted into `my-site/main` through a fresh bounded implementation because GitHub's connector could not safely expand the 4.4 MB transfer patch. Run one normal-browser sanity check before treating the `my-site/main` runtime numbers as identical to the preserved receipt.

Headless FPS values are intentionally not promoted as buyer-facing performance claims.

## Submission attachment set

Use the preserved final evidence bundle from PR #176:

1. `industrial_loop_base_16s.mp4`
2. `industrial_base_hero.png`
3. `industrial_structural.png`
4. `industrial_flow.png`
5. `industrial_thermal.png`

Optional: `industrial_seed_variation.png`.

## Remaining gate

Only one bounded runtime confirmation remains before send:

1. Serve current `my-site/main` over HTTP.
2. Open normal interactive mode and confirm no blocking console errors.
3. Open `?capture=1&seed=1&mode=base&t=4` and verify deterministic state/camera composition.
4. Scrub 0 / 2 / 4 / 6 / 8 / 10 / 12 / 14 / 16 seconds and confirm the motion law still reads correctly.
5. Confirm `window.__industrialLoop.getState().loopDelta` is zero.
6. Do not expand scope after this check; fix only blockers.

## Handoff

```text
STATUS: FINAL SOURCE CANONICAL / SANITY CHECK GATED
SOURCE AUTHORITY: fromage3900/my-site main
PRESERVED CAPTURE AUTHORITY: Melodia PR #176
CANONICAL SEED: 01
BUYER-FACING CLAIM: deterministic mechanical motion + restrained information visualization
DO NOT CLAIM YET: client CAD import, ProRes delivery, <5MB AV1/VP9 delivery, buyer-facing FPS benchmark
NEXT SINGLE ACTION: one normal-browser sanity check, then human-review attachments/proposal and submit
DO NOT REOPEN: motion architecture, new machinery, bloom, camera animation, real solver work, CAD parsing
```
