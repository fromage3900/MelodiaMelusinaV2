# Next agents — parallel workstreams (2026-08-13 closeout)

**Read this first.** Supersedes stale P1s in `Saved/Audit/melusina_aaa_commit_review_2026-08-13.md` and the ~15:20 `_SESSION_HANDOFF.md` block that said hair apply never ran.

**Repo:** `C:\EnvironmentPortfolio\BS_GodFile` → remote `MelodiaMelusinaV2` · branch `feature/repo-lockin-20260813`. Owner asked to **push** this lock-in branch (no force).  
**Website is a sibling tree:** `C:\EnvironmentPortfolio\my-site-clean`. Do not mix website commits into this repo. Cam_Beauty plate lives there: `generated/melusina_cam_beauty_nikki_2026-08-13.png`.

Locks still hold: [Rhythm WORKED](RHYTHM_GAME_LOCKED_2026-08-12.md) · [Quill WORKED](QUILLSCRIPT_LOCKED_2026-08-12.md). Do not reopen highway/Quill as P0.

---

## Hard rules (every lane)

1. **One Unreal Editor. One Blender.** Never launch a second of either. Never trust a PID in a doc — run `Get-Process UnrealEditor` / `Get-Process blender` yourself.
2. **Do not start Flip. Do not rebake. Do not save v22** unless the owner sets `MELODIA_ALLOW_STAGE_SAVE=1` and asks.
3. **Rhythm + Quill are LOCKED.** Scan-only. No highway graph edits. No Quill widget graphs.
4. **Done = named evidence** under `Saved/Audit/` (local, gitignored) plus a note on this file or `_SESSION_HANDOFF.md`. Prose “done” is not done.
5. Claim one workstream. Independent streams may run in parallel **except** they must not share the editor. If the editor is held, take a no-editor stream (5, 6, 7 docs) or wait.

---

## What is already true (do not re-hunt)

| Fact | State | Evidence |
|------|--------|----------|
| **Hair is water** | Flip cine Geometry Cache + Niagara drip on `head_x` with **inverse bind**. SK hair is fallback, `hidden_in_game`. | Live `BP_Melusina` (`WaterHairFlipCache` sibling on `CharacterMesh0`, socket `head_x`, inverse ≈ `(0, 144.23, -15.90)` + `WaterHairDripFX`). Script: `Content/Python/apply_melusina_aaa_hair_today.py`. |
| Review P1 “apply never ran” | **STALE.** Product landed in the open editor and was saved. | Owner + BP save. Missing `Saved/Audit/melusina_aaa_hair_today.json` does not mean it failed. |
| GC is a **sibling component** | Not stuffed into `UMelodiaHairComponent` (that class is skeletal). | `import_hair_flip_geometry_cache.py` docstring + apply script. |
| Attach API | UE 5.8: `AnimPoseSpaces.WORLD` for composed bind; `k2_attach_to` (no `attach_socket_name` editor property). | `apply_melusina_aaa_hair_today.py` |
| **Idle** | `BS_Melusina_Locomotion` speed **0** = `A_Melusina_Idle_Mocap_RootX`. Walk 180 / run 420 / sprint 630 untouched. | Editor save. `Saved/Audit/melusina_idle_restore_mocap_2026-08-13.md` |
| Blender idle | On disk only: `A_BL_Melusina_Idle_Loop` from `Exports/MelusinaAnim/A_BL_Melusina_Idle_Loop_cm.fbx`. **Do not re-wire.** Gate `MELUSINA_WIRE_BLENDER_IDLE` stays off. | `import_blender_melusina_idle.py` |
| **Menu fonts** | Live `/Game/Melodia/UI/WBP_MainMenu`. Composite **UFont** `F_Melodia_UI` with Regular/Bold aliases → Inline `F_Syne`. All **12** TextBlocks use that UFont. FontFaces are **not** assignable to `TextBlock.Font`. | `Saved/Audit/wbp_main_menu_fonts_2026-08-13.md` (Saved/ is hook-blocked; facts copied below). |
| v22 blend | Saved ~16:36 ET, dirty **false**. Do not commit the ~2.38 GB `.blend`, sidecar, 209 MB `.abc`, or Flip `.bobj`. | Disk on **G:** only. |
| Nikki / Genshin maps | FACE/BODY landed in Blender: custom normals, vertex `Col`, Light Map G, UV1. Not on Flip / Hair PRO. Plate reads **bald** (cache below scalp) — do not rebake. | [`NIKKI_GENSHIN_BLENDER_2026-08-13.md`](NIKKI_GENSHIN_BLENDER_2026-08-13.md) |
| Census | 226 WidgetBlueprints indexed 2026-08-13. | `Saved/Audit/wbp_game_sections_scan_2026-08-13.md` |

---

## PARALLEL workstreams

Pick **one**. Streams 1–4 need the single editor (serialize). Streams 5–7 can run without Unreal/Blender.

### 1. PIE idle proof — **samples confirmed; PIE not run**

**Status 2026-08-13:** blendspace speed 0 is mocap; ABP is `ABP_Melusina_Current`. PIE skipped (live map was MainMenu). See [`REMAINING_TASKS_EXECUTE_2026-08-13.md`](REMAINING_TASKS_EXECUTE_2026-08-13.md).

**Goal:** Confirm standstill is the mocap idle (not collapsed).  
**How:** PIE or viewport on the live pawn. Speed 0 must look like `A_Melusina_Idle_Mocap_RootX`.  
**If collapsed:** **Stop and report.** Do not re-wire Blender idle. Do not import FBX. Do not set `MELUSINA_WIRE_BLENDER_IDLE`.  
**Deliverable:** `Saved/Audit/pie_idle_proof_2026-08-14.md` (pass/fail + screenshot or log line).  
**Do not:** touch walk/run/sprint samples; touch Rhythm/Quill.

### 2. Morning hair presence — **BP_Melusina CDO OK; JRPG pawn gap**

**Status 2026-08-13:** `BP_Melusina` has GC + Niagara on `head_x`. Morning has **no placed Melusina**; GameMode pawn is `BP_MelusinaJRPGCharacter` **without** GC (SK hair `hidden_in_game=false`). Do not copy the product onto the JRPG pawn unless the owner asks.

**Goal:** `L_MelusinaMorning` shows `SK_Melusina` **and** the water-hair product (GC + Niagara) in view. GC is already on `BP_Melusina`; this is a **level presence** check, not a re-apply.  
**How:** Load `/Game/Melodia/Levels/Opening/L_MelusinaMorning` in the **already-open** editor. Confirm `WaterHairFlipCache` + `WaterHairDripFX` visible; SK hair hidden in-game.  
**Do not:** load `L_KaleidoNave` unless the owner asks. Do not run Flip. Do not re-import ABC.  
**Deliverable:** `Saved/Audit/morning_hair_presence_<stamp>.md`.  
**If GC missing:** report; only then consider re-running `apply_melusina_aaa_hair_today.py` in the same editor (never a second editor).

### 3. Niagara drip rates — **still blocked** (emitter stack)

**Status 2026-08-13:** MI scalars already `subtle_drip`. `emitter_handles` / `EmitterHandles` / NiagaraEditorLibrary absent or protected. User params have no `SpawnRate`. Do not use Water V10 as hair solver.

**Goal:** Splash/drip spawn looks right on the live hair.  
**Known constraint:** `NiagaraSystem.emitter_handles` **failed as a public API on UE 5.8** in this project. Material-instance scalars **did** set. Prefer MI / user-parameter scalars on `/Game/Melodia/VFX/Melusina_WaterFX` (`set_melusina_waterfx.apply_preset("subtle_drip")`) over emitter-handle walks.  
**Do not:** treat Water (Advance) / Flip domain as a hair solver. Do not restore `Water (Advance).001` here. Do not start Flip.  
**Deliverable:** audit of what spawned vs what you changed (preset name + any MI scalar).  
**Code:** `Content/Python/set_melusina_waterfx.py` — if `emitter_handles` still throws, document and use the MI path.

### 4. MelodiaWardrobe plugin — **isolated** (`Enabled: false`, uncommitted)

**Status 2026-08-13:** plugin not mounted; no load-failure modal; Monolith answers. Leave the `BS_GodFile.uproject` hunk **uncommitted**.

**Goal:** Editor boots without a blocking “plugin failed to load” modal.  
**Last boot:** `Plugin 'MelodiaWardrobe' failed to load because module 'MelodiaWardrobe' could not be initialized successfully after it was loaded.` That modal took down Monolith `:9316` / UnrealMCP / Python-remote until dismissed.  
**Working tree:** `Plugins/MelodiaWardrobe/` is **untracked WIP**. `BS_GodFile.uproject` has a dirty `MelodiaWardrobe` `Enabled: false` hunk — **leave it uncommitted** unless the owner wants that plugin state in git.  
**How:** Isolate/disable so UI and Python-remote work. Do not expand wardrobe features. Do not block streams 1–3 or 5.  
**Deliverable:** boot log excerpt + whether Monolith `:9316` answers.

### 5. WBP dead-HUD cleanup — **partial (committed)** — NOT rhythm highway

**Status 2026-08-13:** `/Game/Blueprints/WBP_RhythmHUD` reparented to `UMelodiaRhythmHUDWidget`. Dead `BP_MelodiaGameMode` `HUDWidgetClass` / `battle_results_widget_class` unhooked. Empty templates **not** deleted (Decision 049 / 020). Highway untouched.

**Goal:** Remove or quarantine remaining dead HUD copies. **Do not touch** live `/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway`.  
**Live menu fonts are already fixed** — do not redo `WBP_MainMenu` fonts.

Actionable (from census, 226 WBPs):

| Target | Why | Verdict |
|--------|-----|---------|
| `/Game/Melodia/Blueprints/WBP_RhythmHUD` | Parents `UMelodiaRhythmHUDWidget`, **zero** referencers | Duplicate; not live |
| `/Game/Blueprints/WBP_RhythmHUD` | Parents **dead module** `MelodiaMelusina_PROD.MelodiaRhythmHUDWidget`; only `BP_RhythmHUD` | Duplicate; not live |
| `WBP_Battle_Rhythm` / `WBP_Battle_Results` | Hang off dead `BP_MelodiaGameMode`, not `BP_MelodiaJRPGGameMode` | Not on live GameMode |
| `WBP_Battle_Mobile` | Orphan; empty tree; `BindWidgetOptional` names missing | Empty |
| `WBP_GradePop` | Orphan; empty tree | Empty |
| `WBP_SaveLoad` | Orphan; empty; superseded by `WBP_SaveLoadPanel` | Empty |

**Do not delete on census alone** (Decision 049 / 020 — C++ / umap soft refs hide from registry). Propose a delete list with owner sign-off.  
**Full census:** `Saved/Audit/wbp_game_sections_scan_2026-08-13.md` (local). Counts: 104 LIVE, 6 LIVE-via-C++/config, 77 UNANCHORED, 39 ORPHAN, 75 duplicate short names. Compile errors: 0.

### 6. Website / recruiter sendoff — **sibling agent only**

**Owner of this lane:** whoever is on `C:\EnvironmentPortfolio\my-site-clean`. **This Unreal repo is not the site.**

Facts that agent **must not get wrong**:

- **Hair is water.** Gameplay/product = Flip cine Geometry Cache + Niagara on `head_x` inverse bind. `SK_MelusinaHair` is hidden fallback, not the live silhouette. Older site copy that says “gameplay hair = SK_MelusinaHair” is **stale**.
- **Idle is mocap** (`A_Melusina_Idle_Mocap_RootX`). Blender `A_BL_*` is on disk only; do not advertise it as live.
- **Fonts:** assign `F_Melodia_UI` (**UFont** composite). `F_Syne` / `F_InstrumentSerif` are **UFontFace** and will not render on `TextBlock.Font`.
- SSOT checkout: `my-site-clean`. Do not commit site files into `BS_GodFile`. Do not treat `my-site-deploy/` as truth. Token linter (`npm run verify:all`) is pre-existing FAIL; facts/asset scripts have passed.
- Site git is **not** this branch. Do not force-push. Do not unrelated-history merge without owner.

### 7. Deferred (do not start unless owner names it)

- Faceit drivers  
- Save `L_KaleidoNave` (Cathedral + V2-test review strips still unsaved if the editor still has that map dirty)  
- Face SDF full angular bake (P1; UV1 copy only so far)  
- Flip cache-below-scalp (plate reads bald) — **do not rebake** unless owner names it

**Landed in Blender 2026-08-13 ~16:36 (do not redo):** Nikki Lights / `beauty_clean`; `Water (Advance).001` restore without `nikki_mat_apply`; Genshin FACE/BODY custom normals + Col + Light Map G + UV1. See [`NIKKI_GENSHIN_BLENDER_2026-08-13.md`](NIKKI_GENSHIN_BLENDER_2026-08-13.md).

---

## WBP_MainMenu fonts (tracked facts; Saved/ audit is hook-blocked)

Live widget: `/Game/Melodia/UI/WBP_MainMenu` via `AOrreryMainMenuGameMode`. Boot map `L_MelodiaMainMenu`.

`F_Melodia_UI` faces: `Syne` / `InstrumentSerif` / `InstrumentSerifItalic` / `TwinkleStar`, plus **Regular** and **Bold** aliases both → Inline `F_Syne`.

| Widget | Typeface | Size |
|--------|----------|-----:|
| TitleText | Syne | 68 |
| MenuKicker / MenuSectionLabel / MenuWorldKicker / MenuCornerNote | Syne | 16 / 14 / 14 / 14 |
| BtnLabel_Continue / NewGame / LoadGame / Settings | Syne | 19 |
| MenuSubtitle / MenuWorldTitle | InstrumentSerif | 21 |
| SaveStateText | InstrumentSerif | 16 |

All 12 FontObject paths: `/Game/Melodia/UI/Fonts/F_Melodia_UI`. Compiled clean. Rhythm/Quill not edited.

---

## Git health (this closeout)

- **`a6bbb55d`**: water-hair apply script, `BP_Melusina`, blendspace, idle unit-guard, `_cm` FBX. Do not amend.
- **`cb7b6550`**: live menu font uassets + this handoff's first closeout. Do not amend.
- **`62d74d81`**: CREDITS + SOURCES_MATRIX + credits_gate. Do not amend.
- This commit: HUD unhooks (`WBP_RhythmHUD` reparent, `BP_MelodiaGameMode` widget refs cleared), remaining-tasks + idle-restore + Nikki/Genshin notes under `Docs/Handoffs/` (`Saved/` is hook-blocked), Cascadeur anim-only import fix. Owner asked to **push** (no force).
- **Left uncommitted on purpose:** GN (`deploy/surreal_arch/**`), `Plugins/MelodiaWardrobe/**`, wardrobe shirt/MI dirties, `l_melodia_dreamstate..umap`, 209 MB ABC, v22 blend + sidecar, Cam_Beauty PNG (sibling `my-site-clean`), `BS_GodFile.uproject` wardrobe plugin hunk, import-pipeline Scripts/.

---

## Contended resources

| Resource | Concurrency |
|----------|-------------|
| UnrealEditor + Monolith `:9316` | **ONE** lane (streams 1–4) |
| Blender 5.2 / v22 | **Do not open** this round |
| `my-site-clean` | Stream 6 only |
| Docs / WBP census / plugin source | Streams 5, 4 (source-only), 7 |
