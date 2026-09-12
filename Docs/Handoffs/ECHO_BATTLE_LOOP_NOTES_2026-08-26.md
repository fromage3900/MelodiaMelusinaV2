# Echo pipeline + battle-loop iteration notes — 2026-08-26

Six back-to-back battle-session iterations against the `melodia_*` MCP fixture, run
immediately after the `BP_MelodiaJRPGPlayerController` reparent fix landed on disk.

**Scope caveat carried forward:** the `melodia_*` MCP tools are synthetic in-process state,
not live PIE proof. Nothing here records a gate row. Findings below are about the *fixture's*
model of the economy/quest contract, which is still useful because it is what the Echo
`monolith_static` stage and any future automated battle harness would consult.

---

## Controller fix — verified persisted

| Check | Result |
|---|---|
| `compile_blueprint` | `success:true, status:UpToDate, 0 errors, 0 warnings` |
| `get_parent_class` | `BP_JRPGPlayerController_C` (was native `PlayerController`) |
| `playerUnits` CDO | `BP_SirMelodiousPlayerUnit_C` — Melodia roster restored |
| `CursorFxAccumulator` | present, `owner_class: BP_MelodiaJRPGPlayerController_C` |
| Disk mtime | moved `2026-08-20 12:43` → `2026-08-26 23:13:54` |
| Live re-query after save | matches (not mtime-only proof) |

**Ordering trap found:** `compile_blueprint` run *after* `set_cdo_property` wiped the
`playerUnits` override back to empty. The override must be applied **last**, then saved,
with no compile in between. First save shipped an empty map; second save shipped the
correct value.

---

## Static gates — both failures are pre-existing and orthogonal

`echo_run.py run static_gates`: `graph_reachability` ok, `bp_live_path` ok, `ui_lint` ok,
`bp_sweep` FAIL, `verify_baseline` FAIL.

- **`bp_sweep`** — `bp_sweep.py` itself exits 0. The gate fails because `run_bp_sweep`
  (`Tools/echo_run.py:313`) additionally requires `DUPES == 0`. There are ~15 duplicate short
  names, every one a `/Game/Melodia/<path>` vs `/Game/<path>` mirror pair
  (`BP_MelodySlime`, `BP_MelodySlimeBattle`, `BP_Melusina`, `BP_RhythmHUD`, `WBP_RhythmHUD`, …).
  This is the already-documented two-sources-of-truth mirror tree, not new damage.
- **`verify_baseline`** — 16 drifted assets, 39 clean, 0 failed. All 16 are **materials**
  (`M_Master_Toon_Universal`, `MF_Madoka`, `MPC_Melodia_Palette`, …). Zero gameplay assets.

Neither failure touches the controller or the battle loop.

---

## Iteration log

### Run 1 — `hub_run_01` — PASS
23 perfect hits → cast all three families → resolve.
`blocked_enemy: true`, `quest_advancement: true`, quest → **complete**.

**Economy model learned:** grief inversely scales the economy. As grief fell 30 → 13,
mana gain fell `1.30 → 1.135` while healing gain rose `0.85 → 0.9325`. Utility is flat at
`0.3/hit` regardless of grief, which makes utility the hard bottleneck — ~27 perfect hits
to afford one tier-1 `utility_debuff` from zero.

Cast costs: healing 10, mana 10, utility 8.
`healing_song` returns 5 mana; `mana_song` converts 10 mana → 10 grief reduction;
`utility_debuff` drains 15 enemy mana.

### Run 1b — repeat-resolve of `hub_run_01`
Re-resolving the same id returns `resolved / quest_advancement:true` again, but
`resolved_encounters` still holds exactly one entry. **Idempotent at the list level** —
no double-credit. This is the one repeat-consume behaviour that holds.

### Run 2 — `hub_run_02` — PASS
Tested grade scaling and tiers.

- **Accuracy scales every output linearly.** At `accuracy 0.5`: mana `0.65`, healing `0.425`,
  utility `0.15`, grief delta `-0.25` — exactly half of the 1.0 values. Rhythm grade genuinely
  changes the result at the fixture level.
- **Tier scales cost linearly**, and is rejected cleanly when unaffordable:
  `utility_debuff` tier 2 → `required: 16.0, available: 8.2, success:false`.
  `healing_song` tier 3 consumed 30. `mana_song` tier 2 consumed 20 and reduced grief by 20,
  **clamping at 0** rather than going negative.
- Enemy `mana_drain` is a flat `-15` mana, independent of tier or grief.

### Run 3 — `hub_run_03` — correct NEGATIVE
`accuracy 0.0` is a true no-op (all gains `0.0`, grief unchanged). Resolved with no casts →
`blocked_enemy: false`, `quest_advancement: false`. The fixture does distinguish a failed
encounter from a successful one.

**Also found:** `cast_history` is **reset by `encounter_start`**. It is per-encounter, not a
global accumulator.

### 🔴 Defect found after Run 3 — quest completion is not latched

`P0_FirstDream` regressed from **`complete`** back to **`in_progress`** after Run 3, purely
because Run 3 was a failed encounter.

`melodia_quest_check_p0` recomputes `has_combat_skills` from the *current, per-encounter*
`cast_history`, which `encounter_start` had just cleared. A previously-completed quest is
therefore un-completed by any subsequent unrelated encounter. `resolved_encounters` keeps
growing correctly (`hub_run_01, 02, 03`), so the resolve ledger is monotonic — the
*completion verdict* is not.

**Consequence:** these MCP tools cannot be used to prove `repeat_consume`, `save_load`, or
quest persistence. They will report a false negative on a quest that genuinely completed.
This is a fixture defect, not evidence about the shipped C++ path — `CommitQuestCompletion` /
`ConsumeOnce` in `MelodiaNarrativeSubsystem.cpp` is the real authority and has its own native
test. Recording it so a future session does not chase a phantom regression.

### Run 4 — `hub_run_04` — PASS, regression confirmed reproducible
Full 27-hit → three-cast → resolve loop. `quest_advancement: true`, quest returned to
**`complete`**. So the regression is not sticky: completion is simply recomputed from live
state every time it is asked for, in both directions.

### Run 5 — `hub_run_05` — minimal repro + floor test

**Minimal repro of the regression (one tool call, no combat at all):**
`melodia_encounter_start("hub_run_05")` on its own flipped the quest
`complete` → `in_progress`. `encounter_start` clears `cast_history`, `has_combat_skills`
immediately reads `false`, and the completion verdict follows. `resolved_encounters` was
untouched (`hub_run_01..04`), confirming the resolve ledger and the completion verdict are
computed from different, disagreeing sources.

**Floor test:** five consecutive `enemy_action` calls drove mana `59.78 → 44.78 → 29.78 →
14.78 → 0.0 → 0.0`. Mana clamps at 0 correctly and never goes negative. **But
`mana_drained` reports a flat `15.0` on every call**, including the two where the true delta
was `14.78` and `0.0`. The reported drain is the nominal cost, not the applied change — a HUD
bound to that field would show a drain that did not happen.

### Run 6 — `hub_run_06` — error handling + partial-cast negative

- **Unknown encounter id is rejected cleanly:** `resolve("never_started_xyz")` →
  `{"error": "encounter not found: never_started_xyz"}`. No partial state written.
- **`activate_grief_hook` and `encounter_start` are the same lever** — both set grief to a
  flat `30.0`, neither is additive, and running one after the other is a no-op the second time.
- **Failed casts are side-effect free:** `mana_song` tier 1 at 5.0 mana returned
  `success:false, required:10.0, available:5.0` and left every value untouched.
- **Partial cast → correct negative:** resolving with only `healing_song` in history gave
  `blocked_enemy:false`, `quest_advancement:false`. All three families are genuinely required,
  not just any one cast.
- **Balance finding:** `healing_song` returns a flat `5.0` mana **regardless of tier**.
  Tier 2 consumed 20 healing for the same 5 mana as tier 1's 10. Higher healing tiers are
  strictly worse per unit of healing spent, so there is no mana-economy reason to ever cast
  healing above tier 1.

---

## Summary across the six runs

| Run | Intent | Result |
|---|---|---|
| 1 | Full happy path | PASS — quest complete |
| 1b | Repeat-resolve same id | Idempotent — no double-credit |
| 2 | Grade + tier scaling | PASS — both scale linearly |
| 3 | Zero-accuracy / no casts | Correct NEGATIVE |
| 4 | Re-complete after failure | PASS — regression reproducible |
| 5 | Bare `encounter_start` + drain floor | Minimal repro found; mana clamps, reporting off |
| 6 | Error paths + partial cast | Correct NEGATIVE; clean error; balance finding |

The loop is behaviourally consistent and its negative cases are all correct. The one real
defect is the unlatched quest-completion verdict.

## What still needs live PIE (not provable here)

- `rhythm_owner` — needs real Q/W/O/P input reaching `BP_BattleController::DealDamage` once.
- `hud_single_writer` — needs one battle widget + one rhythm surface on screen.
- `battle_integration_map` — needs the reparented controller exercised in
  `MelodiaIntegrationMap` with Melusina actually possessed.
- `BP_MelodySlimeBattle_Hub` is still **abstract** and cannot be spawned, so the slime is not
  yet battle-triggerable in the hub map. Unresolved; no exposed Monolith action clears the
  abstract flag.
