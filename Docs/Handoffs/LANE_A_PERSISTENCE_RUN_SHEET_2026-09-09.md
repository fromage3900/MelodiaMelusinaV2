# Lane A UE-Hour Run Sheet — Persistence / Idempotency Proof — 2026-09-09

**Goal (TODO "NOW — close the song"):** golden chain to restart-safe, repeat-load-safe state.
**Bloker note:** B2 ChoralSheep C++ (header change) is UNBUILT. Either run the hour on content-only
paths that avoid the new Tick/MID code, or open with a closed-editor `Build.bat` (kills the hour —
recommend: proof first, build after).

## 1. Preflight (first 5 min, non-negotiable)

1. `Get-Process UnrealEditor` → exactly one instance.
2. Rider Problems View → Errors on `MelodiaChoralSheepActor.*` noted, not fixed live (header = closed build).
3. Dirty packages noted; do NOT save maps/materials unrelated to the run.
4. PIE map: `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` (chain proof).
5. Ultra Dynamic Sky: this run needs no Sea Above A/B — sky pin not required.

## 2. Logpoints (suspend=NONE — never freeze PIE)

| # | Symbol | File:line | Expression / watch |
|---|--------|-----------|--------------------|
| L1 | `UMelodiaNarrativeSubsystem::RestoreNarrativeRecord` | `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.cpp:768` | log result + `Record.ConsumedIntentIds.Num()` |
| L2 | `RestoreNarrativeRecordFromSave` | same file `:958` | log `LOADED_NARRATIVE_RESTORED` vs reset path |
| L3 | `OnRewardRequested` broadcasts | same file `:263, :345, :446` | log `RewardId` (expect `reward.first_resonance_echo`) |
| L4 | `ConsumeOnce` / intent add | same file `:336, :439, :582, :613` | log `CompletionIntentId`/`ApplyIntentId`, before/after `Contains` |
| L5 | `UMelodiaWardrobeComponent::ApplyWardrobeState` | `Plugins/MelodiaWardrobe/.../Private/MelodiaWardrobeComponent.cpp:21` | log Accessories equipped bool |
| L6 | `UMelodiaTraversalComponent::RequestTraversalMode` | `Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.cpp:162` | log Glide accept airborne / reject grounded |
| L7 | Save/load seam | `MelodiaSaveSlotLibrary.cpp:177, :257` | log slot name + `bNarrativeRestored` |

Drain via `DRAIN_EVENTS` (`tracepointOutputsTail`); breakpoint errors via `breakpointErrorsTail`.

## 3. PIE script (0:10–0:50)

1. Confirm portal locked: `IsTraversalUnlocked == false`, reason `capability_blocked_or_locked`.
2. Step music node → expect `HitCount=1, PerfectCount=1, Score=100, bCompleted=true`.
3. Same-frame chain (L3→L5): grant `Cos_Accessories_MelusinaV2` → auto-equip Accessories.
4. `IsSlotEquipped(Accessories) == true`; airborne Glide ACCEPT, grounded REJECT
   (`glide_requires_airborne_state`); portal unlocked, prompt = `Continue exploring  [F]`.
5. Canonical save → **full process exit** → relaunch → load → expect
   `LOADED_NARRATIVE_RESTORED` + `ApplyWardrobeState` → Accessories `true` (L1+L2+L5).
6. **Repeat-load:** load the same slot twice more; diff durable state
   (`ConsumedIntentIds`, wardrobe, stats) — must be equal, no duplication (L4 `Contains` short-circuit).
7. End PIE; assert **zero dirty packages** from the verification run.

## 4. Evidence bar (0:50–1:00)

- Frames + assertion JSON side by side under `Saved/Audit/<date>/` (frames without a report
  are not evidence). Use the committed harness — fix-then-rerun if it crashes; never certify
  from an uncommitted driver.
- `record_gate.py` row for the gate claimed; state level honestly:
  source-built / live-proven / restart-proven / packaged-proven.
- Probe/injected calls (`pie_call_function`, `K2_SetActorLocation`) prove the authority chain,
  NOT player-input routing — label accordingly; real-key (`OnKeyDown` Q/W/O/P) run still owed
  for full `runtime` certification.
- Hard no's: no second SaveGame authority, no persisted live rhythm session, no raw Starskiff
  physics snapshot, no schema extension before durable-vs-transient ownership is written down
  (Starskiff + Convergence tracing still open per TODO).

## 6. Night run 2026-09-09 — what actually happened (read before re-running)

Committed harness `Tools/run_p0_real_input_probe.py` was fixed and run live 4x:

- **Run 1: FAIL** — cold-PIE teleport landed off-beat (`MissCount=2`, never completed).
  Lesson: grading is music-clock-relative; teleports are phase-lottery.
- **Run 2: PASS** — exact 08-31 signature (`Perfect/100/completed`, portal unlocked).
  But step 3 called `RequestTraversalMode` on the **character** (not found) and the
  harness printed PASS unconditionally → **void glide assertion**. Kept as run log,
  superseded, scratch copy removed.
- **Diagnosis:** traversal authority lives on `MelodiaTraversal` component instance;
  native signature `RequestTraversalMode(EMelodiaTraversalMode RequestedMode)`.
  Serializer quirk: `Result=Accepted` (enum 0) is dropped → accepted reads
  `(RequestedMode=Glide)`; rejections serialize fully. `IsGliding`/`GetTraversalMode`
  are the behavioral oracles.
- **Run 3 (fixed harness): genuine PASS** — `Docs/Evidence/P0_REAL_INPUT_PROBE_2026-09-09.json`:
  locked → `Perfect/100/bCompleted=True` (2 accumulated misses from re-step cycles,
  misses do not gate `MarkCompleted`) → probe-equip → grounded
  `RejectedContext/glide_requires_airborne_state` → airborne `IsGliding=true`,
  mode `Glide` → portal unlocked, reason `None`.
- **Withheld:** no `record_gate.py` row — teleports are probe movement, not real-key
  input, and step-2 equip is probe-injected (reward path re-owed, last proven 08-31).
  Screenshots in the evidence JSON were never captured by the harness (dangling paths).
  `TryInteract` returns False while unlocked in all runs — interaction preconditions
  (overlap/facing) unsatisfied by teleport; routing TBD, not asserted.
- **Restart proof NOT run:** editor kill deferred (relaunch risk, owner absent). Zero-cost
  check passed: 0 dirty packages after all PIE runs. Save-driver gap found: no committed
  caller of `CreateCanonicalJRPGSlot`; `pie_call_function` cannot reach static
  `UBlueprintFunctionLibrary` entries ("No PIE actor matched"). Next step is an in-game
  save trigger (checkpoint path?) or a Monolith static-lib call, then
  save → quit → relaunch → load → load-again with the fixed harness asserting each leg.

## 7. After this run

- Commit deferred Sea Above actors from clean editor close (see Git Health doc §4).
- Push feature branch; next promotion batch to `main` after PR #133 lands.
