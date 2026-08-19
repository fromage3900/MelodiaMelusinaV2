# Claireon Evaluation — Should This Project Adopt It?

**Date:** 2026-08-19
**Context:** Comparing Believer.gg's open-source Claireon MCP plugin against
this project's current Monolith + VibeUE setup. Determining feasibility and
value of a test integration.

---

## What Claireon is

Open-source UE5 MCP plugin from Believer Entertainment (MIT license).
- **600+ tools** spanning Blueprint, anim graphs, perf traces, data tables,
  widget blueprints, and more.
- **Deliberately small agent surface:** only three tools exposed — `python_execute`,
  `tool_search`, and `proxy`. Agent discovers the catalog via `tool_search`,
  preventing context bloat.
- **Crash-survival proxy:** local Python proxy sits between agent and in-process
  plugin so session survives editor restarts and crashes.
- **9-stage workflow state machine** (`/claireon:workflow`) with JSON branch state
  — long-running work survives context compaction and session interruption.
- **Extensible tool catalog:** any UE module can register tools without forking.
- **Every mutation is an undoable transaction.** GC barriers, deferred ops,
  structured exception handling.

GitHub: github.com/believer-oss/Claireon (130 stars, MIT)

---

## Why this project isn't currently using it

### Reason 1: Wrong UE version (primary blocker)
Claireon is developed and tested against **UE 5.5.4**.
This project runs **UE 5.8**.

Current compatibility status (as of Aug 19, 2026):
- UE 5.7: **open bug #6** (filed June 18, 2026, unresolved). `PendingMove`
  missing from `FNetworkPredictionData_Client_Character` in CMC inspect tools.
  Affects `ClaireonCMCInspectTool.cpp` and `ClaireonFlythroughManager.cpp`.
- UE 5.8: **untested**. README was updated to say "5.x (tested with 5.5+)"
  but no confirmed build report exists for 5.8. UE 5.8 introduced Substrate
  (replaces traditional shading model — affects any material tools),
  significant Blueprint compiler changes, and the native MCP plugin.

Risk: installing an untested C++ plugin into a project with known safe-working
rules around C++ compilation is not trivial. A failed compile means a closed-
editor build pass, and rule 15 applies: "Live Coding cannot introduce new
imports."

**This is the primary reason Claireon was not adopted when it launched June 2026.**

### Reason 2: Wrong primary agent (secondary)
Claireon documentation and all examples use **Claude Code**. This project
uses **OpenCode** in JetBrains Rider.

However: Claireon's README explicitly says "Claude Code **or any MCP-compatible
client**." Since OpenCode supports standard MCP (stdio and HTTP), it should
connect to Claireon the same way it connects to Monolith. This is a
documentation gap, not a hard technical blocker.

**Claireon's MCP surface is agent-agnostic. OpenCode compatibility is plausible
but untested.**

### Reason 3: Monolith already exists and is project-hardened
Monolith is the existing custom in-process MCP plugin for this project, with
116 actions validated against this specific codebase. Decision log entries
document known-safe tool patterns. The `bp_regression_checker.py`,
`t3d_blueprint_injector.py`, and all pipeline scripts use the Monolith
JSON-RPC envelope directly.

Claireon would be additive, not a replacement. The question is whether its
600+ tools cover ground Monolith doesn't.

### Reason 4: `python_execute` runs unsandboxed
Claireon's primary execution path is `python_execute` — arbitrary Python
in the editor process, unsandboxed. This project has a known fatal crash
path from Python: calling `load_blueprint_class()` or `get_default_object()`
on anything under `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` triggers
a fatal `PyWrapperTypeRegistry` crash (D_DamageType enum).

Any use of `python_execute` in this project would require auditing that
Claireon's tools never touch that path. Claireon's extensible catalog means
new tools could be added that violate this — the audit would need to be
ongoing, not one-time.

---

## What Claireon would add that Monolith doesn't cover

Based on the published tool catalog:
- **Perf traces** — Monolith has no performance profiling tools
- **Flythrough camera** — not in Monolith
- **CMC (Character Movement Component) inspection** — not in Monolith
  (also broken on 5.7+, so moot until fixed)
- **9-stage workflow state machine with branch-persisted JSON** — this is the
  genuinely novel capability. Monolith has no equivalent. This would directly
  address the context compaction safety failure (the `git checkout -- .`
  incident) by persisting workflow state to the branch rather than relying on
  session context.
- **Session crash survival** — the proxy keeps the agent connected across
  editor restarts. This project loses session state on every crash. Relevant
  given the known editor instability.

---

## How to test Claireon safely

### Prerequisites to verify before attempting
1. Check if Claireon issue #6 (UE 5.7 CMC build errors) has been fixed — if
   5.7 still has open build errors, 5.8 is likely to as well.
2. Check if anyone has filed or confirmed a 5.8 build in the Claireon issues.
3. Read the full tool catalog to identify any tools that could touch
   `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` paths.

### Safe test procedure
1. **Branch first.** Test on a fresh branch, never on main or a live feature
   branch.
2. **Backup first.** `CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26`
   is the reference. Copy the current state before adding any new C++ plugin.
3. **One editor instance.** Confirm no other editor is running (safe-working
   rule 7) before the compile pass.
4. **Attempt build with Claireon added.** A failed build here is safe — no
   assets are touched, just a compile error to fix or report.
5. **Connect OpenCode to Claireon only** (not Monolith simultaneously) for the
   first test. Never run two MCP surfaces against the same graph.
6. **Test `tool_search` first.** Verify the catalog discovery works from
   OpenCode before any write operations.
7. **Test a read-only operation** (Blueprint inspect, asset query) before any
   writes.
8. **File a report.** Document the result — either as a Claireon GitHub issue
   (#6 follow-up for 5.8) or as a positive confirmation that 5.8 works.

### What to specifically test for OpenCode ↔ Claireon
- Does `tool_search` work from OpenCode the same way it does from Claude Code?
- Does the agent correctly use `tool_search` to discover and call tools, or
  does it try to call Claireon tools directly (which won't work — only three
  tools are exposed)?
- Does the session proxy (`claireon_proxy.py`) survive an editor restart when
  OpenCode is the client?
- Does context compaction in OpenCode lose the workflow JSON state that
  Claireon persists to the branch?

---

## Why this matters for the OpenCode pitch

Testing Claireon with OpenCode produces one of the most valuable data points
possible for the pitch:

> "Claireon is Claude Code-first. Its documentation doesn't mention OpenCode.
> I tested it with OpenCode on UE 5.8 — here's what worked, here's what
> didn't, here's the specific gap in OpenCode's MCP session handling that
> Claireon's proxy exposes."

This is concrete, reproducible, comparative data — not a narrative. It directly
addresses the "why should we care about your workflow" question by producing
evidence that sits at the intersection of:
- OpenCode's MCP session reliability (known open issues)
- The most sophisticated open-source UE5 MCP surface available
- A UE 5.8 environment nobody at Believer has tested

That's a PR or a bug report, not just a pitch email.

---

## Decision

**Not blocking on Claireon for the current sprint.** The UE 5.8 build risk is
real and the current final 30% of the game needs to ship first.

**Schedule for after the current sprint:** attempt the test build described
above. File the result as a Claireon GitHub issue regardless of outcome. Feed
findings into the OpenCode pitch.

---

*Researched and written 2026-08-19.*
