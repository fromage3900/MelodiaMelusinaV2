# Melodia Systems Composition Contract — 2026-07-30

> **⚠️ Sections 2 and 3 are HISTORICAL (annotated 2026-07-31).**
> They describe `SocialStats` as `Transient` with no record field ("right now they evaporate on
> reload") and `FMelodiaNarrativeRecord::CurrentVersion` as still 1. Both were true when written and
> were superseded **within this same file** by §5a, appended later the same day. Source confirms
> §5a: `MelodiaNarrativeTypes.h:42` is `CurrentVersion = 2`, `SocialStats` is a `SaveGame` record
> field, and the transient map is gone. A reader who stops at §2 will re-implement finished work.
>
> The "Not runtime-verified — editor open (PID 21272)" caveat is also stale: the native build has
> been green since 2026-07-30 (three successive builds), and a further green build ran 2026-07-31.
> The genuinely open item is the save round trip across a **full process restart**, which remains
> unproven.

**Purpose:** name the architectural pattern this project already uses, so every future system is
built the same way, stays in scope, and composes with the others instead of sitting beside them.

**Companion docs:** `Docs/FOUNDATION_LOCKIN_PLAN_2026-07-30.md` (sequencing) ·
`Docs/LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md` (lane authority) · `_DECISION_LOG.md`

---

## 1. The pattern already exists — it just has no name

`UMelodiaPersonaSubsystem` is the reference implementation. Every Melodia system that touches
stock JRPG state has independently converged on the same six-part shape:

| Part | Persona example |
| --- | --- |
| **Stable ID** — an `FName` that never changes, never a Blueprint path | `melodia_tuning_fork` |
| **DataAsset** — content authored as data, not code | `DA_MelodiaPersonaContent` |
| **Facade subsystem** — typed read model, no authority | `UMelodiaPersonaSubsystem` |
| **Typed request** — asks; does not act | `RequestEquip(UnitId, EquipmentId)` |
| **Stock authority resolves it** — the real state change | `WearEquipmentOnUnit` on `BP_JRPGPlayerController` |
| **Typed result broadcast** — presentation reacts | `OnEquipmentRequested`, `OnQuestStateChanged` |

Call this the **Melodia Adapter Pattern**. It is the reason Persona-lite passed its PIE smoke while
the overnight rhythm-combat trio had to be quarantined: the trio skipped parts 4–6 and wrote
outcomes directly.

### The checklist for any new system

Before writing a line of a new Melodia system, answer these. If any answer is "a new one," stop.

1. What stable `FName` identifies its things?
2. Which existing DataAsset holds its content — or does it genuinely need its own?
3. Which **stock** system already owns the state it wants to change?
4. What is the typed request that asks that owner to change it?
5. What does it broadcast so UI/VFX/audio can react?
6. What, if anything, must survive a save — and which field of `FMelodiaNarrativeRecord` holds it?

Question 6 is the one that gets skipped, and it is the expensive one.

---

## 2. `FMelodiaNarrativeRecord` is the bus, and it has a hole

`UMelodiaNarrativeSubsystem::SyncNarrativeRecordToSave` /
`RestoreNarrativeRecordFromSave` is the **single** persistence seam in the project. That is a good
design — one embedded, versioned record inside the canonical `BP_JRPGSaveGame` transaction, not a
second save system.

The consequence is absolute and worth stating plainly:

> **If it is not a field on `FMelodiaNarrativeRecord`, it does not persist. There is no other way.**

Current fields: `Version`, `Flags`, `QuillVariables`, `QuillPersistentData`, `ScriptCheckpoint`,
`ConsumedIntentIds`, `ActiveQuestIds`, `ConsumedRewardIds`.

### The hole

`UMelodiaPersonaSubsystem::SocialStats` is a `TMap<FName, int32>` marked `Transient`, and there is
no corresponding record field. **Social stats are the core currency of a Persona-lite game, and
right now they evaporate on reload.** `Docs/PERSONA_LITE_LOW_AGENCY_HANDOFF_2026-07-28.md` records
this as a known gap; it is the single highest-value schema addition available.

Fixing it is small — one `TMap<FName, int32> SocialStats` field, plus sync/restore — but it is a
save-format change, so it wants to land with a version bump and before content depends on it.

---

## 3. Decide the schema shape now, while `Version == 1`

Adding a field to a save record that no shipped save contains is free. Adding it after players
have saves costs an upgrade path forever. `FMelodiaNarrativeRecord::CurrentVersion` is still 1 and
no build has shipped — this window closes exactly once.

Reserve these now, even if nothing writes them for months:

| Field | Why reserve it now |
| --- | --- |
| `TMap<FName, int32> SocialStats` | The Persona-lite currency. Already exists transiently. |
| `TMap<FName, int32> BondRanks` | Confidant/social-link ranks. Persona-lite implies them eventually; retrofitting a rank axis is painful. |
| `int32 PhaseIndex` | Even if the game is "one dream = one phase," a monotonic counter costs 4 bytes and makes time-gated content possible later. Without it there is no way to express "this happened after that." |
| `TMap<FName, FName> SpawnContext` | Destination spawn tags for Orrery travel — `Docs/CORE_QOL_AUDIT_2026-07-29.md` already calls for "preserve a destination spawn tag in the existing narrative record." |

**Also add an upgrade function now.** A `MigrateRecord(FMelodiaNarrativeRecord&, int32 FromVersion)`
that currently does nothing is five minutes of work today and the difference between "old saves
load" and "old saves are gone" the first time the schema moves.

Note what deliberately does **not** belong here: rhythm calibration offset, volumes, reduced
motion, UI scale. Those are `UMelodiaGameUserSettings` — player preferences, not campaign state.
That separation is already correct; keep it.

---

## 4. Making the systems feed each other

The systems are currently a star around the narrative record, which is the right topology. What is
missing is that a few edges are not connected, so the loop does not close.

### The complete Persona-lite loop, once social stats persist

```text
Quill dialogue choice
   -> allowlisted intent            (UMelodiaNarrativeSubsystem validates)
   -> AddSocialStat                 (UMelodiaPersonaSubsystem)
   -> stat gates quest availability (GetAvailableQuests)
   -> quest gates minimap marker    (RequiredQuestId)
   -> marker leads to encounter     (stock BP_InteractionBattle)
   -> stock battle result           (stock JRPG controller -- sole authority)
   -> typed result                  (EMelodiaBattleResult)
   -> narrative flag + reward       (SetNarrativeFlag / GrantDialogueReward)
   -> flag unlocks next dialogue    (Quill reads melodia_ variables)
   -> autosave at the boundary      (SyncNarrativeRecordToSave)
```

Every arrow above already exists in code except `AddSocialStat` surviving a reload. **That one
field closes the loop.** This is the whole Persona-lite game, and it is roughly 80% built.

### Three concrete reuse wins available right now

**a. One ID for a skill, everywhere.**
`FMelodiaAbilityDefinition` already carries `AbilityId` and `StockSkillAssetId`. Make
`DA_MelodiaRhythmProfile.SkillId` **be** `FMelodiaAbilityDefinition.AbilityId`. Then the rhythm
profile, the tooltip, the battle skill, and the unlock level all key off one `FName`. Renaming a
Blueprint stops breaking anything.

**b. One gating predicate, two consumers.**
`UMelodiaPersonaSubsystem::GetVisibleMinimapMarkers()` filters markers on `RequiredQuestId`. The
Orrery travel adapter that `CORE_QOL_AUDIT` specifies needs `IsSphereUnlocked` — which is *the same
question*: "is this content available given quest state?" Extract one
`bool IsGatedContentAvailable(FName RequiredQuestId) const` and have both call it. Two features,
one rule, no drift.

**c. One reward route.**
Dialogue rewards go through `GrantDialogueReward` → `ConsumedRewardIds` (idempotent by
construction). Gatherable pickups and interaction props should route through *that exact function*,
not a parallel path. `LOWER_TIER_FOUNDATION_LOCK` already requires it; naming it here makes it the
default rather than a rule someone has to remember.

### The rhythm layer's place in the loop

The music clock feeds presentation only, and that is deliberate. But note it now has a legitimate
non-combat use that costs nothing: **musical time is a great source of ambient life.** Idle
animations, lantern flicker, UI breathing, and petal drift can all sample
`GetBeatPhase(VisualTimebase)` in exploration, not just battle. That makes the world feel scored
without the rhythm layer ever touching a gameplay decision — which is exactly the Persona-lite
tonal target.

---

## 5. Scope guard — reusability and scope are the same question

A system built to the pattern in §1 is cheap to add and bounded by construction: it cannot grow a
second authority because it has no mechanism to write state directly. A system built outside the
pattern is unbounded — the quarantined rhythm trio is the proof.

So the scope rule and the reuse rule are one rule:

> **New capability is expressed as new data against existing seams, not as new authority.**

Concretely, in scope: a new quest, ability, equipment ID, marker, rhythm profile, Quill script,
interaction prop, Orrery destination. Each is a row in a DataAsset plus, at most, a presentation
Blueprint.

Out of scope, permanently, without a new logged decision: a second battle manager, save class,
inventory, quest manager, HUD root, dialogue system, player controller, map-travel authority, or
beat clock.

### Sequencing rule

Do not author content against a seam before that seam has passed its runtime gate. The foundation
gates in `_VERTICAL_SLICE_SCOPE.md` exist for this reason — content authored against an unproven
save path has to be re-authored when the path changes.

---

## 5a. Status — native pass landed 2026-07-30

Items 1 and 3 of §6 are implemented and awaiting the closed-editor build. Decisions 013–015.

```text
Task attempted:      Persona-lite persistence foundation + project-wide musical time.
Files/assets changed:
  MelodiaNarrativeTypes.h            Version 2; +SocialStats, BondRanks, PhaseIndex, SpawnContext
  MelodiaNarrativeSubsystem.h/.cpp   +MigrateRecord (stepwise, refuses newer records);
                                     +GetSocialStat/AddSocialStat/GetBondRank/SetBondRank/
                                      AdvancePhase/Get|SetSpawnContext;
                                     RestoreNarrativeRecord now migrates instead of wiping
  MelodiaPersonaSubsystem.h/.cpp     transient SocialStats map REMOVED; reads/writes the record;
                                     +IsGatedContentAvailable, used by GetVisibleMinimapMarkers
  MelodiaMusicClockSubsystem.h/.cpp  +static Get / GetMusicBeatPhase / GetMusicPulse
  MelodiaAudioReactivePresentation   BeatPhase published outside battle too
Authority preserved: Stock JRPG owns turns/damage/results/save transaction. The record remains
                     embedded in BP_JRPGSaveGame, not a second save system. 009/011 intact.
Validation run:      Static only. Grep confirms no stale SocialStats member references and that
                     Persona initialises Narrative before use.
Observed result:     Not runtime-verified. Editor open (PID 21272); new reflected members and a
                     save-schema change cannot be hot-reloaded.
Unproven or blocked: The save round trip itself -- which is now also the acceptance test for
                     social-stat persistence.
Single next action:  Closed-editor build, then the PERSONA_LITE NOW save round-trip gate with one
                     social stat included in the assertions.
Do not touch:        Config/, stock BP_BattleUI, hair assets, environment art.
```

**Migration note for the first load after this build:** existing saves carry `Version == 1`.
`MigrateRecord` steps them to 2 with empty stat maps, which is the truthful value — no stats were
ever persisted before. Nothing is lost that existed.

## 6. Recommended order

Assumes the pending closed-editor rebuild lands first.

| # | Item | Why here |
| --- | --- | --- |
| 1 | Add `SocialStats` + reserved fields + `MigrateRecord` to `FMelodiaNarrativeRecord`, bump to Version 2 | Free now, expensive later. Batch it into the rebuild that is already queued. |
| 2 | Prove the canonical save round trip (`PERSONA_LITE` NOW task) | Everything downstream depends on it. Now covers social stats too. |
| 3 | Extract `IsGatedContentAvailable` | Ten minutes; unblocks the Orrery adapter cleanly. |
| 4 | Finish Skybound Refrain's conditional bonus | Last co-op mechanic; pure stock rules. |
| 5 | Harmonix content pass (MIDI asset, clock actor, first profile) | Needs the rebuild plus the content promotion out of `Experiments/`. |
| 6 | Orrery travel adapter on the registry | The first system built entirely to the pattern in §1 — treat it as the pattern's test case. |
| 7 | "How to add a system" one-pager derived from §1 | Write it once the Orrery pass proves the checklist is complete. |

Item 7 is what actually makes this reusable. The pattern is only real once someone can follow it
without reading the source.
