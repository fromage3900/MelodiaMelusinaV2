---
name: unreal-logicdriver
description: Use when working with Logic Driver Pro plugin via Monolith MCP -- creating and editing state machines, states, transitions, runtime PIE control, JSON spec builds, scaffolding templates, and text visualization. Triggers on state machine, logic driver, SM blueprint, state graph, FSM, state transition, dialogue tree, quest system, game flow.
---

# Unreal Logic Driver Pro Workflows

**66 LogicDriver actions** across 10 categories via `logicdriver_query()`. Discover first: `monolith_discover({ namespace: "logicdriver" })`

## Key Parameters

- `asset_path` / `state_machine_path` -- SM Blueprint path (e.g., `/Game/StateMachines/SM_EnemyBehavior`)
- `node_id` / `state_name` -- node identifier or human-readable name
- `transition_id` -- transition identifier
- `save_path` -- destination for new assets
- `spec` -- JSON spec for `build_sm_from_spec`
- `template` -- scaffold template (e.g., `hello_world`, `horror_encounter`)
- `format` -- text output: `ascii`, `mermaid`, `dot`
- `instance_index` -- runtime SM instance (default 0)

## Action Reference

### Asset CRUD (8)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `create_state_machine` | `save_path`, `sm_name`? | Create SM Blueprint |
| `get_state_machine` | `asset_path` | Read full structure |
| `list_state_machines` | `path_filter`?, `limit`? | List all SMs |
| `delete_state_machine` | `asset_path` | Delete SM |
| `duplicate_state_machine` | `asset_path`, `save_path` | Duplicate |
| `rename_state_machine` | `asset_path`, `new_name` | Rename |
| `validate_state_machine` | `asset_path` | Lint: orphans, dead ends, unreachable |
| `compile_state_machine` | `asset_path` | Compile (required before PIE) |

### Graph Read/Write (20)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `get_graph_structure` | `asset_path` | Full topology: nodes, edges, nesting |
| `get_state_info` | `asset_path`, `node_id` | State details: class, properties |
| `get_transition_info` | `asset_path`, `transition_id` | Transition: conditions, priority, color |
| `get_nested_graph` | `asset_path`, `node_id` | Nested SM graph |
| `add_state` | `asset_path`, `state_class`, `state_name`? | Add state node |
| `remove_state` | `asset_path`, `node_id` | Remove state + transitions |
| `add_transition` | `asset_path`, `source_node`, `target_node`, `condition_class`? | Add transition |
| `remove_transition` | `asset_path`, `transition_id` | Remove transition |
| `set_state_property` / `get_state_property` | `asset_path`, `node_id`, `property_name`, `value`? | Set/read state UPROPERTY |
| `set_transition_property` / `get_transition_property` | `asset_path`, `transition_id`, `property_name`, `value`? | Set/read transition UPROPERTY |
| `set_entry_state` | `asset_path`, `node_id` | Set entry point |
| `add_conduit` | `asset_path`, `conduit_name`? | Add conduit node |
| `add_state_machine_ref` | `asset_path`, `ref_path`, `node_name`? | Add nested SM reference |
| `set_node_position` | `asset_path`, `node_id`, `x`, `y` | Set graph position |
| `get_all_states` | `asset_path` | All states with IDs and classes |
| `get_all_transitions` | `asset_path` | All transitions with source/target |
| `auto_arrange_graph` | `asset_path`, `spacing`? | Auto-layout (BA bridge) |
| `set_graph_property` | `asset_path`, `property_name`, `value` | Top-level graph UPROPERTY |

### Node Config (8)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `set_on_state_begin` / `update` / `end` | `asset_path`, `node_id`, `graph_nodes` | Configure state event graphs |
| `set_transition_condition` | `asset_path`, `transition_id`, `condition_class`, `params`? | Set condition |
| `set_transition_priority` | `asset_path`, `transition_id`, `priority` | Set priority (lower = first) |
| `add_state_tag` / `remove_state_tag` | `asset_path`, `node_id`, `tag` | Add/remove gameplay tag |
| `set_state_color` | `asset_path`, `node_id`, `color` | Set node color |

### Runtime/PIE (7)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `runtime_get_active_states` | `actor_label`?, `component_name`? | Current active states |
| `runtime_force_state` | `actor_label`, `state_name`, `instance_index`? | Force to state |
| `runtime_send_event` | `actor_label`, `event_name`, `instance_index`? | Send event |
| `runtime_get_variables` | `actor_label`, `instance_index`? | Read SM variables |
| `runtime_set_variable` | `actor_label`, `variable_name`, `value`, `instance_index`? | Set SM variable |
| `runtime_restart` | `actor_label`, `instance_index`? | Restart SM |
| `runtime_stop` | `actor_label`, `instance_index`? | Stop SM |

### JSON/Spec (5)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `build_sm_from_spec` | `save_path`, `spec` | **POWER ACTION** -- full SM from JSON in one call |
| `export_sm_to_spec` | `asset_path` | Export to JSON spec |
| `import_sm_from_json` | `save_path`, `json_path` | Import from JSON file |
| `export_sm_to_json` | `asset_path`, `json_path` | Export to JSON file |
| `diff_state_machines` | `asset_path_a`, `asset_path_b` | Structural diff |

### Scaffolding (7)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `scaffold_hello_world` | `save_path` | Minimal 2-state SM |
| `scaffold_dialogue` | `save_path`, `dialogue_lines`? | Dialogue tree with branching |
| `scaffold_quest` | `save_path`, `quest_stages`? | Quest progression |
| `scaffold_interactable` | `save_path`, `interaction_type`? | Idle->Interact->Cooldown |
| `scaffold_weapon` | `save_path`, `weapon_type`? | Idle->Fire->Reload->Overheat |
| `scaffold_horror_encounter` | `save_path`, `phases`? | Ambient->Alert->Chase->Attack->Reset |
| `scaffold_game_flow` | `save_path`, `flow_stages`? | MainMenu->Loading->Gameplay->Pause->GameOver |

### Discovery (6)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `list_state_classes` / `list_transition_classes` / `list_conduit_classes` | `filter`? | Available node classes |
| `get_sm_class_hierarchy` | `class_name` | Inheritance hierarchy |
| `find_sm_references` | `asset_path` | Assets referencing SM |
| `get_sm_stats` | `asset_path` | State/transition count, depth, complexity |

### Component (3)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `add_sm_component` | `blueprint_path`, `sm_asset_path`, `component_name`? | Add SMInstance component |
| `configure_sm_component` | `blueprint_path`, `component_name`, `properties` | Configure (auto-start, tick) |
| `list_sm_components` | `blueprint_path` | List SM components |

### Text Graph (2)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `visualize_sm_as_text` | `asset_path`, `format`? | Render as ascii/mermaid/dot |
| `search_sm_content` | `query`, `path_filter`? | Full-text search across SMs |

## Technical Notes

1. **Reflection only** -- Marketplace plugin. MonolithLogicDriver uses UObject reflection, not direct C++ linkage. Works across LD versions.
2. **`#if WITH_LOGICDRIVER`** -- Probes `Plugins/` and `Plugins/Marketplace/`. Empty stub when absent.
3. **Settings toggle** -- `bEnableLogicDriver` in `UMonolithSettings` (default: true).
4. **SM Architecture** -- `USMBlueprint` assets with compiled `USMInstance`. Edits update both EdGraph and runtime layers.
5. **State hierarchy** -- Root: `USMStateInstance_Base`. Key: `USMStateInstance` (standard), `USMStateMachineInstance` (nested), `USMConduitInstance` (branch). Transitions: `USMTransitionInstance`.
6. **`build_sm_from_spec` format** -- `{ states: [{name, class, properties, event_graphs}], transitions: [{source, target, condition}], entry_state?, metadata? }`.
7. **Blueprint Assist** -- `auto_arrange_graph` reads FBACache if BA installed, falls back to grid layout.
8. **Runtime actions require PIE** -- `runtime_*` locate SM instances via actor label + component name.

## Common Workflows

### Create SM from Spec (Fastest)
```
logicdriver_query({ action: "build_sm_from_spec", params: {
  save_path: "/Game/StateMachines/SM_EnemyAI",
  spec: {
    entry_state: "Idle",
    states: [
      { name: "Idle", class: "USMStateInstance" },
      { name: "Patrol", class: "USMStateInstance" },
      { name: "Chase", class: "USMStateInstance" },
      { name: "Attack", class: "USMStateInstance" }
    ],
    transitions: [
      { source: "Idle", target: "Patrol" },
      { source: "Patrol", target: "Chase" },
      { source: "Chase", target: "Attack" },
      { source: "Attack", target: "Idle" }
    ]
  }
}})
```

### Scaffold + Customize + Compile
```
logicdriver_query({ action: "scaffold_horror_encounter", params: {
  save_path: "/Game/StateMachines/SM_GhostEncounter",
  phases: ["Ambient", "Whispers", "Apparition", "Chase", "Vanish"]
}})
logicdriver_query({ action: "compile_state_machine", params: {
  asset_path: "/Game/StateMachines/SM_GhostEncounter"
}})
```

## Validation Catches

- Orphan states (no in/out transitions except entry)
- Dead-end non-terminal states
- Unreachable states from entry point
- Missing `compile_state_machine` after structural edits
- Circular transitions without exit condition
- SM exists but no actor has SMInstance component referencing it
