# Master P0 Closeout & Loose Ends — 2026-08-28

**Author:** Melusina (Hermes agent, z-ai/glm-5.2)
**Date:** 2026-08-28
**Status:** Offline work complete; all P0 gates HOLD until editor is up and build completes
**Authority:** This document consolidates all handoff docs from the 2026-08-28 session. It is the single source of truth for the current P0 position. Read this first; read the individual handoffs for detail.

---

## 1. Current P0 Gate Status

**Summary: 6 PASS, 5 OPEN, 1 FAIL — 12 total gates.**

### Gate Ledger

| Gate | Status | Date | Evidence | Source |
|------|--------|------|----------|--------|
| `runtime` | **PASS** | 2026-08-13 | Owner PIE, real keyboard input, all 4 outcomes | `gate_ledger.json` row `owner-realkey-20260813` |
| `save_load` | **PASS** | 2026-08-14 | Canonical BP_JRPGSaveGame slot, process restart | `gate_ledger.json` row `owner-verified-20260814` |
| `repeat_consume` | **PASS** | 2026-08-14 | Flag+reward restore, stat idempotent per IntentId | `gate_ledger.json` row `session-894e8f57` |
| `package_launch` | **PASS** | 2026-08-14 | Dev packaged build launches outside editor | `gate_ledger.json` row `session-894e8f57` |
| `battle_integration_map` | **PASS** | 2026-08-28 | Live PIE on MelodiaIntegrationMap, all 4 terminal outcomes, Quill resumed exactly once | `gate_ledger.json` row `session-7aa8ad8a` |
| `hud_single_writer` | **PASS** | 2026-08-28 | One writer owns HUD; runtime widget identity proven (bidirectional link confirmed) | `gate_ledger.json` row `session-7aa8ad8a` |
| `rhythm_owner` | **OPEN** | — | Needs PIE — confirm exactly one rhythm path reaches JRPG damage | `P0_TASK_LEDGER.json` active_p0_gates |
| `rhythm_grade_to_result` | **OPEN** | — | Needs PIE — real-key grade changes battle result, Quill resumes once | `P0_TASK_LEDGER.json` active_p0_gates |
| `wardrobe_equip_roundtrip` | **OPEN** | — | Needs PIE — equip/save/restart/load cycle through UMelodiaWardrobeSubsystem | `P0_TASK_LEDGER.json` active_p0_gates |
| `wardrobe_gameplay_hook` | **OPEN** | — | Needs PIE — one outfit produces one observable traversal capability | `P0_TASK_LEDGER.json` active_p0_gates |
| `music_world_key` | **OPEN** | — | Needs PIE + BP — BP_MelodiaPCGChallengeHost may need creation; one phrase → one world response | `P0_TASK_LEDGER.json` active_p0_gates |
| `static_gates` | **FAIL** | 2026-08-14 | Baseline drift — 2 material fingerprints (M_Master_Simple_Universal, M_Master_Toon_Landscape_HeightBlend) changed size/node count; needs re-run against current content | `gate_ledger.json` rows 2026-08-14 |

### Phase State

| Phase | Status |
|-------|--------|
| Phase 0 — Hygiene | **CLOSED** |
| Phase 1 — Allowlist & compile | **CLOSED** (2026-08-28, offline proof) |
| Phase 2 — Live-prove four pillars | **OPEN** — editor + PIE required |
| Phase 3 — Rhythm/music gates | **OPEN** — editor + PIE required |
| Phase 4 — Closeout | **OPEN** — one item landed in source (LiveResultsWidgetPath backfill), four remain |

### Critical Caveat

All PASS dates except `battle_integration_map` and `hud_single_writer` are from 2026-08-13/14 — **150+ commits stale**. The `package_launch` pass in particular is the 08-14 baseline and is not current shipping certification. Historical passes apply only to their captured baselines.

---

## 2. Work Done This Session (2026-08-28)

### Commits (6 commits, 43+ files)

| Commit | Scope | Files |
|--------|-------|-------|
| `92af496b` | TWeakObjectPtr crash fix (NarrativeSubsystem), profiler traces (RhythmCombat + AudioReactive), MelodiaShader module wiring (.uproject + BS_GodFile.Build.cs) | 5 |
| `47eb208a` | Docs, config, Python tools, task ledger update | 16 |
| `1dd37870` | Fixtures manifest refresh + model entries | 13 |
| `7b00aa81` | MelodiaShader module source — 6 .ush files (39KB) + .Build.cs + .h + .cpp | 9 |
| `519762e9` | Evening closeout and session router update | — |
| `eb407df3` | Sir Melodious Perch BP design + flight-with-stamina spec | — |
| `d7ccf3a3` | Python tools, handoff docs, Houdini MCP, P0 action plans | — |

### Key Offline Deliverables

| Deliverable | Status | Detail |
|-------------|--------|--------|
| TWeakObjectPtr crash fix | **COMMITTED** | Fixed ACCESS_VIOLATION in NarrativeSubsystem when Ollama callback fired; was killing PIE |
| Profiler traces | **COMMITTED** | TRACE_CPUPROFILER_EVENT_SCOPE on StartSession + DriveOceanBeatValues for Unreal Insights |
| MelodiaShader module | **COMMITTED** | New UBT module (Runtime, PostConfigInit) — 6 .ush shader source files; .Build.cs deps: Core, CoreUObject, Engine, RenderCore, RHI |
| `.qsc → .uasset` compilation | **VERIFIED** | All 5 P0 scripts have valid compiled .uasset, each newer than source |
| Allowlist IDs | **VERIFIED** | All 30+ P0 IDs present in DA_MelodiaIntegrationConfig CDO (QuestIds: 9, NarrativeFlagIds: 17, TravelLevelIds: 4, DialogueRewardIds: 10, SocialStatIds: 3, EncounterIds: 2) |
| Contract tests | **PASS** | `test_qsc_allowlist_contract` 4/4 PASS; `test_p0_content_integration` 10/10 PASS |
| Wardrobe automation tests | **AUTHORED** | `MelodiaWardrobeAutomationTests.cpp` — 4 C++ automation tests (EquipRoundtrip, GameplayHook, SaveLoadRoundtrip, TraversalIntegration) |
| LiveResultsWidgetPath backfill | **IN SOURCE** | `MelodiaUIBridgeSubsystem.cpp:131-133` — requires closed-editor rebuild to take effect |

### Handoff Documents Created (7)

| Doc | Purpose |
|-----|---------|
| `P0_CLOSEOUT_ACTION_PLAN_2026-08-28.md` | Per-gate action plan for all 5 open gates |
| `EDITOR_UP_EXECUTION_CHECKLIST_2026-08-28.md` | Step-by-step editor-up sequence (build → static → PIE → record) |
| `JUNIE_PLAN_IMPLEMENTATION_2026-08-28.md` | Rider/shader lane plan + editor-bound remaining items |
| `SIR_MELODIOUS_PERCH_FLIGHT_DESIGN_2026-08-28.md` | Sir Melodious perch BP + flight-with-stamina system design |
| `UNTRACKED_FILE_TRIAGE_2026-08-28.md` | Full untracked file categorization (safe/editor-bound/junk) |
| `SESSION_REVIEW_ALL_FINDINGS_2026-08-28.md` | Complete findings — 19 loose ends, wardrobe architecture, FGameplayTag migration status |
| `MELUSINA_V23_REBUILD_PLAN_2026-08-28.md` | Melusina v23 Blender → UE rebuild plan |

### Sir Melodious Flight-with-Stamina Design

A complete design for Sir Melodious's traversal system was authored:

1. **SirMelodiousPerch BPs** — Level-placeable anchor points based on `AMelodiaExplorationInteractionVolume` (no new C++ class). Perches serve as visual landmarks, stamina recovery spots (3x regen multiplier), and exploration waypoints. Placeholder mesh for P0; environment-specific variants post-P0.

2. **Flight with stamina cap** — BP-only stamina system on `BP_SirMelodious_Flight` (no C++ header changes for P0):
   - MaxFlightStamina: 5.0s (longer than glide's 3.5s — flight is Sir's primary mode)
   - Drain: 1.0/s, Regen: 2.0/s (faster than glide), RegenDelay: 0.3s
   - PerchRegenMultiplier: 3.0x
   - When depleted: gravity increases to 0.8, Sir falls, must land before takeoff

3. **Recommendation:** Start with Blueprint-only stamina (option b) — no C++ compile needed, can be promoted to native `UMelodiaTraversalComponent` variant post-P0 if the gate passes.

4. **Gate mapping:** Sir's flight is progression-gated (unlocked after rescue), NOT wardrobe-gated. The `wardrobe_gameplay_hook` gate should use a different outfit (Glide/Dash/Swim for Melusina).

**Full detail:** `Docs/Handoffs/SIR_MELODIOUS_PERCH_FLIGHT_DESIGN_2026-08-28.md`

---

## 3. Editor-Up Execution Sequence

**The editor is currently building** (MelodiaShader new module requires a full closed-editor UBT build — Live Coding cannot register new reflected types). When the build finishes, execute this sequence:

### Step 1: Full Closed-Editor Build Verification

```
Build.bat BS_GodFileEditor Win64 Development \
  -project="C:/EnvironmentPortfolio/BS_GodFile/BS_GodFile.uproject" \
  -NoUba -MaxParallelActions=6 -WaitMutex
```

**Verify:**
- [ ] Build completes with 0 errors
- [ ] `Binaries/Win64/UnrealEditor-BS_GodFile.dll` is updated
- [ ] No unity-build symbol collisions
- [ ] MelodiaShader module loads (LoadingPhase=PostConfigInit)

**If build fails:** Check MelodiaShader.Build.cs deps (Core, CoreUObject, Engine, RenderCore, RHI), UE 5.7→5.8 API differences (UserDefinedStruct.h moved to CoreUObject/StructUtils/), unity-build collisions.

**After build succeeds:** Reopen the editor. Verify no Oceanology compatibility modal appears.

### Step 2: Static Gates Run

```bash
python Tools/echo_run.py run static_gates
```

**5 gates:** `graph_reachability`, `bp_live_path`, `bp_sweep`, `ui_style_audit` (ui_lint), `verify_baseline`

**If all 5 pass:** Record to ledger:
```bash
python Tools/record_gate.py static_gates pass --note "2026-08-28 full static chain 5/5 pass after MelodiaShader build"
```

**If `verify_baseline` fails:** The 2026-08-14 baseline drift (M_Master_Simple_Universal 32305→33784 bytes, M_Master_Toon_Landscape_HeightBlend 427468→450364 bytes) may persist. Owner decision: re-freeze the baseline against current content, or fix the material drift.

### Step 3: PIE — Rhythm Gates (shared session)

1. Start PIE on `MelodiaIntegrationMap`
2. Trigger P0 Playthrough (Quill dialogue → encounter)
3. Start battle with Melusina; use her unique skill → rhythm highway
4. **`rhythm_owner`:** Confirm exactly one rhythm path reaches JRPG damage (no competing subsystem)
5. **`rhythm_grade_to_result`:** Play with real keyboard (Q/W/O/P), achieve a grade, confirm it changes the battle result
6. Confirm Quill resumes exactly once after battle
7. Record both:
```bash
python Tools/record_gate.py rhythm_owner pass --note "2026-08-28 PIE: one rhythm path to damage, Melusina unique skill"
python Tools/record_gate.py rhythm_grade_to_result pass --note "2026-08-28 PIE: real-key grade changed battle result, Quill resumed once"
```

### Step 4: PIE — Wardrobe Gates (shared session)

1. PIE on MelodiaIntegrationMap
2. **`wardrobe_equip_roundtrip`:** Equip outfit via UMelodiaWardrobeSubsystem → save (BP_JRPGSaveGame) → restart PIE → load save → verify outfit + materials correct
3. **`wardrobe_gameplay_hook`:** Equip outfit with traversal capability (Glide) → verify capability active → unequip → verify inactive
4. Record both:
```bash
python Tools/record_gate.py wardrobe_equip_roundtrip pass --note "2026-08-28 PIE: equip/save/restart/load correct"
python Tools/record_gate.py wardrobe_gameplay_hook pass --note "2026-08-28 PIE: outfit produces traversal difference"
```

**Alternative:** If RiderLink is installed, run C++ automation tests:
- `RunTests Melodia.Wardrobe.EquipRoundtrip`
- `RunTests Melodia.Wardrobe.GameplayHook`

### Step 5: PIE — Music World Key (separate session)

1. Check if `BP_MelodiaPCGChallengeHost` exists in the content tree
2. If not, create it (T3D injection or manual placement in the level)
3. PIE: play a musical phrase on the world instrument
4. Verify `OnPatternCompleted` reaches `UMelodiaNarrativeSubsystem` as a 7-verb notification
5. Verify a world object responds (door opens, etc.)
6. Record:
```bash
python Tools/record_gate.py music_world_key pass --note "2026-08-28 PIE: one phrase → one world response → 7-verb notification"
```

### Step 6: Final Ledger Check

```bash
python Tools/echo_run.py status
```

**Expected: all 11 gates PASS** (6 existing + 5 newly recorded). If all pass, P0 is CLOSED.

### Execution Order Summary

```
1. Full closed-editor build (MelodiaShader new module)
2. Static gates (5 tools, all editor-bound)
3. PIE: rhythm_owner + rhythm_grade_to_result (shared battle)
4. PIE: wardrobe_equip_roundtrip + wardrobe_gameplay_hook (shared equip)
5. PIE: music_world_key (may need BP creation first)
6. Record all gates to ledger
7. echo_run status — verify all 11 pass
```

**Safety reminders:**
- One editor instance always — check port 9316 has exactly one listener
- MODAL_OPEN in the log is not a hang — grep before concluding the editor is dead
- Never `git clean -fd` or `git checkout -- .`
- Never touch `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python
- Never FBX import into a path that already holds an asset

---

## 4. Loose Ends & Their Status

### 4.1 Critical Loose Ends (block or affect P0 closure)

| # | Item | Status | Detail | Next Action |
|---|------|--------|--------|-------------|
| 1 | `.qsc → .uasset` compilation | **RESOLVED** | All 5 P0 scripts have valid compiled .uasset | None |
| 2 | Allowlist IDs in CDO | **RESOLVED** | All 30+ P0 IDs present in DA_MelodiaIntegrationConfig | None |
| 3 | `BP_MelodiaPCGChallengeHost` not created | **OPEN** | `music_world_key` gate has no host actor | Create in editor (T3D injection or manual) |
| 4 | `LiveResultsWidgetPath` empty | **IN SOURCE** | Backfill at `MelodiaUIBridgeSubsystem.cpp:131-133`; needs closed-editor rebuild | Verify after build |
| 5 | Player death crash (`AnimMontage.h:781`) | **OPEN** | Defeat path crashes editor ~10s after SetHP(0) on BP_SirMelodiousPlayerUnit_C; likely null/invalid death montage | NOT a P0 gate blocker; fix post-P0 |
| 6 | Quill background panel not rendering | **OPEN** | Background panel not rendering in PIE; `ShowBackgroundBox` may need investigation | Out of scope for P0 gates; post-P0 fix |
| 7 | Choral Sheep mesh not skinned | **OPEN** | Companion stays PRESENTATION_ONLY; needs owner-side skinning | Owner-side; post-P0 |
| 8 | Slime/Cosmic Reaver meshes missing | **OPEN** | Enemy meshes missing; `BP_MelodySlimeBattle_Hub` still abstract, cannot be spawned | Owner-side mesh import; post-P0 |

### 4.2 Melusina v23 Rebuild

**Status:** Planning — v23 .blend file not yet found.

The user wants to rebuild Melusina from the v23 Blender source. The current UE assets are functional but the user wants the v23 mesh. The `.melodia_v23*` files found at `C:\Users\froma\` are only 66K (LFS placeholders, not the real ~73MB .blend file).

**Plan:** 5 phases — find V23 source → verify current UE state → export from Blender 5.2 → import to new UE path (NOT over existing) → PIE verify. Full plan at `Docs/Handoffs/MELUSINA_V23_REBUILD_PLAN_2026-08-28.md`.

**Next action:** Filesystem search for the real V23 .blend file (>1MB) across user directories, OneDrive, and EnvironmentPortfolio.

### 4.3 Melody Slime Mesh

**Status:** OPEN — owner-side.

`BP_MelodySlimeBattle` exists but the hub variant (`BP_MelodySlimeBattle_Hub`) is still abstract and cannot be spawned. The slime enemy is the intended pattern enemy but needs a concrete mesh. The canonical path is `/Game/_PROJECT/Characters/Enemies/BP_MelodySlimeBattle` (not the stale `/Game/Melodia/_PROJECT/...` duplicate). `DT_MelodySlime_Enemies` has 48 rows. This is owner-side mesh work, not P0-blocking.

### 4.4 Oceanology Plugin

**Status:** HOLD — awaiting editor boot to confirm native load.

The `.uplugin` is corrected to `EngineVersion: 5.8.0` with matching binary BuildId `55116800`. The plugin should load natively on next editor boot (no compatibility modal). The 2026-08-27 Gate E core pass confirmed: native load, actor spawn, PIE stability, save/close/reopen survival.

**Remaining for Oceanology:**
1. Confirm plugin loads natively on editor boot (LogPluginManager shows `Mounting Project plugin Oceanology_Plugin`)
2. PPV reconciliation on ZenForestTest — live read of PPV state to resolve disagreement between 08-27 live capture and 08-28 material audit
3. Create `MI_Oceanology_NikkiHero` parenting `M_Oceanology` with bioluminescence + Nikki SDF/pearl/glitter MFs
4. Wire `MPC_Melodia_Palette` params into the MI
5. PIE: ocean surface pulses with music, bioluminescence glows on contact

**Authority model:** Oceanology is hero-surface simulation authority in ocean regions ONLY. It is never a second writer on gameplay state. Nikki aesthetic layers on top as MI instances. Full coexistence model in `UNIFIED_PPV_OCEANOLOGY_LOOKDEV_PLAN_2026-08-28.md` §5.

### 4.5 Ink Compile Fix (M_PP_MelodiaInk)

**Status:** OPEN — first editor action after PPV reconciliation.

`M_PP_MelodiaInk`'s Custom HLSL node declares 42 named inputs; 38 are wired, 4 are missing: `SceneColor`, `cR`, `cB`, `smeared`. These are 4 SceneTexture PostProcessInput0 samples (base frame color + three dynamic-UV offsets for print misregistration and motion smear). The graph has zero SceneTexture expressions — the build script that created them was interrupted or a later edit dropped them.

**Fix path:** Run `build_dreamprint_material.py:wire_custom_inputs(mat, custom, force=True)` — this recreates the 4 SceneTextures at correct coordinates, builds the dynamic-UV graph, and wires all 42 inputs. Then recompile, save, and verify via `melodia_material_get_compile_stats`.

**Why it matters:** Once the ink compiles, the audio-reactivity gap closes — the ink is the only material that reads the full 14-param audio set from `MPC_Melodia_Palette` + `MPC_MelodiaInk`. The entire PPV stack becomes audio-reactive through 2 of 4 blendables (Grade + Ink). Ink weight should be re-evaluated from 0.31 → target 1.0 in PIE after the fix.

**Warning:** The simple `_fix_ink_wiring.py` will NOT work — it assumes 4 SceneTextures already exist (`sts[0..3]`). There are none. It would IndexError. Use `wire_custom_inputs(force=True)` instead.

### 4.6 PPV Reconciliation

**Status:** OPEN — first editor action.

Two sources disagree about the live PPV state on ZenForestTest:

| Source | PPV label | Slot 1 | Grade weight | Ink weight |
|--------|----------|--------|--------------|------------|
| Live capture 08-27 | PPV_NikkiDream | MI_StarryNight_Hero @ 1.0 | 1.0 | 0.31 |
| Material audit 08-28 | PPV_Dreamprint_Candidate | MI_StarryNight_VanGogh (MD_SURFACE — BROKEN) | 0.18 | — |

**First editor action:** Read live PPV state through Monolith (`get_level_actors` + property read) to determine which is real. Three possibilities: (1) audit is stale → live capture is correct; (2) someone swapped the stack → re-run hero stack script; (3) two PPV actors exist → remove the old one.

### 4.7 Sea Above Remaining Items

**Status:** OPEN — editor-bound.

The Sea Above cutscene (`MelodiaQuillSeaAboveCutscene.qsc`) is authored and compiled. The `LV_SeaAbove_Prototype` map is in the TravelLevelIds. Remaining:
1. Verify the membrane pulse shader integration (16.0s biological pulse cycle) works in PIE
2. Confirm the travel to `LV_SeaAbove_Prototype` fires correctly from the cutscene script
3. The `flag.sea_above.membrane_pulse_active` flag is authored but needs PIE verification

These are editor-bound and fold into the `music_world_key` PIE session or a separate Sea Above-specific PIE.

### 4.8 Zero-Byte Root Files & .uproject BOM

| Item | Status | Action |
|------|--------|--------|
| Zero-byte root files (`Checking`, `Installing`, `Set`, `uv`) | **OPEN** | Delete — junk from PowerShell redirect |
| `BS_GodFile.uproject` BOM + reindent | **OPEN** | Restore from HEAD to eliminate whole-file churn |

### 4.9 FGameplayTag Migration

**Status:** 1 of 7 subsystems done; 6 pending.

| Subsystem | Status |
|-----------|--------|
| MelodiaWaterGameplaySubsystem | **DONE** |
| MelodiaNarrativeSubsystem | PENDING |
| MelodiaExternalJRPGBridgeSubsystem | PENDING |
| MelodiaExplorationActors | PENDING |
| MelodiaPCGWaterGameplayBridgeComponent | PENDING |
| MelodiaPCGNarrativeChallengeBridgeComponent | PENDING |
| MelodiaBattleMapConfig | PENDING |

**Post-P0.** Each migration is a header change → full closed-editor rebuild.

---

## 5. Post-P0 Deferred Expansion (9 items)

The old nine-item economy expansion is explicitly post-P0. Do not start until P0 is closed.

| # | Item | System | Priority |
|---|------|--------|----------|
| 1 | Define 4 global economy data structs (Healing/Mana/Utility/Grief) | Global Economies | 1 |
| 2 | Grief modifier on rhythm note hits | Grief Hook | 2 |
| 3 | HealingSong (base + 1 scalar tier) | Healing Song | 3 |
| 4 | ManaSong (base + 1 scalar tier) | Mana Song | 4 |
| 5 | UtilitySong_Debuff (mana drain type) | Utility Song | 5 |
| 6 | HUD/WBP for economy inputs and indicators | HUD/WBP | 6 |
| 7 | Economy-focused dungeon route | Dungeon Route | 7 |
| 8 | Debuff/status-pressure enemy | Enemy | 8 |
| 9 | Economy-skill quest chain | Quest Integration | 9 |

---

## 6. Recommended Next Session Priorities

### Priority 1 — Close P0 (editor-up sequence)

1. **Dismiss any editor modal** — check `Saved/Logs/BS_GodFile.log` for `MODAL_OPEN`
2. **Verify the closed-editor build completed** — `UnrealEditor-BS_GodFile.dll` updated, MelodiaShader loaded
3. **Run static gates** — `python Tools/echo_run.py run static_gates` (expect 5/5 pass or diagnose baseline drift)
4. **PIE: rhythm gates** — `rhythm_owner` + `rhythm_grade_to_result` (shared battle session)
5. **PIE: wardrobe gates** — `wardrobe_equip_roundtrip` + `wardrobe_gameplay_hook` (shared equip session)
6. **PIE: music_world_key** — may need `BP_MelodiaPCGChallengeHost` creation first
7. **Record all gates** — `record_gate.py` for each verified gate
8. **Final ledger check** — `echo_run status` shows all 11 PASS → P0 CLOSED

### Priority 2 — Lookdev foundation (same editor session, after P0 gates)

1. **PPV reconciliation** — live read of ZenForestTest PPV state; resolve the audit vs. live capture disagreement
2. **Ink compile fix** — `wire_custom_inputs(force=True)` → recompile → save → verify; re-evaluate ink weight 0.31 → 1.0
3. **Oceanology native load** — confirm plugin loads on boot (no compatibility modal)
4. **Deploy 4-blendable hero stack** to all 5 shipping levels via `finalize_ppv_hero_stack.py`
5. **Create `MI_Oceanology_NikkiHero`** — parent to `M_Oceanology`, wire bioluminescence + Nikki SDF/pearl/glitter MFs

### Priority 3 — Post-P0 cleanup

1. **Re-run `package_launch`** — 08-14 baseline is 150+ commits stale; repackage and verify
2. **Find Melusina v23 .blend** — filesystem search across user dirs, OneDrive, EnvironmentPortfolio
3. **Delete zero-byte root files** — `Checking`, `Installing`, `Set`, `uv`
4. **Fix `BS_GodFile.uproject` BOM/reindent** — restore from HEAD
5. **Retire vestigial Blueprint vars** — `melodiaBattleUI` and `MelodiaUI` are None at runtime but exist as pre-bridge vars; owner decision to remove
6. **Fix player death crash** — `AnimMontage.h:781` null/invalid death montage
7. **Fix Quill background panel** — not rendering in PIE
8. **Complete FGameplayTag migration** — 6 remaining subsystems

### Priority 4 — Sir Melodious implementation (after P0 closed + lookdev stable)

1. **Create `BP_SirMelodiousPerch`** — BP subclass of `AMelodiaExplorationInteractionVolume`
2. **Add BP-only flight stamina** on `BP_SirMelodious_Flight` — timer-based drain/regen, no C++
3. **Place perches in shipping levels** — 3-5 per level at high points and junctions
4. **PIE test** — Ctrl-cycle to Sir, fly to perch, land, verify stamina regen

---

## 7. Reference Document Map

| Document | Location | Role |
|----------|----------|------|
| This document | `Docs/Handoffs/MASTER_P0_CLOSEOUT_AND_LOOSE_ENDS_2026-08-28.md` | **Master consolidation — read first** |
| P0 closeout action plan | `Docs/Handoffs/P0_CLOSEOUT_ACTION_PLAN_2026-08-28.md` | Per-gate detail for 5 open gates |
| Editor-up execution checklist | `Docs/Handoffs/EDITOR_UP_EXECUTION_CHECKLIST_2026-08-28.md` | Step-by-step build → static → PIE → record |
| Junie plan implementation | `Docs/Handoffs/JUNIE_PLAN_IMPLEMENTATION_2026-08-28.md` | Rider/shader lane + editor-bound remaining |
| Sir Melodious perch design | `Docs/Handoffs/SIR_MELODIOUS_PERCH_FLIGHT_DESIGN_2026-08-28.md` | Full flight-with-stamina system design |
| Untracked file triage | `Docs/Handoffs/UNTRACKED_FILE_TRIAGE_2026-08-28.md` | File categorization (safe/editor-bound/junk) |
| Session review — all findings | `Docs/Handoffs/SESSION_REVIEW_ALL_FINDINGS_2026-08-28.md` | 19 loose ends, wardrobe architecture, FGameplayTag status |
| Melusina v23 rebuild plan | `Docs/Handoffs/MELUSINA_V23_REBUILD_PLAN_2026-08-28.md` | Blender → UE character rebuild |
| Unified PPV/Oceanology lookdev | `Docs/Handoffs/UNIFIED_PPV_OCEANOLOGY_LOOKDEV_PLAN_2026-08-28.md` | PPV stack + ink fix + Oceanology integration |
| P0 task ledger | `Docs/P0_TASK_LEDGER.json` | Gate status, phase state, resolved blockers, deferred expansion |
| Gate ledger (echo) | `Saved/gate_ledger.json` | Per-gate evidence rows with dates and notes |
| AGENTS.md | `AGENTS.md` | Project context, working agreement, protocols, conventions |

---

## 8. Single-Rule Reminders

- **QuillScript owns narrative.** TurnBased JRPG template owns combat. `UMelodiaNarrativeSubsystem` is only the narrow bridge. Do not invent parallel authority.
- **A gate is certified only when `record_gate.py <id> pass` has a ledger row.** Prose in a session log is not a ledger row. Probe-injected calls are not play evidence.
- **Rhythm + Quill are owner-locked WORKED.** Do not reopen "highway unverified" or "rhythm never observed." The 2026-08-13 owner-verified real-key pass is ground truth.
- **Every remaining P0 item is editor-bound.** `echo_run status` reports `editor reachable on 9316: no` while the editor is down. Nothing in Phase 2–4 can advance until it is up.
- **Never fabricate a file path.** Never `git clean -fd`. Never `git checkout -- .`. Never FBX import over an existing asset. Never touch `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python.
- **One editor instance always.** Check port 9316 has exactly one listener before any editor work.
