# MelodySlime Tutorial × L_MelusinaMorning — Establish, Test, Integrate

> For Hermes: implement task-by-task, one editor holder at a time.

Goal: Make the authored MelodySlime first-tide chain playable in L_MelusinaMorning with real-input PIE proof.
Architecture: Existing seams only — Quill starts, Phoenix resolves, rhythm grades on top, narrative resumes once. No new battle/material authority.
Tech Stack: UE5.8, Rider + Monolith :9316, QuillScript, stock TurnBased JRPG.

---
Current context (verified 2026-09-18, no new edits):
- Authored chain (commit 5d2685d47): DT_MelodySlime_Skills 24→31 rows; DA_MelodySlimeTutorialSongs "Tide Wave" (12 eighth-notes, 128 BPM); DA_TideWave auto-discovered; BP_MelusinaTidecall mapped in StockSkillRhythmIds 6/6; MelodiaQuillSlimeTutorial.qsc 30 compiled statements; allowlist +encounter/+quest/+flag/+reward saved; MorningIntro voice cues mel_perch_01 + mel_battle_entry compiled; MI_MelodySlime_Body on M_Master_Toon_Character (Tide tint, Chladni, BeatAccent 1.5).
- Tests green: test_melody_slime_datatables_contract PASS; echo static_gates recorded (commit 4b3283255, ledger agent_work_log_2026-09-18_slime_tutorial).
- Placed: BP_MelodySlimeTutorialBattle label exists in Saved/Audit/SceneContext/L_MelusinaMorning/scene_context_latest.json (~line 2274). Roster {slime 1.0, lvl 1}, fleeChance 100.
- Owed (ledger + CURRENT_STATE): (1) tag placed battle actor melodia_slime_tutorial; (2) QSC starter/trigger in Morning; (3) real-input PIE proof victory/defeat/flee + exactly-once resume. Deferred: Tidecall display text, mannequin→slime visual swap, packaged proof.
- Traps live here: actor may sit in sublevel L_Melodia_Dreamstate not the persistent map (check sublevel field); prior session left 242 foreign dirty packages — save ONLY the Morning map; relaxed allowlist passes typos in PIE but fails in shipping.

## Phase 0 — Establish truth (read-only, editor untouched)

### Task 0.1: Read the placed actor from scene context
Files: Saved/Audit/SceneContext/L_MelusinaMorning/scene_context_latest.json (~line 2274).
- Extract BP_MelodySlimeTutorialBattle entry: transform, sublevel, tags, roster props.
- Verify: actor present, note which level/sublevel owns it. If sublevel ≠ persistent, the PIE load plan must include it (it must load at startup or the encounter is absent at runtime).

### Task 0.2: Verify live allowlist truth
- Via Monolith blueprint_query get_cdo_properties on DA_MelodiaIntegrationConfig (never the fixture-returning list tool): confirm EncounterIds has melodia_slime_tutorial (3 total), QuestIds quest.slime_tutorial.first_tide (12), NarrativeFlagIds flag.slime_tutorial.completed (23), DialogueRewardIds reward.slime_tutorial.tidecall (14).
- Verify: counts match ledger; any mismatch stops Phase 1 (re-save the config first).

### Task 0.3: Re-run offline contracts
- Run: python -m unittest Tools.test_melody_slime_datatables_contract -v (expect PASS) and Content.Python.Tests.test_qsc_allowlist_contract -v (expect 4/4).
- Verify: both green on current tree before any editor work.

### Task 0.4: Read MorningIntro starter state
Files: Content/MelodiaIntegration/Narrative/MelodiaMorningIntro.qsc + compiled .uasset; MelodiaQuillSlimeTutorial.qsc (65 lines, Start→battle notify→victory/defeat/fled branches→Finish flag).
- Determine how Morning currently starts Quill (starter actor? trigger? level blueprint?) and where the slime trigger should live (proximity volume near placed battle actor is the locked choice).
- Rider use: Code Vision above UMelodiaNarrativeSubsystem HandleQuillNotification — confirm the seven verbs route battle/quest/reward/flag; Inlay Hints for CDO defaults. Read-only.

## Phase 1 — Wire into Morning (single editor, single MCP writer)

Pre: TASKLIST shows exactly 1 UnrealEditor; netstat 9316 one listener; list_errored_blueprints clean. Duplicate-before-template rule if touching stock assets (prefer overrides on the slime child, never whole-file copies).
- Do NOT hand-edit .uasset; do NOT load_level straight after stopping PIE; MODAL_OPEN in log means blocked, not hung.

### Task 1.1: Open Morning and confirm the actor live
- Open L_MelusinaMorning; confirm BP_MelodySlimeTutorialBattle present with expected transform; read its sublevel field live.
- Verify: live transform matches scene-context file; owner eyeballs placement (height- snapped, no floaters — delegate to world-builder measurement if moved).

### Task 1.2: Tag the battle actor melodia_slime_tutorial
- Set the encounter tag/id to melodia_slime_tutorial (the exact allowlisted EncounterId the QSC notifies).
- Save ONLY the owning map. Verify via list_dirty_packages that no foreign package got saved (the 242-package trap).
- Verify: re-read tag live; mismatch here = silent no-op battle notify later.

### Task 1.3: Add the QSC starter/trigger
- Place/point a trigger (volume or interact) at the slime actor that starts MelodiaQuillSlimeTutorial on player approach; wire through the existing Morning Quill starter path, not a parallel notify bus.
- Verify: trigger fires Start once; replaying after Finish is a no-op path (resolved flag), not a double battle.

### Task 1.4: Tidecall display text
- Confirm BP_MelusinaTidecall shows its tutorial name/text in battle UI (display-text debt from ledger).
- Verify: visible in PIE battle UI, spelled exactly; no second HUD writer.

### Task 1.5: Commit the wiring
- git add -f only if new .uasset paths are gitignored (document as one-time, as before); commit map + qsc + config delta with message feat(slime-tutorial): Morning wiring — tag, trigger, display text; push branch; verify 0 0 vs origin.
- Update CURRENT_STATE.md tutorial paragraph same commit (only status doc).

## Phase 2 — Real-input PIE proof (the gate that matters)

Harness: PIE loop — load_level → run_pie_smoke → start_pie → real keys → pie_get_object_properties → HighResShot → stop_pie. Rider: structured color log, PIE pause/step toolbar; RiderLink gutter once installed, else Monolith calls. Probe-injected subsystem calls are NOT evidence — fingers through BP_BattleUI::OnKeyDown Q/W/O/P only.

### Task 2.1: Victory path, real keys
- Trigger in Morning → Quill Start → battle notify fires → fight with Q/W/O/P lane hits → victory → quest + reward + flag commit in order → Quill resumes exactly once.
- Verify: pie_get_object_properties on BP_BattleController (currentAttackingUnit, currentTurn, isBattleOver) + player controller (gameState, playerUnits); damage delta vs grade visible.

### Task 2.2: Defeat + flee paths
- Defeat → Sir Melodious line, resolved flag, no quest/reward (branch-conditional commit). Flee (fleeChance 100 should allow) → return line, resolved flag, slime keeps rhythm.
- Verify: each branch commits only its authored set; exactly-once resume each.

### Task 2.3: Receipt + ledger row
- Save Docs/Evidence/SLIME_TUTORIAL_MORNING_REAL_INPUT_2026-09-18.json beside stills: state assertions, grade→damage numbers, error counts, harness path. Frames without a JSON report are not evidence.
- Run: python -B Tools/echo_run.py record <gate-id> pass --note ... ONLY after the JSON exists. No ledger row, no claim.
- Verify: gate_ledger.json carries the row; CURRENT_STATE.md reflects PIE-proven (scoped).

## Phase 3 — Further integrate (only after Phase 2 green)

- Visual swap: mannequin → SM_MelodySlime + MI_MelodySlime_Body on owner judgment in viewport (presentation-ready per state; gameplay untouched).
- fleeChance/design: 100 always-escapable suits tutorial — confirm with owner, else tune roster.
- MorningIntro voice timing: mel_perch_01 + mel_battle_entry against trigger walk-up time.
- Packaged proof (cook to G:, omit -map=) stays a separate gate with its own ledger row — never inferred from PIE.

Risks: foreign dirty packages (mitigated: save-one-map + list_dirty_packages check); sublevel not loading at startup (check sublevel field + runtime tag probe); relaxed-allowlist typo passing PIE then failing shipping (verification pass with it off before package); pre-existing BP_BattleController bug only bites outside normal encounter flow — tutorial uses the normal flow.
Open questions: trigger radius + placement (propose 250cm at actor, adjust live); visual swap now or after playtest feel; fleeChance keep 100?
