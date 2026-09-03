# Audio-Reactive Pipeline Guide

**Date:** 2026-09-03 | **Scope:** Blender 5.2 → UE 5.8 audio-reactive workflow for Melodia Studio
**Audience:** Technical artists, lookdev, and pipeline engineers building audio-reactive content

---

## Table of Contents

1. [Blender 5.2 Sample Sound Frequencies Node](#1-blender-52-sample-sound-frequencies-node)
2. [Baking Audio Reactivity for UE Export](#2-baking-audio-reactivity-for-ue-export)
3. [Audio Tools Comparison](#3-audio-tools-comparison)
4. [The audio_terrain.py Builder](#4-the-audio_terrainpy-builder)
5. [UE-Side: MelodiaAudioReactivePresentationSubsystem](#5-ue-side-melodiaaudioreactivepresentationsubsystem)
6. [The Cymatic Pipeline](#6-the-cymatic-pipeline)
7. [Practical Exercises](#7-practical-exercises)
8. [References](#8-references)

---

## 1. Blender 5.2 Sample Sound Frequencies Node

The **Sample Sound Frequencies** node is Blender 5.2's first-class Geometry Nodes audio analysis node. It performs FFT analysis on audio data-blocks and outputs amplitude values for driving any GN field.

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `Sound` | Sound data-block | Audio file loaded into Blender (VSE strip or sound data-block) |
| `Time` (seconds) | Float | Sample time in **seconds** (not frames — wire Scene Time → Seconds) |
| `All Channels` / `Channel` | Enum | Mono sum (All Channels = true) or specific channel for stereo cymatics |
| `Low` | Float | Lower Hz bound of the frequency band |
| `High` | Float | Upper Hz bound of the frequency band |
| `FFT Size` | Int | FFT window size: 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768 |
| `Window` | Enum | Window function: Hann, Hamming, Blackman |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `Amplitude` | Float | Summed amplitude for the Hz range at the given time (0.0 to ~1.0+) |

### How to Use

1. **Load audio:** VSE → Add → Sound Strip, or load a sound data-block via the GN interface
2. **Add node:** Geometry Nodes Editor → Add → Utilities → Sound → Sample Sound Frequencies
3. **Wire time:** Use `GeometryNodeInputSceneTime` → `Seconds` output → `Time` input
4. **Set frequency band:** Connect Low/High Hz values (e.g., bass = 20–250 Hz, mids = 250–2000 Hz, highs = 2000–8000 Hz)
5. **Drive fields:** Connect `Amplitude` output to any GN input (Set Position offset, Set Material attribute, etc.)

### Key Gotchas

- **Time is seconds, not frames** — always convert frame to seconds: `time_seconds = frame / fps`
- **All Channels = true** for mono sum; split L/R for stereo cymatic patterns
- **FFT Size tradeoff:** Higher = better frequency resolution, worse temporal resolution
- **Scrub-safe:** Fully procedural — works with timeline scrubbing, no baking required for preview
- **Codec-dependent accuracy:** FFmpeg-backed; lossy codecs (MP3) may show artifacts vs WAV/FLAC

### Melodia Integration Pattern

```python
# From audio_terrain.py — standard band sampling pattern
sample = tree.nodes.new("GeometryNodeSampleSoundFrequencies")
sample.inputs["All Channels"].default_value = True
# Link: Sound → Sound, Time → Time, Low → Low, High → High
# Output: Amplitude → Math(MULTIPLY) → Audio Gain → Set Position.Offset.Z
```

---

## 2. Baking Audio Reactivity for UE Export

Blender's GN audio nodes are **Blender-only** — they do not export to UE. Three bake paths ship audio reactivity to Unreal:

### Path A: Alembic Cache (Animated Geometry)

**Best for:** Hero fabric, terrain, cathedral geometry — anything needing per-vertex motion.

```
GN_MEL_AudioReactive_Fabric → Set Position (audio-driven) → Alembic export
```

- Export: `File → Export → Alembic (.abc)` with frame range matching audio
- UE import: `Geometry Cache` actor plays back animated vertices
- Stores: Per-vertex positions + named attributes (`audio_amplitude`, `frequency_hz`)
- Limitation: Heavy file size; no real-time audio reactivity in UE

### Path B: Image Sequence / Curve Atlas (Texture-Based)

**Best for:** Material-driven reactivity (emissive pulse, UV distortion, WPO amplitude).

```
GN → Compositor File Output OR numpy → EXR sequence → UE Curve Atlas texture
```

- Bake bands to 1px-per-frame image (X = band index, Y = time)
- UE Material samples by time via `Time` node → `TextureCoordinate` UV
- Material function `MF_AudioBand_Sample` reads amplitude per band
- Advantage: Lightweight, real-time, works with MPC-driven materials

### Path C: JSON Curves (Gameplay Triggers)

**Best for:** Music-as-key puzzle, rhythm triggers, gameplay events.

```
bpy.data.actions → F-Curves → Content/Python/BakedAudio/{track}.json
```

- Export per-frame float arrays: `{frame: [band_0, band_1, ..., band_31]}`
- UE: `DataTable` / `CurveFloat` → `UMelodiaAudioReactiveSubsystem` reads for sync
- Used for: Beat triggers, encounter music alignment, wardrobe beat events

### Bake Decision Matrix

| Scenario | Recommended Path |
|----------|-----------------|
| Hero fabric motion | A (Alembic) |
| Emissive/UV pulse | B (Image Sequence) |
| Rhythm gameplay triggers | C (JSON Curves) |
| Multi-band material drive | B + C combined |
| Quick previz | A (fastest to author) |

---

## 3. Audio Tools Comparison

### 3.1 Sample Sound Frequencies (Blender 5.2 Native)

- **Type:** Procedural GN node (live, no bake)
- **Strengths:** Ships in 5.2 LTS, scrub-safe, FFT Size 128–32768, window functions
- **Weaknesses:** Blender-only, no built-in band splitting (one node per band)
- **When to use:** Live authoring, real-time preview, driving GN fields directly
- **Cost:** Free (built-in)

### 3.2 Sound Nodes (negdo)

- **Type:** GN-native spectrum/chromagram analyzer
- **Strengths:** Bakes loudness, beats, spectrogram, chromagram as keyframes; auto-generates GN nodes
- **Weaknesses:** Lite version crippled; last updated 2023-10; 7 open issues
- **When to use:** Cymatic fabric (spectrogram → radial displacement), wardrobe hue (chromagram → palette)
- **Cost:** Lite free, Full paid (Superhive)

### 3.3 Sound Reaktor (Inoshiro/Yatima)

- **Type:** SciPy-powered bake replacement (most powerful)
- **Strengths:** 6 methods (FFT, Onset, RMS, Spectral Centroid, Flatness, Rolloff); 9 presets; Drivers + Keyframes modes; 50–200× faster than native; Pro adds GN + Shader node groups
- **Weaknesses:** Paid (Pro); Lite retired 2026-07-21
- **When to use:** Primary bake path for UE — Drivers mode during authoring, Bake Drivers before export; Sea Above FFT bands → GN Set Position; RMS → emissive pulse; Onset → wardrobe beat triggers
- **Cost:** Pro paid (Superhive Market)

### 3.4 AudVis (example-sk/audvis)

- **Type:** Real-time + MIDI + scriptable
- **Strengths:** Only tool with MIDI alongside spectrum; Sequence Analyzer (VSE) + Realtime Analyzer (mic); Python API for spreading drivers across many objects
- **Weaknesses:** GPL-2.0; 2021 origin; less polished than Sound Reaktor
- **When to use:** Live playtest (Realtime Analyzer → viewport GN); MIDI-driven wardrobe/Resonant World; auto-generating 100s of GN instances via scripting API
- **Cost:** Free (GitHub) + paid market version

### 3.5 Animation Nodes (Legacy Reference)

- **Type:** Legacy GN predecessor (Sound Spectrum node)
- **Strengths:** Cleanest prior art for exposing spectrum as list/field; Attack/Release smoothing
- **Weaknesses:** 2.9–3.x era, NOT updated for 5.2; do not build new graphs
- **When to use:** Reference only — steal API shape for GN builder design; AN Low/High 0-1 normalized → Hz via map_range to Sample Sound Frequencies
- **Cost:** Free (legacy)

### Summary Table

| Tool | Live | Bake | MIDI | Cost | UE Export | Best For |
|------|------|------|------|------|-----------|----------|
| Sample Sound Frequencies | ✅ | ❌ | ❌ | Free | Via bake | Live GN authoring |
| Sound Nodes | ✅ | ✅ | ❌ | Free/Paid | Alembic/JSON | Cymatic fabric, chromagram |
| Sound Reaktor | ✅ | ✅ | ❌ | Paid | Alembic/JSON | Primary UE bake path |
| AudVis | ✅ | ✅ | ✅ | Free/Paid | Alembic | Live playtest, MIDI sync |
| Animation Nodes | ✅ | ❌ | ❌ | Free | N/A | Legacy reference only |

---

## 4. The audio_terrain.py Builder

**Location:** `deploy/surreal_arch/melodia_gn/audio_terrain.py`

### How It Works

The module defines three registered GN builders using Blender 5.2's `GeometryNodeSampleSoundFrequencies`:

| Builder | ID | Purpose |
|---------|----|---------|
| Audio Spectrum Terrain | `MEL_audio_spectrum_terrain` | Continuous walkable terrain displaced by frequency energy |
| Audio Spectrum Towers | `MEL_audio_spectrum_towers` | Frequency-bin mesh city/wall generator |
| Audio Radial Field | `MEL_audio_radial_field` | Concentric audio-reactive membrane for arenas |

### Architecture

```
Sound Input → Sample Sound Frequencies → Amplitude
    ↓
Map Range (position X → Hz band)
    ↓
Audio Gain × Height → Set Position (Z offset)
    ↓
Store Named Attribute (audio_amplitude, frequency_hz)
    ↓
Universal Music Pass → Output
```

### Key Functions

- **`_add_sound_param(tree)`** — Adds `Sound` interface socket (NodeSocketSound)
- **`_sample_band(tree, gin, loc, low, high)`** — Creates Sample Sound Frequencies node, wires Sound/Time/Low/High, returns Amplitude
- **`_map_frequency(tree, gin, position, loc)`** — Maps position X to Hz band via SeparateXYZ → MapRange → Math
- **`_audio_inputs(tree)`** — Adds standard inputs: Time, Low Hz, High Hz, Band Width, Audio Gain
- **`_store_float(tree, geometry, name, value, loc)`** — Stores named attribute for UE export

### How to Extend

1. **Add a new builder:** Define `build_*()` function, call `_audio_inputs(tree)`, use `_sample_band()` for frequency analysis, end with `register_builder()`
2. **Add new frequency bands:** Call `_sample_band()` multiple times with different Low/High ranges
3. **Add stereo support:** Set `All Channels = False`, use `Channel` input for L/R separation
4. **Add radial patterns:** Use `_map_frequency()` with `ShaderNodeVectorMath(LENGTH)` for distance-based mapping
5. **Export attributes:** Use `_store_float()` to bake `audio_amplitude`, `frequency_hz` for Alembic/USD

### Example: Adding a Fabric Builder

```python
def build_audio_fabric(group_name="MEL_audio_fabric"):
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs(tree)
    add_float_param(tree, "Fabric Width", 10.0, 1.0, 100.0)
    add_int_param(tree, "Segments", 128, 16, 1024)
    
    grid = safe_node(tree, "GeometryNodeMeshGrid", (-900, 120))
    # ... wire segments/width ...
    
    # Bass band → vertical displacement
    bass_amp = _sample_band(tree, gin, (-80, -80), 
                            gin.outputs["Low Hz"],   # 20 Hz
                            250.0)                    # 250 Hz
    # ... gain, set position, store attributes ...
    
    register_builder(group_name, build_audio_fabric, 
                     "Audio Fabric", "Audio-reactive fabric panel", "music")
```

---

## 5. UE-Side: MelodiaAudioReactivePresentationSubsystem

**Location:** `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.h/.cpp`

### Role

**Sole writer** of `MPC_Melodia_Palette` — the single authority that publishes audio-reactive values to materials, Niagara, and Oceanology surfaces. Presentation-only; never owns combat, gameplay audio, or input.

### What It Writes (Per Tick)

| Parameter | Source | Consumer |
|-----------|--------|----------|
| `BeatPulse` | `cos²(BeatPhase × π)` | Materials, Niagara, Oceanology |
| `BeatPhase` | Music clock phase | Phase-locked effects |
| `BeatIntensity` | Same as BeatPulse | Alias for clarity |
| `Bass` | Battle intensity (gated) | Battle-only materials |
| `BassIntensity` | Alias of Bass | Cymatics subsystem |
| `Mid` | Impact pulse | Transient effects |
| `MidIntensity` | Alias of Mid | Cymatics subsystem |
| `Treble` | BeatPulse | High-frequency effects |
| `GlobalReactivity` | Battle active? intensity : 0 | Master reactivity gate |
| `BeatTracker` | Latch of current beat pulse | Beat-synced systems |

### Niagara Mirror

Writes identical values to `NPC_Melodia_Palette` (Niagara cannot read MPCs). Also publishes rhythm-specific values from `UMelodiaRhythmReactivitySubsystem::GetSignal()`:

- `ComboNormalized`, `CrescendoNormalized`, `CommandEnergy`, `RhythmPulse`, `BreakPulse`, `VictoryPulse`, `EnemyTension`

### Oceanology Drive

Creates dynamic material instances for Oceanology actors and writes:
- `PhaseGLow` = 0.75 + BeatPulse × 0.75
- `HighlightBoost` = 10.0 + BeatPulse × 10.0
- `ScatterBoost` = 10.0 + CombatEnergy × 5.0
- `Biolum_Intensity` = 1.0 + BeatPulse × 1.5
- `DeepScatteringColor` shifted by ImpactPulse

### Tick Flow

```
1. Read UMelodiaMusicClockSubsystem → BeatPhase, BPM
2. On beat wrap (BeatPhase < LastBeatPhase) → NotifyBeat() → RhythmReactivity subsystem
3. Decay ImpactPulse
4. Compute BeatPulseValue = cos²(BeatPhase × π)
5. Write MPC_Melodia_Palette scalars
6. Write alias lanes (BassIntensity, MidIntensity, BeatTracker)
7. Drive Oceanology MIDs (game worlds only)
8. Write NPC_Melodia_Palette (Niagara mirror)
9. Read RhythmReactivity signal → write rhythm params to NPC
```

### Single-Writer Contract

**Never add a second writer.** `UMelodiaAudioReactivePresentationSubsystem` is the ONLY code that writes `MPC_Melodia_Palette`. `UMelodiaCymaticsWriterSubsystem` writes `MPC_Cymatics_Driver`. `UMelodiaCymaticsSubsystem` is read-only.

---

## 6. The Cymatic Pipeline

### Overview

```
Audio (Bass/Mid/Beat)
    ↓
UMelodiaAudioReactivePresentationSubsystem (MPC_Melodia_Palette)
    ↓
UMelodiaCymaticsSubsystem (READ-ONLY)
    ↓
Chladni Standing-Wave Pattern
    ↓
World Field Bus (Resonance / Tension)
    ↓
Consumers: Materials, Niagara, PCG, Vegetation
```

### Chladni Eigenmode Math

The cymatic pattern is a **Chladni standing-wave plate**:

```
amp(u,v) = cos(n·π·u) · cos(m·π·v) − cos(m·π·u) · cos(n·π·v)
```

Where:
- `u, v ∈ [0, 1]` — normalized plate coordinates
- `n, m` — mode indices driven by audio bands:
  - `ModeN = clamp(2 + floor(Bass × 6), 1, 8)`
  - `ModeM = clamp(3 + floor(BeatPulse × 5), 1, 8)`
- Final amplitude: `amp × max(BeatPulse, 0.15)` (floor prevents zero-field)

### World Field Bus

**Location:** `Source/BS_GodFile/MelodiaIntegration/MelodiaWorldFieldBus.h`

The `UWorldFieldBus` publishes cymatic output as shared spatial fields:

| Field | Source | Semantic |
|-------|--------|----------|
| `Resonance.N` | Chladni ModeN | Standing-wave harmonic signature |
| `Resonance.M` | Chladni ModeM | Cross-mode index |
| `Tension` | `|amp(0.5, 0.5)|` | Pattern pull strength at center |
| `BeatPulse` | Mirrored from MPC | Beat intensity passthrough |

### Publish Call

```cpp
// From MelodiaCymaticsSubsystem::RefreshFromMPC()
const float TensionAtCenter = FMath::Abs(SampleCymaticAmplitude(0.5f, 0.5f));
UWorldFieldBus::PublishResonance(ModeN, ModeM, TensionAtCenter, BeatPulse);
```

### Consumer Chain

```
WorldFieldBus::PublishResonance()
    ↓
UWorldFieldBus::LastPublished (static)
    ↓
Consumers:
  - Materials: WPO_Resonance_Scale, Iridescence, UVDistortion
  - Niagara: particle placement, emission rate
  - PCG: scatter density, vegetation growth (Tension > 0.5 → VegetationGrowth)
  - Water: SampleCymaticRipple() → height-aware water vs fog
```

### Read-Only Contract

`UMelodiaCymaticsSubsystem::IsReadOnlyByContract() = true` — it READS `MPC_Melodia_Palette` and converts to Chladni patterns. It never writes MPC. This is the **single-writer + read-only consumer** pattern enforced across Melodia.

---

## 7. Practical Exercises

### Exercise 1: Create an Audio-Reactive Fabric

**Goal:** Build a fabric panel that ripples with bass and shimmers with highs.

**Steps:**

1. **Create the GN tree:**
   ```
   Group Input → Grid Mesh (128×128 segments, 10m × 10m)
   ↓
   Sample Sound Frequencies (Low=20, High=250) → Bass Amplitude
   Sample Sound Frequencies (Low=2000, High=8000) → Treble Amplitude
   ↓
   Bass Amplitude × 2.0 → Set Position.Z (vertical ripple)
   Treble Amplitude × 0.5 → Store Named Attribute (emissive_treble)
   ↓
   Group Output
   ```

2. **Add to audio_terrain.py:**
   ```python
   def build_audio_fabric(group_name="MEL_audio_fabric"):
       tree, gin, gout = new_geometry_tree(group_name)
       _audio_inputs(tree)
       add_float_param(tree, "Fabric Size", 10.0, 1.0, 100.0)
       add_int_param(tree, "Segments", 128, 16, 1024)
       add_float_param(tree, "Bass Height", 2.0, 0.0, 50.0)
       add_float_param(tree, "Treble Emissive", 0.5, 0.0, 10.0)
       
       grid = safe_node(tree, "GeometryNodeMeshGrid", (-900, 120))
       link_sockets(tree, gin.outputs["Fabric Size"], grid.inputs["Size X"])
       link_sockets(tree, gin.outputs["Fabric Size"], grid.inputs["Size Y"])
       link_sockets(tree, gin.outputs["Segments"], grid.inputs["Vertices X"])
       link_sockets(tree, gin.outputs["Segments"], grid.inputs["Vertices Y"])
       
       # Bass → vertical displacement
       bass = _sample_band(tree, gin, (-80, -80), 
                           gin.outputs["Low Hz"], 250.0)
       bass_gain = safe_node(tree, "ShaderNodeMath", (120, -80))
       bass_gain.operation = "MULTIPLY"
       link_sockets(tree, bass, bass_gain.inputs[0])
       link_sockets(tree, gin.outputs["Bass Height"], bass_gain.inputs[1])
       
       # Treble → emissive attribute
       treble = _sample_band(tree, gin, (-80, -200), 2000.0, gin.outputs["High Hz"])
       treble_gain = safe_node(tree, "ShaderNodeMath", (120, -200))
       treble_gain.operation = "MULTIPLY"
       link_sockets(tree, treble, treble_gain.inputs[0])
       link_sockets(tree, gin.outputs["Treble Emissive"], treble_gain.inputs[1])
       
       offset = safe_node(tree, "ShaderNodeCombineXYZ", (300, -80))
       link_sockets(tree, bass_gain.outputs[0], offset.inputs["Z"])
       
       set_pos = safe_node(tree, "GeometryNodeSetPosition", (480, 100))
       link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
       link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])
       
       geom = _store_float(tree, set_pos.outputs["Geometry"], 
                          "audio_amplitude", bass_gain.outputs[0], (680, 100))
       geom = _store_float(tree, geom, 
                          "emissive_treble", treble_gain.outputs[0], (880, 100))
       geom = apply_universal_music_pass(tree, gin, geom, (1080, 100))
       link_sockets(tree, geom, gout.inputs["Geometry"])
       return label_tree(tree, group_name, [
           {"title": "Bass Ripple", "nodes": ("sample", "set position"), "role": "geometry"},
           {"title": "Treble Emissive", "nodes": ("store",), "role": "attribute"},
       ])
   
   register_builder("MEL_audio_fabric", build_audio_fabric,
                    "Audio Fabric", "Bass-rippled, treble-shimmer fabric panel", "music")
   ```

3. **Bake for UE:**
   - Path A: Alembic export → Geometry Cache actor
   - Path B: Store named attribute → material reads `emissive_treble` via `Vertex Color` or `Custom Data`

4. **Verify in UE:**
   - Fabric ripples on bass hits
   - Emissive shimmer on high-frequency content
   - `audio_amplitude` attribute drives WPO in material

---

### Exercise 2: Create a Music-Driven Particle System

**Goal:** Particles emit on beat, colored by frequency band, positioned by Chladni pattern.

**Steps:**

1. **Bake frequency data to JSON:**
   ```python
   import bpy
   import json
   
   # After Sound Reaktor bake or GN simulation
   track = "melodia_hero_theme"
   fps = 24
   frame_start = 1
   frame_end = 720  # 30 seconds
   
   bands = ["bass", "mid", "treble"]
   data = {}
   
   for frame in range(frame_start, frame_end + 1):
       bpy.context.scene.frame_set(frame)
       # Read from GN evaluated values or F-Curves
       data[frame] = {
           "bass": bpy.data.actions["audio_bass"].fcurves[0].evaluate(frame),
           "mid": bpy.data.actions["audio_mid"].fcurves[0].evaluate(frame),
           "treble": bpy.data.actions["audio_treble"].fcurves[0].evaluate(frame),
           "beat": 1.0 if is_beat(frame, fps) else 0.0
       }
   
   with open(f"Content/Python/BakedAudio/{track}.json", "w") as f:
       json.dump({"fps": fps, "bands": bands, "frames": data}, f)
   ```

2. **Create UE DataTable:**
   - Import JSON as `DA_AudioBands_{track}` (Float Curve)
   - Or use `UCurveFloat` per band

3. **Niagara System Setup:**
   - Emitter: `NS_Melodia_AudioParticles`
   - Spawn Rate: driven by `NPC_Melodia_Palette.BeatPulse` (burst on beat)
   - Particle Color: 
     - Bass → deep blue/purple
     - Mid → magenta/pink
     - Treble → white/cyan
   - Position: Sample `UWorldFieldBus::SampleResonanceTension()` for Chladni distribution

4. **Material-driven approach (no Niagara):**
   - Use `UMelodiaCymaticsSubsystem::SampleCymaticAmplitude(U,V)` for particle placement
   - `Tension > 0.5` → spawn particle at that UV position
   - Color from `ModeN/ModeM` → hue shift

5. **Blueprint integration:**
   ```cpp
   // In Tick or Event Graph:
   if (UMelodiaCymaticsSubsystem* Cymatics = 
       GetGameInstance()->GetSubsystem<UMelodiaCymaticsSubsystem>())
   {
       float Pulse = Cymatics->GetBeatPulse();
       if (Pulse > 0.8f) {
           // Spawn particle burst
           int32 N, M;
           Cymatics->GetCymaticMode(N, M);
           // Position by Chladni UV
           float Amp = Cymatics->SampleCymaticAmplitude(U, V);
       }
   }
   ```

6. **Validation:**
   - Particles emit on beat (not randomly)
   - Color shifts with frequency content
   - Pattern matches Chladni standing-wave nodes
   - No second writer — all values from `MPC_Melodia_Palette` / `NPC_Melodia_Palette`

---

## 8. References

- **Research Report:** `Docs/Research/BLENDER_AUDIO_GEOMETRY_NODES_PIPELINE_2026-09-02.md`
- **Builder Source:** `deploy/surreal_arch/melodia_gn/audio_terrain.py`
- **Core Utilities:** `deploy/surreal_arch/melodia_gn/core.py`
- **UE Audio Subsystem:** `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.h/.cpp`
- **UE Cymatics Subsystem:** `Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsSubsystem.h/.cpp`
- **World Field Bus:** `Source/BS_GodFile/MelodiaIntegration/MelodiaWorldFieldBus.h`
- **Single-Writer Contract:** `Docs/Art/UNIVERSAL_GARMENT_SYSTEM_MASTER_SPEC_2026-09-02.md`
- **Cymatic Pipeline:** `Docs/Art/CYMATIC_GARMENT_NIKKI_PIPELINE_2026-09-02.md`
- **AAA Audit:** `Docs/AAA_AUDIT_2026-09-02.md`
- **Emerging Toolchain Index:** `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md`

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                  AUDIO-REACTIVE PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│ BLENDER 5.2                                                     │
│   Sound → Sample Sound Frequencies → Amplitude → GN Field      │
│   Bands: Bass 20-250Hz | Mid 250-2kHz | Treble 2k-8kHz        │
├─────────────────────────────────────────────────────────────────┤
│ BAKE PATHS                                                      │
│   A: Alembic (.abc) → Geometry Cache (hero fabric)             │
│   B: Image Sequence → Curve Atlas → Material (emissive/UV)     │
│   C: JSON Curves → DataTable → Gameplay (rhythm triggers)      │
├─────────────────────────────────────────────────────────────────┤
│ UE 5.8                                                          │
│   MelodiaAudioReactivePresentationSubsystem (SOLE WRITER)      │
│     → MPC_Melodia_Palette (materials)                          │
│     → NPC_Melodia_Palette (Niagara)                            │
│     → Oceanology MIDs (water surface)                          │
│   MelodiaCymaticsSubsystem (READ-ONLY)                         │
│     → Chladni amp = cos(nπu)cos(mπv) − cos(mπu)cos(nπv)      │
│     → WorldFieldBus.PublishResonance(N, M, Tension, Beat)      │
├─────────────────────────────────────────────────────────────────┤
│ CONTRACT                                                        │
│   Single writer: AudioReactivePresentationSubsystem             │
│   Read-only: CymaticsSubsystem, Materials, Niagara, PCG        │
│   Never add a second MPC writer.                                │
└─────────────────────────────────────────────────────────────────┘
```
