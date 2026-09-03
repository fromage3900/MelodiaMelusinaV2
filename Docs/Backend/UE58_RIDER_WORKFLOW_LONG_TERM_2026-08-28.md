# UE 5.8 + Rider Workflow — Long-Term Deep Dive (2026-08-28)

**Status:** planning/draft, offline, no editor
**Author:** Melusina (Hermes agent, no-editor lane)
**Live with:** Junie (Rider, editor lock) — this lane stays offline until she frees it
**Companion:** `Docs/Backend/MELODIA_BACKEND_INTEGRATION_PLAN_2026-08-28.md` (§6 — the summary;
this is the deep dive)

---

## Purpose

A deep dive on the UE 5.8 + Rider workflow for BS_GodFile Melodia development — the two-lane
model, Live Coding limits, the single-editor rule, how to read truth from CDOs and Blueprints, the
T3D injection steps, and the evidence standard that governs every editor-bound action. Written so
that any agent — this lane or a future one — can pick it up and know exactly what Rider does, what
this lane does, what gates behind the editor lock, and what counts as evidence.

---

## 1. The two-lane model

| Lane | Tool | Holds | Does |
|------|------|-------|------|
| **Editor/C++** | Rider (OpenCode, `bedrock-mantle/qwen.qwen3-coder-next`) | editor lock for PIE/CDO/T3D | header + source edits, Blueprint reads via `blueprint_query`, PIE, T3D injection, asset saves |
| **No-editor** | this lane (Solar Pro 4, offline) | nothing | full closed-editor builds, contract tests, docs, skills, git review, planning |

**The rule:** when Rider holds the editor, this lane stays strictly offline. When this lane is doing
a closed-editor build, Rider can still edit source (the build reads files, not the editor). The
editor lock is only for PIE, CDO reads/writes, T3D injection, and `.uasset` saves.

**Why two lanes:** AGENTS.md #17 — "Parallelise research, never the editor." Source/C++ work
parallelises because it builds while the editor is closed. All editor work must serialise through one
holder. Another MCP server does not help — Monolith runs in-process, so a second surface is a second
writer on the same lock.

**How to tell who holds the lock:** `Get-Process UnrealEditor` must be a single instance and port
9316 must have exactly one listener. If either is ambiguous, assume the editor is locked and stay
offline (AGENTS.md #7/#17).

---

## 2. Live Coding limits (the most common trap)

### What Live Coding can do

- `.cpp`-only edits hot-patch fine via `editor_query live_compile`. The editor patches the running
  binary without a full rebuild.
- This is the fast path for small source fixes — a logic change, a debug print, a value tweak.

### What Live Coding cannot do

- **Any header change** — new class, new `UFUNCTION`, new `UPROPERTY`, new forward-declared enum —
  **needs a full closed-editor UBT rebuild**. Live Coding `trigger_build` reports
  `patch_applied=true` but ends in `compile_log: 'Live coding failed'` for header changes.
- **New imports.** Live Coding cannot introduce new imports. If a change calls a symbol the compiled
  binary never imported, it fails with no useful message in the editor log (AGENTS.md #15).
- **A file existing is not a file compiling.** Before planning around C++ another lane left behind,
  build it (AGENTS.md #22). `MelodiaJRPGPostBattleLibrary.cpp` sat in the tree for a day looking like
  finished work; it had never once compiled — a UE 5.7 include path, a typed accessor called on a base
  `FProperty*`, and `&` of a temporary.

### The rule of thumb

- If the change is `.cpp`-only and calls only symbols already in the compiled binary → Live Coding.
- If the change touches a header, adds a new symbol, or calls a symbol not yet imported → full
  closed-editor rebuild, always. Do not trust `patch_applied=true` as proof of a successful header
  change.

### Why this matters for the long-term items

- **StateTree:** any `FStateTreeTask_*` C++ task class is a header change → full closed-editor
  rebuild, always (AGENTS.md #15/#21).
- **Native validators:** any `UEditorValidatorSubsystem` subclass is a header change → full
  closed-editor rebuild, always.
- **FGameplayTag migration:** the water subsystem proof-of-concept is done (header + source, compiled
  at the 2026-08-27 baseline). The remaining subsystems (`MelodiaNarrativeSubsystem`,
  `MelodiaExternalJRPGBridgeSubsystem`, etc.) are header + source changes → full closed-editor rebuild,
  always.

---

## 3. The single-editor rule (the most dangerous trap)

### The rule

AGENTS.md #7/#17: one editor instance, always. On 2026-08-08 three editors ran concurrently on this
project — five crash reports in one hour, assets changing mid-edit, and 39 unsaved packages lost to a
forced kill. Check `Get-Process UnrealEditor` and that port 9316 has exactly one listener before any
editor work.

### Decision 025

Decision 025 forbids two MCP surfaces on one graph. This is the same hazard one level up: Monolith
runs in-process, so a second MCP server is a second writer on the same lock. Do not start a second
MCP server to "help" with editor work — it does not help, it collides.

### MODAL_OPEN is not a hang

A modal dialog blocks the game thread, so Monolith goes silent and Windows reports "Not Responding".
Grep for `MODAL_OPEN` before concluding the editor is dead — killing it there costs every unsaved
package for nothing. An FBX import dialog caused exactly this on 2026-08-09.

### How to recover from a stuck editor

1. Grep the log for `MODAL_OPEN` — if present, find the dialog and close it.
2. If no `MODAL_OPEN`, check whether the editor is actually dead or just silent (Monolith can be
   silent during a long compile or a modal dialog).
3. Do not kill the editor unless you've confirmed it's not a modal dialog — killing it costs every
   unsaved package.

---

## 4. Reading truth (the most common source of wrong conclusions)

### Allowlist truth

- `melodia_config_get_allowlist` (MCP) returns **stale fixture data** — use
  `blueprint_query get_cdo_properties` for config truth (AGENTS.md #18, `P0_TASK_LEDGER.json` →
  `tooling_traps`).
- The `DA_MelodiaIntegrationConfig` asset is a `.uasset`. The live authority is the CDO. A text
  search of the asset can confirm presence but never absence (AGENTS.md #20) — to establish that
  something is missing, read it through reflection (`get_cdo_properties`), not a text search.

### Blueprint truth

- `blueprint_query` is C++, not Python, so `get_cdo_properties`, `get_graph_data`, and `export_graph`
  all read skill Blueprints safely. Only the `editor_query run_python` route is dangerous — it forces
  UE to generate Python glue for user-defined enums like `D_DamageType`, which fails fatally (AGENTS.md
  #Python+sKillBlueprints).
- A variable-reference census misses expose-on-spawn pins (AGENTS.md #13). `find_variable_references`
  counts `K2Node_VariableSet` nodes only. Before declaring a property unwritten, check
  `K2Node_CreateWidget`/`K2Node_SpawnActor` nodes that construct the object.
- A committed export is an output, not an input (AGENTS.md #12). Verifiers re-derive from the live
  graph every run; do not assert against a stored export (the one exception is
  `bp_regression_checker.py`, whose baseline is tracked at `Docs/T3D_Baseline/bp_fingerprints.json`
  and hard-fails when missing).

### Level actor truth

- A level actor listing aggregates sublevels (AGENTS.md #24). `get_level_actors` reports actors from
  streaming sublevels alongside the persistent level. The distinction is load-bearing: a sublevel that
  is not set to load at startup is **absent from the PIE world**. Read the `sublevel` field, and
  confirm at runtime with a tag probe.
- `ORPHAN` means prove it, not delete it (AGENTS.md #11). `bp_live_path` cannot see `TSoftObjectPtr`
  (Decision 049) or `.umap` actor references (Decisions 020/029d/037a).

### Build truth

- "The build is green" decays into a lie (AGENTS.md #21). Adaptive unity keeps recently-changed files
  in separate translation units, so a tree can build incrementally for days while being unbuildable from
  clean. Three of four blockers on 2026-08-10 were unity-build symbol collisions that only appeared on
  a full rebuild.
- **Do a full closed-editor build before trusting a green claim, and before starting editor work.**

---

## 5. T3D injection workflow (the editor-bound path)

### The pipeline

```
Spec Change → T3D Inject → Compile → Fingerprint → Regression Test → Promote
```

### The apply workflow (from `melodia-ui-artist` skill §4, AGENTS.md § Apply workflow)

```
export_graph            -> save it: rollback record AND assertion baseline
get_graph_fingerprint   -> before
<mutate via blueprint_query/ui_query>
compile_blueprint       -> not clean? STOP.
assert_graph_matches    -> matched:false? STOP.
get_graph_fingerprint   -> after; record both
save_asset              -> then re-read live state to confirm (mtime <10min + re-read)
```

### Compile order trap

`compile_blueprint` WIPES CDO overrides set before it. Order is always
`compile -> set_cdo_property -> save`. Never compile between set and save.

### mtime is not proof

Re-read live state (`get_cdo_properties`, `get_level_actors`) after save. `.uasset` often goes
read-only after checkout — `attrib -R <path>` before saving. A `save_asset` returned inconclusive at
least once — confirm via `list_dirty_packages` (AGENTS.md #9).

### Evidence standard for graph mutation

A graph mutation is "done" when:
- (a) the pre-injection fingerprint is recorded (rollback record + assertion baseline)
- (b) `compile_blueprint` is clean
- (c) `assert_graph_matches` matches
- (d) the post-injection fingerprint is recorded
- (e) the asset re-read shows the new values
- (f) if it's the dialogue chain, the viewport guards are correct

A live PIE `HighResShot` plus before/after state reads is the only valid runtime evidence —
`capture_scene_preview`/`capture_anim_frames` produce stale frames and are not proof.

### What this lane can do offline

- Author/validate the spec JSON against the schema in `Docs/Production/T3D_MONOLITH_REFERENCE.md`.
- Write the verification harness: export the pre-injection fingerprint, assert `matched:false` is a
  hard stop, record both fingerprints.
- Run `python Tools/bp_sweep.py --filter <name>` and `python Tools/bp_live_path.py` **only if**
  Monolith is reachable — otherwise they die with connection-refused and you must note that as a HOLD,
  not a pass/fail.

### What this lane cannot do offline

- `bp_regression_checker.py` talks to Monolith over HTTP and dies with connection-refused when the
  editor is down. `static_gates` therefore cannot be checked offline at all.
- `t3d_dashboard.py --live` adds drift only with the editor up.
- Any `editor_query` action (trigger_build, run_pie_smoke, run_python) is editor-bound.

---

## 6. The editor lane's daily workflow (for Junie/Rider)

### Start of day

1. Check `Get-Process UnrealEditor` and port 9316 — confirm the editor is the only instance.
2. Check `git status --porcelain` — identify modified/untracked.
3. Re-run the offline contract tests (`test_p0_quests_and_content_contract` 8/8, `test_qsc_allowlist_contract` 3/4 expected FAIL) — confirm no regression since the last cycle.
4. Read the latest cycle report from `Saved/Backend/cycle_reports/` — confirm nothing changed that
   needs attention.

### During the day

1. For any C++ change: header → full closed-editor rebuild (not Live Coding). Source-only → Live
   Coding is fine.
2. For any T3D injection: follow the apply workflow (export → fingerprint → inject → compile →
   assert → fingerprint → save → re-read).
3. For any Blueprint read: use `blueprint_query` (C++), never `run_python` on skill Blueprints.
4. For any allowlist read: use `blueprint_query get_cdo_properties`, never `melodia_config_get_allowlist`.
5. For any asset save: re-read live state after save, confirm mtime + values.

### End of day

1. `git status --porcelain` — commit any tracked changes, leave untracked files as-is (Choral Sheep
   FBXs are owner-side).
2. Re-run the offline contract tests — confirm no regression.
3. Write a cycle report to `Saved/Backend/cycle_reports/<ISO-timestamp>.md` (or let the cron job do
   it — `ac916651f550` runs every 2h).
4. Confirm the editor is closed before leaving (one editor instance, always).

---

## 7. The no-editor lane's daily workflow (for this lane)

### Every cycle

1. `git status --porcelain` — flag anything risky (destructive commands in log, untracked `.uasset/.fbx`,
   modified `.uasset` with no commit).
2. `git diff --stat` — confirm the churn is the change intended.
3. `git log --oneline -10` — confirm no regressions.
4. `python -m unittest Content.Python.Tests.test_p0_quests_and_content_contract -v` — expect 8/8.
5. `python -m unittest Content.Python.Tests.test_qsc_allowlist_contract -v` — expect 3/4, 1 expected
   FAIL (27 missing IDs — that is normal until the allowlist is extended).
6. Confirm `Saved/gate_ledger.json` still has `battle_integration_map` + `hud_single_writer` both PASS.
7. Write a cycle report to `Saved/Backend/cycle_reports/<ISO-timestamp>.md`.

### What this lane never does

- Touches the editor (PIE, CDO, T3D, `.uasset` saves).
- Commits or pushes.
- Runs editor-bound tools (bp_sweep, bp_live_path, ui_style_audit, bp_regression_checker) and claims
  pass/fail when Monolith is unreachable — those are HOLD, not pass/fail.

### What this lane does in parallel with Junie

- Full closed-editor builds (when the user authorizes a long build and the editor is closed).
- Contract tests (always runnable).
- Docs (this lane's primary output tonight).
- Skills (this lane created `melodia-backend` tonight).
- Git review (this lane's primary ongoing output — the cron job).

---

## 8. File map

| File | Purpose |
|------|---------|
| `Docs/Backend/UE58_RIDER_WORKFLOW_LONG_TERM_2026-08-28.md` | **this file** — deep dive on UE 5.8 + Rider workflow |
| `Docs/Backend/MELODIA_BACKEND_INTEGRATION_PLAN_2026-08-28.md` | Single plan for backend work (§6 is the summary of this) |
| `Docs/Backend/MONOLITH_TEXT_INJECTION_SCALE_UP_2026-08-28.md` | Deep dive on T3D/Monolith batch scale-up |
| `.claude/skills/melodia-backend/SKILL.md` | No-editor runbook (the quick reference) |
| `.claude/skills/melodia-ui-artist/SKILL.md` | UI audit/style/apply runbook (the editor-bound counterpart) |
| `Saved/Backend/cycle_reports/` | Cycle reports (one per 2h cycle, written by this lane or the cron job) |
