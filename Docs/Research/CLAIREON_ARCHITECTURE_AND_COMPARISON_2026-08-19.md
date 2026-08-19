# Claireon Architecture & Three-Way Comparison — August 2026

Primary-source research. Every architectural claim cites the repo, commit,
issue, or blog post it came from.

---

## Part 1: Claireon Architecture (what "600+ tools" actually means)

### The MCP surface the agent sees

The agent sees **exactly two tools** (plus one meta-tool):

| MCP tool | What it does |
|----------|-------------|
| `tool_search` | Hybrid discovery: SQLite FTS5 keyword index + vendored `bge-small-en-v1.5-int8` ONNX embedding model (MIT). Returns ranked results. Agent queries with natural language or tool names. |
| `python_execute` | Runs arbitrary Python in the editor process. All catalog tools are callable as `claireon.<tool_name>(...)` via this single entry point. |
| `proxy` | Meta-tool for proxy operations (launch editor, query status). Only present when proxy is running. |

Source: believer-oss/Claireon README, commit 3b724d0.

### What "600+ tools" means

The 600+ tools are **C++ tool implementations** registered in the catalog,
discoverable via `tool_search`, and callable via `python_execute`. They are
NOT 600 MCP tools — they are 600 operations behind two MCP tools.

The agent flow is:
1. Agent calls `tool_search("blueprint compile")` → gets ranked list
2. Agent calls `python_execute("claireon.bp_compile(asset_path='...')")` → executes

This is architecturally the opposite of StraySpark (400 individual MCP tools),
UAIP (730+ individual MCP tools), or Epic native (830 individual toolset tools).
Claireon solved the context problem by putting ALL tools behind a discovery
layer, so the agent's MCP context cost is always ~2 tools regardless of how
many operations exist.

The tool families include:
- Blueprint editing (graphs, properties, components, connections)
- Animation authoring (sequences, montages, notifies, blend spaces, AnimBP)
- State Trees (inspect, edit nodes, runtime state)
- Behavior Trees & EQS
- Widget Blueprints (UMG hierarchies, animations)
- Niagara & PCG (inspect, edit)
- Data Tables (CRUD, CSV/JSON import/export)
- Audio & MetaSounds
- Sequences, cameras, tags, input, landscape
- Perf traces
- CMC (Character Movement Component) inspection

Source: believer-oss/Claireon README features list.

### Tool discovery: SQLite FTS5 + embeddings

Claireon vendors a `bge-small-en-v1.5-int8` embedding model (ONNX, MIT license)
inside the plugin. At server start, it builds:
1. A **SQLite FTS5** keyword index over tool names and descriptions
2. An **embedding vector index** using the vendored model

`tool_search` runs both indexes and fuses the results (keyword + semantic
ranking), returning the top 10 by default. This is the same hybrid retrieval
pattern that Nous Research's Hermes Agent proposed in issue #13332 (BM25 +
semantic, score fusion via RRF).

This means the agent can find tools via exact name ("bp_compile") OR via
natural language intent ("compile a blueprint") — without any tools being in
the MCP manifest.

Source: commit 47a9369, ClaireonEmbeddingModel.cpp, ClaireonToolSearchIndex.cpp,
ClaireonToolEmbeddingIndex.cpp. Test coverage in ClaireonToolSearchCorpusTests.cpp
(737 lines), ClaireonToolSearchIndexTests.cpp (2187 lines).

### Proxy architecture

Claireon's proxy (`claireon_proxy.py`, stdlib-only Python) runs as a singleton
on port 43017. It sits between the MCP client and the in-editor plugin.

Key behaviors:
- **Per-worktree port derivation:** Each Git worktree gets a deterministic
  port (SHA-256 of checkout path, mapped to 49152–65535). Port is written to
  `Saved/Claireon/MCPServer.json`.
- **Session survival:** If the editor crashes or restarts, the proxy holds the
  MCP connection open. The agent doesn't disconnect. When the editor comes
  back, the proxy reconnects internally.
- **Editor-less mode:** The proxy can start without any editor running. It
  serves file-backed prompts (including the `/claireon:workflow` state machine)
  directly from disk. `tool_search` and `python_execute` become available when
  an editor registers. Agent can even launch the editor via
  `proxy(command='launch_editor')`.
- **Token-gated editor ingress:** Bearer token authentication between proxy
  and editor. Not between client and proxy (the MCP client connects to the
  proxy's port normally).

Source: commit 5c2f66a, 242440d, claireon_proxy.py.

### Per-asset exclusive locking

`ClaireonSessionManager.h` implements per-asset exclusive locks. If the agent
opens a Blueprint for editing, another agent or tool call cannot modify the
same asset concurrently. This directly addresses the "two writers on one graph"
problem that this project documented in Decision 025 and safe-working rule 7.

Source: ClaireonSessionManager.h in the repo.

### Known issues (as of Aug 2026)

- **UE 5.7.4 build failure (issue #6, open):** `FNetworkPredictionData_Client_Character::PendingMove`
  removed in 5.7. Affects CMC inspect tools and FlythroughManager. Unresolved.
- **bp_compile hangs indefinitely (issue #7, open):** `claireon.bp_compile()`
  freezes the editor game thread. Direct Python `unreal.BlueprintEditorLibrary.compile_blueprint(bp)`
  does NOT freeze. Bug is in the EditBlueprintGraph session management, not in
  the Python path. Filed on UE 5.5.4 with Claude Code.
- **UE 5.8 compatibility: UNKNOWN.** No issues filed, no confirmed builds.
  The 5.7 build errors suggest 5.8 will also have API-level incompatibilities
  (Substrate, MCP plugin collision, Blueprint compiler changes).

---

## Part 2: Three-Way Architecture Comparison

### A) UE 5.8 Native MCP (Epic)

| Dimension | Description |
|-----------|-------------|
| **Agent-facing surface** | 830 tools across 52 toolsets, all individually registered as MCP tools |
| **Discovery** | `list_toolsets`, `describe_toolset`, `call_tool` meta-tools. No semantic search. Agent must know or guess toolset names. |
| **Context overhead** | Massive. With AllToolsets enabled, the full manifest is ~60K+ tokens. No lazy loading. No catalog mode. |
| **Execution model** | Serial on game thread. One call at a time. HTTP at `localhost:8000/mcp`. |
| **Persistence** | None. Server dies with the editor. No proxy. Session state lost on crash. |
| **Verification** | None built in. Agent must issue separate read calls after writes. |
| **Failure recovery** | None. Crash = full reconnect + lost context. |
| **Security** | No authentication. Local-only. No per-tool permissions. |
| **Extensibility** | Register custom toolsets in C++. Requires editor restart (Live Coding can't register new MCP tools). |
| **Optimized for** | Breadth. Every engine subsystem has tools. Designed as platform infrastructure, not a workflow. |

### B) Claireon (Believer)

| Dimension | Description |
|-----------|-------------|
| **Agent-facing surface** | 2 tools (`tool_search` + `python_execute`). 600+ operations behind discovery layer. |
| **Discovery** | Hybrid SQLite FTS5 + embedding model. Semantic + keyword search. Agent finds tools by intent, not by name. Top-10 default. |
| **Context overhead** | Minimal (~2 tool schemas). Catalog cost is zero regardless of how many tools exist. This is the architecture's defining choice. |
| **Execution model** | Python in-process via `python_execute`. All operations are Python calls to `claireon.<tool_name>()`. Serial on game thread. GC barriers, deferred ops, structured exception handling. Every mutation is an undoable transaction. |
| **Persistence** | Proxy survives editor restarts. Workflow state persisted as JSON on branch. Editor-less mode serves prompts from disk. |
| **Verification** | 9-stage workflow state machine with human checkpoints. Agent never self-merges. Long output spills to grep-able disk files. |
| **Failure recovery** | Crash-first design. Proxy holds connection. Workflow state on branch survives any interruption. |
| **Security** | Bearer token between proxy and editor. `python_execute` is unsandboxed — security relies on trust + source control review. Believer's blog explicitly acknowledges this risk. |
| **Extensibility** | `IClaireonToolProvider` modular-feature interface. Any UE module can register tools without forking. No editor restart needed for tools registered at module load. |
| **Optimized for** | Resilience and workflow continuity. Designed for "dozens of agents running across real sprints" at a studio. |

### C) This Project (OpenCode + Monolith + VibeUE)

| Dimension | Description |
|-----------|-------------|
| **Agent-facing surface** | Monolith: 116 actions via `blueprint_query({action, params})`. VibeUE: ~150 flat tools. UEBlueprintMCP: ~60 tools (disabled by default). All three are individually registered MCP tools. |
| **Discovery** | None. Agent sees full tool manifest. Routing is via prompt rules ("prefer Monolith"). No semantic search, no lazy loading. |
| **Context overhead** | Moderate when one server active (~116 tools). Severe when multiple active. UEBlueprintMCP disabled specifically to manage context. |
| **Execution model** | Monolith: C++ in-process, JSON-RPC to `localhost:9316/mcp`. VibeUE: HTTP to port 8088. UEBlueprintMCP: Python TCP on port 55558. Mixed transports. |
| **Persistence** | None. Session lost on editor crash. No proxy. Workflow state lives in conversation context (lost on compaction). Some state in `project_state.py` output, but not branch-persisted. |
| **Verification** | Manual. Agent must be prompted to re-read after writes. `bp_regression_checker.py` and `graph_reachability.py` exist as offline verification tools but are not called automatically. Echo evidence ledger tracks gate claims. |
| **Failure recovery** | 24 safe-working rules in `AGENTS.md` documenting known failure modes. `project_state.py` for state reconstruction after session loss. No automatic recovery. |
| **Security** | None beyond prompt rules. No authentication on any MCP server. No per-tool permissions. "Never run two surfaces against the same graph" is enforced by convention, not by the harness. |
| **Extensibility** | Monolith is a custom plugin with its own action dispatch. Adding tools requires Monolith source changes. Not modular in the way Claireon's `IClaireonToolProvider` is. |
| **Optimized for** | Shipping this specific game. Every tool, rule, and workaround exists because something went wrong on this project. Project-hardened, not generalizable. |

---

## Part 3: Is OpenCode + Claireon already a thing?

### Direct evidence search results

| Source | Query | Result |
|--------|-------|--------|
| GitHub (believer-oss/Claireon issues) | "opencode" | **No results.** No issues mention OpenCode. |
| GitHub (believer-oss/Claireon PRs) | "opencode" | **No results.** |
| GitHub (anomalyco/opencode issues) | "claireon" OR "unreal" | **No results for Claireon.** Unreal mentions exist only in the context of general MCP discussion. |
| GitHub (general search) | "claireon" + "opencode" | **No results.** |
| Reddit | "claireon opencode" | **No results found.** |
| Web search | "Claireon OpenCode" | **No results.** The search returned the two repos independently, no combined usage. |
| StraySpark blog (Claude Code vs Cursor vs Windsurf) | OpenCode mention | **Not mentioned.** The comparison covers only Claude Code, Cursor, and Windsurf. OpenCode is not in the UE5 AI agent conversation at all. |
| Claireon README | Non-Claude clients | Says "Claude Code **or any MCP-compatible client**" — no specific mention of OpenCode, Cursor, or Windsurf by name. |

### Has Claireon been tested with ANY non-Claude client?

**No public evidence found.** Every Claireon example, blog post, LinkedIn post,
and issue uses Claude Code. The bp_compile hang (issue #7) was filed with
Claude Code. The UE 5.7 build error (issue #6) was filed with Claude Code.
Believer's internal usage (per their blog) is Claude Code.

The README says "or any MCP-compatible client" which is architecturally true —
Claireon speaks standard MCP over HTTP, and any client that can connect to an
HTTP MCP endpoint should work. But this is a specification-level claim, not a
tested-in-production claim.

Claireon's `tool_search` + `python_execute` pattern adds a specific behavioral
requirement: the agent must understand that it should call `tool_search` first
to discover operations, then call `python_execute` with the discovered tool
name. Whether non-Claude models reliably follow this two-step pattern is
untested. StraySpark's blog notes that "GPT-backed Cursor is noticeably less
fluent with MCP tools" and Windsurf's agent "sometimes 'forgets' MCP tools
exist mid-task." These behavioral differences could affect Claireon's
discovery pattern specifically.

### The `opencode-claude-cli` plugin

There IS a community plugin (`leohenon/opencode-claude-cli`) that lets OpenCode
use Claude Code as a backend provider. This routes OpenCode sessions through
the local `claude` CLI. In this configuration, OpenCode becomes a frontend for
Claude Code's harness — MCP servers are resolved Claude-side, not OpenCode-side.
This means you could technically run Claireon from OpenCode via this plugin,
but the MCP connection would go through Claude Code, not through OpenCode's
native MCP client. This is a workaround, not a native integration.

### Conclusion

**No one has publicly used Claireon with OpenCode's native MCP client.**
No issues, no PRs, no blog posts, no Reddit threads, no search results of any
kind confirm this combination. Claireon's architecture is theoretically
compatible (standard MCP over HTTP), but it has never been tested outside of
Claude Code in any public record.

Testing this combination would produce a genuinely novel data point. Not because
the protocol is different, but because the agent behavior (tool discovery
fluency, two-step `tool_search` → `python_execute` pattern, model-specific
tool selection) may differ between Claude and DeepSeek-via-OpenCode in ways
that are undocumented.

---

*All sources verified via web search and GitHub inspection, 2026-08-19.*
