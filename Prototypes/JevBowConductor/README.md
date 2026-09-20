# Jev Bow Conductor for Melusina (isolated prototype)

One bounded experiment: Jev conducts Melusina's weapon bow — selecting the
authored attack asset per musical phrase, plus a loose/hold gate. Jev creates
nothing; existing ABP/montage systems execute.

## Honest status

- 20/20 capture evaluations ran **jev-live** (this shell carries
  TYPESAFE_API_KEY in its environment only — never in any file).
- Contract tests: 26/26 (fallback path, deterministic, free).
- The capture arc reads musically: IDLE → BOW_V1 → BOW_V2 + 3× loose →
  IDLE. Two restraint notes, kept as data: Jev held IDLE through the DRAW
  beat (greet-before-celebrating, same conservatism as the sheep duet) and
  chose IDLE over LOWER_BOW at the exhale. Full distributions in
  `bow_capture_report.json`.
- Role labels (V1 = standard voice, V2 = louder voice, POLISHED = showcase)
  are interpretive and need the owner's eye against the actual anims. The
  asset mapping itself is verified on disk by the test.

## Run

  python Prototypes/JevBowConductor/test_jev_bow_director.py   # free, fallback
  python Prototypes/JevBowConductor/scenario_bow_capture.py    # needs key=live

Outputs: `bow_capture_log.txt`, `bow_capture_report.json`.

## Files

- `jev_bow_director.py` — 7 authored options + asset map, Choice+Noul in one
  system_one call, fallback, cooldown/hysteresis, debug HUD.
- `scenario_bow_capture.py` — five-beat scripted driver (40s, 2s phrases).
- `test_jev_bow_director.py` — asset presence, authored-only, beats,
  cooldown, determinism, HUD.

## UE wiring (later, not this task)

| BowState field | Trustworthy live source (verify in editor) |
|---|---|
| bpm_intensity / beat_energy | Rhythm subsystem / audio-reactive palette |
| target_distance_m / movement | Player controller / character velocity |
| resonance | Resonance/cymatic driver intensity |
| wind_strength | Environment wind actor |
| seconds_since_last_loose | Conductor's own clock (already live) |
| current_bow | Conductor's held state (already live) |

Execution: route the chosen asset name to the existing bow montage/ABP
branch (A_/AM_ range-attack slots); gate the loose notify on `loose=true`.
Mirror `format_hud()` to UMG later; dev-only.

## Blender staging gap (the missing files — still open)

No `.blend` source exists for `M_bow_002` anywhere (mesh + textures live
only as UE imports). Staging options, owner's call:
  a. Export M_bow_002 from UE to FBX, stage poses against
     `RawArt/Inbox/updated_melusina_rig_noclothes.fbx` on an audit copy.
  b. Author the bow fresh in Blender, treat UE mesh as reference.
Either way: audit copy first, never the live session file.
