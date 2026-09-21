# Jev × FL Studio Phrase Conductor (isolated prototype)

One bounded experiment: Jev conducts arrangement across phrase boundaries
in a duplicated Melodia FL Studio cue. Jev ONLY selects among 8 authored
responses — HOLD, THIN, BUILD, BLOOM, RESTRAIN, DROP_TO_VOICE,
FULL_CHORUS, SETTLE. It creates nothing.

## Honest status

- The loop is built and unit-tested offline. Live FL and live Jev have
  NOT run yet: FL Studio was closed when probed, no test `.flp` exists in
  the repo or user folders, and `TYPESAFE_API_KEY` is not configured.
- Without the key the bridge runs a deterministic classical fallback,
  labeled `classical-fallback` on every line. That is NOT Jev evidence.
- The device script (`FLStudioMCP` v0.2, SysEx) already exposes every
  snapshot primitive except time-marker reads — so the authored section
  comes from the cue config's bar map, and the device script was NOT
  modified.
- Bar math assumes 4/4 unless the cue config sets `beats_per_bar`.

## Files

- `jev_fl_conductor.py` — 8 closed choices, state, Jev Choice call,
  fallback, hysteresis arbiter, SETTLE safety, debug HUD.
- `fl_snapshot.py` — transport/tempo/position/peaks/mute reads through
  the bridge; energy EMA + trend. Takes any `call(cmd, params)` bridge.
- `conductor_bridge.py` — the external process. Owns the API key (env
  only). Phrase loop, preset execution (mixer mutes on whitelisted stems
  only), HUD stdout, JSONL sidecar with full distributions.
- `jev_fl_cue.example.json` — copy to `jev_fl_cue.json`, fill mixer
  indices from the DUPLICATED cue. The bridge refuses configs with
  missing presets, non-whitelisted tracks, or a mutable master.
- `test_jev_fl_conductor.py` — offline tests (no FL, no key).

## Run

  python Prototypes/JevFLConductor/test_jev_fl_conductor.py  # via pytest
  python Prototypes/JevFLConductor/conductor_bridge.py --cue <cue>.json --check-cue
  python Prototypes/JevFLConductor/conductor_bridge.py --cue <cue>.json --dry-run --once
  TYPESAFE_API_KEY=... python Prototypes/JevFLConductor/conductor_bridge.py --cue <cue>.json --max-phrases 16

Live day needs, in order: FL Studio open with the duplicated cue playing,
FLStudioMCP controller enabled in MIDI settings, loopMIDI ports up,
cue config filled, key exported. Then A (authored baseline) vs B (Jev
conductor) capture and a listening verdict — then STOP.
