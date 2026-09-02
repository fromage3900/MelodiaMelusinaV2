# Melodia Runtime Persistence Closure Plan — 2026-09-02

## Purpose

Close the current runtime-integration layer without rewriting the working combat stack.

The governing rule for this lane is:

> **Phoenix remains the turn-based combat scaffold. MelodiaCore / UMelodiaRhythmCombatSubsystem remain the rhythm execution authority. MelodiaWardrobe remains wardrobe authority. FMelodiaNarrativeRecord remains the canonical persistence record. Convergence is the glue. Starskiff/world systems consume restored state; they do not invent a second save authority.**

This plan applies the strongest production lessons from the current Runtime Closure Atlas, especially the failure-mode contracts observed in Akuma's UE5.8 RPG framework and the validate-before-mutate / idempotent-restore discipline observed in Embermere.

---

## Current verified project state

### Combat / rhythm

`Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.h`

- single battle-scoped rhythm combat authority;
- exactly one authoritative session result path;
- duplicate-session rejection;
- `UseSkillWithRhythm` defers stock skill execution until the rhythm scalar exists;
- stock Phoenix/JRPG resolver still applies damage/status/turn/victory/defeat;
- explicit `InvalidateSession()` exists for battle-end/save-recovery/HUD teardown paths;
- rhythm subsystem does not own save mutations.

**Decision:** freeze this ownership boundary. Do not add persistence logic to the rhythm subsystem.

### Wardrobe

`Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaWardrobeSubsystem.h`

- GameInstanceSubsystem is wardrobe state authority;
- owned/equipped state reads/writes through the canonical narrative record;
- catalog validation happens before permanent mutation;
- grants are idempotent by durable ownership and session-local grant receipts;
- purchases already use preflight validation and rollback semantics;
- traversal capabilities are derived read-only from equipped/unlocked forms.

**Decision:** extend restore validation around this authority; do not introduce a second wardrobe save object.

### Canonical persistence

`Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeTypes.h`

`FMelodiaNarrativeRecord` is currently version 5 and already owns:

- narrative flags;
- Quill persistent payload;
- encounter receipts;
- consumed intent/reward IDs;
- quest state;
- social stats / bonds / phase;
- spawn context;
- `OwnedCosmeticIds`;
- `EquippedCosmeticIds`;
- wardrobe pull timestamp;
- logical water gameplay state.

`UMelodiaNarrativeSubsystem` already exposes migration, restore, reset, sync-to-save and restore-from-save functions.

**Decision:** new durable Starskiff / Convergence facts must enter this existing snapshot only after their stable identifiers and runtime owners are verified.

---

## Reference patterns to adapt

### Akuma pattern A — distinguish load outcomes

Never collapse these states:

1. **No existing save** — defaults may be seeded.
2. **Existing save loaded and validated** — exact persisted state is authoritative, including intentionally empty equipment.
3. **Existing save detected but load/validation failed** — do not seed defaults and do not auto-overwrite the damaged/unsupported save.

Melodia contract:

```text
SAVE RESOLUTION
    |
    +-- NoSave ----------> seed approved new-game defaults
    |
    +-- Loaded ----------> restore exact canonical state
    |
    +-- Failed ----------> fail closed; preserve runtime/save for recovery
```

### Akuma pattern B — serialize player-state writes

Do not allow older async snapshots to finish after newer snapshots and become authoritative.

Melodia target:

- one player/canonical-record write queue or generation counter;
- coalesce mutation bursts (equip -> convergence recalc -> traversal capability refresh) before disk write;
- world-state persistence may be independently scheduled only if ownership is explicit and it cannot overwrite player state.

### Embermere pattern A — validate complete candidate before mutation

Restore must be two-phase:

```text
READ -> MIGRATE -> RESOLVE -> VALIDATE EVERYTHING -> COMMIT
```

Before COMMIT, validate at minimum:

- schema version migrates successfully;
- every equipped cosmetic ID exists in the catalog;
- every equipped cosmetic is owned unless an explicit migration exception exists;
- each cosmetic belongs to the saved slot;
- referenced assets required for presentation resolve;
- persistent Convergence identifiers are known;
- persistent Starskiff identifiers/state enum values are known;
- logical world/water state validates;
- no live battle/rhythm session is restored as a runtime object.

If validation fails, the currently running canonical state remains unchanged.

### Embermere pattern B — restore is idempotent

Loading the same canonical record twice must produce the same state vector as loading it once.

Forbidden outcomes include:

- duplicate outfit bonuses;
- duplicate Convergence contribution;
- duplicate reward receipts;
- duplicate traversal capability registration;
- duplicated delegate bindings;
- repeated Starskiff grants/unlocks;
- repeated battle rewards.

---

## Target runtime ownership

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
    +-----------------------------+
                                  v
                     UMelodiaNarrativeSubsystem
                         canonical record
                                  |
        +-------------------------+------------------------+
        |                         |                        |
        v                         v                        v
MelodiaWardrobe            Convergence owner        Starskiff owner
(read/write through        (stable persistent       (stable persistent
 canonical record)          facts only)              facts only)
        |                         |                        |
        +-------------------------+------------------------+
                                  v
                       presentation / traversal /
                       world-response rebuild
```

No subsystem may restore another subsystem's live objects directly. Restore stable facts, then let each authority rebuild its runtime representation.

---

## Golden vertical-slice closure gate

The first closure proof is deliberately small:

1. Start from a known fresh-save fixture.
2. Equip one approved outfit/form.
3. Confirm its observable traversal or combat capability.
4. Use Starskiff traversal / encounter entry.
5. Enter one Phoenix battle.
6. Execute one `MelodiaCore` rhythm skill through `UseSkillWithRhythm`.
7. Resolve one Convergence-visible consequence.
8. Receive one persistent reward/state change.
9. Save.
10. **Exit the process completely.**
11. Launch fresh process.
12. Load.
13. Verify the complete state vector.
14. Load the same save again.
15. Verify no state duplicated or drifted.

### Required state vector

- equipped cosmetic IDs exactly match;
- owned cosmetic set exactly matches;
- outfit visuals rebuild correctly;
- outfit-derived gameplay capability is exactly-once active;
- Starskiff durable state matches;
- Convergence durable facts match;
- encounter receipt matches;
- world/water logical state matches;
- no rhythm session is active after load;
- no pending rhythm request survives load;
- no stock battle object is resurrected;
- second load produces an identical state vector.

---

## Implementation phases

### P0 — Save-resolution contract

Add an explicit load-resolution result at the canonical save bridge:

- `NoSave`
- `Loaded`
- `Failed`
- optionally `IncompatibleVersion` if it materially improves diagnostics.

Rules:

- only `NoSave` may seed defaults;
- `Loaded` may be empty and remains authoritative;
- `Failed` / incompatible must never cause new-game defaults to overwrite the slot;
- failure returns a machine-greppable reason.

**Do not** change Phoenix, rhythm grading, or damage flow in this phase.

### P1 — Two-phase canonical restore

Introduce a pure/preflight validator for `FMelodiaNarrativeRecord`.

Candidate workflow:

```text
Candidate = Save.Record
MigrateRecord(Candidate)
ValidateCanonicalRecord(Candidate, Reason)
if valid:
    RestoreNarrativeRecord(Candidate)
else:
    leave current NarrativeRecord untouched
```

Wardrobe validation must be catalog-first and fail closed, matching existing grant/equip behavior.

### P2 — Deterministic rebuild hooks

After a successful canonical commit:

- Wardrobe refreshes presentation from the equipped map;
- traversal capability registry rebuilds from Wardrobe, not duplicate persisted capability flags;
- Convergence recalculates derived runtime values from persistent facts;
- Starskiff runtime representation rebuilds from its persistent facts;
- water/PCG runtime rebuilds from logical save data;
- UI subscribes to post-restore observation events and never mutates the restored candidate.

### P3 — Save ordering / stale-write protection

Instrument canonical save writes with a monotonic generation/sequence number or a serialized request queue.

Acceptance:

```text
snapshot A starts
snapshot B starts later
A finishes after B
=> A MUST NOT become the final authoritative slot state
```

Prefer the smallest mechanism that works with the existing Phoenix/JRPG SaveGame path.

### P4 — Full restart automation / proof

Add or extend an automation proof that performs:

- save fixture creation;
- process/PIE restart boundary;
- load;
- state-vector assertions;
- repeat load;
- idempotency assertions.

An in-memory serialize/deserialize test does **not** close this gate.

---

## First implementation slice

### Slice A — Outfit restore safety

Before adding Starskiff fields, close the state that already exists.

Tests / assertions:

- existing save with empty `EquippedCosmeticIds` stays empty;
- existing save with one valid equipped cosmetic restores exactly once;
- unknown cosmetic ID rejects candidate before canonical mutation;
- equipped-but-not-owned ID rejects candidate unless a documented migration path says otherwise;
- cosmetic in wrong saved slot rejects candidate;
- loading the same valid record twice does not duplicate capability registration or presentation application.

### Slice B — Rhythm teardown at restore boundary

On save recovery / world teardown / restore initiation:

- invalidate live rhythm session;
- clear deferred stock skill references through the existing authority path;
- verify no pending effect request is applied after restore;
- do not persist rhythm session objects.

Do this by invoking existing lifecycle seams, not by adding a second rhythm state machine.

### Slice C — Starskiff / Convergence schema discovery

Before schema v6:

- locate the actual Starskiff runtime owner and durable state candidates;
- locate current Convergence runtime owner and durable state candidates;
- classify each field as `persistent fact`, `derived runtime`, or `presentation only`;
- persist only stable facts;
- add a v5 -> v6 migration case only when the field semantics are locked.

---

## What not to rewrite

Freeze unless a failing closure test proves otherwise:

- Phoenix turn selection and stock resolver;
- `UMelodiaRhythmCombatSubsystem` authority model;
- `UseSkillWithRhythm` ordering;
- MelodiaCore grading windows / note highway authority;
- Wardrobe's canonical-record ownership model;
- wallet transaction owner;
- Quill persistent-data authority;
- existing water logical-save approach.

Do not import Akuma or Embermere wholesale. Extract contracts and test methods.

---

## Acceptance gates

### Gate R0 — authority

Exactly one owner for every mutation.

### Gate R1 — no destructive defaults

Existing-empty and failed-load states cannot be mistaken for a new game.

### Gate R2 — atomic restore

Invalid candidate causes zero canonical mutation.

### Gate R3 — idempotency

Second load equals first load bit-for-bit at the logical state-vector level.

### Gate R4 — restart survival

A full process restart restores the golden slice.

### Gate R5 — stale-write immunity

Older async snapshot can never win over a newer committed state.

### Gate R6 — package proof

The same closure proof passes in a packaged build, not PIE only.

---

## Remote implementation session task order

1. **Audit current save bridge implementation** (`RestoreNarrativeRecord`, `RestoreNarrativeRecordFromSave`, save-slot helpers, BP save-class contract).
2. **Add save-resolution enum/result contract** without changing existing callers' success path.
3. **Add candidate validator** for existing v5 record, beginning with wardrobe invariants.
4. **Add tests for existing-empty vs missing vs failed.**
5. **Add repeat-load/idempotency tests.**
6. **Trace Starskiff and Convergence owners** before changing schema.
7. **Add durable fields + v6 migration only after owner audit.**
8. **Add save-write generation/serialization guard if the current JRPG path is actually async/racy.**
9. **Run full restart golden-slice proof.**
10. **Run packaged proof.**

---

## Session stop conditions

Stop and investigate rather than expanding scope if any of these appear:

- a second SaveGame authority is required to make the design work;
- Phoenix must be forked merely to persist Melodia state;
- rhythm result objects need to survive process restart;
- outfit gameplay effects cannot be reconstructed from equipped IDs + authoritative progression facts;
- Convergence cannot distinguish durable facts from derived runtime state;
- Starskiff state requires raw transient physics transforms rather than a logical respawn/state description;
- a validation failure partially mutates the canonical record.

---

## Definition of runtime-closure success

Melodia is considered through this integration gate when a player can:

```text
Outfit -> Starskiff -> Encounter -> Phoenix command -> Rhythm phrase
-> Convergence consequence -> Reward -> Save -> Quit
-> Relaunch -> Load -> same world/player state -> Load again -> no duplication
```

At that point the project has moved from interconnected prototypes toward a restart-safe game runtime.