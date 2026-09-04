# CURRENT DISCOVERY OVERRIDE — 2026-09-04

This file contains historical orchestration patterns. **Current agents must read [`AGENT_START_HERE.md`](AGENT_START_HERE.md) first.** References below to `_SESSION_HANDOFF.md` or `_TASK_QUEUE.md` are historical; those scratch files were removed and must not be recreated as current authority.

For laptop/remote work, use `Docs/Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md`. For images/reference boards, use `Docs/Art/VISUAL_REFERENCE_INDEX.md`.

---

# Agent Ecosystem — Solo Developer + Parallel AI Agents

**Paradigm (2026-07-26):** One human developer. Multiple AI agents working in parallel on scoped tasks. No ownership boundaries. No STOP files. No sentinel runners. Direct access to everything.

**How it works:**
1. Human (or Cline as project lead) defines scoped tasks in `_TASK_QUEUE.md`
2. Any AI agent (Claude, DeepSeek, Ollama, future agents) picks a task from the queue
3. Agent reads the relevant scaffolding docs (`_*.md` files) for context
4. Agent executes the task, updates the queue, fills in `_SESSION_HANDOFF.md`
5. Next agent (or human) reviews, continues

**No agent owns any file.** All agents can access everything. The scaffolding documents are the shared context that keeps parallel work coherent.

---

## Available AI Agent Types

| Agent Type | Best For | Access Pattern |
|---|---|---|
| **Claude (Cline)** | Project lead, architectural decisions, pipeline fixes, code generation | Direct file access + UE MCP |
| **DeepSeek** | PCG analysis, material audits, large-scale search/replace | File access, script execution |
| **Ollama (local models)** | Blessing evolution, content generation, creative text | Local inference, file I/O |
| **Hermes** | Health checks, validation, light verification | MCP tool calls |
| **Rider / C++ IDE Agent** | Subsystem C++, automation tests, shader authoring, static analysis | Direct source access, RiderLink, Qodana, Insights profiling |
| **Future agents** | Any scoped task | Follow the same queue + scaffolding pattern |

---

## How an Agent Joins

1. Read `_SESSION_HANDOFF.md` — what's the current state?
2. Read `_TASK_QUEUE.md` — pick an unassigned task
3. Read the relevant phase doc (`_PORTFOLIO_SHIP_CHECKLIST.md` or `_VERTICAL_SLICE_SCOPE.md`)
4. Read `_DECISION_LOG.md` — check for decisions that affect the task
5. **If the task involves Blueprint wiring:** read `Docs/BLUEPRINT_WIRING_SKILL_2026-08-07.md`
   (operating procedure) and `Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md` (API source of truth).
   **Use `ueblueprintmcp` for all Blueprint graph work** — NOT Monolith or it-is-unreal.
6. Execute the task
7. Update `_TASK_QUEUE.md` — mark task as done or report progress
8. Update `_SESSION_HANDOFF.md` — record what was accomplished

**That's the entire onboarding.** No agent boundaries, no ownership docs, no safety lane manuals.

> **Blueprint wiring rule (2026-08-07):** The `ueblueprintmcp` MCP server is the ONLY tool that
> can read/write Blueprint EventGraphs (nodes, pins, compile). Monolith and it-is-unreal cannot.
> Prior handoffs that told agents to use Monolith for wiring are the known root cause of failed
> wiring sessions. The contract doc is the canonical API reference — it supersedes all handoffs
> where they conflict.

## Guarantees

- **All scaffolding files (`_*.md`) are append-only or overwritable by any agent.** There is no file ownership.
- **The task queue is the single source of truth for what's happening.** If it's not in the queue, it's not tracked work.
- **If two agents conflict, the human resolves it.** This is expected ~1% of the time and acceptable for a solo operation.
- **No agent waits for another agent's permission.** Pick a task, do the task, report back.
