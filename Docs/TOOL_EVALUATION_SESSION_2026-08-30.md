# Melodia Melusina — Production Tool Evaluation Session

**Date:** 2026-08-30
**Status:** Active testing plan
**Goal:** Test newly released or substantially improved tools against real Melodia production problems. Do not adopt tools because they are novel; adopt only when they reduce iteration time, improve quality, or unlock a workflow we can actually ship.

## Morning priorities

### P0 — Cascadeur 2026.2

Evaluate Cascadeur as a non-destructive character-animation and motion-polish layer feeding Unreal Engine 5.8.

Test:
- Install/update Cascadeur 2026.2 and confirm UE 5.8 Live Link/export path.
- Import one representative Melodia character/rig rather than building a throwaway test.
- Test AutoPosing / physics-assisted posing on an exaggerated traversal or reaction pose.
- Test Animation Layers for non-destructive secondary motion and corrections.
- Test interpolation/easing controls on a short gameplay-quality clip.
- Round-trip the result into UE 5.8 and inspect skeleton compatibility, root motion, timing, foot contact, scale, retargeting, and visible degradation.
- Time the workflow against doing the same polish conventionally.

Melodia-specific experiments:
1. Flow-reactive stumble/recovery or landing animation.
2. Cloth/fashion-oriented character turn with exaggerated readable silhouette.
3. A short traversal animation that could later be parameterized by rhythm/convergence state.

**Pass condition:** demonstrably faster animation blocking/polish with a clean UE round trip.
**Adopt if:** it can become a reliable polish/variation stage without creating another fragile asset pipeline.

### P0 — Blender MIDI / music-driven procedural workflow

Investigate the new/current Blender MIDI workflow and determine whether it materially improves the existing Melodia MIDI-to-runtime-geometry concept.

Do not stop at a visualizer. Test MIDI as structured worldbuilding data.

Test MIDI-derived channels for:
- note -> geometry instance / spawn event
- velocity -> scale, displacement, emission, force, or intensity
- pitch -> height, species/type selection, hue/material parameter, or spatial band
- duration -> lifetime, growth, trail length, or deformation
- track/channel -> biome/system layer
- tempo/beat -> simulation clock or procedural pulse

Build one compact Geometry Nodes prototype where a MIDI phrase generates a readable environment response. Favor a Melodia-like test: flowers, reeds, shells, water rings, ribbons, stars, architecture fragments, or terrain accents instead of piano-key visualization.

Then answer:
- Can the result be baked/exported cleanly?
- Can attributes survive into Houdini or Unreal?
- Is Blender best used as authoring/previsualization while UE remains runtime authority?
- Does this replace any existing custom MIDI tooling, or complement it?
- Can MIDI become a reusable procedural art-control format across Blender + Houdini + UE?

**Pass condition:** MIDI becomes useful structured art/world data, not merely synchronized animation.

## P1 — USD Portal

After the two P0 tests, benchmark USD Portal on a small real asset chain:

`ZBrush / Blender -> USD Portal -> Houdini -> Blender -> Unreal`

Check geometry hierarchy, UVs, vertex colors/polypaint, scale, naming, visibility, material/texture references, and iteration speed. Compare with the current manual export path.

**Pass condition:** fewer repetitive export/import steps without corrupting authored data.

## P1 — IlluGen 1.2

Run one effects-texture experiment using the new Accumulate workflow. Candidate: persistent wake/residue mask from animated water/rhythm motion. Export a small texture sequence/atlas and test it in a UE material or Niagara context.

**Pass condition:** faster creation of production-usable procedural masks/flipbooks than the current route.

## P1 — SideFX Labs GSplat tools

Test only if time remains. Use Relight / Normals / Delight GSplats on one capture or representative splat dataset. The production question is whether captured environmental information can become editable Melodia source data rather than remaining a camera-dependent splat.

Potential pipeline:

`capture -> GSplat -> delight/normal reconstruction -> Houdini processing -> authored geometry/material/terrain reference -> UE`

## P2 — Unreal agent tooling benchmark

Do not destabilize the project today. Evaluate Rekall UE only in an isolated test context and compare its useful editor operations against Epic/native MCP and the existing Rider + Junie workflow.

Score specifically on repetitive worldbuilding operations: material creation, foliage/biome editing, level operations, Blueprint scaffolding, Sequencer operations, and batch asset changes.

No production adoption until reliability and source-control behavior are understood.

## P2 — Research/reference only

- Autodesk open-source Golaem Houdini/Unreal/USD bridges: study architecture for procedural cache streaming and USD interoperability; no dependency adoption yet.
- WorldClaw and similar agentic world-generation research: watch for structured/editable procedural representations. Do not integrate research prototypes into production.

## Integration target

The important architectural experiment is whether these tools can strengthen one coherent Melodia authoring loop:

`MIDI / musical intent`
`        |`
`        v`
`Blender Geometry Nodes <-> Houdini procedural systems`
`        |                       |`
`        +---------- USD --------+`
`                    |`
`                    v`
`             Unreal Engine 5.8`
`                    |`
`          convergence/runtime state`

Cascadeur sits beside this graph as the character-motion authoring/polish lane feeding Unreal.

The goal is not more software. The goal is to discover whether music can become a shared procedural control language for geometry, environments, animation, VFX, and eventually runtime convergence behavior.

## Session order

1. **Cascadeur 2026.2** — 60–90 min focused test.
2. **Blender MIDI** — 90–120 min; produce one actual Melodia procedural scene experiment.
3. **USD Portal** — 30–45 min round-trip benchmark.
4. **IlluGen 1.2** — 30–45 min effects texture test.
5. **SideFX GSplat** — optional if a useful dataset is ready.
6. **Rekall / Golaem / WorldClaw** — research lane only after production tests.

## Capture results

For every test record:

| Tool | Setup min | Useful output min | UE round-trip | Quality gain | Iteration gain | Stability | Decision |
|---|---:|---:|---|---|---|---|---|
| Cascadeur 2026.2 | | | | | | | |
| Blender MIDI | | | | | | | |
| USD Portal | | | | | | | |
| IlluGen 1.2 | | | | | | | |
| SideFX GSplat | | | | | | | |

Decision values: **ADOPT / KEEP TESTING / REFERENCE ONLY / DROP**.

## End-of-session deliverable

Before adding another tool, produce:
- one Cascadeur -> UE proof,
- one MIDI -> procedural-world proof,
- screenshots/video where useful,
- measured friction/setup notes,
- explicit adoption decisions,
- follow-up implementation tasks only for tools that pass.

If the Blender MIDI experiment works, the next engineering task is to define a small canonical `MusicalEvent` representation that can map MIDI-derived intent consistently across Blender, Houdini, and Unreal rather than maintaining three unrelated music-reactive systems.
