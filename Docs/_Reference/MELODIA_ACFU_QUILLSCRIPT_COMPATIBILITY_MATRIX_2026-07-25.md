# MelodiaCore / ACFU / QuillScript Compatibility Matrix

**Date:** 2026-07-25  
**Purpose:** establish safe ownership boundaries before any UE5.8 integration  
**Evidence:** current BS_GodFile source, Monolith project status, ACFU 4.2.3 source package, Quillscript 2.5 source package

## Executive decision — revised after runtime-stability evidence

Do **not** designate MelodiaCore as the production gameplay authority in its
current state. Existing integration is not sufficient evidence of suitability:
the project history records repeated runtime regressions, incomplete end-to-end
PIE proof, unimplemented presentation interfaces, and unresolved battle-rule
correctness issues.

Choose one stable gameplay route:

- **Turn-based route:** the imported TurnBased JRPG template owns battle and its
  supporting runtime.
- **Action-RPG route:** ACFU owns combat and its supporting RPG runtime.

Evaluate **QuillScript as the single narrative/dialogue layer** for either
route. Treat MelodiaCore as a source of project-specific ideas and selectively
salvageable code—not as an active parallel framework.

## Evidence snapshot

| System | Package evidence | UE target | Primary shape |
|---|---|---:|---|
| MelodiaCore | Project plugin source, compiled UE integration, and project regression/audit history | 5.8 | Custom turn-based rhythm kernel; currently runtime-unstable per user observation |
| TurnBased JRPG template | Complete 412-package standalone source at `G:\ueprojects\TurnBasedjRPGTemplate`; two incomplete 330-package imports in `BS_GodFile` | 5.7 source project; UE5.8 lab staged | Standalone runtime stable per user observation; production import not yet proven |
| ACFU | `AscentCombatFramework.uplugin`, version 4.2.3, 40+ source modules, including `AscentDialogueSystem` | 5.7 | Broad action-RPG framework and editor ecosystem |
| QuillScript | `Quillscript.uplugin`, version 2.5, runtime + editor source | 5.7 | Text scripting/interpreter for dialogue and scenes |

UE5.7 package compatibility with UE5.8 is **not yet proven** for either
external plugin. QuillScript has reached UE5.8 source/UHT generation in an
isolated lab after moving the target to `BuildSettingsVersion.V7`; the full
compile is waiting for a natural window in which Live Coding is inactive.
Source availability makes compatibility testing possible; prebuilt binaries
must not be copied into the production project as-is.

## Authority matrix

| Capability | MelodiaCore | TurnBased JRPG template | ACFU | QuillScript | Production decision |
|---|---|---|---|---|---|
| Turn-based battle phases | Custom but unstable | Stable route candidate | Not the turn-based route | None | JRPG template exclusive if turn-based |
| Real-time action combat | Not its design | Not its design | Stable route candidate | None | ACFU exclusive if action RPG |
| Rhythm execution/input | Unique prototype value | Possible future extension point | Possible future extension point | None | Salvage only after base route is stable |
| Combat stats/modifiers | Custom and correctness backlog exists | Template-owned for turn-based route | GAS/ARS-owned for action route | None | Selected route owns all combat stats |
| Character/outfit runtime | Project-specific scaffold | Route adapter required | Full character/controller stack | None | Selected route + project cosmetic layer |
| Inventory/economy | Partial and fragmented | Template-owned if selected | Full inventory/crafting/RPG ecosystem | None | Never run two inventory authorities |
| Quest state | Simple custom manager | Template-owned if selected | Full graph-based quest system | None | Selected route owns quest state |
| VN/dialogue scripting | Current weak/flat path | No mature project-native system identified | `UADSDialogueMasterComponent`, participant components, dialogue assets/cinematics | `UQuillscriptAsset` + `AQuillscriptInterpreter` | QuillScript candidate, pending UE5.8 test |
| Branching/options/conditions | Not mature | No verified narrative authority | Possible through ACFU Dialogue but broad | Native language/interpreter support | QuillScript candidate |
| World travel/transitions | Custom but coupled | Template route owns gameplay transitions | ACFU maps/state systems | Script commands may request travel | Selected route owns; QuillScript emits intent |
| Save/persistence | Custom and tightly coupled | Template route owns or adapts save | ACFU save system | Script state needs adapter | Selected route owns one save schema |
| UI/dialogue box | Existing project widgets | Template battle UI | ACFU UI tools | Can manage or broadcast dialogue UI | Project art layer may skin; route owns behavior |
| Animation/state machine | Partial project scaffold | Template route requirements | Extensive ACFU systems | None | Use only selected route's animation authority |
| PCG/environment systems | Existing project pipeline | No ownership needed | No ownership needed | None | Environment pipeline remains independent |

## Coexistence rules

### Selected stable route + QuillScript: acceptable hybrid

QuillScript may own:

- authored script text and labels;
- dialogue sequencing;
- options and branching;
- script-local variables and conditions;
- narrative callbacks/events.

Its source shows a real interpreter surface rather than a passive text asset:
scripts can travel between labels/scripts, evaluate conditions, mutate
script-local variables, present dialogue/options, and broadcast dialogue-box
events. That makes it a plausible fit for the missing VN layer, but also means
its variables must not silently become a second save/progression store.

The selected gameplay route must own:

- player/world/game state;
- save slots and persistence;
- quest progression authority;
- battle launch and battle results;
- level travel and transition policy;
- inventory, progression, and reward mutation.

The integration boundary should be one-directional and explicit:

`QuillScript event/intent → project adapter → selected route authority`

QuillScript must not directly mutate save data, battle state, inventory, or map
transitions through hidden global lookups.

### MelodiaCore: quarantine and selective salvage

MelodiaCore may be used for:

- rhythm grading and musical-reactivity concepts;
- project-specific enemy/songcraft data worth migrating;
- tests or formulas that can validate replacement behavior;
- isolated code extraction after dependency review.

Do not keep MelodiaCore enabled merely to reuse one feature. Extract the feature
behind a small project-owned interface or migrate its data, then remove the
parallel authority.

### ACFU: valid only as the selected action-RPG route

ACFU's breadth is an advantage if the game is intentionally real-time/action
RPG. It remains a liability if combined with the TurnBased JRPG template or
MelodiaCore. Its dialogue system is also a direct QuillScript competitor;
select one narrative runtime.

ACFU must not be enabled in the production `.uproject` until the action-RPG
route is explicitly selected and its UE5.8 smoke gates pass, with an explicit
migration boundary and rollback path.

## Route comparison

| Route | Advantages | Costs / risks | Status |
|---|---|---|---|
| TurnBased JRPG template + QuillScript | Stable turn-based base aligned with corrected Persona-like loop | Requires project art/content adaptation and a narrow narrative bridge | Recommended if turn-based |
| ACFU + QuillScript | Stable broad action-RPG foundation and focused script authoring | Much larger runtime; UE5.8 source-build proof required | Recommended only if action RPG |
| Native MelodiaCore only | Preserves custom rhythm ideas | Runtime instability and unresolved correctness/presentation debt | Do not use as foundation now |
| ACFU + TurnBased template | Maximum feature breadth | Competing combat, stats, save, input, UI, and character ownership | Reject |
| Any route + active MelodiaCore framework | Retains custom features quickly | Parallel authority and regression surface | Reject; salvage selectively |

## UE5.8 compatibility gates

Neither external plugin is approved for production integration until all gates
pass in a disposable UE5.8 test project:

1. Source compilation against the installed UE5.8 toolchain.
2. Editor startup with the plugin enabled and no module-load errors.
3. Creation/loading of one representative asset or test map.
4. Packaged Development build launch.
5. Runtime smoke test for the capability being evaluated.
6. No new dependency or ownership conflict with the selected gameplay route.

For QuillScript, the representative smoke test should include a script with
dialogue, a choice, a condition, a label jump, a variable mutation, and a
callback into a project-owned adapter.

The adapter must translate only approved intents, for example:

- `StartBattle(EncounterId)`
- `CompleteQuest(QuestId)`
- `SetNarrativeFlag(FlagId, Value)`
- `RequestTravel(LevelId)`
- `GrantDialogueReward(RewardId)`

The adapter must reject or log unknown intents and must not expose raw save,
inventory, or subsystem pointers to script authors.

For ACFU, run the smoke test only if the product decision is explicitly the
action-RPG route. Compatibility alone is not a reason to select that route.

## Explicit non-adoption list

Do not currently adopt:

- MelodiaCore as the production runtime authority without a new end-to-end
  stability proof.
- ACFU alongside the TurnBased JRPG template.
- MelodiaCore combat/save/quest/progression systems alongside either stable
  replacement route.
- ACFU GAS/statistics, inventory, save, quest, or animation systems piecemeal
  inside the turn-based route.
- Both ACFU Dialogue and QuillScript.
- Any external plugin binary built only for UE5.7 in the production project.

## Follow-up research

- Prove the complete 412-package standalone template in
  `CompatibilityLabs/TurnBasedJRPGUE58`; do not treat either incomplete
  330-package production import as the runtime baseline.
- Continue the TurnBased JRPG template seam inventory from
  `Docs/JRPG_QUILLSCRIPT_FOUNDATION_2026-07-25.md`.
- Validate QuillScript API and UE5.8 compilation in isolation.
- Compare a minimal turn-based vertical slice against an isolated ACFU action
  slice before selecting the product route.
- Extract a minimal QuillScript-to-selected-route adapter contract if
  compatibility passes.
- Mark legacy roguelike plans as superseded by the fixed-loop brief.
- Revisit ACFU only if the post-portfolio gameplay brief expands materially.

## Current conclusion

The durable foundation is route-dependent: **the TurnBased JRPG template owns
the game if the target remains the small Persona-like loop; ACFU owns the game
if the target becomes action RPG; QuillScript may author the story in either
case; MelodiaCore is quarantined and selectively salvaged.**
