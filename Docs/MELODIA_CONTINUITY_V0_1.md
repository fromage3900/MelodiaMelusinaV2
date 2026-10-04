# Melodia Continuity V0.1

Status: experimental branch scaffold

## Purpose

Melodia Continuity makes the mission durable instead of making any one chat
thread durable. Codex, OpenCode, Hermes, Nous-backed workers, and local models
should be disposable workers that can resume from the same verified project
state.

This layer does not replace Monolith, agent_bridge, or the Melodia gameplay MCP.

- Monolith remains the authoritative Unreal mutation surface.
- agent_bridge remains the execution/router surface.
- melodia_mcp_server remains the gameplay inspection/verification surface.
- continuity owns only cross-agent goal state, receipts, and bounded handoffs.

## V0.1 state model

The append-only source of truth is:

    Saved/AgentState/events.jsonl

The local query projection is:

    Saved/AgentState/melodia_state.sqlite

Both are runtime/local state. They are not intended to become canonical game
content or to carry provider secrets.

The first implementation supports:

- persistent goals
- checkpoints
- evidence receipts
- explicit decisions
- provider/session attachment
- a single next action
- bounded context compilation for another worker

## Example

    from pathlib import Path
    from Tools.continuity import ContinuityStore, compile_handoff

    root = Path(__file__).resolve().parents[1]
    store = ContinuityStore(root)

    store.upsert_goal(
        "melusina-final-polish",
        "Finalize Melusina runtime presentation",
        phase="runtime-polish",
        next_action="Verify animation state in PIE",
    )

    store.attach_session(
        "melusina-final-polish",
        actor="orchestrator",
        provider="codex",
        session_id="<codex-thread-id>",
    )

    packet = compile_handoff(
        store,
        "melusina-final-polish",
        target="opencode",
        token_budget=8000,
    )

    print(packet["markdown"])

## Safety boundary

V0.1 intentionally has no Unreal, Blender, Houdini, Git, Perforce, or provider
mutation adapters. It cannot claim an editor write surface and cannot execute
the next action itself.

That preserves the project's existing rule: one writer per surface.

The continuity layer records what happened and what should happen next. Existing
authorized surfaces perform the work and return evidence.

## MCP adapter

The branch includes deploy/melodia_continuity_mcp.py with a dependency-free
stdio MCP loop matching the existing agent bridge style. Every exposed tool is
declared in specs/mcp_tool_policy.v1.json before registration.

The server is intentionally not added to .mcp.json in git because .mcp.json is
machine-local and contains provider configuration. Register it locally only
after the branch is checked out and the contract tests pass.

Current tools cover goal reads/lists, goal upsert, checkpoints, evidence,
decisions, session attachment, bounded handoff compilation, and next-action
updates.

## Next branch steps

1. Add work-claim/lease records that mirror the one-writer rule.
2. Add a Codex App Server adapter that stores thread IDs and can request resume.
3. Add OpenCode/Hermes client configuration examples without secrets.
4. Add automatic checkpoint hooks around commit, test, compaction, quota exit,
   and model switch.
5. Add a rebuild command that recreates SQLite from events.jsonl.
6. Add a human-readable CURRENT_AGENT_STATE.md materializer.
7. Dogfood one real Melusina polish handoff from Codex to OpenCode before merge.

Do not add provider tokens or secrets to the continuity database or event log.
