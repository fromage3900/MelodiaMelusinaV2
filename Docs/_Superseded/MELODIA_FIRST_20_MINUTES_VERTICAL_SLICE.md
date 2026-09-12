# Melodia — First Twenty Minutes Vertical Slice

> **Partially superseded (2026-07-26).** Preserve its authored character,
> companion, Dissonance, accessibility, and presentation ideas. The recursive
> expedition/roguelike promise and MelodiaCore rhythm authority are no longer
> requirements for the active fixed-loop MVP. Re-scope implementation through
> `MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`.

**Status:** Authored historical target; not current implementation authority.  
**Scope:** One 15–25 minute introduction to Melusina, Sir Melodious, Songcraft, Dissonance, and the recursive-expedition promise.

## Player promise

By minute twenty, a new player understands that Melusina is emotionally strained; Sir Melodious, her cockatoo, anchors the power in her music; timing enriches tactical combat without hard-failing it; Dissonance changes both her world and abilities; and a cleared doorway leads to another variable expedition.

## Story and gameplay timeline

| Minute | Beat | Player learning |
|---|---|---|
| 0–3 | Melusina wakes from a disturbed dream. Sir Melodious is missing from his perch; her first note harmlessly fizzles. | Her music and emotional state are linked; his absence matters. |
| 3–6 | Follow distant chirps and musical motes through the garden to an overlook. | He is a character, not an icon; his flight path previews future traversal. |
| 6–9 | Reunion and short call-and-response. A Resonance Bond is restored; use Basic rhythm input against a harmless Dissonant Echo. | Timing improves power but does not lock progress. |
| 9–12 | A memory trigger shifts the garden from Clear Resonance to Strain/Rupture. Audio detunes and the route becomes surreal but readable. | Dissonance is emotional, visual, and mechanical. |
| 12–16 | Fight a Sakura Phantom: Basic, one Songcraft skill, SP, grades, toughness break, enemy response, victory. Sir Melodious visibly empowers the skill. | Tactical command plus musical execution; companion bond is gameplay. |
| 16–19 | The restored echo opens the first Resonant Door. Complete a tiny seeded expedition: Room A, blessing/burden choice, Room B/encounter, exit. | Future journeys are variable and renewable. |
| 19–20 | Return with a recorded seed/reward. Sir Melodious reacts; a second sealed doorway appears. | Completion changes the hub and promises the recursive loop. |

## Slice system rules

### Resonance Bond

```text
Absent -> Reunited -> Resonant -> Strained
```

- `Absent`: tutorial-only; Songcraft fails safely or is visibly weak.
- `Reunited`: Sir Melodious is present and begins to support the player.
- `Resonant`: standard potency; Perfect/break can trigger a companion flourish.
- `Strained`: a declared, bounded modifier alters selected effects but never input validity.

For this slice, Sir Melodious may be a follow/presentation and battle-anchor actor. Direct player flight is a later feature, not a fake toggle for the demo.

### Dissonance Profile

Start with one data asset containing `Tier`, `SongcraftModifier`, `AudioProfile`, `MaterialProfile`, `EncounterModifier`, and `Accessibility` settings. Use Clear, Strain, and Rupture. Do not secretly alter timing windows. Reduced-distortion and intensity warning options are required before graphic surreal/body-horror imagery is introduced.

### Recursive expedition contract

```text
RunSeed + DoorwayID + DissonanceTier
  -> Room A -> Blessing/Burden -> Room B/Encounter -> Exit/Reward
```

Record seed, room IDs, enemy IDs, modifier, result, and reward. The same seed must replay the same declared micro-run before the team builds a larger dungeon generator.

## Task-by-task authoring plan

### 0. Lock canon and assets

1. Confirm Sir Melodious's canonical source FBX, textures, skeleton, and animation set.
2. Import to `/Game/Melodia/Characters/SirMelodious/`; create materials, physics asset, animation blueprint, and `BP_SirMelodious`.
3. Author his character sheet: personality, independent desire, relationship with Melusina, and why he is the resonance anchor.
4. Create stable IDs: `Companion.SirMelodious`, `Doorway.FirstEcho`, `Dissonance.GardenRupture`, and `Run.FirstDoor`.
5. Verify mesh, textures, idle/fly/land, collision, follow offset, and references in UE.

**Gate:** He is a placeable Unreal actor, not only a Blender-stage asset.

### 1. Author the reunion hub

6. Choose one canonical map (`ZenForestTest` or a new `L_MelusinaMorning`) before level work; do not maintain two versions of the slice.
7. Build bedroom -> garden -> overlook, empty perch, failed-note prompt, and sound/mote path.
8. Implement companion perch/follow states and `ResonanceBond` state data.
9. Author reunion dialogue and a visible world reaction to the call-and-response.

**Gate:** A new player can explain Sir Melodious's importance without a codex.

### 2. Make Dissonance playable

10. Create `DA_DissonanceProfile_GardenRupture` and bind it to existing audio/material/post-process hooks.
11. Add reduced-distortion and intensity options; set a reviewed visual-content boundary.
12. Author one hallucination that does not obscure route, telegraph, or objective.
13. Add one Rupture encounter modifier, not random stat inflation.

**Gate:** The player sees, hears, and understands the state change with accessibility on/off.

### 3. Finish one battle

14. Use the Sakura Phantom with a distinct silhouette and readable encounter marker.
15. Human-PIE test Basic, one Songcraft skill, SP, grading, toughness break, enemy response, victory, and return to exploration.
16. Add Sir Melodious battle presentation: resonance pulse and a Perfect/break flourish.

**Gate:** A player can name the companion's and Dissonance's combat effects after victory.

### 4. Prove the first doorway

17. Author three room chunks and two encounter variants.
18. Implement seed-backed run recording before random selection.
19. Assemble `Room A -> choice -> Room B`; give one blessing and one burden immediate, readable effects.
20. Return to the hub with changed dialogue/visual state and a second unopened doorway.

**Gate:** same seed = same run; different seed = declared variation without broken progress.

### 5. Playtest, capture, cut scope

21. Run two new-player tests with reduced distortion off/on.
22. Measure time, input recovery, companion comprehension, Dissonance readability, and doorway-loop comprehension.
23. Capture a full run, companion reunion, accessibility comparison, and two run seeds.
24. Defer direct flight control, full dungeon generation, party roster, inventory/shop, mobile release, and further acts until these gates pass.

**Final gate:** a player completes the loop in 15–25 minutes and accurately describes the bond, emotional distortion, and replayable-doorway promise.

## Level structure amendment — Dreamstate and bedroom

The opening uses two deliberately small authored levels:

1. **`L_Melodia_Dreamstate`** — a short, controlled prologue/cutscene on a floating bifrost-like bridge in an open sky. It establishes emotional Dissonance and Sir Melodious's distance/absence; it is not an exploration map or procedural dungeon.
2. **`L_MelusinaMorning`** — the first controllable authored level, limited initially to Melusina's bedroom interior. It contains the bed/save sanctuary, empty companion perch, first failed Songcraft cue, and transition out to the later garden chapter.

`ZenForestTest` remains the combat smoke-test map until the bedroom and Dreamstate transitions are stable. Do not use it as the permanent bedroom level.
