# Blueprint Wiring Skill — Shared Agent Operating Procedure

**Created:** 2026-08-07
**Applies to:** Any agent (Cline, DeepSeek, Kimi, Ollama, future) doing Blueprint graph work
**Companion doc:** `Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md` (the API source of truth)

> **Load this skill before ANY Blueprint wiring task.** It tells you which MCP server to use,
> the exact command sequence for the common patterns, and the verification loop that defines "done".

---

## 1. Mandatory Tool Selection

**Use `ueblueprintmcp` for all Blueprint graph work.** It is the only MCP server in this
project that can read an EventGraph, add nodes, connect pins, and compile.

| Server | Use for | Never use for |
|---|---|---|
| **`ueblueprintmcp`** | Blueprint nodes, pins, compile, UMG widgets, Enhanced Input | Materials, PCG, render capture |
| `monolith` | Materials, PCG graphs, viewport/render capture, editor build | Blueprint graph wiring |
| `it-is-unreal` | Asset registry, level queries, general editor | Blueprint graph wiring |

**If a handoff says "run monolith + it-is-unreal" for a Blueprint wiring task, ignore that
instruction.** It is a known failure pattern from 2026-08-03/06 handoffs. Use `ueblueprintmcp`.

---

## 2. The Standard Wiring Loop

Every wiring task follows this exact sequence. Do not skip steps.

### Step 1 — Read the current graph state

```
find_blueprint_nodes(blueprint_name="BP_BattleUI", graph_name="EventGraph")
```

- Returns `node_guid`, `node_class`, `node_title` for every node.
- **Always do this first.** You cannot wire into a graph you haven't read.
- If a node you expect is missing, stop and investigate before adding anything.

### Step 2 — Inspect pins when a connection fails

```
get_node_pins(blueprint_name="BP_BattleUI", node_id="<guid>", graph_name="EventGraph")
```

- Lists every pin on a node with its category (exec, object, struct, enum, etc.).
- **Use this whenever `connect_blueprint_nodes` fails.** Pin names in handoffs are often
  slightly wrong; the live pin list is ground truth.

### Step 3 — Add nodes

```
add_blueprint_function_node(blueprint_name="BP_BattleUI", function_name="StartSession",
    target_blueprint="UMelodiaRhythmCombatSubsystem", node_position=[x, y], graph_name="EventGraph")
```

- For static functions, pass the class name as `target_blueprint` (e.g. `KismetMathLibrary`).
- For subsystem access, prefer `add_blueprint_get_subsystem_node` (typed return) over a
  generic function call.
- Record the returned `node_id` for each node you create — you'll need them for connecting.

### Step 4 — Connect pins

```
connect_blueprint_nodes(blueprint_name="BP_BattleUI",
    source_node_id="<guid>", source_pin="then",
    target_node_id="<guid>", target_pin="execute",
    graph_name="EventGraph")
```

- **Wire exec pins first** (establishes flow), then data pins.
- If a pin name is rejected, run `get_node_pins` on that node and use the exact live name.

### Step 5 — Set pin defaults (object references, enums, constants)

```
set_node_pin_default(blueprint_name="BP_BattleUI", node_id="<guid>", pin_name="SkillId",
    default_value="CadenceStrike", graph_name="EventGraph")
```

- Object pins use asset path format: `/Game/Path/AssetName.AssetName`.
- The command calls `StaticLoadObject` automatically for object pins.

### Step 6 — Compile and verify (THE definition of done)

```
compile_blueprint(blueprint_name="BP_BattleUI")
```

- Returns `error_count`, `warning_count`, and detailed errors with node IDs.
- **A wiring task is NOT done until `error_count == 0`.**
- If there are errors, read the node IDs in the error output, fix the wiring, and recompile.
- Do not report success with warnings unless you can explain each one.

---

## 3. Common Patterns

### 3.1 Get a WorldSubsystem (typed)

```
add_blueprint_get_subsystem_node(blueprint_name="BP_BattleUI",
    subsystem_class="UMelodiaRhythmCombatSubsystem", node_position=[x, y])
```

Returns a typed `ReturnValue` pin you can feed straight into `StartSession`/`SubmitRatedInput`.

### 3.2 Branch on a condition

```
add_blueprint_branch_node(blueprint_name="BP_BattleUI", node_position=[x, y])
```

Pins: `Execute` (exec in), `Condition` (bool in), `Then` (exec out, true), `Else` (exec out, false).

### 3.3 Bind a delegate (e.g. `OnRhythmComplete`)

```
bind_event_dispatcher(blueprint_name="BP_BattleUI", dispatcher_name="OnRhythmComplete",
    node_position=[x, y])
```

Creates the bind node + a matching custom event automatically. Wire the custom event's body
to the resolver hookup.

### 3.4 Call a custom Blueprint function

```
create_blueprint_function(blueprint_name="BP_BattleUI", function_name="HandleRhythmComplete",
    inputs=[...], outputs=[...])
compile_blueprint(blueprint_name="BP_BattleUI")   # REQUIRED before calling
call_blueprint_function(blueprint_name="BP_BattleUI", function_name="HandleRhythmComplete")
```

---

## 4. Verification Checklist (attach to every handoff)

Before you write a handoff claiming a wiring task is done, confirm ALL of:

- [ ] `find_blueprint_nodes` shows the expected nodes in the target graph
- [ ] `compile_blueprint` returned `error_count == 0`
- [ ] Every warning is explained (or eliminated)
- [ ] Exec flow is wired first, data pins second
- [ ] Object pin defaults use `/Game/...` asset paths
- [ ] The graph was auto-saved (UEBlueprintMCP auto-saves after successful operations)

---

## 5. Known Traps (from real failures 2026-08-03 → 08-06)

1. **Using Monolith/it-is-unreal for Blueprint wiring** — they cannot add/connect nodes.
   Use `ueblueprintmcp`. (This is the #1 cause of "agents can't wire blueprints".)
2. **Trusting handoff pin names over live pins** — always `get_node_pins` on failure.
3. **Skipping compile** — a graph that "looks wired" but doesn't compile is not wired.
4. **"Poor" grade** — does not exist. Grades are Miss/Good/Great/Perfect.
5. **Marking UMG widgets as Is Variable on the rhythm HUD** — false premise. The HUD is
   NativePaint; there are no BindWidget properties. See the contract doc §6.
6. **StartSession → Branch → UseSkill cluster** — fires UseSkill on both branches and runs
   the montage in parallel with the session, so rhythm-scaled damage lands unscaled.
   Use `UseSkillWithRhythm(StockSkill)` instead. See contract doc §7.1.

---

## 6. When to Escalate

- A node type you need doesn't exist in `ueblueprintmcp`'s command surface → extend the
  plugin (see `Plugins/UEBlueprintMCP/docs/SKILL.md` "Extending the MCP") rather than
  hand-wiring in the editor.
- A compile error references a C++ API you can't resolve → check the contract doc first,
  then the source header, then escalate with the exact error text.
- The editor is not running / `ueblueprintmcp` is not connected → do not guess. Report the
  connection state and stop.