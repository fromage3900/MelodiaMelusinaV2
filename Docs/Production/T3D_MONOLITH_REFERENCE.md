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
| Action | Purpose |
|--------|---------|
| `niagara_query:add_module` | Add ModuleScript to Niagara |

Search Monolith's full namespace (~1330 actions / 24 namespaces) before declaring a capability absent.
