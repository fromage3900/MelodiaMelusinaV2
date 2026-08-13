# A1 — Stock Battle Path PIE Checklist (2026-08-12)

**Goal:** Verify that the First Dream route reaches and completes one stock JRPG encounter in PIE.
**Route:** `L_MelusinaMorning` → `L_KaleidoNave`
**Encounter:** actor tagged `melodia_smoke_encounter` + `BP_BattleController` + stock `StartBattle` contract

## Preconditions

- [ ] Water-system-polish lane has released the editor (no other agent holds it).
- [ ] Exactly one `UnrealEditor.exe` process.
- [ ] Monolith MCP responsive on `127.0.0.1:9316`.
- [ ] Closed-editor C++ build green (if any C++ changed since last editor start).
- [ ] `Content/EnvSandbox/Environments/L_KaleidoNave.umap` saved and not dirty from another lane.

## Static entry checks (run first)

```powershell
cd C:\EnvironmentPortfolio\BS_GodFile
python Tools/battle_path_static_audit.py
python Tools/playtest_harness.py preflight
python Tools/playtest_harness.py check-wiring
```

Expected:
- `battle_path_static_audit.py` → assets present, levels present, Monolith reachable.
- `preflight` → `unreal_editor_processes: 1`, `monolith_reachable: true`.
- `check-wiring` → status `RAW_KEY_BACKEND` or `ENHANCED_INPUT_BACKEND`, not `UNWIRED`/`MISSING`.

## PIE execution

### 1. Launch PIE on KaleidoNave with the persona probe

Use `Tools/playtest_harness.py` or a targeted PIE smoke:

```powershell
python Tools/playtest_harness.py run --map /Game/EnvSandbox/Environments/L_KaleidoNave --backend auto --keys Q W O P --duration 45 --capture-clip
```

Watch the editor log for:
- `MELUSINA_LOOP_PROBE tagged_count=1 tagged_classes=[BP_InteractionBattle_C]`
- `MELUSINA_LOOP_PROBE quill_started`
- `MELUSINA_LOOP_PROBE after_quill pending=true ... bridge_active=true`
- `MELODIA_RHYTHM` without `no rhythm id mapped`
- `ShowBattleUI` / `ShowRhythmGrade` / lane registration
- No `Accessed None` crash on `ABP_Melusina_WaterHair` (pre-existing, not fatal).

### 2. Confirm battle starts

Evidence required (any one is enough to claim A1 reachable):
- `BP_BattleController` spawned in PIE world.
- Battle UI (`BP_MelodiaBattleUI`) added to viewport.
- Rhythm highway notes visible.
- One turn resolves (hit, damage number, enemy HP change).

If battle does **not** start, record the exact fail point:
- Does the encounter actor exist? (`tagged_count`)
- Does `BP_BattleController` exist in the level? (`controllers`)
- Does `StartBattle` CustomEvent fire? (log / graph)
- Does the bridge `is_jrpg_battle_active()` return true?
- Is there a widget-construction failure? (`check-wiring` output)

### 3. Capture evidence

Save to `Saved/Audit/battle_path_<timestamp>/`:
- `report.json` from playtest harness
- Editor log excerpt (`Saved/Logs/BS_GodFile.log`)
- At least one screenshot showing battle UI or highway

## Success criteria

A1 is **PASS** if:
- PIE boots `L_KaleidoNave` without crash.
- Exactly one `melodia_smoke_encounter` actor is found.
- `BP_BattleController` is present.
- Battle UI appears.
- At least one turn resolves or the battle state advances meaningfully.

A1 is **FAIL (documented)** if:
- A clear single failure point is identified and recorded.
- The failure point becomes the next P0 fix.

## Next gates after A1 PASS

1. **Victory/Defeat/Fled/unavailable result matrix** — run the battle to each terminal state and verify Quill resumes/aborts exactly once.
2. **Canonical save/load across restart** — `Pause → Save → Quit → Reload`.
3. **Input parity** — mouse, keyboard, controller for Attack/Skill/Item/Flee.
4. **Launch packaged build** — run `BS_GodFile.exe` outside editor.

## Anti-rules

- Do not reopen rhythm-highway or Quill “unverified” claims — both are owner-locked WORKED.
- Do not delete `_ThirdParty` or duplicate UI trees without owner sign-off.
- Do not run a second UnrealEditor instance.
- Do not hand-build engine data structures (song map, etc.).
