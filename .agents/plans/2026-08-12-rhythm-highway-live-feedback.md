# Rhythm Highway — Live Feedback Plan (2026-08-12)

## Goal
Make `WBP_MelodiaRhythmHighway` + `BP_BattleUI` rhythm lanes visible and responsive in PIE on `L_KaleidoNave` via the canonical trigger+Quill path (`MelodiaQuillSmoke.qsc:33` `melodia:battle:melodia_smoke_encounter` → `FirstDream_InteractionBattle` tagged actor → `BP_BattleController_C_0`), with real `Q/W/O/P` through `BP_BattleUI::OnKeyDown`, and prove it with screenshot/video + JSON report next to frames.

## Success Criteria
- Highway renders in PIE: `SheetMusicBG`, `AuroraOverlay`, `SparkleField`, `BeatRingScale`/`BeatRingOpacity` pulsing on `OnMelodiaBeat` (MIDI `128BPMarpeggiomelody_beatgrid`), `ShowRhythmGrade` → `RhythmGradeText` visible (alpha fixed, not `A=0`).
- Lanes light on `OnKeyDown Q/W/O/P` and unlight on `OnKeyUp` same keys (no `D/F/J/K` drift latch).
- `PushHighwayToHUD` driven lanes survive one tick (ambient `bExecutionDrivingHighway` does not clear them).
- `MELODIA_RHYTHM session=` appears once per session in log.
- `melodia.Rhythm.Disable 0` damage `A` vs `1` damage `B` with identical input: `A≠B` (rhythm scalar applied).
- Evidence: `Saved/Playtest/PLAYTEST_*_report.json` + `Saved/PIE_Loop/frame_*.png` next to each other, plus a short video capture, committed harness.

## Context And Current Facts
- `v2` canonical `1ce81cd8` 3 ahead, `0e34eaed` gates `ALL OK` (`graph_reachability` critical-only, `bp_sweep` SHADOWED/DUPES 0, `verify_baseline` 55 clean), `UnrealEditor 90148` just restarted after `17:44` AudioMixer crash, `M1` `RestorePartyAfterBattle` wired `HandleBattleOver` before `CompleteBattle→ResumeQuillOnce` `live_compile 0` errors.
- `L_KaleidoNave` `WorldSettings.DefaultGameMode → BP_MelodiaJRPGGameMode_C`, `FirstDream_InteractionBattle` `Tags ["melodia_smoke_encounter"]` allowlisted, `enemyList len=1`, `battleController → KaleidoNave_BattleController` — `StartTaggedJRPGBattle` would not reject roster. Idle `pie_smoke` `bIsMoving false` never hits volume and `ActiveInterpreter` never notifies battle, so no highway appears. Canonical trigger is Quill `MelodiaQuillSmoke.qsc` line 33.
- Existing tools: `Tools/playtest_harness.py` (probe/slate-sendinput/pie_inject_input backends), `Tools/pie_smoke_runner.py` (frame capture `Saved/PIE_Loop`), `Tools/loop_monitor.py` highway layers check, `Tools/echo_run.py` ledger, `Docs/ECHO/campaign_01_rhythm_damage_delta.md` evidence standard.

## Constraints And Non-goals
- One editor on `9316` only (Windows `C:\Python314\python.exe` reaches Monolith, WSL `python3` does not).
- Do not add compensation flags/branches for highway; delete cause (shared HUD clear, alpha 0, stale drift).
- Do not push `Content/` LFS; `QuillScript` `melodia:stat` idempotent per `IntentId` must remain, `melodia:item:give` stays logging stub.
- Non-goal: redesign input layout (`W→O` 6-key shift is owner feel), redesign materials, or re-track `Content/Art` `SK_Melusina` `40 MB` untracked.

## Key Decisions
- **Trigger:** Quill (`melodia:battle:melodia_smoke_encounter` via `MelodiaQuillSmoke.qsc`) + tagged volume both valid; use **Quill** because it also sets `PendingEncounterId` and `ActiveInterpreter` needed for `CompleteBattle` → `ResumeQuillOnce` exactly-once proof. Rejected volume-only walk (needs pathing to `FirstDream_InteractionBattle` coords, flakier).
- **Input backend:** `auto` → `slate-sendinput` (real OS `SendInput` to focused PIE viewport) primary, fallback `pie_inject_input` (Enhanced Input). Rejected `probe` `register_lane_hit()` (proves seam, not highway; evidence standard §2 HOLD).
- **Capture:** `pie_smoke_runner` PNG sequence + `playtest_harness` JSON report next to frames plus a short `ScreenCapture` video via `Tools/capture_pie_movement_clip` / `ffmpeg`. Rejected single screenshot (needs A/B delta).

## Recommended Approach
1. Verify Monolith live + static gates (already `ALL OK` after `0e34eaed`; re-confirm after editor restart).
2. Run `playtest_harness` Quill battle on `L_KaleidoNave` with `probe` first to prove end-to-end plumbing, then `auto` for real keys. Poll `OnMelodiaBeat`, `PushHighwayToHUD`, `ShowRhythmGrade`, `MELODIA_RHYTHM session=` and `damage_before/after`.
3. If highway blank, fix in order: (a) HUD alpha (`Judgement/Combo` `A`), (b) `bExecutionDrivingHighway` clear guard, (c) `OnKeyUp` drift. Each is a single Blueprint/C++ edit, live-compile, re-capture.
4. Record `runtime` ledger row only when `A≠B` + `session=` + frames+JSON present.

## Work Plan
| Unit | Owner | Files / Surface | Done |
|------|-------|----------------|------|
| W1 Verify live | Muse | `python Tools/echo_run.py status` + `run static_gates` | `ALL OK` + `editor reachable yes` |
| W2 Quill battle smoke (probe) | Muse | `python Tools/playtest_harness.py run --map /Game/EnvSandbox/Environments/L_KaleidoNave --backend probe` | `Saved/Playtest/PLAYTEST_*_report.json` `status COMPLETE` |
| W3 Real-key battle + highway capture | Muse | `... --backend auto` (Q/W/O/P) + `Tools/pie_smoke_runner.py --map ... --duration 12 --capture-interval 0.2` | PNGs `Saved/PIE_Loop/` + report JSON, `MELODIA_RHYTHM session=` logged |
| W4 Highway fix if blank (only if W3 fails) | Muse | `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmHUDWidget.cpp` (ownership), `Content/Melodia/UI/WBP_MelodiaRhythmHighway` (alpha/layers), `BP_BattleUI` `OnKeyUp` graph | `live_compile` `0` errors, re-run W3 |
| W5 Evidence record | Muse | `python Tools/echo_run.py record runtime pass --note "quill smoke highway Q/W/O/P, dmg A vs B, session=..."` | `Saved/gate_ledger.json` row, `Saved/Echo/state.txt` `runtime PASS` |

## Validation Plan
- `powershell python Tools/echo_run.py run static_gates` → `ALL OK`
- `powershell python Tools/playtest_harness.py run --map /Game/EnvSandbox/Environments/L_KaleidoNave --backend probe` → `report.json` `status COMPLETE` `keys [Q,W,O,P]` `backend probe`
- Same with `--backend auto` → `damage_before` vs `damage_after` `A≠B`, log `Select-String "MELODIA_RHYTHM session=" Saved/Logs/BS_GodFile.log`
- `Get-ChildItem Saved/PIE_Loop/*.png` `>5` frames, `Saved/Playtest/*.json` next to them; open one PNG (highway visible) + one video `ffmpeg -f gdigrab` clip `~5s`
- `python Tools/pie_smoke_runner.py --map ... --duration 8` → `Frames >0 Samples 11 Errors 0`

## Risks / Rollback
- Risk: `AudioMixer` crash on PIE re-entry (just crashed `17:44`). Mitigation: keep `DerivedDataCache`/`Intermediate` intact while editor `LISTENING`, use short `8–12s` PIE, stop with `editor_query stop_pie` before next run. Rollback: restart editor `91348` → `UnrealEditor.exe BS_GodFile.uproject -unattended` `30s` for Monolith.
- Risk: `StockSkillRhythmIds` map drift — already `4` correct, re-check `DA_MelodiaIntegrationConfig` if `StartSession` returns `0`.
- Risk: `W→O` 6-key shift feels bad — not a gate failure, owner decision.

## Open Questions
None — all allowlist IDs, MIDI beatgrid, and highway layers are discoverable locally via `get_cdo_properties`/`export_graph`/`project_query search`. `MELODIA_RHYTHM session=` precondition chain is `ActiveInterpreter valid` + `PendingEncounterId` set via `melodia:battle` + `StartTaggedJRPGBattle` finds exactly one tagged actor with `enemyList>0` + `OnBattleOver` delegate bound → `ClassifyJRPGBattleResult` → `CompleteBattle` → `ResumeQuillOnce`.
