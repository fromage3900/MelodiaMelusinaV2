# Campaign 05 — Environment Art Pipeline (Chapter 2)

**Gate chain:** `ch2_environment.env_asset_author` → `env_asset_inject` →
`env_render_capture` → `env_promote`

**Predecessor:** `ch1_gameplay.promote` (Chapter 1 must be promoted first)

**Lane:** vision → code → vision → orchestrator

## Overview

This campaign moves a Blender generative-design asset through the Melodia T3D
injection pipeline into Unreal Engine, compiles materials, captures portfolio
renders, and promotes the result. It is the archetypal Chapter 2 loop:
authoring happens in Blender (vision lane), injection/compilation in Unreal
(code lane), and capture back in vision.

## Gate 1 — `env_asset_author` (vision lane)

### Evidence required
1. Blender GN script in `deploy/surreal_arch/melodia_gn/` produces a candidate
   mesh with a provenance JSON (`asset_id`, `prompt`, `seed`, `poly_count`).
2. The mesh is exported as FBX to `Content/EnvSandbox/Imports/Pending/`.
3. `run_python_code.txt` log shows 0 errors.

### Record
```
python Tools/echo_run.py record ch2_environment.env_asset_author pass --layer ch2_environment --lane vision --note "GN asset <id> produced, <n> tris"
```

## Gate 2 — `env_asset_inject` (code lane)

### Evidence required
1. `t3d_blueprint_injector.py` succeeds for the mesh with 0 errors.
2. UE material compiles with 0 errors.
3. Shader instruction count ≤ 150 (via `shadersanity` or `umg_shader_stats`).
4. `graph_reachability.py` reports no dead exec islands.

### Record
```
python Tools/echo_run.py record ch2_environment.env_asset_inject pass --layer ch2_environment --lane code --note "material 0 errors, <n> instructions"
```

### Quality gate: `material_compile` must be `0_errors`

## Gate 3 — `env_render_capture` (vision lane)

### Evidence required
1. Beauty, wireframe, and material-grid renders captured via `run_portfolio_capture.py`.
2. Renders saved to `Saved/Portfolio/<asset_id>/` with metadata JSON.
3. `render-specs.json` schema matches `Docs/WebsiteRenderArchive/metadata/render-specs.json`.

### Record
```
python Tools/echo_run.py record ch2_environment.env_render_capture pass --layer ch2_environment --lane vision --note "3 renders + metadata"
```

## Gate 4 — `env_promote` (orchestrator lane)

### Prerequisites
- All three upstream gates must be PASS.
- Verify: `python Tools/echo_run.py topo check-promote ch2_environment.env_promote`

### Evidence required
1. `git add` only exact paths (mesh, material instance, render folder).
2. `git_safe_push.py --check-only` passes LFS budget (512 MB default).
3. `record_gate.py --report` updated.

### Record
```
python Tools/echo_run.py record ch2_environment.env_promote pass --layer ch2_environment --lane orchestrator --note "committed <n> assets, <n> MB LFS"
```

## Lane dispatch

- **vision** → `mistralai/mistral-medium-3-5` (screenshot review, render QA)
- **code** → `deepseek/deepseek-v4-flash` (T3D injection, compile)
- **orchestrator** → `x-ai/grok-4.20-multi-agent` (promote decision)

```bash
# See what's eligible right now
python Tools/echo_run.py topo schedule
# Verify promote readiness
python Tools/echo_run.py topo check-promote ch2_environment.env_promote
```
