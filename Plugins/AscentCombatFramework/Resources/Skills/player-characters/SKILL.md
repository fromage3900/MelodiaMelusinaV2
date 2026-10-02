---
name: player-characters
description: Choose and extend the right ACF player-character Blueprint — FullPlayer (combat only), MMFullPlayer (combat + Motion Matching), UltimatePlayer (combat + quest/dialogue/map/etc.), and GASPlayer (Ultimate + GASP locomotion, the project default pawn). Use when creating, picking, or subclassing a player pawn in this sample.
globs: []
alwaysApply: false
---

# Player Characters — ACF Sample Pawns

This sample ships a layered set of ready-made **player** Blueprints. Never start a player
from a bare `AACFCharacter` (or `ACFCharacterBP`) — those have no input, camera, or player
wiring. Instead **subclass the variant that matches the feature set you need**, or just use
the default (`ACF_GASPlayer_BP`) and reskin it.

> All combat components (Actions/GAS, Locomotion, ARS Statistics, Equipment, DamageHandler,
> Ragdoll, Effects, Initializer, Team) come from the C++/plugin base and are present on every
> variant below. The variants differ in **locomotion system** and **enabled gameplay systems**.

---

## 1 — The inheritance chain

```
AACFCharacter                         (C++  /Script/AscentCombatFramework.ACFCharacter)
└─ ACFCharacterBP                     (plugin /AscentCombatFramework/Blueprints/)        base combatant, all ACF components
   └─ ACFPlayerCharacterBP            (plugin /AscentCombatFramework/Blueprints/)        adds player input + camera base
      └─ ACFFullPlayerBP   ............ "FullPlayer"     — combat-only player
         ├─ ACF_MMFullPlayer_BP ....... "MMFullPlayer"  — combat-only + Motion Matching locomotion
         └─ ACFUltimatePlayerBP ....... "UltimatePlayer"— combat + quest + dialogue + map + all Ultimate systems
            └─ ACF_GASPlayer_BP ....... "GASPlayer"     — Ultimate + GASP locomotion   ★ PROJECT DEFAULT PAWN
               ├─ ACF_MetaPlayer_BP ... GASPlayer with a MetaHuman mesh
               └─ ACF_GASPlayer_FP_BP . first-person GASPlayer
```

`ACF_MMFullPlayer_FP_BP` is the first-person Motion-Matching variant (under the GASP folder).

---

## 2 — Which one to use

| Blueprint | "Name" | Locomotion | Gameplay systems | Use when |
|---|---|---|---|---|
| `ACFFullPlayerBP` | FullPlayer | ACF standard | Combat only | You only need the regular ACF combat sample, no Ultimate features |
| `ACF_MMFullPlayer_BP` | MMFullPlayer | **Motion Matching** | Combat only | Combat-only, but you want Motion Matching animation |
| `ACFUltimatePlayerBP` | UltimatePlayer | ACF standard | Combat **+ quest, dialogue, map, inventory UI, etc.** | Full Ultimate feature set on classic locomotion |
| `ACF_GASPlayer_BP` | GASPlayer | **GASP** (Game Animation Sample) | Ultimate (everything) | **Default.** Start here unless you have a reason not to |
| `ACF_MetaPlayer_BP` | — | GASP | Ultimate | You want a MetaHuman-bodied player |
| `ACF_GASPlayer_FP_BP` | — | GASP (first person) | Ultimate | First-person camera |

**Rule of thumb:** GASPlayer is the default and most complete — pick it unless you specifically
need combat-only (FullPlayer / MMFullPlayer) or a different locomotion/camera.

---

## 3 — Asset locations

| Blueprint | Path |
|---|---|
| `ACFFullPlayerBP` | `Content/FullSample/Blueprints/Characters/Player/` |
| `ACF_MMFullPlayer_BP` | `Content/FullSample/Blueprints/Game/` |
| `ACFUltimatePlayerBP` | `Content/FullSample/Integrations/Ultimate/Blueprint/Game/` |
| `ACF_GASPlayer_BP` | `Content/FullSample/Integrations/Ultimate/` |
| `ACF_MetaPlayer_BP` | `Content/FullSample/Integrations/Ultimate/` |
| `ACF_GASPlayer_FP_BP` | `Content/FullSample/GASP/Blueprints/GASP-FirstPerson/` |
| `ACF_MMFullPlayer_FP_BP` | `Content/FullSample/GASP/Blueprints/GASP-FirstPerson/` |

---

## 4 — How the default is wired

- `Config/DefaultEngine.ini` → `GlobalDefaultGameMode = ACFUltimateGameModeBP`
  (`Content/FullSample/Integrations/Ultimate/Blueprint/Game/`).
- `ACFUltimateGameModeBP` → `DefaultPawnClass = ACF_GASPlayer_BP`.

So out of the box the player spawns as **GASPlayer**. To change the default player project-wide,
edit `DefaultPawnClass` on the active GameMode (or swap the GameMode in `DefaultEngine.ini`).

---

## 5 — Creating your own player

1. **Pick the variant** from the table above (default: `ACF_GASPlayer_BP`).
2. **Create a child Blueprint** of that variant — do NOT subclass `AACFCharacter`/`ACFCharacterBP`
   directly (you'd lose input, camera, and the whole player layer).
3. Override what you need on the child:
   - **Mesh / materials** — set the skeletal mesh on the inherited `Mesh` component
     (for MetaHuman, subclass `ACF_MetaPlayer_BP` instead).
   - **CharacterDataAsset** — on the `InitializerComp`, assign your own `UACFCharacterDataAsset`
     (duplicate a sample one; see the `acf-core` skill) to drive stats, team, starting items,
     and the default ability set.
   - **Ability sets / movesets** — via the DataAsset's `DefaultAbilitySet`, or
     `SwitchMovesetActions` at runtime.
4. **Set it as the pawn**: change `DefaultPawnClass` on your GameMode to your new child.
5. Each variant exposes BP-overridable hooks already implemented up the chain — e.g.
   `HandleSprint` / `StopSprint`, `UserConstructionScript`, and ACF interface events like
   `ShouldStrafe`, `IsEntityAlive`, `GetMainMesh`, `GetEntityCombatTeam`. Override these on your
   child rather than rewriting them.

> **Locomotion is baked into the variant, not a toggle.** Motion Matching (MMFullPlayer) and GASP
> (GASPlayer) come from those branches. To switch a character's locomotion system you switch which
> variant you inherit from — you can't flip combat-only FullPlayer to GASP by a property.

---

## 6 — Verify

- [ ] Your player Blueprint's parent is one of the variants above, not `ACFCharacterBP`/`AACFCharacter`.
- [ ] The active GameMode's `DefaultPawnClass` points at the player you intend to spawn.
- [ ] `InitializerComp` has a valid `UACFCharacterDataAsset` (no null → stats/team/items work).
- [ ] If you wanted Ultimate features (quest/dialogue/map), you inherited from `ACFUltimatePlayerBP`
      or `ACF_GASPlayer_BP` — NOT from `ACFFullPlayerBP`/`ACF_MMFullPlayer_BP` (combat only).
- [ ] If you wanted Motion Matching or GASP locomotion, you inherited from the matching branch.

**Related skills:** `acf-core` (character data assets, teams, damage), `character-controller`
(locomotion states), `actions-system` (ability sets / movesets).
