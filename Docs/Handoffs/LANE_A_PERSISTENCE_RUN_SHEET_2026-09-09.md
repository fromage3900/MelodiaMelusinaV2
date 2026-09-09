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

## 5. After the hour

- Commit deferred Sea Above actors from clean editor close (see Git Health doc §4).
- Push feature branch; next promotion batch to `main` after PR #133 lands.
