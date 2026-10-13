# Grandmaster Houdini Studio — Foundry Day 2026-10-13

**Status:** scaffold code staged; no Houdini cook, GUI acceptance or UE runtime proof claimed.

This is an additive *scene* over the existing [Houdini Studio package](../../deploy/houdini/README.md), [October 7 convergence plan](MELODIA_HOUDINI_STUDIO_CONVERGENCE_2026-10-07.md), and [Foundry Day gates](FoundryDay_2026-09-24/README.md). \`CURRENT_STATE.md\` remains the status authority.

## Why this scene exists

A reusable, artist-friendly HIP for rapidly iterating Melodia environments, not a second World Compiler. The builder inserts a real, existing CrystalCathedralV3 OBJ HDA and lays out annotated world-facing authoring zones. All mission/recipe pointers are **read-only references**, deliberately not fake cooked or linked data.

- Universe Foundry: \`Tools/universe_foundry.py\` deterministically builds the Faraway Mother World Zero mission from the existing genome and **fixture** delta. The fixture must not count as save persistence proof.
- Houdini Foundry: \`Tools/Houdini/foundry/houdini_foundry.py\` validates the Cathedral recipe and preserves existing manifest/hash contract.
- Houdini: \`hda/CrystalCathedralV3.hda\` is an active 18-parameter source, with \`OUT_Cathedral\`, \`OUT_Rose\`, \`OUT_Collision\`, \`OUT_Corridor\`. Existing HDA verification remains authoritative.
- World Compiler: \`Tools/world_compiler.py\` handles \`recipes/kaleido_archipelago.v1.json\` via its existing archipelago stage. **Kaleido is a separate authoring demo**; it is not a Faraway mission task.
- Unreal: only the existing UE PCG/World Compiler driver or explicit Houdini Engine editor cook/bake may author UE content after acquiring the editor lease. Saving and gameplay truth stay in UE.

## Humber workstation quick start (PowerShell, from repo root)

1. Run Git preflight: \`git status --short --branch\`; \`git fetch origin\`. Do not reset, clean or overwrite portable-SSD work. Check out this branch only in a clean dedicated working tree.
2. Activate the existing portable package:

   \`\`\`powershell
   .\deploy\houdini\install_melodia_studio.ps1 -Verify
   \`\`\`

3. Pure-Python path check (safe even without a Houdini licence):

   \`\`\`powershell
   python Tools/Houdini/grandmaster/build_grandmaster_hip.py --check
   \`\`\`

4. In a dedicated **Hython** process, create the starter HIP (the script refuses to clear any interactive GUI HIP):

   \`\`\`powershell
   hython Tools/Houdini/grandmaster/build_grandmaster_hip.py
   \`\`\`

   Output (untracked intentionally):
   \`Saved/HoudiniFoundry/Grandmaster/Melodia_Grandmaster.hip\`
   and \`Melodia_Grandmaster.scaffold.json\`.

   For a clean read-only mission/World Compiler **offline** validation+compile before creation, append \`--refresh-offline\`. This can write generated \`Saved/UniverseFoundry\` and \`Saved/WorldCompiler\` bundles; it never changes Unreal.

5. Open the generated HIP in Houdini's \`Melodia_Studio\` desktop. Confirm V3 asset instantiation, all 18 controls, all four output nodes and a clean cook; capture screenshots. If the HDA definition isn't resolving on a different machine, install \`hda/CrystalCathedralV3.hda\` there rather than silently substituting an HDA.
6. Don't use \`--force\` unless intentionally rebuilding a disposable generated HIP. Save creative work as a **new** scene name; the generator never edits existing authored HIPs.

## Scene lanes

| Scene marker | Intended use | Authority |
| --- | --- | --- |
| \`A0_FOUNDRY_MISSION\` | genome, delta, mission task reference | Universe Foundry CLI |
| \`B0_WORLD_COMPILER\` | recipe/bundle input | World Compiler CLI |
| \`C0_FIELDS_ECOLOGY\` | FieldAtlas, ecology, PCG fields | existing Houdini Foundry + compiler contracts |
| \`C1_CRYSTAL_CATHEDRAL_V3\` | **real instance** of active Cathedral V3 HDA | existing HDA builder + registry |
| \`D0_COPERNICUS_LOOKDEV\` | author fields, materials, resonance previews | Houdini / Copernicus; no new OSC/MPC writer |
| \`E0_BAKE_EVIDENCE\` | receipts and checked output manifests | existing evidence + Foundry validator |

Markers are empty OBJ nulls. They **do not** imply that World Compiler/FieldAtlas/UE are connected at scene runtime.

## One bounded rapid-iteration proof

1. Use the existing V3 canary **without rebuilding the HDA**. Capture its baseline values and output stats (HDA verification supplies the current golden pins).
2. Change *one exposed parameter* (e.g. crystal density or arch span) and inspect the visible authored geometry. Do not move or overwrite Sea Above's owner-authored Cathedral placement.
3. Restore the original value and compare the geometry/bounds and HDA cook evidence. No mass world bake.
4. Independently, validate/compile the existing Kaleido archipelago World Compiler recipe and inspect its real bundle. Do not claim the Cathedral is part of Kaleido or Faraway without a lawful task/recipe seam.
5. Only once read-only evidence is satisfactory, establish a real \`mission_ref\` (\`mission_id\` + \`task_id\`) through the existing **Houdini Foundry bake request** contract for a compatible Faraway task. If no generic Cathedral mission task exists, **record the missing seam**; do not create a fake world genome/task.
6. For genuine UE proof: obtain UE editor lease; consume one bounded, versioned bake via the owning importer or Houdini Engine editor; show bounded change, save/reload, then restore original inputs. Keep fixtures distinct from real game-save-export deltas. Capture an independent reviewer receipt.

**Exit criterion for today's college session:** portable studio opens, HIP generated, V3 controls work, offline mission/World Compiler validates, and there is a captured explicit gap list. UE mutation and full reversible end-to-end bridge remain separate gates until proven.

## Hard boundaries

- No second compiler, world-state writer, Chladni solver, OSC/MPC writer, chord table, or PCG graph authority.
- Keep binaries, HIPs, bgeo, temporary fields and turntables under \`Saved/\` or workstation scratch unless the existing tracked artifact/LFS policy explicitly approves them.
- Do not use the World Zero demo delta as evidence for restart persistence.
- Houdini Engine cook is **editor authoring only**, not an Unreal packaged-runtime dependency.
- Reuse the existing project installer, shelf, desktops, HDA registry and proofs. Do not add a competing \`Melodia_Foundry\` package or replace \`CURRENT_STATE.md\`.
