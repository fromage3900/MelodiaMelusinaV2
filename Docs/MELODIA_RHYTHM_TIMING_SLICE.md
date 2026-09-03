# Melodia Rhythm Timing Slice

Status: planned, presentation-only

## Purpose

Add a rhythm-game hit grade to the already-proven Melusina Focus Attack without
creating a second battle authority. The JRPG battle controller remains the sole
owner of damage, effects, turn release, and terminal results.

## First mechanic

The Focus Attack montage supplies one authored contact point through the existing
`BP_UseSkillN` notify. A presentation adapter records the player's timing input
relative to that contact point and classifies it as:

- `Perfect`
- `Good`
- `Late`
- `Miss`

The initial slice is telemetry and feedback only. It may drive a hit flash,
sound layer, camera response, and a small UI label. It must not change damage,
apply an effect, start another montage, or release the turn.

## Timing contract

```text
command accepted -> montage starts -> one BP_UseSkillN notify -> JRPG resolves
                  \-> timing grade observes the same contact point
```

The timing adapter must be idempotent per command instance. A command instance
may produce at most one grade, and a missing input must resolve to `Miss` without
blocking the JRPG attack.

## Incremental gates

1. **Instrumentation:** record montage start, contact time, input time, and
   grade; no gameplay mutation.
2. **Presentation:** show the grade and vary cosmetic feedback; repeat Focus
   Attack and verify one command, one montage, one notify, one damage result,
   and one turn release.
3. **Bounded bonus (later):** only after the Quill -> JRPG -> Quill authored
   loop and save gates pass, consider a deterministic optional bonus. A missed
   rhythm input must retain a valid ordinary attack path.

## Explicit exclusions

- MelodiaCore does not become battle or rhythm authority.
- No second damage/effect path is allowed from the timing adapter.
- No montage-completion callback may advance the turn.
- No global dissonance, modifier stack, roguelike phase, wardrobe, or ACFU
  system is imported for this slice.

## Acceptance evidence

- Edited assets compile with zero errors and warnings.
- Runtime logs show one accepted command, one montage, one notify, one JRPG
  resolution, one grade, and one turn release.
- Repeated Focus Attacks produce stable grades without duplicate damage.
- A no-input attack still completes normally.
