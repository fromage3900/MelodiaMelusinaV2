# Resonant World UI Handoff — 2026-08-22

## Purpose

Expose the magical passage as a readable, musical UI response without creating a
second clock, wardrobe state, reward path, or save object.

## Source of truth

The runtime presenter is:

`Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaResonantPassageComponent.h`

Bind the UI to `OnStageChanged(MovementId, StageIndex, Stage, bVoiced)`. Do not
poll the world every frame and do not infer the stage from wall-clock time.

The event is emitted by authored `UMelodiaMusicClockSubsystem::OnMelodiaBeat`
events. The component advances four stages at `BeatsPerStage` (default 4):

1. Invocation
2. Unfolding
3. Threshold
4. Release

## Existing UI targets and assets

- Primary existing HUD candidate: `/Game/Blueprints/WBP_RhythmHUD`
- Existing rhythm textures: `Content/EnvSandbox/Textures/Source/MelodiaGameUI/`
- Existing filigree/grade assets: `Content/EnvSandbox/Textures/Melodia/GameUI/`
- Existing palette path: `MPC_Melodia_Palette` through the music-clock/presentation
  layer

The UI should render a four-node passage rail, the active movement name, and a
quiet “voicing unavailable” state when `bVoiced` is false. The stage event may
drive a pulse, icon swap, text reveal, or camera/photo affordance; it must not
grant a traversal capability or complete a narrative challenge.

## Blueprint wiring

On the canonical Melusina pawn:

1. Obtain the `MelodiaResonantPassageComponent` reference.
2. Bind `OnStageChanged` once in the HUD/controller setup path.
3. Map `StageIndex` to the four rail nodes.
4. Use `MovementId` to select authored labels and iconography.
5. Use `bVoiced=false` to clear/soft-disable the rail.
6. Use `UMelodiaMusicClockSubsystem::GetMusicPulse` only for presentation
   breathing; never introduce a UI timer as a replacement clock.

## MCP verification calls

```json
{"name":"melodia_resonant_world_compile_passage","arguments":{"seed":3900,"movement_id":"petal_cantata","archetype_id":"SakuraDreamer"}}
{"name":"melodia_resonant_world_get_handoff","arguments":{"target":"ui"}}
{"name":"melodia_resonant_world_validate","arguments":{}}
```

## Current status

Source contract and offline handoff are present. Blueprint wiring and PIE visual
evidence remain pending the single-editor integration window. Do not mark this
handoff runtime-complete until the widget compiles and a beat-driven stage change
is captured in PIE.
