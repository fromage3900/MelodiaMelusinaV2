# Reconciliation Plan — Duplicate Content Trees

**Status:** PLAN ONLY — owner sign-off required before any deletion. The mirror
is untracked and unrecoverable; a wrong deletion is permanent.
**Gate ids on record:** none until executed — this plan itself is gated.

## The duplicates

### 1. Two `BP_BattleUI`
- LIVE: `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleUI` (the one
  the battle controller constructs; all wiring fixes landed here)
- ORPHAN ISLAND: `/Game/_ThirdParty/TurnBasedJRPGTemplate/...` — carries its own
  `BP_BattleController`, reachable by nothing (its GameMode chain is retired,
  Decision 029a)

### 2. The 33-asset mirror
- `Content/MelodiaIntegration/Content_MelodiaIntegration/` — untracked in git,
  dates to 2026-07-26, still contains a copy of `BP_MelodiaBattleUI` carrying
  the **ten shadowed events** that were fixed in the live copy. This is the
  dangerous one: it looks like a live tree.

## Verification before anything moves

For each asset, `python Tools/bp_live_path.py <asset>`:

- `LIVE` → keep, record which path is canonical.
- `ORPHAN` → **prove it, do not delete on the verdict alone.** `bp_live_path`
  cannot see `TSoftObjectPtr` (Decision 049) or `.umap` actor references
  (Decisions 020/029d/037a).
- `AMBIGUOUS(n)` → resolve the n entry points first.

## Owner decision required

1. **Which `BP_BattleUI` is canonical** — the LIVE one (recommended: it is the
   one the loop constructs) — and whether the `_ThirdParty` island is deleted
   or simply left unaddressed.
2. **The 33-asset mirror**: delete, or keep as quarantine? If deleted, the
   safe move is `git mv`-style relocation to
   `_QuarantineAssets_20260809/` (mirrored path, reversible, per Decision 022)
   rather than `Remove-Item`.
3. **Whether the mirror's stale `BP_MelodiaBattleUI` (with the shadowed
   events) may be used as evidence** — it is a record of the pre-fix defect,
   but keeping it as a *live-looking* tree is the hazard.

## Execution (after sign-off)

1. One editor instance; `python Tools/echo_run.py status` reachable.
2. Relocate (never delete) the mirror to `_QuarantineAssets_20260809/`.
3. Re-run `python Tools/bp_sweep.py` project-wide to confirm zero duplicate
   short names remain.
4. Re-run `python Tools/echo_run.py run static_gates` (live-path + sweep +
   reachability) and record:
   ```text
   python Tools/echo_run.py record duplicate_trees pass --note "mirror quarantined; single canonical BP_BattleUI; sweep clean"
   ```

## Do not

- Run `git clean` of any kind (bulk `Content/` is untracked; it would erase
  the project).
- `delete_asset` anything not created this session.
- Delete the mirror before the quarantine copy is verified on disk.
