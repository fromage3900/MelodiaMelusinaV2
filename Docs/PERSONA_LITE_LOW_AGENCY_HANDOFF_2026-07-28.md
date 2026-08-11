# Persona-lite Lower-Agency Execution Handoff

**Date:** 2026-07-28  
**Purpose:** deterministic continuation guide for models that should execute narrow tasks without rediscovering architecture or expanding scope  
**Project:** `C:\EnvironmentPortfolio\BS_GodFile`

## Read order

1. This file.
2. `Docs/MELODIA_SOLO_GAMEPLAY_CONSTITUTION_2026-07-27.md` for product scope.
3. `Docs/JRPG_SAVE_RUNTIME_CHAIN_AUDIT_2026-07-28.md` for evidence gates.
4. `Docs/JRPG_UI_QUILL_NEXT_IMPLEMENTATION_2026-07-28.md` only when working on active battle/dialogue UI.
5. `_SESSION_HANDOFF.md` for detailed history and current caveats.

Do not treat older roguelike, ACFU, MelodiaCore battle, or recursive-agent plans as active production instructions.

## Non-negotiable authority boundary

| Concern | Sole authority | Adapter/presentation role only |
|---|---|---|
| Combat, turns, damage, skills | stock `/Game/TurnBasedJRPGTemplate` | Melodia visuals and typed requests/results |
| Party, inventory, equipment, quests | stock JRPG controller/data | `UMelodiaPersonaSubsystem` resolves stable IDs and calls stock APIs |
| Canonical save/load | JRPG GameInstance and `BP_JRPGSaveGame` | versioned Melodia narrative record embedded in the JRPG transaction |
| Dialogue and choices | QuillScript | `UMelodiaNarrativeSubsystem` validates allowlisted intents and resumes Quill |
| Exploration HUD | active stock `BP_ExploreUI` | one Persona marker panel inside it |

Never create a second battle system, inventory, quest manager, HUD root, dialogue system, or canonical save slot.

## Completed work — do not redo

- Main Menu New Game is deterministically bound through `AOrreryMainMenuGameMode` and rebuilt.
- Persona content asset exists at `/Game/MelodiaIntegration/Config/DA_MelodiaPersonaContent`:
  - 4 abilities;
  - 3 equipment definitions;
  - 3 sequential quests;
  - 4 minimap markers.
- Active Melusina unit is `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation`.
- Its `battleSkills` map is:
  - `BP_FocusAttack` -> level 1;
  - `BP_Thunderbolt` -> level 2;
  - `BP_BasicHeal` -> level 2;
  - `BP_MeteorStorm` -> level 4.
- Persona equipment mappings are:
  - `melodia_tuning_fork` -> `BP_Rod`;
  - `melodia_dreamweave_shawl` -> `BP_LeatherArmor`;
  - `melodia_star_charm` -> `BP_LeatherBoots`.
- `UMelodiaPersonaSubsystem` calls stock `AddEquipmentToInventory` and `WearEquipmentOnUnit` when `BP_JRPGPlayerController` is active.
- Active `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ExploreUI` contains one `MelodiaMinimapPanel`.
- Petal Priestess and Star Weaver markers are always visible. Rhythm Echo and Path Forward begin collapsed and refresh from quest state.
- ZenForest NPCs have exact identity tags plus `MelodiaQuestNPC`; their existing interaction component routes to the corresponding Persona quest notification.
- Both `UnrealEditor-BS_GodFile.dll` and `UnrealEditor-MelodiaCore.dll` linked after these changes.
- Focused asset validation passed.
- PIE smoke `pie_smoke_2_163720` passed with quest 1 activation/completion, quest 2 activation, gated encounter marker visibility, and accepted equipment request. It recorded no Blueprint runtime error, Accessed None, traceback, or equipment-resolution warning.

## Important caveat

`/Game/ZenForestTest` currently runs `MelodiaSmokeCharacter` with a plain `PlayerController`. Therefore, direct readback of the stock controller's `equipment` property is unavailable on that map. Do not “fix” this by adding another inventory or spawning a controller just for storage. Prove equipment state on the route where the stock JRPG controller is naturally active.

Persona social stats and active quest acceptance are transient. Completion flags/reward consumption use the narrative record, but full Persona state persistence through `BP_JRPGSaveGame` is not proven. Continue and Load Game must remain fail-closed.

## NOW / NEXT / LATER

### NOW — one task

Prove one canonical `BP_JRPGSaveGame` process-restart round trip containing one allowlisted narrative flag and one consumed reward, with no duplicate application.

Binary acceptance gate:

1. Use a disposable canonical JRPG slot.
2. Save outside battle.
3. Exit Unreal completely.
4. Relaunch and load the same slot.
5. Confirm the flag restored.
6. Confirm the reward remains consumed/applied exactly once.
7. Record active GameInstance, SaveGame class, slot name, and logs.

If this cannot be proven, document the exact missing call or class and stop. Do not create a replacement save system.

### NEXT — at most three tasks

1. Run Victory, Defeat, Fled, and unavailable through Quill; prove each restores/advances exactly once.
2. Identify the runtime battle widget package path and update only that root for keyboard/mouse focus and clickable commands.
3. Isolate the cook `UnrealNames.cpp` long-string assertion and repair the missing `Morning_RoomShell` validator contract.

### LATER

- broader combat options;
- outfit expansion;
- social-stat persistence after the canonical schema is proven;
- presentation polish after behavior gates pass;
- packaging certification after PIE result and save matrices pass.

## Exact build and validation commands

Use PowerShell on Windows. Close Unreal Editor before native builds.

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" `
  BS_GodFileEditor Win64 Development `
  -Project="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" `
  -WaitMutex -NoHotReloadFromIDE
```

Healthy Git access:

```powershell
$env:GIT_DIR='C:\EnvironmentPortfolio\.repo_recovery_20260727\.git'
$env:GIT_WORK_TREE='C:\EnvironmentPortfolio\BS_GodFile'
git status --short
git diff --check -- <only-the-files-you-changed>
```

Do not use `C:\EnvironmentPortfolio\BS_GodFile\.git`; it remains corrupt. Do not commit or push unless the user explicitly requests it. GitHub LFS budget currently blocks the recovery-branch push.

Focused Persona validation scripts:

- `Content/Python/author_melodia_persona_foundation.py`
- `Content/Python/setup_melodia_npc_placeholders.py`
- `Content/Python/verify_melodia_npc_placeholders.py`
- `Content/Python/apply_persona_minimap_ui.py`
- `Content/Python/validate_persona_live_wiring.py`
- `Content/Python/persona_lite_final_pie_probe.py`

Do not rerun authoring scripts merely to re-prove closed work. Run them only when their owned content intentionally changes.

## Do-not-touch boundaries

- Do not read or edit `Source/BS_GodFile/MelodiaIntegration/MelodiaHairComponent.cpp` for Persona/JRPG work.
- Do not modify environment geometry, materials, lighting, PCG, landscape, or art while closing gameplay gates.
- Do not edit `/Game/_ThirdParty/TurnBasedJRPGTemplate` in parallel with the active `/Game/TurnBasedJRPGTemplate` root.
- Do not globally bind left mouse to menu confirm.
- Do not enable Continue or Load Game before process-restart save proof.
- Do not claim packaged readiness: the known cook assertion remains.
- Do not duplicate the existing GameFeatureData rule; the startup diagnostic persists despite the visible rule.
- Do not use broad `CompileAllBlueprints` as this slice's acceptance gate; the legacy baseline contains unrelated errors.

## Required closeout format

Every lower-agency work pass must end with:

```text
Task attempted:
Exact files/assets changed:
Authority preserved:
Validation run:
Observed result:
Unproven or blocked:
Single next action:
Do not touch:
```

Never report “complete” from a successful command alone. Read back the requested property, runtime state, asset path, or persisted value that constitutes the acceptance gate.
