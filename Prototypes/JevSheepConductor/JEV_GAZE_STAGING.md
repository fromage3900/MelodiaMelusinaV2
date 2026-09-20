# JEV GAZE — in-engine staging runbook (FIRST IN-ENGINE PROOF)

Goal: one capturable moment. Melusina enters, flock turns, wind rises,
gaze holds, authored release. Nothing else.

## 0. Preconditions (do not skip)

- ONE editor instance. `tasklist | findstr UnrealEditor` shows one PID.
- Port 9316 answers: `python Tools/mcp_call.py` probe or
  `python Prototypes/JevSheepConductor/sheep_truth_probe.py` exits 0.
  Exit 2 with "editor unreachable" means a modal dialog is open on the
  workstation ("This asset editor has no docked tabs" seen 2026-09-19):
  dismiss it on the machine itself. Never kill the editor for this.
- `list_errored_blueprints` + `list_dirty_packages` checked first.
- For Director=JEV during capture, the editor process needs
  TYPESAFE_API_KEY in its environment (launch from a shell with it set).
  Without it the director runs Director=FALLBACK — still valid for
  staging geometry, camera, and timing; not valid as Jev proof.

## 1. Truth first (read-only)

1. `python Prototypes/JevSheepConductor/sheep_truth_probe.py`
2. Read `sheep_truth_report.json` and fill the hook table:

   | need | truth source |
   |---|---|
   | rotate a sheep (yaw) | CDO knob or `monolith_gaze_binding` actor-set |
   | head weighting | bone/socket name from sheep-bones, else whole-body yaw only |
   | existing awareness radius | CDO value or interaction_radius_cm=160 from ChoralSheepDefinition.json |
   | Melusina pawn to possess | pawn class from probe (step 5) |
   | wind | staged actor or authored scripted ramp (provenance=scenario) |

3. Do NOT invent missing assets. If no Melusina pawn exists, stage with
   the default pawn and say so in the capture notes.

## 2. Isolated stage (reversible by deletion)

- DUPLICATE (never edit in place):
  `/Game/Melodia/Levels/Opening/L_MelusinaMorning`
  -> `/Game/Melodia/Levels/Opening/L_JevSheepGaze_PROOF`
  (Morning is a 14KB shell; the duplicate is the whole isolation.)
- Place in the duplicate only: 3x BP_ChoralSheep (triangle, 2-3m apart),
  player start facing them from ~12m, camera framing flock + approach
  lane. No other map or system is touched.
- Save ONLY the duplicate map. Touch nothing else.

## 3. Rehearse the loop (external director, zero asset writes)

- `monolith_gaze_binding.py` (next to this file at staging time) polls
  PIE world state each 2s phrase: player distance, speed, wind01.
- Each phrase calls `SheepGazeDirector.tick()` (already built + tested:
  `test_jev_gaze_director.py` 22/22). Jev decides the middle; authored
  release owns the end; failsafe owns failure.
- Actuation uses the hook from step 1 (per-sheep yaw, eased, variance).
- Wind test: scripted authored ramp 0.2 -> 0.9 across phrases 3-4 while
  Melusina stands still at ~5m. Gaze must hold while Jev says TURN.

## 4. Capture A–E (effect must read without the HUD)

A. idle graze, B. Melusina enters, C. flock turns (staggered, eased),
D. gaze sustains as wind rises, E. authored release to idle.
Frames + assertion JSON side by side (proven `pie_smoke_runner.py`
pattern: `capture_pie_movement_clip` on the duplicate map).

## 5. Forbidden in this proof

Spiral, gold, crescendo, second Jev question, production-map edits,
sheep-architecture restructuring, blocking gameplay on the API.

## 6. Cleanup

Delete `L_JevSheepGaze_PROOF` (and HLOD sidecars if generated) when the
clip lands. The bridge code stays in Prototypes/JevSheepConductor/.
