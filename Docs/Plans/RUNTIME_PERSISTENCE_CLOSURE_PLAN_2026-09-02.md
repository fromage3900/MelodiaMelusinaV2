# Melodia Runtime Persistence Closure Plan — 2026-09-02

## Purpose

Close the current runtime-integration layer without rewriting the working combat stack.

> **Phoenix remains the turn-based combat scaffold. MelodiaCore / UMelodiaRhythmCombatSubsystem remain the rhythm execution authority. MelodiaWardrobe remains wardrobe authority. FMelodiaNarrativeRecord remains the canonical persistence record. Convergence is the glue. Starskiff/world systems consume restored state; they do not invent a second save authority.**

This plan applies the strongest production lessons from the Runtime Closure Atlas, especially Akuma's explicit load-state / stale-write discipline and Embermere's validate-before-mutate / idempotent-restore discipline.

---

## Verified project state

### Combat / rhythm — freeze the authority model

`Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.h`

- one battle-scoped rhythm combat authority;
- one authoritative session-result path;
- duplicate-session rejection;
- `UseSkillWithRhythm` defers the stock skill until the rhythm scalar exists;
- Phoenix/JRPG stock resolver still owns damage/status/turn/victory/defeat;
- `InvalidateSession()` already exists for battle-end/save-recovery/HUD teardown;
- rhythm subsystem does not own save mutation.

**Do not move persistence into this subsystem.**

### Wardrobe — already canonical-record-backed

`Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaWardrobeSubsystem.h`

- GameInstanceSubsystem is wardrobe state authority;
- owned/equipped state is stored through the canonical narrative record;
- grant/equip validates catalog data before permanent mutation;
- ownership gives durable idempotency;
- purchases already use preflight + rollback semantics;
- traversal capabilities are derived read-only from equipped/unlocked forms.

**Extend restore validation around this authority; do not create a second wardrobe save object.**

### Canonical persistence — existing v5 authority

`Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeTypes.h`

`FMelodiaNarrativeRecord::CurrentVersion == 5` already persists:

- narrative flags;
- Quill payload;
- encounter receipts;
- consumed intent/reward IDs;
- quest state;
- social stats / bonds / phase;
- spawn context;
- `OwnedCosmeticIds`;
- `EquippedCosmeticIds`;
- wardrobe pull timestamp;
- logical water gameplay state.

`UMelodiaNarrativeSubsystem` already owns migration, restore, reset, sync-to-save and restore-from-save.

### Important audit correction — Akuma-style load-state split already exists

`Source/BS_GodFile/MelodiaIntegration/MelodiaSaveSlotLibrary.h/.cpp`

Melodia already distinguishes:

- `Missing` — no slot exists;
- `Refused` — slot exists but cannot be safely loaded;
- `LoadedNarrativeRestored`;
- `LoadedNarrativeDegraded`.

`LoadCanonicalJRPGSlotDetailed()` also preflights the embedded `melodiaNarrativeRecord` and verifies that it can migrate before invoking the stock load path.

**Therefore do not add another save-resolution enum.** The Akuma lesson is already substantially implemented at the slot boundary. The next gap is deeper candidate validation + deterministic restore proof.

---

## Runtime ownership target

```text
Phoenix turn system
    |
    v
UMelodiaRhythmCombatSubsystem
    |  authoritative performance result only
    v
stock battle resolver
    |
    v
battle outcome / rewards
    |
    v
UMelodiaNarrativeSubsystem
canonical FMelodiaNarrativeRecord
    |
    +-------------------+--------------------+
    |                   |                    |
    v                   v                    v
Wardrobe           Convergence          Starskiff
state authority    runtime owner        runtime owner
    |                   |                    |
    +-------------------+--------------------+
                        v
              presentation / traversal /
              world-response rebuild
```

Persist stable facts. Rebuild runtime objects. Never serialize live rhythm sessions, battle objects, delegate bindings, animation state, transient physics, or duplicated derived capabilities.

---

## Reference patterns to adapt

### Akuma — preserve three semantic outcomes

Melodia's existing `Missing` / `Refused` / loaded split must remain the outer contract.

Rules:

- only `Missing` may lead to an explicit new-game creation path;
- a valid loaded record may intentionally contain an empty wardrobe;
- `Refused` must never silently become "new game" or overwrite the existing slot;
- degraded/failed load must remain visible to UI/recovery code.

### Akuma — stale async writes must not win

Before adding any generation counter or write queue, prove whether the current stock JRPG save path actually performs overlapping async writes.

If it does, add the smallest stale-write guard that guarantees:

```text
snapshot A starts
snapshot B starts later
B represents newer state
A finishes after B
=> A can never become the final authoritative slot state
```

Do **not** add complexity if current writes are synchronous and serialized.

### Embermere — validate complete candidate before mutation

Target restore flow:

```text
READ
  -> MIGRATE CANDIDATE
  -> VALIDATE CANDIDATE
  -> COMMIT CANONICAL RECORD
  -> REBUILD RUNTIME REPRESENTATIONS
```

Validation must happen before the first canonical mutation.

### Embermere — repeat load is a first-class test

Loading the same save twice must equal loading it once.

Forbidden second-load effects:

- duplicate outfit bonuses;
- duplicate Convergence contribution;
- duplicate traversal capability registration;
- duplicate delegate binding;
- repeated rewards;
- repeated Starskiff unlock/grant;
- resurrected battle or rhythm state.

---

## Golden runtime-closure gate

1. Start from an explicit new-game fixture.
2. Equip one approved outfit/form.
3. Confirm one observable outfit-derived capability.
4. Use Starskiff traversal / encounter entry.
5. Enter one Phoenix battle.
6. Execute one Melodia rhythm skill through `UseSkillWithRhythm`.
7. Resolve one Convergence-visible consequence.
8. Receive one persistent reward/state change.
9. Save.
10. **Exit the process completely.**
11. Launch a fresh process.
12. Load.
13. Verify the full logical state vector.
14. Load the same slot again.
15. Verify zero duplication or drift.

### Required state vector

- owned cosmetic set exact;
- equipped map exact;
- outfit visuals rebuilt correctly;
- outfit-derived gameplay capability active exactly once;
- Starskiff durable state exact;
- Convergence durable facts exact;
- encounter receipt exact;
- logical water/world state exact;
- no active rhythm session after load;
- no pending rhythm request after load;
- no live Phoenix battle object restored;
- second load produces the same logical vector.

---

## Implementation phases

### P0 — candidate-validation seam (START HERE)

The current slot preflight proves only that the save contains the correct struct and that the record can migrate. Extend the restore path with a **pure/pre-commit validator** for the v5 record.

Intrinsic checks should live with the canonical persistence layer. Subsystem-specific semantic checks should remain with the subsystem that owns those semantics so module dependencies do not invert.

First wardrobe invariants to prove:

- every equipped cosmetic is present in `OwnedCosmeticIds`;
- duplicate/invalid slot state cannot commit;
- intentionally empty `EquippedCosmeticIds` is valid;
- unknown/unresolvable cosmetic IDs fail closed at the wardrobe validation seam;
- wrong-slot cosmetic mappings fail closed;
- invalid candidate leaves the currently running canonical record unchanged.

### P1 — deterministic rebuild hooks

After a successful canonical commit:

- Wardrobe rebuilds visual presentation from the equipped map;
- traversal capability registry derives from Wardrobe state rather than persisted duplicate flags;
- Convergence recomputes derived runtime values from persistent facts;
- Starskiff rebuilds from logical persistent facts;
- water/PCG rebuilds from existing logical save data;
- UI observes post-restore events but does not mutate the restore candidate.

### P2 — idempotency tests

Add tests for:

- empty wardrobe restore;
- one valid outfit restore;
- invalid equipped-not-owned candidate;
- unknown cosmetic candidate;
- wrong-slot candidate;
- valid record loaded twice;
- no duplicate capability / presentation application on second load.

### P3 — Starskiff / Convergence owner audit before schema v6

Before adding any new SaveGame fields:

- locate the actual runtime owner for Starskiff state;
- locate the actual runtime owner for Convergence state;
- classify each candidate field as `persistent fact`, `derived runtime`, or `presentation only`;
- persist only stable facts;
- add a v5 -> v6 migration only once semantics are locked.

Prefer logical state such as route/spawn/mode/unlock/condition IDs over raw transforms or velocities.

### P4 — save-write ordering proof

Audit the actual stock save transaction for sync vs async behavior.

- if synchronous/serialized: document and do nothing;
- if overlapping async writes are possible: add sequence/generation protection or serialized queue;
- test an intentionally reordered completion case.

### P5 — full restart + packaged proof

In-memory serialize/deserialize is insufficient.

Required final proof:

```text
Save -> terminate -> fresh launch -> load -> assert -> load again -> assert
```

Then repeat in a packaged build.

---

## Rhythm restore boundary

Do not persist rhythm session state.

At restore / recovery / battle teardown boundaries, use existing authority seams to guarantee:

- active rhythm session invalidated;
- deferred stock skill cannot fire after restoration;
- pending effect request cannot leak into the restored battle/world;
- restored save never recreates a live timing session.

Do not add a second rhythm state machine to accomplish this.

---

## What not to rewrite

Freeze unless a failing closure test proves otherwise:

- Phoenix turn selection;
- Phoenix stock resolver;
- `UMelodiaRhythmCombatSubsystem` authority model;
- `UseSkillWithRhythm` ordering;
- MelodiaCore grading / note highway authority;
- `EMelodiaLoadSlotResult` outer load-state contract;
- Wardrobe canonical-record ownership;
- wallet authority;
- Quill persistent-data authority;
- existing logical water-save model.

Do not import Akuma or Embermere wholesale. Extract contracts and failure tests.

---

## Acceptance gates

**R0 — Single authority**  
Exactly one owner for every mutation.

**R1 — No destructive defaults**  
`Missing` is not the same thing as `Refused`; intentionally empty loaded state remains authoritative.

**R2 — Atomic restore**  
Invalid candidate causes zero canonical mutation.

**R3 — Idempotency**  
Second load equals first load at the logical state-vector level.

**R4 — Restart survival**  
Golden slice survives a full process restart.

**R5 — Stale-write immunity**  
If writes are async, an older snapshot cannot beat a newer one.

**R6 — Package proof**  
The same closure proof passes outside PIE.

---

## Active implementation-session order

1. **DONE — audit current load-state contract.** Existing `EMelodiaLoadSlotResult` is sufficient; do not duplicate it.
2. Audit `RestoreNarrativeRecord` / `RestoreNarrativeRecordFromSave` for partial mutation and post-restore side effects.
3. Locate the cleanest candidate-validation seam without introducing a BS_GodFile <-> MelodiaWardrobe circular dependency.
4. Implement intrinsic v5 candidate validation.
5. Add Wardrobe-owned semantic validation for equipped/owned/catalog/slot invariants.
6. Add repeat-load/idempotency tests.
7. Trace Starskiff and Convergence runtime owners.
8. Define stable persistent facts; only then consider schema v6.
9. Audit save-write ordering and add protection only if a real race exists.
10. Run restart proof, then packaged proof.

---

## Session stop conditions

Stop and investigate instead of expanding scope if:

- a second SaveGame authority appears necessary;
- Phoenix must be forked just to persist Melodia state;
- rhythm result/session objects appear necessary to save;
- outfit gameplay cannot be reconstructed from equipped IDs + authoritative progression facts;
- Convergence cannot distinguish durable facts from derived runtime state;
- Starskiff requires transient physics serialization rather than logical respawn/state;
- candidate validation itself creates a reverse/circular module dependency;
- validation failure partially mutates canonical state.

---

## Definition of success

```text
Outfit -> Starskiff -> Encounter -> Phoenix command -> Rhythm phrase
-> Convergence consequence -> Reward -> Save -> Quit
-> Relaunch -> Load -> same state -> Load again -> no duplication
```

That is the runtime-closure milestone: not more interconnected prototypes, but a restart-safe game runtime.