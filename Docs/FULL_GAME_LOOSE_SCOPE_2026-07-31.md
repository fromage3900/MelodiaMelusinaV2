# Melodia — Full Game Loose Scope (North Star)

**Date:** 2026-07-31
**Status:** Reference only, deliberately loose. Not a commitment, not a plan of record, no code changed.
**Owner inputs (2026-07-31):** exploration > dialogue · ~12h main route · 4 movements · reunion-per-movement ·
found-family party (Melusina + Sir from the start) · duet-partner stays absent · 4th recruit is someone else.
**Anchors:** `Docs/MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md` (the slice this scope grows from),
`Docs/Research/MELODIA_BARD_GRIEF_HOOK_2026-07-31.md` (the emotional core), `Docs/MELODIA_IDENTITY_AND_LOOP_2026-07-30.md`
(musical naming; *music you cannot fail at*), `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaPartySubsystem.h` (the roster).

---

## 1. Structure model — exploration-forward

```
hub  →  Resonant Door  →  seeded expedition  →  return  →  changed hub  →  next reunion
```

- Exploration carries most playtime. QuillScript dialogue is **seasoning at the seams**, not the
  payload (owner's weight rule).
- The slice's recursive-door promise is the spine: `RunSeed + DoorwayID + DissonanceTier`, seed-backed
  runs that replay deterministically, rewards that change the hub.
- Each movement ends in a **reunion** that recruits a new party member and opens the next register.

---

## 2. Length budget — ~12h main route

| Movement | Target | Basis |
|---|---|---|
| 1 | ~3h | Reuses the proven 15-25 min slice loop, scaled to first full chapter |
| 2 | ~3h | Same systems, new register, first recruit joins |
| 3 | ~3h | Same systems, new register, second recruit joins |
| 4 | ~3h | Same systems, new register, third recruit joins, reunion arc closes |
| **Total** | **~12h** | 4 × proven-loop-with-new-content |

The feasibility argument: every movement reuses the same systems (resonance combat, seeded
expeditions, party roster, QuillScript seams). Growth is **content and register**, never new
machinery. This is how 12h stays a solo-dev-with-agents possibility.

---

## 3. The four movements

Musical naming per the Identity doc (a dream is a *movement*, its phases are *bars*). Each movement
carries a tonal register — the saturated/muted palette-split arc from the hook doc.

| Movement | Register (direction of travel) | Reunion | Recruit |
|---|---|---|---|
| 1 | Morning → first door; the slice's proven arc (empty perch → fizzle → first expedition → Sir anchor) | First door closes behind; hub gains a new doorway | **Recruit A** (placeholder) |
| 2 | Deeper dream register; the world starts to "listen" | Reunion at a place she has been before, now changed | **Recruit B** (placeholder) |
| 3 | Farthest register; the past-duet-partner's fragments peak (absent, felt, never met) | Reunion that does not resolve the old wound — grief and warmth coexist | **Recruit C** (placeholder) |
| 4 | Return register; the first time she is not late | The final reunion — Sir home, the road behind, the found family assembled | **Recruit D** (placeholder) — the "someone else" |

---

## 4. The found-family party — schema-supported today

- **Melusina + Sir Melodious are the tandem unit from the start.** Besties; she the bard, he the
  flight/companion anchor. Not recruits, not a reward — the base state.
- **4 recruits, one per movement**, added to the ordered roster via the existing pattern:
  `UMelodiaPartySubsystem::PartyPawnClasses` (index 0 = Melusina) + the recruit-acknowledgment
  pattern Sir already proves (`SetSirMelodiousExplorationUnlocked` — "the stock JRPG party has
  recruited a companion"). Each recruit = one roster entry + one acknowledgment call. **Zero new
  mechanics.**
- **Final roster ceiling: 6** (Melusina + Sir + 4 recruits).
- Each recruit is a new **answering voice** for the Resonance loop — re-opens the hook doc's parked
  "second resonance relationship" spot, scoped to party members only. Sir's "skills always answer
  Melusina's marks" rule extends: every recruit answers, no one stands alone.
- **Recruit identities are named placeholders** (`Recruit A/B/C/D`) for the owner to fill in.
  Role archetypes only, tagged loosely against the grief/abandonment themes for the owner to pick or
  discard: someone who stayed when others left · someone who also left and came back · someone who was
  always there and she never noticed · someone the road gave her.
- **The past duet-partner stays absent.** Fragments, half-melodies, an authored silence where a
  second voice used to answer. Never a recruit, never met, never resolved. The wound stays a wound;
  the family grows around it.

---

## 5. Content surface (rough counts — sanity, not spec)

| Item | Target |
|---|---|
| Boss-battles | ~4 (one per movement) |
| Authored places | ~4-6 (hub + one distinct register per movement) |
| Expedition room pool | Enough for the seeded-run contract; grows per movement |
| QuillScript beats | Seasoning, not payload — a handful per movement at the seams |
| Party roster | 6 ceiling (Melusina + Sir + 4) |
| Movement count | 4 |
| Main route | ~12h |

---

## 6. Hard limits

1. **Schema unchanged.** `PhaseIndex` / `SocialStats` / `BondRanks` / `melodiaNarrativeRecord` as-is;
   the roster already exists in `UMelodiaPartySubsystem`.
2. **No new subsystems or mechanics.** Everything lands on: resonance combat, seeded expeditions,
   party roster, QuillScript seams, pacing authority, music clock.
3. **Hook-doc guardrails hold:** no dead bird / no animal harm · no guilt-wound · no sanity/dream
   meter with teeth · OCD as ritual, never punishment · no on-screen diagnosis · reunion is the ending.
4. **Duet-partner stays absent** (owner's answer) — fragments only.
5. **Exploration > dialogue** is the weight rule, not a preference.
6. **`L_SakuraPath` art direction stays human-owned** (README boundary).

---

## 7. What this doc is NOT

Not a production plan, not a milestone list, not a task queue entry, not a commitment to ship all of
it. It exists so future agent sessions and the owner share one north star while the 20-minute slice
finishes. When the slice ships, this doc gets its first real revision.

*Authored 2026-07-31 from the owner's stated inputs. Reference only.*
