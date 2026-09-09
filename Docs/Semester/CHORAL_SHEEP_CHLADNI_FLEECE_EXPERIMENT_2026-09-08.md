# Choral Sheep — Chladni Fleece Experiment

**Status:** LOCKED — Capstone 01 Technical-Art Experiment A  
**Date:** 2026-09-08  
**Capstone:** Choral Sheep — Harmonic Ecology Prototype  
**Presentation spine:** Creature → Motif → Harmony → World

## 1. Locked idea

When a Choral Sheep enters Harmonize, its musical identity becomes visible **inside the wool**.

The fleece does not simply glow to audio amplitude. It organizes into a pitch-linked Chladni / standing-wave pattern that appears woven beneath or through the wool.

One sheep produces one readable resonant pattern.

Multiple sheep in harmony share one coherent harmonic field.

The field can then extend outward into the surrounding Resonant World.

Core visual progression:

```text
quiet fleece
→ sheep harmonizes
→ pitch-linked pattern emerges
→ second sheep answers
→ interference relationship appears
→ third sheep resolves the chord
→ flock patterns synchronize
→ same resonance language spreads into water / reef / pearl environment
```

The first hero chord is:

**C → E → G**

## 2. Why this is the capstone's first technical experiment

Chladni Fleece connects the project's existing systems without inventing another authority:

- Choral Sheep already carries musical motif identity;
- pitch class is already the variant axis;
- Harmonize is already an authored companion interaction;
- Melodia already has a read-only cymatics / World Field language;
- materials already consume resonance/tension-like presentation data;
- TouchDesigner already exists as a music-analysis / visual-presentation lane;
- Unreal remains the authored world and final game renderer;
- After Effects can explain the pipeline without faking implementation.

The result is easy to communicate:

> **The harmonic state of a companion flock becomes a cymatic field that drives character materials and environmental presentation.**

## 2.5 Existing implementation this experiment extends

This experiment is deliberately **an application of existing Melodia infrastructure**.

### Already implemented / source-present

- `UMelodiaRhythmReactivitySubsystem`
  - publishes the existing `FMelodiaRhythmReactivitySignal`;
  - sends UE→TD OSC on `127.0.0.1:9000`;
  - already publishes `/rhythm/beat_pulse`, `/rhythm/beat_phase`, combo, crescendo, command energy, victory, tension, dread, and dissonance;
  - already exposes `RegisterReactiveMeshComponent(UPrimitiveComponent*)` and pushes `DreamPulseAmp`, `Iridescence`, `TemporalStrength`, and `ParallaxStrength` into registered MIDs.

- `UMelodiaReactiveMeshRegistrar`
  - scans actors tagged `ReactiveToMusic`;
  - registers visible primitive components with the reactivity subsystem.

- `UMelodiaAudioReactivePresentationSubsystem`
  - owns the continuous music-clock-derived beat namespace in `MPC_Melodia_Palette`;
  - writes the Niagara-side twin;
  - already drives Oceanology water presentation from the same beat data.

- `UMelodiaCymaticsSubsystem`
  - already computes Chladni standing-wave amplitude from the canonical audio palette;
  - is explicitly read-only.

- `UMelodiaCymaticsWriterSubsystem`
  - already maps BeatPulse/Bass/Mid into `Cymatic_ModeN`, `Cymatic_ModeM`, emissive, iridescence shift, and UV distortion in `MPC_Cymatics_Driver`.

- TouchDesigner
  - active project: `_TouchDesigner/grandmaster_melodia/grandmaster_melodia7.22.toe`;
  - `wire_audio_reactive_flower.py` already builds a CHOP audio-analysis network and OSC mapping;
  - TD→UE audio bands and UE→TD beat/phase routes already exist;
  - loopback validation previously recorded 38 pass / 0 fail in the audio-reactive flower handoff.

### Therefore the actual missing delta

Chladni Fleece does **not** need a new global bridge.

It needs:

1. Choral Sheep-specific pitch/harmony presentation fields;
2. one fleece material consumer/profile;
3. a TD Chladni field network that plugs into the existing grandmaster project;
4. deterministic replay for final capture;
5. one optional world-propagation consumer.

This is a consumer specialization problem, not an infrastructure problem.

## 3. Authority boundary

This experiment is **presentation-only**.

It may read:

- pitch class;
- amplitude;
- beat phase / beat pulse;
- Harmonize state;
- motif phase;
- harmony-group state;
- read-only cymatic resonance/tension;
- presentation-strength scalars.

It may drive:

- wool material masks;
- subtle wool WPO / shell displacement;
- emissive / sheen;
- bell / trim response;
- TouchDesigner halos / pitch constellations;
- water-light;
- environmental material response;
- presentation-only procedural visualization.

It must not:

- decide whether a chord is valid;
- grant rewards;
- write save state;
- recruit a companion;
- move the player;
- complete a quest;
- become a second gameplay music authority.

Where canonical runtime harmony exists, presentation consumes it.

Where the first prototype uses a fixed C/E/G test, documentation must call that a **presentation fixture**, not runtime harmony proof.

## 4. Existing cymatics relationship

Melodia already uses:

- `UMelodiaCymaticsSubsystem` as a read-only Chladni/cymatic evaluator;
- `WorldField.Resonance` for standing-wave harmonic signature;
- `WorldField.Tension` for field pull/strength;
- downstream presentation consumers rather than direct gameplay coupling.

Chladni Fleece should follow the same pattern.

Preferred conceptual data flow:

```text
canonical music / companion presentation state
                ↓
       read-only resonance description
                ↓
       TouchDesigner visualization
          + Unreal material consumer
                ↓
  fleece / bell / halo / water / reef response
```

Do not introduce a second cymatics subsystem for the sheep.

## 5. Visual design

The fleece should feel like **hidden embroidery revealed by song**.

Preferred language:

- pearl-on-pearl value change;
- iridescent seam emergence;
- fine standing-wave lines;
- soft woven filigree;
- subtle local fleece lift;
- low-frequency shape first, micro-detail second;
- controlled sheen / emissive;
- pattern strongest near body mass, softer at fleece boundary.

Avoid:

- full-surface neon;
- rainbow spectrum mapping;
- generic audio visualizer bars;
- aggressive displacement spikes;
- noisy high-frequency shimmer everywhere;
- patterns that erase the sheep's face/silhouette.

At rest, the sheep must still read as a beautiful creature rather than a shader demo.

## 6. Prototype A — One sheep / one note

### Target

One Choral Sheep, fixed pitch class C.

Sequence:

1. Idle/rest baseline.
2. Harmonize begins.
3. C resonance fades in.
4. Fleece pattern becomes visible.
5. Bell/trim gains a small supporting response.
6. Amplitude changes intensity, not pattern identity.
7. Beat phase produces a restrained breathing/pulse.
8. Harmonize ends.
9. Pattern decays cleanly to baseline.

### Minimum signals

```text
pitch_class = C
harmonize_active
amplitude
beat_phase
beat_pulse
motif_phase
resonance_strength
```

### Pass condition

A viewer should be able to understand:

> the sheep sang, and its wool organized into a musical pattern.

No technical labels should be necessary.

## 7. Prototype B — C + E + G

Three sheep form the core capstone harmony.

Each sheep remains individually identifiable by pitch class, but their fleece should not look like three unrelated shaders.

Preferred model:

- each sheep has its own local pitch basis;
- one shared chord/harmony field influences all three;
- shared field phase/tension creates family resemblance;
- local sampling / offset preserves individuality;
- resolved harmony stabilizes the field;
- unresolved harmony may remain slightly asymmetric/unstable.

Sequence:

```text
C active
→ E joins
→ shared field becomes more complex
→ G joins
→ harmony_resolved
→ field stabilizes
→ all three fleece patterns visibly synchronize
```

The important visual event is not “more glow.”

It is:

> **the patterns become more ordered together.**

## 8. Prototype C — World propagation

Once the three-sheep proof reads:

Reuse the same resonance language in one nearby world response.

First candidates:

1. water beneath flock shows matching standing-wave pattern;
2. pearl grass / reef emissive aligns to nodal structure;
3. pearl filigree / route geometry appears on nodal lines;
4. Starskiff mooring receives a low-amplitude answering pulse.

Do only one first.

The environment response must feel causally connected to the flock.

## 9. TouchDesigner role

TouchDesigner should generate and/or visualize the field deterministically.

Recommended network:

```text
/choral_sheep_capstone/chladni_fleece
  /input_replay
  /pitch_modes
  /field_solver
  /harmonic_mix
  /pattern_grade
  /fleece_mask
  /world_mask
  /debug
  /record
```

Outputs:

```text
OUT_FLEECE_C
OUT_FLEECE_E
OUT_FLEECE_G
OUT_SHARED_HARMONY_FIELD
OUT_WORLD_FIELD
OUT_DEBUG
```

The final render path should use replay data, not depend on a perfect live OSC take.

## 10. Unreal material role

Unreal remains responsible for making the result belong to the actual game asset.

Preferred material consumers:

- mask intensity;
- mask scale / phase;
- subtle WPO or shell lift;
- emissive;
- sheen / roughness modulation;
- bell/trim accent.

Do not require destructive mesh changes.

The first proof should be achievable as a reversible material/presentation layer on the approved sheep asset.

## 11. After Effects breakdown

The experiment gets one clear breakdown sequence:

```text
A. plain sheep beauty
B. pitch / harmony replay values
C. TouchDesigner field
D. Unreal fleece material mask
E. final sheep
F. three-sheep resolved harmony
G. world response
```

Suggested caption:

**MUSICAL STATE → CYMATIC FIELD → FLEECE + WORLD**

Do not show a node wall without first showing the final result.

## 12. Evidence package

Store working evidence under:

`Saved/SemesterEvidence/2026-W37/ChoralSheep/ChladniFleece/`

Target captures:

- `CF_A01_IDLE.png`
- `CF_A02_C_HARMONIZE.png`
- `CF_A03_C_FIELD.png`
- `CF_B01_CE_UNRESOLVED.png`
- `CF_B02_CEG_RESOLVED.png`
- `CF_B03_FLOCK_SYNC.png`
- `CF_C01_WORLD_RESPONSE.png`
- `CF_BREAKDOWN_TD_FIELD.png`
- `CF_BREAKDOWN_UE_MASK.png`

## 13. Scope ladder

### LOCKED P0

**one sheep + C + visible Chladni Fleece**

### LOCKED P1

**C + E + G + synchronized resolved field**

### P2

**one environment propagation response**

### Stretch

- twelve pitch-class Chladni atlas;
- unique mode families per sheep;
- full chromatic flock;
- traversal geometry grown on nodal lines;
- deeper live-performance mode.

Do not start stretch work until P1 photographs beautifully.

## 14. First build question

The first implementation question is intentionally narrow:

> **Can one pitch-stable, amplitude-responsive Chladni mask look beautiful when integrated into the current Choral Sheep wool material without damaging the creature silhouette?**

If no, solve the material/art problem before adding multiple sheep or world response.

## 15. Success definition

Chladni Fleece succeeds when:

- it reads as part of the sheep, not an overlay pasted on top;
- pitch identity affects pattern structure;
- amplitude affects strength;
- timing affects pulse/phase;
- C/E/G visibly converge into a shared harmonic state;
- the same language can extend to one environment response;
- final replay is deterministic;
- no new gameplay/save authority was created;
- a professor can understand the final effect before seeing the technical breakdown.
