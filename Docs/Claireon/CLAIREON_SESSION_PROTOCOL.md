# Claireon Session Protocol

Coordination doc for using Claireon (the MCP server running inside the Unreal Editor for this
project) safely across multiple git worktrees and/or multiple Claude Code sessions on this
machine. This doc exists because Claireon's own architecture leaves a real gap here, and the
project's existing "one editor instance" rules don't say how to reconcile that gap with
worktree-based session isolation.

## What Claireon actually guarantees, and what it doesn't

Verified against `Plugins/Claireon/Content/Python/claireon_proxy.py` and
`Docs/Research/CLAIREON_ARCHITECTURE_AND_COMPARISON_2026-08-19.md`:

- **One proxy singleton per Windows account** multiplexes MCP traffic from every git worktree to
  whichever Unreal Editor instance is registered for that worktree.
- **Per-asset exclusive locks** exist at the graph-edit layer (`ClaireonSessionManager.h`) — two
  callers cannot both open the same Blueprint/graph for editing at once.
- **There is no PIE-session lock.** Nothing in Claireon stops one caller from calling
  `pie_stop_async()` while another caller (or the human, in the editor) is mid-test.
- **There is no editor-instance arbitration.** If two worktrees both register against the same
  running editor, Claireon happily serves both — it does not know or care that they might be
  working on unrelated things at the same time.

This matches — and is the concrete mechanism behind — the project's existing prose rules:
`CLAUDE.md`'s MCP protocol section ("One editor instance. Always.") and
`_AGENT_WORKING_AGREEMENT.md`'s mandatory Blueprint verification loop
(`export_graph -> fingerprint -> mutate -> compile -> assert_graph_matches -> fingerprint ->
save`, one asset per transaction). Those rules exist *because* Claireon won't enforce them for
you.

## The worktree isolation gap

A git worktree fully isolates git state (branch, working tree, uncommitted changes) — verified
this session by branching a task off `origin/main` while another session had unrelated live
edits on `main`. It does **not** isolate:

- The running Unreal Editor process (there is only one, shared by every worktree's Claireon
  registration).
- The current PIE session (`claireon.pie_status()` reflects whatever the editor is doing right
  now, regardless of which worktree asked).
- `Saved/` (git-ignored, so it's a genuinely separate directory per worktree — a task workspace
  under `Saved/Claireon/Workflow/<task>/` created in one worktree is **invisible** from another
  worktree or from the main checkout. Confirmed directly: an archived task workspace had to be
  edited from the original checkout directory, not from a sibling worktree, because the files
  simply don't exist there.)

**Rule of thumb: worktrees protect git; they do not protect the editor.** Always default new
Claireon tasks into a worktree (cheap, fully solves the git side), but never assume worktree
isolation extends to PIE or live editor state.

## Preflight checklist (before any editor-touching Claireon work)

1. `claireon.pie_status()` — if `active: true`, do not call `pie_stop_async()` or load a new
   level without confirming whose session it is. A PIE session with single-digit-second uptime is
   very likely someone's live test, not stale state.
2. `git status --short` and `git branch --show-current` in whatever directory you're about to
   commit from — confirm the branch and working-tree state match what you expect before creating
   a new branch, stashing, or committing.
3. Read `~/.claude/claireon/ACTIVE_TASK.md` — the current cross-session task pointer (see below).
   If it names a different task/branch than what you're about to start, that's a signal to check
   in before proceeding, not proof of a problem.
4. If starting a new task: default to a worktree unless there's a specific reason not to.

## The other four instruction resources

Only `workflow` (the Creation Workflow orchestrator) and `begin-work` (branch/workspace setup)
are in habitual use today. Four more exist under
`Plugins/Claireon/Content/MCP/Instructions/`, all opt-in ("do not use unless asked"):

| Resource | Reach for it when |
|---|---|
| `architecture-viz` | You want an interactive HTML diagram of a specific system (data flow, class hierarchy) to hand to someone or refer back to — not for routine planning. |
| `push-branch` | You just want uncommitted changes + local commits moved to a standardized branch, rebased on `main`, and pushed — without doing the rebase/branch-naming dance by hand. |
| `refine-proposal` | You have a plan document and want a structured, source-cross-referenced critical review (Critical Issues / Design Questions / Consistency Issues / etc.) before committing to it. |
| `sequencing` | A plan is approved and needs to become ordered, individually-implementable stage files (`NNN-stage-name.md`) for later execution. |

See `CLAIREON_CAPABILITY_CHEATSHEET.md` in this directory for underused MCP *tools* (as opposed
to these workflow-level instruction resources).
