# Actual TouchDesigner Live-Visual Pipelines — Research Fold-In

**Research date:** 2026-09-08  
**Purpose:** replace vague "audio reactive visuals" assumptions with documented production patterns used in real shows and current TouchDesigner practice.

## 1. Production pattern that repeats

Across touring productions, VJ systems, and current TD tooling, the robust pattern is:

```text
SHOW / MUSIC SIGNALS
        ↓
SEMANTIC CONTROL BUS
        ↓
SCENE / SONG MODULE
        ↓
GENERATOR(S)
        ↓
BOUNDED FX STACK
        ↓
MIX / STATE / MANUAL TRIM
        ↓
OUTPUT / MEDIA SERVER / CAPTURE
```

The important lesson is not one magic operator.

It is **separation of concerns**.

## 2. SETUP — Red Hot Chili Peppers world tour

Source:
https://derivative.ca/community-post/how-setup-did-world-tour-red-hot-chili-peppers/66633

Reported production:
- grandMA2 is the live show-control surface;
- one console owns show structure/cue lists/lighting;
- another acts as live video control;
- grandMA sends parameters to TouchDesigner over sACN;
- TD selects/generates scenes, adjusts speed/particle parameters, mixes/processes camera content;
- content uses abstraction, particles, noise, shapes, GLSL;
- SETUP explicitly says optimization was the major lesson;
- in hindsight they would keep **generation/content management** in TD and move more utility display/pixel-map logic elsewhere.

### Melodia adoption

KEEP:
- semantic control values;
- scene selection;
- live parameter trim;
- generator-centric TD;
- external/runtime authority remaining separate.

DO NOT:
- make TD own game state;
- make TD responsible for every delivery/display concern.

## 3. Moment Factory — Nine Inch Nails

Source:
https://derivative.ca/community-post/moment-factorys-mastery-temporary-play-space

Reported pipeline:
- full moving-screen stage was previsualized in TD;
- Kinect depth streams were distributed across computers using Touch Out/In;
- silhouettes drove particle collision, water distortion, shadows, masks/reveals;
- show-master cues arrived through Art-Net.

### Melodia adoption

KEEP:
- previz inside TD;
- live image/data used as masks/fields rather than only overlays;
- distributed input when necessary;
- external cue authority.

APPLICATION:
A UE sheep silhouette/depth/matte could eventually shape TD fields without TD becoming the creature/game owner.

## 4. Plastikman — Ableton-integrated visual system

Source:
https://derivative.ca/community-post/plastikman-derivative-team-2010-tour/60824

Reported pipeline:
- Ableton shared controller values, active loops, clocks, sequencing/transitions, raw audio and audio-effect outputs;
- visual artists worked in per-track "cocoons" with standardized music signals already available;
- TD had a custom operator/performance UI.

### Melodia adoption

This is extremely close to the desired architecture:

```text
Melodia canonical music/game semantics
        ↓
standard TD signal bus
        ↓
scene-specific "cocoon"
```

Each scene should not rediscover beat detection or networking.

## 5. Rush — one authored performance system per song

Source:
https://derivative.ca/community-post/rush-30th-anniversary-tour/60822

Reported pipeline:
- one Touch "synth" per song;
- each contained textures, 3D shapes, triggerable motion, controls, lighting and presets;
- sections of songs had prepared scene states/presets;
- selected parameters remained open for live MIDI/mouse/keyboard improvisation.

### Melodia adoption

Build **authored states + bounded improvisation**.

For Choral Sheep:
- QUIET
- ROOT
- INTERVAL
- RESOLUTION
- WORLD
- AFTERIMAGE

Manual controller input may trim intensity/opacity/timing, but not redefine the game's harmonic truth.

## 6. okVJ — current modular VJ tooling

Sources:
https://derivative.ca/community-post/touchdesigner-confluence-mutek-2026/75005
https://github.com/ok-vj/okVJ-Shared

Current concepts:
- custom controls;
- scene management;
- MIDI/audio-reactive workflows;
- shader switching;
- FX stacks;
- modular stand-alone components;
- parameter mapping and control surfaces.

### Melodia adoption

Treat:
- scene;
- state;
- FX;
- controller mapping

as reusable components.

Do not build one unstructured root network.

## 7. Current Derivative concert tutorial pattern

Source:
https://derivative.ca/tutorials

A current concert-visual recipe explicitly uses:

```text
Edge
→ Feedback
→ Lookup
→ Bloom
→ Displace
```

This is a useful **hit / transition recipe**, not a Melodia default look.

Melodia translation:
- feed a pitch glyph, silhouette, Chladni contour, or ornament edge into the chain;
- trigger/gate feedback from authored show state;
- keep a reset path;
- composite it as one event layer.

## 8. GLSL TOP — field generator

Sources:
https://docs.derivative.ca/GLSL_TOP
https://docs.derivative.ca/Write_a_GLSL_TOP

GLSL TOP is appropriate for deterministic image-space procedural fields.

Melodia usage:
- Chladni equations;
- interference;
- polar/radial transforms;
- line fields;
- displacement masks;
- deterministic texture generation.

GLSL should receive **shaped semantic parameters**, not raw unmanaged audio whenever possible.

## 9. GPU geometry — POPs / instancing

Sources:
https://docs.derivative.ca/POP
https://docs.derivative.ca/Particle_POP
https://docs.derivative.ca/Geometry%20COMP

Current TD POPs run numeric/3D data on the GPU; Particle POP is suitable for large GPU particle systems. Geometry COMP instancing can be driven from TOP/CHOP/SOP/DAT data.

Melodia usage:
- pearl point clouds;
- staff-line particles;
- constellation nodes;
- flock-field echoes;
- screen-scale line/point structures.

Do not use a million particles when one GLSL field communicates the idea better.

## 10. Perform Mode / performance monitoring

Sources:
https://docs.derivative.ca/Perform_Mode
https://docs.derivative.ca/Perform_CHOP

Perform Mode is the correct live-show execution context: only the specified performance window/control UI is rendered instead of the full editor.

### Required Melodia show gate

Before calling a TD scene live-ready:
- run in Perform Mode;
- monitor FPS/cook timing;
- test reset;
- test scene switching;
- test input loss;
- test bypass.

Target: stable real-time playback at the intended output resolution on the actual show machine.

## 11. Spout / texture exchange

Source:
https://docs.derivative.ca/Syphon_Spout_Out_TOP

Spout is local-machine GPU texture sharing on Windows and does not transmit across machines.

### Melodia integration tiers

**P0 — current / safe**
- existing OSC data;
- deterministic replay;
- TD image-sequence / transparent pass output;
- AE assembly.

**P1 — verify before claiming**
- local Spout texture exchange with Unreal, **only after a real UE Spout receiver is proven in this project**.

**P2 — optional**
- TouchEngine-UE / deeper embedding if a future performance requirement justifies it.

Do not make the capstone depend on an unverified texture bridge.

## 12. DMX / stage-lighting future lane

Sources:
https://docs.derivative.ca/DMX_In_CHOP
https://docs.derivative.ca/DMX_Out_CHOP

TD can ingest/output Art-Net and sACN/DMX.

This is useful for a future Melodia live-performance installation.

It is not required for Choral Sheep Capstone 01.

## 13. Actual pipeline we should use now

```text
UE / deterministic replay
        ↓
existing OSC + audio semantic layer
        ↓
SIGNAL NORMALIZATION
Null CHOP hubs / lag / trigger / state
        ↓
SHOW STATE
quiet / root / interval / resolution / world / afterimage
        ↓
SCENE COMP
Chladni Fleece
        ↓
GENERATOR
GLSL field + optional POP/instancing layer
        ↓
FX
event-gated feedback / lookup / bloom / displace
        ↓
MIX
subject-safe compositing
        ↓
OUTPUTS
beauty / alpha / field / glyph / debug
        ↓
Movie File Out / AE
        ↓
optional Spout after verification
```

## 14. Production rule

> **The music should choose the state. The artist should choose what that state looks like.**

Raw amplitude can modulate an authored visual.

It should not be allowed to art-direct the whole scene.
