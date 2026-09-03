# PCG Piano Keyboard

## Build order

After the `BS_GodFile` editor module has compiled and the editor has reloaded the module, run this from the Unreal Python console or the editor Python bridge:

```python
import sys
sys.path.append(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python")

import setup_pcg_piano_all
setup_pcg_piano_all.build_all(force=True)
```

The scripts are additive and target `/Game/EnvSandbox/PCG/Musical`. The graph creates 52 white-key actors and 36 black-key actors, each with a stable key index/MIDI note packed into the PCG point seed.

## Runtime contract

- `APCGPianoKeyboard` owns the PCG component and forwards key events.
- `APCGPianoWhiteKey` and `APCGPianoBlackKey` are spawned one per point with `NoMerging`.
- `InitializeFromPCGPoint(FPCGPoint, const UPCGMetadata*)` assigns key identity and applies profile mesh/material references.
- A player-controlled pawn overlapping a key's `StepTrigger` presses it with a spring-damped animation and releases it when contact ends.
- When a pawn overlaps both layers in the same footprint, the higher black key wins; unrelated neighboring contacts remain independently active.
- Sound is an optional profile hook. Set `bPlayPressSound` and assign `PressSound` when a sound asset is available.

## Verification state on 2026-08-08

- Pure layout tests: passing, 88/52/36, A0–C8.
- Live editor Geometry Script build: passing; beveled key, black key, and keybed meshes plus ivory/ebony/keybed material instances were created.
- C++ translation unit compile: `PCGPianoKeyboard.cpp` compiled successfully in the Unreal build action.
- Full editor link was blocked by the already-running editor holding plugin/module DLLs; restart the editor before running the graph/level scripts so the new reflected classes are loaded.

## Follow-on graph: music step sequencer

After the piano proof level has been rendered and audited, build the second musical graph with:

```python
import setup_pcg_music_sequencer_all
setup_pcg_music_sequencer_all.build_all(force=True)
```

This creates `/Game/EnvSandbox/PCG/Musical/Sequencer/PCG_MusicStepSequencer`, a 16-column by 4-lane grid with 64 interactive pads, plus the dedicated `L_PCG_MusicStepSequencer` proof level. The pad event carries `(StepIndex, Lane, MidiNote, SteppingActor)` so a Blueprint can sequence audio, light the active lane, or score a rhythm challenge.

The expected verification order is:

1. Open `L_PCG_PianoKeyboard`, render the overview, and walk across white and black keys.
2. Audit 88 piano actors and confirm spring release plus black-over-white contact arbitration.
3. Open `L_PCG_MusicStepSequencer`, render the overview, and walk across several lanes and columns.
4. Audit 64 pads and confirm the grid's aggregate activation count and event delegates.
