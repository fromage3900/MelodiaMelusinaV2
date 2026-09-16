# 3D Spatial Awareness — research and Rider plan (2026-09-15)

## What the shelves hold (verified today, not remembered)

- Mix architecture EXISTS: SCL_Master/Music/SFX/Voice/Ambience +
  SUBMIX_Music/SFX/Voice/Ambience (`/Game/Melodia/Audio/Mix/`).
- BGM (Duvet 93 BPM, Sewaa 131 BPM + 11 vocal stems), 26 UI blips,
  98bpm ambience bed. Quartz clock + MPC palette live.
- Spatial: NOTHING. Zero attenuation assets, zero spatialized cues. The
  August immersion plan lists "attenuation presets for 3D grade pops /
  ambient placement" as remaining — still remaining.
- `UMelodiaAudioComponent` is referenced (PCGHeroMusic.h, rhythm component)
  but DEFINED NOWHERE in Source/. The staged August C++ never landed here.

## What the engine offers (all on disk, UE 5.8)

- Native (free, no plugin): SoundAttenuation assets — distance falloff,
  cones, occlusion traces, stereo spread; default panner per source.
- `Spatialization` plugin: basic spatializer options. `SoundFields`:
  ambisonic beds (dream-drone skies). `AudioModulation`: game-state mix.
- HRTF path: `ResonanceAudio` (Google — ships, but archived upstream 2023,
  do not adopt) and `SteamAudio` (Valve — maintained, HRTF + baked
  occlusion, but packaging weight + phonon bake step).
- `MetaSounds`: procedural-call/response stingers (sheep song grammar).

## The rhythm-game rule (the one insight that matters)

Timing-critical sound NEVER spatializes: metronome, hit grades, BGM stay
2D + Quartz-quantized, because HRTF/convolution add latency and rhythm
lives or dies in milliseconds. Spatial audio is for EXPLORATION ONLY:
beacons, bells, brook, sheep. Two buses, two laws — clock vs compass.

## Melodia tie-ins (why this is immeasurable here, not generic)

1. Mr Choral Sheep as a spatial beacon — follow the song to the lake.
   Music-as-key you hear with your whole head.
2. Arpeggio bells as positional melody — walk the bridge, play the tune
   by moving through it.
3. Hearing-mode accessibility (Aug plan item 7): spatial awareness IS the
   feature — pulse + direction for every cue.

## Rider task (small, builds closed-editor, no editor lock)

Define `UMelodiaAudioComponent` (missing — see above) with ONE verb:
`PlaySpatialCue(Sound, Location)` using `FSoundAttenuationSettings`
constructed in code (sane dell defaults: 800 inner, 4000 falloff,
occlusion on). `UGameplayStatics::SpawnSoundAtLocation` accepts the
settings struct — zero editor assets, zero plugin strings, testable via
a RiderLink automation test. Native attenuation first; Steam Audio only
if ears demand HRTF later.

## Order of work

1. Rider: component + spatial cue verb + automation test (build, green).
2. Editor (owner or one-holder session): 2 attenuation presets if assets
   preferred over code; place ambience + sheep beacon in Morning.
3. Playtest with headphones: sheep-found-by-ear before sheep-seen.
