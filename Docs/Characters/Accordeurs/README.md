# Les Petits Accordeurs — Character Foundry

**Status:** concept-art authority verified; production prototypes PLANNED. **This branch does not contain accepted meshes or implemented gameplay.**  
**Owner:** Melodia Melusina / character & world team.  
**Created:** 2026-10-11.  
**Branch:** feature/les-petits-accordeurs-foundry-20261011.

## Purpose
Preserve the seven tiny watercolor/ink repair spirits without reinterpreting them as generic photorealistic furry fantasy creatures. Converge lore, individual character bibles, a **procedural Geometry Nodes character family**, later rigging, and Maison L'Accordeur into a bounded production lane. **Blender Melodia Studio GN geometry is the production authority; Tripo is optional shape exploration only.**

## Visual authority / explicit rejection
**APPROVED SOURCE OF TRUTH (provided by owner):**
1. Les Petits Accordeurs Character Lineup.jpeg — seven original watercolor/ink characters, simple readable silhouettes and colors.
2. Les Petits Accordeurs Concept Sheet.jpeg — names, roles, heights, props, expressions, actions, outfit variants, materials, lore.
These image references were supplied in chat and are **not** committed here. When exporting approved assets, place references in a controlled local art-source folder and record provenance before adding binaries.

**REJECTED:** 'Les Petits Accordeurs Atelier Magique.png' — over-rendered cinematic furry/goblin reinterpretation. Never use as a character shape, texture or material reference.

## Original named cast
- Monsieur Committe — Archivist.
- Mlle. Merge — Seamstress of Realities.
- Petit Cache — Keeper of What Might Be.
- Le Build — Foreman.
- Madame L.F.S. — Quartermaster.
- Monsieur Rebase — Cartographer.
- Le Bot — Errand-Runner.

Size reference: roughly 15–25 cm against Melusina approximately 160 cm (as labeled on concept sheet).
Mottos: "Small hands. Better worlds.", "Keep things in tune.", "Different tasks. Same song."

## Read in order
1. [CANON_LORE_AND_CHARACTER_BIBLE.md](CANON_LORE_AND_CHARACTER_BIBLE.md) — established details separated from pitches.
2. [GAMEPLAY_AND_MAISON_DESIGN.md](GAMEPLAY_AND_MAISON_DESIGN.md) — data-driven proposal, scoped to existing authorities.
3. [STEPFUN_GN_HANDOFF.md](STEPFUN_GN_HANDOFF.md) — **primary StepFun execution contract**, using existing Melodia Studio GN registry.
4. [TRIPO_TO_UE58_MESH_PIPELINE.md](TRIPO_TO_UE58_MESH_PIPELINE.md) — optional reference mesh exploration, not canonical geometry.
5. [accordeurs_manifest.json](accordeurs_manifest.json) — stable IDs and authoring status.

## Non-negotiable implementation boundaries
- **Do not edit active Melusina AnimBP, skeleton, wardrobe, level maps, or ongoing VFX work.**
- No new narrative or save authority. Use the repository's QuillScript/narrative and JRPG/persistence ownership once the integration owner confirms exact interfaces.
- No new live runtime system until a small isolated playtest passes and the owner approves.
- **Make original editable, seeded Geometry Nodes builders in the EXISTING Melodia Studio add-on.** Tripo images or GLBs can inform proportions but must not become the mandatory mesh-authoring route. Avoid uncontrolled GLB/LFS payloads.
- A branch/plan is not proof of mesh generation, rigging, Unreal import, or playable runtime.

## First bounded milestone
1. Use the individual approved crops of **Le Build**, **Mlle. Merge**, **Petit Cache** solely as references, with full concept sheet for cross-checks.
2. Audit current `deploy/surreal_arch/melodia_gn` registry, Melodia Studio GN Stack, Blender 5.2 verification and presets; DO NOT make a parallel implementation.
3. Build one seed-driven procedural Le Build silhouette with independent, tweakable body/face/ear and accessory modules; capture same-scale orthographic views.
4. Prove the SAME reusable GN family can generate visually distinct Mlle. Merge and Petit Cache presets; do not fake this with colors alone.
5. Owner reviews silhouettes and geometry prior to topology/rigging and any UE sandbox import. Keep gameplay designs proposed until explicit acceptance.
