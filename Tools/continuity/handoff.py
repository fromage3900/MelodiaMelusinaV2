"""Compile bounded, model-portable handoff packets from continuity state."""
from __future__ import annotations

import json
from typing import Any

from .store import ContinuityStore


IMPORTANT_KINDS = {
    "decision",
    "evidence",
    "checkpoint",
    "session_attached",
    "next_action_set",
}


def _event_summary(event: dict[str, Any]) -> str:
    kind = event["kind"]
    actor = event["actor"]
    payload = event["payload"]

    if kind == "checkpoint":
        return f"[checkpoint/{actor}] {payload.get('summary', '')}"
    if kind == "decision":
        return f"[decision/{actor}] {payload.get('decision', '')}"
    if kind == "evidence":
        return (
            f"[evidence/{actor}] {payload.get('evidence_type', 'artifact')}: "
            f"{payload.get('uri', '')} {payload.get('summary', '')}".strip()
        )
    if kind == "session_attached":
        return (
            f"[session/{actor}] {payload.get('provider', '')}:"
            f"{payload.get('session_id', '')}"
        )
    if kind == "next_action_set":
        return f"[next/{actor}] {payload.get('next_action', '')}"
    return f"[{kind}/{actor}] {json.dumps(payload, ensure_ascii=False)}"


def compile_handoff(
    store: ContinuityStore,
    goal_id: str,
    *,
    target: str = "generic",
    token_budget: int = 4000,
) -> dict[str, Any]:
    """Return a compact handoff packet rather than raw conversation history."""
    token_budget = max(500, min(int(token_budget), 32000))
    char_budget = token_budget * 4
    goal = store.get_goal(goal_id, recent_events=0)
    events = store.list_events(goal_id, limit=120)

    important = [event for event in events if event["kind"] in IMPORTANT_KINDS]
    selected: list[dict[str, Any]] = []
    used = 0

    # Prefer newest receipts, but return them in chronological order.
    for event in reversed(important):
        line = _event_summary(event)
        cost = len(line) + 80
        if selected and used + cost > char_budget:
            break
        selected.append(event)
        used += cost
    selected.reverse()

    lines = [
        f"# Melodia Handoff — {goal_id}",
        "",
        f"Target: {target}",
        f"Objective: {goal['objective']}",
        f"Phase: {goal['phase']}",
        f"Status: {goal['status']}",
        f"Next action: {goal.get('next_action') or 'UNSET'}",
        "",
        "## Canonical metadata",
        json.dumps(goal.get("metadata", {}), indent=2, ensure_ascii=False),
        "",
        "## Recent authoritative receipts",
    ]
    lines.extend(f"- {_event_summary(event)}" for event in selected)
    lines.extend(
        [
            "",
            "## Continuation rule",
            "Treat repository state, explicit decisions, and verified evidence as "
            "authoritative. Do not redo completed work without contradictory evidence. "
            "Continue from the next unfinished action.",
        ]
    )

    return {
        "schema": "melodia.continuity.handoff.v0.1",
        "goal_id": goal_id,
        "target": target,
        "token_budget": token_budget,
        "goal": {
            "objective": goal["objective"],
            "phase": goal["phase"],
            "status": goal["status"],
            "next_action": goal.get("next_action"),
            "metadata": goal.get("metadata", {}),
        },
        "events": selected,
        "markdown": "\n".join(lines),
    }
