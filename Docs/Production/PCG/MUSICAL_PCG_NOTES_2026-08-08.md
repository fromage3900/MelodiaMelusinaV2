# Musical PCG notes — interactive piano keyboard

## Current implementation

- Full 88-note A0–C8 layout: 52 white keys and 36 black keys.
- Deterministic layout math lives in `Content/Python/pcg_piano_layout.py` and is unit-tested outside Unreal.
- The PCG graph is authored as two explicit branches:
  `PCGCreatePointsSettings → PCGSpawnActorSettings (NoMerging) → InitializeFromPCGPoint`.
- Each point packs the key index and MIDI note into `FPCGPoint.Seed`, so the spawned actor receives stable identity without a bespoke PCG node.
- White and black keys have separate actor classes, collision volumes, spring-return motion, player-pawn overlap triggers, and Blueprint/dynamic event hooks.
- Key contact arbitration keeps a black key on top of an overlapping white key while allowing distinct neighboring keys to play together.
- Editor-time Geometry Script baking produces centered beveled StaticMesh assets; the runtime keyboard does not depend on Geometry Script.
- A small dedicated material master produces ivory, ebony, and keybed material instances with separate PBR parameter values.
- `setup_pcg_piano_level.py` creates a neutral light proof level with floor, lighting, player start, overview camera, keyboard host, and PCG generation.

## Bottlenecks and roadblocks encountered

1. The workspace root was not the Git repository. The actual Unreal project/repository is `BS_GodFile`; implementation is scoped there.
2. The worktree already contains unrelated user changes and generated files. They are intentionally preserved; new piano files are additive.
3. The project's existing PCG experiments show `PCGVolumeSampler` can emit zero points in this project. The keyboard graph therefore uses authored `PCGCreatePointsSettings` data rather than a volume sampler.
4. PCG actor spawning can be expensive in large existing test maps. The keyboard gets a dedicated light level so generation and interaction can be checked without `ZenForestTest`-scale content.
5. A custom PCG node was initially a possible route for key identity. UE 5.8 already exposes point arrays, point seeds, and `PostSpawnFunctionNames(FPCGPoint, Metadata)`, which is a smaller and more native solution.
6. Geometry Script asset baking needs a live editor smoke test because Python bindings and asset-save behavior are editor-version-sensitive. The baked-mesh boundary keeps that risk out of runtime gameplay.
7. Dedicated material graph generation is deliberately small. The current project has a large, complex material library; the piano gets an isolated PBR master to avoid coupling to unrelated universal-material changes.
8. The live editor session generated the Geometry Script assets successfully, but its Monolith bridge disconnected during Live Coding. The C++ translation unit compiled; the editor must be restarted/reloaded before the new reflected piano actor classes can be used by the graph script.
9. Continuation audit: the same UnrealEditor process is still open and pre-reload. A filesystem audit confirms the seven baked visual assets, but no `DA_PianoKeyboardProfile`, `PCG_PianoKeyboard`, or `L_PCG_PianoKeyboard` asset yet. The one-shot `setup_pcg_piano_all.py` now reduces the remaining post-reload work to one command.

## Second graph: interactive music step sequencer

- `PCGMusicStepSequencer` is now scaffolded in `Source/BS_GodFile/Piano/PCGMusicSequencer.*`.
- The graph is deterministic: 16 step columns x 4 lanes = 64 pads, with step and lane packed into each point seed.
- Each `APCGMusicStepPad` has a player-pawn trigger, spring press/release motion, lane MIDI identity, and activation/deactivation delegates.
- `APCGMusicStepGrid` owns the PCG component and aggregates pad events, so a Blueprint or audio system can turn the grid into a playable loop, visualizer, or rhythm challenge.
- `setup_pcg_music_sequencer_all.py` builds the profile, graph, and dedicated proof level after the reflected module is loaded.
- The pure-Python sequencer contract tests pass (16 steps, 4 lanes, 64 deterministic identities). Unreal compilation and visual QA remain pending the editor reload.

## Future musical PCG graphs with gameplay

- `PCG_MusicStepSequencer`: spawn a grid of beat/step pads; stepping a row queues a pattern event and lights the active lane.
- `PCG_ArpeggioStair`: encode scale degree and octave in stair height; player traversal emits an ascending/descending arpeggio.
- `PCG_ChordGarden`: generate nearby chord clusters whose overlaps harmonize; activate a complete triad to grow the next garden ring.
- `PCG_RhythmBridge`: build a bridge from beat cells; missed beats retract or change collision state while successful movement drives percussion events.
- `PCG_TonalDoorway`: generate three to five keyed floor tiles and open a doorway only when the player performs the generated chord progression.
- `PCG_DynamicMusicMaze`: generate room graph motifs from a scale or mode; each room contributes a stem, and the player's route becomes the arrangement.

The step sequencer is the first follow-on graph. After its render and gameplay audit, the next useful graph to promote is `PCG_ArpeggioStair`, because it reuses the same seed-identity and spring-trigger patterns while testing traversal-driven musical progression.
