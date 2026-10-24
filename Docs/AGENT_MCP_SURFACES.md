# Agent MCP surfaces

Split out of `AGENTS.md` on 2026-08-13. **Read [`AGENTS.md`](../AGENTS.md) first** — this
file is the surface catalogue and command reference; policy lives there.

## The rule that matters

**One writer per surface. One editor. Always.**

Decision 025 forbids two MCP surfaces on one Blueprint graph. AGENTS.md safe-working
rule 7 forbids two editors. These are the same hazard at two levels: Monolith runs
in-process with the editor, so a second MCP surface is a second writer on the same lock.

Prefer **Monolith** wherever more than one surface can do the job — it is the only one
with the full readback contract (`export_graph`, `get_graph_fingerprint`,
`assert_graph_matches`) that the mandatory verification loop depends on.

All UE surfaces need the editor running. Monolith additionally cannot answer while a
modal dialog blocks the game thread — **grep the log for `MODAL_OPEN` before concluding
the plugin is at fault.**

### Mutation policy

The machine-readable policy is [`specs/mcp_tool_policy.v1.json`](../specs/mcp_tool_policy.v1.json)
and the JCODE coordinator overlay is [`.jcode/melodia_permissions.json`](../.jcode/melodia_permissions.json).
Read-only discovery and graph fingerprints are allowed without approval. Blueprint mutation,
compile, save, and PIE require `editor` approval. Shared generated-content evolution requires
`owner` approval. `ue_editor_command` is deny-by-default; use the verified
`Tools/t3d_safe_wire.py` transaction, which records validate/compile/assert/save/re-export evidence.

## Registered surfaces

`.mcp.json` registers ten servers; `.claude/settings.local.json` enables eighteen (the
extra ones come from user-level config). AGENTS.md previously documented only Monolith.

### Unreal

| Server | Transport | Shape | Default |
|---|---|---|---|
| `agent_bridge` | stdio `deploy/agent_bridge_mcp.py` | Policy-aware routing/status/memory surface. Every exposed tool is cross-checked against `specs/mcp_tool_policy.v1.json`; raw `ue_editor_command` remains denied. | **On** |
| `monolith` | `Plugins/Monolith/Binaries/monolith_proxy.exe` -> :9316 | ~116 Blueprint actions via `blueprint_query({action, params})`, plus ~1426 actions across 24 live namespaces (run `monolith_status()` for the live count). Full graph read, the verification loop, atomic T3D injection. | **On** |
| `it-is-unreal` | HTTP :8088 (VibeUE) | ~150 flat tools (`add_node`, `connect_nodes`, `take_screenshot`, ...). General editor/asset/level queries only — **not** an authoritative graph writer. | On |
| `ueblueprintmcp` | Python venv -> TCP :55558 | ~60 tools incl. Enhanced Input. **Deliberately off** (Decision 027): third-party, unaudited, and overlaps the graph-mutation surface this project consolidated onto one owner. Needs a closed-editor build before first use. | **Off** |

> `UnrealMCP` binds :55557 and is **not** the same service as `ueblueprintmcp` (:55558).
> The port mismatch is configuration drift, not a reason to add a third graph writer.

### DCC and realtime

| Server | Notes |
|---|---|
| `blender` | stdio `uvx blender-mcp`, port **9876**. Connect via **N -> BlenderMCP -> Connect**, not Live Bridge. 9876 is shared with LiveLink TCP — do not run both. |
| `cascadeur` | `deploy/cascadeur_mcp_server.py`, proxy 53151. |
| `envoy` | TouchDesigner via the Embody bridge, port 9870. Runs from a **G:** venv — unavailable on a machine without that drive. |
| `figma` | Design surface. **The API key was public on V2 and rotation is still owed** (carried since 2026-08-11). |

### Model routers

`ollama` (:11434), `deepseek-v4`, `kimi-k3`, plus user-level `qwen`, `mistral-medium-3-5`,
`grok-4-5`, `grok-multi-agent`, `meta-muse-spark`, `nemotron-free`, `gpt-oss-free`.
Routed through `Tools/model_router.py`; per-model cost in `Saved/router_ledger.jsonl`.

**Secrets:** `.mcp.json` holds plaintext provider keys. It is gitignored
(`.gitignore:39`) and has never been committed — keep it that way. Never paste a key
into a doc, a commit message, or a subagent prompt.

### Other

`cpp-compile-feedback` (`Content/Python/mcp_compile_feedback_server.py`) is a second
in-repo MCP server against the same project root. `rider` and `Roblox_Studio` appear in
some sessions from user-level config.

Run `python Tools/validate_mcp_registration.py` after changing either MCP config. It
checks both registrations, the bridge entrypoint, policy coverage for every exposed
tool, deny-by-default, and raw UE command denial.

## MCP servers load at session start

Editing `.mcp.json` mid-session does nothing until the session restarts. Check what you
actually have before promising editor work.

## CI workflows

| Workflow | Runner | Notes |
|---|---|---|
| `echo_gates.yml` | `[self-hosted, Windows, UE58]` | Spec validation, static gate sweep (incl. `art_gates.py`), LFS budget. Queues forever if no runner carries those labels. |
| `unreal_build.yml` | `[self-hosted, Windows, UE58]` | Build.bat + pytest + ruff. Hardcodes the project path to this machine. |
| `release_tag.yml` | `ubuntu-latest` | Refuses to cut a release until all four completion gates have ledger pass rows. |

### Monolith MCP Commands Reference

#### Blueprint
| Action | Purpose |
|--------|---------|
| `blueprint_query:build_blueprint_from_spec` | Inject T3D spec in single transaction |
| `blueprint_query:compile_blueprint` | Compile Blueprint |
| `blueprint_query:get_graph_fingerprint` | Topology fingerprint |
| `blueprint_query:assert_graph_matches` | Verify no unintended rewire |
| `blueprint_query:get_cdo_properties` | Read CDO property values |

#### Material (63 actions)
| Action | Purpose |
|--------|---------|
| `material_query:set_instance_parameter` | Set scalar/vector/texture on material instance |
| `material_query:set_instance_parameters` | Batch-set, single recompile |
| `material_query:get_instance_parameters` | Read all overrides from instance |
| `material_query:recompile_material` | Force material recompile |
| `material_query:get_compilation_stats` | VS/PS instruction counts, compile status |
| `material_query:build_material_graph` | Build material graph from JSON spec |
| `material_query:get_material_properties` | Read material settings (blend, shading, etc.) |
| `material_query:validate_material` | Check for broken connections, unused nodes |
| `material_query:get_all_expressions` | List all expression nodes |
| `material_query:export_material_graph` | Serialize graph to JSON |
| `material_query:import_material_graph` | Import graph from JSON |
| `material_query:begin_transaction` | Start undo group |
| `material_query:end_transaction` | End undo group |

#### Editor
| Action | Purpose |
|--------|---------|
| `editor_query:run_python` | Run headless Python scripts |
| `editor_query:trigger_build` | Trigger full C++ build |
| `editor_query:run_pie_smoke` | Headless PIE smoke test |

#### Project
| Action | Purpose |
|--------|---------|
| `project_query:export_asset_text` | Export asset as T3D text (universal escape hatch) |
| `project_query:search` | Find assets by name/type |
| `project_query:get_asset_details` | Get indexed asset metadata |

#### Niagara (129 actions: 118 in `MonolithNiagaraActions.cpp` + 1 `auto_layout` + 9 timing + 1 `audit_cross_asset_refs`)
The namespace is far larger than the single `add_module` entry this file used to
list. Grouped representative actions below; the full, authoritative list is
`monolith_discover(namespace="niagara")` (terse: name + one-line description).
A read-only surface verifier lives at `Tools/verify_niagara_surface.py`; run it
after any change to docs/policy/scripts.

| Group | Representative actions |
|-------|------------------------|
| Systems | `list_systems`, `create_system`, `create_system_from_spec`, `get_system_summary`, `get_system_diagnostics`, `get_system_property`, `set_system_property`, `get_system_timing`, `set_warmup_profile`, `set_fixed_tick_delta`, `set_require_current_frame_data`, `request_compile`, `save_system`, `diff_systems`, `export_system_spec`, `validate_system`, `preview_system`, `get_compiled_gpu_hlsl` |
| Emitters | `list_emitters`, `add_emitter`, `remove_emitter`, `duplicate_emitter`, `set_emitter_enabled`, `reorder_emitters`, `set_emitter_property`, `get_emitter_summary`, `get_emitter_timing_summary`, `set_emitter_loop_profile`, `rename_emitter`, `get_emitter_property`, `list_emitter_properties`, `create_emitter`, `create_stateless_emitter`, `save_emitter_as_template` |
| Modules | `get_ordered_modules`, `get_module_inputs`, `get_module_graph`, `get_module_output_parameters`, `get_module_input_value`, `add_module`, `remove_module`, `move_module`, `set_module_enabled`, `set_module_input_value`, `set_module_input_binding`, `set_module_input_di`, `set_static_switch_value`, `duplicate_module`, `clone_module_overrides`, `clear_emitter_modules`, `create_module_from_hlsl`, `create_function_from_hlsl`, `get_custom_hlsl_text`, `set_custom_hlsl_text`, `list_module_scripts` |
| Parameters | `get_all_parameters`, `get_user_parameters`, `get_parameter_value`, `get_parameter_type`, `add_user_parameter`, `remove_user_parameter`, `rename_user_parameter`, `set_parameter_default`, `trace_parameter_binding`, `get_available_parameters`, `get_di_functions`, `get_di_properties` |
| Renderers | `list_renderers`, `add_renderer`, `remove_renderer`, `set_renderer_material`, `set_renderer_property`, `get_renderer_bindings`, `set_renderer_binding`, `set_renderer_mesh`, `configure_ribbon`, `configure_subuv`, `list_renderer_properties`, `list_available_renderers` |
| Dynamic inputs / events / sim stages | `list_dynamic_inputs`, `get_dynamic_input_tree`, `remove_dynamic_input`, `add_event_handler`, `get_event_handlers`, `remove_event_handler`, `add_simulation_stage`, `get_simulation_stages`, `remove_simulation_stage`, `set_sim_stage_iteration_count`, `set_sim_stage_execute_behavior`, `set_particle_lifetime` |
| Data interfaces / params / effects | `create_npc`, `get_npc`, `add_npc_parameter`, `remove_npc_parameter`, `set_npc_default`, `create_effect_type`, `get_effect_type`, `set_effect_type`, `set_effect_type_property`, `get_scalability_settings`, `set_scalability_settings` |
| Bulk / search | `batch_execute`, `auto_layout`, `query_niagara`, `search_by_parameter`, `search_by_data_interface`, `search_by_material`, `find_similar_systems`, `find_niagara_references`, `list_system_data_interfaces`, `audit_cross_asset_refs`, `fill_kind` (DataInterfaceArray / Curve / ParameterOverrides) |

Policy: `specs/mcp_tool_policy.v1.json` now declares all 129 as `niagara_query.<action>` (reads `none`, mutations `editor`). Live proof of any action still requires the single editor; see `CURRENT_STATE.md`.

Action index (machine-readable, 129 entries):
```
niagara_query:add_dynamic_input, niagara_query:add_emitter, niagara_query:add_event_handler, niagara_query:add_module, niagara_query:add_npc_parameter, niagara_query:add_renderer, niagara_query:add_simulation_stage, niagara_query:add_user_parameter, niagara_query:audit_cross_asset_refs, niagara_query:auto_layout, niagara_query:batch_execute, niagara_query:clear_emitter_modules, niagara_query:clone_module_overrides, niagara_query:configure_curve_keys, niagara_query:configure_data_interface, niagara_query:configure_ribbon, niagara_query:configure_subuv, niagara_query:create_effect_type, niagara_query:create_emitter, niagara_query:create_function_from_hlsl, niagara_query:create_module_from_hlsl, niagara_query:create_npc, niagara_query:create_stateless_emitter, niagara_query:create_system, niagara_query:create_system_from_spec, niagara_query:diff_systems, niagara_query:duplicate_emitter, niagara_query:duplicate_module, niagara_query:duplicate_system, niagara_query:export_system_spec, niagara_query:find_niagara_references, niagara_query:find_similar_systems, niagara_query:get_all_parameters, niagara_query:get_available_parameters, niagara_query:get_compiled_gpu_hlsl, niagara_query:get_custom_hlsl_text, niagara_query:get_di_functions, niagara_query:get_di_properties, niagara_query:get_dynamic_input_inputs, niagara_query:get_dynamic_input_tree, niagara_query:get_dynamic_input_value, niagara_query:get_effect_type, niagara_query:get_emitter_parent, niagara_query:get_emitter_property, niagara_query:get_emitter_summary, niagara_query:get_emitter_timing_summary, niagara_query:get_event_handlers, niagara_query:get_module_graph, niagara_query:get_module_input_value, niagara_query:get_module_inputs, niagara_query:get_module_output_parameters, niagara_query:get_module_script_inputs, niagara_query:get_npc, niagara_query:get_ordered_modules, niagara_query:get_parameter_type, niagara_query:get_parameter_value, niagara_query:get_renderer_bindings, niagara_query:get_scalability_settings, niagara_query:get_simulation_stages, niagara_query:get_static_switch_value, niagara_query:get_system_diagnostics, niagara_query:get_system_property, niagara_query:get_system_summary, niagara_query:get_system_timing, niagara_query:get_user_parameters, niagara_query:import_system_spec, niagara_query:list_available_renderers, niagara_query:list_dynamic_inputs, niagara_query:list_emitter_properties, niagara_query:list_emitters, niagara_query:list_module_scripts, niagara_query:list_renderer_properties, niagara_query:list_renderers, niagara_query:list_system_data_interfaces, niagara_query:list_systems, niagara_query:move_module, niagara_query:preview_system, niagara_query:query_niagara, niagara_query:remove_dynamic_input, niagara_query:remove_emitter, niagara_query:remove_event_handler, niagara_query:remove_module, niagara_query:remove_npc_parameter, niagara_query:remove_renderer, niagara_query:remove_simulation_stage, niagara_query:remove_user_parameter, niagara_query:rename_emitter, niagara_query:rename_user_parameter, niagara_query:reorder_emitters, niagara_query:request_compile, niagara_query:save_emitter_as_template, niagara_query:save_system, niagara_query:search_by_data_interface, niagara_query:search_by_material, niagara_query:search_by_parameter, niagara_query:search_dynamic_inputs, niagara_query:set_curve_value, niagara_query:set_custom_hlsl_text, niagara_query:set_dynamic_input_value, niagara_query:set_effect_type, niagara_query:set_effect_type_property, niagara_query:set_emitter_enabled, niagara_query:set_emitter_loop_profile, niagara_query:set_emitter_property, niagara_query:set_event_handler_property, niagara_query:set_fixed_bounds, niagara_query:set_fixed_tick_delta, niagara_query:set_module_enabled, niagara_query:set_module_input_binding, niagara_query:set_module_input_di, niagara_query:set_module_input_value, niagara_query:set_npc_default, niagara_query:set_parameter_default, niagara_query:set_particle_lifetime, niagara_query:set_renderer_binding, niagara_query:set_renderer_material, niagara_query:set_renderer_mesh, niagara_query:set_renderer_property, niagara_query:set_require_current_frame_data, niagara_query:set_scalability_settings, niagara_query:set_sim_stage_execute_behavior, niagara_query:set_sim_stage_iteration_count, niagara_query:set_simulation_stage_property, niagara_query:set_spawn_shape, niagara_query:set_static_switch_value, niagara_query:set_system_property, niagara_query:set_warmup_profile, niagara_query:trace_parameter_binding, niagara_query:validate_system
```

Read this file before changing gameplay integration.
