# Co-op skill: Resonance payoff — implementation spec (2026-08-08)

**Status:** config done, graph work owed. Must be authored **by hand in the Blueprint
editor**, not via MCP — see "Why not automated" below.

## Design (settled with owner)

Melusina marks a foe with **Petal Cadence** → applies **Resonance** (2 turns).
Sir answers with **Skybound Refrain** → **1.8×** damage instead of 1.2×, and **consumes**
the Resonance mark.

## Already done

| Change | State |
|---|---|
| `BP_Resonance.durationTurn` 1 → **2** | applied + saved |
| `/Game/MelodiaIntegration/Party` added to `DirectoriesToAlwaysCook` | applied |

The cook-list line is not cosmetic. `BP_SirMelodiousPlayerUnit` is loaded at runtime by a
hardcoded `LoadClass` in `MelodiaJRPGPartyBootstrapSubsystem`, and its only static
referencer was the orphan mirror tree. Without that line it is not cooked, `LoadClass`
returns null in a packaged build, and **Sir silently never joins the party** — working
perfectly in PIE the whole time.

## The graph to author

Target: **`/Game/MelodiaIntegration/Party/Skills/BP_SirSkyboundRefrain`** — confirmed the
real asset (3 referencers; the `Content_MelodiaIntegration` copy has none).

In the Blueprint editor, override the parent event and **add a call to parent**:

1. My Blueprint → Functions → Override → `UseSkillOnNotify`
2. Inside it, right-click → **Add Call to Parent Function** (this is the critical step)
3. Wire:

```
[Entry]
   → Get battleController → Get currentTargetUnit → Get activeBuffs
   → Map Contains (key = BP_Resonance_C)  ── bool ──> [Branch]
                                                        │
   True  → Set damageMultiplier = 1.8                   │
         → Map Remove (activeBuffs, key = BP_Resonance_C)   ← the "consume"
         → ┐                                            │
   False → Set damageMultiplier = 1.2                   │
         → ┘                                            │
              → [Call Parent: UseSkillOnNotify]
```

`activeBuffs` is `TMap` keyed by **class** (`map:class:BP_BuffBase_C`) on `BP_UnitBase`, so
`Contains`/`Remove` take `BP_Resonance_C` as the key. There is no buff-removal helper
function on `BP_UnitBase` — removing the map entry is the mechanism.

Setting `damageMultiplier` before the parent call is what makes this work: the parent's
`UseSkillOnNotify` reads that variable and feeds it straight into
`DealDamage(pureDamage=0, damageMultiplier=...)`.

## Why not automated

`override_parent_function` via MCP creates an **empty function graph** that replaces the
parent's event implementation wholesale. That is precisely the defect class that broke
`BP_MelodiaBattleUI` this morning — ten empty child events shadowing working parent ones,
including `ShowBattleUI`, which is why the battle UI never appeared.

I created that hazard here, detected it, and removed it (`remove_function`); the Blueprint
is back to its original 3-node EventGraph + UserConstructionScript. The correct pattern
needs a `K2Node_CallParentFunction`, which I could not confirm Monolith can author. Doing it
by hand is one right-click and about five minutes; doing it wrong silently disables Sir's
entire skill.

**Verify after authoring:** `BP_SirSkyboundRefrain` must still show `parent_class:
BP_FocusAttack_C` and the override must contain a visible "Parent: UseSkillOnNotify" node.
If that node is absent, the skill deals no damage at all.

## Still owed beyond this

- **`skillAnimation` has no entry for `BP_SirMelodiousPlayerUnit`.** The map currently only
  maps the Swordsman and Melusina units. Sir has exactly one animation
  (`FreeCameraTrackingframeupdate_Anim_RT`, 31.9s flight + landing) and no attack montage.
  The dive section — roughly **t=8 to t=13** — reads as a swooping strike and would make a
  serviceable Skybound Refrain montage if trimmed.
- **Turn order is unverified.** Both units have `speed = 0` in their CDOs and turn order is
  ActionTime-driven, so there is no guarantee Sir acts within Resonance's 2-turn window.
  Worth confirming in PIE before tuning the multiplier further.
- **Petal Cadence lives in `/Game/Experiments/MelodiaJRPG/Skills/`** while Skybound Refrain
  lives in `/Game/MelodiaIntegration/Party/Skills/`. Half the co-op pair is in an
  Experiments folder. Both are live; the split is just fragile.
