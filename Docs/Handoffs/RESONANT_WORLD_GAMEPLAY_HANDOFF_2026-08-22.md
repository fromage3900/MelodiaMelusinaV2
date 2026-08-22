# Resonant World Gameplay Handoff — 2026-08-22

## Purpose

Promote one wardrobe-voiced magical movement through the canonical gameplay
seams while preserving the existing JRPG, narrative, traversal, and reward
authorities.

## Runtime component

Add `UMelodiaResonantPassageComponent` from:

`Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaResonantPassageComponent.h`

Attach it to the canonical player pawn candidate:

`/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter`

Initial Petal Cantata proof configuration:

```text
MovementId              = petal_cantata
RequiredResonantFormId  = ResonantForm_PetalRipple
bRequireUnlockedForm    = true
BeatsPerStage           = 4
bAdvanceOnMusicBeat     = true
TraversalContextId      = <matching authored exploration context, if used>
```

The component reads the existing `UMelodiaWardrobeSubsystem`, requires the form
to be equipped and unlocked, listens to the existing
`UMelodiaMusicClockSubsystem`, and never ticks frame-by-frame.

## Gameplay boundaries

- Wardrobe declares the form and answers unlock/capability queries.
- `UMelodiaTraversalComponent` remains the only traversal authority.
- `RequestGlideAtThreshold()` is an explicit player-facing request and delegates
  to `RequestTraversalMode(Glide)`; it does not grant Glide.
- `UMelodiaNarrativeSubsystem` remains the only canonical narrative/save owner.
- `UMelodiaPCGNarrativeChallengeBridgeComponent` remains the only music-pattern
  completion adapter.
- The passage component never grants currency, cosmetics, capabilities, rewards,
  quests, flags, or save data.

For the first persistent music-key proof, keep the existing challenge fixture and
bridge configuration:

```text
ChallengeId        = challenge.first_resonance_echo
CompletionFlagId   = challenge.first_resonance_echo.completed
RewardId           = reward.first_resonance_echo
CompletionIntentId = challenge.first_resonance_echo.attempt_id
```

Attach that bridge only to the existing `APCGHeroMusicGraphHost` owner. Do not
move its transaction into the passage component.

## MCP verification calls

```json
{"name":"melodia_resonant_world_get_atlas","arguments":{}}
{"name":"melodia_resonant_world_compile_passage","arguments":{"seed":3900,"movement_id":"petal_cantata"}}
{"name":"melodia_resonant_world_get_handoff","arguments":{"target":"gameplay"}}
{"name":"melodia_resonant_world_validate","arguments":{}}
```

## Current status

The source component, deterministic passage artifacts, PCG plan, and proof
envelope are authored. A closed-editor build, additive map application, form
materialization check, and PIE evidence are still required before this becomes a
runtime-complete gameplay slice.
