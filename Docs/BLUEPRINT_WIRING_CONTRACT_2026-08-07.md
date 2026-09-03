# Blueprint Wiring Contract — Canonical Source of Truth

**Created:** 2026-08-07
**Last corrected:** 2026-08-08 (§1 tool selection was wrong — see the note in that section)
**Status:** Verified against live source headers (MelodiaIntegration + MelodiaCore plugin)
**Supersedes:** All prior wiring handoffs where they conflict (DeepSeek 08-03, Kimi 08-03, Cline 08-06)

> **READ THIS FIRST.** Every API name, enum value, and struct field below was verified
> against the actual `.h` files on 2026-08-07. If a handoff contradicts this document,
> **this document wins.** If you believe this document is wrong, re-verify against the
> source header before changing anything — do not trust a newer handoff over source.
>
> That rule cuts both ways: §1 of this document was itself wrong for a day, and because
> this document outranks handoffs, nothing downstream could correct it. **Source and the
> live graph outrank this document.** Re-derive rather than trusting any doc, including
> this one.

### Status as of 2026-08-08

Verified against the live graph, not against handoffs:

- **B3, B4, B7 are wired and done.** `verify_battle_closure.py` reports 10/10 invariants on the
  live battle controller (`Exports/bp_battlecontroller_eventgraph_live.json`).
  `UseSkillWithRhythm` is wired through `UseMP` → node → `HideSkillButtons` with
  `StockSkill ← currentSkill`; the `Switch` → `Sequence_3/4/5` → `CompleteBattle` legs and the
  damage latch are all present.
- **B7 is not a stub.** `ShowRhythmGrade` is implemented (Entry → ToText → SetText on
  `RhythmGradeText`) with the exact C++-expected signature. The 08-07 "stub" finding predates
  the work and is withdrawn.
- **Sir-departure authority** is the compiled MorningIntro script:
  `melodia:battle:melodia_smoke_encounter` → typed result → `melodia:flag:melodia_smoke_complete`
  → `$ End`. `HandleMorningIntroEnded` and `BeginWindowDeparture` are **verified-disconnected
  legacy** — do not wire to them.
- **B6 reward gap** is already fixed in the author script.
- The **7 `OpenLevel` sites** use the travel-provider pattern with a documented fallback.

Still open: these prove the graph is **connected**, not that the loop **plays**. The rhythm
session has not yet been observed in PIE moving beat and grade. Do not read 10/10 as "the
minigame works."

---

## 1. Tool Selection (the #1 cause of failed wiring)

> **CORRECTED 2026-08-08.** The previous version of this section said `ueblueprintmcp` was "the
> ONLY server that can read/write an EventGraph" and that "Monolith and it-is-unreal cannot add
> or connect Blueprint nodes." Both claims were false, and because this document outranks every
> handoff, they routed agents to a server that is not running while telling them the two that
> are could not do the job. If you were sent here by an older handoff expecting
> `ueblueprintmcp`, read the table below instead.

| Task | MCP Server | Why |
|---|---|---|
| **Blueprint graph wiring** (nodes, pins, compile) | **`monolith`** | Atomic T3D authoring: `validate_nodes_t3d`, `inject_nodes_t3d`, `set_node_property`, `export_graph`, `get_graph_fingerprint`, `assert_graph_matches`, `compile_blueprint`, `save_asset`. See `Plugins/Monolith/Docs/MONOLITH_GUIDE.md` Recipes 15–16 and the five committed patterns in `Docs/T3D_Patterns/`. |
| Material / PCG / render capture | `monolith` | Material expressions, PCG graphs, viewport capture. |
| General editor / asset queries | `it-is-unreal` | Asset registry, level queries, screenshots. |
| — | `ueblueprintmcp` | **Disabled by default and not running.** Registered in `.mcp.json` but deliberately absent from `enabledMcpjsonServers` per Decision 027. Enabling it needs a **closed-editor `Build.bat` pass** — it is a new plugin module with reflected types, so Live Coding cannot register it. Do not write instructions that assume it. |

**Rules:**

1. Prefer `monolith` wherever more than one surface can do the job (Decision 025).
2. **Never run two surfaces against the same graph in one session.** This is the one rule that
   survived Decision 025's reversal, and it applies to all three servers.
3. All surfaces need the editor running. Monolith additionally cannot answer while a modal
   dialog blocks the game thread — grep the log for `MODAL_OPEN` before blaming the plugin.
4. MCP servers load at session start. Editing `.mcp.json` mid-session does nothing until the
   session restarts; check what you actually have before promising editor work.

### 1.1 Before you inject: prove the graph is on the live path

A write that returns `success: true` only means nothing threw. A graph that compiles clean and
moves its fingerprint can still be **unreachable**, in which case the change does nothing and
every verification tier reports green:

- `get_graph_fingerprint` / `assert_graph_matches` read *one graph*. They cannot see whether
  anything instantiates its owner.
- `pie_smoke_runner` fails on `must_absent` hits and missing `must_present`. An unreachable
  graph produces neither — it produces silence, which reads as a clean pass.

This has now happened twice. `BP_BattleUI` had a live `ShowBattleUI` exec chain that nothing
ever constructed, so lane input, the rhythm highway, focus and teardown were all dead
(`Source/BS_GodFile/MelodiaIntegration/Tests/MelodiaWiringContractTests.cpp`). And a lane remap
landed on `UMelodiaBattleInputComponent`, which only `AMelodiaGameMode` instantiates — but the
configured mode is `BP_MelodiaJRPGGameMode`, so the component is never created.

**Verifying a call site is not verifying the call.** Run `Tools/bp_live_path.py <asset>` and
abort on `ORPHAN` or `AMBIGUOUS` before authoring anything.

### 1.2 Derive from live. Never verify against a committed artifact.

Committed exports and fingerprint baselines stand in for the live graph and drift from it
silently. On 2026-08-08 the committed battle-controller export was stale, and a fail-closed
preflight caught it before anything was derived from fiction.

The rule that follows is stronger than "check freshness first," and it is already how the
verifiers here are built: **a committed export is an output, not an input.**
`verify_battle_closure.py` re-exports the live graph on every run and writes
`Exports/bp_battlecontroller_eventgraph_live.json` as a byproduct — so there is no window in
which it can read a stale one. Every verifier under `Tools/` and `Docs/T3D_Patterns/` does the
same; none reads a committed export back in.

Keep it that way. Do not add a script that loads an export and asserts against it, and do not
add a freshness-gate helper to make that safe — the staleness class is currently eliminated by
construction, and a gate would only be a mechanism for re-admitting it.

The one place a stored artifact IS the input is `bp_regression_checker.py`, whose whole job is
comparing today's fingerprints to a recorded baseline. That baseline therefore lives at the
**tracked** `Docs/T3D_Baseline/bp_fingerprints.json`, not under the gitignored `Saved/`, and a
missing or unreadable baseline is a hard failure. It used to respond to a missing baseline by
writing one and reporting OK, which made every run after a clean checkout pass by construction.

---

## 2. Rhythm Combat Subsystem — `UMelodiaRhythmCombatSubsystem`

**Header:** `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.h`
**Class:** `UTickableWorldSubsystem` (World-scoped; get via `Get`)

### 2.1 Accessor

| Function | Type | Signature |
|---|---|---|
| `Get` | BlueprintPure, static | `UMelodiaRhythmCombatSubsystem* Get(const UObject* WorldContextObject)` — meta `WorldContext` |

### 2.2 Session lifecycle

| Function | Type | Signature | Notes |
|---|---|---|---|
| `StartSession` | BlueprintCallable | `int32 StartSession(FName SkillId)` | Returns unique session ID, or **0** if skill not registered. |
| `FinishSession` | BlueprintCallable | `bool FinishSession()` | Derives aggregate grade, validates, broadcasts `OnRhythmComplete`. |
| `InvalidateSession` | BlueprintCallable | `void InvalidateSession()` | Tears down session + pending request. Does NOT reset `PendingDamageMultiplier`. |
| `IsSessionActive` | BlueprintPure | `bool IsSessionActive() const` | True while a session is live. |
| `GetActiveSessionId` | BlueprintPure | `int32 GetActiveSessionId() const` | 0 if none. |
| `GetSessionHitCount` / `GetSessionMissCount` | BlueprintPure | `int32 ...() const` | Banked hits/misses in active session. |

### 2.3 Result submission

| Function | Type | Signature | Notes |
|---|---|---|---|
| `SubmitResult` | BlueprintCallable | `bool SubmitResult(const FMelodiaAuthoritativeRhythmResult& InResult)` | Single authoritative result path. |
| `SubmitRatedInput` | BlueprintCallable | `bool SubmitRatedInput(EMelodiaSkillGrade Grade, int32 HitCount, int32 MissCount)` | Bridge for timing graders. Builds + validates the authoritative result. |
| `RegisterLaneHit` | BlueprintCallable | `EMelodiaSkillGrade RegisterLaneHit(int32 LaneIndex)` | Grades one lane press against the music clock. Returns Miss (no accumulation) when no session. |

### 2.4 Effect request consumption (stock resolver hookup)

| Function | Type | Signature | Notes |
|---|---|---|---|
| `HasPendingRequest` | BlueprintPure | `bool HasPendingRequest() const` | True when a validated, unconsumed request is pending. |
| `ConsumePendingRequest` | BlueprintCallable | `bool ConsumePendingRequest(FMelodiaRhythmEffectRequest& OutRequest)` | Pops the request for the stock resolver. |
| `GetPendingDamageMultiplier` | BlueprintPure | `float GetPendingDamageMultiplier() const` | Effective magnitude (BaseMagnitude × RhythmScalar), or 1.0 identity. **Poll at damage-notify time.** |
| `ClearPendingDamageMultiplier` | BlueprintCallable | `void ClearPendingDamageMultiplier()` | Reset to identity after the scaled damage is applied. |

### 2.5 Skill catalog

| Function | Type | Signature | Notes |
|---|---|---|---|
| `RegisterSkill` | BlueprintCallable | `void RegisterSkill(UMelodiaRhythmSkillDefinition* InSkill)` | Call once per skill at startup. |
| `FindSkill` | BlueprintPure | `UMelodiaRhythmSkillDefinition* FindSkill(FName SkillId) const` | Look up a registered skill. |
| `ResolveRhythmSkillId` | BlueprintPure | `FName ResolveRhythmSkillId(const UObject* StockSkill) const` | Maps a stock skill object → rhythm SkillId, or `NAME_None`. Feed straight into `StartSession`. |

### 2.6 Stock-skill integration (preferred entry point)

| Function | Type | Signature | Notes |
|---|---|---|---|
| `UseSkillWithRhythm` | BlueprintCallable | `bool UseSkillWithRhythm(UObject* StockSkill)` | **Single entry point** for "use this stock skill, with its rhythm minigame if it has one". Deferred skills fire `UseSkill` from `FinishSession` so the damage scalar exists in time. Returns true when deferred. |
| `GetDeferredSkill` | BlueprintPure | `UObject* GetDeferredSkill() const` | The skill whose UseSkill is deferred, or null. |

### 2.7 HUD binding

| Function | Type | Signature | Notes |
|---|---|---|---|
| `BindRhythmHUD` | BlueprintCallable | `void BindRhythmHUD(UMelodiaRhythmHUDWidget* InHUD)` | Held weakly. Call when the HUD is constructed. |

### 2.8 Delegate

| Delegate | Type | Signature |
|---|---|---|
| `OnRhythmComplete` | BlueprintAssignable | `FMelodiaRhythmSessionCompleted` — `(EMelodiaSkillGrade Grade, int32 HitCount, int32 MissCount)` |

**Fires exactly once per session.** Bind this to drive the stock resolver hookup and HUD teardown.

---

## 3. Enums (verified)

### 3.1 `EMelodiaSkillGrade` — `MelodiaRhythmCombatTypes.h`

```
Miss, Good, Great, Perfect
```

> ⚠️ **There is NO "Poor" grade.** The DeepSeek 08-03 handoff's "Poor=0.5" is wrong.
> Grade multipliers live in the skill DataAsset, not the subsystem (see §5).

### 3.2 `EMelodiaRhythmEffectType` — `MelodiaRhythmCombatTypes.h`

```
Damage, Crit, Heal, RemoveDebuff, Debuff, None
```

### 3.3 `EMelodiaRhythmNiche` — `MelodiaRhythmSkillDefinition.h`

```
Sad (→ Debuff), Calm (→ Heal + RemoveDebuff), Vigorous (→ Damage + Crit)
```

---

## 4. Structs (verified)

### 4.1 `FMelodiaRhythmEffectRequest` — `MelodiaRhythmCombatTypes.h`

| Field | Type |
|---|---|
| `bConsumed` | bool |
| `SkillId` | FName |
| `SessionId` | int32 |
| `EffectType` | EMelodiaRhythmEffectType |
| `BaseMagnitude` | float |
| `RhythmScalar` | float |
| `TargetMode` | FName |
| `TargetCount` | int32 |
| `Duration` | float |
| `TurnShift` | int32 |
| `Scalar` | float |
| `Magnitude` | float |
| `TargetId` | FName |

### 4.2 `FMelodiaAuthoritativeRhythmResult` — `MelodiaRhythmCombatTypes.h`

| Field | Type |
|---|---|
| `bValid` | bool |
| `SessionId` | int32 |
| `Grade` | EMelodiaSkillGrade |
| `PresentationScalar` | float |
| `HitCount` | int32 |
| `MissCount` | int32 |
| `NoteCount` | int32 |
| `Accuracy` | float |
| `ClockSource` | EMelodiaMusicClockSource |

---

## 5. Skill Definition — `UMelodiaRhythmSkillDefinition`

**Header:** `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmSkillDefinition.h`
**Class:** `UPrimaryDataAsset` (BlueprintType) — skills are DataAsset rows, not code.

### 5.1 Grade multipliers

`FMelodiaRhythmGradeMultipliers` struct with **defaults**:

| Grade | Default |
|---|---|
| Miss | 0.70 |
| Good | 1.00 |
| Great | 1.20 |
| Perfect | 1.45 |

Each skill row carries its own `DamageMultipliers`, `HealMultipliers`, `ResourceMultipliers`, `SpeedMultipliers`.
**Multipliers are per-skill data, NOT subsystem constants.** Read them from the DataAsset.

### 5.2 Key fields

| Field | Type | Notes |
|---|---|---|
| `SkillId` | FName | Stable ID used by subsystem + stock resolver |
| `Niche` | EMelodiaRhythmNiche | Maps to effect family |
| `EffectType` | EMelodiaRhythmEffectType | Requested effect family |
| `BaseMagnitude` | float | Before rhythm scalar |
| `TargetMode` / `TargetCount` | FName / int32 | Targeting |
| `SPCost` | int32 | Mana cost |
| `TempoBPM`, `IntroBeats`, `ActiveBeats`, `OutroBeats`, `NoteDensity` | float/int | MIDI pattern params |

---

## 6. Rhythm HUD — `UMelodiaRhythmHUDWidget`

**Header:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmHUDWidget.h`
**Class:** `UUserWidget` (Blueprintable), **NativePaint** rendering.

> ⚠️ **There are NO `BindWidget` UPROPERTYs and no UMG TextBlocks to bind.**
> The Kimi/DeepSeek task "mark `JudgementText`/`ComboText`/`ClockSourceText` as Is Variable"
> is based on a **false premise**. The HUD renders via Slate `NativePaint`. Do NOT spend time
> marking UMG widgets as variables — there is nothing to bind.

### 6.1 Accessor

| Function | Type | Signature |
|---|---|---|
| `FindFirst` | BlueprintCallable, static | `UMelodiaRhythmHUDWidget* FindFirst(const UObject* WorldContextObject)` |

### 6.2 Setters (all `BlueprintNativeEvent` — a BP subclass can override them)

| Function | Signature |
|---|---|
| `SetHUDMode` | `void SetHUDMode(EMelodiaHUDMode NewMode)` |
| `SetJudgment` | `void SetJudgment(const FText& NewText)` |
| `DoPulse` | `void DoPulse()` |
| `TriggerSparkleBurst` | `void TriggerSparkleBurst()` |
| `SetEnemyVitals` | `void SetEnemyVitals(float CurrentHP, float MaxHP)` |
| `SetPartyVitals` | `void SetPartyVitals(float CurrentHP, float MaxHP)` |
| `SetSkillPoints` | `void SetSkillPoints(int32 CurrentValue, int32 MaxValue)` |
| `SetUltimateGauge` | `void SetUltimateGauge(float CurrentValue, float MaxValue, bool bReady)` |
| `SetEnemyBreakGauge` | `void SetEnemyBreakGauge(float CurrentValue, float MaxValue, bool bBroken)` |
| `SetNoteHighwayActive` | `void SetNoteHighwayActive(bool bActive, const TArray<FMelodiaHighwayNote>& Notes, float BeatPosition, float ScrollBeatsAhead)` |
| `ShowActionPrompt` | `void ShowActionPrompt(const FString& PromptText)` |
| `SetBattlePhaseBanner` | `void SetBattlePhaseBanner(const FString& PhaseLabel)` |
| `PushFloatingCombatText` | `void PushFloatingCombatText(const FString& Text, bool bAnchorEnemy, FLinearColor Tint)` |
| `TriggerDamageFlash` | `void TriggerDamageFlash(float DamageValue)` |
| `ShowBattleStatus` | `void ShowBattleStatus(const FString& StatusText)` |

### 6.3 Other callables

| Function | Type | Signature |
|---|---|---|
| `SetSprintGlide` | BlueprintCallable | `void SetSprintGlide(bool bSprint, bool bGlide)` |
| `NotifyPerfectHit` | BlueprintCallable | `void NotifyPerfectHit()` |
| `GetMotionAmplitude` | BlueprintPure | `float GetMotionAmplitude() const` |

### 6.4 Readable state (BlueprintReadOnly)

`ActiveHUDMode`, `bIsSprinting`, `bIsGliding`, `LastActionPromptText`, `LastBattleStatusText`,
`LastBattlePhaseLabel`, `LastEnemyHP/MaxHP`, `LastPartyHP/MaxHP`, `LastSkillPoints/Max`,
`LastUltimateGaugeValue/Max`, `bUltimateReadyVisible`, `LastEnemyToughness/Max`,
`bEnemyBreakVisible`, `bNoteHighwayActive`, `HighwayNotes`, `HighwayBeatPosition`,
`HighwayScrollBeatsAhead`, `FloatingCombatTexts`, `LastJudgmentText`, `LastPulseTime`,
`LastSparkleBurstTime`, `LastDamageFlashTime`, `LastBannerTime`, `MotionTier`, `Displayed*` values.

---

## 7. Verified Wiring Seams

### 7.1 Cadence Strike → rhythm game (`BP_BattleUI` EventGraph)

After stock `OnUnitHasEnoughMP` passes for the skill:

```
OnSkillSelected(skillId="CadenceStrike")
  → Get UMelodiaRhythmCombatSubsystem (static Get(WorldContextObject))
  → StartSession("CadenceStrike") → returns sessionId (0 if skill not registered)
  → IF sessionId > 0:
      → show WBP_Battle_Rhythm (SetHUDMode / SetNoteHighwayActive)
      → push rhythm input context
      → hide stock command menu
  → ELSE: fall through to stock skill
```

**Preferred alternative:** call `UseSkillWithRhythm(StockSkill)` instead of the
StartSession → Branch → UseSkill cluster. The old cluster fired `UseSkill` on BOTH branch
outputs, running the montage in parallel with the session — the damage notify lands ~0.51s
in, the session latches at ~3.05s, so every rhythm-scaled hit landed unscaled.
`UseSkillWithRhythm` defers `UseSkill` until after `FinishSession` latches the scalar.

### 7.2 Rhythm → stock resolver hookup

On `OnRhythmComplete` (or after `FinishSession` returns true):

```
OnRhythmComplete(Grade, HitCount, MissCount)
  → Get UMelodiaRhythmCombatSubsystem
  → SubmitRatedInput(Grade, HitCount, MissCount) → bool accepted
  → IF accepted AND HasPendingRequest():
      → ConsumePendingRequest(OutRequest)
      → feed OutRequest into stock damage/heal resolver (route by EffectType)
  → restore stock menu
```

Route by `EffectType`:
- **Damage/Crit:** multiply stock damage by `RhythmScalar`
- **Heal/RemoveDebuff:** multiply stock heal by `RhythmScalar`
- **Debuff:** apply stock debuff with `Duration` from request

### 7.3 Damage-notify scalar read (montage path)

The damage anim-notify is an async callback on the montage's own call stack — there is no
pin to feed the scalar down. **Poll `GetPendingDamageMultiplier()` at notify time**, then
call `ClearPendingDamageMultiplier()` after applying. Returns 1.0 (identity) when nothing
is pending, so an unscaled hit is never zeroed.

---

## 8. Regeneration

This contract was hand-verified against source. To regenerate the BlueprintCallable surface
automatically, run:

```
python Content/Python/dump_blueprint_callable_surface.py
```

(see `Content/Python/README.md` for output location and format). Re-verify this doc against
the dump whenever the C++ API changes.
