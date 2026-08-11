# Melodia Dreamstate Prologue

**Status:** Authored opening specification  
**Level:** `L_Melodia_Dreamstate`  
**Target duration:** 90 seconds to 3 minutes; mostly controlled/cinematic.

## Purpose

Dreamstate is the emotional overture before the bedroom. Melusina walks a floating,
bifrost-like bridge through an impossible sky while a distant Sir Melodious calls to her.
The level establishes that her memory, resonance, and perception are unstable before the
player enters a grounded, intimate room.

It is not a combat arena, a large traversal map, or a procedurally generated run. Its job
is to make the later empty perch and failed Songcraft note emotionally legible.

## Beat sequence

| Beat | Event | System signal |
|---|---|---|
| Arrival | Melusina appears alone at the bridge threshold. | Clear but fragile music; restricted camera and path. |
| Call | Sir Melodious is heard/seen across the bridge but cannot be reached. | His motif is present; Resonance Bond reads `Absent`. |
| Fracture | The bridge repeats, stretches, or loses sections as a memory intrudes. | Dissonance shifts Clear -> Strain; non-critical materials/audio distort. |
| Choice | Player walks toward the call; one simple input/call-and-response can be used. | Input confirms intent, not a pass/fail rhythm test. |
| Fall/Wake | The bridge dissolves below or beyond Melusina; cut to bedroom wake-up. | Rupture ends on a clear transition, not player death. |

## Spatial rules

- One forward path, roughly 45–90 seconds at walking speed; no fall deaths.
- Use soft collision rails, fog, and camera framing rather than visible hard walls.
- Reserve the far end for Sir Melodious's silhouette or light, not a detailed character
  interaction before his Unreal import is complete.
- The bridge must have at least one clean visual state and one fractured state using the
  same geometry so Dissonance reads as transformation rather than asset replacement.

## Existing project candidates

- `SM_venetianbridge` under `/Game/Melodia/_PROJECT/MelusinasHouse/` is the preferred
  starting geometry for a quick bridge blockout.
- `MI_Sakura_Bridge`, the Starry Night/Impressionist sky materials, `MF_NikkiDreamGrade`,
  and the Sakura Dream sparkle system are visual candidates to test, not automatic final
  dependencies.
- No `Dreamstate` level currently exists; create it cleanly rather than altering a World
  Partition pillar or the ZenForest smoke map.

## First implementation tasks

1. Create `L_Melodia_Dreamstate` and place the bridge blockout plus start/end cameras.
2. Add one level-sequence or simple trigger-driven camera path; retain an accessible skip.
3. Create Clear and Strain material/post-process presets driven by one Dissonance profile.
4. Add placeholder distant-call audio and a temporary Sir Melodious silhouette/marker.
5. Transition deterministically to `L_MelusinaMorning`; spawn Melusina at the bed-facing
   camera with `ResonanceBond = Absent`.
6. Verify skip, transition, input recovery, and no fall/death loop in PIE.

## Acceptance gate

A new player can state: “Melusina is separated from Sir Melodious, something is wrong
with her world, and she has awakened somewhere safe,” before they receive control in the
bedroom.
