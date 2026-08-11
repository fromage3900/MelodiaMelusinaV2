# Campaign 2 — Save Round Trip + Repeat Consume

**Gate ids:** `save_load`, `repeat_consume`
**Requirement:** `_VERTICAL_SLICE_SCOPE.md` — canonical `BP_JRPGSaveGame` slot
across a full process restart; one narrative flag + one reward restore without
duplication; `melodia:stat:` idempotent per `<IntentId>` (not per `<StatId>`).

## Preconditions

1. `python Tools/echo_run.py status` → editor reachable.
2. Slot names unified on `MelodiaJRPGSlot0/1/2` (writer + both readers) —
   verified 2026-08-07 (`save_system` ledger row). If the ledger says this is
   open, fix it first.
3. `melodia:item:` is a logging stub — do NOT author content that depends on
   it granting anything (AGENTS.md).

## Part A — save/load across full process restart

1. In PIE: play to the first autosave boundary (post-battle result).
2. Confirm the save file exists on disk:
   `%LOCALAPPDATA%/BS_GodFile/Saved/SaveGames/MelodiaJRPGSlot0.sav`
   (or `Saved/SaveGames` — confirm the project's actual save dir).
3. **Fully exit** the editor (not just PIE). Relaunch exactly one editor.
4. Load the slot via the canonical flow (Main Menu Continue/Load or the
   `WBP_SaveLoadPanel` path — the one the game actually uses).
5. Confirm: dialogue/flag state and JRPG-owned state restored; no duplicate
   reward, no duplicate dialogue.

**This is the gate that has never closed.** An in-memory guard passing the
reopen-dialogue test and double-paying after relaunch is exactly the defect
class this campaign exists to catch (Wallet restart-idempotence, `_TASK_QUEUE`).

## Part B — repeat consume

1. Replay the same authored beat twice (Quill resume + save reload paths).
2. The second occurrence must be a no-op: `melodia:stat:` recorded in
   `ConsumedIntentIds` once; reward granted once.
3. Two different beats may both award the same stat — that is legal and must
   still work (idempotence is per intent, not per stat).

## Record

```text
python Tools/echo_run.py record save_load pass --note "MelodiaJRPGSlot0 round-trip across full process restart"
python Tools/echo_run.py record repeat_consume pass --note "stat idempotent per IntentId; reward granted once"
```

Both rows required. One pass and one fail = campaign incomplete.
