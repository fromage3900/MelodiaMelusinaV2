# Procedural dungeon reactivation — analysis and staged plan (2026-08-14)

**Ask:** reactivate the procedural dungeon systems, tie them to existing levels, blessing/burden
mechanics, and UI traversal. Owner's framing: *"mainly just a procedural room builder that acts as
a spawner for roguelike mechanics — it doesn't really change the gameplay, just allows endless
dungeon generation and content loops."*

**That framing is exactly right, and it maps onto a clean split in the code.** The stack is in two
halves, and only one of them is quarantined. The room-builder half can go live today. The
persistence half cannot, for a specific reason (§3).

Decision 016 requires a logged decision to re-enable any quarantined class. This document is the
analysis that decision should be made against.

---

## 1. What is already live

| Thing | State |
|---|---|
| `ProceduralDungeon` plugin | **v3.8.3, already enabled** in `BS_GodFile.uproject` |
| `PCGExtendedToolkit` | already enabled |
| 22 dungeon/roguelike source files | present in `Plugins/MelodiaCore/Source/MelodiaCore/` |

Nothing needs installing. This is a wiring job, not an integration job.

## 2. The split — five clean classes, three quarantined

| Class | Quarantined? | Role |
|---|---|---|
| `RoguelikeRoomCustomData` | **clean** | Room metadata: type, NPC archetype, lighting preset |
| `MelodiaRoguelikeDefinitions` | **clean** | The 8-class definition hierarchy |
| `MelodiaRoomEntrance` | **clean** | Room ingress |
| `MelodiaRoomExit` | **clean** | Room egress |
| `MelodiaFirstDungeonGate` | **clean** | Gate actor, listens to `OnFirstDungeonUnlocked` |
| `MelodiaDungeonRunCoordinator` | **QUARANTINED** | Owns `ADungeonGeneratorBase`, drives a run |
| `MelodiaRoguelikeRunSubsystem` | **QUARANTINED** | Run lifecycle/state |
| `MelodiaRoguelikePersistence` | **QUARANTINED** | **3 SaveGames — the real problem, see §3** |

**The clean five are the room builder / spawner** — precisely what the owner described. They carry
no quarantine marker, no save authority, and no gameplay-rule ownership.

`RoguelikeRoomCustomData` already models blessing rooms as first-class:

```
ERoguelikeRoomType: Start | Standard | Elite | Boss | Shop | Treasure | Event | Blessing
```

with `Blessing UMETA(DisplayName = "Blessing (Altar Room)")`. Its documented flow is
`URoomData -> CustomData array -> URoguelikeRoomCustomData`, read by
`ADungeonGenerator::OnRoomAdded` to configure encounter triggers, lighting, NPCs, shops, treasure,
and blessing altars.

**Caveat found while reading:** `RoguelikeRoomCustomData.h` is in the "zero C++ includers" set.
The data model exists and the consumer is expected to be
`BP_RoguelikeDungeonGenerator` (Blueprint), which still needs a live interface/graph check.

**Content refresh:** the earlier statement that burden did not exist anywhere was too broad.
`WBP_BlessingBurden.uasset`, Figma blessing/burden card textures, and the two Blessing Altar
room levels are real tracked content. `Content/Melodia/DataStuctures/DT_Blessings.json` contains
26 authored blessing rows with cost/effect fields, but it contains **zero burden rows**, and no
native catalog/consumer was found for the JSON. The widget/presentation therefore cannot be
treated as a gameplay-ready blessing/burden system. The exact fail-closed boundary is now
captured in `specs/roguelike/melodia_blessing_burden_contract.v1.json` and its offline gate
`Tools/test_melodia_blessing_burden_contract.py`.

## 3. Why the persistence layer must not be re-enabled as-is

`UMelodiaRoguelikeProfileSaveGame` collides field-for-field with the canonical record:

| Roguelike profile save | `FMelodiaNarrativeRecord` | Verdict |
|---|---|---|
| `UnlockedCosmeticIds` | `OwnedCosmeticIds` (`:165`) | **Direct duplicate** — a second cosmetic-ownership authority, against the wardrobe |
| `CompanionBond` (int32) | `BondRanks` (`:132`) | Duplicate concept |
| `NarrativeMemoryIds` | `Flags` / `ConsumedIntentIds` | Overlapping |
| `Settings` | belongs in `UMelodiaGameUserSettings` | Wrong home |
| `EntitlementCache` | `UMelodiaEntitlementSubsystem` (also quarantined) | Duplicate |
| `DiscoveredDefinitionIds` | *no equivalent* | **Genuinely new — this one is needed** |

Re-enabling it means:

1. **A second save authority**, which is the stated reason for Decision 016 and the quarantine.
2. **A second cosmetic-ownership authority**, directly against `UMelodiaWardrobeSubsystem`.
3. **Risk to two gates that just passed.** `save_load` and `repeat_consume` were certified
   2026-08-14 against `FMelodiaNarrativeRecord` as the single persistence seam. A parallel
   SaveGame writing overlapping state is exactly what `repeat_consume` exists to catch.

**The good news:** `FMelodiaNarrativeRecord` already has the slots. `BondRanks` (`:132`) and
`PhaseIndex` (`:140`) are documented in-file as **reserved and never written** — they were designed
for this and left unwired. Run state belongs there, not in a fourth SaveGame.

## 4. Staged plan

### Stage 1 — room builder only (today, no quarantine change, no save risk)

Turn on the spawner and prove endless generation without touching run state or persistence.

1. Run the read-only `Content/Python/audit_roguelike_generator_readonly.py` and confirm
   `BP_RoguelikeDungeonGenerator` parent, `UMelodiaDungeonRecipeConsumer` interface,
   function graphs, and placement before any generation helper. Then inspect whether it
   reads `URoguelikeRoomCustomData` on `OnRoomAdded` (the C++ side has no includer).
2. Author `URoomData` assets for the room types, each with a `URoguelikeRoomCustomData` entry.
   Start with **Start / Standard / Blessing** — three types is enough to prove the loop.
3. Place a generator in an existing level. **`/Game/ZenForestTest` is the authority exploration
   map** and is the natural host.
4. Wire `MelodiaRoomEntrance` / `MelodiaRoomExit` for traversal between generated rooms.

**Acceptance:** rooms generate, differ by type, and the player can walk in and out. No run state,
no saving, no roguelike rules. This is the "doesn't change gameplay" layer, and it is genuinely
free of the quarantine problem.

### Stage 2 — the Sir connection (worth doing regardless)

`AMelodiaDungeonRunCoordinator` is **one of only two callers of `NotifySirRescued()`**, and no map
places it. That is directly implicated in the separate finding that Sir is unavailable on
Ctrl party-switch (see `_TASK_QUEUE.md` and the opening-flow analysis).

The opening-flow ladder currently dead-ends: `NotifyDreamstateCompleted()` has **zero shipping
callers**, so the phase never reaches `ZenExploration`, never `FirstDungeonUnlocked`, and every
`NotifySirRescued()` refuses.

**Reactivating the dungeon run may be the intended fix for Sir** — the coordinator is the author's
original rescue trigger. But the ladder break is upstream of it and must be closed first, or the
coordinator will refuse for the same reason the bootstrap subsystem does.

### Stage 3 — run state, without a second save authority

If endless runs need persistence:

- Add `DiscoveredDefinitionIds` (the one genuinely new field) to `FMelodiaNarrativeRecord`, bump
  the record version, and extend the existing migration path.
- Wire `BondRanks` / `PhaseIndex`, which are already reserved for this.
- Leave `UMelodiaRoguelikePersistence` quarantined. Un-quarantine `MelodiaRoguelikeRunSubsystem`
  **only** if its state can be made to write through the narrative record.

`Settings` should go to `UMelodiaGameUserSettings`; `EntitlementCache` stays out.

## 5. Decision required (Decision 016 gate)

| Class | Recommendation |
|---|---|
| The clean five | **Use now.** No decision needed — never quarantined. |
| `MelodiaDungeonRunCoordinator` | **Un-quarantine, scoped.** Needed for runs and for the Sir rescue path. Close the opening-flow ladder break first. |
| `MelodiaRoguelikeRunSubsystem` | **Un-quarantine only with §3 rework** — run state through the narrative record. |
| `MelodiaRoguelikePersistence` | **Keep quarantined.** Three SaveGames duplicating cosmetics, bond, and narrative memory is the second-authority hazard the quarantine exists for, and it puts two freshly-passed gates at risk. |

## 6. Open questions for the owner

1. **Is "burden" meant to exist?** Only `Blessing` is modelled. A paired burden mechanic is new
   design, not reactivation.
2. **Which level hosts the generator?** ZenForestTest is the authority exploration map, but a
   dungeon generator mutating it has content-risk implications for hand-authored areas.
3. **"UI traversal"** — is this the room-to-room transition UI, a run map/minimap, or the
   blessing-selection screen? `MelodiaRoguelikeRewardWidget` exists and may already cover the third.
