# Jev-Driven Choral Sheep Conductor (isolated prototype)

One bounded experiment: Jev conducts the Choral Sheep flock as a tiny
musical/world-state director. Jev ONLY selects among authored options —
9 flock behaviors, 6 world accompaniments. It creates nothing.

## Honest status

- There is no `L_MelusinasMorning` map in the repo and no prior Jev routing
  pilot was found (only the skill install). So the "safest isolated
  version" is: no map at all. This prototype is pure Python under
  `Prototypes/JevSheepConductor/` — no `.umap`, no `.uasset`, no editor,
  no production mutation. Delete this folder to remove everything.
- No `TYPESAFE_API_KEY` is configured, so live Jev has never run here yet.
  The loop works today on a deterministic classical fallback (clearly
  labeled `classical-fallback` in every output). Set the key and the same
  code calls Jev live (`jev-live`) with zero logic changes.
- The 48s "capture" is a scripted-state run (`scenario_capture.py`), not an
  in-engine play session. It proves the decision loop, cooldown, HUD, and
  distributions — not on-screen sheep.

## Run

  python Prototypes/JevSheepConductor/test_jev_sheep_conductor.py
  python Prototypes/JevSheepConductor/scenario_capture.py
  TYPESAFE_API_KEY=... python Prototypes/JevSheepConductor/scenario_capture.py

Outputs: `capture_log.txt` (HUD lines), `capture_report.json` (full
probability distributions + provenance per evaluation).

## Files

- `jev_sheep_conductor.py` — options, state, Jev 2xChoice call, fallback,
  cooldown/hysteresis arbiter, debug HUD.
- `scenario_capture.py` — five-beat scripted driver (48s, 2s evaluations).
- `test_jev_sheep_conductor.py` — authored-only, distributions, cooldown,
  determinism, HUD format.

## Runtime rules (enforced)

- 9 flock + 6 world options are closed sets; unauthored Jev output is
  refused and falls back. No codegen, no assets, no file edits, no map
  mutation. Evaluations every 2s (phrases, not frames). MIN_HOLD 4s +
  margin/confidence gates stop twitching.

## Experiment 2 — shadow duet (awaiting key)

`shadow_duet.py` runs the same 48s snapshots through fallback (arm A,
`live_enabled=False`) and live Jev (arm B), measuring judgment only.
Needs `TYPESAFE_API_KEY` in the environment; without it the script exits
2 and writes nothing — fallback is never mislabeled as Jev.

  TYPESAFE_API_KEY=... python Prototypes/JevSheepConductor/shadow_duet.py
  python Prototypes/JevSheepConductor/shadow_duet.py --selftest  # no key

Artifacts on a live run: `live_shadow_capture_log.txt`,
`live_shadow_report.json`, `LIVE_JEV_DUET_REVIEW.md` (five beats,
agreement rates, hysteresis holds, high-confidence disagreements,
golden-question notes).

## UE wiring (later, not this task)

Existing systems execute selections; Jev never touches them directly:

| ConductorState field | Trustworthy live source (to verify in editor) |
|---|---|
| bpm_intensity / beat_energy | Rhythm subsystem / audio-reactive presentation palette |
| player_distance_m / movement | Player controller / character velocity |
| resonance | Resonance/cymatics driver intensity |
| wind_direction_deg / strength | Environment wind actor or Morning Niagara lane |
| palette_state | PPV / palette subsystem, if exposed (else leave None) |
| seconds_since_last_response | Conductor's own clock (already live) |
| recent_interaction | Overlap/interact events on BP_ChoralSheep |
| current_behavior | Conductor's held state (already live) |

Execution mapping (authored responses, example owners):
GRAZE/TURN_TO_PLAYER/CHORAL_SWAY/PART_PATH -> ABP_ChoralSheep states;
SPIRAL_FORMATION -> flock placement/BP logic; RESONANCE_PULSE /
CRESCENDO_BURST -> existing VFX/audio + MPC; accompaniments ->
wind actor, palette/PPV weights, flower MIs, ripple MPC.
Debug HUD `format_hud()` mirrors to UMG later; keep it dev-only.
