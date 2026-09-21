# Listening Field — durable contract

**Status:** CANONICAL DATA CONTRACT. Not a status document.  
**Code is the source of this page:** [`Tools/phrase_bridge/`](../../Tools/phrase_bridge/) (`melodia.phrase/v1`) and [`Tools/listening_field/`](../../Tools/listening_field/) (`melodia.directive/v1`). Live session proof belongs only in [`CURRENT_STATE.md`](../../CURRENT_STATE.md).

Jev is a **director**. It selects among authored sheep / world / layout options. It does not compile meadows, write MPCs, move actors, or open a second Unreal editor.

---

## 1. Phrase state (`melodia.phrase/v1`)

Schema owner: [`Tools/phrase_bridge/phrase_schema.py`](../../Tools/phrase_bridge/phrase_schema.py). Unknown fields fail validation. This is the musical SoT for the Listening Field.

| Field | Type | Contract |
|---|---|---|
| `schema_version` | string | must be `melodia.phrase/v1` |
| `phrase_index` | int ≥ 0 | authored phrase in the plan |
| `section` | enum | `SPARSE` `VOICE` `BUILD` `CLIMAX` `RELEASE` |
| `bar` | int ≥ 0 | engine bar |
| `beat_in_bar` | float | `[0, beats_per_bar]` (trace authority is 4/4) |
| `energy` | float | `[0, 1]`, authored automation, not DSP |
| `energy_trend` | enum | `FALLING` `FLAT` `RISING` |
| `confidence` | float | `[0, 1]`; decays through rests |
| `boundary_pulse` | bool | held for exactly one bar when confidence ≥ 0.5 |

Trace authority clock ([`bridge.py`](../../Tools/phrase_bridge/bridge.py)): **80 BPM**, **4/4**, **10 Hz** ticks, **3.0 s/bar**. `boundary_pulse` fires on bar wrap only when `confidence >= 0.5`.

**Not this schema:** [`Content/Python/resonant_world_phrase_bridge.py`](../../Content/Python/resonant_world_phrase_bridge.py) is the MIDI-ecology voxel bridge. Do not feed it to Jev.

---

## 2. Transport — UDP OSC `:9000` only

Phrase packets move as OSC 1.0 over **UDP `127.0.0.1:9000`**. Encoder: [`Tools/phrase_bridge/osc_min.py`](../../Tools/phrase_bridge/osc_min.py) (stdlib only). Addresses:

| Address | Typetag | On-wire size | Payload |
|---|---|---|---|
| `/melodia/phrase/state` | `,isifsfi` | 72 B | `phrase_index:int`, `section:str`, `bar:int`, `energy:float`, `energy_trend:str`, `confidence:float`, `boundary_pulse:int 0/1` |
| `/melodia/phrase/boundary` | `,ii` | 40 B | `phrase_index:int`, `bar:int` (sent once at the start of a pulsed bar) |

UE consumer is **transport-only**: [`MelodiaPhraseBusSubsystem`](../../Source/BS_GodFile/MelodiaIntegration/MelodiaPhraseBusSubsystem.h) listens on **UDP `127.0.0.1:9000`**, republishes on the game thread, and **never** writes MPCs, Niagara, sheep, or World Compiler data. Consumers subscribe to delegates and stay single-writer on their own surfaces. Silence timeout default: **6 s** (two bars at 80 BPM).

**Live ingest is `RecvFrom`** on the unconnected datagram socket. `Recv()` is the retired bug (packets never reached Parse; GetCurrentState stayed bar 0 / energy 0.0). **LIVE PROVEN 2026-09-20:** PIE `UEDPIE_0_L_MelusinaMorning`, loaded `UnrealEditor-BS_GodFile.dll` 3,232,768 bytes mtime 2026-09-20 17:48:36, GetCurrentState bar 0/energy 0.0 → bar 10/energy 0.92 (phrase_index 4, CLIMAX, RISING). Session proof lives only in [`CURRENT_STATE.md`](../../CURRENT_STATE.md). The `.cpp` is landed; this spec stays transport-only. Do not revive `Recv()`. Do not invent a second OSC port or a second phrase bus.

---

## 3. Directives (`melodia.directive/v1`)

Schema owner: [`Tools/listening_field/directive_schema.py`](../../Tools/listening_field/directive_schema.py). Unlisted values are a **silent no-op** (empty sheep/world, `layout_seed=None`), same idea as an unallowlisted Quill id.

### Sheep allowlist

`HOLD` · `TURN_TO_PLAYER` · `SPIRAL_FORMATION` · `RESONANCE_PULSE` · `CRESCENDO_BURST`

`SETTLE` and `RETURN_TO_IDLE` are conductor-owned and **not** in this vocabulary.

### World allowlist

`RESTRAIN` · `RELEASE`

### Other fields

| Field | Contract |
|---|---|
| `for_bar` | bar the decision **applies** at (see §4) |
| `restraint` | `[0, 1]` |
| `layout_seed` | a key in `LAYOUT_SEEDS` or `None` |
| `source` | `jev` or `fallback` |
| `confidence` | `[0, 1]` |

Director: [`Tools/listening_field/jev_director.py`](../../Tools/listening_field/jev_director.py). TypeSafe `System One` when `TYPESAFE_API_KEY` is set and `typesafe_sdk` imports; otherwise [`director_table.py`](../../Tools/listening_field/director_table.py) is the contract. `--verify` requires both paths to agree.

Jev never mutates the Unreal editor. `layout_seed` picks **already-authored** WC/PCG data. It does not compile a meadow from text. `recipes/jev_showcase_bloom.v1.json` is a World Compiler recipe whose name is unrelated to this director.

---

## 4. Latency — decide at bar N, apply at bar N+1

Every directive is tagged `for_bar = state.bar + 1`. The decision is taken on the boundary pulse of bar N and must not take effect until bar N+1. Tests in [`test_jev_director.py`](../../Tools/listening_field/test_jev_director.py) lock this.

Dwell: at most one non-`HOLD` sheep change per bar (`MIN_BARS_BETWEEN_SHEEP_CHANGES = 1`). A `layout_seed` is chosen **once**, on the transition into `CLIMAX`, not on every boundary that climax spans.

---

## 5. Authored 45 s plan and fallback table

[`bridge.py` `SECTION_PLAN`](../../Tools/phrase_bridge/bridge.py) is the trace authority for capture. FL Studio may redraw energy automation later; `emit --record` / `replay` must stay byte-stable against this plan.

| t (s) | phrase_index | section | energy ramp | confidence |
|---|---|---|---|---|
| 0:00 | 0 | SPARSE | 0.15 → 0.20 | 1.0 |
| 0:08 | 1 | VOICE | 0.30 → 0.45 | 1.0 |
| 0:15 | 2 | VOICE | 0.45 → 0.55 | 0.9 |
| 0:22 | 3 | BUILD | 0.55 → 0.75 | 1.0 |
| 0:30 | 4 | CLIMAX | 0.80 → 1.00 | 1.0 |
| 0:38 | 5 | RELEASE | 0.70 → 0.30 | 0.9 |
| 0:42 | 6 | SPARSE (rest) | 0.20 → 0.10 | 0.3 (gates boundary) |

Fallback / Jev answer key ([`director_table.py`](../../Tools/listening_field/director_table.py)):

| (section, phrase_class) | sheep | world | restraint |
|---|---|---|---|
| SPARSE / opening | HOLD | RESTRAIN | 1.0 |
| VOICE / arrival | TURN_TO_PLAYER | RESTRAIN | 0.7 |
| VOICE / sustain | HOLD | RESTRAIN | 0.7 |
| BUILD / layering | RESONANCE_PULSE | RELEASE | 0.2 |
| CLIMAX / major | SPIRAL_FORMATION | RELEASE | 0.0 |
| RELEASE / tail | CRESCENDO_BURST | RELEASE | 0.3 |

Restraint score labels: `full_hold=1.0`, `held_breath=0.7`, `partial=0.5`, `open=0.2`, `full_release=0.0`.

---

## 6. Layout seeds — pick existing data, never compile

From `LAYOUT_SEEDS` in [`directive_schema.py`](../../Tools/listening_field/directive_schema.py). Radius / band / density are authored constants.

| Seed | Formation (authored) | Maps onto existing WC/PCG | Never means |
|---|---|---|---|
| `seed_arc_walk` | ARC, center `escher_walk`, 18 m, full rainbow | `WC_EscherWalk_*` walk dressing | a new meadow compile |
| `seed_ring_pond` | RING, center `pond_waterline`, 10 m, warm | waterline framing already in the Morning recipe | planting the Oceanology lake |
| `seed_spiral_north` | SPIRAL, center `north_meadow`, 14 m, 3 turns, cool | the authored flock spiral already in the level | inventing a north meadow or bedroom floor field |

Jev chooses **which** seed. World Compiler + `PCG_WorldCompiler_PointField` remain the only meadow authority. Flowers stay on `BrushifyIsland_*`; dressing on `WC_EscherWalk_*` plus island skirts; bedroom keepout. See [`WORLD_COMPILER_CONTRACT.md`](../WorldGen/WORLD_COMPILER_CONTRACT.md) and `recipes/morning_rainbow_bloom.v1.json`.

---

## 7. Hard no's

- No editor writes from Jev (no MCP actor moves, no `compile`, no MPC/PPV).
- No second phrase schema, second director, second PhraseBus, or second OSC port for this bus.
- No `Recv()` ingest and no treating GetCurrentState bar 0 as current debt.
- No treating `resonant_world_phrase_bridge.py` or `jev_showcase_bloom` as this system.
- Unallowlisted sheep/world/seed values become no-ops; they are not prompts to invent content.
