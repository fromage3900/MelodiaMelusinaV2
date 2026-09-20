# LISTENING FIELD — FL → Jev → UE5.8 Phrase Director Spec

**Date:** 2026-09-20 · **Status:** FRONTIER PLAN, approved for execution · **Lane:** Choral Sheep capstone adjacent — does not own sheep rig/ABP work

**Mission:** smallest production-quality proof where FL Studio exposes live phrase state, Jev (`jev-1.13.0`, no other model — "Jcode" does not exist in the current TypeSafe lineup) chooses among **authored** responses, and UE5.8 answers through existing owner systems. Output: one reproducible 30–60s portfolio capture. Audience reads emotional behavior with **no debug UI**.

**Status authority:** `CURRENT_STATE.md` (evidence levels as of 2026-09-19). Precedence rules: one editor, one writer per surface, extend owners never compete (`AGENTS.md`).

---

## 1. State Contract — `FPhraseState` (schema `melodia.phrase/v1`)

FL is a sequencer and knows the score — **no raw audio analysis**. Composer encodes intent as data:

| Field | Type | Source |
|---|---|---|
| `PhraseIndex` | int32 | FL marker track |
| `SectionTag` | enum {`SPARSE`,`VOICE`,`BUILD`,`CLIMAX`,`RELEASE`} | FL arrangement markers |
| `Bar` / `BeatInBar` | int / float(0–4) | bridge clock, project BPM, quantized |
| `Energy` | float 0–1 | **authored FL automation clip** (dummy ENERGY mixer lane), not DSP |
| `EnergyTrend` | enum {`FALLING`,`FLAT`,`RISING`} | bridge: Energy vs 2-bar window |
| `Confidence` | float 0–1 | bridge: decays through rests/gaps |
| `BoundaryPulse` | bool (held 1 bar) | bridge: Bar wraps ∧ Confidence > 0.5 |

## 2. Transport — one lane, one port, one writer

- FL MIDI Out → loopMIDI → bridge (`Tools/phrase_bridge/`, plain Python) → **OSC/UDP `:9000`** (the existing TD lane port; owner queue already wants one real OSC `:9000` proof).
- Bridge emits `/melodia/phrase/state` @10 Hz, `/melodia/phrase/boundary` as event; **records and replays** traces (`Saved/Audit/phrase_traces/listening_field_v1.jsonl`). Trace playback is the capture path — live OSC is the flex, the trace is the proof.
- UE: one new subsystem `UMelodiaPhraseBusSubsystem` (C++, game thread, UDP socket). Transport authority only — **never writes MPCs, never drives Niagara, never moves sheep.**
- The scaffolded `UWorldFieldBus` is NOT this lane — SCAFFOLDED, not live. The phrase bus is the proven path; the field bus may absorb it later if it closes.

## 3. Jev — director, allowlisted like Quill

- Invoked **only on `BoundaryPulse`**, never per tick. Input: `FPhraseState` + `{ResonanceAccumulator, currentSheepState, dwellTimers}`.
- Output is a closed enum + one scalar, nothing else:

```
SheepDirective ∈ {HOLD, TURN_TO_PLAYER, SPIRAL_FORMATION, RESONANCE_PULSE, CRESCENDO_BURST}
WorldDirective ∈ {RESTRAIN, RELEASE}
Restraint      ∈ [0, 1]
```

- TypeSafe primitives: **Choice** per directive enum; **Score** for Restraint (levels: `full_hold, held_breath, partial, open, full_release`); optional **Noul** "is this CLIMAX-worthy". Batch all questions in one request per boundary.
- Quill-allowlist pattern: UE validates every directive against the allowlist; **unlisted → silent no-op**. Classical fallback table in the UE conductor covers every input when Jev is down — the workflow functions before Jev is enabled.
- Jev never owns safety: minimum dwell, hysteresis, `SETTLE → RETURN_TO_IDLE`, and OSC-timeout settle (>2 bars silent → deterministic settle) live in the UE conductor.
- Restraint semantics: `RELEASE` lets the conductor spend `ResonanceAccumulator` on the CLIMAX response; `RESTRAIN` caps response at the authored held-breath curve.
- Decisions at bar N apply at bar **N+1** (latency absorption). OSC jitter absorbed by ±1-beat boundary windows.

## 4. Authored response lanes (existing owners only)

| Lane | Owner (per CURRENT_STATE) | Prototype authors |
|---|---|---|
| Sheep | `BP_ChoralSheep`, `DA_ChoralSheepDefinition`, `MelodiaCompanionComponent`, conductor states | map 5 directives onto existing `TURN_TO_PLAYER / SPIRAL_FORMATION / RESONANCE_PULSE / CRESCENDO_BURST / SETTLE`; Harmonize ramp/decay live-proven 09-13 |
| Cymatics | `MPC_Cymatics_Driver` via the single cymatics writer | SectionTag → authored mode/intensity curve; CLIMAX = bloom (`Cymatic_ModeN/M`, `EmissiveScale`, `BeatPulse`) |
| Wind | `NS_Morning_WindFront`, `NS_Morning_PetalDrift` + wind MPC scalars | phrase-gated `WindFrontVisible` gusts on BUILD/CLIMAX. **Hard dependency on the 09-19 morning-rewire lane** (binds pack `User.*`, renames `SpawnMultiplier`) — run after it; **never write MPCs from this lane** |
| Flowers | World Compiler `WC_morning_rainbow_bloom_Field` (971 flowers, proven) + PCG resonance custom-data materials | authored hue-drift band driven by `ResonanceAccumulator` |
| Accumulator | deterministic UE integrator: `+= Energy × (1 − Restraint) × k` per beat, capped, decays in RELEASE | owned by conductor, not Jev |

CLIMAX+RELEASE = one conductor beat: sheep `SPIRAL_FORMATION` + cymatic mode bloom + `WindFrontVisible` gust + flower band jump + accumulator spend. Four owners, one trigger, each writes only its own surface.

## 5. Sequence — 45 s, trace-driven

| Time | Music | Section | Jev | World |
|---|---|---|---|---|
| 0:00 | sparse piano | SPARSE | HOLD | idle field, wind 0 |
| 0:08 | voice enters | VOICE | TURN_TO_PLAYER | sheep face; Harmonize begins |
| 0:15 | sustained | VOICE | RESTRAIN 0.7 | slow flower hue drift, petals sparse, accumulator visibly held |
| 0:22 | arps layer | BUILD | RELEASE 0.2 | WindFront gust, `RESONANCE_PULSE`, emissive creeps |
| 0:30 | **major phrase** | CLIMAX | SPIRAL_FORMATION + RELEASE 0 | full bloom, all four lanes as one system |
| 0:38 | tail | RELEASE | CRESCENDO_BURST | burst resolves |
| 0:42 | rest | — | (conductor) | deterministic `SETTLE → RETURN_TO_IDLE` |

Camera: proven lookdev cams (`WC_Lookdev_waterline_dolly` @ [-3100,200,180], `website_oblique`) — three fixed shots cut on phrase boundaries; no gameplay input needed, no probe-vs-play ambiguity.

## 6. Evidence standard (2026-08-11 rules, inherited)

- Capture driven by **recorded trace** — identical take every run.
- Frames + JSON report side by side: per-bar `{directive_applied, accumulator, sheep_state, Cymatic_Mode, WindFrontVisible, flower_band}` at `Saved/Audit/listening_field/`; committed harness = harness that ran.
- Echo ledger rows via `Tools/echo_run.py record` per gate — prose is not evidence.
- Deliverable: 45 s render + 5-frame still board + trace file.

## 7. Execution packets (cheaper specialist agents)

Editor work serializes through ONE lock; source/bridge work runs while the editor is closed.

| # | Task | Editor? | Finish line |
|---|---|---|---|
| A1 | Phrase bridge + trace recorder/replayer + schema validator (`Tools/phrase_bridge/`) | No | trace replays byte-stable; validator rejects bad schema; no project mutation |
| A2 | `UMelodiaPhraseBusSubsystem` C++ + allowlist validation + timeout settle | Build only (header change → **closed-editor build**) | restart-proven: receives trace, publishes `FPhraseState`, settles on silence |
| A3 | Sheep directive map in existing conductor (Monolith) | Yes, serialized | PIE: each directive reaches authored sheep state; unlisted id no-ops |
| A4 | Cymatics/wind/flower authored response curves — **after** rewire lane binds `User.*` | Yes, serialized | scoped receipts per surface; one writer each; zero MPC writes by this lane |
| A5 | Jev decision service + classical fallback (`Tools/listening_field/jev_director.py`) | No | bar-N decision applies at N+1; Jev offline → fallback table reproduces identical sequence |
| A6 | Sequence director: trace playback → conductor → capture harness → JSON report | Yes, serialized | full 45 s pass with per-bar report + frames |
| A7 | Ledger rows + `CURRENT_STATE.md` update **in the same commit** | No | gate rows exist; status doc current |

## 8. Traps pre-solved

Single editor (rule 7) · probe ≠ play (fixed cams, trace drive) · scaffolded field bus never claimed live · sheep foot-slide/ABP thresholds stay with the capstone lane, untouched · unlisted directive = silent no-op, same as unallowlisted Quill id · network loss can pause the performance, never wedge it.
