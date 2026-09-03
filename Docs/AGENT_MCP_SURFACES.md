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
| `monolith` | `Plugins/Monolith/Binaries/monolith_proxy.exe` -> :9316 | ~116 Blueprint actions via `blueprint_query({action, params})`, plus ~1330 actions across 24 namespaces. Full graph read, the verification loop, atomic T3D injection. | **On** |
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

#### Niagara
| Action | Purpose |
|--------|---------|
| `niagara_query:add_module` | Add ModuleScript to Niagara |

---

Read this file before changing gameplay integration.
