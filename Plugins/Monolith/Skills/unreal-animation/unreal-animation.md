---
name: unreal-animation
description: Use when inspecting or editing Unreal animation assets via Monolith MCP — sequences, montages, blend spaces, animation blueprints, notifies, curves, sync markers, skeletons, IKRig, IK Retargeter, Control Rig. Triggers on animation, montage, ABP, blend space, notify, anim sequence, skeleton, IKRig, retargeter, control rig.
---

# Unreal Animation Workflows

**130+ animation actions** via `animation_query()`. Discover with `monolith_discover({ namespace: "animation" })` for the live figure (this table covers the high-traffic subset).

## Key Parameters

- `asset_path` -- animation asset path (e.g. `/Game/Animations/ABP_Player`)
- `machine_name` -- state machine name (from `get_state_machines`)
- `state_name` -- state within a machine
- `graph_name` -- optional graph filter for `get_nodes`

## Action Reference

| Action | Key Params | Purpose |
|--------|-----------|---------|
| **Montage** | | |
| `add_montage_section` | `asset_path`, `name`, `time` | Add named section |
| `delete_montage_section` | `asset_path`, `name` | Remove section |
| `set_section_next` | `asset_path`, `section`, `next` | Set section playback order |
| `set_section_time` | `asset_path`, `section`, `time` | Move section to specific time |
| **Blend Space** | | |
| `add_blendspace_sample` | `asset_path`, `animation`, `x`, `y` | Add animation at X/Y (auto-bakes triangulation) |
| `edit_blendspace_sample` | `asset_path`, `index`, `x`, `y` | Move existing sample (auto-bakes) |
| `delete_blendspace_sample` | `asset_path`, `index` | Remove sample point (auto-bakes) |
| `bake_blend_space` | `asset_path` | Rebuild `FBlendSpaceData` triangulation (`ResampleData`) — repair externally-authored or pre-fix blend spaces. Returns `has_blendspace_data`, `sample_count`, `baked`, `warning` if a 2D blend space has <3 samples |
| `set_blend_space_interpolation` | `asset_path`, `use_grid`?, `preferred_triangulation_direction`? | Set `bInterpolateUsingGrid` + edge direction (`None`/`Tangential`/`Radial`), resample. Grid mode → `has_blendspace_data:false` is correct |
| **ABP Reading** | | |
| `get_state_machines` | `asset_path` | List all state machines |
| `get_state_info` | `asset_path`, `machine_name`, `state_name` | State details |
| `get_transitions` | `asset_path`, `machine_name` | Transition rules |
| `get_blend_nodes` | `asset_path` | Blend node trees |
| `get_linked_layers` | `asset_path` | Linked anim layers |
| `get_graphs` | `asset_path` | All graphs in ABP |
| `get_nodes` | `asset_path`, `graph_name`? | Nodes in graph(s) |
| `get_abp_variables` | `asset_path` | Variables with types and defaults |
| `get_abp_linked_assets` | `asset_path` | Referenced anim assets via Asset Registry |
| **ABP Writing (EXPERIMENTAL)** | | |
| `add_state_to_machine` | `asset_path`, `machine_name`, `state_name`, `position_x/y`? | Add state |
| `add_transition` | `asset_path`, `machine_name`, `from_state`, `to_state` | Add transition |
| `set_transition_rule` | `asset_path`, `machine_name`, `from_state`, `to_state`, `variable_name` OR structured `rule` | Wire a transition condition. The `rule` object's `kind` is `bool` / `auto` / `compare` / `expression`; `expression` takes compound multi-term `terms: [{ lhs, op, rhs, abs?, negate? }]` folded through Boolean AND/OR via `combine: "and"|"or"` |
| `remove_anim_state` | `asset_path`, `machine_name`, `state_name`, `remove_dependent_transitions`? | Remove state + tear down inner graph. Refuses to remove the current entry state — re-point first. `remove_dependent_transitions` defaults `true` |
| `set_anim_entry_state` | `asset_path`, `machine_name`, `state_name` | Re-point Entry node at an existing state. Returns previous target; `unchanged` when already the entry |
| `remove_anim_transition` | `asset_path`, `machine_name`, `from_state`, `to_state` | Remove a from→to transition. Reports `matched_transition_count` |
| **ABP Graph Authoring** | | |
| `add_apply_additive` | `asset_path` | Add an Apply Additive node (Base/Additive/Alpha pins) |
| `add_apply_mesh_space_additive` | `asset_path` | Add an Apply Mesh-Space Additive node |
| `add_slot_node` | `asset_path`, `slot_name` | Add a Slot node. `slot_name` validated against the skeleton's slot groups |
| `add_save_cached_pose` | `asset_path`, `cache_name` | Add a Save Cached Pose node |
| `add_use_cached_pose` | `asset_path`, `cache_name` | Add a Use Cached Pose node. Pairs by `cache_name` with the matching save |
| `set_output_pose_source` | `asset_path`, `node` | Wire a node's pose output into the anim graph's Output/Root result pin |
| `set_state_result_source` | `asset_path`, `machine_name`, `state_name`, `node` | Wire a node's pose output into a state's result pin |
| `add_blend_by_int` | `asset_path`, `num_poses` | Add a Blend Poses by Int node grown to `num_poses` pins |
| `add_blend_by_enum` | `asset_path`, `enum_path`, `enumerators`?, `graph_name`?, `state_name`? | Add a Blend Poses by Enum node bound to a `UEnum`: one pose pin per exposed enumerator + a Default/else pin. Skips the auto `_MAX` sentinel and `Hidden` enumerators. `enumerators` exposes a subset. Companion to `add_blend_by_int` |
| `set_sync_group` | `asset_path`, `node`, `name`, `role`?, `method`? | Set a player node's sync group |
| `set_layered_blend_bones` | `asset_path`, `node`, `bones` | Set per-bone branch filters (bone + blend depth) on a Layered Blend Per Bone node |
| `add_anim_control_rig_node` | `asset_path`, `control_rig_class` | Add a Control Rig anim-graph node. IO pins regenerate from the class |
| `add_linked_anim_layer` | `asset_path`, `layer_name`, `interface_class`? | Add a Linked Anim Layer node |
| `add_conduit` | `asset_path`, `machine_name`, `name` | Add a conduit node to a state machine. Its bound graph is a transition-logic graph, not an anim graph |
| **Notifies** | | |
| `set_notify_time` | `asset_path`, `notify`, `time` | Move notify |
| `set_notify_duration` | `asset_path`, `notify`, `duration` | Set notify state duration |
| **Bone Tracks** | | |
| `set_bone_track_keys` | `asset_path`, `bone`, `keys` | Set keyframes |
| `add_bone_track` | `asset_path`, `bone` | Add track |
| `remove_bone_track` | `asset_path`, `bone` | Remove track |
| **Skeleton** | | |
| `add_virtual_bone` | `asset_path`, `source`, `target` | Create virtual bone |
| `remove_virtual_bones` | `asset_path`, `bones` | Remove virtual bones |
| `get_skeleton_info` | `asset_path` | Bone hierarchy, sockets, virtual bones |
| `get_skeletal_mesh_info` | `asset_path` | Mesh details, LODs, materials |
| **IKRig** | | |
| `get_ikrig_info` | `asset_path` | Solvers, goals, chains, skeleton |
| `add_ik_solver` | `asset_path`, `solver_type`, `root_bone`?, `goals`? | Add solver + goals. `solver_type` accepts a friendly alias (`fullbodyik`/`fbik`, `limb`, `pole`, …), exact struct name, or unique substring — Full Body IK now resolves (`root_bone` meaningful for FBIK) |
| `remove_ik_solver` | `asset_path`, `solver_index` | Remove a solver by 0-based index (validated). Returns `removed_index`, `solver_count_after` |
| `get_retargeter_info` | `asset_path` | Source/target rigs, chain mappings |
| `set_retarget_chain_mapping` | `asset_path`, `auto_map`? OR `source_chain`+`target_chain` | Map chains |
| **Control Rig** | | |
| `get_control_rig_info` | `asset_path`, `element_type`? | Hierarchy -- bones, controls, nulls |
| `get_control_rig_variables` | `asset_path` | Animatable controls and BP variables |
| `add_control_rig_element` | `asset_path`, `element_type`, `name`, `parent`?, `control_type`?, `animatable`?, `transform`? | Add bone/control/null |

## Common Workflows

### Inspect ABP state machines
```
animation_query({ action: "get_state_machines", params: { asset_path: "/Game/Animations/ABP_Player" } })
animation_query({ action: "get_transitions", params: { asset_path: "/Game/Animations/ABP_Player", machine_name: "Locomotion" } })
```

### Set up montage section flow (intro -> loop -> outro)
```
animation_query({ action: "add_montage_section", params: { asset_path: "/Game/Animations/AM_Attack", name: "Intro", time: 0.0 } })
animation_query({ action: "add_montage_section", params: { asset_path: "/Game/Animations/AM_Attack", name: "Loop", time: 0.5 } })
animation_query({ action: "set_section_next", params: { asset_path: "/Game/Animations/AM_Attack", section: "Intro", next: "Loop" } })
```

## Posed Skeletal-Mesh Capture (editor:: action)

`editor_query("capture_scene_preview", { asset_path: "/Game/.../SK_Char", asset_type: "skeletal_mesh", animation_path: "/Game/.../A_Idle", seek_time: 0.5 })` renders the skeletal mesh at the requested pose (omit `animation_path` for rest pose). Useful for visually verifying retarget output, montage section poses, or sequence keyframes. See `monolith_guide(section="recipes")` entry "Visual introspection — going beyond thumbnails".

## Rules

- Editing tools modify assets **live in the editor** -- changes are immediate
- Primary param is `asset_path` (not `asset`)
- `get_nodes` accepts optional `graph_name` filter
- Use `project_query("search", { query: "AM_*" })` to find animation assets first
- ABP write actions are **EXPERIMENTAL** -- always compile after and check for errors
- `set_retarget_chain_mapping`: `auto_map: true` for automatic OR explicit `source_chain`+`target_chain`
- `add_control_rig_element`: `animatable` uses `IsAnimatable()` internally -- not a raw bool field
- Blend space mutators (`add/edit/delete_blendspace_sample`, `set_blend_space_axis`) now auto-bake the triangulation (`ResampleData`) after each edit, so MCP-authored blend spaces no longer ship empty and A-pose at runtime. For blend spaces authored externally or before this fix, call `bake_blend_space` once to repair. In grid mode (`use_grid: true`) an empty triangulation / `has_blendspace_data: false` is correct, not a failure
- `add_ik_solver`: `solver_type` resolves against the live solver-struct table (alias -> exact struct name -> unique substring); an ambiguous value returns the candidate list. Full Body IK now adds correctly
- `auto_layout`: use `formatter: "builtin"` (also the `"auto"` fallback) for a dependency-aware anim-graph layout that works WITHOUT Blueprint Assist, so layout works in release builds where Blueprint Assist is compiled out
- `set_anim_node_pin_binding` now bootstraps the binding object on previously-unbound nodes, so it works on a node that has no binding yet instead of refusing it
- `set_transition_rule`: pass a structured `rule` object instead of authoring rule-graph nodes by hand — `kind` is `bool` / `auto` / `compare` / `expression`. The `expression` kind builds compound multi-term conditions (`terms: [{ lhs, op, rhs, abs?, negate? }]` folded through Boolean AND/OR via `combine`); `get_transition_rule` decodes any rule back
