# DreamAnchor Event Wiring Spec
**Date:** 2026-08-31  
**Source:** `bp_sweep_offline_2026-08-31.json` (records 1-2)  
**Verdict:** Spec only — BP changes need editor.

---

## 1. Parent Class Analysis

**`AMelodiaExplorationInteractionVolume`** (Source/BS_GodFile/MelodiaIntegration/MelodiaExplorationActors.h:19, .cpp:26)

| Property | Value |
|----------|-------|
| `PrimaryActorTick.bCanEverTick` | **false** (line 28) |
| `BeginPlay` override | Calls `Super::BeginPlay()` then binds `OnComponentBeginOverlap` / `OnComponentEndOverlap` (lines 37-42) |
| `Super::BeginPlay` chain | AActor::BeginPlay → no additional bindings |

**`AMelodiaPuzzleRelayVolume`** (line 77)

| Property | Value |
|----------|-------|
| `PrimaryActorTick.bCanEverTick` | **false** (line 79) |
| `BeginPlay` override | Calls `Super::BeginPlay()` then binds `OnComponentBeginOverlap` (lines 88-92) |
| `Super::BeginPlay` chain | AActor::BeginPlay → no additional bindings |

---

## 2. Empty Event Inventory

### BP_MelodiaInteraction_DreamAnchor (parent: AMelodiaExplorationInteractionVolume)

| Event | Current Wiring | Verdict | Recommended Action |
|-------|---------------|---------|-------------------|
| `Event BeginPlay` | None (empty exec) | **SAFE — keep empty** | Parent BeginPlay handles overlap binding. Super::BeginPlay call in BP not needed (parent already calls Super). Comment: `// Parent binds overlap handlers in BeginPlay` |
| `Event ActorBeginOverlap` | None | **NEEDS WIRE** | Bind to `OnMelusinaEntered` broadcast → triggers narrative/quest flow. This is the primary interaction trigger. |
| `Event Tick` | None | **SAFE — keep empty** | `bCanEverTick = false` on parent. No tick logic needed. Delete the empty event or leave with comment. |

### BP_MelodiaPuzzleRelay_FirstResonance (parent: AMelodiaPuzzleRelayVolume)

| Event | Current Wiring | Verdict | Recommended Action |
|-------|---------------|---------|-------------------|
| `Event BeginPlay` | None | **SAFE — keep empty** | Parent handles overlap binding. Same as DreamAnchor. |
| `Event ActorBeginOverlap` | None | **NEEDS WIRE** | Bind to `OnPuzzleActivated` broadcast → triggers puzzle sequence. |
| `Event Tick` | None | **SAFE — keep empty** | `bCanEverTick = false`. Delete or comment. |

---

## 3. Blueprint Wiring Steps (editor)

### DreamAnchor

1. Open `BP_MelodiaInteraction_DreamAnchor` in Blueprint editor.
2. In EventGraph, right-click → **Add Event → Actor BeginOverlap** (if not present).
3. Drag `Other Actor` → **Cast To BP_MelusinaJRPGCharacter** (or use `IsEligibleExplorer` via interface call).
4. From cast success → **Fire Custom Event / Call OnMelusinaEntered** (or trigger narrative via `UMelodiaNarrativeSubsystem`).
5. Leave `Event BeginPlay` empty (parent handles it).
6. Delete empty `Event Tick` or add comment: `// Tick disabled on parent class`.

### PuzzleRelay

1. Open `BP_MelodiaPuzzleRelay_FirstResonance`.
2. Wire `Actor BeginOverlap` → `OnPuzzleActivated.Broadcast`.
3. Optionally add a `PrintString` or `Play Sound` for debug feedback.
4. Leave `Event BeginPlay` empty.
5. Delete empty `Event Tick`.

---

## 4. Cross-reference

- `PUZZLE_RELAY_EVENT_STUB_SPEC_2026-08-30.md` previously audited this BP — verified the same 3 empty events.
- The 2026-08-30 spec labeled them "safe as stubs" but recommended wiring BeginPlay.
- **Correction:** Parent class already binds overlap in its own BeginPlay. Super::BeginPlay call in child BP is redundant and potentially harmful (double-bind risk). The correct action is:
  - Leave BeginPlay **empty** in both child BPs.
  - Wire `ActorBeginOverlap` (the primary interaction trigger).
  - Remove or comment `Tick`.

---

## 5. Blockers

- Requires open editor with level loaded.
- No .uasset writes from this daemon (BP changes need editor save).

---

## 6. Metadata

| Field | Value |
|-------|-------|
| daemon_pass | read_review_loop_5 (2026-08-31) |
| status | SPEC_ONLY — pending owner execution |
| files | 0 writes proposed |
| action_items | 2 (wire DreamAnchor.ActorBeginOverlap, wire PuzzleRelay.ActorBeginOverlap) |