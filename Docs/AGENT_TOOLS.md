# Agent tools

Split out of `AGENTS.md` on 2026-08-13, which had reached 34 KB against a 32 KB
subagent context cap — it no longer fit in the window of the agents that were
supposed to read it.

**Read [`_AGENT_WORKING_AGREEMENT.md`](../_AGENT_WORKING_AGREEMENT.md) and
[`AGENTS.md`](../AGENTS.md) first.** This file is the tool catalogue only. It holds no
policy; where it disagrees with AGENTS.md, AGENTS.md wins.

## Execution contract

Every script under `Content/Python/` runs **inside the editor**, through Monolith:

```
editor_query run_python  ->  Content/Python/<script>.py
```

**Do not spawn `UnrealEditor-Cmd`** and do not run these from a plain shell — they
import `unreal`. One editor, always (AGENTS.md safe-working rule 7), and never point
`run_python` at `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` (the `D_DamageType`
glue failure kills the editor outright — AGENTS.md "Python + skill Blueprints").

Scripts under `Tools/` are the opposite: plain Python, no `unreal` import, runnable
with the editor closed. That split is load-bearing — `Tools/` is what CI can run.

### Core Tools (Already Built)
| Tool | Purpose | Entry Point |
|------|---------|-------------|
| `t3d_safe_wire.py` (2026-08-13) | **The enforced composite wiring operation.** export/fingerprint/validate/mutate/compile(nested-status)/assert/fingerprint/save/re-export, one asset per transaction, hard-stops (never retries) on a dirty compile or `matched:false`, and verifies request-owned required/forbidden nodes, required links, an explicit before→after graph delta, compile count, and saved re-export before committing evidence to `Saved/T3D/<asset>_<ts>/manifest.json`. A non-placeholder request ID and live pre-edit fingerprint are mandatory; request IDs are rejected when already present in the evidence journal. Pure logic is covered by `Tools/test_t3d_safe_wire.py`; request-schema fixtures are checked by `Tools/test_t3d_request_contract.py`. **Live verification against the editor is still owed** — see the module docstring. | `safe_wire()`, CLI via `--asset --graph --spec --expected-fingerprint [--dry-run]` |
| `t3d_blueprint_injector.py` | Thin library wrapper over `build_blueprint_from_spec` for a single one-shot transaction; no CLI, no fingerprint/assert/save loop. Prefer `t3d_safe_wire.py` for anything that needs the mandatory verification sequence. | `T3DBlueprintInjector.inject_into()` |
| `bp_regression_checker.py` | Graph fingerprinting + baseline comparison (fixed 2026-08-06: JSON-RPC envelope to `http://localhost:9316/mcp`) | `fetch_fingerprint()`, `compare_fingerprints()` |
| `continuous_loop.py` | Auto-detect → T3D fix → verify loop | `ContinuousLoop.check_and_fix()` |
| `nl_to_blueprint.py` (fixed 2026-08-13) | NL → local LLM (deepseek-r1:14b default, qwen2.5-coder:7b, or OpenRouter DeepSeek remote) → patch spec → schema check → `t3d_safe_wire.safe_wire()`. No longer defaults to the uninstalled `qwen3:8b`, no longer emits `function_class` (the builder reads `target_class`), no longer reports success after an injection/compile failure. | `main()` with `--bp --prompt [--model --expected-fingerprint --dry-run]` |
| `mcp_client.py` (fixed 2026-08-13) | The shared Monolith JSON-RPC client every `Tools/*` script imports. Honours `MONOLITH_URL` env var, unique request ids, raises/reports on `result.isError`, returns all text content items joined (not just the first). `--selftest` does a read-only `monolith_status` reachability check. | `monolith()`, `discover()`, `selftest()` |
| `pie_smoke_runner.py` | Headless PIE + Monolith polling | `PieSmokeRunner.run()` / `main()` |
| `regression_suite.py` | Quick/full OOD passes | `run_suite()` |
| `t3d_material_curve_injector.py` | Inject material curves, scalars, colors, textures via Monolith | `T3DMaterialCurveInjector.apply_toon_profile_spec()` |
| `t3d_material_inject_demo.py` | Demo: apply TP_Melusina spec with read/apply/verify | `main()` with `--read`, `--verify`, `--all` |

### Verification tools (added 2026-08-08)

Read-only. Each answers a question that a compile, a fingerprint and a smoke test all
answer wrongly.

| Tool | Question it answers |
|------|---------------------|
| `bp_live_path.py` | Is this asset reachable from a configured entry point? `LIVE` / `ORPHAN` / `AMBIGUOUS(n)`. Catches the "perfectly wired graph nothing instantiates" defect. |
| `bp_sweep.py` | Project-wide audit for five shipped defect classes: shadowed parent events, empty-bodied events, dead exec islands, unreachable assets, duplicate short names. |
| `ui_style_audit.py` | What fonts/colours/paddings are actually authored across every widget, and what is the smallest token set covering them. |
| `t3d_dashboard.py` | Where the material-spine complexity lives (offline; `--live` adds drift). |
| `project_state.py` | Derived project state + doc staleness radar. Reads state, never prose. |
| `graph_reachability.py` | Dead exec islands *inside* a graph. Complements `bp_live_path` — a graph can pass this and still be an asset nothing constructs. |
| `rhythm_battle_runtime_probe.py` | Direct-invocation driver for the stock-skill rhythm seam (subsystem + controller events called straight from Python). **Not** gate evidence — see below. |

Two of these have committed assertions because loosening a check is how you blind one:
`Docs/T3D_Baseline/test_canonical.py` and `Tools/test_ui_style_audit.py`. Run them after
touching the corresponding tool.


### Editor-side art + import scripts (`Content/Python/`, added 2026-08-13)

Landed in `840b7650` and never documented. All follow the `run_python` contract above.

| Script | What it does |
|---|---|
| `assign_hero_zentrim.py` | Assigns `MI_ZenTrim_Base4K` to hero props. Closed-editor default is a disk inventory; `--apply` writes. |
| `import_cathedral_fbx.py` | Imports 41 `SM_Cathedral_*.fbx` from `KitbashExport/CathedralKit` to `/Game/EnvSandbox/Meshes/Cathedral/`. |
| `import_hair_flip_geometry_cache.py` | Imports the Flip Fluids Alembic as a Geometry Cache cine asset (Layer C). |
| `import_melusina_v2_test.py` | Imports updated Melusina meshes as `*_V2Test` copies. Never replaces live `SK_Melusina`. Skips the ~33 MB ARP rig unless `--include-rig` (it hung the editor ~15 min once). |
| `import_blender_melusina_idle.py` | Imports the live Blender NLA idle onto `SK_Melusina_Skeleton`. **Unit trap:** live mocap is centimetres, raw Blender FBX is metres; a metres clip collapses the mesh. |
| `wire_melusina_idle_locomotion.py` / `save_melusina_idle_locomotion.py` | Replace only the speed-0 sample on `BS_Melusina_Locomotion`; bake and persist. Walk/run/sprint untouched. |
| `apply_instance_parameter_policy.py` | Applies `specs/instance_parameter_policy.json`. Deterministic (md5-of-path seeded), never clobbers owner-authored overrides, re-reads to verify. **Writer only — it has no `--check` mode**, so it cannot detect drift. |
| `audit_mi_runtime.py` | Full MI audit: parent-is-a-Material, toon_profile, zero-override maskers, duplicate short names, save/reload/re-read. Read-only unless `--fix-parents`. |
| `extract_owner_instance_profiles.py` | Dumps owner-authored MI overrides — the source of the policy vocabulary. |
| `build_material_test_grid.py` / `build_material_render_studio_grid.py` | Swatch grid and portfolio beauty level (void-gradient doctrine; never SkyAtmosphere/UDS). |
| `convert_halftone_trio.py` | Ports and repairs the three MooaToon halftone masters (dangling `MaterialFunctionCall` nodes). |
| `add_nikki_params_to_magicians.py` | Injects the `NikkiHero` layer — `BaseTint` (vector) + `TintStrength` (scalar, default **0.0**, so the master look is unchanged) — as `Lerp(original, BaseTint, TintStrength)` into the Toon BSDF base colour, across 50 converted Magicians masters that had zero parameters. Then creates one `MI_` per master with a per-family `toon_profile` and tint. |
| `lib_gates.py` | Shared honest pass/fail helpers. `gate_material_compiles(asset, max_ps=...)` is the shader-instruction check; it had **zero callers** until `Tools/art_gates.py --live`. |
| `gmm/geometry/procedural_window.py` | Pure-Python window cutter producing a boolean-DIFFERENCE `ModifierStack` for UE intake. No `unreal` import at load. |

### Evidence and lane tooling (`Tools/`)

`Tools/` holds ~190 entries; these are the ones that matter and were undocumented.

| Tool | What it is |
|---|---|
| `art_gates.py` | **The art-side gate** (2026-08-13). Offline: naming, duplicate short names, spine hygiene, budget-spec sanity. `--live`: shader instruction counts via `lib_gates`. Baselined against `specs/art_gates_baseline.json` — pre-existing debt accepted, new violations fail. `--strict` shows the true state. Runs in `echo_gates.yml`. |
| `playtest_harness.py` | Real-input PIE verification and gate recording. This is the tool that does the job AGENTS.md long described as unbuilt manual work. |
| `record_gate.py` | Appends pass/fail rows to `Saved/gate_ledger.json` atomically. `--list`, `--report`. **A gate is certified only when it has a ledger row.** |
| `echo_run.py` | Echo pipeline runner: `list`, `status`, `run static_gates`, `validate-spec`, `record`. |
| `project_state.py` | Derived project state and doc-staleness radar. Reads state, never prose. `--view git\|gates\|baselines\|staleness\|tools\|live\|all`, `--out <path>`. |
| `git_safe_push.py` | LFS batch budget gate. Called by `.githooks/pre-push` and `echo_gates.yml`. 50 MB on `collab/`/`cursor/`/`docs/`, 512 MB elsewhere. |
| `lfs_health_audit.py` | LFS pointer/object health. |
| `model_router.py` | Task-class model selection + cost ledger (`Saved/router_ledger.jsonl`). |
| `lane_dispatcher.py` | Queue-to-lane routing, read-only. **Caveat: routes against the platform queue, not `_TASK_QUEUE.md`.** |
| `memory_index.py` | Keyword index over docs, ledger and playtest reports. |
| `video_review_lane.py` | Free-tier vision review of PIE captures. |
| `melodia_website_root.py` | Shared website-root resolver — use instead of a hardcoded path. |

### Wiring and baseline verification

| Path | What it is |
|---|---|
| `Docs/T3D_Baseline/` | `verify_baseline.py`, `test_canonical.py`, `bp_fingerprints.json`, `material_catalog.json`. The tracked fingerprint baseline; `bp_regression_checker.py` hard-fails when it is missing. |
| `Docs/T3D_Patterns/wiring/` | Shipped-defect fix scripts: `verify_battle_closure.py` (10 invariants), `battleui_debris.py`, `battleui_unshadow.py`, `gameinstance_debris.py`, `sir_cleanup.py`. Live — and undocumented until now. |

Two tools have committed assertions, because loosening a check is how you blind one:
`Docs/T3D_Baseline/test_canonical.py` and `Tools/test_ui_style_audit.py`. Run them after
touching the corresponding tool.

### Declarative Spec Format

#### Toon Profile Spec (`specs/toon_profiles/tp_melusina.json`)
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

#### Niagara MPC Binding (`specs/niagara_mpc_bindings.json`)
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

### Injection Workflow

#### Blueprint Graph Injection
```python
# 1. Load spec
spec = json.load(open("specs/toon_profiles/tp_melusina.json"))

# 2. Inject via Monolith
monolith("blueprint_query", {"action": "build_blueprint_from_spec", "spec": spec})

# 3. Compile & verify
monolith("blueprint_query", {"action": "compile_blueprint", "asset_path": spec["asset_path"]})

# 4. Fingerprint & assert
monolith("blueprint_query", {"action": "get_graph_fingerprint", "asset_path": spec["asset_path"]})
monolith("blueprint_query", {"action": "assert_graph_matches", "asset_path": spec["asset_path"], "expected_fingerprint": "..."})
```

#### Material Curve Injection (Toon Profiles, MPCs)
```python
from t3d_material_curve_injector import T3DMaterialCurveInjector

inj = T3DMaterialCurveInjector()

# Apply full toon profile spec (curves + scalars + textures in one pass)
result = inj.apply_toon_profile_spec(spec)

# Or individual operations:
inj.set_scalar_parameter(asset_path, "DiffuseIndirectScale", 0.3)
inj.set_color_parameter(asset_path, "SomeColor", {"r": 1.0, "g": 0.5, "b": 0.0, "a": 1.0})
inj.write_curve_to_asset(asset_path, "DiffuseRamp", curve_points)
inj.compile_and_verify(asset_path)

# CLI mode:
# python Tools/t3d_material_curve_injector.py --spec specs/toon_profiles/tp_melusina.json
# python Tools/t3d_material_curve_injector.py --asset <path> --set-scalar Brightness=0.5
# python Tools/t3d_material_curve_injector.py --asset <path> --read-curve DiffuseRamp
```

### CI/CD Pipeline

> **Corrected 2026-08-13: `.github/workflows/melodia_ci.yml` does not exist.**
> It was removed on 2026-08-06 (Monolith binaries are gitignored and `windows-latest`
> has no UE 5.8) and the block below was left behind describing it. The real workflows
> are `echo_gates.yml`, `unreal_build.yml` and `release_tag.yml`, all documented in
> [`AGENT_MCP_SURFACES.md`](AGENT_MCP_SURFACES.md) and the workflow files themselves.
> The YAML below is kept only as a record of the intended shape.

#### Historical (removed workflow)
```yaml
name: Melodia CI
on: [push, pull_request]
jobs:
  verify:
    runs-on: windows-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - name: Start Monolith
        run: |
          Start-Process "Plugins/Monolith/Binaries/monolith_proxy.exe" -WorkingDirectory "BS_GodFile"
          Start-Sleep 15
      - name: Verify Blueprints
        run: python Tools/bp_regression_checker.py --all
      - name: Run Continuous Loop
        run: python Tools/continuous_loop.py --max-failures 0
      - name: Run Regression Suite
        run: python Tools/regression_suite.py --full
      - name: PIE Smoke Test
        run: python Tools/pie_smoke_runner.py --smoke
```

### Quality Gates (`specs/ci_gates.json`)

> Until 2026-08-13 this file was read by **nothing** — `grep -rn ci_gates` returned this
> doc and a search index, no code — and its values were strings (`"max_150"`), so no
> parser could have existed. `Tools/art_gates.py` now parses it and enforces the
> checkable budgets. `shader_instructions` and `triangle_budget` normalise to numbers;
> the categorical entries (`0_errors`, `exact_match`, `pass`) are passed through.
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
