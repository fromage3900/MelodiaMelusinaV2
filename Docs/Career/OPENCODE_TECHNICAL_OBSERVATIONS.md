# Technical Observations for OpenCode — From 4 Months of UE5.8 + MCP

Structured for an engineer receiving this, not a recruiter. Each observation
names the GitHub issue it maps to (where one exists), describes what was
observed in the UE5.8 + Monolith + VibeUE + UEBlueprintMCP environment, and
proposes the concrete data or reproduction path that would be useful.

All observations are from real production use. None are invented.

---

## Observation 1: Multi-server tool manifest causes critical context starvation with 1330+ tools

**Relevant open issues:** #17480, #9350, #16206, #19300, #20489

**What happened:**
Running three MCP servers simultaneously (Monolith: ~116 actions,
VibeUE: ~150 flat tools, UEBlueprintMCP: ~60 tools, plus Epic's native
UE5.8 MCP endpoint: 830 tools across 52 toolsets) meant that any session
with all servers active consumed the majority of the context window on
tool manifests before a single prompt was processed.

**Workaround adopted:**
UEBlueprintMCP was permanently disabled in `.mcp.json` (flagged as
"deliberately off by default"). A custom rule was added to `AGENTS.md`:
"Prefer Monolith where more than one surface can do the job. Never run two
surfaces against the same graph in one session." This was a safety rule, but
the underlying driver was context economics — not just collision risk.

**Why this is useful data:**
The existing issues describe the problem in terms of "many MCP servers with
generic tools." The UE5 case is distinct: ONE server (Epic's native Toolset)
exposes 830 tools, which is more than most users' entire multi-server stack.
The failure mode — agent selecting a plausible-looking but wrong tool from
an 830-tool manifest because the correct one isn't in the top of the schema
— is different from "too many servers." The per-turn `listTools()` overhead
(issue #19300) compounds on every Blueprint compile, which happens dozens of
times per session.

**Concrete data available:**
Session logs showing tool selection errors attributable to manifest
saturation. Before/after context consumption with three servers vs. one.
The exact tool collision scenarios that triggered the "never run two surfaces
against the same graph" rule (Decision 025).

---

## Observation 2: The agent cannot distinguish between "tool failed" and "editor is blocked"

**Relevant open issues:** None found — appears to be a gap

**What happened:**
When a modal dialog appeared in the UE5 editor (FBX import dialog, Blueprint
compile progress, save confirmation), the Monolith MCP server went silent.
OpenCode continued sending tool calls. The calls returned nothing — no error,
no timeout, no indication that the editor was in a blocked state. The agent
interpreted the silence as success and continued, producing cascading
incorrect state.

From `AGENTS.md`, rule 8: "`MODAL_OPEN` in the log is not a hang. A modal
dialog blocks the game thread, so Monolith goes silent and Windows reports
'Not Responding'. Grep for it before concluding the editor is dead — killing
it there costs every unsaved package for nothing."

**Why this is useful data:**
OpenCode has no model for "MCP server is connected but temporarily
non-responsive due to upstream state." The only states it models are
"connected" and "disconnected." In any environment where the MCP server
gates on an external stateful process (a game engine, a long build, a
hardware device), this gap causes compounding errors. The UE5 case is
the clearest production example of this because the editor's modal state
is deterministic and diagnosable.

**Concrete data available:**
Specific session log entries where tool calls returned nothing during
modal state, with timestamps and the resulting incorrect agent actions.
The MODAL_OPEN detection workaround (grep the UE output log) that was
added to the safe-working rules.

---

## Observation 3: Model switching mid-session breaks tool selection heuristics

**Relevant open issues:** #30119, #22043, #13456

**What happened:**
The project runs DeepSeek as the primary model for most tasks. For
spatial geometry reasoning (quaternion math, PCG placement, Blueprint
graph topology), a different model was needed mid-session. OpenCode
requires starting a new session (`/new`) to switch models, which loses
the accumulated session context — including which files were modified,
which tool calls succeeded, and which error patterns were already diagnosed.

In a UE5 session, losing context mid-task is more costly than in a pure
code task: the editor state (unsaved packages, modified assets, compile
status) is not captured by the conversation history. The agent cannot
reconstruct "what the editor currently looks like" from the session
transcript alone.

**Specific variant not covered by existing issues:**
Issue #30119 describes switching on rate limits. The UE5 case is about
switching on *task type* within a session — a model that is excellent at
Blueprint wiring calls (`DeepSeek`) is not the right model for "describe
the spatial relationship between these six actors and which PCG node
should connect to which." The desired behavior is task-routing within a
session, not provider failover.

**Concrete data available:**
The three-tier model topology documented in `AGENTS.md` / jcode swarm
configuration (Hermes 8B → LongCat 14B → Cloud) shows the explicit
routing logic that was built AROUND OpenCode's limitation. This is
direct evidence that the absence of in-session model routing created
architectural complexity in the project.

---

## Observation 4: Subagent hang pattern with long-running build commands

**Relevant open issues:** #31495, #21250, #13841, #17516

**What happened:**
UE5 builds (C++ compilation via `Build.bat`) take 10–40 minutes.
PIE (Play-in-Editor) startup takes 2–5 minutes. When the agent triggered
a compile and waited for output, the session would enter an indefinite
`Thinking` state. The agent had no way to distinguish between:
- The build is running and will complete
- The build failed silently
- The editor crashed and the process is orphaned

From `AGENTS.md`, rule 7: "One editor instance. Always. On 2026-08-08
three ran concurrently on this project: five crash reports in one hour,
assets changing mid-edit, and 39 unsaved packages lost to a forced kill."

**Why this is a distinct data point:**
The existing issues (#31495) describe this as a "start server then test"
workflow problem with web dev servers. The UE5 case has a harder constraint:
the build process itself produces diagnostic output (compiler errors,
linker errors, warning counts) that the agent NEEDS to read to plan the
next step. A generic "run in background" solution doesn't help if the
agent can't poll for and interpret the build output. The agent needs:
(a) non-blocking dispatch, (b) structured polling for completion/failure,
(c) output parsing for error extraction.

The `pie_smoke_runner.py` and `continuous_loop.py` tools in the project
were built specifically to work around this — they poll Monolith for PIE
state rather than waiting on a shell command.

**Concrete data available:**
The `pie_smoke_runner.py` architecture as a worked example of a polling
pattern for long-running UE5 processes. Session logs showing the 45–66s
stall pattern from issue #21250 in a UE5 context. The specific commands
that triggered hangs (full C++ build, PIE startup, shader compilation).

---

## Observation 5: Tool call verification is absent — agent cannot close the edit-verify loop

**Relevant open issues:** None found specifically for this

**What happened:**
In a UE5.8 workflow, every successful-looking tool call must be verified
by a second read-back. Examples from `AGENTS.md`, rule 9: "`success: true`
only means nothing threw. `save_asset` returned inconclusive at least once;
confirm via `list_dirty_packages`." Rule 12: "A committed export is an
output, not an input. Verifiers here re-derive from the live graph every run."

The agent had no native mechanism to:
1. Mark a tool call as requiring verification before proceeding
2. Automatically issue a read-back tool call after a write
3. Treat a verification failure as a first-class signal (not just text)

Every verify-then-proceed pattern had to be specified explicitly in the
prompt. When context was compacted, the verification discipline was often
lost, and agents would proceed on `success: true` without confirming
editor state.

**Why this is useful to OpenCode:**
This is not UE5-specific — it's any MCP surface where writes are
non-atomic or where the tool's return value is not the ground truth.
StraySpark's MCP server added `describe_graph` specifically to close this
loop (agent writes Blueprint nodes, then calls `describe_graph` to verify
its own edits). OpenCode has no equivalent primitive at the harness level.
A `verify_after_write` hook or a tool annotation (`"requires_verification":
true`) would allow MCP servers to declare their tools' verification
requirements, and OpenCode to enforce the read-back automatically.

**Concrete data available:**
The 24 safe-working rules in `AGENTS.md` — a large fraction of them exist
specifically because verification was absent and the agent proceeded on
incorrect state. This is a direct enumeration of what goes wrong when
verification is absent.

---

## Observation 6: Context compaction loses structured knowledge that cannot be reconstructed from prose

**Relevant open issues:** Partial — the context-mode issue #46 (external
project) covers this for Claude Code. No OpenCode-native issue found.

**What happened:**
When context was compacted, the agent lost:
- The decision log (`_DECISION_LOG.md` — 49+ settled questions that must
  not be re-investigated)
- The safe-working rules (`AGENTS.md` — 24 rules with specific commands
  that must never be run)
- The list of protected files (`.gitignore`, `.gitattributes`, specific
  assets)
- The current editor state (which packages are dirty, which Blueprint has
  errors)

After compaction, agents would re-investigate settled questions (e.g.,
repeatedly asking "is `curentMP` a typo?" after it had been confirmed via
live reflection), write to protected files, or run destructive commands that
the safe-working rules prohibit.

**The specific failure mode:**
On 2026-08-08, an agent ran `git checkout -- .` after context compaction,
because the compacted context lost the rule "NEVER RUN `git checkout -- .`"
and the agent derived from the current state that it was the right action.
This silently destroyed five Python files. The files were unrecoverable
because they were uncommitted edits. `AGENTS.md` now begins with a bold
warning section; it was added after this incident.

**Why this is useful to OpenCode:**
This is the clearest production example of compaction safety failure I'm
aware of in any agent environment. The standard suggestion is "put
important rules in the system prompt." But a system prompt that contains
all 24 rules, the decision log, the protected file list, and the current
editor state is too long to be useful — which is the same context-bloat
problem that motivated compaction in the first place. The compaction hook
(`experimental.session.compacting`) that OpenCode exposes (per the
context-mode issue) is the right primitive; the question is what the
compaction protocol should preserve vs. compress.

**Concrete data available:**
The before/after of the incident: the destroyed Python files (lost, but
the context around the incident is in `_DECISION_LOG.md`). The evolution
of `AGENTS.md` from its original form to its current 24-rule form shows
exactly which knowledge compaction could not preserve. The `project_state.py`
tool was built specifically to provide a compaction-safe state summary that
the agent can re-read after any session restart.

---

## Observation 7: The agent treats all MCP servers as equivalent; no priority or trust model

**Relevant open issues:** None found

**What happened:**
The three MCP servers in this project have different characteristics:
- Monolith: high-trust, C++ in-process, native UE5 operations, used for
  all graph writes
- VibeUE: lower-trust, HTTP, used for reads and scene queries
- UEBlueprintMCP: untrusted, third-party, never run against a live graph

OpenCode treats all three identically. There is no way to:
- Mark a server as read-only from OpenCode's side (enforced at the harness,
  not the server)
- Prefer one server over another when both expose overlapping tools
- Prevent the agent from calling a lower-trust server for a write operation

The safe-working rules enforce this via prompt discipline: "Prefer Monolith
where more than one surface can do the job. Never run two surfaces against
the same graph." But this breaks whenever context is compacted or a new
session is started.

**Why this is useful to OpenCode:**
As MCP becomes the standard interface for agentic tool calls, multi-server
environments will be common. The current model (all servers equal) creates
safety problems in any environment where server capabilities overlap but
trust levels differ. A trust-level or permission annotation in `opencode.json`
per MCP server (`"permissions": ["read"]`, `"priority": 1`) would let the
harness enforce routing decisions that currently live only in prompts.

---

## Observation 8: No mechanism for the agent to know when NOT to call a tool

**Relevant open issues:** None found

**What happened:**
Certain tool calls in this project are catastrophically dangerous:
- `delete_asset` on any asset not created in the current session (registers
  a deletion that makes the asset invisible to the registry while the file
  remains on disk — the editor then reports valid metadata with a false-negative
  load, which looks like file corruption and is not)
- Any Python call to anything under `Content/TurnBasedJRPGTemplate/Blueprints/Skills/`
  (triggers a fatal editor crash from a broken enum wrapper)
- `git clean -fd` or `git checkout -- .` (destroys untracked content with
  no recovery path)

These are documented in `AGENTS.md` under "NEVER RUN THESE." But they are
not enforceable at the harness level. The agent can call them if it reasons
its way to them from first principles, especially after context compaction.

**The gap:**
OpenCode currently has no tool-level blocklist or "confirm before executing"
primitive for specific tool calls. Claude Code has a `--allowlisted-tools`
flag that restricts which tools the agent can call. OpenCode's permissions
model is coarser (server-level, not tool-level).

**Why this is useful to OpenCode:**
In any environment where some MCP tools are irreversible or destructive,
the current model puts all safety responsibility on the prompt. A per-tool
blocklist in `opencode.json` (by tool name or pattern), or a "confirm"
annotation that requires human approval before executing specific tools,
would make the harness enforceable rather than advisory.

---

## Observation 9: DeepSeek model behavior differs from Claude in ways that affect MCP tool selection

**Relevant open issues:** None found specifically for non-Anthropic model
behavior differences

**What happened:**
The project routes primarily through DeepSeek (via OpenCode). The entire
UE5+MCP ecosystem is documented and tooled assuming Claude. Every StraySpark
tutorial, every Believer.gg workflow, every PixelsDesign guide assumes Claude
Sonnet or Opus as the executing model.

Differences observed in the UE5.8 context:
- DeepSeek is more likely to generate plausible-looking but hallucinated
  tool call parameters when the tool schema is ambiguous
- DeepSeek recovers better from compiler error feedback when given explicit
  error format hints in the prompt (Claude recovers more naturally)
- DeepSeek is faster and cheaper for high-volume repetitive tool calls
  (material parameter sets, batch Blueprint property reads) but worse for
  multi-step planning with cross-graph dependencies

**Why this is useful to OpenCode:**
OpenCode's explicit value proposition is model-agnosticism. But the UE5.8
MCP documentation (including Epic's own tutorials) only tests with Claude.
If OpenCode surfaces model-specific behavior differences in production
environments with structured MCP tools, that's evidence for whether the
model-agnostic claim holds at the tool-call layer, not just the text layer.
This is user research data from the one environment where both OpenCode's
model-agnosticism and a complex MCP surface are tested simultaneously.

---

## What I'm NOT claiming

- That any of these are OpenCode bugs specifically. Several are upstream MCP
  limitations, UE5 architecture constraints, or agent behavior issues.
- That my workarounds are the right fixes. They're engineering around gaps.
- That this is a complete list. Four months of sessions on one project is one
  data point, not a representative sample.

## What I AM offering

Four months of continuous production use in one of the most complex MCP
environments in the public record, from a user profile (non-programmer,
3D artist, game developer) that is unlikely to be well-represented in
OpenCode's existing telemetry. Every observation above has session logs,
commit history, or documented incidents behind it.

---

*Author: 4th-year 3D major, University of [X]*
*Duration: April–August 2026*
*Setup: OpenCode in JetBrains Rider, DeepSeek primary model, UE5.8 +
Monolith + VibeUE + UEBlueprintMCP + Epic native MCP*
*Project: Melodia/Melusina V2 (JRPG, ~70% complete)*
*Repo: github.com/fromage3900/MelodiaMelusinaV2*
