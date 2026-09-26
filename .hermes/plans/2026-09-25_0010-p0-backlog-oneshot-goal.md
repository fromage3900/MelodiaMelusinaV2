# GOAL — P0 backlog one-shot: golden run closed, Melusina conforming, route defects cleared (2026-09-25)

**Bounded:** one session, one editor, one mutating MCP surface (Monolith). Every step ends in a live read-back or PIE measurement, not a compile.
**Source:** findings from the 2026-09-24 night P0 re-run (`CURRENT_STATE.md` entries "P0 closeout re-run", "Kawaii collision fix", "pro-setup ruling") plus the still-open P0 items in §3.
**Ruling:** Jev `jev-1.13.0` (`Saved/Audit/p0_closeout_2026-09-24/jev_melusina_pro_setup.json`) — garment conformance first; Kawaii stays the skirt solver; riskiest = reimports breaking assets.
**Done =** every gate below is green or explicitly parked with a reason, `CURRENT_STATE.md` is updated, and ledger rows are appended for the gates that actually closed.

## G0 — Unblock (owner, 1 minute)
- Add `"mcp__monolith__editor_query"` to `permissions.allow` in `.claude/settings.local.json` (auto mode blocks asset reference edits and self-edits of settings).
- **Gate:** one Monolith `run_python` asset write is accepted.

## Progress (2026-09-25 ~00:20)
- W1.6 voice lines: **source fixed** — `MelodiaMorningIntro.qsc` referenced `mel_perch_01` / `mel_battle_entry` without the `.ObjectName` suffix every working Quill reference uses; both now full object paths (backup `Saved/Audit/p0_closeout_2026-09-24/MelodiaMorningIntro.qsc.bak`). **Saved 00:20:30**, both sounds resolve (read-back).
- W1.4 arrival: **source fixed** — `AMelodiaSirMelodiousIntroActor` hard-coded `TravelTo(..., NAME_None)`; new `DepartureSpawnTag` (default `Arrive_FromDreamstate`) is passed. **Built** (closed-editor UBT 26.9 s; headless `Melodia.` 101/103, same two known headless-only fails). **Live proof pending** — needs a real Morning→KaleidoNave departure; watch for `MELODIA_TRAVEL_ARRIVED spawn_tag=Arrive_FromDreamstate placed=1`.
- W1.1 skirt skeleton: **DONE 2026-09-25** — `SK_Melusina_V2_Skirt_R2_SmoothChains.Skeleton` → `SK_Melusina_Skeleton` (Claireon `uobject_set_property`, allow_non_editable; saved). PIE: 0 `default slot 7 refused`, Skirt slot shows the mesh, visible, leader-posed to `CharacterMesh0`; penetration unchanged (0 surface contacts). G0 permission added.
- New finding (owner PIE 2026-09-25 04:15): `Accessed None trying to read saveUI` in `BP_SavePointBase` EventGraph (`RemoveFromParent`) — add to W1 before the golden run save step.
- Reunion trigger sits over the lake (no floor collision); the earlier 'falling pawn' was the agent's scripted drop into water — W1.5 closed as test artifact unless a real walk reproduces it.
- W1.8 preflight: `deploy/` is deliberately read-only (105 files) — **parked for owner**.

## Wave 1 — Agent-executable now (no owner input)

### W1.1 Default skirt conforms to the body skeleton
- `SK_Melusina_V2_Skirt_R2_SmoothChains` → assign `SK_Melusina_Skeleton` (Monolith `compare_skeletons`: 465/465 bones, hierarchy identical; only the skirt mesh references its private skeleton). Backup: `Saved/Audit/p0_closeout_2026-09-24/skirt_skeleton_backup/`.
- Leave the orphaned `…_SmoothChains_Skeleton` on disk (deletion is Red / owner).
- **Gate:** PIE spawn logs no `MELODIA_WARDROBE default slot 7 refused`; Skirt slot component shows the mesh, visible; leader pose follows body; `kawaii_penetration.py` still 0 surface-chain contacts.

### W1.2 Garment import guard (Jev step 1, second half)
- One check, in the existing wardrobe preflight path (`UMelodiaWardrobeComponent::IsGarmentSkeletonCompatible` is already the authority): an editor-time scan of `DefaultGarmentMeshes` + catalog meshes on `BP_MelusinaJRPGCharacter` that reports any mesh whose skeleton ≠ body skeleton. Runs as a `Melodia.Wardrobe.*` automation test, not a new runtime mechanism.
- **Gate:** test passes after W1.1; fails if the skirt is pointed back at its private skeleton.

### W1.3 Skirt Kawaii bone constraints (Jev step 2)
- Add `KawaiiPhysicsBoneConstraintsDataAsset` with horizontal ring constraints between adjacent `c_kilt_XX_YY_l/r` chains + `BoneConstraintSubdivisionCount` collision proxies on the skirt node in `ABP_Melusina_Current`. Follow the Section-2 verification loop (export → fingerprint → mutate → compile → assert → save).
- **Gate:** penetration check at idle and during a scripted swept walk; owner motion check parked to Wave 2.

### W1.4 KaleidoNave arrival point
- Departure (`BP_MelodiaSirMelodiousMorningIntro` → `TravelTo`) sends `spawn_tag=None`; KaleidoNave's `PlayerStart_0` / `Dream_PlayerStart_0` carry no tag, so arrival falls back to the default start (`placed=0`). The 09-25 MultiWorld receipt recorded `Arrive_FromDreamstate placed=1`.
- Restore the authored arrival: tag the existing `Dream_PlayerStart_0` `Arrive_FromDreamstate` (additive, no new actor) and pass that tag from the departure. Content fix, not code.
- **Gate:** `MELODIA_TRAVEL_ARRIVED … spawn_tag=Arrive_FromDreamstate placed=1`.

### W1.5 Backgrounded Morning pawn keeps falling
- After MultiWorld switch the Morning pawn sat at Z −83 566 (swimming mode) in the paused main world. **Likely a test artifact:** the agent had swept her down into the reunion trigger to Z −600 with a scripted move, where there may be no floor. Reproduce with a real walk into the trigger first; fix only if it recurs.
- **Gate:** after forward travel + 30 s, the Morning pawn's Z is unchanged; return travel lands her on Morning ground.

### W1.6 Route asset gaps (cook blockers)
- Quill `Voice` nulls: `/Game/Melodia/Characters/Melusina/Audio/mel_perch_01`, `mel_battle_entry` — locate the real assets (renamed/moved?) and repoint the QSC; if they never existed, remove the `$ Voice` lines rather than ship nulls.
- `L_KaleidoNave` missing dependencies: `MI_Outline_PremiumV3_Hero`, `MI_StarryNight_Hero`, `MI_MeluColorGrade_PortfolioHero`, `NS_SDF_ParallaxFish_Candidate`, `NS_SakuraWaterPetals` — find each referencing actor/PPV; repoint to the existing canonical asset or clear the slot.
- **Gate:** loading KaleidoNave logs zero `LoadErrors`; Morning Quill logs zero `Invalid sound asset`.

### W1.7 UI stalls on the route
- Battle start: 3.25 s from `StartBattle` to battle input, game thread blocked on sync loads of `SeaAbove/Prototype/Reef/Meshes/SM_Flora_Chime` / `SM_Leviathan`. Find who references them in the KaleidoNave battle path; preload with the level or make the reference async.
- First dialogue: ~320 ms hitch from synchronous font loads; one font resolves from an absolute `G:/EnvironmentPortfolio/BS_GodFile/Imports/UI/Fonts/Syne[wght].ttf` path (breaks packaged builds on other machines). Import the font as a project Font Face asset and point the style at it; make the glyph fallback (`DroidSansFallback`) unnecessary for authored text.
- **Gate:** `StartBattle` → `MELODIA_INPUT_PUSH … Battle` < 0.5 s; first dialogue frame < 50 ms; no `G:/` font paths in the log.

### W1.8 Echo tooling truthfulness
- `melodia_system_golden_run_preflight` also reads `issue51_runtime_closure` and `static_gates` latest rows (it reported `ready` while both were FAIL).
- `Tools/regression_suite.py --quick`: retire or fix the stale checks (`WBP_MelodiaRhythmHighway` path, old skill ids, `WalkForward`/`Interact` console commands, `log_matches` counting patterns not hits).
- `bp_regression_checker.py`: handle the 6 notify/library BPs Monolith returns empty for.
- Smoke frame capture returned 0 frames (viewport 0×0 + `InRHITexture` ensure) — capture from the PIE viewport.
- **Gate:** `echo_run.py run runtime_gates` output matches reality (no false passes, no false fails).

### W1.9 Phrase bus on :9002
- Re-run the phrase-bus live proof with the sender on 9002 (`Tools/ship_queue_live_proof.py` already moved); check `Tools/listening_field/jev_director.py` and any TD phrase sender for a hard-coded 9000.
- **Gate:** `GetCurrentState` reads back all seven fields in PIE.

## Wave 2 — Owner hands (real input; agents record)
### W2.1 Golden run, spec `specs/p0/core_p0_dream_golden_run.v1.json`
- Fresh slot → Morning Quill beat → KaleidoNave arrival (W1.4) → one encounter played by keyboard with rhythm skills → save → full editor exit → relaunch → Continue on `MelodiaIntegrationMap` → load again.
- Agents time battle UI → rhythm prompt → grade → result → control return, read wardrobe state before save and after each load.
- **Gate:** every `required_observations` item recorded; no harmony/quest/reward duplication; outfit restored; ledger rows `runtime`, `save_load`, `repeat_consume` appended fresh.
### W2.2 Owner motion check of skirt + hair (run, turn, jump, battle idle)

## Wave 3 — Package + land (owner OK per operation, git law)
### W3.1 Packaged proof — cook to `G:\melodia_packages\`, launch without `-map=`, one pass with `bRelaxedAllowlistInEditor` off. Ledger `package_launch`.
### W3.2 Commit plan, stated before any git op: MultiWorld travel + viewport client + plugin `ShouldCreateSubsystem` patch, PhraseBus :9002, OSC Blender port, Kawaii limit DAs, skirt skeleton reassignment, Wave-1 fixes, `CURRENT_STATE.md`. `DefaultEngine.ini` viewport-client line needs `SKIP_PROTECTION=1` + owner sign-off. Explicit pathspecs only.

## Not in this goal (owner decisions or out of scope)
Hair re-hosted onto the body skeleton (Jev step 4 — reimport risk; owner rig decision) · body physics asset as the single collision source (step 3; after W1.3 shows whether it's needed) · UV-animation motion-blur fix (step 5) · deleting orphaned skeletons / `PCG_East_AtlantisGrove2` (Red) · retiring vestigial `melodiaBattleUI` vars · audio reactivity on `M_Master_Toon_Universal_Alpha` (master architecture) · Morning eye-adaptation −5.4 · Houdini license · Choral Sheep foot-slide · `static_gates` pre-existing asset failures (known-failing).
