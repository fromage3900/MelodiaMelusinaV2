# Melodia TouchDesigner Show-System Architecture

**Status:** CURRENT DESIGN CONTRACT — 2026-09-08  
**Extends:** `/project1` in `grandmaster_melodia`  
**Does not replace:** existing `audio`, `osc`, `postfx`, `render` networks.

## 1. Authority

Unreal / Melodia gameplay remains canonical for:
- game state;
- beat/music clock;
- companion state;
- harmonic success;
- world consequence;
- save/progression.

TouchDesigner owns:
- live visual interpretation;
- scene state presentation;
- graphic/generative fields;
- live-performance controls;
- output/capture passes.

## 2. Current project assets to preserve

Existing, source-present:
- `/project1/audio`
- `/project1/osc`
- `/project1/postfx`
- `/project1/render`
- `/project1/melodia_audio` when the audio-reactive flower script is installed
- TDN exports under `grandmaster_melodia/networks/`
- current OSC routes and reusable Null/CHOP hubs.

Do not rename/move these during Capstone 01 merely to make the graph prettier.

## 3. Add one performance container

Preferred extension:

```text
/project1/performance
  /input
  /state
  /scenes
  /fx
  /mix
  /ui
  /output
  /audit
```

### /input
References existing semantic sources.

No second OSC listener unless an existing shared route is proven unusable.

Expected normalized channels:

```text
beat_phase
beat_pulse
bpm

pitch_class
amplitude
motif_phase
harmonize_active

harmony_root
harmony_quality
harmony_tension
harmony_resolved

world_response_strength
```

Capstone fixture/replay may supply these before live runtime integration.

### /state

One show-state CHOP/DAT:

```text
QUIET = 0
ROOT = 1
INTERVAL = 2
RESOLUTION = 3
WORLD = 4
AFTERIMAGE = 5
```

It should expose:
- state id;
- transition progress;
- hit trigger;
- scene intensity;
- manual trim;
- reset pulse.

### /scenes

Each visual idea is a self-contained Base COMP.

First scenes:

```text
/chladni_fleece
/pitch_glyph
/shared_harmony
/world_field
```

Each scene must expose:

**Inputs**
- semantic CHOP;
- optional image/matte TOP;
- reset.

**Parameters**
- Intensity;
- Seed;
- Bypass;
- Palette profile;
- Transition;
- Manual trim.

**Outputs**
- `OUT_MAIN`
- `OUT_ALPHA`
- `OUT_FIELD`
- `OUT_DEBUG`

No hidden references to random root operators.

### /fx

Reusable, bypassable effects:

```text
/fx_feedback_hit
/fx_bloom
/fx_displace
/fx_grade
/fx_glitch_hit
```

Effects do not own show state.

Every temporal/feedback effect must have explicit reset.

### /mix

Composites:
- subject/UE input;
- primary scene;
- supporting effect;
- optional glyph;
- atmosphere.

The subject-readability rule lives here.

### /ui

Live operator controls:
- scene/state select;
- intensity;
- manual trim;
- reset;
- bypass;
- output preview;
- performance stats.

Future MIDI/DMX mapping attaches here.

### /output

Stable named outputs:
- `OUT_SHOW_MAIN`
- `OUT_SHOW_ALPHA`
- `OUT_SHOW_FIELD`
- `OUT_SHOW_GLYPH`
- `OUT_SHOW_DEBUG`

Final capture can use Movie File Out.

Spout is optional and only enabled after project-side receiver proof.

### /audit

Displays:
- current semantic inputs;
- state;
- dropped/missing signals;
- FPS;
- cook timing;
- active scene;
- feedback reset status.

## 4. Scene contract

Every performance scene must answer:

1. What semantic input changes the **structure**?
2. What changes only the **strength**?
3. What event triggers it?
4. What is its rest state?
5. How does it reset?
6. What is its one memorable image?
7. What visual identity rule does it obey?

If those cannot be answered, the scene is not ready to build.

## 5. Choral Sheep state table

| State | Primary image | Structural driver | Modulation | Allowed support |
|---|---|---|---|---|
| QUIET | sheep / dark field | none | breath | tiny pearl atmosphere |
| ROOT | single C field | pitch class | amplitude | sparse glyph |
| INTERVAL | C/E interference | interval relation | tension | short feedback hit |
| RESOLUTION | coherent C/E/G field | harmony resolved | beat phase | controlled bloom |
| WORLD | field at architectural scale | world response | amplitude | water/pearl echo |
| AFTERIMAGE | fading nodal trace | transition progress | none | no new effects |

## 6. Manual control law

Manual performance control may alter:
- opacity;
- intensity;
- effect mix;
- transition timing within bounds;
- selected presentation scene;
- camera/screen framing for a standalone show.

Manual control may not:
- mark harmony valid;
- grant world response;
- write game state;
- replace canonical music clock.

## 7. Replay mode

Final capstone should support deterministic replay.

Replay source should produce exactly the same semantic channel names as live mode.

Recommended switch:

```text
LIVE INPUT ─┐
            ├─ Switch CHOP → semantic_bus → rest of show
REPLAY ─────┘
```

No scene should know whether its input came from UE or replay.

## 8. Output mode

### Live preview
- intended performance resolution;
- Perform Mode;
- performance monitor visible on control screen only.

### Final capstone
- deterministic playback;
- render independent layers;
- transparent/lossless image sequences when needed;
- AE does editorial/final assembly.

## 9. Failure behavior

If:
- OSC disappears;
- replay ends;
- pitch value invalid;
- harmony state absent;

then scene should:
1. hold briefly if appropriate;
2. decay to QUIET;
3. never explode to full intensity;
4. never leave feedback uncleared.

Fail soft, visually.
