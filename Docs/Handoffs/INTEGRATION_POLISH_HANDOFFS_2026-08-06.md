# Integration-Layer Polish — Agent Handoffs (2026-08-06, evening)

**For:** parallel AI agents polishing the Melodia integration layer
**Editor:** UE 5.8. Build recipe is `-NoUBA` (UBA thrashes RAM and serves stale file states — it is why Live Coding died all day). Editor must be CLOSED to build.
**Read first:** `AGENTS.md` working agreement. **Static graph inspection is not runtime proof** — never report a lane done off a compile, fingerprint, or graph export.

## Hard rules for every lane below

1. **One writer at a time.** Monolith is a single editor connection. If another agent is mutating, you are READ-ONLY.
2. Do not touch `Tests/` — other sessions edit those.
3. Verify every asset write with an **independent readback** (`export_asset_text` / `get_widget_tree`), not the setter's own response. `save_asset` returning `was_dirty:false` has silently no-op'd before.
4. `build_blueprint_from_spec` wires only the **injected subgraph's internal** exec pins. Connecting to pre-existing stock nodes always needs a second `connect_pins` pass. Skipping it is what produced the 5 dead islands that were removed today.

---

## State as of this handoff (verified unless marked)

| Area | State |
|---|---|
| Travel allowlist | Fixed — all 4 route ids in `DA_MelodiaIntegrationConfig` |
| Quill dialogue UI | Renders (owner-confirmed PIE). Root cause was default `100x30` wrapper slots. |
| Double Quill-resume | **Removed** — `BP_MelodiaSirMelodiousMorningIntro` no longer binds `OnBattleCompleted`; `HandleBattleCompleted` graph deleted |
| Reward listener | **Wired** — `UMelodiaPersonaSubsystem::HandleRewardRequested` + `UMelodiaPersonaContent::RewardEquipment` map (3 entries seeded) |
| Rhythm chart | `DA_MelodiaSongs` exists — 192 notes, 64 beats, 128 BPM, parsed from the real MIDI |
| Rhythm highway | Created→viewport(z90)→cast→stored→`BindRhythmHUD`→shown in `BP_BattleUI`; removed + `InvalidateSession` on hide |
| Damage scaling | Both `DealDamage` sites read `GetPendingDamageMultiplier()` |
| §3a StartSession seam | `UseMP → StartSession("cadence_strike") → Branch(>0) → UseSkill` |
| Lane input `OnKeyDown` | **DONE** — D/F/J/K → `RegisterLaneHit(0..3)`, compiles 0e/0w, saved 23:45. One known defect, see Lane A |
| Grade feedback | **DONE** — `RegisterLaneHit` calls `SetJudgment` (PERFECT/GREAT/GOOD/MISS) |
| Skill→rhythm-id resolution | **PARTIAL** — `StockSkillRhythmIds` + `ResolveRhythmSkillId()` exist; map is EMPTY and BP still passes a literal, see Lane C |
| 22 dead nodes + 2 `UToolMenus::Get` | Removed from `BP_BattleController` |

---

## Lane A — `BP_BattleUI::OnKeyDown` — BUILT, one defect left (P1)

Graph exists and is saved. Shape:

```
OnKeyDown → GetKey(InKeyEvent)
  → Branch(key==D) → RegisterLaneHit(0)
  → else Branch(key==F) → RegisterLaneHit(1)
  → else Branch(key==J) → RegisterLaneHit(2)
  → else Branch(key==K) → RegisterLaneHit(3)
  → Return(Handled)
```

**KNOWN DEFECT, do not ship as-is:** with a single return node this returns **Handled for every key**, swallowing all keyboard input to the battle UI. Latent today (nothing else uses battle keys — `IMC_MelodiaDefault` was empty before the lane actions), but it must be gated before any other battle hotkey exists. Fix with a `Select` (True=`Handled`, False=`Unhandled`) driven by a bool set in the lane paths. Monolith's second `Return` node does **not** get a `ReturnValue` pin synced, so a two-return solution is not reachable through MCP — author it in-editor or use the Select.

Gotchas already paid for: `GetKey`'s input pin is `Input`, not `Key`. `blueprint_query save_asset` failed on this asset; `editor_query save_packages` worked — they are not equivalent.

**Verify in PIE, not statically:** press D/F/J/K during a battle and confirm `MELODIA_RHYTHM lane=N` in the log.

## Lane B — Focus hazard (P0, blocks Lane A being real)

`BP_ActionButton`'s `IsFocusable` default was never confirmed. `UButton` defaults to focusable. If a command button holds focus during a rhythm session it will **swallow D/F/J/K before `OnKeyDown` ever fires**.

Check `BP_ActionButton` + `BP_ActionsUI` for `IsFocusable` and any `SetKeyboardFocus`. If focusable, either un-focus them while `EMelodiaInputContext::Rhythm` is active, or call `SetKeyboardFocus` on the battle UI at session start. **This was the single biggest unverified risk in the rhythm path as of 2026-08-06 — superseded by the 2026-08-12 owner lock confirming rhythm input WORKED in live PIE.**

## Lane C — Skill→SkillId mapping — PLUMBING DONE, DATA EMPTY (P0)

The C++ landed: `UMelodiaIntegrationConfig::StockSkillRhythmIds` (`TMap<FName,FName>`) + `UMelodiaRhythmCombatSubsystem::ResolveRhythmSkillId(const UObject*)` (BlueprintPure). Key is the **runtime generated class name** (`BP_FocusAttack_C`), value is a rhythm id. Unmapped → `NAME_None` → `StartSession` returns 0 → stock skill resolves normally, no branch needed.

**Two things remain:**
1. **Seed the map** on `DA_MelodiaIntegrationConfig`. It is currently empty, so every skill resolves to `None`.
2. **Repoint the BP pin.** `BP_BattleController` `K2Node_CallFunction_196` (`StartSession`) still has `SkillId` as the literal `"cadence_strike"`. Feed it from `ResolveRhythmSkillId(currentSkill)` instead — until then *every* skill runs the Cadence Strike chart.

The 8 ids: `cadence_strike`, `resonant_arc`, `lullaby_mend`, `downbeat_break`, `dissonant_silence`, `tempo_shift`, `crescendo_wave`, `harmony_shield`.

Known stock skill BPs: `BP_FocusAttack`, `BP_Thunderbolt`, `BP_BasicHeal`, `BP_GreatHeal`, `BP_FullHeal`, `BP_MeteorStorm`, `BP_TrueStrike`, `BP_DoubleHit`, `BP_FireBall`.

## Lane D — Rhythm/damage timing (P1)

Both branch outputs currently go to `UseSkill`, so the rhythm session runs **in parallel** with the skill montage — and the montage always wins. Measured from the assets: all four template attack montages are `1.2999833s` with their damage anim-notify at **0.500–0.516s**, while a Cadence Strike session ends at **~3.05s** (`TempoBPM=128` → 0.46875 s/beat; `IntroBeats=2` + `ActiveBeats=4` = 6 beats, + 0.5 `ExpiryGraceBeats`). The notify fires roughly **2.5s before** `FinishSession` latches the multiplier, so in the parallel wiring every rhythm-scaled hit currently lands **unscaled** — this is not a race, it is a deterministic loss.

Correct fix: gate `UseSkill` on the `OnRhythmComplete` broadcast instead of firing it immediately on the True branch. Note Monolith's `add_node` has **no `CreateDelegate`**, so BP-side delegate binding is not reachable through MCP — do this in C++ or author it in-editor by hand.

## Lane E — Grade feedback — DONE for judgment, rest still unwired (P2)

`RegisterLaneHit` now calls `SetJudgment(GradeToText(Grade))` on `BoundHUD` for every press (PERFECT/GREAT/GOOD/MISS).

Still unwired in the authoritative path: `PushFloatingCombatText`, `TriggerDamageFlash`, `ShowBattleStatus`, `SetEnemyVitals`, `SetPartyVitals`, `SetSkillPoints`, `SetUltimateGauge`, `SetEnemyBreakGauge`. Every existing call site for these is in **quarantined MelodiaCore** (`MelodiaBattleSession.cpp`, `MelodiaGameMode.cpp`) and does not run in the JRPG-authoritative loop. `PushFloatingCombatText` carries a `Tint`, so it is the natural surface for crit/grade-coloured damage numbers — `BP_DamageTextUI` has no crit concept at all.

## Lane F — Save leg (P0, independent of rhythm)

Two defects, both precisely located, both block the save gate:

1. `BP_MelodiaJRPGGameInstance::OnNewGameStarted` execs only `RegisterSkill` x3 and stops. The stock `CreateSaveGameObject → Set jRPGSaveGame_0` chain is reachable **only** via `Array_Add (AddInteractions) → UToolMenus::Get → CreateSaveGameObject`. On a cold session the first save finds the object null and **writes no file at all**. Reconnect `OnNewGameStarted` into the stock chain and delete the stray `UToolMenus::Get` (same editor-only-class-in-runtime-graph pattern already purged from `BP_BattleController`).
2. Slot names do not intersect: writers use `"0"/"1"/"2"` (`BP_SavePointBase`) and `"MelodiaJRPGSlot0"`; readers use `"MelodiaJRPGSlot0"` and `"MelusinaSlot0"` — the last is written by nothing. Unify on one string.

Supporting: `ConsumedRewardIds` is `SaveGame`-flagged and genuinely persistable, so idempotence fails because of 1 and 2, not the guard. `Btn_Continue`/`Btn_LoadGame` re-enable themselves on `Construct` once the slot file exists — the "deliberately disabled" gate self-defeats the moment saving works.

## Lane G — Chart quality (P2)

Lane histogram on the current chart is **65 / 24 / 32 / 71**. That is `Pitch % 4` on an arpeggio: pitch classes repeat, lanes clump, lane 1 is nearly empty. It will play lopsided. `UMelodiaMidiParser` supports `EMelodiaLaneMode::ChordVoiceIndex` as an alternative, or add a lane-balancing pass. Decide before authoring more songs — it changes how every chart feels.

## Lane H — Two HUD authorities (P2)

`UMelodiaUIBridgeSubsystem` (`BP_MelodiaBattleUI`) and `UMelodiaJRPGBattleOverlaySubsystem` (`BP_MelodiaRhythmPrompt`) both `AddToViewport` at **z-order 100** on the same battle triggers. The rhythm highway was placed at z90 to sit under both. A third authority — the stock battle widget — is still unidentified (`_VERTICAL_SLICE_SCOPE.md` gate "Identify the instantiated stock battle widget package at runtime" is still unchecked). Resolve to one owner.

---

## Environment gotchas that have cost real time

- **Disk sat at 99%** today; a save failing on a full disk is the signature of the 5 assets quarantined on 07-30 for "truncation/header damage". `BS_GodFile\Intermediate` is ~12 GB and is pure build artifact — safest reclaim.
- **`.mcp.json` API keys are in git history** (deepseek-v4, kimi-k3). File is untracked now; **keys still need rotating by the owner** — cannot be delegated.
- `InputMappingContext.mappings` is **deprecated** in UE 5.8. Writing it silently no-ops; the live field is `DefaultKeyMappings.mappings`. This nearly shipped four dead lane bindings.
- Monolith param names are inconsistent: `add_variable` wants `name`/`type`, `remove_function` wants `name`, `connect_pins` wants `source_node`/`target_node`, `set_node_property` wants `path`, `run_python` wants `command`. Read the error — it names the expected key.
- `add_node` needs short type names (`VariableSet`, `cast`), **not** `K2Node_` prefixes. The prefix silently falls through to a generic fallback that produces a malformed node.
