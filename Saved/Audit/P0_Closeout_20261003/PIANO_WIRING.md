# Piano key-run completion -> Quantum draw

Apply: from BS_GodFile root `patch -p1 < Saved/Audit/P0_Closeout_20261003/piano_keyrun_complete.patch` (dry-run verified against the working tree 2026-10-03; fuzz 1 is only asymmetric context, harmless).

## What it does
- APCGPianoKeyboard tracks `PlayedWhiteKeys` (key indices) in NotifyKeyPressed; black keys ignored.
- When `PlayedWhiteKeys.Num() >= RequiredWhiteKeyCount` (default 14) and not yet completed: sets `bKeyRunCompleted`, broadcasts `OnKeyRunCompleted` (once), calls `UMelodiaRhythmReactivitySubsystem::NotifyVictory()`, then ONE `UMelodiaQuantumDrawSubsystem::RequestDraw`.
- Candidates: `chart_0` ResonanceBeat (diff 0.25, spacing 0.20) vs `chart_1` WorldAwakening (diff 0.75, spacing 0.55). layout_ranker.score_candidate peaks at diff 0.75 / spacing 0.55: chart_1 = 1.0, chart_0 = 0.56, so WorldAwakening is the predicted winner (classical-baseline always; qsharp/score-weighted backends ~64%).
- Provider is passed empty: RequestDraw falls back to `Config->QuantumDrawProvider` (default "qsharp-simulator"); if config/service is off it completes with `classical-baseline`, bSuccess=false; timeout path (3000 ms) already exists. Never blocks.
- `ResetKeyRun()` (BlueprintCallable) clears the set and re-arms.

## Includes added (cpp)
`MelodiaQuantumDrawSubsystem.h`, `Engine/GameInstance.h`. No Build.cs change expected (same module).

## Risks
- Seed is `hash(KeyboardId) ^ FMath::Rand()`: non-reproducible by design; fix the seed if a deterministic test is wanted.
- RequestDraw rejects with backend `busy` if another draw (battle song draw) is in flight: no QuantumPulse then; completion event/victory still fire.
- RequiredWhiteKeyCount counts distinct white KeyIndex values; if the placed run is not 14 white keys, edit the property on the instance.
- Playing a key before PCG keys register is unaffected. New UPROPERTY/UFUNCTION: needs a closed-editor build, not Live Coding.
- Owner's uncommitted edits to these files: re-run `patch --dry-run` before applying.

## PIE observation
- Grep log: `MELODIA_PIANO key run completed`, `MELODIA_QUANTUM`, `MELODIA_PIANO key-run draw winner=`.
- Step on all 14 white keys: completion line appears exactly once; further presses silent until ResetKeyRun().
- Draw log: winner=chart_1 (expected); with service down: winner=None backend=classical-baseline/timeout success=0.
- QuantumPulse on MPC_Melodia_Palette spikes then decays at 3.5/s only when a real chart_N winner returns.
- Bind OnKeyRunCompleted in BP to confirm single fire.
