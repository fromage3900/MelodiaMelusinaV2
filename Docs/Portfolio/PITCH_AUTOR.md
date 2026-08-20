# Engineering Pitch: Autor (Toronto) — Practical AI & MCP Engineering

**Target:** Autor (Toronto)
**Focus:** Practical AI / MCP Engineering, JSON-RPC Proxy Architecture
**Date:** 2026-08-18

---

## 1. The Engineering Challenge

Autor focuses on the unglamorous infrastructure that makes AI systems reliable — protocol design, strongly-typed validation, and live-editing pipelines. The Melusina project has solved three engineering challenges that align directly with Autor's technical focus:

1. **JSON-RPC Proxy Architecture for 1,330 MCP Actions**
2. **Live-Editor Bridge (Monolith) with Bidirectional Feedback**
3. **Strictly Typed JSON Schema Validation at the Proxy Boundary**

All three are implemented, tested, and operational — not research prototypes.

---

## 2. JSON-RPC Proxy Architecture

The core of Melusina is a **JSON-RPC proxy layer** that decouples the agent-facing interface from the execution engine. This isn't a thin pass-through — it's a routing plane with:

- **Request/response multiplexing** across tool calls
- **Namespaced dispatch** that scopes 1,330 actions into 24 logical domains
- **Wire-protocol stability** that survives schema drift on either side
- **Structured error propagation** that lets the agent reason about failures without parsing stack traces

The proxy means the agent never talks directly to the editor. It talks to a typed, testable boundary that can be versioned, mocked, and reasoned about independently.

This is implemented in `deploy/agent_bridge_mcp.py` and `Tools/mcp_client.py`, with the proxy handling all communication between the LLM and the live UE5 editor.

---

## 3. Monolith Live-Editor Bridge

On the other side of the proxy sits **Monolith**, the live-editor bridge that turns agent tool calls into real-time visual feedback inside the Unreal Editor. The bridge handles:

- **State synchronization** between the agent's tool invocations and the editor's document model
- **Hot-reload validation** — schema changes propagate without restarting the host
- **Bidirectional feedback** — editor state flows back into the agent context so the next tool call is informed by what just happened on screen
- **1330 actions across 24 namespaces** covering editor manipulation, mesh analysis, material graph editing, animation state machines, Blueprint compilation, VFX systems, and C++ reflection

The Monolith architecture is documented in `Plugins/Monolith/Docs/MONOLITH_GUIDE.md`, and the 7 DLLs (`MonolithEditor`, `MonolithMesh`, `MonolithMaterial`, `MonolithAnimation`, `MonolithBlueprint`, `MonolithUI`, `MonolithNiagara`, `MonolithReflectionIntel`) are compiled and operational.

---

## 4. Strictly Typed JSON Schema Validation

Every one of the 1,330 actions is guarded by **JSON Schema validation** at the proxy boundary. This isn't optional linting — it's enforced at runtime:

- **Input validation** before dispatch — malformed tool calls are rejected at the edge, never reaching execution
- **Output validation** on return — the schema guarantees the agent gets back what it expects, or a typed error
- **Schema-as-contract** — the JSON Schema definitions are the single source of truth for what each tool accepts and returns, generating typed clients and documentation automatically

This turns "the agent sent bad JSON" from a debugging nightmare into a one-line validation error with a pointer to the offending field.

The schema registry is at `specs/mcp/melodia_mcp_tools.v1.json`, and the validation layer is in `Tools/mcp_client.py`.

---

## 5. Deployment Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENTIC CLIENT / LLM                        │
│              (Nous Hermes 3, LongCat, Qwen 2.5, DeepSeek)       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                   deploy/agent_bridge_mcp.py                      │
│                   - JSON-RPC Proxy Layer                          │
│                   - Request/Response Multiplexing                 │
│                   - Namespaced Dispatch (24 domains)              │
│                   - Schema Validation (JSON Schema)               │
│                   - Structured Error Propagation                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Monolith Live-Editor Bridge                   │
│                     (Port 9316, 1330 actions)                     │
│                                                                   │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│   │  Editor     │ │   Mesh     │ │  Material  │ │ Animation  │   │
│   │  Query      │ │  Query     │ │   Query    │ │   Query    │   │
│   └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│   │ Blueprint  │ │    UI      │ │  Niagara   │ │ Reflection │   │
│   │  Query     │ │  Query     │ │   Query    │ │   Intel    │   │
│   └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Unreal Engine 5.8 Runtime                      │
│                    (Actor spawning, Blueprint                     │
│                     compilation, C++ CDO properties)              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Why This Matters for Autor

AI engineering at scale is an infrastructure problem. Agents that work in demos but fail in production usually fail because of:

1. **Untyped boundaries** — stringly-typed tool calls that silently corrupt
2. **Tight coupling** — the agent and the application are hard to test or evolve independently
3. **Missing validation** — errors surface deep in execution where they're expensive to recover from

Melusina's architecture addresses all three:

- The **JSON-RPC proxy** gives a testable boundary between agent and editor
- **Monolith** provides real-time feedback without coupling the agent to the editor's internals
- **Strict JSON Schema validation** catches errors at the edge where they're cheap

This is the kind of infrastructure Autor values — systems that work every time, not just in the demo.

---

## 7. Evidence

| Claim | Evidence Source |
|-------|-----------------|
| 1,330 actions | `Plugins/Monolith/` — 7 DLLs, 24 namespaces |
| JSON-RPC proxy | `deploy/agent_bridge_mcp.py`, `Tools/mcp_client.py` |
| Monolith bridge | `Plugins/Monolith/Docs/MONOLITH_GUIDE.md` |
| Schema validation | `specs/mcp/melodia_mcp_tools.v1.json` |
| Operational status | `Saved/Audit/monolith_probe.json` — ping: true |
| Test coverage | `Tools/test_melodia_mcp.py` — 13/13 pass |

---

## 8. Closing

Melusina provides a working reference implementation of the exact infrastructure Autor specializes in: JSON-RPC proxy architecture, live-editor bridges, and strictly typed validation boundaries. The system is compiled, benchmarked, and operational against UE 5.8.

Autor specializes in the infrastructure that makes AI systems reliable. Melusina is that infrastructure, running in production on a AAA game engine. Let's build tooling that the rest of the industry will copy in two years.

---

*Document: PITCH_AUTOR.md — Autor Portfolio Pitch*
*Target: Autor (Toronto)*
*Focus: JSON-RPC Proxy, Monolith Live-Editor Bridge, Strict JSON Schema Validation*
