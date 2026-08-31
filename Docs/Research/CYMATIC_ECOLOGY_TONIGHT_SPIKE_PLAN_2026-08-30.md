# Cymatic Ecology — Tonight Integration Spike Plan

**Date:** 2026-08-30  
**Project:** Melodia Melusina / Unreal Engine 5.8  
**Status:** TONIGHT SPIKE / presentation-only R&D  
**Primary target:** `LV_RND_CymaticEcology`  
**Hard rule:** no new rhythm/combat authority, no production-map migration, no edits to frozen master materials.

---

# 1. Goal

Build the smallest convincing version of a Melodia-specific effect where rhythm judgement becomes visible as **physical coherence in the environment**.

The desired read is not “music visualizer.” It is:

> The world appears to contain a hidden mathematical/ecological nervous system, and music briefly makes it legible.

A judged note emits a field impulse. Recent impulses interfere. Good timing produces clean standing-wave geometry; worse timing introduces phase error and destructive interference. Niagara particles and lightweight presentation materials reveal the resulting nodes.

This must remain presentation-only. Gameplay/rhythm authority stays in `UMelodiaRhythmCombatSubsystem`.

---

# 2. Existing project seam to use

Current project code already exposes:

```cpp
FMelodiaLaneHitJudged OnLaneHitJudged;
```

with:

```text
LaneIndex
Grade
TimingErrorMs
```

The subsystem explicitly documents this as per-press, presentation-only output. This is the correct seam.

**Do not:**

- add another rhythm timer;
- recompute grading;
- change damage/session logic;
- feed VFX state back into rhythm combat;
- create a duplicate music clock.

---

# 3. Architecture

```text
UMelodiaRhythmCombatSubsystem
        |
        | OnLaneHitJudged
        v
BP_MelodiaCymaticPresentationBridge
        |
        | write one rhythm impulse
        v
NDC_MelodiaRhythmPulse
        |
        +------------------+
        |                  |
        v                  v
NS_Melodia_CymaticDust   Cymatic field presentation
Niagara particles         material/plane/volume
        |                  |
        +---------+--------+
                  v
            visible nodes
```

UE5.8 Niagara Data Channels are the preferred transport because Epic documents them specifically for communication between game code/Blueprint and Niagara systems and between Niagara systems.

**Primary Epic references:**

- https://dev.epicgames.com/documentation/unreal-engine/data-channels-in-niagara-for-unreal-engine
- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/Niagara/UNiagaraDataChannelAsset
- https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/Niagara/UNiagaraDataChannelLibrary

---

# 4. Asset plan

Create only isolated R&D assets first.

```text
/Game/Melodia/RND/CymaticEcology/
  Maps/
    LV_RND_CymaticEcology
  DataChannels/
    NDC_MelodiaRhythmPulse
  Blueprints/
    BP_MelodiaCymaticPresentationBridge
  Niagara/
    NS_Melodia_CymaticDust
    NE_Melodia_CymaticDust_GPU
  Materials/
    M_RND_CymaticField
    MI_RND_CymaticField
  Geometry/
    SM_RND_CymaticFieldPlane
```

Do not touch existing frozen water or toon masters for the first pass.

---

# 5. Data Channel payload

`NDC_MelodiaRhythmPulse` v0 should stay intentionally primitive and easy to inspect.

```text
PositionWS       : Vector3
LaneIndex        : Int32
GradeOrdinal     : Int32
GradeAmplitude   : Float
TimingErrorMs    : Float
PhaseOffset      : Float
WorldTimeSeconds : Float
PulseId          : Int32
```

Recommended presentation mapping:

```text
Perfect -> 1.00 amplitude, minimal phase noise
Great   -> 0.82 amplitude, low phase noise
Good    -> 0.58 amplitude, moderate phase noise
Miss    -> 0.18 amplitude, strong destructive phase perturbation
```

These values are presentation constants, not gameplay rules.

### Lane-to-frequency canary

Use four deliberately simple ratios first:

```text
Lane 0 -> 1.00
Lane 1 -> 1.25
Lane 2 -> 1.50
Lane 3 -> 2.00
```

Do not over-musicalize the mapping until the visual read works.

---

# 6. First field implementation — analytic, not simulation

Do **not** begin with Grid2D, FluidNinja, or a custom solver.

For the first visual, keep the latest 4 impulses and evaluate a simple interference field analytically in one R&D material:

```text
W(P) = sum_i A_i * sin(k_i * distance(P, Origin_i) + Phase_i)
```

Then derive:

```text
node_mask = 1 - saturate(abs(W) * NodeSharpness)
crest_mask = smoothstep(CrestMin, CrestMax, abs(W))
```

Use `node_mask` to reveal:

- emissive lace/ripples;
- opacity breakup;
- thin rose-window-like bands;
- optional normal distortion.

This gives a visible result without committing to a persistent field solver.

---

# 7. Timing-error visual language

The point of the effect is that timing becomes physical coherence.

Recommended mapping:

```text
PhaseOffset = TimingErrorMs * PhaseScale
```

Then:

- **Perfect:** symmetric/clean nodes, long persistence.
- **Great:** nearly stable nodes with subtle drift.
- **Good:** broader/fuzzier nodes, visibly unstable interference.
- **Miss:** local destructive interference / brief fracture.

The exact constants are aesthetic and should be tuned by fixed-camera captures, not guessed from vendor examples.

---

# 8. Niagara particle consumer

Create `NS_Melodia_CymaticDust` as the first ecological reader.

## v0 behavior

Particles:

- spawn sparsely around the player and field plane;
- read the latest rhythm pulses through the Data Channel;
- calculate the same analytic wave approximation or a simplified attractor value;
- bias velocity toward low-|W| node regions;
- increase emissive/scale near nodes;
- decay gently after the last pulse.

The first pass does **not** need a true gradient solver. A finite-difference approximation or simple local sample pair is enough if it creates the visual read.

## v1 only if v0 wins

Move the field into Niagara Grid2D / Simulation Stages for persistent node deposition and richer ecology response.

Epic UE5.8 documents Grid2D/Grid3D as named-attribute storage used by Niagara fluid computation and Simulation Stages as advanced GPU passes that can run sequentially/iteratively.

References:

- https://dev.epicgames.com/documentation/en-us/unreal-engine/fluid-simulation-in-unreal-engine---overview
- https://dev.epicgames.com/documentation/en-us/unreal-engine/key-concepts-in-niagara-effects-for-unreal-engine

---

# 9. Optional material synchronization

If the Niagara/Data Channel path needs to drive non-Niagara materials, use a small dedicated `MaterialParameterCollection` rather than editing dozens of instances.

Potential:

```text
MPC_MelodiaCymatic
  Pulse0_PosAmp
  Pulse1_PosAmp
  Pulse2_PosAmp
  Pulse3_PosAmp
  Pulse0_PhaseFreq
  ...
```

But do not build this unless the first Data Channel/Niagara pass requires it.

UE5.8 supports Material Parameter Collections as shared scalar/vector parameters across materials, and Niagara Parameter Collections can reference an MPC.

References:

- https://dev.epicgames.com/documentation/unreal-engine/using-material-parameter-collections-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/Niagara/UNiagaraParameterCollection

---

# 10. Tonight execution sequence

## C0 — static visual canary — 20 min

- [ ] Create `LV_RND_CymaticEcology`.
- [ ] Add one flat/simple test surface above quiet water or neutral floor.
- [ ] Create `M_RND_CymaticField` with four manually-set pulse positions/frequencies.
- [ ] Produce visible interference bands.
- [ ] Capture fixed camera screenshot.

**Stop condition:** if the pattern does not look unmistakably intentional at a glance, tune this before any event wiring.

## C1 — rhythm event bridge — 30 min

- [ ] Create `NDC_MelodiaRhythmPulse`.
- [ ] Create `BP_MelodiaCymaticPresentationBridge`.
- [ ] Bind once to `OnLaneHitJudged`.
- [ ] Write one event per judged press.
- [ ] Log pulse id / lane / grade / timing error in R&D only.
- [ ] Verify no duplicate bindings after PIE restart.

**Pass:** one press -> exactly one pulse record.

## C2 — live field response — 30 min

- [ ] Maintain latest 4 pulses presentation-side.
- [ ] Update the R&D field material or Niagara-readable state.
- [ ] Verify lane changes wavelength.
- [ ] Verify `TimingErrorMs` changes phase, not gameplay.
- [ ] Verify Miss visibly de-coheres the field.

## C3 — particle ecology — 30–45 min

- [ ] Add pearl dust / pollen.
- [ ] Bias particles toward nodes.
- [ ] Keep GPU cost visible in Niagara profiler.
- [ ] Capture 10-second Perfect-streak and Miss clips.

## C4 — musical path waveguide — OPTIONAL

Use one existing Musical Dream piano-roll spline/path as a visual waveguide.

- [ ] propagate pulse position along spline distance;
- [ ] do not modify walkability or gameplay collision;
- [ ] use only presentation components/instances;
- [ ] capture one camera where a phrase visibly travels down the route.

---

# 11. Success criteria

Promote from `SPIKE` to `PROTOTYPE` only if all are true:

- rhythm event binding adds zero new gameplay authority;
- one press reliably produces one visual impulse;
- Perfect vs Miss is readable without UI labels;
- the effect looks like environmental physics rather than a music visualizer;
- fixed-camera visual improvement is obvious in under 3 seconds;
- GPU cost is small enough for a background environmental effect in the test scene;
- no frozen master material or production map was modified;
- complete rollback is deleting the R&D folder + bridge placement.

---

# 12. Evidence bundle

Create after the test:

```text
Saved/Audit/RND/CymaticEcology/<timestamp>/
  manifest.json
  baseline.png
  perfect_streak.png
  miss_breakup.png
  perfect_streak.mp4      # optional / not necessarily committed
  stat_gpu.txt
  niagara_notes.md
```

Commit lightweight evidence only.

Manifest fields:

```json
{
  "schema": "melodia.rnd.cymatic-ecology.v1",
  "ue_version": "5.8.x",
  "map": "LV_RND_CymaticEcology",
  "pulse_count": 0,
  "niagara_data_channel": true,
  "grid2d_used": false,
  "fixed_camera": "",
  "gpu_ms_before": 0.0,
  "gpu_ms_after": 0.0,
  "decision": "ADOPT|PARK|REJECT",
  "notes": ""
}
```

---

# 13. Future semantic-field bridge

If the native analytic version wins, connect it later to the toolchain contract:

```text
melodia_filter_flow_strength
melodia_filter_flow_dir_ws
melodia_monolith_proximity_m
melodia_tension
```

Then the cymatic wave does not propagate uniformly. It bends, attenuates, or concentrates according to the hidden ecological/Monolith field generated upstream by Houdini/PCG.

That future state is the real design target:

```text
Rhythm judgement
   -> visible wave
   -> semantic ecology field
   -> Niagara / materials / particles
   -> player perceives hidden world structure
```

No Houdini runtime dependency is required.

---

# 14. Decision rubric

### ADOPT
The effect creates a distinctive Melodia read, is cheap, deterministic enough for presentation, and cleanly consumes existing rhythm events.

### PARK
The visual is attractive but reads as generic music VFX or needs a more mature field implementation.

### REJECT
It requires gameplay-authority changes, frozen material rewrites, expensive simulation, or creates timing instability around the rhythm subsystem.

---

# 15. Tonight rule

> Get one magical, undeniable field reaction working before adding complexity.

A single convincing Perfect -> coherent rose-window interference pattern is a better result tonight than a half-built persistent solver.
