# SirMelodiousPerch + Flight-with-Stamina Design — 2026-08-28

**Author:** Melusina (Hermes agent, z-ai/glm-5.2)
**Date:** 2026-08-28
**Status:** Design complete; implementation queued for editor session

---

## 0. Executive Summary

The user wants Sir Melodious to function as a capable flying party member in the Melodia
traversal system today. The design has two deliverables:

1. **SirMelodiousPerch BPs** — level-placeable anchor points that Sir Melodious can land on
   during exploration. These are exploration actors (like `AMelodiaExplorationInteractionVolume`)
   that serve as visual + gameplay landing spots.

2. **Flight with stamina cap** — Sir Melodious's flight mode (`BP_SirMelodious_Flight`)
   needs a stamina system parallel to Melusina's glide stamina, so flight is sustained but
   finite — not unlimited. When stamina depletes, Sir must land on a perch or the ground.

The existing `UMelodiaTraversalComponent` handles glide/sprint/dash/swim/dive for Melusina.
Sir's flight needs its own stamina model because flight is a different movement mode from
glide — Sir is airborne under his own power, not falling with reduced gravity.

---

## 1. Current Architecture (truth, not claims)

### Party roster (UMelodiaPartySubsystem — MelodiaCore plugin)

```
Index 0: Melusina (ground/glide/swim) — whatever pawn the game mode spawns
Index 1: Sir Melodious (flight) — BP_SirMelodious_Flight at /Game/Melodia/Characters/SirMelodious/
```

- `SwitchToNext(APlayerController* PC)` — Ctrl-cycles between roster members
- `bSirMelodiousExplorationUnlocked` — false until the stock JRPG party recruits Sir
- `ParkPawn(APawn*, bool bParked)` — hides, disables collision, pauses anims when inactive
- `SetActiveIndex(int32, APlayerController*)` — possesses new pawn, parks old, blends camera
- Handoff transform: old pawn's location + 150 Z offset, teleported

### Traversal component (UMelodiaTraversalComponent — BS_GodFile)

On Melusina's pawn only. Handles:
- **Glide:** GravityScale=0.16, AirControl=1.0, TerminalFallSpeed=240, ActivationLift=190
  - Stamina: MaxGlideStamina=3.5s, drain=1.0/s, regen=1.5/s, regenDelay=0.45s, minStart=0.25s
  - Input: Jump (SpaceBar) → press again mid-air → glide tap
- **Sprint:** SprintSpeed=630, NormalWalkSpeed=380
- **Dash:** DashImpulse=900, cooldown=0.7s, persist=0.22s (Strafe key)
- **Swim:** SwimSpeed=400, stamina=5.0s, drain=0.5/s
- **Dive:** DiveImpulse=800, SurfaceJumpImpulse=600, Breath=10.0s

### Capability provider (IMelodiaTraversalCapabilityProvider)

- Capabilities: Glide (`capability.melodia.glide`), Dash (`capability.melodia.dash`), Swim (`capability.melodia.swim`)
- Registry: `UMelodiaTraversalCapabilityRegistry` (GameInstanceSubsystem)
- Wardrobe registers as the provider — outfits grant capabilities
- `bRequireCapabilityProviderForGlide` — opt-in per-pawn, false by default

### Opening flow (UMelodiaOpeningFlowSubsystem — MelodiaCore)

```
NotStarted → Morning → SirDeparted → Dreamstate → ZenExploration
  → FirstDungeonUnlocked → SirRescued → ReturnedHome
```

- `NotifySirRescued()` requires `FirstDungeonUnlocked` phase — strict, non-repeatable
- After rescue: `RecruitSirMelodiousThroughStockParty()` → `SetSirMelodiousExplorationUnlocked(true)`
- Ctrl-cycling unlocks only after the stock JRPG party accepts Sir

### Sir Melodious flight pawn

- `BP_SirMelodious_Flight.uasset` (35KB, Aug 11) — the flight pawn BP
- `SK_SirMelodious_Rigged.uasset` (76MB) — skeletal mesh
- `ABP_SirMelodious.uasset` (32KB) — animation blueprint
- Retarget: `RTG_UE4Mannequin_To_SirMelodious`, `RTG_FlightSource_To_Sir`
- `_FlightSource/` — FreeCamera tracking frame update anims (19MB)
- Skill: `BP_SirSkyboundRefrain.uasset` (27KB) in `Content/MelodiaIntegration/Party/Skills/`

### Existing perch reference

`Content/Python/setup_melodia_opening_levels.py` already spawns a perch proxy:
```
perch_location = (160.0, 130.0, 120.0)
Morning_SirMelodiousPerch_PROXY_REPLACE — proxy mesh at perch_location
```
This is the morning intro scene where Sir is on his perch. The Perch BP is the exploration-
mode generalization of this concept.

---

## 2. SirMelodiousPerch BP Design

### Purpose

Level-placeable anchor points that Sir Melodious can land on during exploration. They
serve three roles:

1. **Visual** — a readable perch object in the world (a branch, a railing, a ruined arch)
2. **Gameplay** — a landing spot where flight stamina regenerates faster
3. **Navigation** — a waypoint that guides the player toward interesting exploration paths

### Architecture

The Perch is a lightweight exploration actor built on the existing `AMelodiaExplorationInteractionVolume` pattern. It is NOT a new C++ class — it is a Blueprint subclass or a composition
of existing components, because:

- The editor is building (no C++ compiles until the build finishes)
- The existing exploration actor pattern already handles overlap, interaction, and one-shot
- Adding a new C++ class would require a header change → full closed-editor rebuild

**Option A (preferred — no C++):** BP_SirMelodiousPerch as a Blueprint based on
`AMelodiaExplorationInteractionVolume`, with:
- A static mesh component (the perch visual — branch, railing, arch fragment)
- The existing InteractionVolume box component for overlap detection
- An `InteractionId` set to `perch.sirmelodious.landing`
- `bRequireMelusina` = false (Sir lands here, not Melusina)
- `bOneShot` = false (reusable — Sir can land and take off repeatedly)
- On `OnInteractionRequested` → trigger stamina regen boost on Sir's traversal component

**Option B (if a stamina regen aura is needed):** Add a `BP_SirMelodiousPerchAura`
variant with a larger overlap volume that passively regenerates flight stamina while
Sir is within range. This is a Blueprint timer + line trace, no C++.

### Perch placement

Perches should be placed at:
1. **High points** — cathedral arches, cliff edges, rooftop ridges (where Sir would naturally land)
2. **Exploration junctions** — where a flight path branches and the player chooses a direction
3. **Stamina recovery spots** — at intervals along long flight paths (every ~3.5s of flight = one perch)
4. **Visual landmarks** — the perch mesh should read as "Sir was here" from a distance

### Perch visual

The perch visual should be a simple static mesh that matches the environment:
- In forest levels: a bare branch or broken tree top
- in cathedral/ruin levels: a broken arch fragment or railing
- In coastal levels: a driftwood post or sea-stack top

For P0, use a simple placeholder mesh (a cube or cylinder) and swap to environment-specific
meshes later. The important thing is the overlap volume and the gameplay logic.

---

## 3. Flight-with-Stamina Design

### The problem

`BP_SirMelodious_Flight` has no traversal component and no stamina system. When the player
Ctrl-cycles to Sir, they possess a pawn that can fly — but with no stamina limit, flight is
infinite. The user wants a stamina cap so flight is sustained but finite, like a real bird:
fly, land, rest, fly again.

### Design: FlightStamina on the flight pawn

Add a `UMelodiaTraversalComponent` to `BP_SirMelodious_Flight` (or a lightweight flight-
specific component) with these parameters:

| Parameter | Value | Notes |
|-----------|-------|-------|
| MaxFlightStamina | 5.0s | Longer than glide (3.5s) because flight is Sir's primary mode |
| FlightStaminaDrainPerSecond | 1.0/s | Same as glide drain |
| FlightStaminaRegenPerSecond | 2.0/s | Faster regen than glide (1.5/s) — perches boost this further |
| FlightStaminaRegenDelay | 0.3s | Shorter than glide (0.45s) — Sir recovers faster on landing |
| MinimumFlightStartStamina | 0.3s | Must have 30% stamina to take off |
| PerchRegenMultiplier | 3.0x | While on a perch, regen is 3x normal |

### Flight input model

Sir's flight should reuse the existing input actions where possible:

| Action | Key | Sir behavior |
|--------|-----|-------------|
| MelodiaTraversalJump | SpaceBar | Take off / ascend (if stamina > min) |
| MelodiaTraversalSprint | LeftShift | Sprint-fly (faster, drains 2x stamina) |
| MelodiaTraversalStrafe | LeftAlt/RightAlt | Dash in air (impulse, costs stamina chunk) |
| MelodiaTraversalDive | C | Dive (descend fast, regenerates stamina on landing) |

### Stamina states

```
[Grounded] --jump--> [Taking Off] --airborne--> [Flying]
                                              |
                                              v
                                         [Landing] --on perch--> [Perched (3x regen)]
                                              |                        |
                                              v                        |
                                         [Grounded] <-----------------+
                                              |
                                         (normal regen after delay)
```

### What happens when stamina depletes mid-flight

When flight stamina hits 0:
1. Sir's gravity scale increases to near-normal (0.8) — he starts falling
2. A "tired" state plays (animation hook via `IMelodiaTraversalStateProvider`)
3. He must land (on ground or a perch) before he can take off again
4. Landing starts the regen timer (0.3s delay, then 2.0/s regen, or 6.0/s on a perch)

This is the "stamina cap" — flight is not infinite, but the recovery is forgiving enough
that the player rarely feels punished. The perches make recovery faster and more fun.

---

## 4. Implementation Plan

### Phase 1: Offline (NOW — while editor builds)

1. ✅ This design doc
2. Write a Python tool `Content/Python/setup_sir_melodious_perches.py` that:
   - Defines perch spawn locations for each shipping level
   - Spawns `AMelodiaExplorationInteractionVolume` actors with the right settings
   - Sets `InteractionId = "perch.sirmelodious.landing"`
   - Sets `bRequireMelusina = false`, `bOneShot = false`
   - Assigns a placeholder static mesh
3. Write a spec for the flight stamina parameters (above table)
4. Write a test contract for the flight-with-stamina gate

### Phase 2: Editor-bound (after build completes)

1. **Create BP_SirMelodiousPerch** — Blueprint based on `AMelodiaExplorationInteractionVolume`
   - Add a static mesh component (placeholder cube)
   - Set InteractionId, bRequireMelusina, bOneShot
   - Add an `OnInteractionRequested` handler that triggers stamina regen
   - Save to `Content/Melodia/Characters/SirMelodious/BP_SirMelodiousPerch.uasset`

2. **Add traversal component to BP_SirMelodious_Flight** — add `UMelodiaTraversalComponent`
   OR a lightweight flight-stamina component
   - Configure flight stamina parameters
   - Wire input actions (reuse existing MelodiaTraversalJump/Sprint/Strafe/Dive)
   - Add the stamina drain/regen logic in Tick

3. **Place perches in shipping levels** — use the Python tool or place manually
   - ZenForestTest, L_KaleidoNave, L_FallenMoon, L_MelusinaMorning, L_Template
   - 3-5 perches per level at high points and exploration junctions

4. **PIE test** — Ctrl-cycle to Sir, fly to a perch, land, verify stamina regen
5. **Record gate** — `record_gate.py wardrobe_gameplay_hook pass --note "2026-08-28 Sir flight with stamina cap, perch landing"`

---

## 5. C++ vs Blueprint split

**No new C++ classes needed for P0.** The Perch is a BP subclass of the existing
`AMelodiaExplorationInteractionVolume`. The flight stamina is either:

(a) Reuse `UMelodiaTraversalComponent` on Sir's flight pawn with modified parameters
   (the component already has glide stamina — repurpose it for flight by treating
   flight as a variant of glide with different gravity/stamina tuning)

(b) A lightweight Blueprint-only stamina system on `BP_SirMelodious_Flight` — a timer
   that drains while flying and regens while grounded/perched, with a UPROPERTY float
   exposed to BP. This is simpler and avoids any C++ changes.

**Recommendation:** Start with (b) — Blueprint-only stamina on `BP_SirMelodious_Flight`.
It's faster to implement, needs no C++ compile, and can be promoted to a native component
later if the gate passes and the system stabilizes.

If (a) is needed later, the `UMelodiaTraversalComponent` already has:
- `GlideStamina`, `MaxGlideStamina`, `GlideStaminaDrainPerSecond`, `GlideStaminaRegenPerSecond`
- `GetGlideStaminaNormalized()`, `GetGlideStamina()` — already exposed to BP
- `OnGlideStateChanged` delegate — already fires on state change
- The tick already drains/regens glide stamina

The flight variant would add:
- `EMelodiaTraversalMode::Flight` (new enum value — needs C++ header change)
- `FlightStamina`, `MaxFlightStamina`, `FlightStaminaDrainPerSecond`, etc.
- `StartFlight()`, `StopFlight()` — parallel to `StartGlide()`, `StopGlide()`
- `IsFlying()` — parallel to `IsGliding()`

But this is a header change → full closed-editor rebuild. Defer to post-P0.

---

## 6. Perch BP naming convention

```
BP_SirMelodiousPerch              — base perch BP (BP subclass of AMelodiaExplorationInteractionVolume)
BP_SirMelodiousPerch_Branch      — forest variant (bare branch mesh)
BP_SirMelodiousPerch_Arch         — ruin variant (broken arch fragment)
BP_SirMelodiousPerch_Post         — coastal variant (driftwood post)
```

For P0, only `BP_SirMelodiousPerch` (placeholder mesh) is needed. Variants are post-P0.

---

## 7. Gate mapping

This work contributes to two open P0 gates:

| Gate | How |
|------|-----|
| wardrobe_gameplay_hook | Sir's flight is an outfit-granted traversal capability (if wardrobe provides flight) |
| music_world_key | Perches can double as music-world-key anchors if a perch plays a phrase when Sir lands |

If the user wants Sir's flight to be wardrobe-gated (an outfit grants flight), then
`wardrobe_gameplay_hook` is the gate. If flight is always available after rescue, it's
not wardrobe-gated — it's a progression-gated capability.

**Recommendation:** Flight is progression-gated (unlocked after Sir is rescued), not
wardrobe-gated. The `wardrobe_gameplay_hook` gate should use a different outfit
(Glide/Dash/Swim for Melusina). Sir's flight is its own thing.

---

## 8. Safety notes

- Do NOT add a new C++ class while the editor is building — the build is in progress
- Do NOT import FBX into a path that already holds an asset
- Do NOT touch `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python (fatal editor crash)
- Do NOT run `git clean -fd` or `git checkout -- .`
- The perch BP should be created in the editor after the build completes
- The flight stamina should be Blueprint-only for P0 (no C++ header changes)
- One editor instance always — check port 9316 before any editor work
