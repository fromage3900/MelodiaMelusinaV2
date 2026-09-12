# JRPG Desktop UI and Quill Dialogue — Next Implementation Plan

**Date:** 2026-07-28  
**Goal:** Polish the already functional Melusina JRPG battle path for desktop keyboard/mouse use and make the Quill-authored narrative path visibly verifiable without creating a second gameplay authority.

## Baseline evidence

The user has interactively verified that Melusina can enter the stock JRPG battle, cast a skill, and apply damage. The project defines keyboard mappings in `Config/DefaultInput.ini`, including:

| Action | Desktop binding |
|---|---|
| Confirm | Enter, Space |
| Cancel | Escape |
| Navigate | WASD, arrow keys |
| Attack | J |
| Skill | K |
| Item | I |
| Flee | F |
| Interact | E |
| Open menu | Tab |

The remaining desktop battle problem is not missing key declarations. It is active Widget Blueprint presentation, mouse/button binding, focus ownership, and visible Quill dialogue lifecycle.

## Persona-lite wiring status — 2026-07-28

The exploration-side Persona-lite foundation is now implemented and must not be reopened as discovery work:

- active Melusina unit: `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation`;
- skill unlock map: Focus Attack 1, Thunderbolt 2, Basic Heal 2, Meteor Storm 4;
- active exploration HUD: `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ExploreUI`;
- one `MelodiaMinimapPanel` with NPC markers and quest-gated encounter/exit markers;
- placed Petal Priestess, Star Weaver, and Twilight Dancer use exact identity tags plus `MelodiaQuestNPC`;
- NPC interaction routes the corresponding quest notification through `UMelodiaPersonaSubsystem`;
- equipment IDs resolve to stock `BP_Rod`, `BP_LeatherArmor`, and `BP_LeatherBoots`, then call the stock controller's inventory/equip functions when that controller is active.

Validation evidence:

- both `UnrealEditor-BS_GodFile.dll` and `UnrealEditor-MelodiaCore.dll` linked;
- active unit and `BP_ExploreUI` compile with zero focused errors/warnings;
- NPC metadata verification passed for all three actors;
- PIE smoke `pie_smoke_2_163720` returned `ok=true`, proving quest 1 activation/completion, quest 2 activation, gated Rhythm Echo visibility, and an accepted equipment request with no runtime errors, `Accessed None`, tracebacks, or equipment-resolution warnings.

Do not claim direct inventory readback from `ZenForestTest`: that map currently uses `MelodiaSmokeCharacter` with a plain `PlayerController`. Full inventory mutation/persistence evidence belongs to the active stock JRPG controller route and the canonical save test.

## Authority rules

1. Stock JRPG Blueprint functions remain authoritative for command selection, targets, turns, damage, resources, and results.
2. UMG buttons call existing stock command functions; they do not recalculate or mutate combat state independently.
3. QuillScript owns dialogue flow and choice sequencing.
4. `UMelodiaNarrativeSubsystem` validates allowlisted intents and tracks the active interpreter; it does not force uninitialized plugin widgets into the viewport.
5. Exactly one runtime battle HUD and one active dialogue/selection layer may exist.

## Workstream A — Identify the active JRPG widget root

The project contains parallel full JRPG trees:

- `/Game/TurnBasedJRPGTemplate`
- `/Game/_ThirdParty/TurnBasedJRPGTemplate`

Do not assume which one is active. In the playable map:

1. Inspect GameMode, PlayerController, BattleBase, and BattleController class references.
2. Start PIE and use Widget Reflector or runtime object inspection to identify the instantiated battle widget class and package path.
3. Record that path before modifying any asset.
4. Make changes only in the active root.
5. Confirm only one battle HUD is added to the viewport.

**Stop condition:** if the active widget cannot be identified unambiguously, do not edit either duplicate root.

## Workstream B — Desktop command strip

For the active battle command widget:

1. Replace PS2-specific glyph-only prompts with command text plus input labels.
2. Use focusable `UButton` controls for Attack, Skill, Item, Flee, Confirm, and Back where applicable.
3. Bind `OnClicked` to the same existing functions/events used by the stock controller input path.
4. Disable buttons while the command is illegal, a montage/turn is resolving, or the actor is not active.
5. On command-menu entry, focus Attack or the last valid command.
6. On submenu cancellation, restore focus to the originating command.
7. On target cancellation, restore focus to the originating skill/item.
8. Add visible hover, focused, pressed, disabled, and selected states.

Recommended prompt labels:

- `Attack  [J]`
- `Skill  [K]`
- `Item  [I]`
- `Flee  [F]`
- `Confirm  [Enter / Space]`
- `Back  [Esc]`
- `Navigate  [WASD / Arrows]`

Do not add `LeftMouseButton` as a global `MenuConfirm` mapping. Mouse activation must occur through button hit testing.

## Workstream C — Input and focus lifecycle

At battle command selection:

- set input mode to Game and UI;
- show the cursor;
- enable click and mouse-over events;
- focus the initial command button;
- prevent exploration movement from also consuming menu keys.

During montage/turn resolution:

- lock command controls;
- retain or intentionally clear focus without allowing duplicate submissions;
- ensure one input produces one stock command invocation.

On battle completion/removal:

- remove battle widgets once;
- clear stale focus;
- return input ownership to the resumed Quill dialogue when one is active, otherwise to exploration;
- restore cursor visibility according to the destination state rather than an assumed global default.

## Workstream D — Quill dialogue visibility

`UMelodiaNarrativeSubsystem::HandleQuillScriptPlay` now emits:

```text
MELUSINA_LOOP_QUILL_PLAY interpreter=<name> dialog=<name> in_viewport=<true|false>
```

Use this as a diagnostic boundary.

### Verification sequence

1. Interact with the intended NPC.
2. Confirm a Quill asset starts and the log contains `MELUSINA_LOOP_QUILL_PLAY`.
3. If no log appears, fix the NPC/interactable script-start wiring; do not modify dialogue rendering yet.
4. If `dialog=None`, inspect the Quill asset/settings for a missing `DialogBoxClass` or disabled managed-dialogue behavior.
5. If a dialog exists but is not visible, inspect its Blueprint `Play(Speaker, Text, Tags)` override.
6. In `Play()`:
   - populate speaker and text first;
   - call `AddToViewportAtLayer()` when not attached;
   - set visibility to Visible;
   - set focus to the advance control;
   - expose an actual clickable advance button.
7. For choices, confirm the configured selection widget creates focusable/clickable option buttons and routes selection through Quill's `OptionSelected` path.

Do not force `ShowDialogBox()`, `Show()`, or `ShowMouseCursor()` from `OnScriptPlay`. At that point the first statement has not executed; forced presentation can show empty UI, override authored script settings, or schedule callbacks beyond immediate script teardown.

## Workstream E — Dialogue/battle round trip

Use one disposable script fixture:

1. Visible pre-battle line.
2. At least two selectable choices.
3. `melodia:battle:<EncounterId>` notification.
4. One post-victory line.
5. One post-defeat/flee branch or acknowledgement.
6. End cleanly.

Verify the log sequence:

- `MELUSINA_LOOP_QUILL_PLAY`
- `MELUSINA_LOOP_QUILL_NOTIFY`
- battle adapter entered/started encounter
- `MELUSINA_LOOP_BATTLE_COMPLETED` or `MELUSINA_LOOP_BATTLE_ABORTED`
- `MELUSINA_LOOP_QUILL_RESTORE`
- `MELUSINA_LOOP_QUILL_NEXT`

Each terminal battle path must resume the interpreter once. Duplicate callbacks must be rejected without advancing dialogue twice.

## Acceptance matrix

| Case | Expected result |
|---|---|
| Mouse clicks Attack | Stock Attack path invoked once |
| J pressed | Same stock Attack path invoked once |
| Mouse clicks Skill | Skill submenu opens and focus moves predictably |
| K pressed | Same skill submenu behavior |
| Escape from submenu | Returns to prior command and restores focus |
| WASD/arrows | Move UI focus without moving exploration pawn |
| Dialogue starts | Speaker/text visible; advance control focused/clickable |
| Choice appears | Mouse and keyboard select exactly one option |
| Battle starts from Quill | Dialogue pauses; exactly one encounter starts |
| Victory | Quill resumes once on victory branch |
| Defeat | Quill resumes once on defeat branch |
| Flee | Quill resumes once on flee branch |
| Missing/duplicate encounter actor | Request fails closed and narrative recovers visibly |
| Script ends immediately | No delayed widget callback or stale UI |
| Cursor-hidden authored script | Project integration does not override its policy |

## Validation commands

With Unreal Editor closed:

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" `
  BS_GodFileEditor Win64 Development `
  "C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" `
  -WaitMutex -NoHotReloadFromIDE -NoUBA
```

After Blueprint edits:

1. Compile and save every touched Blueprint.
2. Run the disposable PIE dialogue/battle fixture.
3. Verify the expected log sequence and absence of duplicate UI.
4. Run targeted automation for `Melodia.CoreRules.Rhythm` as a regression check.
5. Build a Development package only after PIE passes.

## Out of scope

- Replacing JRPG combat authority with MelodiaCore.
- Rewriting turn scheduling, damage, skill resources, quests, inventory, or saves.
- Editing both duplicate JRPG roots.
- Mobile/touch controls.
- Broad UI art redesign before behavior is verified.
- Global mouse-to-confirm mappings.
