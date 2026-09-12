# Handoff: PCG Hero Music lane (2026-08-09)

Addressed to the agent/owner working the PCG Hero Music + Piano lane (ChatGPT session,
window "BS_GodFile - help me source th...").

## 1. Your file blocks every build — fix or coordinate

`Source/BS_GodFile/Piano/PCGPianoKeyboard.cpp:1` — `#include "Piano/PCGPianoKeyboard.h"`
fails with `C1083` (the header exists beside the .cpp; the include root cannot resolve
it). This and `MelodiaWaterInteractionSubsystem.cpp:115` (`AWaterBody` undefined) are the
**only** two errors in the last compile; they block Live Coding and UBT for every lane.

Suggested fix: `#include "PCGPianoKeyboard.h"` (same directory) or add the module include
path. The water one needs the correct `AWaterBody` header ordering — both are one-liners.

## 2. BGM wiring change landed (MelodiaCore)

`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAudioComponent.cpp` — `PlayBGM()` and
`PlayBGMQuantized()` now prefer `/Game/Melodia/Audio/BGM/SW_BGM_Battle_Duvet_Cover`
(211 s, 93 BPM, looping) and fall back to `SW_BGM_Battle_Placeholder_128`. Compile-clean
in isolation; needs a closed-editor rebuild to go live.

## 3. New audio asset — do not delete

`/Game/Melodia/Audio/BGM/SW_BGM_Battle_Duvet_Cover` (SoundWave, looping) — imported from
the Duvet cover render. Owned by the audio lane.

## 4. Audio lane activity (in progress)

Rhythm SFX sourcing (Lyra / TurnBasedJRPG sample / ElectricDreamsEnv), live-audio wiring,
and mixing architecture are being staged by the audio lane. Assets will land under
`Content/Melodia/Audio/`. If you see new `.uasset`/`.wav` there it is intentional.

## 5. Editor rules (unchanged, restated)

- One editor instance: PID 33484 currently, Monolith 9316 is the only MCP surface.
- `MODAL_OPEN` in the log = modal dialog, not a hang.
- Verify by re-reading; `success: true` only means nothing threw.

## 6. Hero graph lane update

The hero proof builders now preserve the measured classic-library architecture
branches and add two authored PCGEx paths per graph:

- a tagged `PCGGetSpline` -> `PCGSplineSampler` -> `PCGExSampleNearestSpline`
  curve branch using the exact playable cathedral/bridge layout curve;
- the project’s existing expanded tensor source graph, copied into the hero
  graph and retargeted to a measured classic arch mesh/material.

The measured curve points are now authored inside each graph through
`PCGExCreateSplineSettings`, so the proof levels do not depend on a missing
Blueprint `SplineActor` class. This keeps the graph walkable and curve-driven
without introducing a second clock, MPC writer, or generic cube architecture
fallback.
