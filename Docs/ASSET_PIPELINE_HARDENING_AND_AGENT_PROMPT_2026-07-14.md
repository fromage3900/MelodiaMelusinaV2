# Asset Pipeline Hardening and Agent Prompt - 2026-07-14

> **Authority amendment (2026-07-26).** Asset-pipeline practices remain useful,
> but statements below naming MelodiaCore as runtime/gameplay authority are
> superseded. The complete TurnBased JRPG template is the provisional
> mechanical authority; MelodiaCore is quarantined for selective salvage. See
> `MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`.

**Purpose:** Lock in the long-term production lens for Melodia/EnvironmentPortfolio: prevent pipeline drift, make asset creation faster, and give agents a shared execution prompt for NPCs, environments, gameplay assets, materials, and validation.

This complements the runtime review in `Docs/MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md`. That document covers immediate MelodiaCore gameplay correctness. This document covers the production machine that creates, validates, and keeps assets usable.

## Long-Term Faults That Can Break The Pipeline

### 1. Dual Runtime Truth

Gameplay truth must not silently split between `MelodiaCore`, `Content/Python/gmm`, Blueprint scaffolds, and docs.

Watch for:

- Balance changes made only in GMM.
- Blueprint-only behavior that bypasses MelodiaCore.
- C++ tests green while simulator behavior has drifted.
- Docs saying a rule exists without generated C++/Python parity.

Rule:

- `MelodiaCore` is runtime authority.
- GMM is authoring, simulation, and parity evidence.
- Generated rule outputs must be regenerated and verified together.

### 2. Generated Assets Without Regeneration Contracts

Generated artifacts become dangerous when people hand-edit them or cannot reproduce them.

Watch for:

- PCG graphs with no source script listed.
- `MelodiaRulesGenerated.h` or `rules_generated.py` edited directly.
- NPC data assets created manually without source manifests.
- Room maps or data assets whose generator command is unknown.

Rule:

Every generated asset family needs:

- Source-of-truth file.
- Generator command.
- Output paths.
- Validation command.
- Last verified date.

### 3. Editor-Only Success

Systems that only work after Live Coding, editor Python, warmed asset registry state, or a specific open editor session are not production-safe.

Watch for:

- Success only in PIE, not after editor restart.
- Automation requiring Python editor modules for shipping gameplay.
- C++ changes that need Live Coding patches after every launch.
- Packaged Development build never tested.

Rule:

For gameplay-critical systems, require both:

- C++ automation or no-editor validation.
- PIE or packaged Development smoke for the actual loop.

### 4. Stale Docs Outliving Code

The project has strong docs, but older docs can become traps.

Watch for:

- "MelodiaCore disabled" notes after the plugin is enabled.
- Old gap inventories listing work that has since shipped.
- Commit notes that do not point to the current SSOT.

Rule:

- Every active system gets one current SSOT doc.
- Older docs remain historical evidence, not task authority.
- `NEXT_ACTIONS.md` and `NEXT_HIGHEST_LEVERAGE_TASK.md` must point to the current SSOT.

### 5. Master Material and Style Sprawl

New masters and style variants are cheap to create and expensive to maintain.

Watch for:

- New material masters for one-off looks.
- Character/environment/VFX assets with unclear parent lanes.
- Texture refs fixed in one instance but not the family.
- Captures that look good but cannot be reproduced.

Rule:

New assets choose a blessed lane:

- Character toon.
- Environment toon.
- Water.
- VFX/emissive.
- UI.

Exceptions need an explicit note and validation capture.

### 6. Procedural Spaces Without Playability Metadata

Instance counts are not enough. A player needs readable spaces.

Watch for:

- PCG output with no role tags.
- Walkable and decorative geometry using the same mesh/material.
- Missing entrance/exit anchors.
- Room variants with no encounter sockets, NPC sockets, or safe spawn.
- Environments that pass generation but fail navigation/readability.

Rule:

Environment recipes need playability metadata:

- `walkable`
- `wall`
- `dressing`
- `landmark`
- `hazard`
- `reward`
- `entrance`
- `exit`
- `encounter_socket`
- `npc_socket`

### 7. NPC Pipeline Split Across Look, Data, and Gameplay

NPCs fail when visual identity, dialogue, battle mapping, rig state, and interaction setup are produced separately.

Watch for:

- Imported meshes with no `NPCId`.
- NPC data with no placed interaction actor.
- Dialogue-only NPCs with no battle/progression mapping when the design expects one.
- Generated NPC battle enemies not validated against native `FMelodiaEnemyDef`.

Rule:

Every NPC ships with one manifest row that binds visual, interaction, dialogue, battle reference, and validation evidence.

### 8. Manual Acceptance Paths

If proving a feature requires remembering a long set of steps, it will rot.

Watch for:

- "Test in PIE" without a checklist.
- No saved evidence artifact.
- No known failure mode list.
- No deterministic seed or room ID logged.

Rule:

Every major asset family needs:

- One smoke command or checklist.
- One validation artifact.
- One preview scene or lineup.

## AssetPassport Contract

Create one lightweight asset passport for every production-facing asset. This can begin as JSON or Markdown; it does not need a large tool before it becomes useful.

```json
{
  "id": "stable_asset_id",
  "type": "npc | room | prop | enemy | skill | material | vfx | ui",
  "status": "draft | generated | validated | shipped | deprecated",
  "owner_lane": "MelodiaCore | GMM | PCG | NPC | Materials | UI | Site",
  "source_of_truth": "path/to/source",
  "generator_command": "command or manual source note",
  "generated_outputs": ["path/or/asset"],
  "runtime_refs": ["class/data/blueprint IDs used by gameplay"],
  "preview_scene": "map/blend/lineup/capture path",
  "validation_command": "command/checklist",
  "last_verified_date": "YYYY-MM-DD",
  "known_risks": ["short risk notes"]
}
```

Minimum viable version:

- Do not block content creation on perfect schema tooling.
- Start with a folder of passport JSON/MD files or a single registry table.
- The first win is consistency, not automation grandeur.

## Streamlined Asset Creation Lanes

### NPC Lane

Required passport fields:

- `npc_id`
- archetype
- visual source
- skeletal mesh
- material profile
- animation/idle set
- dialogue set
- interaction type
- battle enemy ID, if applicable
- spawn tags
- validation evidence

Validation:

- Mesh exists.
- Materials compile.
- Skeleton/animation compatible.
- Dialogue is nonempty.
- Interaction prompt exists.
- Battle enemy ID maps to native enemy definitions when set.
- One lineup/preview level shows the NPC with label and prompt.

Recommended MVP:

1. Pick one stationary dialogue NPC.
2. Create/update passport.
3. Generate or configure native NPC definition.
4. Place in preview/vertical-slice map.
5. Validate prompt, dialogue, return to exploration, and optional battle handoff.

### Environment / Room Lane

Required passport fields:

- `room_id`
- map/level
- biome/style genome
- allowed floor/stage range
- entrance anchors
- exit anchors
- encounter sockets
- NPC sockets
- reward sockets
- PCG style graph
- lighting profile
- music/profile ID
- validation evidence

Validation:

- Level/map exists and loads.
- Entrance and exit anchors exist.
- Encounter metadata is valid or explicitly absent.
- PCG instance counts are inside declared range.
- Role tags cover walkable, wall, dressing, landmark, entrance, and exit.
- Room is readable from player height.

Recommended MVP:

1. Author one room recipe.
2. Generate/load it with deterministic seed.
3. Validate role coverage and anchors.
4. Place one encounter or NPC socket.
5. Save one preview capture.

### Gameplay Asset Lane

Applies to skills, enemies, afflictions, modifiers, rewards, and run artifacts.

Required passport fields:

- stable ID
- rules source
- generated outputs
- runtime consumer
- simulator parity note
- automation test name

Validation:

- Rules regenerate to C++ and Python.
- Runtime consumer uses generated values.
- C++ automation covers runtime path.
- GMM parity test covers simulation path.
- No direct edit to generated files.

### Material / VFX Lane

Required passport fields:

- material or system ID
- blessed parent/lane
- texture set
- key parameters
- target asset/use case
- preview capture
- compile status

Validation:

- Parent is one of the blessed lanes or exception is documented.
- Material compiles.
- Texture refs are valid.
- Preview capture exists.
- Asset usage is listed.

## Validator Roadmap

Start tiny and composable:

1. `validate_asset_passports`: required fields, paths exist, current SSOT links.
2. `validate_npc_passports`: NPC IDs, mesh/material refs, dialogue, battle enemy refs.
3. `validate_room_passports`: map refs, anchors, sockets, PCG role coverage.
4. `validate_gameplay_passports`: generated rules, C++/Python parity, automation names.
5. `validate_material_passports`: parent lanes, texture refs, compile/capture evidence.

Each validator should output:

- JSON report under `Saved/Audit/`.
- Human summary.
- Clear pass/fail count.

## Agent Execution Prompt

Copy this prompt into the next agent/task that will execute the pipeline-hardening work:

```text
You are working in C:\EnvironmentPortfolio\BS_GodFile. Your goal is to harden the long-term asset pipeline and streamline asset creation for NPCs, environments, gameplay assets, and materials.

Read these first:
- Docs/ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md
- Docs/MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md
- NEXT_ACTIONS.md
- NEXT_HIGHEST_LEVERAGE_TASK.md

Rules:
- Do not treat Content/Python/gmm as runtime authority. GMM is authoring/simulation/parity evidence; MelodiaCore is runtime authority.
- Do not hand-edit generated artifacts such as MelodiaRulesGenerated.h or generated PCG outputs unless the task explicitly says to repair generated output metadata. Prefer source-of-truth + generator + validation.
- Keep changes small, testable, and documented.
- Do not modify user-authored Content assets or maps unless explicitly requested. Prefer docs, schemas, validators, and small runtime/source changes with clear acceptance gates.
- Every new asset family must answer: source of truth, generator command, generated outputs, runtime refs, preview scene, validation command, and last verified date.

Immediate execution goals:
1. Create the first minimal AssetPassport registry or schema for production assets.
2. Seed example passports for one NPC, one room/environment, one gameplay rule asset, and one material/VFX asset using existing project assets.
3. Add or specify a validator that checks required fields and path/reference existence without mutating Unreal assets.
4. Update NEXT_ACTIONS.md with the exact command/checklist for running the validator.
5. Keep MelodiaCore gameplay correctness tasks from the deep review as the runtime priority: modifier stack math, permanent modifier duration, AV turn authority, ultimate interrupt semantics, roguelike phase ordering, and reward-to-next-stage proof.

Acceptance criteria:
- A human can open the passport registry and understand where each example asset comes from, what it generates, what runtime uses it, and how to validate it.
- The validator/checklist has a deterministic output location under Saved/Audit/ or a clear manual evidence path.
- No generated file is edited by hand.
- NEXT_ACTIONS.md and NEXT_HIGHEST_LEVERAGE_TASK.md continue to point at the current SSOT docs.
```

## Current Highest-Leverage Production Move

Do not start by building a giant asset manager. Start with a minimal passport registry and a validator for required fields. Once the first NPC, room, gameplay asset, and material can be traced end to end, scale the same pattern across the project.
