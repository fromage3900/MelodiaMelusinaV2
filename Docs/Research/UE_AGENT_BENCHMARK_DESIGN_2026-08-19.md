# UE5.8 Agent Architecture Benchmark Design
## Questions 4–10: Experiment Plan for an Individual Developer

*Primary sources: believer-oss/Claireon README + commits, StraySpark catalog-mode
blog, tc-imba/ue-official-mcp, arxiv MCP-Bench paper (2602.15945),
OpenCode issue tracker. Written 2026-08-19.*

---

## Section 4: Architecture Comparison (detailed)

### Already documented

Full three-way comparison is in
`Docs/Research/CLAIREON_ARCHITECTURE_AND_COMPARISON_2026-08-19.md`.
Summary of what each architecture is *optimizing for*:

| Architecture | Optimizing for |
|---|---|
| **Epic native UE5.8 MCP** | Breadth + platform parity. Every engine subsystem exposed. Designed as infrastructure primitive, not a workflow. First-party = supported. |
| **Claireon** | Resilience + workflow continuity at studio scale. Crash-survival, per-asset locks, branch-persisted state, human-gated merges. Context economy via 2-tool surface + semantic discovery. |
| **This project (OpenCode + Monolith + VibeUE)** | Shipping this specific game. Every tool and rule exists because something broke on this project. Project-hardened, not generalizable. |

### The architectural tension the benchmark must test

Claireon and Epic native represent opposite bets:

- **Epic native:** "Expose everything, let the model choose." 830 MCP tools,
  agent selects by tool name.
- **Claireon:** "Expose almost nothing, let the model search." 2 MCP tools,
  agent discovers operations via hybrid semantic search.

The question isn't which has more tools. The question is: **does the agent make
better decisions with 830 choices vs. 2 choices + a search engine?**

There is published evidence for both sides:
- StraySpark measured 60K tokens → 3K (95%) reduction with catalog mode, same
  task completion. *Source: strayspark.studio/blog/mcp-server-context-costs*
- The arxiv CE-MCP paper (2602.15945) found that code-execution-style MCP
  (one program, not many tool calls) reduces token use AND latency but expands
  attack surface. Claireon's `python_execute` IS this pattern.
- tc-imba/ue-official-mcp measured describe_toolset round-trips at 300–700ms
  each, 1,000–3,000x slower than reading a cached Markdown file.

**What is NOT measured:** Whether the agent's tool *selection quality* degrades
with 830 choices on a real UE5.8 project with a specific codebase. That's the
gap this experiment can fill.

---

## Section 5: Task Suite (5–10 tasks on the real project)

Design principle: tasks must be objectively verifiable (pass/fail is
deterministic), drawn from work that already needs to be done, and graduated
in complexity.

### T1: Blueprint read + report (baseline, read-only)
**Task:** Report the names of all custom events in `BP_BattleController`,
whether each has an implementation (non-empty body), and how many nodes each
contains.
**Why:** Tests tool discovery and read accuracy. No writes. Safe on any branch.
**Success:** Exact match against a pre-verified ground truth (run manually once,
record, seal as test fixture).
**Metrics:** Tool calls, failed calls, context tokens used, wall time,
accuracy (exact match vs ground truth).
**Relevance to architecture:** Tests whether the agent can FIND the right
inspection tool without being told its name. Claireon: `tool_search("blueprint
inspect custom events")` → `python_execute`. Epic native: must know
`BlueprintTools.get_blueprint_info` by name.

### T2: Material parameter read + verify (read-only)
**Task:** Read all scalar and vector parameter overrides on
`MI_Melusina_Toon_Base` and confirm the value of `DiffuseIndirectScale`.
**Why:** Tests MCP access to material system. No writes.
**Success:** Correct parameter value reported (sealed fixture).
**Metrics:** Same as T1.

### T3: Single Blueprint property write + verify
**Task:** Set the `bExecutionDrivingHighway` boolean default on
`BP_MelodiaRhythmHUDWidget` to `false`, then read it back to confirm.
**Why:** Write + immediate verification. Tests whether the architecture
closes the edit-verify loop.
**Success:** Read-back matches intended value. No unintended side effects
(check via dirty packages list before/after).
**Metrics:** Tool calls, failed calls, incorrect modifications (was anything
else touched?), verification success rate, human interventions.
**Note:** This is a real property that exists on the project. Ground truth is
known.

### T4: Blueprint compile + error capture
**Task:** Compile `BP_BattleController`. If there are compile errors, report
the error messages. If it compiles clean, confirm with a `0 errors` result.
**Why:** Tests long-running operation handling (Blueprint compile can take
10–60 seconds). Tests whether the agent correctly handles the blocking compile
and captures structured output.
**Success:** Correct error count reported (sealed fixture — run manually, record
the expected count).
**Metrics:** Tool calls, wall time (compile is the long-running part), whether
the agent correctly waited vs. timed out vs. hung, correct error count.
**Architecture test:** Epic native compile blocks the game thread. Claireon's
`bp_compile` has an open bug (#7: hangs indefinitely on even UE 5.5.4 — if this
reproduces on 5.8, it's a critical finding). Monolith has its own compile path.

### T5: PCG graph inspection
**Task:** List all PCG nodes in a specific PCG graph asset (e.g., the main
environment scatter graph), and identify which nodes have connections vs.
isolated nodes.
**Why:** Tests a non-Blueprint system. PCG is a different tool family from
Blueprint. Tests whether the agent discovers the right tool family.
**Success:** Correct node count and connection map (sealed fixture).
**Metrics:** Same as T1. Plus: did the agent correctly identify the PCG tool
family without being prompted?

### T6: Editor state query under stress (modal/hang test)
**Task:** Trigger a save-all operation, then immediately query the list of
dirty packages.
**Why:** This tests the "modal blocking" failure mode. Save-all can trigger
confirmation dialogs. The query after must either wait correctly or report the
blocked state — NOT silently return nothing and continue.
**Success:** Correctly reports either (a) 0 dirty packages after clean save,
or (b) error/timeout state if dialog appeared. NEVER silently returns empty
and proceeds.
**Metrics:** Whether failure mode is detected (yes/no), what the agent did
when blocked (waited / timed out / continued silently / errored).
**Architecture test:** This is directly testing observation #2 from
`OPENCODE_TECHNICAL_OBSERVATIONS.md`. Claireon has a watchdog timeout (60s
default). Epic native has no timeout mechanism.

### T7: Context persistence across simulated session restart
**Task:** (a) Read the Blueprint graph of `BP_MelodiaRhythmHUDWidget` and
summarize it. (b) Simulate a session restart (close and reopen OpenCode, or
force a new session). (c) Without providing any context, ask the agent to
compile the same Blueprint.
**Why:** Tests whether the architecture retains session context across
interruptions. Claireon's proxy + branch-persisted state is specifically
designed for this.
**Success:** (a) Correct summary. (b-c) Agent correctly compiles the Blueprint
without re-reading the graph from scratch OR explicitly reports missing context
and asks.
**Metrics:** Whether the agent correctly handles context loss, token cost of
re-establishing context, human interventions required.
**Architecture test:** Claireon's proxy survives editor restarts. Current setup
loses all state on session end. This is the clearest test of Claireon's stated
primary feature.

### T8: Tool selection under high tool-count condition (tool explosion test)
**Task:** Run T1 (Blueprint read + report) but with ALL MCP surfaces active
(Monolith + VibeUE + Epic native, if using the native path) or with Claireon's
full catalog. Do not hint which tool to use. Measure which tool the agent calls
first, whether it selects correctly, and how many wrong tools it tries before
success.
**Why:** Direct test of tool-explosion hypothesis. Same task as T1, but more
tools in the manifest.
**Success:** Same as T1 (accuracy). But also: first-tool-selection accuracy
(did the agent pick the right tool family on the first call?).
**Metrics:** First-call accuracy, total tool calls, wrong-tool attempts,
context tokens used in tool manifest at session start.
**Key measurement:** Compare context tokens for T1 under:
- Monolith only (~116 tools in manifest)
- Epic native AllToolsets (~830 tools in manifest)
- Claireon (2 tools in manifest, discovery via tool_search)

### T9: Failure recovery after editor crash
**Task:** Start a read task, then kill the editor process mid-task, wait 30s,
restart the editor, then ask the agent to continue the task.
**Why:** Tests Claireon's crash-survival proxy vs. current no-persistence setup.
**Success:** Agent either (a) correctly resumes without full re-initialization
(Claireon path), or (b) detects disconnection and handles gracefully (any path),
or (c) silently produces garbage output (failure mode).
**Metrics:** Recovery time (seconds from restart to first successful tool call),
whether any state from pre-crash session survived, whether agent detected the
interruption.
**Note:** Do this on a test branch only. Kill -9 the editor process (Windows:
Task Manager force kill). This is safe on a branch with no unsaved changes.

---

## Section 6: Tool Explosion Experiment (in detail)

### Hypothesis
Exposing 830 individual MCP tools to an agent produces worse task performance
(lower first-call accuracy, more wasted tool calls, higher context cost) than
a 2-tool surface with dynamic discovery, even for identical tasks.

### What's already known
- StraySpark measured 60K→3K tokens (95% reduction) with catalog mode.
  *This is a context-cost measurement, not a task-quality measurement.*
- tc-imba/ue-official-mcp measured per-toolset round-trip latency at
  300–700ms (vs. 0.3ms for cached Markdown). *Latency, not accuracy.*
- The CE-MCP paper found reduced token use AND latency with code-execution
  patterns, but did not measure UE-specific tool selection quality.

**What is NOT measured in public literature:** Whether the agent selects the
*correct* tool more reliably from a 2-tool discovery surface vs. a 830-tool
flat surface, on a real UE5 project with a real codebase.

### Experiment design

**Condition A:** OpenCode + Epic native MCP (AllToolsets, ~830 tools in manifest)
**Condition B:** OpenCode + Claireon (2 tools in manifest, discovery via tool_search)
**Condition C:** OpenCode + Monolith only (~116 tools, current setup)

**Tasks:** Run T1, T2, T5, T8 (the read-only tasks) under all three conditions.
Read-only because write tasks have irreversible side effects.

**Controlled variables:**
- Same OpenCode version
- Same model (fix to one for the tool-explosion comparison)
- Same task prompt (verbatim — no hints about which tool to use)
- Same project state (reset to a known Git commit before each run)
- Same hardware / no background processes

**Measured variables:**
- Context tokens consumed at session start (before first user message)
- Tool calls per task
- First-call accuracy (did the first tool call invoke the correct tool family?)
- Total failed/retried calls
- Wall time to task completion
- Correct result (yes/no vs. ground truth)

**Confound:** Model behavior differences could swamp harness differences.
Claireon's `tool_search` → `python_execute` pattern requires the model to
understand it should search first. A model that doesn't grasp this will fail
regardless of the architecture. *Mitigation: run with multiple models (Section 7).*

### What your project can contribute

Your project has a known-hard tool selection case documented in `AGENTS.md`
rule 10: `UnitHasEnoughMP` vs `Unit Has Enough MP` — node instance titles are
spaced. This is a substring search ambiguity that substring-based tools get
wrong and semantic search might get right. That's a real, documented case where
the architecture matters.

---

## Section 7: Model-Independent Benchmark

### The core problem

You want to separate **harness effects** from **model effects**. They interact:
- Claireon's discovery pattern (search then execute) requires good instruction
  following. Smaller or less capable models may not reliably invoke `tool_search`
  before `python_execute`.
- Epic native's flat tool list requires good tool name matching. Different models
  have different knowledge of UE tool naming conventions.

### Fixed variables (must not change between model runs)

| Variable | What to fix |
|---|---|
| OpenCode version | Pin to current release on day of experiment |
| Task prompts | Identical verbatim text for all conditions |
| Project state | Same Git commit SHA, reset before each run |
| MCP server version | Same Claireon/Monolith/Epic native versions |
| System prompt / instructions | Identical or none (don't give tool hints) |
| Hardware | Same machine, no background processes |

### Model matrix (minimum viable)

| Model | Why include |
|---|---|
| DeepSeek (your current primary) | Baseline — your existing workflow |
| Claude Sonnet (latest) | Dominant model in published UE+MCP literature — calibration |
| Qwen3 (latest, OpenCode-supported) | Strong on tool use, relevant comparison |
| One local model via Ollama | Tests whether Claireon's context savings enable local models |

**Do not include:** Models you can't run consistently (rate limits, cost) or
models that require different prompting styles that you'd need to tune separately
(that introduces confounds).

### Stopping criteria for each run

- Task completes (success or failure) within 10 minutes wall time, OR
- Agent makes 30+ tool calls without progress, OR
- Agent explicitly reports being stuck

Do not retry failed runs with prompting help — that introduces human intervention
as a variable.

### Sample size

For each (architecture × model × task) combination: **3 independent runs**.
That's enough to detect consistent failure modes but not enough for statistical
significance. Be honest about this. You're doing exploratory engineering
experiments, not a clinical trial.

### How to distinguish harness effects from model effects

If a task fails under Claireon with DeepSeek but succeeds under Claireon with
Claude, that's a model effect (DeepSeek may not follow the tool_search pattern).
If a task fails under Epic native with BOTH models but succeeds under Claireon
with both models, that's a harness effect. Record which cell of the matrix
(architecture × model) produces the failure — the pattern across models tells
you whether it's the harness or the model.

---

## Section 8: Security Review of Running Claireon

### What Claireon's security model actually is (from the README directly)

1. **Unauthenticated HTTP server, localhost only.** The MCP server binds on a
   per-worktree port (SHA-256 derived, 49152–65535). Localhost-only access is
   enforced by `Origin`/`Host` header validation — "best-effort, not by socket
   bind." The editor's `FHttpServerModule` actually binds ALL interfaces;
   the loopback restriction is software-enforced.

2. **`python_execute` is completely unrestricted.** Equivalent to the editor's
   built-in Python console. Full filesystem access, full network access, full
   UE editor API access. No sandboxing. Execution timeout (60s default) is
   "best-effort" — a blocking native call is not interrupted.

3. **No authentication on the proxy's MCP endpoint.** Any process on localhost
   can call the Claireon proxy. The proxy adds a bearer token for editor-proxy
   communication, but the proxy itself is wide open.

4. **Port exposure surface:** Proxy singleton port 43017 + per-worktree ports
   49152–65535.

### What an autonomous agent could potentially do

If OpenCode (or the model it's routing to) receives a hallucinated or malicious
instruction that results in a `python_execute` call, it can:

- Read or write any file on the filesystem (not scoped to the project)
- Make outbound network requests
- Call any UE Python API, including destructive ones
- Execute arbitrary OS commands via `subprocess` in Python
- Delete assets via `unreal.EditorAssetLibrary.delete_asset()` — which in this
  project creates a registry corruption (known failure from `AGENTS.md`)
- Touch `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` — which crashes the
  editor fatally

This is not a hypothetical. Your project has documented fatal crash paths from
Python. Claireon's python_execute is the same execution surface, with no
additional guardrails.

### Safe experimental setup

**Step 1: Git worktree isolation**
```
git worktree add ../Melodia_ClaireonTest claireon-test
```
Run all Claireon experiments in the worktree, never in the main checkout.
If something goes wrong, `git worktree remove` and the main checkout is untouched.

**Step 2: Use a known-clean commit**
Before each experiment run, reset the worktree to a specific commit where you
know the project state exactly. No uncommitted changes in the worktree.

**Step 3: Never enable UEBlueprintMCP alongside Claireon**
The known fatal path (`D_DamageType` skills Python crash) is triggered by
`load_blueprint_class()` / `get_default_object()` from Python. Claireon's
`python_execute` runs arbitrary Python — it can trigger this if the agent
reasons its way to those calls. Mitigation: keep UEBlueprintMCP disabled and
do not hint about the skills path in any task prompt.

**Step 4: Blocklist in task prompts**
Add a system-level note (not Claireon config — it has no blocklist):
```
NEVER call unreal.EditorAssetLibrary.delete_asset().
NEVER access Content/TurnBasedJRPGTemplate/Blueprints/Skills/.
NEVER use subprocess or os.system.
```
This is prompt-level, not harness-level — it can be lost on compaction.
For experiments where context compaction could happen (T7, T9), repeat these
as the first message after session restart.

**Step 5: Host firewall**
On the experiment machine, add a Windows Firewall rule blocking inbound
connections to ports 43017 and 49152–65535 from any IP other than 127.0.0.1.
This converts Claireon's software-enforced loopback restriction to a
hardware-enforced one.

**Step 6: Read-only tasks first**
Run T1, T2, T5 (read-only) before any write tasks. Confirm the setup works
before giving the agent write access to your project.

**Step 7: Monitor the Python audit log**
Claireon writes an audit log of every `python_execute` invocation
(timestamp, success, duration, visible in the UE output log as
`LogClaireon: Display: [MCP] PythonAuditLog`). Read this after every run.
Any call to a dangerous path will appear here.

### What NOT to do
- Do not run Claireon in your main project checkout
- Do not run with uncommitted work in the worktree
- Do not run write tasks before verifying read tasks work correctly
- Do not run while another editor instance is open (safe-working rule 7)

---

## Section 9: Novelty Classification

For every potential finding, I'm classifying against what's already in the
literature.

### Already known — do not claim as novel

| Finding | Already known because |
|---|---|
| Context overhead is proportional to tool count | StraySpark measured this precisely (60K→3K). |
| Catalog mode / lazy loading reduces context | StraySpark, OpenCode issues #17480, #9350. Already shipped in StraySpark v4 and OpenCode's `mcp_lazy`. |
| `bp_compile` hangs on Claireon | Open bug #7, filed by the community. |
| UE 5.7+ has build errors on Claireon | Open bug #6, filed by the community. |
| Non-Claude models are less fluent with MCP tools | StraySpark: "GPT-backed Cursor is noticeably less fluent." Partially known. |
| Claireon's python_execute has no sandboxing | Documented in their own README, SECURITY.md. Not a discovery. |

### Known but poorly measured — worth adding data

| Finding | Why it needs better data |
|---|---|
| Tool explosion degrades task quality (not just context cost) | StraySpark measured context cost. Nobody has measured whether first-call accuracy or task completion rate declines with 830 tools vs. 2 tools on a real UE5 project. |
| Model-specific tool selection quality on UE5 tasks | StraySpark's comparison is qualitative. No published per-task, per-model accuracy numbers on real UE5 Blueprint/PCG/material tasks. |
| Claireon's proxy actually improves continuity on crash recovery | The claim is documented, but there are no published quantitative results: how long does reconnection take? Does the agent correctly resume or just retry from scratch? |
| `tool_search` semantic accuracy vs. flat manifest for domain-specific UE task language | No published test of whether hybrid FTS5+embedding search correctly resolves domain-specific UE terminology (Blueprint vs. K2Node, Material vs. MI, PCG vs. ProcGen). |

### Potentially new (if you find it)

| Finding | Why it would be new |
|---|---|
| Claireon on UE 5.8: does it compile and what breaks? | No public record of a UE 5.8 Claireon build. Filing the result as a GitHub issue is a direct community contribution. |
| Claireon with OpenCode: does `tool_search` → `python_execute` work with DeepSeek? | No public record of Claireon with any non-Claude client. |
| Whether OpenCode's context compaction loses Claireon's workflow state | Claireon persists state to the branch as JSON. OpenCode compacts differently from Claude Code. Interaction untested. |
| `python_execute` with the D_DamageType crash path | Whether Claireon's execution triggers the known fatal Python crash on skills Blueprints, and whether the audit log gives warning before it happens. |

### Interesting anecdote, not generalizable

| Finding | Why not generalizable |
|---|---|
| "My specific game project ran X% faster with Claireon" | n=1, project-specific, not reproducible by others. |
| "DeepSeek made better tool choices than Claude in my workflow" | Single project, single developer, confirmation bias risk. |
| "I found a bug I hadn't seen before" | Anecdote unless reproducible and filed as an issue. |

### Actually actionable engineering evidence (if found)

| Finding | Who it's useful to |
|---|---|
| Claireon build result on UE 5.8 (pass or fail with specific error) | Believer team (Claireon), anyone wanting to adopt it |
| `tool_search` pattern with OpenCode/DeepSeek (works or fails with specific failure mode) | OpenCode team, Claireon team |
| Measured context cost: Monolith (116 tools) vs. Epic native (830) vs. Claireon (2) on identical tasks | Epic, StraySpark, community — adds a real-project data point to the catalog mode literature |
| Whether Claireon's proxy survives an editor restart when OpenCode is the client (specific seconds, log evidence) | Claireon team — currently untested |

---

## Section 10: The Practical Experiment Plan

### What you need before starting

- [ ] Claireon builds on UE 5.8 (or a known failure with specific error messages)
- [ ] Git worktree created and clean (`git worktree add ../Melodia_ClaireonTest`)
- [ ] Known-clean commit SHA documented as the test baseline
- [ ] Ground truth for T1/T2/T5 sealed manually (run them yourself, record the answers)
- [ ] Windows Firewall rule blocking external access to Claireon ports
- [ ] Audit log location confirmed (`Saved/Logs/*.log` or UE output log)

### Phase 0: Can Claireon even build? (1–2 hours)

Before running any experiments, install Claireon in the worktree and attempt
a build. This is the most uncertain step. Possible outcomes:

- **Clean build:** Proceed to Phase 1.
- **Known 5.7 errors (PendingMove, FJsonObject::SetNumberField):** File a
  comment on issue #6 confirming 5.8 replication. Apply the fix if trivial
  (guard the API call with `ENGINE_MINOR_VERSION`). Proceed if fixed.
- **New 5.8-specific errors (Substrate, Blueprint compiler, MCP plugin
  collision):** Document them. File a new issue. Stop here if not fixable in
  <2 hours — you have enough to report.

*If Claireon doesn't build on 5.8, the rest of the experiment collapses to
Epic native vs. Monolith only. That's still useful.*

### Phase 1: Context cost measurement (1–2 hours)

Run T8 (tool explosion test) read-only under three conditions:
A) Monolith only
B) Epic native AllToolsets
C) Claireon (if built successfully)

**Model:** Fix to DeepSeek (your current model).

For each condition, before the first task prompt, dump the OpenCode context
state (total tokens, tool manifest size). The tool manifest size IS the
measurement — you don't even need to complete the task for this phase.

**Expected result:** You'll get concrete numbers (e.g., Monolith = 8K tokens,
Epic native = 65K tokens, Claireon = 2K tokens) that are directly comparable
to StraySpark's published numbers on a real project with a specific tool count.

**Time:** This is the fastest experiment and the most publishable result.
It doesn't require Claireon to work perfectly — just enough to connect.

### Phase 2: Task correctness under tool explosion (3–4 hours)

Run T1, T2, T5 (read-only) under all three conditions WITH task completion.

**Model:** Fix to DeepSeek.
**Runs per condition:** 3.

Record:
- First-call accuracy (log the exact first tool call made)
- Total tool calls to completion
- Correct result (yes/no vs. sealed fixture)
- Any wrong-tool attempts

**If Claireon isn't built:** Compare Monolith vs. Epic native only. Still
produces the tool explosion data point the community is missing.

### Phase 3: Persistence and recovery (2–3 hours)

Run T7 (session restart) and T9 (editor crash) under:
A) Current setup (Monolith)
B) Claireon (if built)

**Model:** Fix to DeepSeek.
**Runs:** 2 per condition (crash recovery is time-consuming).

Record:
- Did the agent detect the interruption?
- How long to first successful tool call after restart?
- How many tokens consumed re-establishing context?
- Did any session state survive?

### Phase 4: Model matrix on T1 (2–4 hours)

Re-run T1 under the best-performing architecture from Phase 2, with all models:
- DeepSeek
- Claude Sonnet (latest)
- Qwen3 (latest)
- One local model via Ollama

**Fix:** Same architecture, same task prompt, 3 runs per model.

This separates model effects from harness effects on the baseline task.

### Phase 5: Claireon UE 5.8 build report (1 hour, can run in parallel with Phase 0)

Regardless of what else you find: document exactly what happened when you
tried to install and build Claireon on UE 5.8. Even a build failure is a
contribution. File it on believer-oss/Claireon.

---

## Logging and recording methodology

For every run, record:

```json
{
  "run_id": "YYYYMMDD_HHMMSS_taskN_conditionX_modelY",
  "task": "T1",
  "architecture": "claireon | monolith | epic_native",
  "model": "deepseek-r2 | claude-sonnet-5 | qwen3-235b | ...",
  "opencode_version": "x.y.z",
  "project_commit": "abc123",
  "session_start_tokens": 0,
  "tool_manifest_tokens": 0,
  "tool_calls": [],
  "first_call_tool": "",
  "first_call_correct": true,
  "total_tool_calls": 0,
  "failed_calls": 0,
  "result_correct": true,
  "wall_time_seconds": 0,
  "human_interventions": 0,
  "incorrect_modifications": [],
  "notes": ""
}
```

Save one JSON file per run in `Saved/BenchmarkRuns/`. After all runs, a simple
script can aggregate into a comparison table.

---

## Stopping criteria

Stop the entire experiment if:
- Any run causes an unrecoverable editor state (outside the worktree)
- Claireon triggers the D_DamageType fatal crash (stop, document, file the issue)
- Phase 0 takes more than 2 hours without a successful build

Stop an individual run if:
- 30+ tool calls without progress
- 10 minutes wall time without completion
- Agent modifies something outside the expected scope (check modified files
  immediately after)

---

## What to do with the results

**If Claireon builds on UE 5.8 and OpenCode connects:** File a comment on
issue #6 confirming UE 5.8 works (or what breaks). This is the most direct
community contribution available.

**If context measurements match or exceed StraySpark's published numbers:** You
have a real-project data point to cite. You can write a short note for the
UE Toronto meetup or MCP Dev Summit.

**If tool selection accuracy differs between architectures:** You have the
measurement the literature is missing. This is publishable as a GitHub
discussion or a short blog post — not a paper, but a concrete data point.

**If Claireon's proxy materially improves recovery vs. current setup:** You
have evidence for one of Claireon's core claims, tested on a configuration
(OpenCode + UE 5.8) nobody has tested before.

**If DeepSeek fails Claireon's discovery pattern:** That's an OpenCode issue
(model-specific tool_search compliance) with a specific reproduction case
you can file.

---

*All methodology derived from primary sources. No conclusions drawn ahead of
running the experiment. This is a plan, not a result.*
