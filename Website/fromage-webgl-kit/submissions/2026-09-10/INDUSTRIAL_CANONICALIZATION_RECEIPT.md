# Industrial Final Polish — Canonicalization Receipt

**Date:** 2026-09-10  
**Canonical repo:** `fromage3900/my-site`  
**Canonical branch:** `main`  
**Preserved capture authority:** `fromage3900/MelodiaMelusinaV2` PR #176

## What changed

The final industrial presentation behavior is now represented directly on `my-site/main` rather than existing only as a Cursor transfer patch.

Canonical source commits:

- `860f795ab049878fd0f14826cc97fb6ab99de269` — final industrial WebGL source implementation;
- `43f6d2e2ef775f0d8de7fee7016bf4608239ec92` — buyer-facing/capture presentation;
- `6452172f14d6c42850d3cc41f562965ba668cbdd` — proposal promoted to final sanity-check gate;
- `6408f0d3038f4a03b4729fb400ee21c29d2cb322` — evidence authority clarified;
- `ccc03bf4c4004fa0e4958936fc0e61e59b9e8a94` — submission manifest updated to canonical-source state.

## Important provenance note

Cursor's exact final `my-site` commit could not be imported bit-for-bit through the GitHub connector because its 4.4 MB `git format-patch` transfer blob could not be safely expanded by the available API.

Therefore the current `my-site/main` source is a **fresh bounded implementation of the final documented behavior**, built against the already-canonical `createRuntime.js` and `createDeterministicTimeline.js` helpers and syntax-checked before commit.

It intentionally implements the same buyer-facing contract:

- fixed 28-degree camera;
- RoomEnvironment reflection response;
- ACES tone mapping;
- soft studio shadowing;
- shared BODY / SHELL / ACCENT / MACHINE / ACTUATOR material families;
- rounded fabricated housings and restrained manufacturing detail;
- greyscale BASE mode;
- information-only Structural / Flow / Thermal color modes;
- 16-second absolute-time linear one-axis choreography;
- hard holds / no easing;
- Seed 01 canonical;
- deterministic `capture/seed/mode/t` URL state;
- diagnostics disclosure;
- chrome-free capture mode;
- programmatic `window.__industrialLoop` capture/QA surface.

## Cursor evidence remains preserved

Melodia PR #176 preserves Cursor's exact final capture package and runtime receipt, including:

- full 16-second BASE MP4/WebM;
- BASE hero;
- Structural / Flow / Thermal stills;
- seed variation captures;
- mobile capture;
- recorded zero console errors;
- `LOOP Δ = 0`;
- 81 draws / 16,948 triangles for Cursor's captured build.

Those measurements belong to Cursor's captured build. Do not assume the fresh canonical implementation has identical draw/triangle/FPS values until it is run once in a normal browser.

## Final gate

Before sending:

1. run current `my-site/main` in a normal browser;
2. confirm no blocking console errors;
3. verify `?capture=1&seed=1&mode=base&t=4` resolves deterministically;
4. verify timeline boundaries and `loopDelta === 0`;
5. human-review the five attachments and proposal;
6. send and stop.

No further architecture or visual expansion is authorized by this receipt.
