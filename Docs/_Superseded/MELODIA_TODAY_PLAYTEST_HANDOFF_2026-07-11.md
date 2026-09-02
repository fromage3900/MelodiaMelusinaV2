# Melodia Today Playtest Handoff - 2026-07-11

Audience: human playtest, Claude editor lane, and Codex no-editor lane.

## Current Proof

- `ZenForestTest` verifier reports `ok=true` with `BP_Melusina`,
  `BP_MelodiaGameMode`, PlayerStart, and a fully composed encounter trigger.
- The prior combat coherence commit compiled and passed 10/10
  `Melodia.CoreRules` tests.
- GMM remains 240/240 green and its deterministic gameplay smoke is green.

## Build Note Before Testing

An uncommitted parity cleanup is ready but needs one clean editor-free rebuild:

- C++ toughness now applies the generated 40 percent reduction.
- Perfect skill rewards apply once per execution, matching GMM.
- Tidal Mend heals from damage dealt, matching GMM.

Do not judge break pacing, Perfect rewards, Tidal Mend balance, or command
clarity until this patch is linked and the CoreRules suite is rerun.

## Feedback Polish Pending Rebuild

The next native HUD pass deliberately reuses the existing rhythm HUD rather
than introducing a new widget or asset dependency:

- The command prompt names the currently selected Skill and its SP cost.
- Cycling a Skill immediately confirms the new selection in the HUD.
- A Perfect triggers the existing sparkle event in addition to its grade text,
  sound, and pulse.
- A toughness break gets an explicit `BREAK!` banner, floating result, and
  sparkle event before the normal damage result.

This is the slice's high-contrast, decisive feedback layer. It is not a claim
of final UI art. During playtest, record whether these events are readable at
normal movement distance and whether they hide a result too quickly.

## Playtest Order

1. Boot `ZenForestTest`; verify BP_Melusina moves, turns, and visibly leaves
   idle when using WASD.
2. Enter `MelodiaSmoke_Encounter_01`; record whether the encounter is legible
   before overlap.
3. Basic: miss once, then hit a stronger timing grade. Confirm rhythm starts,
   resolves, deals ordered damage, and returns to a usable command state.
4. Cycle Skill: confirm its displayed name and SP cost update before execution.
5. Skill: confirm SP changes only after rhythm resolution.
6. Perfect: confirm the grade text, pulse, sound, and sparkle read as one
   clear event, not four unrelated effects.
7. Break: confirm the `BREAK!` beat precedes the damage result; record enemy
   HP/toughness and party HP before/after the break.
8. Victory: confirm the HUD clears, input returns, and exploration continues.

## Evidence-Backed Risks

| Priority | Finding | Owner / action |
| --- | --- | --- |
| P0 | The latest locomotion report still records invalid legacy `A_ThirdPerson*` skeletons and zero automatically added BlendSpace samples. | Verify the current retargeted BP/AnimBP live in PIE; update the report only after it is visibly confirmed. |
| P0 | Runtime BGM searches `/Game/Audio/BGM/BGM_<EnemyId>`, but no matching BGM assets were found in Content. | Either import/map one shared encounter cue or accept grade tones/metronome as the slice's current audio baseline. |
| P1 | Global fallback GameMode remains `MelodiaMobileGameMode`, although ZenForestTest has the correct map-level BP GameMode override. | Before Windows packaging is frozen, make the package GameMode choice explicit. |
| P1 | Enemy data supports meshes/materials, but the first three teaching encounters need a distinct, readable visual silhouette. | Use existing world assets for now; do not block gameplay on bespoke enemy art. |
| P1 | The encounter currently has no mapped BGM asset; grade tones and metronome are the available combat audio baseline. | Map one shared combat loop before capture. Do not wait for enemy-specific music. |
| P1 | Native feedback polish is source-ready but has not been rebuilt against the currently open editor. | On editor release, perform a full build and CoreRules run before judging it in PIE. |
| Out of scope | `WBP_Battle_Mobile` does not exist. | Keep mobile out of this release claim. |

## Do Not Expand Today

- No selectable classes, equipment screen, inventory loop, or mobile port work.
- No new combat mechanics before the core loop survives a complete human run.
- No PCG or shader changes unless they directly prevent player visibility or
  encounter readability.

## Bug Capture Format

For each issue record: map, command, timing grade, enemy HP/toughness, party
HP, SP, Ultimate, visible symptom, and whether input recovered. A screenshot
or 10-second capture is enough for presentation/animation failures.
