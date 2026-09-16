# Afternoon Submission Pack — 2026-09-10

**Target:** prepare three high-fit WebGL/technical-art lanes for human-reviewed submission this afternoon.  
**Source of truth:** this file + each lane's evidence document.  
**Submission rule:** no application leaves `DRAFT` until the listing is still active and all claimed evidence is runtime-verified or genuinely prior owner experience.

## Shared package contract

Each lane should finish with the same small bundle:

```text
01_COVER.png
02_PRIMARY_PROOF.png
03_SECONDARY_PROOF.png
04_MOBILE_PROOF.png
05_EVIDENCE.md
06_APPLICATION_DRAFT.md
07_REQUIREMENT_MAP.md
08_SOURCE_LINKS.txt
```

Optional only when actually useful:

```text
09_VIDEO_PROOF.mp4/webm
10_DCC_SCREENSHOT.png
11_PIPELINE_DIAGRAM.png
```

Do not pad a submission with redundant images. One strong proof per requirement is enough.

---

# LANE A — $3,000 Web-ready Product Animation / GLB

**Owner lane:** Kimi + Brennan visual pass.  
**Current status:** generator / validator / runtime wiring reportedly complete in Kimi workspace; Blender build, GLB export and browser proof remain gated.  
**Canonical warning:** do not mark complete until Kimi's files are actually pushed/merged into the repository and the generated asset has been run locally.

## Submission thesis

`I can prepare real-time product assets for deterministic Three.js presentation: clean hierarchy, web-conscious GLB delivery, scrub-safe motion, parented annotation anchors, and measured runtime validation.`

## Must-have proof before submission

- [ ] Kimi handheld source lands in repository.
- [ ] Blender generation command succeeds.
- [ ] Asset receives Brennan visual/silhouette pass.
- [ ] Validator passes without ignored structural errors.
- [ ] GLB export succeeds.
- [ ] Product Motion Lab loads the GLB.
- [ ] `0 → 1 → 0` scrub produces repeatable pose.
- [ ] 3 callout anchors follow moving components.
- [ ] desktop capture exists.
- [ ] mobile-width capture exists.
- [ ] real triangles / draw calls / DPR / FPS / byte size recorded.
- [ ] listing still active.

## Package order

1. Product hero / viewport image.
2. Web runtime screenshot with callouts.
3. hierarchy / anchor proof or wireframe.
4. measured diagnostics.
5. optional short scrub capture.

## Do not claim unless measured

- Draco / meshopt / KTX2 compression;
- exact client triangle budget compliance;
- React Three Fiber integration;
- production diagnostic-device experience;
- successful web payload target before real export.

## Submission gate

`PROPOSAL READY` when source is canonical, GLB is runtime-verified, evidence images exist, measured values are filled, and the listing remains current.

---

# LANE B — Three.js Fabric Technical-Art Consultant

**Owner lane:** Brennan + existing repository proof; consultant packaging supported by ChatGPT/Kimi.  
**Current status:** source evidence present; application draft present; runtime viewer check, provenance selection and one genuine CLO/Blender artifact remain.

## Submission thesis

`I work across CLO garment preparation, Blender realtime cleanup and Three.js material validation, with an existing browser material-inspection system and a practical approach to separating measured fabric data from artist-authored approximation.`

## Must-have proof before submission

- [ ] runtime-check existing Three.js fabric/material viewer.
- [ ] choose commercial-safe fabric/material evidence.
- [ ] classify selected texture provenance.
- [ ] select or create one genuine CLO artifact/screenshot.
- [ ] if possible, show the same garment or a representative owned garment in Blender.
- [ ] choose one browser material/inspection capture.
- [ ] choose one close-up/grazing-light capture if already available or easy to add.
- [ ] application links point only to evidence Brennan can explain confidently.
- [ ] listing still active.

## Package order

1. CLO garment/source evidence.
2. Blender realtime-prep/topology evidence.
3. Three.js material viewer / material atlas capture.
4. concise pipeline strip: `CLO → Blender → GLB → Three.js validation`.
5. consultant evaluation checklist / short requirement map.

## Minimum viable application

This lane does **not** require the full knitwear configurator before submission. The listing is consulting/strategy, so runtime viewer proof + real CLO/Blender experience + clear pipeline judgment is enough if presented honestly.

## Do not claim

- physical BRDF measurement expertise without proof;
- calibrated colorimetry;
- automatic physical swatch digitization already exists;
- one-click photoreal material generation;
- CLO specialization beyond actual experience shown.

## Submission gate

`PROPOSAL READY` when the existing viewer is runtime-checked, one CLO/Blender artifact is selected, evidence provenance is safe, and the listing remains current.

---

# LANE C — $10,000 Procedural Industrial Homepage Loop

**Owner lane:** Cursor currently owns BASE monochrome polish + capture mode.  
**Current status:** source implemented; deterministic timeline helper extracted; buyer mapping and application draft staged; runtime/capture evidence still required.

## Submission thesis

`I can execute tightly constrained procedural mechanical animation using absolute-time deterministic motion, constant-speed segments, hard stops, seeded systems, and restrained solver-inspired visualization states.`

## Must-have proof before submission

- [ ] Cursor finishes monochrome BASE readability pass.
- [ ] capture mode works without changing the underlying motion law.
- [ ] browser console is clean.
- [ ] Seeds 01/02/03 are visually stable.
- [ ] BASE / STRUCTURAL / FLOW / THERMAL modes work.
- [ ] timeline arbitrary scrubbing shows no transform drift.
- [ ] `0.00s` and `16.00s` are visually identical.
- [ ] `LOOP Δ` reports zero or expected numerical zero within the implementation tolerance.
- [ ] one full 16-second capture exists.
- [ ] desktop/mobile layout evidence exists.
- [ ] real FPS / DPR / triangles / draw calls recorded.
- [ ] listing still active.

## Package order

1. clean BASE monochrome hero capture.
2. motion-law / timeline evidence.
3. STRUCTURAL / FLOW / THERMAL comparison.
4. seed-variation strip.
5. measured diagnostics.
6. optional 16-second loop capture.

## Do not claim unless executed

- client CAD import;
- production ProRes master;
- 2560×1080 final render;
- AV1/VP9 delivery under 5 MB;
- real FEA/CFD/thermal simulation.

## Submission gate

`PROPOSAL READY` when Cursor's visual/capture pass is runtime-verified, the evidence bundle is exported, measured values are inserted, and the listing remains current.

---

# Afternoon triage order

If time gets tight, submit in this order **only when each respective evidence gate is satisfied**:

1. **Fabric Technical-Art Consultant** — smallest remaining proof burden; consulting scope; strong CLO + Blender + Three.js story.
2. **$3,000 Product / GLB** — strongest buyer-fit once the generated asset actually runs.
3. **$10,000 Industrial** — highest upside but requires the strongest capture/evidence quality.

Do not delay a ready consulting application waiting for the other two lanes.

---

# Figma packaging pass

Use `FIGMA_MINIMAL_POLISH_BRIEF.md` only after real captures exist.

Figma's job is:
- normalize hierarchy;
- crop and annotate evidence cleanly;
- create three coherent cover cards;
- create desktop/mobile proof sheets;
- export application-ready PNGs.

Figma's job is **not**:
- invent UI functionality;
- change runtime code;
- manufacture metrics;
- create fake client deliverables;
- hide missing requirements.

---

# Final 15-minute pre-submit check

For each lane:

```text
LISTING STILL OPEN?        YES / NO
MUST-HAVES TRUTHFUL?       YES / NO
LIVE OR CAPTURED PROOF?    YES / NO
MEASURED VALUES FILLED?    YES / NO / N/A
PROVENANCE SAFE?           YES / NO
MISSING REQUIREMENTS SAID? YES / NO
APPLICATION READ ONCE?     YES / NO
HUMAN APPROVES SEND?       YES / NO
```

Any `NO` above blocks submission except `MEASURED VALUES` when genuinely irrelevant to that listing.

## End state for today

The goal is not to finish three giant projects. The goal is to have up to three **small, defensible, buyer-shaped evidence packages** where every visual and every claim can be explained if the client replies immediately.
