# Listening Field — spec (2026-09-20)

Durable contract for phrase state, Jev directives, and the UE phrase bus.
Python schemas are executable truth; this page is the cited map so agents
do not follow ghost or MIDI-ecology bridges.

| Layer | Schema / owner | Not this |
|---|---|---|
| Phrase clock | `melodia.phrase/v1` — `Tools/phrase_bridge/` | `Content/Python/resonant_world_phrase_bridge.py` (MIDI ecology) |
| Director | `melodia.directive/v1` — `Tools/listening_field/` | `recipes/jev_showcase_bloom.v1.json` (a WC recipe name) |
| UE transport | `UMelodiaPhraseBusSubsystem` UDP `127.0.0.1:9000` | MPC writes, Niagara, sheep motion, WC compile |

Jev is a **director**: it picks among authored allowlists. It does not mutate the editor.

---

## 1. Phrase state — `melodia.phrase/v1`

Source: `Tools/phrase_bridge/phrase_schema.py`.

| Field | Type | Notes |
|---|---|---|
| `schema_version` | `"melodia.phrase/v1"` | required |
| `phrase_index` | int ≥ 0 | authored section index |
| `section` | `SPARSE` `VOICE` `BUILD` `CLIMAX` `RELEASE` | |
| `bar` | int ≥ 0 | |
| `beat_in_bar` | float | JSON/trace only; **not** on the OSC wire |
| `energy` | 0..1 | authored automation, not DSP |
| `energy_trend` | `FALLING` `FLAT` `RISING` | |
| `confidence` | 0..1 | decays through rests |
| `boundary_pulse` | bool | held exactly one bar; gated by confidence ≥ 0.5 |

Trace authority: 80 BPM, 4/4, 10 Hz tick, bar = 3.0 s. Engine: `Tools/phrase_bridge/bridge.py`.

---

## 2. OSC wire (UE ↔ phrase_bridge / TD)

Port **9000**, bind **127.0.0.1** (local capture workstation). Encoder: `Tools/phrase_bridge/osc_min.py` (OSC 1.0, big-endian, 4-byte padded strings).

`bridge._send_state` emits:

```
/melodia/phrase/state    ",isifsfi"
  phrase_index:i  section:s  bar:i  energy:f  energy_trend:s  confidence:f  pulse:i (0|1)

/melodia/phrase/boundary ",ii"     (only when boundary_pulse and beat_in_bar < tick)
  phrase_index:i  bar:i
```

Unknown addresses are ignored. Timeout: 6 s of silence (two bars) → `OnPhraseTimeout` once; the conductor owns settle.

---

## 3. Directives — `melodia.directive/v1`

Source: `Tools/listening_field/directive_schema.py`. Unlisted values are a silent no-op.

| Field | Allowlist |
|---|---|
| `sheep` | `HOLD` `TURN_TO_PLAYER` `SPIRAL_FORMATION` `RESONANCE_PULSE` `CRESCENDO_BURST` or `""` |
| `world` | `RESTRAIN` `RELEASE` or `""` |
| `restraint` | 0..1 |
| `layout_seed` | a `LAYOUT_SEEDS` key or `null` |
| `for_bar` | decision at bar **N** applies at bar **N+1** |
| `source` | `jev` \| `fallback` |

`SETTLE` / `RETURN_TO_IDLE` are conductor-owned and are **not** in this vocabulary.

### LAYOUT_SEEDS → existing World Compiler data

Jev picks the **key**. It never compiles, never writes MPCs, never plants. Mapping is a lookup onto already-authored Morning WC data (`recipes/morning_rainbow_bloom.v1.json`):

| Key | Existing WC / level data |
|---|---|
| `seed_arc_walk` | `WC_EscherWalk_*` walk dressing (`ground_labels` include `WC_EscherWalk_` plus Brushify island skirts) |
| `seed_ring_pond` | waterline framing — `lookdev.cameras[]` name `waterline_dolly` / `WC_Lookdev_waterline_dolly` at `[-3100, 200, 180]` |
| `seed_spiral_north` | north meadow / `BrushifyIsland_*` flower field (flowers snap onto Brushify islands only) |

---

## 4. UE phrase bus (A2)

`Source/BS_GodFile/MelodiaIntegration/MelodiaPhraseBusSubsystem.*`

- `UGameInstanceSubsystem`, auto-registered with module `BS_GodFile` (`Sockets` + `Networking`).
- Game-thread poll via `FTSTicker` (no receiver thread).
- Delegates: `OnPhraseState`, `OnPhraseBoundary`, `OnPhraseTimeout` (BlueprintAssignable).
- **No gameplay side effects** in the subsystem.

Choral Sheep: bind `BP_ChoralSheep` to `OnPhraseBoundary`. When a Jev directive is due (`for_bar <= Bar`) and `sheep` is `RESONANCE_PULSE` or `CRESCENDO_BURST`, call existing `TryBeginHarmonize`. Do not invent companion AI or move sheep from C++.

---

## 5. Authored 45 s sequence (trace authority)

Times from `Tools/phrase_bridge/bridge.py` `SECTION_PLAN`:

| t (s) | phrase_index | section |
|---|---|---|
| 0 | 0 | SPARSE |
| 8 | 1 | VOICE |
| 15 | 2 | VOICE |
| 22 | 3 | BUILD |
| 30 | 4 | CLIMAX |
| 38 | 5 | RELEASE |
| 42 | 6 | SPARSE (rest; confidence 0.3, pulse gated off) |

Fallback answers: `Tools/listening_field/director_table.py`. `layout_seed` is asked only on the transition into CLIMAX.

---

## 6. Roles

| Owner | Does | Does not |
|---|---|---|
| phrase_bridge | emit / record / replay phrase OSC | direct sheep or worlds |
| Jev / director_table | pick allowlisted sheep, world, restraint, layout_seed; stamp `for_bar = N+1` | compile WC, write MPC, MCP-move actors |
| Phrase bus | decode OSC, republish delegates | any of the above |
| World Compiler CLI | compile recipes into PCG point fields | run because Jev picked a seed |
| `AMelodiaChoralSheepActor` | `TryBeginHarmonize` / existing follow | a second companion framework |
