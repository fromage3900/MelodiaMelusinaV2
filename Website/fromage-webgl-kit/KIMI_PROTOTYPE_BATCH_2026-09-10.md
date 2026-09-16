# Kimi Prototype Batch — 2026-09-10

**Authority:** `LEADS_2026-09-10.md` chooses the market problems; `SERVICES.md` defines what we sell.  
**Execution rule:** build generic proof, not unpaid client deliverables.  
**Destination:** `tools/fromage-webgl-kit/prototypes/` only for new clean-room work. Do not modify deployed recruiter-facing pages unless the owner explicitly promotes a reviewed result later.

## Shared constraints

- Use Three.js/WebGL with clean, readable source.
- Reuse the generic kit primitives under `src/` where they fit; improve them only when a genuinely reusable abstraction falls out of the work.
- Before building something new, audit whether an equivalent capability already exists in `wix/`, `melodia/`, or existing generated/site tooling.
- No Melodia characters, names, logos, music, textures, or proprietary/project-specific assets in commercial clean-room outputs.
- No third-party commercial IP or scraped client assets.
- Procedural geometry, primitive geometry, CC0 assets, or clearly owned generic assets only.
- Mobile-width behavior is mandatory.
- Respect `prefers-reduced-motion` where motion is not functionally required.
- Expose a small performance/debug readout: DPR, approximate FPS, triangles/draw calls if available, and loaded asset bytes when practical.
- Fail gracefully when WebGL or an asset is unavailable.
- No backend, accounts, ecommerce, CMS, analytics, payment, or external API scope.
- Do not redesign the public portfolio or auto-deploy anything.
- Finish each lane with a short `EVIDENCE.md`: what works, what was measured, what remains unverified, and exactly which reusable primitive was created, extracted, or improved.

---

# Prototype A — Web Product Motion Lab

**Market proof target:** real-time product animation, product viewer/configurator, scroll-scrubbed GLB delivery.

**Existing destination:** `tools/fromage-webgl-kit/prototypes/product-motion-lab/`

## Goal

Turn the already-seeded product-motion source into a premium but neutral browser demonstration showing that a web-ready 3D product can be loaded, presented, annotated and scrubbed through a deterministic product-use animation without video.

## Required experience

1. A generic handheld-device-like object built from owned/procedural geometry or an original simple GLB.
2. Neutral studio presentation with physically plausible PBR response.
3. A timeline scrubber and scroll-linked scrub mode.
4. At least three deterministic named animation phases: `intro`, `use`, `idle`.
5. At least three named annotation anchors that remain attached to the correct moving component.
6. Toggleable callouts anchored to those points.
7. A compact diagnostics panel showing approximate triangles, draw calls, DPR/FPS and asset size if measurable.
8. Responsive desktop and phone-width layout.
9. One visual QA mode showing wireframe or normal/material inspection.

## Architecture preference

Keep animation scrub-safe: the same normalized timeline value must always yield the same visual pose. Avoid time-integrated behavior for the core product motion.

If a GLB is generated outside the browser, keep the source asset and document the export settings. If a useful GLB is not immediately available, use original Three.js primitive groups and structure the code as though the root were a product asset; do not block the prototype waiting for DCC work.

## Hard stop

Do **not** build purchasing, quoting, user uploads, CRM integration, or a full configurator.

## Evidence to return

- desktop screenshot/capture;
- phone-width screenshot/capture;
- one complete scrub from 0 → 1 → 0;
- diagnostics values;
- note describing how the same architecture would accept a client GLB.

---

# Prototype B — Existing Fabric Material System Commercialization Pass

**Market proof target:** Three.js technical-art consultancy, PBR fabrics, swatch-to-web material pipelines, knitwear configurators.

**Status:** **EXISTING CAPABILITY — DO NOT REBUILD FROM SCRATCH.**

Existing related surfaces include:

- `wix/realtime-3d-viewer.html` — live Fantasy Fabric Studies selector / interactive asset study;
- `wix/melodia-3d-viewport.js` — fabric sphere, fabric presets, texture/material switching and viewer runtime;
- `wix/melodia-atelier-lab.html` + `wix/melodia-atelier-lab.js` — existing fabric/lookdev turntable integration;
- `wix/sdf-material-gallery.html` — existing controlled Material Atlas presentation.

## Goal

Audit, runtime-verify and **extract only the generic, clearly owned commercializable parts** of the existing fabric/material system. Do not make another parallel material lab simply to satisfy this document.

The desired outcome is either:

1. the existing system is already sufficient proof and receives an evidence/provenance note only; or
2. a small clean-room commercial demo is extracted under `tools/fromage-webgl-kit/prototypes/fabric-material-lab/` containing only the reusable pieces we actually need for client work.

## Required pass

1. Run and inspect the existing fabric sphere / preset workflow before writing replacement code.
2. Inventory existing preset/material/texture provenance and identify what is safely owner-authored/generic versus Melodia-specific, third-party, uncertain, or unsuitable for resale/client reuse.
3. Reuse existing generic architecture for material switching, cameras, lighting and inspection rather than recreating it.
4. Add only commercially useful proof that is genuinely missing, such as direct base-color / roughness / normal / sheen controls, a state readout, lightweight JSON state export, mobile QA or diagnostics.
5. If a clean-room extraction is necessary, use neutral independently authored preset identities such as velvet-like, satin-like, knit-like and coarse-woven rather than Melodia-specific names or assets.
6. Preserve the deployed portfolio pages unchanged during this pass.

## Hard stops

- **No duplicate fabric lab architecture.**
- Do not copy Melodia-specific textures/assets into the commercial kit merely because they are present in the portfolio repo.
- Do not redistribute third-party or provenance-uncertain textures.
- Do not claim physical colorimetry, measured BRDF accuracy, automatic real-swatch capture, or production swatch digitization unless actually implemented and measured.

## Evidence to return

- short inventory of the existing fabric/material capabilities found;
- what was reused versus newly added;
- provenance/IP classification for anything promoted into the clean-room kit;
- one identical-lighting material comparison capture if safe presets are available;
- one grazing-angle inspection capture;
- example exported state if that feature is added;
- explicit statement if **no new prototype was needed** because existing verified proof was sufficient.

---

# Prototype C — Procedural Industrial System Loop

**Market proof target:** procedural industrial homepage work, procedural Three.js worlds, interactive WebGL hero/banner work.

**Create:** `tools/fromage-webgl-kit/prototypes/procedural-industrial-loop/`

## Goal

Build a completely generic industrial/procedural scene whose motion can obey a strict mechanical design language and whose visualization state can communicate structural, flow and thermal-like information without pretending to be a real engineering solver.

## Required experience

1. Procedurally generated mechanical/architectural geometry using primitives and deterministic seeded parameters.
2. Stable art-directed composition despite seed variation.
3. A 10–16 second loop with a deterministic timeline.
4. `MECHANICAL` motion mode: one axis at a time, constant-speed segments, hard stops, no bounce/overshoot/anticipation/easing.
5. Three clearly labelled **visualization styles**, not simulations: `STRUCTURAL`, `FLOW`, `THERMAL`.
6. Visualization color only where it encodes state; keep base scene restrained/neutral.
7. Seed control with at least three visibly different but compositionally valid variations.
8. One optional displacement/shader transition that can be disabled; it must not compromise the mechanical motion proof.
9. Diagnostics/performance overlay.
10. Responsive desktop and phone-width fallback.

## Important language rule

Do not label generated fields as real FEA/CFD/thermal simulation. They are illustrative visualization styles designed to prove rendering, motion-law and procedural-composition capability.

## Hard stop

No CAD parser, no physics solver, no real engineering analysis, no multi-kilometre world, no terrain ecosystem.

## Evidence to return

- one complete mechanical loop capture;
- stills of all three visualization styles;
- stills of three seeds;
- diagnostics snapshot;
- concise explanation of deterministic motion/timeline implementation.

---

# Completion order

Kimi should execute **A first**. After A reaches its evidence gate:

1. audit B as an **existing-system reuse/commercialization pass**, not a new build;
2. only create a clean-room B extraction if the audit proves one is useful;
3. then execute C.

After each lane:

1. run the relevant implementation locally;
2. fix obvious console/runtime errors where in scope;
3. write/update its `EVIDENCE.md`;
4. stop before expanding scope if a clean bounded proof already exists.

Do not merge unrelated portfolio/site changes into this batch.

# Definition of batch success

This batch is successful when we have:

- a reproducible Product Motion proof;
- a verified and provenance-safe Fabric/Material proof, reused from existing work or clean-room extracted only where necessary;
- a reproducible Procedural Industrial proof;
- enough evidence to honestly support proposals for WebGL product, material and procedural work.

The prototypes are evidence generators and reusable kit R&D, not free client work.