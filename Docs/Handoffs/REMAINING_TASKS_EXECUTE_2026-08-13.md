# Remaining tasks execute — 2026-08-13

Git-tracked copy of `Saved/Audit/remaining_tasks_execute_2026-08-13.md` (`Saved/` is hook-blocked). PIDs omitted on purpose — run `Get-Process UnrealEditor` yourself.

**Editor:** one already-open UnrealEditor, Monolith `:9316`. Did not launch a second editor. Did not touch Blender. Rhythm highway + Quill not edited.

**Start map:** `/Game/Melodia/Levels/Menu/L_MelodiaMainMenu` (not dirty). End map: same. Dirty packages at start: none.

---

## Remaining inventory (from handoff TOP)

| # | Lane | Status after this pass |
|---|------|------------------------|
| 1 | PIE idle proof | **Samples + anim class confirmed. PIE not run.** |
| 2 | Morning hair presence | **BP_Melusina CDO product OK. Morning has no placed Melusina; live pawn is JRPG character without GC.** |
| 3 | Niagara drip spawn rates | **Still blocked** on emitter stack. MI scalars already subtle_drip. |
| 4 | MelodiaWardrobe plugin | **Isolated.** `Enabled: false`, not mounted this boot. Monolith answers. |
| 5 | WBP dead-HUD cleanup | **Partial.** Reparented dead-module `WBP_RhythmHUD`. Unhooked dead GameMode widget classes. Empty templates kept. |
| 6 | Website / recruiter | **Skipped** (sibling `my-site-clean`). |
| 7 | Deferred (Nikki/Genshin, Faceit, beauty_clean, Water Advance.001, KaleidoNave save) | **Skipped at this pass** (owner-named only). Nikki/Genshin Blender maps landed later the same hour — see [`NIKKI_GENSHIN_BLENDER_2026-08-13.md`](NIKKI_GENSHIN_BLENDER_2026-08-13.md). |
| — | GN factories, giant ABC/blend commits, force-push | **Skipped.** |

---

## A. PIE / viewport idle proof

**PIE not run.** Live map was `L_MelodiaMainMenu` (boot menu). Starting PIE would have played the menu, not a Melusina standstill. After a temporary Morning load, PIE was still skipped so the owner’s menu session was not stomped.

Blendspace `/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion`:

| Speed | Animation |
|------:|-----------|
| 0 | `A_Melusina_Idle_Mocap_RootX` |
| 180 | `A_Melusina_Walk_Mocap_RootX` |
| 420 | `A_Melusina_Run_Mocap_RootX` |
| 630 | `A_Melusina_Sprint_Mocap_RootX` |

`CharacterMesh0.anim_class` on both `BP_Melusina` and `BP_MelusinaJRPGCharacter` = `ABP_Melusina_Current`. Blender idle not re-wired. `MELUSINA_WIRE_BLENDER_IDLE` not set.

---

## B. `L_MelusinaMorning` hair product

Dirty packages were empty (not KaleidoNave). Loaded `/Game/Melodia/Levels/Opening/L_MelusinaMorning`, inspected, restored MainMenu.

**Placed actors:** no Melusina pawn in the level (only `CAM_MelusinaMorning_Portfolio` matched the name filter). Morning’s GameMode pawn is `BP_MelusinaJRPGCharacter`, not `BP_Melusina`.

### `BP_Melusina` CDO (product — pass)

| Component | Result |
|-----------|--------|
| `CharacterMesh0` | `SK_Melusina` + `ABP_Melusina_Current` |
| `WaterHairFlipCache` | `GC_MelusinaHairFlip_v22`, socket `head_x`, relative ≈ `(0, 144.229, -15.897)` inverse bind |
| `WaterHairDripFX` | Niagara `/Game/Melodia/VFX/Melusina_WaterFX`, socket `head_x`, identity |
| `WaterHairMesh` | `SK_MelusinaHair`, **`hidden_in_game=true`** |

Did **not** re-run `apply_melusina_aaa_hair_today.py` (GC already on `BP_Melusina`).

### Live Morning pawn `BP_MelusinaJRPGCharacter` (gap)

| Component | Result |
|-----------|--------|
| `CharacterMesh0` | `SK_Melusina` + `ABP_Melusina_Current` |
| `WaterHairFlipCache` | **missing** |
| `WaterHairDripFX` | **missing** |
| `WaterHairMesh` | `MelodiaHairComponent` / `SK_MelusinaHair`, **`hidden_in_game=false`** |

Morning PIE would show SK hair, not Flip GC. Copying the product onto the JRPG pawn was not done (apply script targets `BP_Melusina` only; owner call).

---

## C. Niagara `subtle_drip` emitter rates

MI `/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair` already matches preset: HairDripIntensity 0.35, SplashForce 0.25, WaterOpacity 0.72, WaterRoughness 0.28, MagicalIntensity 0.15, CausticIntensity 0.08, DripSpeed 0.20, DripLength 0.08.

**5.8 path tried (not `emitter_handles`):**

- `NiagaraSystem.emitter_handles` — missing; `EmitterHandles` **protected**
- `get_emitter_handles()` — missing
- `NiagaraEditorLibrary` / `NiagaraToolset_System` / `NiagaraEditorSubsystem` — **absent**
- `NiagaraFunctionLibrary.get_all_user_parameters(system)` — **works**
- User params: AudioHigh/Low/Mid, BeatPulse, DreamVisibility, GlobalReactivity, ImpactPosition, Intensity, PlayerProximity, Quantum*, Reaction*, RhythmPulse, Seed, TargetPosition, WindVector. **No `SpawnRate`.**
- `NiagaraComponent.set_variable_float("SpawnRate" | "User.SpawnRate" | "WaterSplashEmitter.SpawnRate")` — calls succeed as instance overrides, do not edit the emitter stack
- `NiagaraPythonModule.acquire_editor_element_handle` — routes to `EngineElementsLibrary` object handles, not emitters

**Still blocked:** WaterSplashEmitter spawn rate lives in the Niagara emitter stack, not exposed user params. Do not use Niagara 3D FLIP / Water V10 as hair solver.

---

## D. MelodiaWardrobe plugin

**This boot (~16:04 ET):** plugin is **not mounted**. `BS_GodFile.uproject` has `"Name": "MelodiaWardrobe", "Enabled": false`. `PluginBlueprintLibrary.is_plugin_mounted("MelodiaWardrobe")` = false. Class `/Script/MelodiaWardrobe.MelodiaWardrobeComponent` missing. Current `Saved/Logs/BS_GodFile.log` has **no** wardrobe load-failure modal. Monolith `:9316` answers.

**Last failing boot** (`Saved/Logs/BS_GodFile-backup-2026.08.13-19.14.44.log`):

```
InternalLoadLibrary: 'MelodiaWardrobe' (.../UnrealEditor-MelodiaWardrobe.dll)
Plugin 'MelodiaWardrobe' failed to load because module 'MelodiaWardrobe' could not be initialized successfully after it was loaded.
```

Earlier same day: unity excluded the `.cpp` files → LNK2001 on component/subsystem ctors; `IMPLEMENT_MODULE` was added later; DLL then loaded but **InitializeModule still failed**. Likely cause (not rewritten): plugin `LoadingPhase: Default` depends on game module `BS_GodFile` (`EMelodiaWardrobeSlot` / `UMelodiaNarrativeSubsystem`) plus `MelodiaCore` wallet. Game-module types/subsystems are not a safe plugin init dependency.

**Safe fix applied:** leave disabled. Do not enable. Do not rewrite. Leave the uproject hunk uncommitted unless the owner wants plugin state in git.

---

## E. WBP dead-HUD cleanup (not rhythm highway)

`WBP_MelodiaRhythmHighway` status remained `BS_UP_TO_DATE`. Quill widgets not opened. `WBP_MainMenu` fonts not redone.

| Action | Result |
|--------|--------|
| Reparent `/Game/Blueprints/WBP_RhythmHUD` → `/Script/MelodiaCore.MelodiaRhythmHUDWidget` | **Saved.** Status `BS_UP_TO_DATE_WITH_WARNINGS` → **`BS_UP_TO_DATE`**. |
| Unhook dead `/Game/Melodia/_PROJECT/BP_MelodiaGameMode` `HUDWidgetClass` (`WBP_Battle_Rhythm`) and `battle_results_widget_class` (`WBP_Battle_Results`) | **Saved** after `attrib -R` (file was ReadOnly). |
| `/Game/Melodia/Blueprints/WBP_RhythmHUD` (zero referencers) | Left as template. |
| Empty `WBP_Battle_Mobile` / `WBP_GradePop` / `WBP_SaveLoad` | **Not deleted** (Decision 049 / 020). Owner sign-off still required for deletes. |

UE 5.8 Python does not expose `WidgetBlueprint.parent_class`; parent was taken from the 2026-08-13 census (`MelodiaMelusina_PROD.MelodiaRhythmHUDWidget` on `/Game/Blueprints/WBP_RhythmHUD`).

---

## Skipped (and why)

- Website / recruiter sendoff — sibling tree `my-site-clean`.
- GN factories, ABC/blend giant commits, force-push — owner skip list.
- Deferred stream 7 at this pass — owner must name. Nikki/Genshin Blender maps landed later (see sibling Blender pass).
- PIE idle visual — would displace MainMenu; samples + ABP confirmed instead.
- Applying water-hair onto `BP_MelusinaJRPGCharacter` — not the apply-script target; report only.
- Deleting empty WBP templates — need owner sign-off.
- Rewriting MelodiaWardrobe C++ — isolate-only.

---

## Files saved / evidence

| File | What |
|------|------|
| `Saved/Audit/remaining_tasks_execute_2026-08-13.md` | Local report (hook-blocked) |
| This file | Git-tracked copy |
| `/Game/Blueprints/WBP_RhythmHUD` | Reparented + compiled + saved |
| `/Game/Melodia/_PROJECT/BP_MelodiaGameMode` | Widget class refs cleared + saved |

Editor left on `L_MelodiaMainMenu`. Dirty packages: none after the GameMode save. Monolith `list_dirty_packages` for Melusina/UI scopes later returned count 0 — disk files only.
