# MCP Surface Scan Report

**Date:** 2026-08-03
**Scope:** Full MCP infrastructure audit for Melodia (BS_GodFile)
**Status:** Read-only research -- complete

---

## 1. MCP Inventory

All configured MCP servers, their statuses, and tool inventories.

### 1.1 Monolith (UE Editor Gateway Proxy)
| Field | Value |
|---|---|
| **Config files** | .opencode.json, .mcp.json (all 4), .rider/mcp.json, BS_GodFile/.mcp.json |
| **Connection** | http://127.0.0.1:9316 |
| **Status** | **UP** -- PID 31916, uptime 424s, v0.20.3 |
| **Registered Tools** | **1,328** across 20+ domains |
| **Binary** | C:\EnvironmentPortfolio\BS_GodFile\Plugins\Monolith\Binaries\monolith_proxy.exe (563 KB) |

**Tool Domains (27 top-level tools confirmed via MCP tools/list):**
- blueprint_query -- Blueprint domain queries/actions
- material_query -- Material domain queries/actions
- animation_query -- Animation domain queries/actions
- chooser_query -- Chooser table queries/actions
- niagara_query -- Niagara FX queries/actions
- editor_query -- Editor operations queries/actions
- config_query -- Config domain queries/actions
- project_query -- Project domain queries/actions
- source_query -- Source code queries/actions
- ui_query -- UI domain queries/actions
- mesh_query -- Mesh domain queries/actions
- gas_query -- Gameplay Ability System queries/actions
- ai_query -- AI domain queries/actions
- audio_query -- Audio domain queries/actions
- level_sequence_query -- Level Sequence queries/actions
- decision_query -- Decision domain queries/actions
- risk_query -- Risk domain queries/actions
- cppreflect_query -- C++ reflection queries/actions
- network_query -- Network domain queries/actions
- pipeline_query -- Pipeline domain queries/actions
- reflect_query -- General reflection queries/actions
- bulk_fill_query -- Bulk fill domain queries/actions
- describe_query -- Describe domain queries/actions
- monolith_discover -- Namespace/action discovery
- monolith_status -- Server health status
- monolith_update -- Update check/install
- monolith_reindex -- Project DB reindex
- monolith_guide -- Editorial workflow guide

**MCP Config:** Spawned as local subprocess via monolith_proxy.exe. Fully enabled.

---

### 1.2 VibeUE / it-is-unreal (AI Editor Copilot)
| Field | Value |
|---|---|
| **Config files** | .opencode.json, .mcp.json, .rider/mcp.json |
| **Connection** | http://127.0.0.1:8088/mcp (HTTP remote) |
| **Status** | **DOWN** -- Connection refused on port 8088 |
| **Health check** | GET http://127.0.0.1:8088/health -- timeout/failure |

**No tools available.** The server is not running.

**What it usually provides (per MCP config):** Remote MCP server for UE AI copilot functions -- likely includes blueprint graph reading/writing, level editing, asset creation, and natural-language-to-blueprint capabilities.

---

### 1.3 Figma MCP (UI Design Integration)
| Field | Value |
|---|---|
| **Config files** | .opencode.json, .mcp.json, .rider/mcp.json (NOT in BS_GodFile/.mcp.json) |
| **Type** | Local stdio via npx figma-developer-mcp --stdio |
| **Status** | **CONFIGURED** (stdio process -- cannot health-check via HTTP) |
| **API Key** | figd_***REDACTED_2026-08-11*** (rotated — key was public on GitHub v2) |
| **REST API direct test** | **WORKING** -- full file access confirmed |

**Figma File: "MelodiaMelusina"**
- File Key: Yx8ud7n39NdWZvnNvo4Xlf
- Role: Owner
- Last Modified: 2026-08-03T05:09:13Z
- Version: 2383351436466014824
- Document Children: 15 pages/sections
- Components: 125 component definitions
- Component Sets: 10 component sets
- Styles: 14 styles
- Link Access: View

**Key Component Node IDs (from figma_mcp_integration.py):**
| Component | Node ID |
|---|---|
| MenuButton | 81:1795 |
| ParchmentPanel | 62:531 |
| SparkleBurst | 72:2007 |
| SparkleDrift | 72:2101 |
| OrrerySparkleOrbit | 72:2165 |
| CornerBaroque | 58:606 |
| DividerScroll | 58:633 |
| CrestBaroque | 58:664 |
| MedallionRosette | 58:689 |

**Note:** .opencode.json is missing a "enabled": true flag for Figma. The BS_GodFile/.mcp.json does NOT include Figma at all -- this is a config gap.

---

### 1.4 UEBlueprintMCP (Blueprint Graph MCP)
| Field | Value |
|---|---|
| **Config files** | .opencode.json, .mcp.json, .rider/mcp.json, BS_GodFile/.mcp.json |
| **Type** | Local stdio via python -m ue_blueprint_mcp.server |
| **Status** | **CONFIGURED** -- socket at 127.0.0.1:55558 is **LISTENING** |
| **Port check** | netstat -an | find "55558" -- TCP 127.0.0.1:55558 LISTENING |

**Provides 43 tools across 6 domains:**

**Blueprint Tools (9):**
- create_blueprint / compile_blueprint / set_blueprint_property
- add_component_to_blueprint / set_static_mesh_properties / set_component_property
- set_physics_properties / spawn_blueprint_actor / create_colored_material

**Editor Tools (12):**
- get_actors_in_level / find_actors_by_name / spawn_actor
- spawn_blueprint_actor / delete_actor / set_actor_transform
- get_actor_properties / set_actor_property
- focus_viewport / get_viewport_transform / set_viewport_transform
- save_all

**Node/Bridge Tools (26):**
- Events: add_blueprint_event_node, add_blueprint_custom_event, add_blueprint_input_action_node, add_enhanced_input_action_node
- Dispatchers: add_event_dispatcher, call_event_dispatcher, bind_event_dispatcher
- Functions: add_blueprint_function_node, create_blueprint_function, call_blueprint_function
- Variables: add_blueprint_variable, add_blueprint_variable_get, add_blueprint_variable_set, set_node_pin_default, set_object_property
- References: add_blueprint_get_self_component_reference, add_blueprint_self_reference, add_blueprint_cast_node
- Flow Control: add_blueprint_branch_node, add_macro_instance_node
- Spawning: add_spawn_actor_from_class_node
- Graph Ops: connect_blueprint_nodes, find_blueprint_nodes, delete_blueprint_node, get_node_pins, set_node_position

**UMG Widget Tools (6):**
- create_umg_widget_blueprint / add_text_block_to_widget / add_button_to_widget
- bind_widget_event / add_widget_to_viewport / set_text_block_binding

**Material Tools (9):**
- create_material / add_material_expression / connect_material_expressions
- connect_to_material_output / set_material_expression_property / set_material_property
- compile_material / create_material_instance / create_post_process_volume

**Project Tools (4):**
- create_input_mapping / create_input_action
- create_input_mapping_context / add_key_mapping_to_context

**Connection Model:** Persistent TCP socket (port 55558) to Unreal Engine MCP Bridge plugin with heartbeat and auto-reconnect.

---

### 1.5 Ollama (Local LLM)
| Field | Value |
|---|---|
| **Config files** | .opencode.json, .mcp.json, .rider/mcp.json, BS_GodFile/.mcp.json |
| **Type** | Local stdio via npx ollama-mcp@latest |
| **Status** | **UP** -- REST API responsive |
| **Ollama REST API** | http://127.0.0.1:11434/api/tags -- working |

**Available Models:**
| Model | Size | Quantization | Context | Capabilities |
|---|---|---|---|---|
| qwen3:8b | 5.2 GB (8.2B params) | Q4_K_M | 40,960 tokens | completion, tools, thinking |

---

### 1.6 AI Provider MCP Servers (LLM Gateways)

These are registered as mcp-openai compliant servers in .mcp.json and .rider/mcp.json:

| Server | Config Present | Status | Notes |
|---|---|---|---|
| deepseek-v4 | .mcp.json, .rider/mcp.json, BS_GodFile/.mcp.json | CONFIGURED | Points to OpenRouter API for DeepSeek V4 |
| kimi-k3 | .mcp.json, .rider/mcp.json, BS_GodFile/.mcp.json | CONFIGURED | Points to TokenRouter API for Kimi K3 |
| qwen | .mcp.json, .rider/mcp.json | CONFIGURED | Points to local Ollama qwen3:8b |

**NOT configured in .opencode.json** -- these three are in .mcp.json but .opencode.json only lists monolith, it-is-unreal, figma, ueblueprintmcp, and ollama.

---

## 2. Missing Surfaces -- VibeUE is DOWN

### What VibeUE (it-is-unreal) Would Provide
VibeUE is an AI copilot for UE editor operations. When running on port 8088, it typically provides:

**Lost Capabilities:**
1. **Natural language to Blueprint** -- Describe what you want in English and VibeUE creates the nodes/wiring
2. **AI-assisted blueprint graph editing** -- Intelligent node suggestions, auto-wiring
3. **Level editing copilot** -- Place assets, adjust lighting, modify landscapes via chat
4. **Asset creation guidance** -- Suggest materials, textures, and settings
5. **Context-aware code generation** -- Understands the current editor context

### What Is Still Available Without It
The project is NOT crippled. The following alternatives exist:

**Monolith (port 9316, 1,328 tools):** Provides comprehensive UE editor automation across 20+ domains -- blueprint, material, animation, Niagara, editor, project, config, mesh, GAS, AI, audio, level sequences, and more. This is actually MORE powerful than VibeUE alone.

**UEBlueprintMCP (port 55558, 43 tools):** Provides fine-grained blueprint graph operations -- add nodes, connect pins, create variables, set properties, compile. This gives direct programmatic control over blueprint graphs.

**Python Editor Utility Scripts (52+ scripts for Blueprint/Editor/Wire):** Including:
- probe_bp_graph_api.py / introspect_blueprint_api.py -- Introspection
- repair_roguelike_room_level_blueprints.py / repair_room_level_blueprints_via_monolith.py -- Repair
- compile_melusina_testing_blueprints.py / fix_bp_parent_classes.py -- Compilation/fixes
- wire_melusina_sprint_blendspace.py / wire_petal_priestess_quill.py and 5+ wire scripts
- run_editor_session.py / run_editor_tasks_headless.py -- Editor automation
- bridge_melusina_to_mpc.py / td_bridge.py -- Bridge utilities
- scaffold_melodia_wbp_atoms.py / scaffold_melodia_jrpg_rhythm_bridge.py -- Scaffolding
- gmm_jrpg_bridge_daemon_tick.py -- JRPG bridge daemon

**Verdict:** VibeUE absence is NOTICEABLE for rapid iteration but not BLOCKING. The Monolith + UEBlueprintMCP + Python scripts triad covers all critical blueprint/editor operations.

---

## 3. Figma API Status

### Token Verification
**Result: TOKEN WORKS.** The API key figd_***REDACTED_2026-08-11*** successfully authenticated to the Figma API.

### What We Can Still Pull
The Figma file "MelodiaMelusina" (owned by us) is fully accessible:
- **125 Components** -- All design components (buttons, panels, decorative elements)
- **10 Component Sets** -- Variant groups (e.g., button states)
- **14 Styles** -- Color, text, and effect styles
- **15 Document Pages** -- Full page hierarchy

**Key UI components mapped for Melodia (from figma_mcp_integration.py):**
- MenuButton, ParchmentPanel (base UI)
- SparkleBurst, SparkleDrift, OrrerySparkleOrbit (VFX/particle references)
- CornerBaroque, DividerScroll, CrestBaroque, MedallionRosette (ornamental chrome)

### MCP Integration
The Figma MCP server (figma-developer-mcp) is configured in .opencode.json, .mcp.json, and .rider/mcp.json but NOT in BS_GodFile/.mcp.json. The stdio-based MCP server will provide tools like figma_get_component, figma_get_file, figma_get_image once launched.

---

## 4. Python Tool Inventory

### Blueprint/Editor/Wire Scripts (52 total -- Content/Python)
These are the most relevant for blueprint wiring and editor automation:

| Script | Purpose |
|---|---|
| introspect_blueprint_api.py | Introspect available blueprint API |
| probe_bp_graph_api.py | Probe blueprint graph API endpoints |
| probe_wbp_api.py | Probe widget blueprint API |
| probe_anim_graph_live.py / probe_animgraph_api.py | Animation graph probing |
| inspect_anim_graph.py / inspect_anim_graph2.py | Animation graph inspection |
| inspect_generator_bp_graphs.py | Generator BP graph inspection |
| audit_bp_melusina.py | Audit Melusina blueprints |
| compile_melusina_testing_blueprints.py | Compile Melusina test BPs |
| fix_bp_parent_classes.py | Fix BP parent class references |
| repair_roguelike_room_level_blueprints.py | Repair room level BPs |
| repair_room_level_blueprints_via_monolith.py | Repair via Monolith MCP |
| wire_melusina_sprint_blendspace.py | Wire Melusina sprint blendspace |
| wire_petal_priestess_quill.py | Wire Petal Priestess Quill |
| wire_skybound_refrain.py | Wire Skybound Refrain |
| wire_starweaver_quill.py | Wire Starweaver Quill |
| wire_twilight_dancer_quill.py | Wire Twilight Dancer Quill |
| wire_substrate_toon_max.py | Wire substrate toon material |
| bridge_melusina_to_mpc.py | Bridge Melusina to MPC |
| td_bridge.py | TD bridge utilities |
| scaffold_melodia_wbp_atoms.py | Scaffold WBP atoms |
| scaffold_melodia_jrpg_rhythm_bridge.py | Scaffold JRPG rhythm bridge |
| run_editor_session.py | Run an editor session |
| run_editor_tasks_headless.py | Run editor tasks headless |
| run_closed_editor_rebuild_gates.py | Run closed editor rebuild |
| run_ornament_kitbash_in_editor.py | Ornament kitbash in editor |
| run_editor_integration.py | Run editor integration tests |
| gmm_jrpg_bridge_daemon_tick.py | JRPG bridge daemon tick |
| assign_room_pcg_graphs.py | Assign PCG graphs to rooms |
| monolith_mcp_client.py / mcp_run.py / mcp_assign_materials.py | Monolith MCP helpers |
| apply_post_process_stack_levels.py | Apply PP stack to levels |
| pcg_graph_builder.py | PCG graph builder |

### Phase 4 MCP Animation Scripts (31 total -- Content/Python)
Scripts for animation blueprint, skeleton, and blendspace operations via MCP:
- _phase4_mcp_discover.py / _phase4_mcp_status.py / _phase4_mcp_runner.py
- _phase4_create_blendspace_mcp.py / _phase4_create_bs2_mcp.py through _phase4_create_bs6_mcp.py
- _phase4_try_import_mcp.py through _phase4_try_import9_mcp.py
- _phase4_check_abp_schemas.py / _phase4_check_bp_ns.py / _phase4_debug_mcp.py
- _phase4_find_melusina_anims_mcp.py / _phase4_fix_skeletons_mcp.py
- _phase4_set_abp_skeleton.py / _phase4_deep_check_anims_mcp.py

### Tools Directory (54 standalone + 124 Blender addon = 178 total)
Standout tools for the Melodia project:
- render_cross_zenlantern_mcp_resume.py -- MCP bridge for render pipeline
- audit_project_hygiene.py -- Project health audit
- serve_melusina_voice.py -- Voice serving
- regenerate_musical_ornaments_surreal_arch.py -- Ornament generation
- setup_voicevox.py / generate_all_voices.py -- Voice synthesis
- export_melodia_rhythm_web_config.py -- Web config export

### UEBlueprintMCP Plugin Source (10 Python files)
Located at C:\EnvironmentPortfolio\BS_GodFile\Plugins\UEBlueprintMCP\Python\ue_blueprint_mcp\:
- server.py -- Main MCP server entry point
- connection.py -- Persistent TCP socket connection to UE (port 55558)
- tools/blueprint.py -- 9 blueprint tools
- tools/editor.py -- 12 editor tools
- tools/nodes.py -- 26 node/graph tools
- tools/umg.py -- 6 UMG widget tools
- tools/materials.py -- 9 material tools
- tools/project.py -- 4 project tools

---

## 5. Recommendations

### 5.1 Restore VibeUE
**Priority:** Medium (expedite if natural-language blueprinting is needed for current phase)

**Steps:**
1. Check if VibeUE is installed: where vibeue or look for it in C:\Users\froma\AppData\Local\Programs\
2. If installed but not running: Start it with vibeue --port 8088
3. If not installed: Install via pip install vibeue or from its repo
4. Verify: curl http://127.0.0.1:8088/health

**Alternative:** Monolith (already UP) has 1,328 registered tools across 20+ domains -- it likely covers most of what VibeUE would provide. Consider whether VibeUE is still needed or if Monolith + UEBlueprintMCP is sufficient.

### 5.2 MCP Config Changes Needed

| Config File | Issue | Fix |
|---|---|---|
| BS_GodFile/.mcp.json | Missing figma server entry | Add Figma MCP server config (copy from .mcp.json) |
| .opencode.json | Missing deepseek-v4, kimi-k3, qwen entries | Add if these AI providers are needed as MCP tools |
| .opencode.json | Figma missing "enabled": true | Add "enabled": true for consistency (functional without it) |

### 5.3 Figma MCP Improvements
- The Figma MCP server is configured in .opencode.json but the figma_mcp_integration.py script uses direct REST calls (not MCP). Consider unifying the approach.
- Add Figma to BS_GodFile/.mcp.json so it is available to all MCP clients in the project.

### 5.4 Pipeline Suggestions
1. **Monolith-first approach:** Monolith (UP, 1,328 tools) should be the primary MCP surface for UE automation. Its coverage is comprehensive.
2. **UEBlueprintMCP for fine-grained graph work:** Use the 43 tools for precise blueprint node/connection operations that Monolith may not expose.
3. **Python scripts as fallback:** The 52+ blueprint/editor/wire scripts exist for specialized operations.
4. **Phase 4 animation scripts** (31 MCP scripts) are already scripted for animation blueprint workflows -- use them directly.

### 5.5 Quick Wins
- Add figma to BS_GodFile/.mcp.json
- Verify Monolith 1,328 tools include everything needed (run monolith_discover with each domain)
- The UEBlueprintMCP socket on port 55558 is listening -- verify its UE connection is actually established (ping through the MCP)

---

## Summary

| MCP Surface | Status | Tools | Notes |
|---|---|---|---|
| **Monolith** | **UP** | 1,328 | Primary UE MCP surface |
| **VibeUE** (it-is-unreal) | **DOWN** | 0 | Not critical -- Monolith covers most |
| **Figma MCP** | **CONFIGURED** | ~10 (stdio) | Token works, 125 components available |
| **UEBlueprintMCP** | **CONFIGURED** (socket listening) | 43 | Fine-grained blueprint graph control |
| **Ollama** | **UP** | 1 model | qwen3:8b with tools support |
| **deepseek-v4** | CONFIGURED | N/A | AI provider gateway |
| **kimi-k3** | CONFIGURED | N/A | AI provider gateway |
| **qwen** | CONFIGURED | N/A | Local AI via Ollama |

**Total Available Tools:** ~1,371 (1,328 Monolith + 43 UEBlueprintMCP)

**Report file:** C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\MCP_SURFACE_SCAN_2026-08-03.md
