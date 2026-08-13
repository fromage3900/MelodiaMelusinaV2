# Melodia Workspace Source of Truth

**Snapshot:** 2026-08-11  
**Scope:** Unreal, ECHO evidence gates, environment-art tooling, portfolio export, website delivery, DCC services, and optional experiments.

This document is the implementation-facing map for the mixed `C:\EnvironmentPortfolio` workspace. It records which tree owns which concern, where state is derived from, and which documentation claims still require verification. It does not authorize deleting or overwriting a duplicate tree.

## Workspace topology

The workspace root is an assembly of separate concerns rather than one Git repository:

| Root | Role | Authority |
|---|---|---|
| `BS_GodFile/` | Unreal project, gameplay C++, ECHO tools, environment tooling, current evidence ledger | Active Unreal/ECHO source for this setup |
| `MelodiaMelusinaV2/` | Second Unreal checkout/snapshot with a largely mirrored project and ECHO surface | Comparison/reference until drift is reconciled |
| `my-site-clean/` | Separate website checkout with its own Git history | Website source candidate; deployment ownership remains to be resolved |
| root `src/`, `wix/`, `generated/`, `public/`, `components/` | Root website/distribution copy and generated handoff material | Keep until mapped against `my-site-clean` |
| `CompatibilityLabs/` | UE 5.8 compatibility projects, plugin experiments, and backups | Isolated references; never treated as production authority |
| `MelodiaMelusina/` | Older archive/review material | Read-only historical reference |
| `.agents/`, `Saved/`, `build/` | Agent handoffs, reports, session/build artifacts | Evidence/context only; generated state is not source |

The root has no usable Git repository boundary. Changes intended for the Unreal project belong to `BS_GodFile`; website changes require an explicit choice between the root website copy and `my-site-clean`.

## Project authority

### Unreal and gameplay

The active project manifest is `BS_GodFile/BS_GodFile.uproject`, associated with Unreal Engine `5.8`. Its runtime code is under `Source/BS_GodFile`, its integration authorities are under `Source/BS_GodFile/MelodiaIntegration`, and its project plugins are under `Plugins/`.

The target gameplay route is:

```text
/Game/Melodia/Levels/Opening/L_MelusinaMorning
  -> /Game/EnvSandbox/Environments/L_KaleidoNave
```

Gameplay authority remains split deliberately:

- QuillScript owns authored narrative and typed terminal results.
- The stock JRPG template owns turn, target, damage, and result mechanics.
- `UMelodiaNarrativeSubsystem` validates and routes `melodia:` intents.
- `DA_MelodiaIntegrationConfig` is the live allowlist authority.
- `UMelodiaTravelSubsystem` owns validated travel.
- `UMelodiaInputContextSubsystem` owns input-context transitions.
- `UMelodiaTokenWalletSubsystem` owns the Melody Token economy.
- Harmonix and `UMelodiaRhythmCombatSubsystem` provide the optional rhythm seam.

Compile/static evidence is not runtime evidence. The current gameplay completion state is ledger-backed, not inferred from older handoffs.

### ECHO evidence pipeline

The ECHO name is canonical. No `ECVHO` identifier was found in the workspace; `ECVHO` is treated as a typo unless a separate pipeline is supplied.

The contract is `specs/echo_pipeline.json`. The implementation entry point is `Tools/echo_run.py`, and the durable evidence state is `Saved/gate_ledger.json`:

```text
author
  -> spec_validate
  -> inject
  -> compile
  -> static_gates
  -> runtime_gates
  -> record
  -> promote
```

The ledger is the claim boundary. A stage or campaign is not complete because a log, handoff, or screenshot says it passed; it is complete only after the required dated ledger row and its re-checkable artifacts exist.

Current active-tree evidence:

- `runtime` has a recorded `fail` row dated 2026-08-11 because earlier runs used probe-injected calls instead of real keyboard input.
- `save_load`, `repeat_consume`, and `package_launch` remain open.
- Existing passes for graph, PIE smoke, materials, and gameplay probes are historical observations and do not close the four current completion gates by themselves.

### Environment-art and portfolio

The environment pipeline is generic and must not require human-owned final Sakura art:

```text
style/biome brief
  -> Blender procedural or imported modular assets
  -> LiveLink FBX/material/animation transport
  -> Unreal import and material crosswalk
  -> universal PCG/material validation in the tracked L_KaleidoNave route
  -> captures, statistics, and manifests
  -> portfolio package
  -> website/Figma/ArtStation handoff
```

The principal code path is:

- Blender addon and world export: `deploy/surreal_arch/`, `Tools/`, `_TouchDesigner/`
- Unreal import/material/PCG code: `Content/Python/`
- portfolio orchestrator: `Content/Python/generate_portfolio.py`
- package adapter: `Content/Python/package_to_website_handoff.py`
- website validation/deployment: root `tools/`, root `.github/workflows/`, and `my-site-clean/`

`DATA_FLOW.md` and the portfolio documents describe Houdini, Figma, and ArtStation boundaries that are partly planned or manual. They must be labelled as such rather than treated as implemented APIs.

## Service contract

| Service | Port | Required for | Health/evidence |
|---|---:|---|---|
| Unreal Monolith MCP | 9316 | ECHO editor gates, Blueprint queries, PIE orchestration | HTTP `/health` and a successful JSON-RPC call |
| Blender LiveLink | 9876 | Blender-to-Unreal geometry/material/animation transport | TCP listener and a test transfer |
| Blender MCP | 9876 | Genome and agent-side Blender control (shared with LiveLink; one live bridge at a time) | HTTP health/tool call |
| VOICEVOX | 50021 | Voice generation only | HTTP `/version` |
| Melusina Voice | 50022 | Custom Melusina voice only | Service-specific health endpoint |
| Ollama | 11434 | Optional local model generation/quantum support | HTTP service check |
| Quantum ranking service | 8008 | Optional experimental layout ranking | FastAPI health/request check |

An editor or DCC service being down is an explicit `HOLD` for the gates that need it; it is not silently converted to a pass.

## Drift and remediation register

| Finding | Impact | Resolution rule |
|---|---|---|
| `BS_GodFile` and `MelodiaMelusinaV2` both contain ECHO manifests/tools | A fix can land in one tree and be absent from the other | Compare before edits; port only reviewed changes |
| Root website and `my-site-clean` duplicate site manifests/workflows | CI and local edits can target different sites | Keep both until one deployment authority is selected |
| `my-site-clean` historically lacked a lockfile while its workflow runs `npm ci` | Reproducible Wix install can fail | Generate and validate a lockfile in the selected website checkout |
| `tools/verify_deployment_manifest.py` used the hyphenated filename while the producer writes `deployment_manifest.json` | Deployment verification can silently skip the real manifest | Support the canonical underscore name and legacy alias |
| `tools/_verify_site_facts.py` used a fixed `G:\EnvironmentPortfolio` path | Validation fails or checks the wrong checkout on this machine | Resolve `MELODIA_WEBSITE_ROOT`, CLI input, then workspace-relative defaults |
| Setup docs and scripts previously disagreed between Blender 5.1 and 5.2 | Collaborators installed different DCC versions | 5.2 is now the production default with configurable environment paths |
| Lightweight onboarding previously omitted the project file and most plugins | MeshBlend/PCGEx could not activate from a sparse checkout | Use the UE-capable manifest and strict validator in `deploy/` |
| `deploy/deploy_all.ps1` is documented but absent | “Full environment” cannot be reproduced from docs alone | Treat autonomous loops as optional; do not claim this launcher exists |
| Production docs claim ECHO tools were removed while the tools are present | Agents can follow an obsolete deletion claim | Derive tool availability from the filesystem and current runner |
| Portfolio aggregation can produce a package with warnings | Package existence alone can look like a successful export | Return failure when required pipeline steps fail; preserve warning details |
| `.mcp.json` is machine-local and contains provider configuration | Copying it can leak credentials or hard-coded paths | Exclude it from setup/sync; use environment variables or a local secret store |

## Environment baseline

The portable contract is:

```text
Unreal Engine: 5.8
Visual Studio: 2022 with C++ desktop/game tooling
Git: Git LFS installed and initialized
Python: 3.11
Node: 20
Blender: 5.2 default; override through configuration when 5.1 compatibility is required
Website: selected root or my-site-clean checkout, never an implicit G: mirror
```

Paths are resolved in this order:

1. Explicit command-line parameter.
2. Environment variable such as `MELODIA_UNREAL_ROOT` or `MELODIA_WEBSITE_ROOT`.
3. `Config/paths.json`.
4. A workspace-relative/default installation location.

Secrets are never supplied through tracked configuration. `.env.local.example` documents names only; actual values remain local.

## Verification order

1. Offline: JSON, Python syntax/tests, Ruff, website lint/assets, path/manifest checks, and documentation drift.
2. Editor: Monolith health, Blueprint compile, reachability/live-path, sweep, UI lint, baseline, `Melodia.Wiring`, and PIE smoke.
3. Runtime: real keyboard rhythm input, save/load across a process restart, repeat-consume idempotence, packaged launch, and result matrix.
4. Record: append evidence-backed ledger rows only for the exact gate observed.
5. Promote: update baselines only when the evidence and source change are reviewable; never promote generated exports as inputs.
