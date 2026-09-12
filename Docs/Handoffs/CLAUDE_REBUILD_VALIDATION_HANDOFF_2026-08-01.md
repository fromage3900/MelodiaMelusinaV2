# Claude rebuild and validation handoff — 2026-08-01

## Read first

This is a bounded editor/rebuild/validation lane. Preserve the stock JRPG systems as the only authority for turns, targets, damage, results, party, inventory, quests, input, encounters, saves, and progression. FX, PPV, Niagara, stencil, and UI remain presentation outputs and must never gate or replace those systems.

Do not interrupt an active editor rebuild. Finish the current safe editor-close/rebuild sequence before opening another validation lane.

## Ownership

Claude owns:

- Safe editor/game shutdown and the closed-editor `BS_GodFileEditor` rebuild.
- Validation of the reflected `UMelodiaRhythmReactivitySubsystem::SetReactiveStencil` API.
- PPV attachment and ArtOfShader integration, including `MPC_PPBlending`, while preserving the existing palette/music-clock path.
- Environment/render A/B review and fixed-camera visual evidence.
- PIE/runtime validation after the native rebuild.

Claude does not own or modify the following in this lane: `MelodiaHairComponent.cpp`, hair assets, environment maps/assets, landscape, lighting, materials, PCG, VFX placement, gameplay authority, or the stale `WBP_Battle_Rhythm` graph. Do not silently repair stale Blueprint references as part of this rebuild batch.

## Closed-editor rebuild

1. Close the Unreal Editor, game/PIE process, and Live Coding session safely.
2. Run the editor-target rebuild from `C:\EnvironmentPortfolio\BS_GodFile`:

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" `
  BS_GodFileEditor Win64 Development `
  "C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" -WaitMutex
```

3. Record the command result, duration, compiler errors/warnings relevant to the changed source, and the resulting editor binary timestamp/hash if available.
4. If Live Coding still blocks the build, stop and report that exact blocker. Do not claim runtime validation from a source-only readback.

## Reflection and runtime checks

After a successful rebuild:

- Confirm the editor can load `UMelodiaRhythmReactivitySubsystem` and expose `SetReactiveStencil(UPrimitiveComponent* MeshComponent, int32 StencilValue)` as a Blueprint-callable function.
- Confirm the implementation remains presentation-only: value `0` clears/disables CustomDepth; positive values clamp to `0–255` and enable CustomDepth on the supplied component.
- Confirm no caller reads stencil state back, branches gameplay on it, waits for an FX callback, or treats visual completion as authority.
- Confirm stencil writes are component-specific and that any test path clears back to `0` on exit/death/teleport/unload/pooling.
- `r.CustomDepth=3` is owner-approved and persisted in `Config/DefaultEngine.ini` per the current handoff. Do not change it again or introduce a competing renderer setting.

## PIE/runtime gates

Run the smallest useful route through the existing systems and record evidence, not impressions:

1. Launch/opening route: travel through the authored route and confirm it uses `UMelodiaTravelSubsystem::TravelTo`; record the graph fingerprint if available.
2. Battle route: enter a stock battle, confirm stock turn/target/damage/result flow, and confirm presentation feedback does not delay input or results.
3. Death/cleanup route: confirm stencil/FX presentation state clears when the relevant actor/component dies, teleports, unloads, or is pooled.
4. Save/restore route: save and restore through the existing save authority; confirm no FX/PPV/UI callback is required for completion.
5. Narrative route: verify the grief-hook presentation remains the locked version—Melusina is the survivor, Sir is alive/retrievable, the past duet partner remains absent through fragments/half-melodies, Resonance is call-and-response, and the ending remains a warm reunion. Do not add a diagnosis, guilt wound, sanity meter, punishment rhythm, dead Sir, animal harm, or a new mechanic.
6. Run the known regression baseline when the editor/runtime is available:

```text
Automation RunTests Melodia
```

Report all results, including the three known failures: `Melodia.NPC.InteractionDefaults`, `Melodia.Roguelike.Functional.ThreeStagePhysicalRoute`, and `Melodia.Roguelike.Functional.TwentyFiveGenerationSoak`. Do not relabel known failures as fixed without new evidence.

## Explicit stop conditions

Stop and hand back evidence if:

- Live Coding, an editor lock, or a native compile failure prevents the rebuild.
- `SetReactiveStencil` is not reflected after a successful rebuild.
- a test requires changing combat, rhythm, quest, save, input, or encounter authority.
- a fix would touch the quarantined files/assets listed above.
- the visual result requires changing environment placement, landscape, lighting, materials, PCG, hair, or VFX placement.
- `WBP_Battle_Rhythm` still exposes missing `ToggleOrreryMenu` pins or a deleted `BP_Melusina` cast. Record the stale graph as a separate follow-up; do not delete, repoint, or invent ownership in this batch.

## Required handback evidence

Return:

- rebuild command and pass/fail output;
- reflected function evidence;
- exact renderer setting source and current value;
- PIE route/battle/death/save observations;
- regression test counts and known failures;
- fixed-camera PPV/FX A/B captures or a clear statement that visual approval remains open;
- files changed, if any, with explicit confirmation that the protected list was untouched.
