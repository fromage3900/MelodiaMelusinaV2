# JCode / Ollama Integration Audit

**Date:** 2026-08-14  
**Scope:** safe support for the Melodia gameplay BP, T3D, and content-package lanes.

## Verified configuration from the read-only audit

- `.jcode/mcp.json` registers the Monolith Unreal proxy and the policy-aware
  `deploy/agent_bridge_mcp.py` route.
- `.jcode/melodia_permissions.json` is currently untracked and protects `.uasset`,
  `.umap`, `Content/_PROJECT`, Sakura, and credentials. Raw Unreal commands are denied;
  `Tools/t3d_safe_wire.py` is the approved mutation path.
- Ollama is configured at `127.0.0.1:11434`. Historical health evidence lists
  `deepseek-r1:14b`, `qwen2.5-coder:7b`, and `hermes3:latest`. This was not freshly
  probed during this audit.
- `deploy/start_ollama_fleet.ps1` launches five detached draft/validation lanes for
  slice content, wardrobe catalog, dialogue, copy, and validation.

## Safe Melodia use

Ollama/JCode may generate or inspect drafts in `Imports/Data`, `Docs`, and other
non-runtime surfaces. It may validate JSON contracts, audit Blueprint exports, and
prepare T3D dry-run requests. Generated JSON/Markdown is proposal material and does
not close a ledger gate.

No Ollama or JCode lane may directly mutate a Blueprint, `.uasset`, `.umap`, save
state, or `_TASK_QUEUE.md`. Live Blueprint changes remain an explicitly owned editor
operation; T3D mutations must use the approved safe-wire path with independent
postconditions and evidence.

## Collision risks

- The shared checkout is heavily dirty and multiple automation files are already
  modified or untracked.
- The Ollama fleet has no shared-checkout lock; duplicate launches can race on drafts,
  logs, and validator output.
- `start_ollama_fleet.ps1` removes the global `deploy/STOP_ALL` marker before spawning;
  do not launch it casually while another lane is active.
- `Imports/*`, `Saved/*`, and health evidence may be ignored by Git, so generated
  output can be invisible to status review.
- The root `.mcp.json` contains plaintext provider API keys and must be treated as a
  credential exposure risk.
- Documentation names models that are not present in the audited fleet, including
  `qwen2.5-coder:14b` and `qwen3.6:latest`.

## Required operating rule

Use Ollama for constrained content proposals and validation only. Promote a proposal
through the shared content contract, a human/owner review, the live Blueprint/T3D
evidence gate, and the task ledger. Never let a daemon-generated file become an
implicit runtime authority.

## New fixture-spec status

The first Skill and TraversalGate fixtures now have contract-only specs:

- `specs/blueprints/fixtures/single_target_resonance_skill.v1.json`
- `specs/blueprints/fixtures/hover_gate_with_dungeon_lock.v1.json`

Both are L1 specification artifacts. They do not claim that the planned Blueprint or
DataAsset exists, compiles, reaches a map, or passes PIE.

## Read-only audit refresh: 2026-08-14

The delegated local-tool audit re-ran the offline path and confirmed **17/17**
contract suites pass, including `Tools/test_ollama_health.py`, MCP policy and
registration, T3D, BP readiness, materialization preflight, and the Skill bridge.
No live Ollama API call, JCode provider login inspection, daemon launch, Unreal
launch, AWS call, or file mutation was performed.

Concrete rebuild follow-ups:

1. **Model contract mismatch:** `Tools/ollama_health.py` and both dialogue/copy
   daemons require `hermes3:latest`, while the model-fleet documentation records
   only `deepseek-r1:14b` and `qwen2.5-coder:7b`. Treat the general lane as HOLD
   until the owner either installs/approves Hermes or removes it from the required
   lane contract. Do not auto-pull a model during rebuild.
2. **Endpoint naming drift:** `model_router.py` uses `OLLAMA_BASE_URL`,
   `nl_to_blueprint.py` uses `OLLAMA_URL`, and `.jcode/mcp.json` uses `OLLAMA_HOST`.
   Normalize these only in a separately owned tooling change; until then, a live
   probe must state which endpoint it used.
3. **Health depth:** version and tag checks do not prove generation. Add a bounded,
   opt-in generation smoke test after the editor/rebuild boundary is stable; it
   must never write evidence by default and must not be used as a runtime game gate.
4. **Safety/config ownership:** `.jcode/melodia_permissions.json` and MCP policy
   files are currently untracked in the dirty checkout. Preserve them and have the
   owner commit them deliberately before relying on a clean checkout. The root
   `.mcp.json` remains a credential-sensitive surface; do not feed it to Ollama or
   expose its provider entries in logs.

The safe usage contract is unchanged: JCode/Ollama may propose or validate JSON,
Markdown, and dry-run T3D specs under non-runtime paths. It may not mutate `.uasset`,
`.umap`, save state, `Content/_PROJECT`, credentials, or `_TASK_QUEUE.md`. Live BP
work still requires one confirmed Monolith owner and the independent T3D evidence
loop.

The current contract-only fixture inventory is now seven files:

- `single_target_resonance_skill.v1.json`
- `hover_gate_with_dungeon_lock.v1.json`
- `first_resonance_world_challenge.v1.json`
- `first_dream_progress_anchor.v1.json`
- `single_stock_enemy.v1.json`
- `repeatable_first_dream_encounter.v1.json`
- `locked_traversal_portal.v1.json`
