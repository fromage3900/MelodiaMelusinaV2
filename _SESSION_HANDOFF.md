# Session Handoff — 2026-09-05

*Overwritten each session. Canonical detail lives in `CURRENT_STATE.md` §7 and
`Docs/P0_TASK_LEDGER.json`.*

---

## The headline: the project builds and plays

| | |
|---|---|
| **Editor build** | **GREEN** — `582fa914`. Binary dated 2026-09-04 21:47, editor runs from it. |
| **Audio reactivity** | **WORKS**, verified live in PIE with measured values — `b1cac649`. |
| **P0 gates** | 8/8 active gates `pass`. |
| **Tests** | 524/524 pass. |
| **Packaged route** | verified, both legs, 0 fatals. |

**Build root cause, for the record:** `LPCTSTR MaterialToken` silently dropped a struct member in
`MelodiaCaptureRenderSubsystem.cpp`. Two earlier `FString::Printf` rewrites blamed a UE 5.8
consteval format sanitiser and were treating symptoms. The fix is `const TCHAR*`.

**Audio root cause:** nothing was wrong with the subsystems — **route leg 0 simply had no music
clock**, so nothing drove `MPC_Melodia_Palette`. The clock now lives on the GameMode
(`5fea50c8`), so every level reacts instead of only levels with a hand-placed clock actor.

---

## Read these before touching the landscape

1. **Ultra Dynamic Sky is not pinned, and its time-of-day is not exposed to Python.** Two captures
   with *identical* material state differed by a lot (terrain colour spread 25.1 vs 15.9). Any
   before/after on `LV_SeaAbove_Prototype` has an uncontrolled lighting variable. **Pin the sky
   first or your A/B is noise.**
2. **`update_material_instance()` or the render is stale.** Parameter read-backs succeed while the
   viewport still shows the old value. This invalidated several measurements last session.
3. **Something rewrites `MI_Glacier_Landscape_Layered`.** `Gaea_SnowWeight` was found at −14.94 and
   `Gaea_RockWeight` at 6.43 *after* both had been set to 1.0 and verified. Writer unidentified.
   The master's `Saturate` clamps limit the damage, and the weights were measured to make no
   visual difference at all.
4. **`W_Glacier_Rock` is a near-black Gaea export** (peaks 31/255). The rock layer cannot read
   until it is re-exported with correct normalisation. Nothing on the UE side fixes this.
5. **SeaAbove `__ExternalActors__` are untracked.** That is why the key-light fix was lost twice.
   The light actor is now force-added (`0fb76675`); the other 73 are not.

---

## Git

- **19 commits replayed onto local `main`** via `merge-tree`/`commit-tree` — no worktree, index or
  HEAD touched. Full record: `Docs/Production/MERGE_TO_MAIN_RECORD_2026-09-04.md`.
- **Local `main` and `origin/main` are diverged lineages** (628 vs 704, neither an ancestor of the
  other). This predates the merge. "On main" means **local** main.
- Off-machine: `recovery/unify-histories-20260904`, `recovery/main-merged-20260904`.
- **Do not push `main`** — the pre-push hook forbids it. Branch names must start with
  `feature/ fix/ docs/ cleanup/ collab/ codex/ recovery/ cursor/`.

**Two other agents write to this repo.** The overnight wardrobe daemon *drives git itself* — it
checked the repo off `main` onto its own branch and committed mid-operation last session. Check
`git status` and `git rev-parse --abbrev-ref HEAD` before assuming which branch you are on.

---

## Next, in the order I would take it

1. **Universal / Universal_Alpha master convergence** — analysed, not executed. The Alpha master
   carries **none** of the 14 `Cymatic_*`/`Audio*` parameters, so its 109 instances — including
   Melusina's `SW_Dress_P01..P48` — are structurally excluded from the audio reactivity that is
   otherwise working. Opaque master has 2205 instances, Alpha 109: keep the opaque one, port the 8
   Alpha-only params (`OpacityMap`/`OpacityStrength`/`bUseOpacityMap` + 5 `Cloth_*`) additively so
   the 2205 are untouched, then reparent the 109 with per-instance `BlendMode=Masked` + `TwoSided`.
2. **Re-export `W_Glacier_Rock` from Gaea.** Unblocks the rock layer *and* the close-range detail
   texture, which is gated behind it.
3. **PCG volume layout** — four concentric 600–800k volumes over a 250k landscape, so no zone owns
   a style. Cheap and non-destructive to fix. `Docs/Plans/SEA_ABOVE_PCG_DRESSING_PLAN_2026-09-04.md`
   §4a.
4. **Find whatever writes junk into the landscape material instance.** Resetting values it will
   overwrite again is treating a symptom.

---

## Tools added this session

| Path | Purpose |
|---|---|
| `Content/Python/lookdev_capture.py` | Deterministic level captures via `SceneCapture2D`. `take_high_res_screenshot` needs a game viewport and silently writes nothing from an editor-only session. |
| `Content/Python/audit_gaea_wiring.py` | Traces each Gaea mask parameter to the `LandscapeLayerSample` it gates and whether it reaches the output. |
| `Content/Python/import_gaea_landscape_paint.py` | Imports Gaea weightmaps into landscape **paint** layers — the half of the pipeline that texture import does not cover. |
