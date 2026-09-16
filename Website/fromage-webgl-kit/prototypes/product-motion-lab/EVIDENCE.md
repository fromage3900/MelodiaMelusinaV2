# Product Motion Lab — Evidence

**Status:** GLB EXISTS + CHECKER PASS / BROWSER RUNTIME PROOF STILL OWED  
**Purpose:** reusable product/accessory presentation proof for Treasury SKU 2 and related proposals.

This file is the only status/evidence note for Product Motion Lab. Do not create another runtime handoff.

## Canonical source

- `../../scripts/build_auriga_meter.py` — Blender generator/exporter for the owned generic Auriga Meter demo.
- `../../scripts/check_auriga_meter.py` — GLB structure/evidence checker.
- `src/auriga-meter.js` — Three.js loader, anchor discovery, scrub control, wireframe/disposal helpers.
- `index.html` / `app.js` — browser presentation shell and procedural fallback.
- `assets/auriga_meter.glb` — generated demonstration artifact.

## Observed artifact

Generated under Blender 5.2.1 after correcting the Blender 4.4+ slotted-action API break and isolating headless config.

```text
assets/auriga_meter.glb  195,920 bytes
CHECK_OK
anchors       ANCHOR_hinge, ANCHOR_port, ANCHOR_screen (3/3)
animations    3
meshes        9
nodes         14
materials     4
triangles     ~2,844
```

`app.js` attempts the real GLB first and preserves a visible procedural fallback if loading fails.

## Implemented capability

- deterministic normalized 0–1 motion timeline;
- slider and scroll-driven scrub path;
- three parented annotation anchors;
- wireframe inspection;
- approximate renderer diagnostics;
- responsive layout + reduced-motion behavior;
- explicit load/error state.

This is directly relevant to premium eyewear/accessory work as **process proof**: web-ready asset structure, controlled motion, attached detail callouts, browser presentation and measured delivery discipline. It is not a claim of eyewear-specific production experience.

## Remaining runtime gate

Only execute what converts this from source proof to observed browser proof:

1. serve the lab over HTTP;
2. visually review the generated asset/silhouette;
3. confirm zero blocking console errors;
4. verify deterministic poses at 0 / 0.5 / 1 and repeatable `0 → 1 → 0` scrub;
5. confirm all three anchors remain attached through motion;
6. confirm desktop and phone-width usability;
7. record stabilized GLB bytes / triangles / draw calls / DPR / approximate FPS;
8. capture one hero, one motion/detail state, one anchor proof and one mobile proof.

Stop there. Do not rebuild the generator or invent a second product unless a qualified paid lead exposes a real missing proof.

## Truth boundary

Do not claim Draco/meshopt/KTX2, React Three Fiber integration, client-specific product expertise, a promised payload ceiling, or production compliance with a buyer's triangle/texture budget until those are actually demonstrated.
