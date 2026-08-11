---
name: unreal-combograph
description: Use when working with ComboGraph plugin via Monolith MCP — creating and editing combo graphs, nodes, edges, effects, cues, and scaffolding combo abilities. Triggers on combo, combo graph, combo node, combo edge, combo ability, combo montage, attack chain, hit sequence.
---

# Unreal ComboGraph Workflows

**13 ComboGraph actions** via `combograph_query()`. Discover with `monolith_discover({ namespace: "combograph" })`.

## Key Parameters

- `asset_path` -- ComboGraph asset path (e.g. `/Game/Combos/CG_LightAttack`)
- `node_id` -- node identifier | `montage_path` -- animation montage path
- `save_path` -- destination for new assets | `ability_path` -- gameplay ability path

## Action Reference

| Action | Key Params | Purpose |
|--------|-----------|---------|
| **Read (4)** | | |
| `list_combo_graphs` | `path_filter`? | List all ComboGraph assets |
| `get_combo_graph_info` | `asset_path` | Full graph: nodes, edges, entry points, effects |
| `get_combo_node_effects` | `asset_path`, `node_id` | Gameplay effects on a node |
| `validate_combo_graph` | `asset_path` | Lint: orphans, missing montages, broken edges, unreachable nodes |
| **Create (5)** | | |
| `create_combo_graph` | `save_path`, `graph_name`? | Create new ComboGraph |
| `add_combo_node` | `asset_path`, `montage_path`, `node_name`? | Add node with montage |
| `add_combo_edge` | `asset_path`, `source_node`, `target_node`, `input_type`? | Add transition edge |
| `set_combo_node_effects` | `asset_path`, `node_id`, `effects` | Set gameplay effects |
| `set_combo_node_cues` | `asset_path`, `node_id`, `cues` | Set gameplay cues |
| **Scaffold (3)** | | |
| `create_combo_ability` | `save_path`, `combo_graph_path`, `ability_name`? | Create Gameplay Ability for ComboGraph |
| `link_ability_to_combo_graph` | `ability_path`, `combo_graph_path` | Link existing ability |
| `scaffold_combo_from_montages` | `save_path`, `montages`, `graph_name`? | Full graph from ordered montage list |
| **Layout (1)** | | |
| `layout_combo_graph` | `asset_path`, `horizontal_spacing`?, `vertical_spacing`? | Auto-layout nodes (BFS tree) |

## Technical Notes

- **Reflection-only** -- interacts via UObject reflection + Asset Registry, no direct C++ API linkage. Works with any ComboGraph version.
- **EdGraph sync** -- action handlers update runtime graph AND reconstruct EdGraph automatically.
- **`#if WITH_COMBOGRAPH`** -- probes Plugins/ and Plugins/Marketplace/. Absent = empty stub (0 actions).
- **Settings toggle** -- `bEnableComboGraph` in UMonolithSettings (default: true).
- **GAS integration** -- `create_combo_ability` and `link_ability_to_combo_graph` require both ComboGraph AND GameplayAbilities plugins.

## Common Workflows

### Create combo from scratch
```
combograph_query({ action: "create_combo_graph", params: { save_path: "/Game/Combos/CG_LightAttack" }})
combograph_query({ action: "add_combo_node", params: { asset_path: "/Game/Combos/CG_LightAttack", montage_path: "/Game/Animations/AM_Slash_1", node_name: "Slash1" }})
combograph_query({ action: "add_combo_node", params: { asset_path: "/Game/Combos/CG_LightAttack", montage_path: "/Game/Animations/AM_Slash_2", node_name: "Slash2" }})
combograph_query({ action: "add_combo_edge", params: { asset_path: "/Game/Combos/CG_LightAttack", source_node: "Slash1", target_node: "Slash2", input_type: "LightAttack" }})
```

### Quick scaffold from montage list
```
combograph_query({ action: "scaffold_combo_from_montages", params: {
  save_path: "/Game/Combos/CG_HeavyCombo",
  montages: ["/Game/Animations/AM_Heavy_1", "/Game/Animations/AM_Heavy_2", "/Game/Animations/AM_Heavy_Finisher"]
}})
```

## Anti-Patterns

- **Orphan nodes** -- no edges (except entry). `validate_combo_graph` catches these.
- **Missing montages** -- deleted montage refs. Flagged by validation.
- **Circular edges without exit** -- infinite combo chains.
- **Unlinked ability** -- graph exists but no ability references it.
- **Effect on entry node** -- damage before attack animation plays. Usually unintended.

## Tips

- Use `scaffold_combo_from_montages` for quick setup, then customize with effects/cues
- Always `validate_combo_graph` after editing
- Pair graphs with abilities via `create_combo_ability` or `link_ability_to_combo_graph`
- Open asset in ComboGraph editor after MCP edits to visually verify
