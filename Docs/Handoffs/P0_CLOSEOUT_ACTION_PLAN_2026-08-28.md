# P0 Closeout Action Plan — 2026-08-28

**Author:** Melusina (Hermes agent, z-ai/glm-5.2)
**Date:** 2026-08-28
**Status:** Offline-prepared; editor gates HOLD until UE is up

---

## Gate Ledger Summary

| Gate | Status | Date | Evidence |
|------|--------|------|----------|
| runtime | PASS | 2026-08-13 | Owner PIE, real keyboard input, all 4 outcomes |
| save_load | PASS | 2026-08-14 | Canonical BP_JRPGSaveGame slot, process restart |
| repeat_consume | PASS | 2026-08-14 | Flag+reward restore, stat idempotent per IntentId |
| package_launch | PASS | 2026-08-14 | Dev packaged build launches outside editor |
| battle_integration_map | PASS | 2026-08-28 | Live PIE, all 4 outcomes |
| hud_single_writer | PASS | 2026-08-28 | One writer owns HUD, source consolidated |
| rhythm_owner | **OPEN** | — | Needs PIE |
| wardrobe_equip_roundtrip | **OPEN** | — | Needs PIE |
| rhythm_grade_to_result | **OPEN** | — | Needs PIE |
| music_world_key | **OPEN** | — | Needs PIE + BP |
| wardrobe_gameplay_hook | **OPEN** | — | Needs PIE |
| static_gates | **FAIL** | 2026-08-14 | Baseline drift; needs re-run against current content |

---

## Per-Gate Action Plan

### 1. rhythm_owner

**What it proves:** Exactly one rhythm path reaches the JRPG damage calculation. This is about the execution path, not which module a class lives in — MelodiaRhythmHUDWidget and MelodiaRhythmReactivitySubsystem both live in MelodiaCore and are both load-bearing.

**What needs to happen:**
- PIE: Start a battle, trigger Melusina's unique skill, observe rhythm highway
- Verify the damage scalar from rhythm flows through exactly one path to the JRPG damage calc
- Confirm no second rhythm path (no competing subsystem) also writes damage

**Offline preparation:** DONE — the TWeakObjectPtr crash fix (commit `92af496b`) fixed the ACCESS_VIOLATION that was killing PIE when the Ollama callback fired. The profiler traces on StartSession and DriveOceanBeatValues are in place for Unreal Insights.

**Editor-bound:** PIE session with Melusina's unique skill active. Confirm one highway, one damage path, one result.

---

### 2. wardrobe_equip_roundtrip

**What it proves:** Equip -> save -> process restart -> load -> correct outfit and correct materials, through the UMelodiaWardrobeSubsystem API only.

**What needs to happen:**
- PIE: Equip an outfit via UMelodiaWardrobeSubsystem
- Save the game (BP_JRPGSaveGame)
- Restart PIE (or end + restart session)
- Load the save
- Verify the outfit and materials are correct

**Offline preparation:** The C++ automation test `Melodia.Wardrobe.EquipRoundtrip` exists in `MelodiaWardrobeAutomationTests.cpp` (grant -> equip -> unequip -> idempotency). The Python contract test `test_08_wardrobe_equip_sets_flag` verifies the .qsc sets the right flag.

**Editor-bound:** PIE with save/load cycle. The automation test can run via RiderLink if installed, or via `RunTests` console command. Otherwise manual PIE.

---

### 3. rhythm_grade_to_result

**What it proves:** A real-key rhythm grade demonstrably changes a JRPG battle result, and Quill resumes exactly once.

**What needs to happen:**
- PIE: Start a battle, play rhythm with real keyboard input (Q/W/O/P)
- Achieve a grade (Perfect/Great/Good/Miss)
- Verify the grade modifies the battle result (damage scalar, turn outcome)
- Verify Quill resumes exactly once after the battle

**Offline preparation:** The profiler traces are in place. The contract test `test_07_p0_playthrough_has_battle` confirms the .qsc triggers a battle.

**Editor-bound:** PIE with real keyboard input through BP_BattleUI::OnKeyDown. This is the gate that requires the most hands-on playtime — the rhythm input must go through the real widget, not a probe injection.

---

### 4. music_world_key

**What needs to happen:** One world object responds to one played phrase. APCGHeroMusicGraphHost::OnPatternCompleted reaches UMelodiaNarrativeSubsystem as a 7-verb notification. Music opens doors; it never enters the combat or damage pipeline.

**What needs to happen:**
- A world puzzle actor (BP_MelodiaPCGChallengeHost or equivalent) must exist in the level
- The player plays a musical phrase (pattern) on the world instrument
- OnPatternCompleted fires and reaches the narrative subsystem as a 7-verb notification
- A door/object in the world responds (opens, activates, changes)

**Offline preparation:** The notification contract (7 verbs) is verified by `test_qsc_allowlist_contract`. The allowlist carries all needed IDs. However, BP_MelodiaPCGChallengeHost may not exist yet — this was flagged as OPEN in the session review.

**Editor-bound:** PIE with the world puzzle actor. May need BP creation first (editor-bound T3D injection or manual placement). This is the highest-effort remaining gate.

---

### 5. wardrobe_gameplay_hook

**What it proves:** One outfit produces one observable gameplay difference via IMelodiaTraversalCapabilityProvider (Glide/Dash/Swim).

**What needs to happen:**
- PIE: Equip an outfit that grants a traversal capability (e.g., Glide)
- Verify the capability is active (player can glide/dash/swim)
- Unequip the outfit
- Verify the capability is inactive

**Offline preparation:** The C++ automation test `Melodia.Wardrobe.GameplayHook` exists (equip -> glide active -> unequip -> glide inactive). The traversal capability registry and interface are in Source/BS_GodFile/MelodiaIntegration/.

**Editor-bound:** PIE with outfit equip + traversal test. Can run via RiderLink automation test if available.

---

## Recommended Execution Order

1. **Full closed-editor build** — MelodiaShader module is new; Live Coding can't register it. Build first.
2. **Static gates** — `echo_run.py run static_gates` (bp_sweep, bp_live_path, graph_reachability, ui_style_audit, verify_baseline)
3. **rhythm_owner** — PIE, Melusina unique skill, confirm one damage path
4. **rhythm_grade_to_result** — Same PIE session, real keyboard input, grade changes result
5. **wardrobe_equip_roundtrip** — PIE, equip/save/restart/load
6. **wardrobe_gameplay_hook** — Same PIE session or new, equip + traversal test
7. **music_world_key** — PIE, may need BP_MelodiaPCGChallengeHost creation first
8. **Record all gates** — `record_gate.py <id> pass --note "2026-08-28 <evidence>"`

Gates 3+4 can share a PIE session (rhythm). Gates 5+6 can share a PIE session (wardrobe). Gate 7 needs its own setup.

---

## Offline Work Already Done (This Session)

| Item | Commit | Status |
|------|--------|--------|
| TWeakObjectPtr crash fix (NarrativeSubsystem) | `92af496b` | COMMITTED |
| Profiler traces (RhythmCombat + AudioReactive) | `92af496b` | COMMITTED |
| MelodiaShader module wiring (Build.cs + .uproject) | `92af496b` | COMMITTED |
| MelodiaShader source (6 .ush files) | `7b00aa81` | COMMITTED |
| Docs/config/Python tools update | `47eb208a` | COMMITTED |
| Fixtures manifest refresh | `1dd37870` | COMMITTED |
| Contract tests (4/4 + 10/10) | — | PASS |
| .qsc -> .uasset (12/13 compiled) | — | VERIFIED |
| Allowlist (all P0 IDs present) | — | VERIFIED |

---

## What Strictly Needs the Editor

1. Full closed-editor build (MelodiaShader new module)
2. Static gates run (5 tools, all editor-bound)
3. PIE for all 5 open gates
4. `record_gate.py` for each gate after PIE verification
5. Recompile stale .uasset (MelodiaQuillDawnVeil, MelodiaQuillSolsticeDrum) — non-P0 but worth fixing
