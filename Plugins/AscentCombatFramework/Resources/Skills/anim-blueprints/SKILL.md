---
name: anim-blueprints
description: Choose and extend the right ACF Animation Blueprint. All AnimBPs derive from UACFAnimInstance via one of three base template families — ACF_Template (Lyra-style state machine), ACF_SimpleTemplate (Blendspace), and ACF_MMTemplate (Motion Matching). Each template hosts a full-body Moveset layer and an upper-body Overlay layer, both with their own base classes. Children of any base are data-only — assign animations, never re-author graph logic. Use when creating, picking, or subclassing a character AnimBP, moveset, or overlay.
globs: []
alwaysApply: false
---

# Animation Blueprints — ACF

Every character Animation Blueprint in ACF derives from the C++ base **`UACFAnimInstance`**
(`/Script/CharacterController.ACFAnimInstance`, CharacterController module). All the animation
**logic** lives in a small set of **base AnimBPs** — three character templates plus their Moveset
and Overlay base classes. Everything you create from them is **data-only**.

> **Golden rule: children are data, bases are logic.** When you subclass any base below, you only
> assign data — animation sequences, blendspaces, montages, chooser tables, additive poses. You do
> **not** add or rewrite graph logic in a child. If you find yourself editing the AnimGraph/state
> machine of a child, you're working at the wrong level — fix or extend the base instead.

The base anim instance reads ACF state (locomotion state, speed/direction, combat type, aiming,
current moveset/overlay tags) from the character and its `LocomotionComp`. Layer swapping is driven
at runtime from `AACFCharacter`: `SwitchMoveset(Tag)` (full body), `SwitchOverlay(Tag)` (upper
body), `SwitchMovesetActions(Tag)` (abilities — see the `actions-system` skill).

---

## 1 — The three base character templates

| Base template AnimBP | Style | Full-body locomotion driven by | Location |
|---|---|---|---|
| `ACF_Template_ABP` | **Lyra-style** layered state machine | **Moveset** linked anim layers | `/AscentCombatFramework/CharacterController/` (plugin) |
| `ACF_SimpleTemplate_ABP` | **Blendspace**-based (lightweight) | **Moveset** linked anim layers | `/AscentCombatFramework/CharacterController/Simple/` (plugin) |
| `ACF_MMTemplate_ABP` | **Motion Matching** | **Chooser Tables** (NO moveset layer swap) | `Content/FullSample/GASP/Blueprints/` |

**Key difference:** `ACF_Template` and `ACF_SimpleTemplate` swap the **full body** by switching a
linked **Moveset** anim layer per weapon/stance. `ACF_MMTemplate` does **not** — Motion Matching
selects its pose from animation databases via Unreal **Chooser Tables** (see `chooser-actions`).
**All three** use **Overlay** layers for the upper body.

---

## 2 — The base classes (the only things with logic)

```
UACFAnimInstance                  (C++ /Script/CharacterController.ACFAnimInstance)
│
├─ ACF_Template_ABP        ...... Lyra-style character template      (plugin)
│     ├─ ACF_BaseMoveset   ...... full-body moveset base             (plugin)
│     └─ ACF_BaseOverlay   ...... upper-body overlay base            (plugin)
│
├─ ACF_SimpleTemplate_ABP  ...... Blendspace character template      (plugin .../Simple/)
│     └─ ACF_SimpleMoveset ...... full-body moveset base             (plugin .../Simple/)
│
└─ ACF_MMTemplate_ABP      ...... Motion Matching character template (Content/FullSample/GASP/Blueprints/)
      └─ ACF_MMBaseOverlay ...... upper-body overlay base            (Content/FullSample/GASP/Animations/Overlays/)
            (no moveset base — MM uses Chooser Tables for the full body)
```

Anything else — `ACF_Humanoid_ABP`, `ACF_SimpleCombat_ABP`, `ACF_MMHumanoid_ABP`,
`ACF_UnarmedMoveset`, `ACF_RifleOverlay`, the creature AnimBPs, etc. — is a **data-only child** of
one of the bases above.

---

## 3 — Moveset layers (full body)

A **Moveset** is a linked Animation Layer that drives **full-body** locomotion for one weapon type
/ stance (Unarmed, Sword+Shield, Rifle, Bow, …), selected at runtime via
`Character->SwitchMoveset(MovesetTag)`.

- **Base (logic):** `ACF_BaseMoveset` (for `ACF_Template`), `ACF_SimpleMoveset` (for
  `ACF_SimpleTemplate`).
- **Children (data):** e.g. `ACF_UnarmedMoveset`, `ACF_RifleMoveset` /
  `ACF_SimpleSwordShieldMoveset` — each just plugs the weapon's locomotion animations into the
  base. No graph editing.
- **`ACF_MMTemplate` has no moveset layer** — the full body comes from Chooser Tables.

To add a weapon moveset: duplicate an existing child of the **same base class** for your template
family, swap in the new animations, and give it a tag the equipment references.

---

## 4 — Overlay layers (upper body)

An **Overlay** is a linked Animation Layer applying an **additive upper-body** pose (weapon
idle/aim posture) on top of the full body, swapped via `Character->SwitchOverlay(OverlayTag)`. Used
by **all three** template families.

- **Base (logic):** `ACF_BaseOverlay` (Lyra template) and `ACF_MMBaseOverlay` (MM template; the
  Simple-combat overlays also build on `ACF_MMBaseOverlay`).
- **Children (data):** e.g. `ACF_RifleOverlay`, `ACF_MMSwordOverlay`, the additive weapon overlays
  under `.../GASP/Animations/Overlays/Additive/` — just the additive pose, no graph editing.

To add an overlay: duplicate a child of the appropriate base, set its additive pose, tag it for
`SwitchOverlay`.

---

## 5 — Creating your own

1. **Pick the base template** (§1): Lyra (`ACF_Template_ABP`), Blendspace (`ACF_SimpleTemplate_ABP`),
   or Motion Matching (`ACF_MMTemplate_ABP`).
2. **Create a data-only child** of it for your character; assign your animations and set it as the
   mesh's Anim Class (or via the `UACFCharacterDataAsset` mesh config — see `acf-core`). Do not edit
   the AnimGraph.
3. **Provide the layers** as data-only children of the matching base classes:
   - Lyra/Simple: one **Moveset** (`ACF_BaseMoveset`/`ACF_SimpleMoveset`) per weapon, selected by
     `SwitchMoveset`.
   - MM: configure the **Chooser Table(s)** instead of movesets (`chooser-actions`).
   - All: **Overlay** (`ACF_BaseOverlay`/`ACF_MMBaseOverlay`) per weapon, selected by `SwitchOverlay`.
4. **Match the skeleton** — layers must share the character skeleton or be retargeted
   (`ACF_GenericRetarget_ABP` exists for that).
5. **Need new behavior?** Change the **base** template/moveset/overlay, not the child. Children
   should stay logic-free so they keep inheriting fixes and features.

---

## 6 — Verify

- [ ] Character AnimBP is a **data-only child** of one of the three base templates — no custom
      graph logic added to the child.
- [ ] Template family matches the locomotion: Lyra (`ACF_Template`), Blendspace
      (`ACF_SimpleTemplate`), or Motion Matching (`ACF_MMTemplate`).
- [ ] Movesets/overlays are data-only children of the right base (`ACF_BaseMoveset`/
      `ACF_BaseOverlay` for Lyra, `ACF_SimpleMoveset` for Simple, `ACF_MMBaseOverlay`/Chooser for MM).
- [ ] Each equippable weapon has a Moveset (Lyra/Simple) **or** Chooser entry (MM) **plus** an
      Overlay, tagged so `SwitchMoveset`/`SwitchOverlay` resolve.
- [ ] No moveset layer expected on the MM template — confirm the Chooser Table is assigned instead.
- [ ] Layers share the character skeleton (or are retargeted).

**Related skills:** `character-controller` (locomotion states / the `LocomotionComp` that feeds
these AnimBPs), `chooser-actions` (Motion Matching / montage chooser tables), `player-characters`
(which player pawn — and thus which template — is the project default), `inventory-system`
(weapons carry the moveset/overlay tags).
