---
name: melodia-p0-loop
description: Use when making or proving a Melodia gameplay/Blueprint change in this UE5.8 project — editor launch, Monolith CDO/graph mutation, child-vs-parent graph diffing, live PIE proof, and Echo gate recording. Invoke for any task that edits a Blueprint graph or CDO property, or that needs to prove a gameplay change actually works at runtime (not just compiles).
---

# Melodia P0 loop

Operational runbook for making a gameplay change in this project and proving it live. Every
step here was validated live in-session — this is not theory. Follow it top to bottom. Section 2
lists the traps that have cost the most time; read it before touching any graph.

## 0. Scope guard

This project runs under `_AGENT_WORKING_AGREEMENT.md` — do the job asked, ship it, stop. This
skill is a *procedure* for doing that safely on Blueprint work, not a license to expand scope.
Do not edit `README.md`, `_TASK_QUEUE.md`, `_SESSION_HANDOFF.md`, `Docs/P0_TASK_LEDGER.json`, or
`Docs/Handoffs/**` unless the task explicitly is one of those. Never modify `.uasset`/`.umap` files
directly on disk, never run raw git commands as a side effect of this loop, and never touch
`Config/` or `Content/Materials/` without asking first.

## 1. Pre-flight

- The editor must already be running, launched via `Launch_Editor.bat` — it bakes in
  `-DDC-ForceMemoryCache`. The `F:\UE_DDC` shared cache is unreliable; a raw launch without this
  flag can crash on startup with `Unable to use cache graph 'Installed' because it has no writable
  nodes available`. This flag is command-line-only — there is no `.ini` equivalent. Do not
  relaunch the editor yourself unless asked; verify it's already up.
- Verify Monolith is reachable: `mcp__monolith__monolith_status`, or `GET
  http://127.0.0.1:9316/health`.
- **One editor, one MCP surface, always.** Check `Get-Process UnrealEditor` and confirm a single
  listener on port 9316 before touching anything. Prefer the `monolith` MCP surface
  (`mcp__monolith__blueprint_query`, `mcp__monolith__editor_query`, etc.) for Blueprint work. Never
  run two MCP graph-mutation surfaces (`monolith`, `it-is-unreal`/VibeUE, `ueblueprintmcp`) against
  the same graph in one session — this project has been burned by exactly that.
- Monolith cannot answer while a modal dialog blocks the game thread. If a call hangs or errors
  oddly, grep the editor log for `MODAL_OPEN` before assuming the plugin is broken.

## 2. Blueprint mutation rules — read this before you touch a graph

These are the expensive lessons. Each one has actually broken something in this project.

- **Compile WIPES CDO overrides.** Calling `blueprint_query` action `compile_blueprint` AFTER
  `set_cdo_property` resets the property back to the class default. The correct order is always:

  ```
  compile_blueprint  ->  set_cdo_property  ->  save_asset
  ```

  Never compile between setting a CDO property and saving. If you must compile after a graph edit
  and also set a CDO property, compile first, then set the property, then save — do not compile
  again afterward.

- **A clean compile does NOT mean a clean graph.** Only object/array/map pins raise compile
  errors when orphaned. Primitive, bool, enum, and exec pins silently fall back to their literal
  default when disconnected. A `Branch` node whose `Condition` pin lost its input will compile with
  0 errors, 0 warnings, and silently evaluate `true` forever. This exact bug once blocked all
  player input while reporting a clean compile. Don't trust `compile_blueprint`'s clean result as
  proof of graph health by itself — pair it with `assert_graph_matches` against a known-good
  fingerprint, or with the parent-diff technique in Section 3.

- **Never delete a shadowed child variable and assume the graph re-links.** Reparenting a
  Blueprint renames a colliding child variable to `<name>_0`. Deleting that `_0` variable then
  purges every `Get`/`Set` node that referenced it — severing both data and exec chains — silently,
  with no compile error.

- **`.uasset` files frequently go read-only after checkout.** Run `attrib -R <path>` on the file
  before `save_asset`, or the save can fail silently.

- **mtime is NOT proof of a save.** After `save_asset`, re-read live state
  (`get_cdo_properties`, `get_level_actors`, etc.) to confirm the value actually landed. A
  concurrent second editor instance has silently reverted confirmed-saved content in this project
  before — this is another reason the "one editor, always" rule in Section 1 matters.

### The mandatory verification loop (from `_AGENT_WORKING_AGREEMENT.md`, Monolith Recipe 15)

Every graph add/remove/rewire through any MCP surface follows this, no exceptions:

```
export_graph            -> save it: rollback record AND assertion baseline
get_graph_fingerprint   -> before
<mutate>
compile_blueprint       -> not clean? STOP.
assert_graph_matches    -> matched:false? STOP.
get_graph_fingerprint   -> after; record both
save_asset
```

"Not clean" or `matched:false` is a hard stop, not a retry trigger — do not attempt a second fix
on an unconfirmed graph state; report what failed and what you saved. On a fresh session, call
`get_graph_fingerprint` twice on an untouched graph and once after a no-op resave, and require
byte-identical hashes before trusting the tool at all. One asset per transaction — never mutate a
second Blueprint before asserting the first landed.

## 3. Diffing a child Blueprint against its parent

Use this when a Blueprint has been reparented, or is behaving suspiciously and you suspect a
severed connection (see the shadowed-variable trap above).

Technique: Monolith exposes a streamable-HTTP MCP endpoint at `http://127.0.0.1:9316/mcp`. POST
JSON-RPC directly — `initialize`, then `tools/call` with `name: "blueprint_query"`, `action:
"export_graph"` — for both the parent and the child graph, and diff the two exports locally
(e.g. with a short Python or Node script). This keeps a potentially huge graph export out of the
model's own context window entirely; only your diff summary needs to come back.

What to look for:
- A pin that is **connected in the parent** but has an **empty `connected_to` in the child** —
  this is the signature of a severed link from the trap above.
- Nodes present in the child but absent from the parent — that set is the genuinely-custom logic
  worth preserving through any further edit.

Document this as a technique (JSON-RPC shape above) rather than relying on a specific throwaway
script — rebuild the POST calls fresh each time so the diff logic stays in your control.

## 4. Live PIE proof loop — this is what actually closes a gate

Compiling clean or a synthetic tool response is not proof. Proof is a live PIE run with real
runtime state read back before/after.

```
editor_query load_level          path=/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap
editor_query run_pie_smoke       duration=12
editor_query poll_pie_smoke      session_id=<from previous>   # want ok:true, "Accessed None":0
editor_query start_pie
editor_query pie_call_function   actor_label=BP_PermanentBattle  function=OverlapStarted  allow_non_callable=true
editor_query pie_get_object_properties  class_name=BP_BattleController  properties=[...]
editor_query run_console_command command="HighResShot 1920x1080"
editor_query stop_pie
```

(`editor_query` here is `mcp__monolith__editor_query` with the given `action` — e.g. `action:
"load_level"`, `params: {path: "..."}`.)

Notes:
- This project uses **legacy input mappings, not Enhanced Input**. `pie_inject_input_action` will
  fail with `No UInputAction asset named 'Interact' found`. Trigger battles by overlap
  (`OverlapStarted`) or a real keypress instead.
- `K2_SetActorLocation` teleports a pawn but does **not** generate overlap events — don't use it to
  fake entering a trigger volume.
- `HighResShot` output lands in `Saved/Screenshots/WindowsEditor/`.

Useful runtime reads that constitute real proof:
- `BP_BattleController`: `currentAttackingUnit`, `jRPGPlayerController`, `melodiaBattleUI`,
  `currentTurn`, `isBattleOver`.
- Player controller: `gameState`, `isExplore`, `exploreCharacter`, `playerUnits`,
  `partyMembers`, `isInputBlocked`.

## 5. Echo pipeline / gate recording

- `python -B Tools/echo_run.py status` — free, offline, check this first.
- `python -B Tools/echo_run.py run static_gates` — runs `graph_reachability`, `bp_live_path`,
  `bp_sweep`, `ui_lint`, `verify_baseline`.
- `python -B Tools/echo_run.py record <gate> pass|fail --note "..."` — **this is the only thing
  that closes a gate.** No ledger row, no claim. Prose in a session log is not evidence
  (`_AGENT_WORKING_AGREEMENT.md` P0 rule 5).

Known-failing, pre-existing, do not chase:
- `bp_sweep` fails solely because `run_bp_sweep` (`Tools/echo_run.py:313`) requires `DUPES == 0`,
  and there are ~15 `/Game/Melodia/<path>` vs `/Game/<path>` mirror-tree duplicate short names.
- `verify_baseline` reports 16 drifted assets, all materials, zero gameplay assets.

Neither of these is your task to fix unless explicitly asked — recording them as known-failing and
moving on is correct, not evasive.

## 6. Screenshot / evidence caveat

`capture_scene_preview` and `capture_anim_frames` are asset-preview tools. They have produced
stale/identical frames in this project and are **not valid gate evidence**. Real evidence is a
live PIE `HighResShot` (Section 4) plus the before/after runtime state reads next to it.

## 7. Synthetic vs. live — do not conflate these

The `mcp__melodia__*` tools (`melodia_encounter_start`, `melodia_economy_*`,
`melodia_quest_check_p0`, etc.) operate on **synthetic in-process state**, not the running editor.
They're useful for exercising the economy/encounter contract in isolation, but they are **not**
live PIE proof and must never be cited to close a runtime gate. Only Section 4's loop, run against
an actual PIE session through `mcp__monolith__editor_query`, counts as proof.
