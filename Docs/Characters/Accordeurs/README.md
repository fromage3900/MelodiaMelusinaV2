# Les Petits Accordeurs — Character Foundry

**Status:** concept-art authority verified; production prototypes PLANNED. **This branch does not contain accepted meshes or implemented gameplay.**  
**Owner:** Melodia Melusina / character & world team.  
**Created:** 2026-10-11.  
**Branch:** feature/les-petits-accordeurs-foundry-20261011.

## Purpose
Preserve the seven tiny watercolor/ink repair spirits without reinterpreting them as generic photorealistic furry fantasy creatures. Converge lore, individual character bibles, one representative mesh/rig, environmental interaction, and Maison L'Accordeur into a bounded production lane.

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
3. [TRIPO_TO_UE58_MESH_PIPELINE.md](TRIPO_TO_UE58_MESH_PIPELINE.md) — seed base meshes, controlled import and acceptance.
4. [accordeurs_manifest.json](accordeurs_manifest.json) — stable IDs and authoring status.

## Non-negotiable implementation boundaries
- **Do not edit active Melusina AnimBP, skeleton, wardrobe, level maps, or ongoing VFX work.**
- No new narrative or save authority. Use the repository's QuillScript/narrative and JRPG/persistence ownership once the integration owner confirms exact interfaces.
- No new live runtime system until a small isolated playtest passes and the owner approves.
- Prefer reproducible, import-only source from Tripo; do not commit uncontrolled generated GLBs to metered Git LFS. Inventory and budget check first.
- A branch/plan is not proof of mesh generation, rigging, Unreal import, or playable runtime.

## First bounded milestone
1. Make a clean single-subject crop of **Le Build**, **Mlle. Merge**, **Petit Cache** from the approved lineup; keep full sheets alongside them for validation.
2. Generate one test base mesh (Le Build), inspect front/side/back against sheet, repair topology/geometry, define an optional shared small-spirit deform skeleton.
3. Accept/reject that mesh with screenshot-based silhouette/material/UV evidence; only then process Mlle. Merge and Petit Cache.
4. In UE 5.8, import into an isolated test asset folder and prove one cosmetic idle plus one interaction without changes to authority systems.
5. Hold gameplay design proposals behind their acceptance gates; no branch merge before owner visual review.
