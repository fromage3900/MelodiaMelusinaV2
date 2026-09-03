# Gameplay BP to Native Surface Audit

**Date:** 2026-08-14  
**Purpose:** verify that the planned Melodia gameplay BP kit maps to real native
authorities before editor materialization.

## Current asset fact

The planned canonical gameplay BP assets are not present on disk yet:

- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaSkill_Base`
- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaTraversalGate_Base`
- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaEnemy_Base`
- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaEncounter_Base`
- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaPortal_Base`
- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaWorldChallenge_Base`
- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaStateAnchor_Base`

The registry and fixture specs are therefore planning/contract evidence, not live BP
readiness evidence.

## Native surfaces confirmed in source

| Content surface | Native authority | Evidence | BP implication |
| --- | --- | --- | --- |
| Skill | `UMelodiaRhythmSkillDefinition` | `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmSkillDefinition.h` | This is a final `UPrimaryDataAsset`, not a Blueprint parent. Author a definition DataAsset plus a thin stock skill presentation child; the BP must request stock execution. |
| Traversal | `UMelodiaTraversalComponent` | `Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.h` | The component now declares a narrow Blueprint request/result API for Grounded and Glide plus a module-neutral capability-provider gate. Source implementation is present; clean-editor compile, live reflection, runtime, and PIE evidence remain open. Sprint, swim, and dive remain native/input-only. The gate must still route all movement through this component. |
| Enemy | `AMelodiaEnemyBase` | `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEnemyBase.h` | Child BP supplies its skeletal presentation and montages; stock enemy presentation callbacks remain native. |
| Encounter | `AMelodiaEncounterTrigger` | `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEncounterTrigger.h` | Child/adapter binds identity, presentation, stock battle preference, and reset policy; no custom battle authority. |
| Portal | `AMelodiaTravelInteractionPortal` | `Source/BS_GodFile/MelodiaIntegration/MelodiaTravelInteractionPortal.h` | Reuse the existing travel interaction route and destination spawn tag; do not introduce direct `OpenLevel`. |
| Narrative | `UMelodiaNarrativeSubsystem` | `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.h` | World challenges and state anchors write/read through the canonical narrative seam; IDs are allowlisted in `UMelodiaIntegrationConfig`. Generic StateAnchor BPs use `AActor`, not the opening-specific anchor. |
| Party | `UMelodiaPartySubsystem` | `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaPartySubsystem.h` | Party changes remain transaction/intention driven. |
| Travel | `UMelodiaTravelSubsystem` | `Source/BS_GodFile/MelodiaIntegration/MelodiaTravelSubsystem.h` | Destination and arrival are subsystem-owned. |

## Ordering decision

The source audit confirms that the two first fixture specs are pointed at real native
surfaces. The TraversalGate now has a narrow native request seam for Grounded/Glide,
but the source must compile and receive live Blueprint evidence before promotion.
The encounter and portal shells are now Blueprint-extensible at source level; clean
compile and live parent reflection are still pending because the editor is currently
blocked in Turnkey SDK detection. After a usable editor session returns, materialize
only these first:

1. `DA_MelodiaSkill_FirstResonance` as a `UMelodiaRhythmSkillDefinition` DataAsset,
   then the stock `BP_MelodiaSkill_Base` presentation child only after the definition
   bridge/cooldown gate is closed.
2. `BP_MelodiaTraversalGate_HoverFixture` from `AActor` with the gate contract bound
   to `UMelodiaTraversalComponent`.

The request and provider seam is recorded in
`specs/traversal/melodia_traversal_capability.v1.json`. Its current status is
`source_wired_closed_editor_build_pending`; the offline validator checks the declared
methods, supported modes, provider boundary, and source markers. Live reflection,
runtime, and reset evidence remain open.

The Skill seam is recorded in `specs/skills/melodia_skill_execution.v1.json`. The
native audit confirms `SPCost`, target, effect, rhythm, and stock-session paths, but
the current definition path is split: `UMelodiaBattleSession` reads
`UMelodiaSongSkillLibrary`, while `UMelodiaRhythmCombatSubsystem` reads
`UMelodiaRhythmSkillDefinition`. The two schemas also do not have a lossless field
mapping: rhythm definitions expose pattern assets, effect families, grade multipliers,
and target rules, while stock recipes require note arrays, instrument, element,
materials, and power scalar. There is no current native cooldown authority or
request-id journal. The first Skill fixture therefore remains L1 and must not be
promoted until a reviewed bridge selects one definition and resource authority and the
failure/idempotency semantics are owned by the battle runtime. Do not implement a
guessed cache adapter.

Then compile/export/fixture-test them before creating the Enemy, Encounter, Portal,
WorldChallenge, and StateAnchor children. The registry now records the exact
artifact model, native parent, and blocker list for each template. This ordering is
consistent with the shared contract and prevents seven empty or authority-ambiguous
assets from being created at once.

## Evidence boundary

This audit proves native class availability and exposes the missing asset paths. It does
not prove Blueprint creation, parent assignment, graph correctness, map reachability,
PIE behavior, save/reset behavior, or task-ledger completion.
