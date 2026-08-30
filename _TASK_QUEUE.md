# Task Queue — Parallel Agent Work

**Purpose:** Single source of truth for what's being worked on, by whom, and what's next.


## Queue — 2026-08-20 (paradigm shift: convergence)

**Read first:** [`../PROJECT.md`](../PROJECT.md) (authority) ·
[`Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`](Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md) (who owns what) ·
[`Docs/ORCHESTRA_CONTRACT_2026-08-20.md`](Docs/ORCHESTRA_CONTRACT_2026-08-20.md) (the seams).

**Never trust a PID written here or anywhere else** — run `Get-Process UnrealEditor`.
`origin` = MelodiaMelusinaV2.

> **Gate status is not maintained here.** Run `python -B Tools/echo_run.py status`.
> The previous block in this spot listed five gates as open; two of them (`rhythm_owner`,
> `rhythm_grade_to_result`) had PASS rows, and it claimed `allowlist_ids` was "certified PASS"
> when that gate **has no ledger row at any status**. See
> `Docs/Plans/SHOREWAKE_TRAVERSAL_PLAN_AND_P0_CLOSEOUT_2026-08-29.md` §1.1 for the two standing
> evidence caveats.
>
> **Genuinely open (no ledger row, ever):** `wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`,
> `music_world_key`. Note that the last two are the **same edge measured twice** — the catalog
> gates `form.first_resonance_echo` (which grants Glide) on flag
> `challenge.first_resonance_echo.completed`, which is what `CommitWorldChallenge` sets when a
> played phrase completes.

> **Materials lane — 2026-08-29 evening (commit `2c201fe3`, 2-hour takeover box).**
> | Item | Status |
> |---|---|
> | Nikki glow wiring on `M_Master_Toon_Landscape_HeightBlend` (`MF_NikkiDreamGrade.Emissive` → `bNikkiFast`-gated Add → `EmissiveColor`) | **Done + saved** (default 593 PS pruned; fast lane 910 PS / 13 samplers clean) |
> | `SK_ShorewakeDress` real material | **Done** — `MI_Melusina_Dress_Shorewake` created + assigned to slot 0; `Material_001` retired |
> | Leviathan/Organ textures (6) | **Done** — imported with correct sRGB/normalmap flags |
> | Leviathan/Organ material instances | **Done** — `MI_SeaAbove_Leviathan_Bone`, `MI_SeaAbove_Organ_Pipe` (Organ Pipe emissive wired) |
> | Landscape master surgery closeout | **Done** — commit `c5e15395` + recipe `06bbbee3` |
> | `SM_Leviathan.obj` / `SM_DrownedOrgan.obj` mesh imports | **Available** — MIs ready and waiting |
> | `MI_Melusina_WaterHair` creation on v7 + `SK_MelusinaHair` 4-slot fix | **Available** — prior doc claim that the MI exists was wrong (deleted from tracking; recreate fresh) |
> | `SK_Melusina_V2_Shirt` outline slot | **Available** — reference wiring on other V2 pieces (`MI_Melusina_Outline_004/_005`) |
> | Ocean visual pass + `DA_Color_AnimeLightBlue`/`DA_Foam_Stylized` + `Toon_Weight` dial | **Available** — owner eyeball task |
> | Starskiff MI family (Hull_Regal, Brass, Cushion, LanternGlass, PlankNail, Wake_Emission) on Universal | **Done 2026-08-29 late** — 25 skiff textures now instanced; masks (patina/jewel/edgewear/damask) unwired pending a mask-input pass |
> | Jellyfish v2 GRAND (Houdini lane) | **Done 2026-08-29 late** — 136 m bell (24 lobes) + 12 × 480 m double-bifurcating 1.5π-twist arms; topology contract verified ×3 poses; FBX + QA renders in `Saved/Audit/sea_above/`; UE import queued |
> | Jellyfish v3 SERAPH (Houdini lane) | **Done 2026-08-29 late** — 190 m dome, 3 golden-ratio floating tiers (Fibonacci lobes 21/13/8), halo ring, 55-filament cilia crown, 13 × 640 m golden-angle arms; zero topology mismatches; FBX + renders; UE import queued |
> | Jellyfish v4 CATHEDRAL (Houdini lane) | **Done 2026-08-29 late** — v3 SERAPH + 8 flying-buttress arches + helix spire + 5 three-stage fountain cascades + 21 drape curtains (94 parts, zero mismatches); FBX + renders; UE import queued |
> | Cloth-mountain terrain generator v0 (Faraway Mother) | **Done 2026-08-29 late** — `build_cloth_mountains.py`: 2 km tile, pleated strata + seam valleys + embroidery path; 148k-pt OBJ + clay renders; v0.1: modulate/warp pleats so strata fade |
> | Five-biome cloth-terrain suite v0.1 (Faraway Mother) | **Done 2026-08-29 late** — commit `c1fc7cda`: Hemlands/PleatedRange/EmbroideredBasin/VeiledMountains/SeamRoad; OBJ + .r16 heightmaps + 10 clay renders; ~4 min full cook |
> | A God That Molts shell kit v0 (Bible #05) | **Done 2026-08-29 late** — `build_molted_god.py`: 4 instars (Settlement 14 m / Cathedral 44 m / Mountain 280 m / FreshMolt 340 m split), golden-ratio tergum bands + golden-angle pores + jagged dorsal fracture; OBJs + renders; v1 next: through-hole pores, membrane interiors, fracture plate kit |
> | Subagent delegation | **Cancelled by owner ("not cycling anything")** — remaining queued work runs in-line; UE import session (jelly FBXs + terrain OBJs) still pending an editor window |
> | Mara Elletra Vell base from Melusina | **Done 2026-08-29 late** — `SK_Mara_Vell_Body` (shared skeleton) + `MI_Mara_Skin_006/007` moonlit retint on Universal, slots 0–2 assigned; gown via Outfit Hub + own outline/eye pass next |
> | P1 arc draft: Mara Elletra Vell + The Faraway Mother | **Draft for owner canon** — `Docs/Plans/P1_MARA_ELLETRA_VELL_AND_THE_FARAWAY_MOTHER_2026-08-29.md` + `specs/progression/melodia_mara_faraway_mother_quest.v1.json` (allowlist quarantined behind owner gate) |
> | Banner/Shroud fabric master (Kelp is an explicit placeholder) | **Available** |
> | Reef/height-blend masters: mirror `M_Master_Toon_Universal`'s Madoka/Itto input wiring | **Available** — owner look decision first |
> | SDF lane consumer decision (`MF_SDF_BandRelief`, `MF_LandscapeStorybookSDF` referenced by zero masters) | **Available** — wire or archive |
> | Research + execution log | `Docs/Research/MATERIAL_TAKEOVER_RESEARCH_2026-08-29.md` (gitignored lane, on disk) |

---

### P0 — The game

| Task | Pri | Status | Agent | Notes |
|---|---|---|---|---|
| ~~Wire `OnPatternCompleted` → narrative notification~~ | P0 | **Superseded — the edge already exists** | — | **This row was wrong on two counts.** (1) The narrative edge is NOT missing: `MelodiaPCGNarrativeChallengeBridgeComponent.cpp:62` binds `OnPatternCompleted` and `:141` calls `CommitWorldChallenge`. Water is not the only consumer. (2) The contract is **8 verbs**, not 7 — `item` was added (`MelodiaNarrativeSubsystem.cpp:1093-1101`: battle, quest, questcomplete, flag, travel, reward, stat, item). **The real blocker was `APCGHeroMusicGraphHost::HandleProgressionEvent` being an empty body** (`Piano/PCGHeroMusic.cpp:634`), so a base host placed in a level could never reach `MarkCompleted()` and never broadcast. Fixed 2026-08-29 with a default completion rule; needs a closed-editor build. Preserve the presentation-only boundary — music opens doors, it never deals damage. |
| Merge `MelodiaJRPGBattleOverlaySubsystem` into `MelodiaUIBridgeSubsystem` | P0 | **Done** | — | `hud_single_writer` certified PASS (2026-08-27 `session-7aa8ad8a`). `UMelodiaUIBridgeSubsystem` is the sole Melodia writer. |
| Shorewake Outfit Transformation (`Cos_ShorewakeDress`) | P0 | **Art done — NOT equippable** | — | ⚠ **`Cos_ShorewakeDress` is not in `DA_MelodiaCosmeticCatalog`** (which holds only the five `*_MelusinaV2` ids), so `EquipCosmetic("Cos_ShorewakeDress")` is rejected at runtime by `MelodiaWardrobeSubsystem.cpp:420-421`. Also **three** `SK_ShorewakeDress` meshes exist with no canonical: `Reef/Meshes/` (its FBX is marked SUPERSEDED by `Reef/IMPORT_QUEUE.md:155`), `Clothes/SK_ShorewakeDress_Magical` (Pass C, merged onto the owner's rigged FBX, 5 morphs — **use this one**), and `ChaosTest/SK_ShorewakeDress_ChaosProxy`. Source USDZ + rigged FBX live in `~/Downloads` and `~/OneDrive/Desktop`, **outside the repo** — not reproducible from a clean clone (mirrored to `G:\BS_GodFile_Mirror\20260830\_external_sources\` 2026-08-29). Original row follows: | 48-panel mesh joined, 3 morphs (`Nikki_Bloom`, `Nikki_Swirl`, `ShimmerWave`), 48 mat slots, PBR textures, Quill quest (`MelodiaQuillShorewake.qsc`), and 5/5 contract tests pass. QA renders in `Saved/Audit/sea_above/renders/skiff/`. |
| Sea Above Level Loop & Enemy Placement | P0 | **Done (Staged & Tested)** | — | `stage_seaabove_level_loop.py` places player, arrival trigger, Starskiff MK2, PCG Arpeggio bridge, `SeaAbove_SmokeBattleEncounter`, and `SeaAbove_Littoral_EnemyPatrol`. 5/5 contract tests pass. |
| Prove the Glide/Dash/Swim capability path end-to-end | P0 | **Available** | — | `wardrobe_gameplay_hook`. The Infinity Nikki pattern is wired (`MelodiaTraversalCapabilityProvider.h:32-38`) and Shorewake quest grant is authored. |
| `rhythm_grade_to_result` — grade changes a JRPG result | P0 | **Available** | — | The seam that defines the game. Rhythm is owner-locked WORKED; the grade→damage edge is unproven in live PIE. |
| Fix `WBP_MelodiaRhythmHighway` lane legend → Q/W/O/P | P0 | **Available** | — | Still shows retired D/F/J/K. Live keys are Q/W/O/P via `BP_BattleUI::OnKeyDown`. Small, visible, unambiguous. |
| `static_gates` — clear baseline drifts | P0 | **Done** | — | PASS 2026-08-29 (`session-e4ee8de9`). Baseline refreshed (16 assets), 55 clean exports, 0 drifted. |
| Bind `BP_BattleController.melodiaBattleUI` / `.MelodiaUI` to the Melodia rhythm-highway HUD | P0 | **Done** | — | Confirmed vestigial pre-bridge variables; `BP_BattleController.battleUI` is correctly linked to `BP_BattleUI_C_0` (`MATCH=True`). |
| Un-abstract `BP_MelodySlimeBattle_Hub` | P0 | **Available** | — | Still an abstract class; the Melody Slime is not battle-triggerable in the hub map until it can be spawned. |
| Re-add `ShowQuestRewards` override (`BP_ItemObtainDialogue`) on `BP_MelodiaJRPGPlayerController` | P0 | **Available** | — | Dropped when the duplicated EventGraph was stripped during the 2026-08-26 reparent fix. |

### P1 — Convergence hygiene

| Task | Pri | Status | Agent | Notes |
|---|---|---|---|---|
| Mark DEAD in-header: `MelodiaRhythmExecutionComponent`, `MelodiaBattleInputComponent` remap, `MelodiaOutfitComponent` | P1 | **Available** | — | Marking only. Deletion is Red-tier and needs owner sign-off. |
| Decide `MelodiaNPRClothingComponent`: merge or dead | P1 | **Blocked — owner** | — | A third outfit-state holder with its own `Get/SetCurrentOutfit`. No external callers found. |
| Establish caller status: `MelodiaBattleResultsWidget`, `MelodiaExplorationHUDWidget` | P1 | **Available** | — | Do not assume dead — two of three assumed-dead MelodiaCore rhythm classes turned out load-bearing. |
| Foundation gates still genuinely open | P1 | **Available** | — | Battle-widget identification, input parity, result matrix, Quill-unavailable load, safe-location routing, interpreter invalidation, mid-battle save lockout, Main Menu wiring, `Morning_RoomShell` validator. See `_VERTICAL_SLICE_SCOPE.md`. |
| Wardrobe importer scripts move behind the C++ API | P1 | **Available** | — | `Content/Python/wire_melusina_wardrobe_*.py` and `import_melusina_wardrobe_contract.py` are authoring tooling, not a runtime authority. |

### P2 — Infrastructure (does not block the game)

> These were P0 in the previous queue. They are real work with real value, and **none of them is
> the game.** They do not gate a single orchestra or shipping gate.

| Task | Pri | Status | Agent | Notes |
|---|---|---|---|---|
| AWS S3 Glacier Deep Archive Backup | P2 | **Blocked — needs `aws login`** | claude | Manifest + runbook ready at [Docs/LFS_COLD_ARCHIVE.md](Docs/LFS_COLD_ARCHIVE.md) with SHA-256 per target. Set A (portfolio stages v16/v17, 3.49 GB) → Glacier IR; Set B (pre-integration backup, 156 MB) → Deep Archive, tarred into one object. Needs an auth code typed into a live terminal. |
| Land the `.gitignore` union | P2 | **Blocked — owner** | sonnet | The 2,243 assets adopted in `309a575d` were force-added; `.gitignore` still excludes them. Union = repo-lockin's version, minus its `.agents/` rule, plus main's root scratch-script block and `Plugins/Claireon/`. **Never-touch file.** |
| Push `main` (28 unpushed) | P2 | **Blocked** | — | Gated on the Glacier archive: local LFS is 11.69 GB against a 10 GiB free tier. |
| AWS S3 Art-Drop Mechanism | P2 | **Available** | — | S3 bucket for the 4.6 GB bulk environment art to replace "ask the owner" onboarding. |
| Setup S3-backed Shared UE DDC | P2 | **Available** | — | So collaborators do not face multi-hour shader compiles. |
| Enable `GitSourceControl` provider | P2 | **Blocked — owner** | — | UE 5.8 ships it; not enabled. This is why 2,224 lockable files have 0 locks. Touches `.uproject` + Config. |
| DDC path is machine-specific (`Config/DefaultEngine.ini:215`) | P2 | **Blocked — owner** | — | Never-touch file. |
| `git lfs prune --recent` | P2 | **Blocked — owner** | — | ~10 GB of the 19 GB local store is orphaned. **Destructive.** |
| Get `Exports/*.blend` out of LFS | P2 | **Available** | — | **63% of all LFS content** (5.6 GB). Regenerable build artefacts, not source. |
| Shrink art-gate baseline: 120 duplicate short names | P2 | **Available** | — | `Tools/art_gates.py --strict`. Makes every short-name-matching audit non-deterministic. |
| Shrink art-gate baseline: 11 WIP masters + 2 `MI_` in `Masters/` | P2 | **Available** | — | Nine landscape variants, four Universal — all loadable and parentable today. |
| `Tools/melodia_asset_passport.py` missing, 3 live importers | P2 | **Available** | — | `melodia_stage_shot.py:398`, `remount_melusina_plates.py:268`, `scan_ornament_fbx_stats.py:116` all ImportError. |
| Run `art_gates.py --live` once | P2 | **Available** | — | Needs the editor. Shader instructions have never been measured against the 150 cap. |
| `recovery/melodia-main-sync-20260811` — 2 commits only on the old repo | P3 | **Available** | — | Cherry-pick onto V2 or abandon. Do not push as-is. |
| `.gitattributes` LFS gaps: `.bmp`, `.pyd`, `.lib` | P3 | **Blocked — owner** | — | Never-touch file. 3 `.bmp` already committed raw (~200 KB). |
| Nested `.git_disabled` pack committed | P3 | **Available** | — | See `Docs/Reports/LFS_HEALTH_2026-08-13.md`. |
| Decide `l_melodia_dreamstate..umap` (double-dot typo) | P3 | **Blocked — owner** | — | Rename or delete; not touching without assent. |
| **Perforce decision** | P3 | **Blocked — owner** | — | `Docs/PERFORCE_MIGRATION_PLAN_2026-08-13.md`. The three gates it waited on are now closed, so this is purely an owner call. |

### Done — do not reopen

| Task | Closed | Evidence |
|---|---|---|
| `runtime` gate | 2026-08-13 | Ledger PASS, owner-verified real keys (`owner-realkey-20260813`) |
| `save_load` gate | 2026-08-14 | Ledger PASS, owner-verified (`owner-verified-20260814`) |
| `repeat_consume` gate | 2026-08-14 | Ledger PASS (`session-894e8f57`) |
| `package_launch` gate | 2026-08-14 | Ledger PASS — packaged Gauntlet, 2782-package IoStore mounted outside the editor |
| Rhythm highway WORKED | 2026-08-12 | `Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md` |
| QuillScript WORKED | 2026-08-12 | `Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md` |
| Credits completion | 2026-08-13 | `Docs/CREDITS.md` + `Docs/SOURCES_MATRIX.md` + `Tools/credits_gate.py` (PASS 66 dirs) |
| Repo lock-in merge | 2026-08-20 | `309a575d` (2,243-file asset half) + `caee6389` (text/code half) squash-merged to local `main` |
| Stage v18 re-fetch | 2026-08-20 | False alarm; both copies byte-perfect against oid `e8f3aebd…09264`. Reclaimed 1.7 GB from `.git/lfs/bad/` |
| `BP_MelodiaJRPGPlayerController` reparent — fixed project-wide battle `Accessed None` cascade | 2026-08-26 | Was a byte-for-byte duplicate of stock `BP_JRPGPlayerController`, not a subclass — every hard-typed cast failed against it. Reparented to `BP_JRPGPlayerController_C`, duplicated EventGraph stripped 569→14 nodes (1.44 MB→74 KB). PIE-verified: 12s smoke on `MelodiaIntegrationMap`, `ok:true`, 0 Blueprint Runtime Error / Accessed None; `BP_BattleController.jRPGPlayerController` cast to `BP_MelodiaJRPGPlayerController_C_0` now succeeds; Sir Melodious confirmed live party member and took a battle turn. See `Docs/Handoffs/P0_CLOSEOUT_HANDOFF_2026-08-26.md`. |

---

<details>
<summary>Earlier queues (historical)</summary>

## Highest-leverage queue — 2026-08-13 ~01:45 ET

**Pick up:** `Docs/Handoffs/SESSION_REVIEW_NEXT_PROMPTS_2026-08-13.md` (still valid as evidence path; process facts below supersede its PID table).

**Live state (as of 01:45 — re-verify, do not trust):** One UnrealEditor owning :9316. **Never trust a PID written in a doc; run `Get-Process UnrealEditor` and use what it returns.** The PID recorded here at 01:45 was 48864, which had itself already replaced 38184 — that is two turnovers inside one night, and every doc naming a fixed PID was wrong within hours. Owner is importing ElectricDreams_Env assets in-editor right now (`Levels/ElectricDreams_Env.umap` + 2,339 `__ExternalActors__` + 6 PCG levels were G:-only; C: had none). `MODAL_OPEN` 01:31:55 → **MCP is unresponsive to all lanes until the import modal dismisses — do not queue editor work behind it.** Rhythm + Quill locks hold. Stash `wip-before-pr4-pr6-pull` reconciled (see checkpoint below).

| Task | Phase | Priority | Status | Agent | Notes |
|---|---|---|---|---|---|
| Wait for owner import modal to clear | Tonight | P0 | **In Progress** | owner | Do not touch Content/ or :9316 until dismissed |
| N1 Save `L_KaleidoNave` (Cathedral strip + V2-test actors unsaved) | Tonight | P0 | **Available** | owner | After import clears; one editor |
| A1 stock battle real-key Q/W/O/P — Morning → KaleidoNave | VS | P0 | **Done** | owner | **2026-08-13 owner verified real keys through `BP_BattleUI::OnKeyDown`.** Ledger `[PASS] runtime 2026-08-13`, session `owner-realkey-20260813`. Do not reopen or re-prove. |
| Verify `runtime` ledger PASS row | VS | P0 | **Done** | — | Resolved 08-13: the 08-12 `pie_smoke_1_145605` row was under-evidenced (restoration + PIE smoke, not real input). Superseded by the owner-verified 08-13 row. |
| B4 battle-result closure — Victory/Defeat/Fled/unavailable each resume/abort Quill exactly once | VS | P0 | **Available** | — | `E_BattleResult` → `CompleteBattle`; restoration wired at bridge (PR #6) |
| B7 `ShowRhythmGrade` display after rhythm works | VS | P0 | **Available** | — | Grade HUD text verified invisible 08-11 — recheck Alpha/vis flags when A1 passes |
| N2 Socket GC cine actor to Melusina head | Tonight | P1 | **Available** | — | Do not replace `SK_MelusinaHair`; flip cache on G: `KitbashExport/flip_cache_melusina_waterhair` |
| N3 Blender idle `A_BL_Melusina_Idle_Loop` second pass | Tonight | P1 | **Parked** | — | Only after N1 proves mocap idle looks normal (unit mismatch burned once) |
| T4 lean vow-cross FBX from v22 | Tonight | P1 | **Blocked** | — | Never `T_Hatch_Cross`; needs 5.2 |
| Stale-ref closeout verify | Sync | P1 | **DONE 2026-08-13** | build | Post-import rescan: **273 → 234 stale, all deliberate skips** (220 ED world actors + 7 datalayers + 5 ED demo BPs + `l_melodia_dreamstate` owner-call + 1 dirtmask). Copied via `Tools/copy_ed_closures_20260813.py`: 37 Asmbly ext actors + `t_softsquare_01_m` + `volume`. Registry-verified 37/37 Asmbly actors + both tail pkgs. Loop maps (KaleidoNave/Morning/MainMenu/FallenMoon) 0 missing. ED audio (`/Game/Audio/Aud_Source`) already landed in owner's import |
| Decide `l_melodia_dreamstate..umap` (copy-bug leftover, owner call) | Sync | P1 | **Blocked** | build | Rename to `.umap` (resurrects merged-out level) or delete; not touching without assent |
| Refresh `Exports/bp_battlecontroller_eventgraph_live.json` from live BP | Sync | P1 | **Available** | — | Committed export is stale (still `BP_MelodiaVictoryDialogue`); stash holds the newer snapshot; regenerable post-modal |
| Drop stash `wip-before-pr4-pr6-pull` | Sync | P2 | **Available** | — | Verified: nothing sole-copy in it (restore superseded by PR #6 bridge call; harness line already in worktree) |
| save_load / repeat_consume / package_launch gates | VS | P0 | **Available** | — | The three remaining runtime completion gates; canonical-slot round trip first |
| Re-run `Tools/bp_sweep.py` + static gates | VS | P1 | **Available** | — | `static_gates` ledger FAIL since 08-11; one-editor rules apply |
| LFS lock discipline before any Content push | Sync | P1 | **Available** | — | 2,224 lockable files, **0 locks held**, Cursor lane pushing `pie-rhythm-highway-notes-1a53` — hold locks on files you modify |
| Quarantine stray root probes (`check_*.py`, `fix_*.py`, `pie_*`) | Tonight | P2 | **Available** | — | Owner sign-off required for delete; `_Quarantine_ThirdPartyFix_20260812/` is the pattern |

## Source-control checkpoint — 2026-08-13 (reviewed ~01:45)

- Unreal `main` = `v2/main` = `840b7650`; fetched 00:47. Working tree: 56 paths dirty
  (24 M + 32 ??). No MERGE_HEAD/REBASE_HEAD. Hooks live via `core.hooksPath=.githooks`
  **Correction 2026-08-13: pre-commit does NOT protect .gitignore/.gitattributes/Config INI/run_verify.ps1.** Nothing in `.githooks/` guards those paths; the hook checks LFS pointers >50 MB, forbidden extensions, build-artifact dirs, zero-byte files and junk names. Do not rely on protection that does not exist.
- LFS 3.6.1: 2,224 lockable files; **0 locks held** — hold a lock before modifying
  Content assets (Cursor lane is pushing `v2/cursor/pie-rhythm-highway-notes-1a53`,
  fetched 00:44, unmerged).
- **Stash `wip-before-pr4-pr6-pull` reconciled — safe to drop.** (1) NarrativeSubsystem
  restore edit is SUPERSEDED by PR #6's bridge call (`MelodiaExternalJRPGBridgeSubsystem
  ::HandleBattleOver` → lines 199/234 on HEAD; the stash's CompleteBattle placement
  would double-heal — do NOT apply). (2) harness BP_TRIES line already in worktree.
  (3) export JSON's newer snapshot is regenerable.
- **Remotes renamed 2026-08-13:** `origin` is now **MelodiaMelusinaV2** (the source of
  truth) and `main` tracks `origin/main`. The old `MelodiaMelusina` is `legacy-melodia`;
  `legacy-origin` (dead environment-portfolio) was removed. `remote.pushDefault=origin`
  and `push.autoSetupRemote=true` are set so a bare push cannot land on the wrong repo.
  `recovery/melodia-main-sync-20260811` still tracks `legacy-melodia/main` (ahead 2) —
  those 2 commits exist only on the old repo; cherry-pick or abandon, do not push as-is.
- **Website repo — resolved 2026-08-20.** `my-site-clean/` is dead (11 stray PNGs, gitignored);
  the live site is `fromage3900/my-site`, published by a Pages **Action off its `main`** (no
  `gh-pages` branch despite what the Pages API reports). Tracked `wix/` is the source of truth
  here and was resynced from live — 57 of 78 files had fallen behind, so the old pipeline would
  have regressed the public site. Deploy target is a clone at `C:\EnvironmentPortfolio\_github_deploy`.
  See [WEBSITE_MAINTENANCE.md](WEBSITE_MAINTENANCE.md).
- **Ledger:** `runtime` **PASS 2026-08-13** (session `owner-realkey-20260813`) — owner
  verified real keyboard input; gate CLOSED. The earlier 08-12 `pie_smoke_1_145605` row
  was under-evidenced and is superseded. `static_gates` FAIL since 08-11. Remaining
  completion gates: `save_load`, `repeat_consume`, `package_launch`.

## Tonight continuation — 2026-08-12 ~20:40 ET

Handoff: `Docs/Handoffs/TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md`. The one running editor (`Get-Process UnrealEditor`) holds A1. Loop 26352 = leave running.

| Task | Phase | Priority | Status | Agent | Notes |
|---|---|---|---|---|---|
| Handpainted channel hunt | Tonight | P0 | **Done** | parent | 1208 hits; inventory JSON/md |
| T1 `assign_hero_zentrim.py` disk inventory | Tonight | P0 | **Done** | parent | `--apply` blocked on A1 |
| T1 `--apply` wand + StreetLamp MI_ZenTrim_Base4K | Tonight | P0 | **Blocked** | — | In already-open editor only |
| T2 P0 mesh gap inventory | Tonight | P0 | **Done** | subagent | Cathedral 41 FBX not imported |
| T2 import CathedralKit FBX | Tonight | P1 | **Available** | — | When A idle |
| T3 Flip bake 1–96 + alembic | Tonight | P0 | **Blocked** | — | Blender MCP down; 0 `.bobj` |
| T4 lean cross FBX from v22 | Tonight | P1 | **Blocked** | — | Needs 5.2; never T_Hatch_Cross |
| D1 harness BP_MelodiaBattleUI | VS | P0 | **Done** | parent | `Saved/Audit/harness_battleui_paths_2026-08-12.md` |

## State updates — 2026-08-05
- Git recovery complete: `BS_GodFile/.git` healthy at repo root on `main`; latest local commit `ec20b015`; checkpoint commit `6154cc1e` captures full live working tree on recovered history.
- GitHub connectivity from this workstation is **intermittent**, not permanently blocked and not fixed: pushes have succeeded repeatedly since 2026-08-11, and a `port 443` timeout recurred on 2026-08-13. Treat a failed push as the network, retry, and push from a clean auxiliary worktree rather than a dirty editor checkout. Do not record it as a standing blocker again.
- Collaborator environment artifacts added: `deploy/collaborator_onboarding.sh`, `deploy/validate_collaborator_setup.sh`. `COLLABORATOR_SETUP.md` and `DOC_INDEX.md` updated with tiered onboarding references.

## State updates — 2026-08-06
- Migration count corrected: 5/23 → **4/23** per `Saved/T3D/LIVE_VS_CATALOG_2026-08-06.md`.
- 22/23 widgets drifted 2x–4x in scale/position — owner-confirmed **intentional** authoring using Figma-sourced Melodia textures; not a regression.
- `.github/workflows/melodia_ci.yml` removed (cannot pass — Monolith binaries gitignored, no UE 5.8 on `windows-latest`; see `Docs/Handoffs/GEMINI_PROJECT_HEALTH_2026-08-06.md`).
- `.mcp.json` untracked from git (committed API-key leak — rotation required; history cannot be scrubbed safely on this repo).
- **KaleidoNave encounter AUDIT CORRECTED (2026-08-06 evening):** the earlier "NEITHER path wired" verdict was based on a stale script docstring (`Encounter_<EnemyId>` prefix) and a broken live check (`actor.find_function` doesn't exist in UE 5.8 Python). Source truth: `StartTaggedJRPGBattle` uses `ActorHasTag(EncounterId)` with the **raw ID, no prefix** (`MelodiaExternalJRPGBridgeSubsystem.cpp:83`). Live verification: exactly **1** actor tagged `melodia_smoke_encounter` in the loaded world (`FirstDream_InteractionBattle`, BP_InteractionBattle_C), and the full stock contract resolves — `StartBattle` is a CustomEvent on `BP_DynamicEnemyBattleBase` (in the actor's class chain, confirmed `K2Node_CustomEvent_0`), `offLevelBattleData` + `OnBattleOver` verified present. **Direct-match path IS available.** The tag script's `has_stock_battle_contract` uses `find_function` and would crash — needs the same correction.
- **PIE smoke 2026-08-06 evening:** `run_pie_smoke` on current editor level (L_KaleidoNave): 0 crashes, 188 frames, teardown clean; `ok=false` only from 3 pre-existing errors (`ABP_Melusina_WaterHair` "Accessed None" — present in logs before this session, unrelated to the loop). Map boots and Melusina animates.
- **Live Coding BLOCKED (2026-08-06 evening):** `editor:trigger_build` fails identically every time (~30s in, "Live coding failed, please see Live console" + a blocking modal mid-compile; LiveCodingConsole log shows "Creating patch" then window destroyed). 5 consecutive failures today including pre-crash attempts — environment issue, not caused by any agent. Until a real (non-Live-Coding) rebuild or a Live-Coding fix happens, the Monolith enum-pin fix **cannot be baked**; BP-side wiring that does not need new C++ reflection is unaffected.
- **BP_BattleUI rhythm state (verified live):** ShowBattleUI already creates `WBP_MelodiaRhythmHighway`, AddToViewport, SetVisibility, pushes `MelodiaBattleInputContextHandle`; HideBattleUI pops it. The two remaining seams are the handoff's §3a (skill-select → `StartSession`) and §3b (`SubmitRatedInput → ConsumePendingRequest` → stock resolver) — **no** StartSession/SubmitRatedInput/Cadence nodes exist in the EventGraph yet. Do NOT touch `JudgementText`/`ComboText` widget-binding (NativePaint HUD — dead task per handoff correction #2).
- **Tools pipeline fixes (2026-08-06 evening):** `bp_regression_checker.py --all` now really scans the 3 Melodia prefixes (Monolith registry scan → on-disk walk → DEFAULT fallback); single-`--bp` mode now scopes the comparison to that BP (was failing on 379 [MISSING] against the full 380-entry baseline); dead `spec` dict removed from `t3d_blueprint_injector.py`; shared `Tools/mcp_client.py` + `Tools/rebuild_all_dashboards.py` created; `continuous_loop.py` has a fingerprint guard around `fix_pipeline_nodes`. Verified: py_compile all green, `--bp` passes, `rebuild_all_dashboards.py` rewrote all 7 dashboard files (Saved + wix mirror).

---

## Active Tasks — Vertical Slice (First Dream)

| Task | Phase | Priority | Status | Agent | Notes |
|---|---|---|---|---|---|---|
| **Phase-0 snapshot (2026-08-06)** — `CompatibilityLabs/Snapshot_2026-08-06` (Content/Melodia, MelodiaIntegration, TurnBasedJRPGTemplate/Blueprints, Content/Python, Saved/T3D, KaleidoNave map) | VS | P0 | **Done** | Gemini | Full working-tree snapshot of the pre-bisect state; preserves the drifted widgets, T3D exports, and the KaleidoNave map for the rebuild. |
| **Phase-1 bisect intake (2026-08-06)** — static forensics of the Quill + battle legs | VS | P0 | **In Progress** | Gemini | Static inspection of the Quill presentation and battle paths; PIE runtime checks pending an editor walkthrough. |
| **Qwen autonomous daemon + content (2026-08-03, approved)** | | | | | |
| Verify KaleidoNave encounter wiring via `AMelodiaEncounterTrigger` (optional `Encounter_<EnemyId>` tag) | VS | P0 | **Verified — direct path available** | 2026-08-06 | Live-verified: exactly 1 actor tagged `melodia_smoke_encounter` (`FirstDream_InteractionBattle`) + full stock contract resolves (`StartBattle` CustomEvent on `BP_DynamicEnemyBattleBase`). Bridge matches the **raw ID** (cpp:83), no prefix — the `Encounter_<EnemyId>` docstring is stale. Fix `tag_kaleido_encounter.py`'s `has_stock_battle_contract` (`find_function` crashes in UE 5.8 Python) + `TRIGGER_LABELS` miss before next use. | |
| Author first Morning Sir grief-hook QuillScript | VS | P2 | **Done** | Qwen | `Content/Melodia/Dialogue/Morning_Sir_GriefHook.qsc` authored per Decision 036 (Sir alive-flew-off-for-snacks, benign, no diagnosis, reunion held). Pending import/compile + PIE. | |
| Qwen-driven autonomous content daemon | VS | P2 | **Done (verified)** | Qwen | `_ollama_experiments/scripts/qwen_daemon.py` (4 tasks: orphan_scripts/pacing_profile/skill_rows/doc_generation). End-to-end verified live: `--task doc_generation` called Qwen3:8b, wrote validated artifact to `_staging/qwen_daemon/`. | |
| UE 5.8 workflow research brief | VS | P2 | **Done** | Qwen | `Docs/Research/UE58_WORKFLOW_RESEARCH_2026-08-03.md` (Substrate/PCG/headless-AI-agents/PCGVolumeSampler). Qwen-generated draft also at `_staging/qwen_daemon/`. | |
| **Parallel lanes (2026-07-31 evening)** | | | | | |
| Ollama QuillScript validation — `_popen` logging probe in `MelodiaNarrativeSubsystem.cpp` | VS | P2 | **Done (built)** | DeepSeek | Logging-only (`MELODIA_Ollama_Validation`), non-gating. `_popen` (blocking, Windows-only) removed from `MelodiaNarrativeSubsystem.cpp`; wired `MelodiaOllamaValidation::ValidateMessageAsync(Message, nullptr)` into `HandleQuillNotification` (Claude's one-line lambda-capture fix inside). Build green. PIE smoke test still owed next PIE session. |
| Psych/music + psych-horror indie research locked to docs | VS | P2 | **Done** | DeepSeek | `Docs/Research/MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md` — OMORI/NecroDancer/Undertale/SH2/Amnesia/DDLC + per-entry "take/reject" mapping to Melodia systems. Decision 033. |
| Narrative hook + full-game loose scope locked to docs | VS | P2 | **Done** | DeepSeek | Two reference docs, no code. `Docs/Research/MELODIA_BARD_GRIEF_HOOK_2026-07-31.md` (Decision 036): owner's lived material (grief/abandonment/BPD/OCD/isolated/behind) metaphorized into Melusina the travelling bard; Sir alive (flew off for snacks, retrievable); heavy wound = past duet-partner, **stays absent**; reunion ending; feel-first/name-once. `Docs/FULL_GAME_LOOSE_SCOPE_2026-07-31.md`: ~12h, 4 movements, exploration > dialogue, reunion-per-movement recruits a party member (Melusina+Sir tandem from start + 4 recruits; roster = existing `UMelodiaPartySubsystem` pattern, zero new mechanics; recruits are owner-filled placeholders A/B/C/D). Both reference-only, north-star, not commitments. |
| Cross-module authority + pacing (2026-07-31, Decisions 030/031/035) | | | | | |
| **Build green** — exploration-gate + Stage C + Stage D + BP_Melusina quarantine, one batch | VS | P0 | **Done** | Claude | 46/3 regression baseline unchanged, zero new failures. Fixed en route: `BlueprintPure` illegal on interface `UFUNCTION`s (Decision 035), and unblocked DeepSeek's `MelodiaOllamaValidation.cpp` (missing lambda capture, one line, their design untouched). |
| Reroute remaining 6 orphaned `OpenLevel` calls through `IMelodiaTravelProvider` | VS | P1 | **Done (build-confirmed)** | DeepSeek | `OrreryMainMenuGameMode.cpp` ×5 via new `TravelToOpeningMap()` helper, `MelodiaOpeningPortal.cpp` inline. Each uses `UMelodiaAuthorityLocator::Get(this)` → `GetTravelProvider()` → `Travel->TravelTo(Map, SpawnTag)` with `OpenLevel` degrade fallback + warning log. Remaining `OpenLevel` sites verified legit: authority itself, save-restore fallback, and the intended degrade paths. **Verified 2026-07-31 late evening (Claude, Decision 037):** closed-editor build zero errors, `Automation RunTests Melodia` 46/3, zero new failures — was previously source-evidence only. |
| Migrate remaining scattered pacing floats to `UMelodiaPacingSubsystem` | VS | P2 | **Done (built)** | DeepSeek | `MelodiaBattleSession` staged-turn windows (`BattleEnemyTelegraphWindow`, `BattleEnemyPostImpact`), `MelodiaBattleArena` hitstop/dolly (`BattleArenaHitstop`, `BattleArenaBreakDolly`), `MelodiaExplorationActors.TravelDuration` (`PlatformTravelDuration`, resolved once in BeginPlay per the Sir pattern). All keep `EditAnywhere` defaults as the false-return fallback. Scope note in `MelodiaPacingSubsystem.h` updated. |
| Author a `UMelodiaPacingProfile` DataAsset | VS | P2 | **Done (built)** | DeepSeek | `DA_MelodiaPacingProfile` at `/Game/MelodiaIntegration/Config/` — 7 IDs seeded at current defaults (MorningDepartureDelay 1.25, MorningDepartureDuration 1.8, BattleEnemyTelegraphWindow 1.0, BattleEnemyPostImpact 0.35, BattleArenaBreakDolly 0.8, BattleArenaHitstop 0.08, PlatformTravelDuration 2.0). Auto-loaded + set active in `UMelodiaPacingSubsystem::Initialize` (mirrors `UMelodiaPartySubsystem::Initialize` pattern); missing asset still degrades to EditAnywhere fallbacks. |
| **Melody Token economy (2026-08-02 — this queue predated the wallet release and had no row for it)** | | | | | |
| Melody Token pickup actor + HUD presentation | VS | P0 | **In progress** | Kiro | Owner confirms Kiro is actively on this (2026-08-02). ⚠️ A file survey the same day reported "not started" — **that finding was wrong and should not be repeated**: it grepped only C++ under `Plugins/` for a `TokenPickup` class, and pickups/HUD are **Blueprint** assets (`BP_`/`WBP_`), which such a grep cannot see. To check this lane's progress, search Content for Blueprints referencing `UMelodiaTokenWalletSubsystem`, not C++ source. Provider is released; test without building assets via `melodia.Wallet.Dump/Grant/Spend/AddMana/SpendMana`. Spec: `Docs/Handoffs/KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md`. |
| Wallet restart-idempotence test | VS | P0 | **Available** | — | The one untested case that reaches players: grant with a `GrantId` → save → **fully exit the process** → relaunch → load → repeat the same grant must still be **rejected**. An in-memory guard passes the reopen-dialogue test and still double-pays after relaunch. Cline verified branch/idempotency behaviour in-session on 2026-08-01 (`CLINE_TOKEN_BRANCH_VERIFICATION_2026-08-01.md`) — all checks pass, but not across a process restart. |
| **KaleidoNave merge fallout (2026-07-31, owner-reported)** | | | | | |
| Dreamstate BPs merged into KaleidoNave don't function on that level | VS | P0 | **Fixed (unverified in PIE)** | Claude | Root cause found: `MelodiaOpeningPortal_0` ("Dreamstate_WakePortal")'s `DestinationLevelName` was never overridden per-instance — still the raw C++ default `/Game/ZenForestTest`, not even the stale value Decision 029i suspected. Fixed via Python (`set_editor_property`) to `/Game/EnvSandbox/Environments/L_KaleidoNave`, level saved. The silent-early-return logging Decision 029i flagged as missing (`BeginWindowDeparture`/`NotifySirDeparted`) already exists (`MELUSINA_DEPARTURE` `UE_LOG` lines, `MelodiaSirMelodiousIntroActor.cpp:198-215`) — not a gap. Not yet PIE-walked end to end. |
| Death routes to stock TurnBasedJRPG menu instead of `WBP_MainMenu` | VS | P0 | **Fixed (unverified in PIE)** | Claude | Decision 021b resolved — see `_DECISION_LOG.md`. Real cause was `BP_BattleController`'s CDO `mainMenuMapName = None` (not the widget's own "MainMenu" default as first diagnosed; that pin is fed by a connected `Get`, so the widget default never applies). Set via `set_cdo_property` to `/Game/Melodia/Levels/Menu/L_MelodiaMainMenu` — owner confirmed this map is the real, working main menu (settings/save/load/start), not a placeholder. Compiled clean, saved. Not yet PIE-walked (party wipe → confirm → arrival). |
| **4 of 5 orphaned-script recoveries are WRONG — do not trust or run yet (2026-07-31 evening)** | VS | P1 | **Available** | — | A background agent (Haiku) reconstructed `audit_project_hygiene.py`, `build_technical_breakdown_manifest.py`, `melodia_asset_passport.py`, `rewrite_content_paths.py`, `validate_local_doc_links.py` from their `.pyc` and self-reported "bytecode-verified ✓" for all 5. **Independently re-verified (Claude) — false for 4/5.** `rewrite_content_paths.py` has inverted boolean logic (`CONTAINS_OP` "not in" vs "in" at the same position) — running it could rewrite the wrong files. `melodia_asset_passport.py` is missing 2 whole functions (22 vs 24 code objects). `build_technical_breakdown_manifest.py` and `validate_local_doc_links.py` both have real opcode-level structural divergence. Only `audit_project_hygiene.py`'s single diff looks benign (a `frozenset` repr artifact of hash-randomization across process boundaries, confirmed by direct test — not a logic bug). **Do not run the 4 broken ones. Redo needed, likely with a stronger model** — the proven method (marshal+dis+positional bytecode compare) works, Haiku's execution of it didn't. |
| **Regression gate has been too narrow — 3 failing tests were hidden (2026-07-31)** | VS | P1 | **Available** | — | The documented gate runs `Automation RunTests Melodia.Integration` = **5 tests**. The full `Melodia` suite is **49 tests, 3 failing**, and has been for an unknown period. **Use `Automation RunTests Melodia` (no `.Integration`) as the gate from now on.** Failures, none caused by the 2026-07-31 `MelodiaMinimalHUD` removal: **(1)** `Melodia.NPC.InteractionDefaults` — assertion failures at `MelodiaNPCApplicationTests.cpp:13,19`, `HasDialogue`/`BeginInteraction` returning the wrong bool with no content. **(2+3)** `Melodia.Roguelike.Functional.ThreeStagePhysicalRoute` and `.TwentyFiveGenerationSoak` — both assert the log warning `'Using CommonUI without a CommonGameViewportClient'` occurs **1 time**; it now occurs **0 times**. These are tests asserting a bug still exists, and the bug was fixed — the tests need retiring, not the fix reverting. `ThreeStagePhysicalRoute` also can't resolve `/Game/UEDPIE_0_ZenForestTest`, the map being retired by the KaleidoNave merge. Roguelike lane is parked (P3) so 2+3 are low urgency; the gate widening is not. |
| **Travel authority cannot reach MelodiaCore (2026-07-31, architectural)** | VS | P1 | **Available** | — | **Correcting an earlier false claim of mine:** `MelodiaSaveSlotLibrary` was *not* "the last direct `OpenLevel`" — it was the last one in the **BS_GodFile game module**. MelodiaCore still has **seven**: `OrreryMainMenuGameMode.cpp:380,388,397,422,449` (five), `MelodiaSirMelodiousIntroActor.cpp:205`, `MelodiaOpeningPortal.cpp:45`. All are in live code paths, not the dead 65/70 headers. **They cannot simply call `TravelTo`:** `UMelodiaTravelSubsystem` lives in the game module and MelodiaCore is a plugin, so reaching it inverts the dependency. Decision 023 is therefore true *within the game module only*. Resolving needs a real choice — move the travel subsystem into MelodiaCore, or expose an interface MelodiaCore can call — **not** a `MelodiaCore.Build.cs` dependency on `BS_GodFile`. Do not hack this; it is a design decision, not a wiring task. |
| **Foundation Gates (pre-combat-expansion)** | | | | | |
| Identify instantiated stock battle widget package at runtime | VS | P0 | **In Progress** | Muse | **Reopened 2026-07-31.** Was marked Done on static evidence while self-labelled "Tool-proven, not PIE-tested" — but the gate says *at runtime*, and `Docs/2026-07-29_PROJECT_HANDOFF.md:22` warns static inspection "must not be used to infer the state of a later active package". Static finding stands and is useful: `/Game/TurnBasedJRPGTemplate/` is active (modified 2026-07-29, referenced by 10+ C++/Python files); `/Game/_ThirdParty/TurnBasedJRPGTemplate/` untouched since the 2026-07-09 import. Needs one PIE capture to close. |
| Prove Attack/Skill/Item/Flee mouse, keyboard, controller parity | VS | P0 | **Available** | — | No duplicate execution |
| Pass Victory/Defeat/Fled/unavailable result matrix | VS | P0 | **Available** | — | Each resumes/aborts Quill exactly once |
| Create/load canonical BP_JRPGSaveGame slot across process restart | VS | P0 | **Available** | — | Full process restart persistence |
| Prove one narrative flag + one reward restore without duplication | VS | P0 | **Available** | — | |
| Load canonical JRPG slot with Quill unavailable, preserve state | VS | P0 | **Available** | — | |
| Route missing/unknown script to authored safe location | VS | P0 | **Available** | — | Without erasing valid current state |
| Test interpreter invalidation during terminal-result broadcast | VS | P0 | **Available** | — | Retain recoverable pending result if Quill resume fails |
| Keep manual saving disabled during active narrative battle | VS | P0 | **Available** | — | |
| Wire Main Menu New Game/Continue/Load to canonical JRPG GameInstance | VS | P0 | **Available** | — | Before making it a startup screen |
| Repair or revise Morning_RoomShell validator contract | VS | P0 | **Available** | — | Missing actor label |
| Identify/isolate overlong serialized name causing cook exit 25 | VS | P0 | **Done** | Claude | 2026-07-30 — `PCGEx_PathTesselate.uasset`, invalid name at index 411. Decision 022 |
| Quarantine 5 damaged assets (`_QuarantineAssets_20260730/`) | VS | P0 | **Done** | Claude | 4 of 5 are truncation/header damage — consistent with the USB migration |
| Package the proven three-map route | VS | P0 | **Done** | Claude | `Saved/StagedBuilds_20260730/` 2.1 GB, all 5 maps, `Success - 0 error(s)` |
| **Launch-test the packaged build** | VS | P0 | **Available** | — | Run `BS_GodFile.exe`, walk Morning → Dreamstate → ZenForest outside the editor. This is the only open packaging item. |
| **Combat Expansion** | | | | | |
| Make active stock command UI readable, focusable, visually consistent | VS | P1 | **In Progress** | Kiro | Layout-overlap fixed + real key labels set (see row below); 2026-08-01 Kiro pass set primary `BP_ActionButton` `ActionButton.IsFocusable=true` and `ActionText.Justification=Center`; graph unchanged and compile clean. Hover/pressed/disabled style states and runtime package identity still require PIE verification. |
| Fixed BP_ActionsUI Attack/Skill/Item/Flee button overlap | VS | P0 | **Done** | Claude | SkillButton/FleeButton shared inconsistent alignment pivots causing near-total overlap; all four buttons now one evenly-spaced row (Attack/Skill/Item/Flee, 16px gaps, uniform anchor+alignment+size), compiled clean |
| Set real desktop labels on the 4 command buttons | VS | P1 | **Done** | Claude | Set `action` text on each instance (`raw_mode=true`, blocked by allowlist otherwise): "Attack [J]", "Skill [K]", "Item [I]", "Flee [F]" per the documented recommended labels. Compiled clean, saved. |
| Preserve stock JRPG controller as turn/target/damage/result authority | VS | P1 | **Done** | GPT | Decision 009 — co-op skills use stock authority |
| Add one meaningful combat decision at a time | VS | P1 | **Available** | — | Playtest before adding another |
| Improve hit/damage/break/result/companion feedback | VS | P1 | **Available** | — | Without making rhythm mandatory |
| Keep one enemy/encounter until complete decision loop is fun | VS | P1 | **Available** | — | |
| Add tests to result matrix when new terminal path introduced | VS | P1 | **Available** | — | |
| **Co-op Skills (2026-07-29)** | | | | | |
| BP_MelusinaPetalCadence — mapped, applies Resonance buff | VS | P0 | **Done** | GPT | Stock BP_BattleSkillBase child, level 1 |
| BP_SirSkyboundRefrain — mapped, conditional bonus on Resonance | VS | P0 | **Done** | GPT | Stock BP_FocusAttack parent, needs conditional bonus wired |
| BP_Resonance — one-turn buff, BP_BuffBase child | VS | P0 | **Done** | GPT | Applied through stock ApplyBuffs flow |
| Skybound Refrain conditional bonus when Resonance present | VS | P1 | **Available** | — | Last remaining co-op mechanic |
| Sir battle mesh/portrait/animation assignment | VS | P1 | **Available** | — | Sir still needs his visual identity |
| **Rhythm / Harmonix (2026-07-30, Decision 012)** | | | | | |
| `UMelodiaMusicClockSubsystem` — single musical-time authority | VS | P0 | **Done** | Claude | Harmonix preferred, Quartz second, no wall clock |
| Harmonix module deps added to `BS_GodFile.Build.cs` | VS | P0 | **Done** | Claude | Harmonix, HarmonixMidi, HarmonixMetasound |
| `RhythmBeatTracker` converted to forwarder | VS | P0 | **Done** | Claude | Same Blueprint pins, correct time |
| Hardcoded 120 BPM wall-clock fallback removed | VS | P0 | **Done** | Claude | Was drawing wrong beats against 128 BPM music |
| `RecordInputNow()` on presentation rhythm component | VS | P0 | **Done** | Claude | Grades on ExperiencedTime; presentation-only |
| Closed-editor build to bake new reflected types | VS | P0 | **Done** | Claude | 2026-07-30 — three green builds, last 35s. Re-confirmed 2026-07-31 (38.5s, zero errors). **Build gate is closed; it is no longer blocking anything.** |
| Import `128BPMarpeggiomelody.mid` as a Harmonix MIDI asset | VS | P1 | **Available** | — | Into `/Game/Melodia/Audio/MIDI/` per the contract |
| Presentation actor: MetaSound source + `UMusicClockComponent` + register | VS | P1 | **Available** | — | Calls `RegisterMusicClock` on BeginPlay |
| `DA_MelodiaRhythmProfile_PetalSever` first proof asset | VS | P1 | **Available** | — | One bar, one downbeat, no gameplay effect |
| Wire calibration offset to `UMelodiaGameUserSettings` | VS | P1 | **Available** | — | `SetCalibrationOffsetMs` is the runtime mirror |
| **Foundation Composition (2026-07-30, Decisions 013–015)** | | | | | |
| `FMelodiaNarrativeRecord` v2 + `MigrateRecord` | VS | P0 | **Done** | Claude | SocialStats canonical; BondRanks/PhaseIndex/SpawnContext reserved |
| Persona social stats read/write through the record | VS | P0 | **Done** | Claude | Transient map removed — no second source of truth |
| `IsGatedContentAvailable` extracted | VS | P1 | **Done** | Claude | Minimap + future Orrery share one rule |
| Music clock project-wide statics + ambient beat | VS | P1 | **Done** | Claude | `Get`/`GetMusicBeatPhase`/`GetMusicPulse`; beat no longer battle-gated |
| **Editor-side (afternoon):** Skybound Refrain conditional bonus | VS | P1 | **Available** | — | Blueprint work; last co-op mechanic |
| **Systems landed 2026-07-30 evening, never tracked here** | | | | | |
| `UMelodiaTravelSubsystem` — single travel authority | VS | P0 | **Done** | Claude | 2026-07-30 21:17–21:32. Allowlist validation + spawn-tag placement + input-context clear on arrival. Decision 023 (written down 2026-07-31). Supersedes `GAMEPLAY_REVIEW_2026-07-30.md` §2. |
| `UMelodiaInputContextSubsystem` — single input/focus authority | VS | P0 | **Done** | Claude | Push/pop context stack; `IsMovementAllowed` / `IsInteractionAllowed` / `IsSavingAllowed`. Structurally enforces the no-mid-battle-save gate. **Corrected 2026-08-06:** consumers ARE wired as of 2026-08-04 — `MelodiaQuillPresentationWidgets.cpp:115-117` pushes the Dialogue context; `MelodiaAudioReactivePresentationSubsystem.cpp:78-82` pushes/pops the Battle context; `MelodiaTraversalComponent.cpp:18`, `MelodiaTravelSubsystem.cpp:137`, and `MelodiaSaveSlotLibrary.cpp:220` consume it. Status stays Done; the open item is **runtime push/pop balance verification**, not wiring. |
| Route `MelodiaMapTransitionComponent` through the travel authority | VS | P1 | **Done** | Claude | Was calling `LoadStreamLevel`, which silently does nothing for a standalone map. |
| Remaining travel bypass: `MelodiaSaveSlotLibrary.cpp:50` | VS | P2 | **Done** | Claude | 2026-07-31 — bypass closed. Now routes through `UMelodiaTravelSubsystem::TravelTo` with allowlist validation, spawn placement, and input-context clear. Degrades loudly (logs + falls back to `OpenLevel`) if ID refused or subsystem unavailable. |
| **Agent tooling (2026-07-31)** | | | | | |
| Restore MCP surface — `.mcp.json`, dead `G:\` paths | VS | P0 | **Done** | Claude | Monolith was unregistered entirely (registration lost in the G:→C: migration while its enable-list entry survived); three adapters still pointed at the failed USB drive. Proxy smoke-tested with the editor closed: 28 namespace tools served. Decision 025. |
| Monolith verification loop — fingerprint + assert + `set_node_property` | VS | P0 | **Done** | Claude | Build green 38.5s. Decision 024. **Gate before use: prove the fingerprint is byte-stable across a no-op resave.** |
| Walker `FClassProperty` fix | VS | P0 | **Done** | Claude | Every `TSubclassOf` write through `set_cdo_property` / `set_property_at_path` / `set_cdo_properties` / `seed_data_asset` silently failed for Blueprint class paths. Fixes 4 existing actions. |
| Recover `generate_melodia_rules.py` + `export_melodia_rhythm_web_config.py` | VS | P1 | **Done** | Claude | Reconstructed from `.pyc`; bytecode-identical, outputs byte-identical. **15 more orphaned scripts remain** — see `_ROADBLOCKS_2026-07-31.md`. |
| Execute wiring checklist items 1, 2a, 2b, 5a via Monolith | VS | P1 | **In Progress** | Rider | 2026-07-31 — items 1, 2a, 5a DONE. Item 2b (PlayerStart tags) BLOCKED on absent `melodia:travel:` dialogue emission. Tag value = "melodia traversal" (owner-provided). |
| Execute wiring checklist item 2c (replace `Open Level` nodes) | VS | P1 | **Done (verified)** | Kiro | Reassigned by owner 2026-08-01. Live Monolith readback found the authored legs already converted: `ChangeMapForBattle` and `ChangeMap` route through two `UMelodiaTravelSubsystem::TravelTo` calls and branch on each return value; only the intentionally preserved `currentMap` save/restore `OpenLevel` nodes (`_30`/`_52`) remain per Decision 028. Allowlist contains KaleidoNave. Fingerprint stable before/after no-op save (`2ab720437bc6bd56811fbe7e113f9f86663a132e`); compile UpToDate, 0 errors/0 warnings; targeted assertion matched 6/6 nodes and 4/4 connections. Full automation/PIE deferred to avoid interrupting active environment work. |
| **Editor-side:** import `.mid`, clock actor, first rhythm profile | VS | P1 | **Available** | — | Needs rebuild + content promotion first |
| **Editor-side:** Orrery travel adapter on the registry | VS | P2 | **Available** | — | First system built entirely to the composition pattern |
| **MUSE lane (2026-08-11, Meta Muse Code)** — keep WSL `muse` auth/validation green | Tooling | P2 | **Done** | Muse | `wsl -e muse --version` → 0.1.0, `muse exec --trust-workspace` smoke PASS, `.\deploy\start_opencode_muse_lane.ps1` PASS; auth at `~/.config/muse/auth.json` (Meta Model API key, verified `KEY_OK` 2026-08-11). Write scope per `.jcode/swarm-prompt.md` §MUSE (`.opencode/`, `Docs/Production/MUSE*`, `deploy/*muse*`); coordinate with jcode MUSE worker per `Docs/PhoneOps/JCODE_SWARM_PIPELINE.md`. Docs: `Docs/Production/MUSE_CODE_LANE_2026-08-11.md`. **Verified 2026-08-11 (in-sandbox):** `muse --version` → 0.1.0-R708.1 OK; `~/.config/muse/auth.json` d--------- (chmod-600, correctly locked — expected Permission denied from shell); `~/.local/bin/muse` 33118 bytes executable; `deploy/start_opencode_muse_lane.ps1` 4739 bytes OK; `.opencode/opencode.jsonc` OK (monolith disabled until UE live); `.jcode/swarm-prompt.md` §MUSE write scope confirmed. `muse exec --trust-workspace` previously PASSED per lane doc; in-sandbox `muse exec --trust-workspace` blocked by sandbox FS (session lock Read-only FS, exit 1) — host re-verify **PASSED**: `wsl.exe -e bash -lc "muse exec --trust-workspace \"Read AGENTS.md Working Agreement point 1...\""` → `Working Agreement point 1 is to do the job asked, ship it and stop...` exit 0; `powershell.exe -File deploy/start_opencode_muse_lane.ps1` → jcode v0.75.3 + opencode 1.18.3 + muse WSL OK → PASS exit 0. |
| Prove canonical save round trip (now covers social stats) | VS | P0 | **Available** | — | PERSONA_LITE NOW task; gate for everything downstream |
| **Hair Fix (2026-07-29)** | | | | | |
| Hair bone analysis (465 body vs 148 hair, zero shared) | VS | P0 | **Done** | GPT | audit_melusina_hair_bones.py |
| Native C++ fallback in UMelodiaHairComponent | VS | P0 | **Done** | GPT | Attach to head_x, retain Kawaii Physics |
| **Melusina hair sits on her head** | VS | P0 | **Done** | Claude | **PIE-verified 2026-07-31.** `UMelodiaHairComponent` sockets to `head_x` and applies the inverse of that bone's bind-pose component-space transform. The hair mesh is authored in character space, so parenting to a bone was stacking `head_x`'s bind transform on geometry that already accounted for it — the ~3 ft offset was head height, the wrong rotation was the bone's axis convention. Removed along the way: `FallbackAttachCorrection`, `bForceAttachCorrection`, shared-bone counting and every branch off it. Log line is now `MELUSINA_HAIR_SOCKET`. |
| **ZenForestTest Combat** | | | | | |
| BP_BattleController added to ZenForestTest | VS | P0 | **Done** | GPT | NPC encounter should work after PIE restart |
| "Hair only" combat body visibility fix | VS | P0 | **Done** | GPT | Staged — defer redirect by one tick, needs native build |

## Active Tasks — Portfolio (Delegated to AI Agents)

| Task | Phase | Priority | Status | Agent | Notes |
|---|---|---|---|---|---|
| 1.1 Fix portfolio level path in generate_portfolio.py | P1 | P0 | **Done** | AI agents | Already fixed — LEVEL path corrected to `/Game/EnvSandbox/Environments/Sakura/L_SakuraPath` |
| 1.2 Fix material preview exporter (NameError + wrong filter) | P1 | P0 | **Done** | AI agents | Already fixed — `import datetime` present, asset filter uses `MaterialInterface` class check |
| 1.3 Verify render capture works (PSO fix + CineCamera) | P1 | P0 | **Available** | — | Start editor with -unattended, trigger_build, test capture on known material |
| 1.4 Run full portfolio pipeline end-to-end | P1 | P0 | **Available** | — | generate → aggregate → handoff, verify all 7 sections populated |
| 1.5 Ship website (ingest → validate → deploy) | P1 | P0 | **Blocked** | BLACKBOXAI | **Reconciled 2026-07-31:** was "In Progress" here and "Blocked" in `_PORTFOLIO_SHIP_CHECKLIST.md:19`. Blocked is correct — it waits on user-supplied hero renders. Pipeline prep can proceed in parallel; the deploy step cannot. |
| Website overhaul — level inventory + static mapping (Task 1.1) | P1 | P0 | **Done** | BLACKBOXAI | 2026-07-31 — `Docs/WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md` created: ~65-map `.umap` inventory, corrected route (L_MelusinaMorning → L_KaleidoNave (merged Dreamstate) → ZenForestTest → Roguelike rooms), stale/duplicate maps flagged (incl. two corrections to the overhaul plan: Dreamstate merged into KaleidoNave; dual L_MelusinaMorning resolution per Decision 029h). |
**Live-verified 2026-07-31 (Monolith port 9316 confirmed CONNECTED, `server_running: true`):** Melody Tokens / Ornament kitbash / Torii greybox / Sakura material support **confirmed** in the live UE index; Cross-as-prop, TrebleClef meshes, Sando, and `zenlantern.fbx` **have no live counterpart — excluded from site copy**. Section G in the level-mapping doc upgraded to per-row live asset paths. Per-level *placement* reference queries logged as follow-up; no longer blocks website copy. |
| Website overhaul — level-to-gameplay-beat mapping + technical descriptions (doc tasks) | P1 | P1 | **Done** | BLACKBOXAI | Beat mapping (0:00→20:00 across the 4 route legs) + technical feedstock (combat authority, Harmonix/Quartz, travel authority, save schema, Substrate/PCG/Blender-5.2 pipeline, rhythm-expressive) in the same doc, cited to decisions. |
| Website overhaul — UE gameplay level renders (beauty/wireframe/material/PCG) | P1 | P0 | **Available** | BLACKBOXAI | Blocked on UE session — user is prepping UE renders (Monolith :9316). Do not duplicate user's in-progress capture. |
| Website overhaul — Blender capture tasks (turntable/concepts/lookdev) | P1 | P1 | **Blocked** | BLACKBOXAI | **Port check 2026-07-31:** TCP connect to 127.0.0.1:9878 FAILED — Blender MCP adapter NOT listening despite "blender should be live". Start the adapter (addon) in a live Blender session before capture. Do not retry blind. |

---

## Completed Tasks

| Task | Phase | Date Done | Agent | Notes |
|---|---|---|---|---|
| Produce project intake report | Strategic | 2026-07-26 | Cline | _INTAKE_REPORT_2026-07-26.md |
| Create portfolio ship checklist | P1 | 2026-07-26 | Cline | _PORTFOLIO_SHIP_CHECKLIST.md |
| Create vertical slice scope doc | P2 | 2026-07-26 | Cline | _VERTICAL_SLICE_SCOPE.md |
| Create decision log | All | 2026-07-26 | Cline | _DECISION_LOG.md — 10 decisions recorded |
| Create agent ecosystem doc | All | 2026-07-26 | Cline | _AGENT_ECOSYSTEM.md — parallel delegation model |
| Create task queue | All | 2026-07-26 | Cline | _TASK_QUEUE.md — this file |
| Create session handoff template | All | 2026-07-26 | Cline | _SESSION_HANDOFF_TEMPLATE.md |
| Create session handoff (current) | All | 2026-07-26 | Cline | _SESSION_HANDOFF.md — populated |
| Restructure DOC_INDEX.md | All | 2026-07-26 | Cline | 3-tier hierarchy, agent docs marked historical |
| Git recovery (6 commits, fsck pass, LFS fsck pass) | VS | 2026-07-28 | Sol/GPT | recovery/core-game-state-20260727 |
| Full Editor build pass | VS | 2026-07-28 | Sol/GPT | 4.11 seconds |
| Playable opening traversal (PIE-verified) | VS | 2026-07-28 | Sol/GPT | Morning → Dreamstate → ZenForest |
| Persona-lite foundation (subsystem, quests, equipment, markers) | VS | 2026-07-28 | Sol/GPT | UMelodiaPersonaSubsystem, 3 quests, 4 markers |
| Quill battle smoke test (42 statements, 3 notifications) | VS | 2026-07-28 | Sol/GPT | MelodiaQuillSmoke.qsc compiled and saved |
| Main menu SoftMG parchment backdrop | VS | 2026-07-29 | GPT | WBP_MainMenu — zero errors |
| Co-op skills (Petal Cadence, Skybound Refrain, Resonance) | VS | 2026-07-29 | GPT | Stock authority, BP_BuffBase child |
| Hair bone analysis + native C++ fix staged | VS | 2026-07-29 | GPT | UMelodiaHairComponent, needs closed-editor build |
| ZenForestTest BattleController added | VS | 2026-07-29 | GPT | Combat should initiate after PIE restart |
| Artist handoff doc created | VS | 2026-07-29 | GPT | MELUSINA_SIR_SKILL_UI_AUTHORING_2026-07-29.md |
| MelodiaStudio addon hardening (B1, B2, B5, P1, P4) | VS | 2026-07-28 | Sol/GPT | 39/39 GN builders gold/works |
| Update website worlds section with actual gameplay levels | VS | 2026-07-29 | Cline | Replaced 4 placeholder levels with real gameplay levels: Melusina Morning, Kaleido Nave, Zen Forest, Fallen Moon. Updated application-hub.html and index.html |

---

## Parked / Future Tasks

| Task | Phase | Priority | Notes |
|---|---|---|---|
| Material system review (7 fixes from 2026-07-02) | Post-ship | P3 | Extract Nikki/Parallax into MFs, collapse dupe params, etc. |
| Fix 4 crashing PCG graphs (AtriumEx, ColonnadeEx, FacadeEx, RotundaEx) | Post-ship | P3 | Quarantine holds — fix after vertical slice ships |
| Fix 10 spline-blocked graphs | Post-ship | P3 | Apply BP_PathSplineProvider pattern after vertical slice |
| More Escher generators | Post-ship | P3 | You have 6 — enough for now |
| Stats exporter for portfolio | Post-ship | P3 | Missing producer — schema slot ready |
| Blender addon updates | Post-ship | P3 | surreal_architecture_gen.py frozen until after ship |
| Performance profile all 4 WP levels | Post-ship | P3 | Only SakuraDream needed for vertical slice |
| MelodiaCore C++ plugin compile | Post-ship | P3 | 5-day budget deferred — working around with JRPG template |
| GitHub LFS budget restoration | Post-ship | P3 | Blocks recovery branch push |
</details>
