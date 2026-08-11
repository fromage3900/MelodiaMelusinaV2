# Melodia Solo Gameplay Constitution

**Date:** 2026-07-27  
**Status:** active operating contract  
**Owner:** the human creator is the sole product, scope, and release authority

## Purpose

This project is being made by one person. Architecture, tooling, documentation,
and agent behavior must reduce cognitive load rather than simulate a studio.
The project is successful when one person can return after a break and answer:

- What am I building now?
- Which system owns this state?
- What is the smallest proof?
- What is explicitly out of scope?
- When do I stop for today?

## Product target

The first shippable gameplay proof is a small, authored persona-lite loop:

```text
bedroom / sanctuary
  -> short authored dialogue
  -> compact exploration route
  -> one fixed JRPG encounter
  -> typed result
  -> buddy / companion reaction
  -> return to bed and save
  -> one visible narrative consequence
```

This is inspired by the intimacy and consequence of OMORI, the readable musical
feedback of Theatrhythm, and the beauty, character attachment, and outfit
identity of Infinity Nikki. These are quality lenses, not feature-count targets.

## Authority map

| Concern | Sole authority | Allowed role for Melodia/Quill |
|---|---|---|
| Battle, party, inventory, quests, travel, input | TurnBased JRPG foundation | None beyond approved requests/results |
| Canonical save transaction | JRPG GameInstance/save flow | Embedded versioned narrative record only |
| Dialogue, choices, labels, authored sequence | QuillScript behind the project adapter | Cannot own gameplay state or raw travel |
| Narrative intent validation and resume | Melodia narrative adapter | Allowlist IDs, reject duplicates/unknowns |
| Melusina, hair, companion, animation, battle feedback | Presentation layer | Cannot resolve damage or advance turns |
| Rhythm | Optional presentation/bonus layer | Never required for basic battle completion |
| Outfit identity | One bounded presentation/interaction slice | No wardrobe platform until loop proves |
| Dissonance | One bounded authored state later | No global framework or hidden stat mutation |

Do not add MelodiaCore, ACFU, a second save system, a second dialogue system,
or a procedural-run authority to this route.

## Solo operating rules

1. **One active workstream.** The current workstream is Quill dialogue -> JRPG
   battle -> result -> Quill resume -> narrative save.
2. **WIP limit: one difficult problem.** Research, implementation, and proof for
   one problem finish before another begins.
3. **NOW contains one task. NEXT contains at most three.** Everything else is
   LATER, frozen, or historical.
4. **No background mutation loops during gameplay work.** Do not run recursive
   agent daemons, unattended content generators, or periodic asset writers.
5. **No parallel authorities.** If an existing system already owns a concern,
   adapters consume it; they do not recreate it.
6. **Every task has a binary acceptance gate before implementation begins.**
   If no observable gate exists, the item is research, not implementation.
7. **One verification pass is enough.** Record the result and move on; do not
   create verification work whose only purpose is to re-prove a closed item.
8. **Stop after the gate passes or the timebox expires.** A blocked task becomes
   a documented decision, not an overnight grind.
9. **No scope expansion from inspiration.** References may improve a proven
   slice; they cannot introduce a new subsystem without a product decision.
10. **Protect recovery.** End each session with the exact next action, known
    blockers, files changed, and explicit do-not-touch boundaries.

## Current phase and acceptance gate

**Phase:** stabilize the proven Persona-lite gameplay wiring, then close persistence and terminal-result gates.  
**Active task:** prove canonical JRPG persistence and the complete terminal-result matrix without adding a second gameplay authority.

Already proven:

```text
Morning Sir interaction
  -> visible Quill dialogue completion
  -> native departure/travel
  -> Dreamstate traversal
  -> ZenForest test arrival

ZenForest Persona-lite interaction
  -> Petal Priestess activates/completes quest 1
  -> Star Weaver activates quest 2
  -> quest-gated Rhythm Echo marker becomes visible
  -> Persona equipment request reaches the stock-controller adapter contract
```

The active Melusina JRPG presentation unit now carries Focus Attack at level 1, Thunderbolt and Basic Heal at level 2, and Meteor Storm at level 4. `BP_ExploreUI` owns the single Resonance Map panel; no second HUD was created. Placed Persona NPCs have exact identity tags and route interaction notifications into the Persona facade. Focused build, Blueprint/widget readback, NPC verification, and PIE smoke `pie_smoke_2_163720` passed.

Required before the vertical slice is release-ready:

```text
one runtime-proven battle widget/root
Victory + Defeat + Fled + unavailable each terminate/resume exactly once
canonical BP_JRPGSaveGame survives a full process restart
equipment persistence is proven on the active stock-controller route
no duplicate reward, dialogue, encounter, HUD, input, quest, or save authority
Morning_RoomShell validator contract repaired
cook name assertion identified or isolated
```

The Main Menu New Game boundary is deterministic and rebuilt. Continue and Load Game remain intentionally disabled while no validated canonical slot exists and `WBP_SaveLoad` remains an empty shell. Do not infer save readiness from successful Persona quest or equipment-request smoke tests.

Combat expansion is limited to improving the already-proven stock encounter: readable command UI, one additional meaningful enemy decision or player option at a time, typed result coverage, and feedback. It does not authorize a second battle system, procedural run framework, broad enemy roster, or environment rebuild.

## Save gate after bridge proof

The minimum canonical narrative record is:

```text
NarrativeSchemaVersion
ActiveScriptId
ResumeLabel
AllowlistedNarrativeFlags
ConsumedIntentIds
ConsumedRewardIds
```

Required cases:

- save before battle and reload safely;
- save after result and restore the narrative consequence;
- duplicate rewards remain rejected;
- missing script/label returns to an authored safe checkpoint;
- JRPG save remains loadable without Quill runtime presence.

## Deferred and frozen work

Frozen until the persona-lite loop passes:

- procedural roguelike depth and seeded room runs;
- MelodiaCore gameplay authority and its old AV/modifier backlog;
- ACFU integration;
- broad wardrobe/inventory systems;
- companion flight and large traversal systems;
- rhythm as battle authority;
- TouchDesigner/OSC gameplay orchestration;
- broad presentation-interface rewrites;
- autonomous content daemons;
- framework cleanup that does not unblock the active gate.

Legacy documents describing these systems remain useful historical evidence but
are not active instructions. The current JRPG/Quill architecture documents and
this constitution take precedence.

## Session closeout template

At the end of each gameplay session record:

```text
Active phase:
One completed proof:
One next action:
Known blocker:
Files changed:
Runtime proof owned by user:
Do not touch:
```

A session is successful when it leaves the project easier to resume than it was
at the start.
