# Cymatic Ecological Memory — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** implementation-ready extension of Cymatic Ecology  
**Decision:** BUILD AFTER STATIC/RHYTHM FIELD MVP

## Goal

Make rhythm quality leave a short-lived spatial memory in the environment instead of disappearing as a one-frame VFX cue.

The memory is environmental response, not rhythm authority.

```text
OnLaneHitJudged
 -> cymatic impulse
 -> local field coherence
 -> temporary spatial memory
 -> Niagara / material / PCG presentation bias
 -> decay back to baseline
```

## Map and assets

```text
LV_RND_CymaticEcologicalMemory
NDC_MelodiaRhythmPulse
NDC_MelodiaEcologyMemory
BP_MelodiaCymaticPresentationBridge
NS_Melodia_CymaticField
NS_Melodia_CymaticMemoryParticles
RT_Melodia_CymaticMemory_A
PCG_CymaticMemoryPreview
```

## v1 memory model

Do not start with persistent save-game ecology.

Use a bounded local field around the player with:

- center/origin;
- harmonic phase/coherence;
- amplitude;
- age;
- decay half-life;
- optional nodal direction/gradient;
- source phrase/frame ID.

Suggested first lifetime: 3–12 seconds depending on effect family.

## Response hierarchy

### Tier A — presentation only

- pearl/pollen particles accumulate near nodal lines;
- material wetness/iridescence sharpens with coherence;
- caustic/filigree overlays persist briefly;
- Misses inject destructive breakup.

### Tier B — environment authoring response

- local grass/coral orientation bias;
- short-lived density visibility/scale bias;
- petals/debris drift along harmonic gradients.

### Tier C — later systemic use

Only after explicit design approval, selected non-critical ecology may consume accumulated memory as a soft world-state input. Never let this alter judgement timing, damage, traversal collision, or hidden authoritative targets.

## Storage approach

v1 should be one of:

1. Niagara/Grid2D local field; or
2. small render target / texture field; or
3. sparse list of recent impulses evaluated analytically.

Start with sparse impulses or a small 2D field. Do not build a large voxel simulation first.

## Decay

Each memory sample follows a deterministic decay function, for example:

```text
strength(t) = initial_strength * exp(-lambda * age)
```

Perfect/Great/Good may vary initial coherence and decay duration. Miss may create brief anti-coherence with a shorter lifetime.

Record exact constants in a data asset rather than hard-coding them across materials and Niagara systems.

## First spike

1. replay deterministic 8-beat sequence;
2. show live cymatic field;
3. write memory for successful hits;
4. let pearl particles migrate toward nodal regions;
5. stop input and observe 8-second decay;
6. replay with one Miss and verify visible disruption;
7. repeat identical sequence twice and compare capture.

## PCG boundary

Do not recook heavyweight world PCG on every beat.

For v1, PCG may consume memory only in a deliberately throttled/local R&D graph or as a later offline/editor experiment. Runtime visual response should stay in Niagara/materials unless profiling proves a PCG path is safe.

## Metrics

- rhythm event -> visible response latency;
- GPU ms;
- field update cost;
- particle count/cost;
- deterministic replay similarity;
- time until full decay;
- readability of Perfect vs Great vs Miss without UI;
- temporal reconstruction stability under TSR/DLAA/DLSS;
- whether the system remains visually useful at low settings.

## Pass / park / reject

**ADOPT** if the field makes rhythm quality legible through environmental organization, remains presentation-safe, costs little enough for real gameplay, and decays predictably.

**PARK** if only beautiful in isolated shots, relies on expensive large-grid simulation, or temporal reconstruction destroys the pattern.

**REJECT** any version that delays/obscures authoritative rhythm feedback or changes collision/gameplay truth.

## Evidence

```text
Docs/Research/Evidence/CymaticMemory/
  README.md
  tuning_manifest.json
  deterministic_sequence.json
  perfect_sequence_capture.md
  miss_sequence_capture.md
  perf_summary.csv
  dlss_tsr_notes.md
```

## Long-term extension

The strongest later connection is:

```text
Houdini/PCG filter-flow field
 + player cymatic memory
 -> visible ecological interference
```

The player would not create arbitrary ecology; music would reveal and temporarily organize the world according to pre-existing Melodia semantic fields.