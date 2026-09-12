# P0 Golden Run — Owner Scorecard (2026-09-06)

Contract: `specs/p0/core_p0_dream_golden_run.v1.json` (status: owner_run_required).
Fill as you play; tick honestly — a failed box is information, not shame.
When done, tell Melusina "golden run done" (or "done with X failed") and the ledger
row + evidence envelope get written from these notes.

## Before you start (1 minute)
- [ ] Other lane's unsaved edits saved or discarded (WBP_MainMenu, MelodiaNarrativeSubsystem .cpp/.h, MelodiaQuillDefeat.qsc) — that session owns them
- [ ] Exactly ONE UnrealEditor.exe running (`tasklist | grep Unreal` → one line)
- [ ] No modal dialog stuck (check popups before PIE)
- [ ] PIE from a NEW GAME / fresh slot — not Continue. Note slot id: ____________
- [ ] Editor process PID before restart: ____________

## Phase 1 — new_game (L_MelusinaMorning)
- [ ] New game entry reachable, fresh slot created
- [ ] Normal input available (move, camera, interact)

## Phase 2 — morning_quill_beat (L_MelusinaMorning)
- [ ] Petal Priestess authored beat visible; dialogue box readable (bg-box fix should show)
- [ ] Choice text readable
- [ ] Harmony intent fires exactly once per choice (watch log: MELODIA_INTENT / harmony)

## Phase 3 — kaleido_nave_departure (travel to L_KaleidoNave)
- [ ] Authored departure completes; travel via allowlist works (no silent no-op)
- [ ] Dreamstate presentation reached
- [ ] Input restored after travel

## Phase 4 — stock_encounter (L_KaleidoNave)
- [ ] One encounter starts (allowlisted)
- [ ] Stock JRPG battle authority drives it (party/turns/damage)
- [ ] Rhythm highway appears on Melusina skill — REAL keys Q/W/O/P, grades change damage
- [ ] One typed result selected (victory/fled/defeat as authored)

## Phase 5 — consequence_and_save (L_KaleidoNave)
- [ ] Quill resumes exactly once after typed result
- [ ] Normal save used (stock save authority); boundary recorded in log

## Phase 6 — process_restart_continue
- [ ] Editor fully exited (PID above) and restarted — PID after: ____________
- [ ] Continue loads the same slot; spawn context correct (map/position/state)
- [ ] Wardrobe/outfit + materials restore visibly (your eyes = ground truth)

## Phase 7 — repeatability (same session, post-continue)
- [ ] Harmony stat NOT duplicated by replaying the beat
- [ ] Quest NOT duplicated; reward NOT duplicated
- [ ] Encounter state consistent

## Notes / oddities (feel-clunk is fine to write here; it's post-P0 polish, not failure)
- 
- 

## Exit criteria (the six that decide the row)
1. route completed without modal/duplicate writer  - [ ]
2. Quill beat visible, advances once per action     - [ ]
3. encounter returns control after one typed result - [ ]
4. save/restart/Continue preserves, never duplicates- [ ]
5. repeatable from fresh slot                       - [ ]
6. no new system needed to explain a failure        - [ ]

Forbidden shortcuts acknowledged: integration-map PIE alone does NOT count;
old 08-13/08-14 envelopes are context only; two-writer runs are void.
