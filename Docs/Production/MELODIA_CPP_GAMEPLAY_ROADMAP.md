# Melodia C++ Gameplay Roadmap — Traversal, Wardrobe, Starskiff

**What this teaches:** the exact C++ work needed for smooth traversal, wardrobe switching, and the
Shorewake → Starskiff → sea-travel chain. Every claim below is read from source on 2026-09-21; where
something is a scaffold or a stale declaration, it says so.

**The good news first:** the architecture is already right. The Resonant Form / capability / registry
separation is well-designed and well-documented, and the Starskiff boarding authority already exists.
Most of the work below is *completing chains that are wired but not connected*, not building systems.

---

## 1. The chain as it exists today

```
FMelodiaResonantForm            declares GrantedCapabilities + RequiredFlagIds
  └─ UMelodiaWardrobeSubsystem::IsCapabilityActive(Capability, ContextId)
       └─ ::QueryTraversalCapability(FName CapabilityId, ...)      [interface impl]
            └─ UMelodiaTraversalCapabilityRegistry::QueryCapability
                 ├─ UMelodiaTraversalComponent        (glide / dash / swim)
                 ├─ AMelodiaTravelInteractionPortal   (RequiredTraversalCapability)
                 ├─ AMelodiaStarskiffPawn             (RequiredCapabilityId)
                 └─ UMelodiaMagicalTransformComponent (TriggerCapability → wing reveal)
```

The registry rejects multiple providers on purpose, so capability truth cannot split. The vocabulary
lives in one place (`MelodiaTraversalCapability`, game module) precisely because it used to be raw
string literals in two modules and a rename silently disabled the ability.

**The whole vocabulary is three ids:**

```cpp
namespace MelodiaTraversalCapability {
    inline const FName Glide{TEXT("capability.melodia.glide")};
    inline const FName Dash {TEXT("capability.melodia.dash")};
    inline const FName Swim {TEXT("capability.melodia.swim")};
}
```

and the matching enum is `EMelodiaFormCapability { Glide, Dash, Swim }`.

---

## 2. Shorewake → Starskiff — the chain is broken in a documented way

### 2.1 What the content declares

`specs/wardrobe/wardrobe_shorewake_manifest.v1.json`:

```json
"resonant_form": {
  "form_id": "form.melusina.shorewake",
  "capability_unlocked": "SeaAboveResonance",
  "required_flags": ["flag.quest.shorewake_completed", "flag.sea_above.starskiff_ready"]
},
"traversal_impact": { "can_board_starskiff": true, "sea_above_buoyancy_active": true }
```

The manifest already carries its own defect note:

> `_stale_fields`: `resonant_form.capability_unlocked` — no matching traversal capability id exists;
> boarding is actually gated by `flag.sea_above.starskiff_ready` OR `capability.melodia.glide`

**`SeaAboveResonance` is not a capability.** It is not in the enum, not in the namespace, and
`QueryTraversalCapability` would fall through to its `unknown_capability` branch. The Shorewake dress
currently grants **nothing mechanical**.

### 2.2 What the code actually gates on

`AMelodiaStarskiffPawn::CanBoard` — player-controlled, within `BoardingRadius` (400 uu), then:

```cpp
const bool bReadyFlag      = Narrative->GetNarrativeRecord().Flags.FindRef(TEXT("flag.sea_above.starskiff_ready"));
const bool bCapabilityReady = Registry->QueryCapability(RequiredCapabilityId, TraversalCapabilityContextId, CapabilityReason);
if (!bReadyFlag && !bCapabilityReady) { /* blocked */ }
```

with `RequiredCapabilityId = "capability.melodia.glide"` by default.

Two consequences, both wrong for the intended design:

1. **Wearing the glide form lets you board the boat.** Gliding and sailing are conflated.
2. **The flag alone unlocks boarding**, bypassing the outfit entirely — `bReadyFlag || bCapabilityReady`.
   So even with a correct Sail capability, the flag is a backdoor.

### 2.3 The work

**W1 — Add a real sailing capability.** Three edits plus one consumer:

| File | Change |
|---|---|
| `MelodiaCosmeticTypes.h` | add `Sail` to `EMelodiaFormCapability` |
| `MelodiaTraversalCapabilityProvider.h` | add `inline const FName Sail{TEXT("capability.melodia.sail")}` |
| `MelodiaWardrobeSubsystem.cpp` | map `MelodiaTraversalCapability::Sail → EMelodiaFormCapability::Sail` in `QueryTraversalCapability` |
| `MelodiaStarskiffPawn.h` | default `RequiredCapabilityId` to the Sail id |

The enum's own comment is the acceptance test here: *"Adding a value here without a matching
implementation creates a form that promises something the traversal authority cannot deliver."* Sail
has a real consumer — the Starskiff — so it is not a name with no behaviour behind it. Do **not** add
`SeaAboveResonance` as a fourth id; it is a content-side name for the same idea, and two names for one
capability is how the original literal-drift bug happened.

**W2 — Decide the flag's role.** `bReadyFlag || bCapabilityReady` should almost certainly become:
the flag gates whether the *form is available* (it is already in `required_flags`), and boarding reads
capability only. That makes the outfit load-bearing, which is the stated design. Keep the flag as an
OR only if you deliberately want a no-outfit story path — a decision, not a default.

**W3 — Update the manifest** `capability_unlocked` to the real id and clear `_stale_fields`.

**W4 — Wire the transform proc.** `UMelodiaMagicalTransformComponent::TriggerCapability` is already
the seam; set it to `Sail` on the Shorewake cosmetic so equipping/activating reveals the sea form the
way the wings reveal for glide. No new code — it is a per-component property.

---

## 3. Oceanology — the boat does not float

`AMelodiaStarskiffPawn` moves on `UFloatingPawnMovement`. That is a *kinematic* movement component:
it has no buoyancy, no water-height query, and no knowledge of Oceanology.

`MelodiaOceanologyWaterBridgeSubsystem.h` states its own status plainly:

> SCAFFOLD — no Oceanology headers included. All plugin contact is via […]
> Oceanology quadtree extent and actor Z are authored in the editor; this […]

So `"sea_above_buoyancy_active": true` in the Shorewake manifest is aspirational. The skiff will sit
at whatever Z it was placed at and slide around on a flat plane.

### The work

**O1 — Surface-height query.** Give the bridge a real `GetWaterHeightAtLocation(FVector) → float`
backed by Oceanology, or adopt Oceanology's own buoyancy component on the skiff hull. The bridge is
the right home: it already exists as the single seam, and putting Oceanology headers in the pawn would
couple the gameplay authority to a marketplace plugin.

**O2 — Skiff follows the surface.** Either swap `UFloatingPawnMovement` for a buoyancy-driven setup,
or keep it and drive Z from O1 each tick with damping. The second is cheaper and keeps the pawn's
movement authority intact; the first looks better in a wake shot.

**O3 — Disembark safety.** `Disembark()` currently just un-possesses. Over open water that drops
Melusina into the sea. Needs a shore//platform query or a forced swim-state handoff into
`UMelodiaTraversalComponent`'s existing swim path.

**O4 — Travel handoff.** `RequestBoatTraversal(DestinationMap, DestinationSpawnTag)` already routes
through the travel authority, and `AMelodiaTravelInteractionPortal` already proves the "single route
owner" pattern. Confirm the skiff's call goes through the same TravelSubsystem rather than loading a
map directly — the portal header explicitly forbids direct map loading in children, and the skiff
should honour the same rule.

---

## 4. Traversal feel — jump and glide

Measured from `MelodiaTraversalComponent.cpp`. Target behaviour (owner, 2026-09-21): tap to jump with
no latency, hold to extend height, hold in air to glide and proc the transform.

| Intended | Actual |
|---|---|
| Tap → jump | Jump fires on **release** (`HandleJumpReleased` → `OwnerCharacter->Jump()`), so every press costs latency |
| Hold → higher | **No charged jump exists.** `GetJumpWindupNormalized()` is computed for visuals only and never touches velocity |
| — | Holding calls `Movement->StopMovementImmediately()` and `MaxWalkSpeed = 0` — it freezes her and returns nothing |
| Hold in air → glide | Requires a **second discrete tap** (`bAwaitingGlideTap`) |
| Variable jump height | Defeated: `FinishReleasedJump` calls `StopJumping()` on the next tick, disabling UE's `JumpMaxHoldTime` |

### The work

**T1 — Fire on press.** Move the `Jump()` call into `HandleJumpPressed` when grounded.

**T2 — Delete `FinishReleasedJump`** and its next-tick timer; let `JumpMaxHoldTime` give variable
height while held. This is the single biggest feel win and it removes code rather than adding it.

**T3 — Stop freezing on windup.** Either drop the windup entirely (it now has no mechanical purpose)
or keep it purely as an anim-driving value with movement untouched.

**T4 — Held-input glide.** Replace `bAwaitingGlideTap` with a held-input check while falling: if the
jump input is still down past a small threshold after apex, `StartGlide()`. Keep the existing stamina
gate (`MinimumGlideStartStamina`, drain, regen delay) — that part is sound.

**T5 — Transform proc on glide entry.** Already available via `MelodiaMagicalTransformComponent`;
confirm it fires on `StartGlide` rather than on equip, so the wings appear at the moment the player
uses the ability.

Tunables already exist and should not be hardcoded: `GlideGravityScale` 0.16, `GlideAirControl` 1.0,
`GlideTerminalFallSpeed` 240, `GlideActivationLiftSpeed` 190, `GlideActivationForwardBoost` 165,
`MaxGlideStamina` 3.5.

---

## 5. Wardrobe switching — smoothness

**W5 — Slot component creation cost.** `FindOrCreateSlotComponent` does `NewObject` +
`SetSkeletalMesh` + `SetLeaderPoseComponent` + `RegisterComponent` + `AddInstanceComponent` on first
use of each slot. That is a hitch on the first equip of any slot, mid-gameplay. Pre-create the slot
components (hidden) at `BeginPlay` for every slot in `DefaultGarmentMeshes`, since `EquipGarment(nullptr)`
already hides rather than destroys — the "re-equipping is cheap" path exists, it just is not primed.

**W6 — `GetBodyMesh` fallback is name-based.** Fixed 2026-09-21 to fall back from `ACharacter` to a
component named `MelusinaPresentationMesh` / `CharacterMesh0`. That unblocked the battle presenter, but
a hardcoded name in a general plugin is debt. Promote it to a `UPROPERTY(EditDefaultsOnly) FName
BodyMeshComponentName` on the component, defaulting to NAME_None with the current names as fallback.

**W7 — Skirt skeleton.** `SK_Melusina_V2_Skirt_R2_SmoothChains` carries its own companion skeleton, so
`IsGarmentSkeletonCompatible` correctly refuses it (leader-pose copies transforms by index; a mismatched
skeleton would render wrongly). This is an **asset** fix, not code — see
`Docs/Production/MELUSINA_REEXPORT_RUNBOOK.md` §6. Do not weaken the compatibility check to work around it.

**W8 — Region-hide morphs.** The body-region clipping contract requires region ids to equal morph
targets `mel_body_hide_*` on the body SK. Missing morphs are a warn-once with no visual collapse. Worth
auditing which declared regions have no morph yet, so garment layering does not silently poke through.

---

## 6. Suggested order

1. **W1–W3** — Sail capability end to end. Small, self-contained, and makes the Shorewake dress mean
   something. Do it in the same build as the traversal work.
2. **T1–T4** — jump/glide rework. Same build; both are game-module C++.
3. **T5 + W4** — transform procs, once the capabilities they key off are real.
4. **W5** — wardrobe pre-warm, measurable as a hitch before/after.
5. **O1–O2** — Oceanology surface query and skiff float. Largest unknown; needs a real look at what
   Oceanology exposes.
6. **O3–O4** — disembark safety and travel handoff, after the boat physically works.
7. **W6, W8** — debt cleanup.

Steps 1–3 are one closed-editor build. Step 5 likely needs its own.

---

## 7. Rules this plan must not break

- **One provider per game instance.** The registry rejects multiples deliberately. Do not register a
  second capability provider for the boat.
- **The form declares; the authority decides.** `FMelodiaResonantForm` must not gain granting logic.
  `UMelodiaTraversalComponent` stays the traversal authority and `UMelodiaNarrativeSubsystem` stays the
  flag authority.
- **TravelSubsystem is the only route owner.** No direct map loading in the skiff or in portal children.
- **One capability id per ability.** Do not let `SeaAboveResonance` and `capability.melodia.sail`
  coexist as synonyms.
- **MelodiaCore stays integration/presentation-only.** None of this work belongs there.

---

## Sources

Read 2026-09-21 from: `MelodiaTraversalCapabilityProvider.h`, `MelodiaStarskiffPawn.{h,cpp}`,
`MelodiaTravelInteractionPortal.h`, `MelodiaTraversalComponent.{h,cpp}`, `MelodiaCosmeticTypes.h`,
`MelodiaMagicalTransformComponent.h`, `MelodiaWardrobeSubsystem.cpp`, `MelodiaWardrobeComponent.cpp`,
`MelodiaOceanologyWaterBridgeSubsystem.h`, `specs/wardrobe/wardrobe_shorewake_manifest.v1.json`.
No runtime or PIE claim is made here; this is source-verified only.
