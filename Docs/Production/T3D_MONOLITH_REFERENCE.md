# T3D / Monolith / Spec Reference

Extracted from `AGENTS.md` (2026-08-12) so the agent bootstrap stays under the 32 KB
subagent cap. Binding behaviour still lives in `AGENTS.md` + `_AGENT_WORKING_AGREEMENT.md`.

## Declarative Spec Format

### Toon Profile Spec (`specs/toon_profiles/tp_melusina.json`)
```json
{
  "asset_path": "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina",
  "class": "ToonProfile",
  "settings": {
    "DiffuseIndirectScale": 0.3,
    "SpecularIndirectScale": 0.3,
    "ShadowExtinctionCoefficient": 0.3,
    "DiffuseRamp": [
      {"time": 0.0, "color": {"r": 0.034, "g": 0.022, "b": 0.047, "a": 1.0}},
      {"time": 0.3, "color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}},
      {"time": 1.0, "color": {"r": 1.08, "g": 1.04, "b": 0.98, "a": 1.0}}
    ],
    "SpecularRamp": [
      {"time": 0.9, "color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}}
    ],
    "ShadowHatchingPattern": "/Game/EnvSandbox/Materials/ToonProfiles/T_HatchPattern",
    "ShadowingExtinction": 0.3
  }
}
```

### Niagara MPC Binding (`specs/niagara_mpc_bindings.json`)
```json
{
  "NS_Uni_WaterMist": {
    "WaterMist": {
      "emitter_update": {
        "ProximityDriver": {
          "type": "ModuleScript",
          "source": "MPC_ScalarParameterCollection = Engine.MaterialParameterCollection'/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette';\nfloat Proximity = MPC_ScalarParameterCollection.GetScalarParameterValue('PlayerProximity');\nProximitySpawnRateMultiplier = 1.0 + (1.0 - Proximity) * 4.0;"
        }
      }
    }
  }
}
```

## Injection Workflow

### Blueprint Graph Injection
```python
spec = json.load(open("specs/toon_profiles/tp_melusina.json"))
monolith("blueprint_query", {"action": "build_blueprint_from_spec", "spec": spec})
monolith("blueprint_query", {"action": "compile_blueprint", "asset_path": spec["asset_path"]})
monolith("blueprint_query", {"action": "get_graph_fingerprint", "asset_path": spec["asset_path"]})
monolith("blueprint_query", {"action": "assert_graph_matches", "asset_path": spec["asset_path"], "expected_fingerprint": "..."})
```

### Material Curve Injection
```python
from t3d_material_curve_injector import T3DMaterialCurveInjector
inj = T3DMaterialCurveInjector()
result = inj.apply_toon_profile_spec(spec)
# CLI: python Tools/t3d_material_curve_injector.py --spec specs/toon_profiles/tp_melusina.json
```

## CI/CD Pipeline (`.github/workflows/melodia_ci.yml`)

Jobs: Start Monolith → `bp_regression_checker.py --all` → `continuous_loop.py` →
`regression_suite.py --full` → `pie_smoke_runner.py --smoke`.

## Quality Gates (`ci_gates.json`)

```json
{
  "graph_fingerprint": "exact_match",
  "blueprint_compile": "0_errors",
  "material_compile": "0_errors",
  "shader_instructions": "max_150",
  "triangle_budget": "max_250k",
  "pie_smoke": "0_crashes",
  "animation_delta": "threshold_0.05",
  "accessibility": "pass"
}
```

## Monolith MCP Commands Reference

### Blueprint
| Action | Purpose |
|--------|---------|
| `blueprint_query:build_blueprint_from_spec` | Inject T3D spec in single transaction |
| `blueprint_query:compile_blueprint` | Compile Blueprint |
| `blueprint_query:get_graph_fingerprint` | Topology fingerprint |
| `blueprint_query:assert_graph_matches` | Verify no unintended rewire |
| `blueprint_query:get_cdo_properties` | Read CDO property values |

### Material (63 actions)
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

### Editor
| Action | Purpose |
|--------|---------|
| `editor_query:run_python` | Run headless Python scripts |
| `editor_query:trigger_build` | Trigger full C++ build |
| `editor_query:run_pie_smoke` | Headless PIE smoke test |

### Project
| Action | Purpose |
|--------|---------|
| `project_query:export_asset_text` | Export asset as T3D text (universal escape hatch) |
| `project_query:search` | Find assets by name/type |
| `project_query:get_asset_details` | Get indexed asset metadata |

### Niagara
See `Docs/AGENT_MCP_SURFACES.md` -> "Niagara (129 actions)" for the grouped
representative list and policy mapping. Authoritative enumeration:
`monolith_discover(namespace="niagara")`. Read-only surface verifier:
`Tools/verify_niagara_surface.py`.

Action index (machine-readable, 129 entries):
```
niagara_query:add_dynamic_input, niagara_query:add_emitter, niagara_query:add_event_handler, niagara_query:add_module, niagara_query:add_npc_parameter, niagara_query:add_renderer, niagara_query:add_simulation_stage, niagara_query:add_user_parameter, niagara_query:audit_cross_asset_refs, niagara_query:auto_layout, niagara_query:batch_execute, niagara_query:clear_emitter_modules, niagara_query:clone_module_overrides, niagara_query:configure_curve_keys, niagara_query:configure_data_interface, niagara_query:configure_ribbon, niagara_query:configure_subuv, niagara_query:create_effect_type, niagara_query:create_emitter, niagara_query:create_function_from_hlsl, niagara_query:create_module_from_hlsl, niagara_query:create_npc, niagara_query:create_stateless_emitter, niagara_query:create_system, niagara_query:create_system_from_spec, niagara_query:diff_systems, niagara_query:duplicate_emitter, niagara_query:duplicate_module, niagara_query:duplicate_system, niagara_query:export_system_spec, niagara_query:find_niagara_references, niagara_query:find_similar_systems, niagara_query:get_all_parameters, niagara_query:get_available_parameters, niagara_query:get_compiled_gpu_hlsl, niagara_query:get_custom_hlsl_text, niagara_query:get_di_functions, niagara_query:get_di_properties, niagara_query:get_dynamic_input_inputs, niagara_query:get_dynamic_input_tree, niagara_query:get_dynamic_input_value, niagara_query:get_effect_type, niagara_query:get_emitter_parent, niagara_query:get_emitter_property, niagara_query:get_emitter_summary, niagara_query:get_emitter_timing_summary, niagara_query:get_event_handlers, niagara_query:get_module_graph, niagara_query:get_module_input_value, niagara_query:get_module_inputs, niagara_query:get_module_output_parameters, niagara_query:get_module_script_inputs, niagara_query:get_npc, niagara_query:get_ordered_modules, niagara_query:get_parameter_type, niagara_query:get_parameter_value, niagara_query:get_renderer_bindings, niagara_query:get_scalability_settings, niagara_query:get_simulation_stages, niagara_query:get_static_switch_value, niagara_query:get_system_diagnostics, niagara_query:get_system_property, niagara_query:get_system_summary, niagara_query:get_system_timing, niagara_query:get_user_parameters, niagara_query:import_system_spec, niagara_query:list_available_renderers, niagara_query:list_dynamic_inputs, niagara_query:list_emitter_properties, niagara_query:list_emitters, niagara_query:list_module_scripts, niagara_query:list_renderer_properties, niagara_query:list_renderers, niagara_query:list_system_data_interfaces, niagara_query:list_systems, niagara_query:move_module, niagara_query:preview_system, niagara_query:query_niagara, niagara_query:remove_dynamic_input, niagara_query:remove_emitter, niagara_query:remove_event_handler, niagara_query:remove_module, niagara_query:remove_npc_parameter, niagara_query:remove_renderer, niagara_query:remove_simulation_stage, niagara_query:remove_user_parameter, niagara_query:rename_emitter, niagara_query:rename_user_parameter, niagara_query:reorder_emitters, niagara_query:request_compile, niagara_query:save_emitter_as_template, niagara_query:save_system, niagara_query:search_by_data_interface, niagara_query:search_by_material, niagara_query:search_by_parameter, niagara_query:search_dynamic_inputs, niagara_query:set_curve_value, niagara_query:set_custom_hlsl_text, niagara_query:set_dynamic_input_value, niagara_query:set_effect_type, niagara_query:set_effect_type_property, niagara_query:set_emitter_enabled, niagara_query:set_emitter_loop_profile, niagara_query:set_emitter_property, niagara_query:set_event_handler_property, niagara_query:set_fixed_bounds, niagara_query:set_fixed_tick_delta, niagara_query:set_module_enabled, niagara_query:set_module_input_binding, niagara_query:set_module_input_di, niagara_query:set_module_input_value, niagara_query:set_npc_default, niagara_query:set_parameter_default, niagara_query:set_particle_lifetime, niagara_query:set_renderer_binding, niagara_query:set_renderer_material, niagara_query:set_renderer_mesh, niagara_query:set_renderer_property, niagara_query:set_require_current_frame_data, niagara_query:set_scalability_settings, niagara_query:set_sim_stage_execute_behavior, niagara_query:set_sim_stage_iteration_count, niagara_query:set_simulation_stage_property, niagara_query:set_spawn_shape, niagara_query:set_static_switch_value, niagara_query:set_system_property, niagara_query:set_warmup_profile, niagara_query:trace_parameter_binding, niagara_query:validate_system
```

Search Monolith's full namespace (~1426 actions / 24 live namespaces - run `monolith_status()` for the live count) before declaring a capability absent.
