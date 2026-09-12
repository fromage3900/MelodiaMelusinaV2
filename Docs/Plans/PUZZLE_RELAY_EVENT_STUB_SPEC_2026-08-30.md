# Puzzle Relay & Dream Anchor Event Stub Spec — 2026-08-30

**Source:** C++ parent class audit (`MelodiaExplorationActors.h/.cpp`)
**Targets:**
- `Content/MelodiaIntegration/Blueprints/BP_MelodiaPuzzleRelay_FirstResonance.uasset`
- `Content/MelodiaIntegration/Blueprints/BP_MelodiaInteraction_DreamAnchor.uasset`
**Mode:** Spec only — no `.uasset` hand-edits.

---

## Parent Class Interfaces

### `AMelodiaPuzzleRelayVolume` (C++ parent of PuzzleRelay_FirstResonance)

| Event | C++ Behavior | Blueprint Override? |
|---|---|---|
| `BeginPlay` | Calls `Super::BeginPlay`, binds `TriggerVolume->OnComponentBeginOverlap` → `HandleBeginOverlap` | **Yes** — call `Super::BeginPlay` first, then bind custom logic |
| `ActorBeginOverlap` | Handled natively by C++ `HandleBeginOverlap` → calls `ActivateRelay` | **No** — use `OnPuzzleActivated` delegate instead |
| `Tick` | `bCanEverTick = false` by default | **No** — leave disabled unless platform-motion subclass needed |

**Key delegates:** `OnPuzzleActivated (FMelodiaExplorationActorEvent)`

**Key call-ins:** `ActivateRelay(AActor*)`, `ResetRelay()`

---

### `AMelodiaExplorationInteractionVolume` (C++ parent of Interaction_DreamAnchor)

| Event | C++ Behavior | Blueprint Override? |
|---|---|---|
| `BeginPlay` | Calls `Super::BeginPlay`, binds `OnComponentBeginOverlap` + `OnComponentEndOverlap` | **Yes** — call `Super::BeginPlay` first, then bind custom logic |
| `ActorBeginOverlap` | Handled natively by C++ `HandleBeginOverlap` → broadcasts `OnMelusinaEntered` | **No** — use `OnMelusinaEntered` / `OnInteractionRequested` delegates |
| `Tick` | `bCanEverTick = false` by default | **No** — leave disabled unless animated prompt needed |

**Key delegates:** `OnMelusinaEntered`, `OnMelusinaExited`, `OnInteractionRequested (FMelodiaExplorationActorEvent)`

**Key call-ins:** `TryInteract(AActor*)`, `SetInteractionActive(bool)`

---

## Blueprint: `BP_MelodiaPuzzleRelay_FirstResonance`

| Empty Event | Recommendation | Rationale |
|---|---|---|
| **BeginPlay** | Call `Super::BeginPlay`, then bind `OnPuzzleActivated` → custom level logic (open door, play chime, increment quest var). Leave stub if level binding exists. | C++ parent already wires overlap→activation. Child should react, not re-implement. |
| **ActorBeginOverlap** | **Leave empty** with comment: `// Handled by AMelodiaPuzzleRelayVolume::HandleBeginOverlap → ActivateRelay`. Do NOT override. | C++ parent consumes the event. Overriding without `Super` call breaks activation. |
| **Tick** | **Leave empty** with comment: `// bCanEverTick=false in parent. Add platform motion subclass if tick needed.`. | Parent explicitly disables tick for performance. Child inherits this. |

---

## Blueprint: `BP_MelodiaInteraction_DreamAnchor`

| Empty Event | Recommendation | Rationale |
|---|---|---|
| **BeginPlay** | Call `Super::BeginPlay`, then optionally set `InteractionId = "DreamAnchor_FirstResonance"` and `PromptText = "Touch the dream"`. Bind `OnMelusinaEntered` → show prompt widget. | C++ parent wires overlap. Child configures editor-facing properties and presentation hooks. |
| **ActorBeginOverlap** | **Leave empty** with comment: `// Handled by AMelodiaExplorationInteractionVolume::HandleBeginOverlap → OnMelusinaEntered.Broadcast`. | C++ parent already broadcasts delegates. Overriding without `Super` breaks overlap detection. |
| **Tick** | **Leave empty** with comment: `// bCanEverTick=false in parent. Add if animated prompt or cooldown UI needed.`. | Parent explicitly disables tick. |

---

## Execution Notes

1. **All 6 empty events** across both BPs are currently safe to leave as documented stubs.
2. **Binding to delegates** (not overriding overlap events) is the correct UE pattern — the C++ parent handles collision, the Blueprint child handles presentation/level logic.
3. **`BeginPlay` is the only event that requires a `Super::BeginPlay` call** — without it, the C++ delegate bindings never register.
4. **If gameplay needs tick later** (e.g., pulsing glow on DreamAnchor), create a new C++ subclass with `bCanEverTick = true` rather than enabling tick in the Blueprint child — keeps collision concerns separate from presentation concerns.
5. **Naming convention for spawned children:** If more puzzle relays or interaction volumes follow this pattern, use `BP_MelodiaPuzzleRelay_<PuzzleId>` and `BP_MelodiaInteraction_<InteractionId>` to match the C++ `PuzzleId`/`InteractionId` properties.