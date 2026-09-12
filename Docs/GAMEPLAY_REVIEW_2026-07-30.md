# Gameplay Deep Review — 2026-07-30

> ## ⚠️ SECTION 2 (TELEPORT) IS SUPERSEDED — read this first
>
> **Corrected 2026-07-31.** Section 2 below was written at 21:14 on 2026-07-30.
> `Source/BS_GodFile/MelodiaIntegration/MelodiaTravelSubsystem.cpp` was written at 21:17–21:32 —
> **three minutes later** — and implements exactly what that section asks for. Four of its specific
> claims are now false:
>
> | Section 2 claim | Reality |
> |---|---|
> | Travel executor "MISSING: this is the whole gap" | `MelodiaTravelSubsystem.cpp:22` subscribes; `:92-113` executes; `:115-144` handles arrival |
> | `RequestTravel` broadcast — "nothing listens" | `MelodiaTravelSubsystem` is the single consumer |
> | `SetSpawnContext`/`GetSpawnContext` — "Nothing uses it" | Written at `:79`, read at `:61` and `:137`, consumed by `PlacePawnAtSpawn` `:146-193` (checks both `PlayerStartTag` and the `Tags` array) |
> | `MelodiaMapTransitionComponent` bypasses the allowlist | `MelodiaMapTransitionComponent.cpp:43-47` now routes through `UMelodiaTravelSubsystem::TravelTo` |
>
> Recommendation #4 in the ranking table ("route the transition component through `RequestTravel`")
> is likewise already done.
>
> **One claim in section 2 is still true:** `MelodiaSaveSlotLibrary.cpp:50` hardcodes `OpenLevel` to
> `L_MelusinaMorning` as a fallback when a slot carries no `currentMap`, and does **not** route
> through the travel authority. That is a genuine remaining bypass and is the only travel work left
> in code. Everything else in section 2 is editor work: allowlist the destination and tag the
> arrival PlayerStarts (`Docs/BLUEPRINT_WIRING_CHECKLIST_2026-07-30.md` §2).
>
> Sections 1 and 3 were re-checked on 2026-07-31 and remain accurate.
>
> **General rule this incident illustrates:** a doc's filename date is when it was *written*, not
> when it was last *true*. Check claims against source mtime before acting on them.

**Basis:** PIE test this evening. Battle UI good. Three reported gaps: rhythm not procing after
skills, no universal teleport, Quill loop unverified / not procing on ZenForest NPCs.

All three are **wiring gaps, not broken systems.** Every piece needed already exists.

---

## 1. Rhythm doesn't proc — unwired at *both* ends

Not a bug. The layer is doing exactly what Decisions 012 and 016 specify: nothing, safely.

### Reason A — nothing calls it

`UMelodiaJRPGPresentationRhythmComponent` is referenced by exactly four things:

```
MelodiaJRPGPresentationRhythmComponent.h / .cpp   (itself)
Tests/MelodiaIntegrationTests.cpp                 (my tests)
Content/Python/fix_npc_and_ui.py                  (a script)
```

**No Blueprint, no skill, no battle graph calls `RecordInputNow()` or `RecordTimingError()`.**
The component is an orphan. Nothing is wired to invoke it when a skill fires.

### Reason B — no music clock ever starts in the shipping lane

The only caller of `StartBattleClock` is:

```
Plugins/MelodiaCore/.../MelodiaBattleSession.cpp:437
    Audio->StartBattleClock(Rhythm->BPM);
    Audio->PlayBGMQuantized();
```

That is **MelodiaCore — the quarantined lane.** The stock TurnBasedJRPG battle never starts a clock,
and no Harmonix `UMusicClockComponent` is registered anywhere. So `HasMusicalTime()` is false, and
`RecordInputNow()` correctly returns a silent zero-scalar result by design.

Even if you wired Reason A today, you would still see nothing until Reason B is fixed.

### What it needs

Two wires, in this order:

1. **Start a clock in the stock lane.** Either register a Harmonix `UMusicClockComponent` from a
   battle presentation actor (the contract path, needs the MIDI asset), or call `StartBattleClock`
   on a `UMelodiaAudioComponent` at battle start from the stock battle graph (the cheap path, works
   today, no content needed).
2. **Call `RecordInputNow()`** from the skill's presentation graph at the moment the player confirms
   the command.

Verify with the console variable already built for this: `melodia.Rhythm.Disable 1` must leave the
skill playing identically at full value. If it does not, the layer has become authority and that is
a Decision 016 violation.

**Cheapest proof:** the Quartz path. `StartBattleClock(128.0f)` at battle start plus one
`RecordInputNow()` call gives a visible, testable rhythm layer with zero content authoring. Harmonix
and the authored MIDI can replace it later without touching the call sites — that is the whole point
of routing through `UMelodiaMusicClockSubsystem`.

---

## 2. Universal teleport — four competing paths, no authority

This is the same second-authority pattern the project keeps hitting, in a new domain.

### What exists today

| Path | Validates? | Spawn point? | Notes |
| --- | --- | --- | --- |
| `UMelodiaNarrativeSubsystem::RequestTravel(LevelId)` | ✅ allowlist `TravelLevelIds` | ❌ | Broadcasts `OnTravelRequested` — **and nothing listens** |
| `UMelodiaMapTransitionComponent` | ❌ | ❌ | Overlap volume → `TransitionToMap()` → direct `OpenLevel`. Bypasses the allowlist entirely |
| `UMelodiaSaveSlotLibrary` | ❌ | ❌ | Hardcoded `OpenLevel` to `L_MelusinaMorning` |
| Blueprint travel nodes | ❌ | ❌ | The literal `/Game/ZenForestTest` string in Dreamstate |
| `SetSpawnContext` / `GetSpawnContext` | — | — | Added to the record today. **Nothing uses it** |

So travel currently happens four different ways, only one of which is validated, none of which
place the player deliberately on arrival, and the validated one has no consumer.

### The design

One path, following the adapter pattern already proven by Persona:

```text
Any teleport source (overlap volume, Quill intent, Orrery UI, dialogue choice)
      ↓  calls
RequestTravel(LevelId)                        -- validates against TravelLevelIds
      ↓  SetSpawnContext(LevelId, SpawnTag)   -- records WHERE to arrive
      ↓  broadcasts OnTravelRequested
      ↓
ONE travel executor listens                   -- MISSING: this is the whole gap
      ↓  OpenLevel
      ↓  on arrival: read GetSpawnContext(CurrentMap), find the tagged PlayerStart,
         place the pawn, clear input mode, fade in
```

The missing piece is small: **one listener that performs travel and one arrival handler that places
the pawn at the tagged spawn.** Everything upstream already exists.

Then `MelodiaMapTransitionComponent` changes from calling `OpenLevel` directly to calling
`RequestTravel` — which immediately gives every overlap volume in the game allowlist validation and
spawn placement for free.

### Why this matters beyond tidiness

Right now nothing guarantees where the player lands. With Morning → KaleidoNave → ZenForest, the
player arrives at whatever `PlayerStart` the engine picks first — KaleidoNave has **four**. That is
a coin flip on every transition, and it will read as a bug long before it reads as a spawn-point
problem.

---

## 3. Quill loop + ZenForest NPCs

### Current state

`ZenForestTest.umap` contains the tag `MelodiaQuestNPC` but **zero Quillscript references.** The
NPCs are tagged for the Persona quest system and their interaction components route to quest
notifications, but no dialogue script is bound to them.

So: quests fire, dialogue does not. That matches what you saw.

### What it needs

1. Bind a `UQuillscriptAsset` to each ZenForest NPC's interaction path, same as the Morning Sir
   interaction already does.
2. Author the scripts with allowlisted `melodia:` intents — and this is the moment to wire
   **Decision 018**: one `melodia:stat:<id>:<delta>` choice. That single line closes the Persona
   loop end to end, and ZenForest NPCs are the natural place for it.
3. Verify the terminal path: dialogue completes → Quill resumes exactly once → no stale input mode
   or lingering dialogue widget.

### The loop verification worth doing once

```text
talk to NPC → Quill plays → choice raises a social stat → stat gates a quest
  → quest gates a minimap marker → marker leads to the encounter
  → stock battle → typed result → flag set → autosave
  → reload → stat and flag both survived
```

Every arrow exists in code. Running it once end to end is the single most valuable playtest
available, because it proves the whole Persona-lite spine in one pass rather than piecemeal.

---

## Recommended order

Ranked by value per hour, with the reasoning.

| # | Task | Why here |
| --- | --- | --- |
| 1 | **Travel executor + spawn placement** | Fixes a coin-flip you will otherwise hit on every single transition, including the new KaleidoNave route. Unblocks everything downstream. |
| 2 | **Quill on ZenForest NPCs + one stat intent** | Closes the Persona loop. Small, and it converts four separate half-built systems into one demonstrable thing. |
| 3 | **Rhythm: Quartz clock + one `RecordInputNow()`** | Cheap path, no content needed, gives you something visible to tune. Harmonix swaps in later with no call-site changes. |
| 4 | Route `MelodiaMapTransitionComponent` through `RequestTravel` | Retires a bypass path once #1 exists. |
| 5 | Save round trip including a social stat | The standing gate. Now meaningfully testable because #2 gives it something real to persist. |

Items 1–3 are each roughly a session. None require new systems — all three are connecting things
that already exist and currently sit unwired.

---

## What is genuinely healthy

Worth stating, since the gaps above are all wiring:

- Battle UI works (your PIE test)
- Stock JRPG battle authority is intact and uncontested
- Narrative record v2 persists, migrates, and round-trips through a SaveGame archive (tested)
- Music clock degrades correctly with no clock rather than fabricating a beat (tested)
- The packaged build cooks clean with the full route
- Monolith is healthy and indexing

The systems are sound. They are just not talking to each other yet, and that is a much better
problem to have than the alternative.
