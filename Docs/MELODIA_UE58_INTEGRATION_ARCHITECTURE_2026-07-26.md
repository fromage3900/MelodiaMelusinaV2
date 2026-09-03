# Melodia UE5.8 Integration Architecture

**Date:** 2026-07-26  
**Status:** active architecture decision and phased research roadmap  
**Production mutation:** none authorized by this document  
**Current product shape:** small authored, VN-led, outfit-aware turn-based RPG loop

## Executive decision

Build the authored game around the complete TurnBased JRPG template as the
mechanical authority. Use project-owned adapters to attach:

- Melodia/Melusina presentation;
- QuillScript narrative authoring, if its runtime gates pass;
- selected Melodia concepts as data or presentation;
- existing portfolio environments as authored destinations.

Do not merge framework authorities. In particular:

- MelodiaCore does not own runtime gameplay;
- ACFU does not enter the chosen turn-based production route;
- QuillScript does not own gameplay state, travel, rewards, quests, or saves;
- presentation notifies do not compute damage or advance turns independently.

The architecture is composition around one proven state spine, not a synthesis
of several frameworks.

## Product boundary

The active loop is:

```text
bedroom / authored dialogue
  -> authored exploration
  -> fixed turn-based encounter
  -> result / quest / companion dialogue
  -> sanctuary / save
```

The following remain outside the current production scope:

- procedural roguelike expedition generation;
- MelodiaCore rhythm authority;
- ACFU action combat;
- broad multiplayer;
- multiple competing inventories, quest systems, or save formats;
- direct QuillScript access to gameplay classes or world travel;
- Infinity Nikki-scale wardrobe breadth.

Infinity Nikki is the quality lens: authored beauty, readable routes,
character attachment, outfit identity, material richness, and polished
interaction feedback. It is not the required feature count.

## Evidence-based authority map

| Concern | Authoritative owner | Allowed consumers | Forbidden duplicate |
|---|---|---|---|
| Game mode and input state | JRPG player controller/game mode | narrative adapter, UI skin | Quill interpreter or Melodia character changing mode directly |
| Battle scheduling | JRPG battle controller | presentation adapter, telemetry | MelodiaCore rhythm session or montage completion advancing turns |
| Damage/heal resolution | JRPG skill and unit flow | hit/VFX/UI presentation | animation notify applying a second effect |
| Party and progression | JRPG controller/data | outfit/presentation queries | Melodia party/progression or ACFU RPG components |
| Inventory/equipment | JRPG inventory/equipment | project reward adapter | ACFU inventory or Melodia inventory as a second store |
| Quests | JRPG quest flow | narrative intent adapter | ACFU quest graph or Quill global variables as canonical quest state |
| Save/load | JRPG game instance/save object | embedded project narrative record | Quill or ACFU writing an independent canonical slot |
| Dialogue sequencing | QuillScript candidate | project narrative adapter | ACFU dialogue system in the turn-based route |
| Character visuals | Melusina presentation adapter | JRPG unit | Melodia exploration character replacing battle-unit authority |
| Environments | authored Melodia maps | transition policy | raw script travel to arbitrary level paths |

## Why the JRPG route wins

Current evidence for the complete standalone template:

- user-verified battles, party, quests, turn management, and UI;
- 412-package complete source located and isolated;
- repaired UE5.8 lab compiles with 0 Blueprint errors, 0 warnings, and 0 load
  failures;
- `MainMenu`, `Gameplay`, and `BattleMap` initialize in UE5.8;
- clear asynchronous battle-result and quest seams;
- existing skills already use animation-notify-mediated resolution.

Remaining uncertainty is bounded: interactive UE5.8 regression, save/load,
packaging, and presentation adaptation. Replacing this foundation would
reintroduce uncertainty across every gameplay concern simultaneously.

## ACFU disposition

ACFU 4.2.3 is a credible alternative action-RPG foundation, not a lightweight
combat add-on. Its plugin declares 46 source modules, including:

- combat, actions, targeting, collisions, executions, status effects, GAS;
- character controller, AI, teams, units, mounts, vehicles;
- inventory, crafting, RPG progression, quests, dialogue, morality;
- save, maps, loading screen, UI navigation, skill trees, state machines;
- multiple graph/editor modules.

Its quest manager, save system, dialogue participants, inventory model, and
character controller overlap directly with the chosen JRPG authorities.
Importing only “combat” would still create dependency and ownership pressure
from the surrounding framework.

Decision:

- preserve the ACFU archive as comparative/reference evidence;
- do not build an ACFU UE5.8 lab during the portfolio render window;
- revisit only after an explicit product pivot to real-time action RPG;
- if revisited, evaluate it as a replacement foundation in a separate project,
  never as a parallel authority inside the JRPG route.

## QuillScript disposition

QuillScript 2.5 is narrower than ACFU and remains a viable candidate, but it is
not stateless.

Verified useful seams:

- dialogue, selection, statement, start, end, and variable-change delegates;
- interpreter pause/resume and label flow;
- Blueprint-callable script playback;
- project-callable hooks can pause script flow and resume by callback.

Verified authority risks:

- game-instance subsystem stores global variables and per-script history;
- snapshots include variables, interpreter state, script settings, background,
  and looping audio;
- `SaveGameAndStoryToSlot`, `LoadGameAndStoryFromSlot`, and
  `ResumeGameAndStoryFromSlot` wrap gameplay saves;
- `Travel` starts another script directly;
- broad Blueprint-callable interpreter surface can bypass a project adapter if
  used casually.

Official Quill documentation confirms that scripts can invoke Blueprint/C++
`UFUNCTION`s, address named objects, and reference assets by Unreal path. It
also warns that passing a mismatched referenced object can crash. This makes an
allowlisted adapter a safety boundary, not merely a style preference.

Therefore the production contract is:

```text
QuillScript authors narrative-local flow
  -> emits a project-owned intent ID
  -> adapter validates the ID and current game state
  -> JRPG authority performs the operation
  -> adapter returns a typed result
  -> interpreter resumes
```

Initial allowlist:

- `StartBattle(EncounterId)`
- `CompleteQuest(QuestId)`
- `SetNarrativeFlag(FlagId, Value)`
- `RequestTravel(LevelId)`
- `GrantDialogueReward(RewardId)`

Unknown commands, raw class paths, raw level paths, arbitrary function
addresses, and direct controller references are rejected.

### Why the JRPG “Dialogues” folder is not a narrative substitute

Live Blueprint inspection shows that the template's
`Blueprints/UI/Dialogues` folder is a collection of modal gameplay widgets:
information/confirmation boxes, victory/defeat, item amounts, shops, crafting,
equipment, skills, quests, and level-up UI.

For example:

- `BP_InfoDialogue` exposes title/text and `OnConfirmed`;
- `BP_YesNoDialogue` exposes title/text and yes/no delegates;
- `BP_DialogueButton` is a generic button with `OnButtonClicked`.

These are useful UI primitives but do not provide authored speaker flow,
branching labels, narrative conditions, history, localization workflow, or
asynchronous story orchestration. They should remain template UI. QuillScript
is still the correct narrative candidate if its runtime gates pass.

The separate 5.7 sample includes two optional compatibility widgets named
`Conversation2DSampleUI` and `Conversation2DSampleShopUI`. Despite their names
and embedded marketing text, package inspection found no
`/Script/Conversation2D` reference: both are ordinary `BP_UIBase` children
using engine, template, and sample assets. Neither the sample nor UE5.8 lab
project descriptor enables `Conversation2D`, and the complete UE5.8 template
compiles with no such package reference. Treat Conversation2D as an obsolete
sample integration, not a dependency of the battle, party, quest, turn, UI, or
save foundation. Exclude those two sample widgets from migration.

ACFU's dialogue module is not considered for this route because adopting it
would reintroduce the broader ACFU dependency/authority surface solely to solve
a concern QuillScript addresses more narrowly.

## Save contract

There will be one canonical slot and one save transaction owner: the JRPG game
instance/save flow.

QuillScript integration must use a project-owned serializable narrative record,
for example:

```text
NarrativeSchemaVersion
ActiveScriptId
ResumeLabel
AllowlistedNarrativeFlags
CompletedNarrativeBeatIds
```

Live inspection confirms that `BP_JRPGSaveGame` currently serializes character
transform, player units, items, equipment, removed battles, interactions, map,
party, gold, and active/completed quests. It does not expose an explicit schema
version or narrative record. Adding narrative persistence is therefore a
planned save-schema change with migration tests, not an incidental Quill setup
step.

Do not persist the entire Quill global-variable map as canonical gameplay
state. Do not call Quill's slot helpers from production UI. On load, the
project adapter reconstructs only the approved narrative state and asks Quill
to resume at an approved script/label.

Before any production save integration:

1. prove a Quill dialogue can pause and resume in its own lab;
2. define migration behavior for renamed scripts, labels, and flags;
3. verify missing script/label recovery returns to a safe authored checkpoint;
4. prove the JRPG save remains loadable with no Quill runtime present;
5. prove narrative restoration does not duplicate rewards or quest completion.

## Character-skill presentation contract

The lab-only `BP_MelusinaSwordsman_Presentation` is the correct first adapter:

- JRPG unit inheritance preserves mechanical authority;
- a dedicated Melusina mesh handles visuals;
- a clean plain-`AnimInstance` AnimBP avoids MelodiaCore/Kawaii dependencies;
- the JRPG montage notify remains the sole effect-resolution signal.

Required invariants:

- one accepted command;
- one montage start;
- exactly one `BP_UseSkillN` impact notify;
- one JRPG effect application;
- one presentation completion;
- one turn release;
- timeout recovery if presentation fails.

The production `ABP_Melusina_Current` is not an integration dependency. Its
hard MelodiaCore, KawaiiPhysicsEd, custom-version, and UE5.8 Property Access
failure surface confirms the need for a clean adapter AnimBP.

## Presentation layering

Use three layers:

1. **Mechanical event:** JRPG validates and resolves skill state.
2. **Authored timing:** montage and one impact notify align visible contact.
3. **Cosmetic response:** VFX, audio, camera, hit reaction, and UI subscribe to
   the resolved event but cannot alter the result.

Rhythm may later modify presentation grading or a bounded optional bonus only
after deterministic battle behavior is proven. It may not become required for
turn completion or basic damage.

## Phased execution roadmap

### Status annotation — 2026-07-28

The project has completed a bounded portion of Phase 3 and Phase 4 in the live project:

- typed encounter/quest/flag/reward/equipment/minimap IDs exist behind project adapters;
- the playable opening reaches ZenForest;
- three placed NPCs advance a sequential Persona quest chain;
- the active stock ExploreUI owns one quest-gated marker panel;
- the active Melusina JRPG unit owns a four-skill stock progression;
- Persona equipment requests map to and call the stock equipment API;
- focused build/readback and PIE smoke `pie_smoke_2_163720` pass.

Phase 4 is not complete because full battle-result coverage and process-restart canonical save/load remain unproven. Phase 5 remains presentation-only and must not begin by introducing another inventory, quest, combat, HUD, or save authority.

### Phase 0 — portfolio protection

- production remains read-only for gameplay;
- finish hero renders and technical breakdown;
- keep each framework in its isolated lab/archive;
- maintain healthy project/DDC storage.

Exit: portfolio capture work is not disrupted by compatibility experiments.

### Phase 1 — independent runtime proofs

JRPG:

- complete one interactive battle in UE5.8;
- verify skill, item, victory, flee/defeat, party, quest, save/load;
- build and launch Development.

QuillScript:

- repair or bypass editor-only `StatementBP`;
- create/reload one script asset;
- prove dialogue, choice, condition, variable, label, callback, pause/resume;
- reject an unknown callback;
- build and launch Development.

Exit: both candidates work independently in UE5.8.

### Phase 2 — character-skill slice

- visually choose the `AM_Mocap_BasicAttack` impact frame;
- add exactly one `BP_UseSkillN` notify;
- run the experimental unit in a disposable battle;
- record command, impact, resolution, completion, and turn-release timestamps;
- repeat with one heal only after attack passes.

Exit: Melusina presentation drives no duplicate or missing JRPG resolution.

### Phase 3 — narrative bridge slice

- create project-owned ID tables for encounter, quest, flag, reward, and level;
- implement the narrow adapter in a disposable integration lab;
- prove `dialogue -> battle -> result -> dialogue`;
- prove unknown IDs fail safely;
- keep Quill save helpers unused.

Exit: narrative can orchestrate one authored loop without owning gameplay.

### Phase 4 — authored vertical loop

- bedroom dialogue;
- one authored exploration route;
- one battle;
- one result/companion dialogue;
- one sanctuary save/load return.

Exit: a player completes the loop after relaunch with correct state and no
framework-specific debug UI.

### Phase 5 — presentation and outfit proof

- replace placeholder UI skin without changing behavior;
- add one outfit identity and one readable outfit-linked affordance;
- add companion and battle presentation;
- capture performance and portfolio evidence.

Exit: the result reads as an authored Melodia experience rather than a template
or systems demo.

## Stop/go rules

Stop integration and return to the previous proven phase if:

- a framework requires ownership of an already-authoritative concern;
- a second canonical save path appears;
- a battle effect can resolve more than once;
- a missing presentation callback can deadlock a turn;
- script content contains raw Blueprint or level paths;
- production must import unstable MelodiaCore/Kawaii dependencies;
- package/build evidence is substituted for interactive runtime evidence.

Proceed only when the prior phase has a reproducible artifact, log, or human
runtime observation.

## Documentation reconciliation

Current:

- `PROJECT_STATUS_2026-07-25.md`
- `JRPG_QUILLSCRIPT_FOUNDATION_2026-07-25.md`
- this architecture decision;
- `MELODIA_INTEGRATION_EVIDENCE_REGISTER_2026-07-26.md`;
- `MELODIA_JRPG_CHARACTER_SKILL_SLICE_2026-07-26.md`

Reference, but not active authority:

- `MELODIA_ACFU_QUILLSCRIPT_COMPATIBILITY_MATRIX_2026-07-25.md`
- `MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md`
- `BP_INTEGRATION_REVIEW_2026-07-18.md`
- MelodiaCore rhythm/presentation implementation documents.

Superseded as production scope:

- procedural roguelike completion plans;
- recursive-expedition requirements in the first-20-minutes plan;
- plans that treat MelodiaCore as battle authority;
- plans that imply ACFU and JRPG should coexist.

Superseded documents remain useful historical evidence and should be labeled,
not deleted.

## Immediate shared tasks

User:

- finish portfolio renders;
- visually scrub the basic-attack montage, especially 3.5–4.5 seconds, and
  report the intended contact time/frame;
- optionally perform a manual Quill dialogue/choice test and preserve exact
  errors or screenshots;
- do not save the dirty JRPG `Gameplay` map.

Codex:

- inspect JRPG extension seams and prepare the battle test harness plan;
- specify the Quill smoke-test script and callback rejection cases;
- keep ACFU archival/reference-only;
- update status documentation as gates become evidence-backed;
- perform only isolated, reversible lab work during rendering.

## External primary references

- QuillScript getting started:
  `https://quillscript.ink/getting-started/`
- QuillScript function calls:
  `https://quillscript.ink/language/command/function-call/`
- QuillScript save helpers:
  `https://quillscript.ink/coding-and-design/libraries/quill/`
- QuillScript labels, options, and conditions:
  `https://quillscript.ink/language/label/`
  `https://quillscript.ink/language/option/`
  `https://quillscript.ink/language/condition/`
- ACF Ultimate documentation:
  `https://slimwiki.com/dark-tower-int/acfu/welcome`
