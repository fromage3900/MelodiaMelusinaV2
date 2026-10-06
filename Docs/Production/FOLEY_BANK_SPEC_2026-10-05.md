# Foley Bank Spec — Surface-Aware, Bus-Routed

**Date:** 2026-10-05. **Status authority:** `CURRENT_STATE.md`. **Companion:** `AUDIO_REACTIVE_CANON.md` (one writer per surface).

## Scope

Melusina walks in silence today: no footstep waves, no interaction SFX, no combat contact
foley. `Melodia\Audio\SFX` holds only `A_UI_Bubble` and UI blips. This spec closes that gap
with three banks, all routed through `SUBMIX_SFX` (never competing with `SUBMIX_Ambience`),
all subject to the `SM_MelodiaAudioBus` class override so TD can pull the whole SFX bus
over OSC `/audio/bus/sfx/level`.

## Source decision (owner call 2026-10-05)

**Created (deterministic) first; neural later.** Neural generation (ACE-Step / Riffusion /
Stable-Audio-class models) is optional for *content* but has two costs the packaged build
cannot absorb: nondeterminism at load time and a network dependency (canon §5 already
flags the editor-only OSC bridge as the parity hole). The banks below are authored from
public-domain/CC0 foley sources plus granular re-voices of existing `fx_amb_*` assets; a
neural swap, if ever approved, lands at the sample-slot level, not at the system level.

## Bank A — Footsteps (highest impact)

| Surface | Samples per layer | Notes |
|---|---|---|
| Grass/meadow | 6 | Melusina's Morning overworld; soft, high-passed |
| Dirt/trail | 6 | Quill paths |
| Stone/paving | 6 | Atlantis architecture zones |
| Wood/deck | 6 | Spline walkways, rail decks |
| Water splash (shallow) | 6 | Puddles (reuse `UDS Puddle_01/03/04` re-voiced) |
| Cloth rustle (always-on underlay) | 3 | Re-voice `fx_amb_spot_foliage_rustle_close_lp_01..06` |

Wiring: `MelodiaTraversalComponent` surface-per-impact events (one notify per foot impact
in the locomotion clips) -> one `SoundCue` per surface (random node over the 6 samples,
pitch 0.92-1.08) -> `SCL_SFX`. No surface-material physics probing: the authored route
is known at design time (Morning is a hand-authored map).

## Bank B — Interaction

| Action | Samples | Trigger owner |
|---|---|---|
| Rock pickup (the `sfx_Amb_RocksInteract_Meta` finally gets a source) | 4 | existing interact action |
| Bench sit / stand | 3 each | traversal sit |
| Door / gate open | 4 | PCG door actors |
| Prop grab (journal, vial) | 4 | F-interact |

All 0.3-0.6 s one-shots, `-18 dB` nominal, `SCL_SFX`.

## Bank C — Combat contact (WaveHarp)

| Event | Samples | Notes |
|---|---|---|
| Bowstring draw (whoosh, deployment 0->1) | 4 | Morphs with AstrolabeOffset |
| String release | 4 | Chord-aware: 5th shot gets a fuller release |
| Arrow whoosh | 3 | One-shot, 0.2 s |
| Impact thud (target) | 6 | Grade-graded: Miss damped, Perfect brighter |

Owner seam: `MelodiaWaveHarpCombatComponent` draw/hold/release events (existing LMB/RMB
ownership; presentation-only, no damage-path wiring per the presentation-layering rule).

## Bus convergence (ties into the OSC system)

```text
TD audio engine                          UE
  | /audio/bus/{ambience,music,sfx,voice}/level
  v                                        v
MPC_MelodiaAudioBus  <---- osc_server.py   UMelodiaAudioBusSubsystem (sole consumer)
  |                                        |
  +-- C++ fallback writes 1.0 without TD   +-- SetSoundMixClassOverride(
                                             SM_MelodiaAudioBus, SCL_*, level, fade 0.4 s)
                                             +-- MelodiaCore tension duck (SCL_Ambience via
                                                SM_MelodiaTensionDuck) remains untouched
```

Harmonic state (tension/consonance/mode) rides `MPC_Melodia_HarmonicState`, written by
`UMelodiaHarmonicStateSubsystem`; game systems read it (aggression, pacing, lighting,
palette). It does not touch the bus gains directly -- bus gains are a TD-owned mix
decision, tension duck is MelodiaCore-owned. Two authorities, zero overlap.

## Asset layout

```text
Content/Melodia/Audio/Foley/
  Footsteps/{Grass, Dirt, Stone, Wood, Splash}/SW_FS_<surface>_<n>.uasset + SC_Foley_Footstep_<surface>
  Interaction/{...}.uasset + SC_Foley_Interaction
  Combat/{...}.uasset + SC_Foley_WaveHarp
```

All 48-52 source waves live in Perforce (bulk binary), not Git; the SoundCues and the
`SCL_Foley_*` subclasses route to `SCL_SFX`.

## Done =

- Bank A ships: a 20 s Morning walk in PIE has audible footsteps under the ambience bed,
  clearly below music, still audible at full music volume.
- Bank B: rock pickup and door open have SFX in a fresh PIE session.
- Bank C: a five-shot LMB run produces five contact sounds, the fifth brighter.
- `/audio/bus/sfx/level` at 0.3 mutes the walk without touching ambience or music.
- Evidence in `Saved/Audit/Status/`.
