---
name: melodia-p0-closeout
description: P0 closeout runbook for BS_GodFile UE5.8 — Phase 1 allowlist+compile, Phase 2 live-prove four pillars, Phase 3 rhythm/music/wardrobe gates, Phase 4 closeout.
---

# Melodia P0 closeout

Operational runbook for closing P0 on `BS_GodFile` UE 5.8. This lane owns the active P0 gates — the
editor-bound closeout work that turns the 08-27 authored content into certified shipping evidence.

## 0. Scope guard

- **Do not hand-edit `.uasset`.** All asset mutations go through the editor (Monolith/editor_query).
- **One editor, one MCP surface.** `Get-Process UnrealEditor` single instance; one listener on 9316.
- **P0 is not closed until the gates are recorded.** `Saved/gate_ledger.json` rows are the evidence.
- **Phase 1 must land before Phase 2.** The 08-27 content commit is inert until the allowlist is
  extended and the 5 `.qsc` are compiled — see `Docs/Handoffs/P0_ALLOWLIST_DELTA_FOR_RIDER_2026-08-28.md`.
- **Subscription to existing authority only.** QuillScript owns narrative. The stock JRPG template
  owns party/turns/damage/results/saves. MelodiaCore is presentation-only this phase.

## 1. The P0 closeout phases (from `Docs/P0_CLOSEOUT_PLAN_2026-08-28.md`)

### Phase 0 — Hygiene (done this session, no editor)

- [x] 4 zero-byte root files gone.
- [x] `BS_GodFile.uproject` clean — only HoudiniEngine + VRM4U enabled.
- [x] QSC authoring defects fixed in working tree (`flags.` → `flag.`, duplicate reward grants removed).
- [x] `Saved/gate_ledger.json` + `Saved/gate_ledger_report.md` synced to 08-27 handoff.
- [x] `Docs/Handoffs/P0_ALLOWLIST_DELTA_FOR_RIDER_2026-08-28.md` + `.json` written.

### Phase 1 — Make the authored content real (editor, Juno's queue)

- [ ] **Extend `DA_MelodiaIntegrationConfig`** with the 27-ID delta. Read truth with
  `blueprint_query get_cdo_properties`, not `melodia_config_get_allowlist`.
  - 5 QuestIds: `quest.first_dream`, `quest.wardrobe.equip_outfit`, `quest.companion.choral_sheep`,
    `quest.cutscene.sea_above`, `quest.harmony_awakening`
  - 13 NarrativeFlagIds: `flag.first_dream.quest.completed`, `flag.p0.playthrough.completed`,
    `flag.p0.playthrough.attempted`, `flag.p0.playthrough.fled`, `flag.wardrobe.outfit_equipped`,
    `flag.wardrobe.equip_completed`, `flag.melusina.sorrow_seam_restored`, `flag.companion.choral_sheep_recruited`,
    `flag.companion.choral_sheep_completed`, `flag.cutscene.sea_above_witnessed`,
    `flag.sea_above.membrane_pulse_active`, `flag.cutscene.sea_above_completed`, `quest.harmony_awakening.completed`
  - 5 DialogueRewardIds: `reward.first_resonance_echo`, `reward.wardrobe.first_outfit`,
    `reward.companion.choral_sheep`, `reward.cutscene.sea_above_memory`, `reward.harmony_awakening`
  - 2 SocialStatIds: `melodia_elegance`, `melodia_resonance`
  - 1 TravelLevelIds: `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`
- [ ] **Compile the 5 `.qsc` → `.uasset`** (4 P0 + `MelodiaQuillHarmonyAwakening`). Confirm each loads.
- [ ] **Verify offline:** `python -m unittest Content.Python.Tests.test_qsc_allowlist_contract -v` → 4/4 PASS.

### Phase 2 — Live-prove the four pillars (editor + PIE)

- [ ] **P0 Playthrough** — victory branch end-to-end. Verify atomic commit order + Quill resumes once.
- [ ] **Wardrobe equip → `wardrobe_equip_roundtrip`** — equip, canonical save, **full process restart**,
  load, confirm outfit + materials restore.
- [ ] **Glide → `wardrobe_gameplay_hook`** — one equipped item, one observable capability.
- [ ] **Choral Sheep** — script-side proof only (companion `PRESENTATION_ONLY` until mesh skinned).
- [ ] **Sea Above** — travel, membrane pulse, droplets (requires `LV_SeaAbove_Prototype` in `TravelLevelIds`).

### Phase 3 — The remaining rhythm gates

- [ ] **`rhythm_owner`**: prove at runtime that exactly one path reaches stock damage — confirm battle UI
  calls `UseSkillWithRhythm`, not stock `UseSkill`.
- [ ] **`rhythm_grade_to_result`**: real-key timing changes a stock result, progression never blocks,
  Quill resumes once.
- [ ] **`music_world_key`**: attach `UMelodiaPCGNarrativeChallengeBridgeComponent` to a host actor in a
  level, prove one Piano phrase commits one idempotent typed result and visibly opens a route.

### Phase 4 — Closeout

- [ ] Owner decision: retire the two vestigial `melodiaBattleUI` / `MelodiaUI` vars → `hud_single_writer`
  fully closed.
- [ ] Owner decision on the two material drifts → re-freeze or revert → rerun full static chain with
  editor up → `static_gates`.
- [ ] Fix `LiveResultsWidgetPath` by mirroring the `MelodiaBattleWidgetPath` backfill in `Initialize()`;
  bundle with any other C++ change so the closed-editor rebuild is paid once.
- [ ] Repackage and rerun `package_launch` against current content (standing pass is 08-14 baseline,
  150+ commits stale).
- [ ] Full 20–30 minute golden run, then record the ledger rows.

## 2. The gate ledger — this is what closes gates

- `python -B Tools/echo_run.py status` — free, offline, check this first.
- `python -B Tools/echo_run.py run static_gates` — runs `graph_reachability`, `bp_live_path`,
  `bp_sweep`, `ui_lint`, `verify_baseline`.
- `python -B Tools/echo_run.py record <gate> pass|fail --note "..."` — **this is the only thing that
  closes a gate.** No ledger row, no claim.
- Live proof uses the PIE loop from `melodia-p0-loop` skill §4 — load_level → run_pie_smoke →
  poll_pie_smoke → start_pie → pie_call_function → pie_get_object_properties → run_console_command
  HighResShot → stop_pie.
- Runtime reads that constitute real proof: `BP_BattleController` (`currentAttackingUnit`,
  `jRPGPlayerController`, `melodiaBattleUI`, `currentTurn`, `isBattleOver`), player controller
  (`gameState`, `isExplore`, `exploreCharacter`, `playerUnits`, `partyMembers`, `isInputBlocked`).

## 3. The allowlist delta (machine-readable)

`Docs/Handoffs/P0_ALLOWLIST_DELTA_FOR_RIDER_2026-08-28.json` — the 27 IDs grouped by set. Read live
truth with `blueprint_query get_cdo_properties`, never `melodia_config_get_allowlist` (returns stale
fixture data per `P0_TASK_LEDGER.json` → `tooling_traps`).

## 4. The four pillars (what to live-prove)

### P0 Playthrough (`MelodiaQuillP0Playthrough.qsc`)

- Victory branch end-to-end.
- Atomic commit order on 08-27 victory branch: `melodia:quest:melodia_q_echo_01`, then
  `melodia:reward:melodia_smoke_reward`, then `melodia:flag:melodia_smoke_complete:true`, then
  `Script 'MelodiaQuillSmoke' ended`.
- Quill resumes exactly once per outcome.
- Fled branch commits only the flag (no quest/reward) — branch-conditional commit.

### Wardrobe equip (`MelodiaQuillWardrobeEquip.qsc`)

- Equip the Resonant Weave, grant `item.outfit.melusina_v2`, set `flag.wardrobe.outfit_equipped` +
  `flag.melusina.sorrow_seam_restored`, then `questcomplete` with reward `reward.wardrobe.first_outfit`.
- Roundtrip: equip → canonical save → **full process restart** → load → confirm outfit + materials
  restore.
- Capability: Glide (from `specs/wardrobe/wardrobe_equip_p0_manifest.v1.json`).

### Choral Sheep (`MelodiaQuillChoralSheepRecruit.qsc`)

- Script-side proof only. Companion stays `PRESENTATION_ONLY` until mesh is skinned.
- Stat: `melodia_harmony:2`. Flags: `flag.companion.choral_sheep_recruited` +
  `flag.companion.choral_sheep_completed`.

### Sea Above (`MelodiaQuillSeaAboveCutscene.qsc`)

- Travel to `LV_SeaAbove_Prototype`, membrane pulse (16.0s cycle), droplets.
- Requires `LV_SeaAbove_Prototype` in `TravelLevelIds`.
- Flags: `flag.cutscene.sea_above_witnessed` + `flag.sea_above.membrane_pulse_active`.
- Stat: `melodia_resonance:5`.

## 5. The remaining gates (Phase 3 + Phase 4)

### `rhythm_owner`

- Prove at runtime that exactly one path reaches stock damage.
- Confirm battle UI calls `UseSkillWithRhythm`, not stock `UseSkill`.
- The stock-skill rhythm seam is already single-path and correct in source:
  `UseSkillWithRhythm → ApplyRhythmAttackScalar() → InvokeStockUseSkill`, scalar folded into
  attacker stats **before** dispatch.

### `rhythm_grade_to_result`

- Real-key timing grade changes a stock JRPG result.
- Progression never blocks.
- Quill resumes exactly once.
- Requires a live battle with a running Quill interpreter + real keys through
  `BP_BattleUI::OnKeyDown` (Q/W/O/P → `RegisterLaneHit`).

### `music_world_key`

- Attach `UMelodiaPCGNarrativeChallengeBridgeComponent` to a host actor in a level.
- Prove one Piano phrase commits one idempotent typed world result.
- Visibly open one player-facing route.
- `UMelodiaPCGNarrativeChallengeBridgeComponent` is source-built but no level/Blueprint attaches it
  to a host actor — the whole blocker is wiring, not code.

### `wardrobe_equip_roundtrip` + `wardrobe_gameplay_hook`

- Equip → canonical save → **full process restart** → load → confirm outfit + materials restore.
- One outfit → one observable capability (Glide is the locked first-slice choice).
- The live pawn `BP_MelusinaJRPGCharacter` already carries `MelodiaWardrobeComponent`,
  `MelodiaTraversalComponent`, `MelusinaSorrowSeamComponent` + the V2 body/shirt/skirt/boots/accessory
  meshes. `FMelodiaNarrativeRecord` already has `SaveGame`-tagged `EquippedCosmeticIds` (Decision 043).

### `static_gates`

- Full blueprint/UI/material chain not rerun.
- Two material drifts against 2026-08-07 baseline: `M_Master_Simple_Universal` 25→26 nodes,
  `M_Master_Toon_Landscape_HeightBlend` 290→304 nodes.
- Owner call: re-freeze if intended, revert if not. Rerun full static chain with editor up.

### `hud_single_writer`

- Runtime widget identity proven 08-27: `BP_BattleController.battleUI = BP_BattleUI_C_0`,
  that widget's `battleController = BP_BattleController_2`, MATCH=True.
- Two vestigial vars (`melodiaBattleUI`, `MelodiaUI`) — both None, pre-bridge Blueprint vars in
  category 'Melodia'. Owner decision to retire them is cleanup, not a gate blocker.

## 6. Evidence standard (the contract)

1. A gate is certified only when `record_gate.py <id> pass` has a ledger row. Prose in a session
   log is not a ledger row.
2. Probe-injected calls are not play evidence — they prove the native seam responds when invoked,
   not that a player pressing keys sees a highway.
3. Frames without a report are not evidence. PNG captures with no accompanying JSON assertion report
   and no committed verifier cannot be re-checked.
4. The committed harness must be the harness that ran. Fix the probe, then rerun. Never paper over it.
5. A committed export is an output, not an input. Verifiers re-derive from the live graph every run;
   do not assert against a stored export (the one exception is `bp_regression_checker.py`, whose
   baseline is tracked at `Docs/T3D_Baseline/bp_fingerprints.json` and hard-fails when missing).

## 7. When to use

- Driving Phase 1 (allowlist + compile) in the editor.
- Live-proving the four pillars in Phase 2.
- Proving the remaining rhythm gates in Phase 3.
- Closing out in Phase 4 (ledger rows, repackage, golden run).
- Re-running the contract tests to confirm Phase 1 landed.

## 8. When NOT to use

- Building new subsystems (P0 is convergence and proof, not construction).
- Adding a fifth wardrobe track, a fourth rhythm path, or a second HUD writer.
- Claiming a gate closed from prose, probe calls, or screenshots without assertion reports.
