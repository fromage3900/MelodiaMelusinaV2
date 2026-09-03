"""Pure-Python preview-session lifecycle for GMM geometry editing.

Sessions model intent and safety gates; Unreal adapters perform the actual mesh
work only after a session has been validated.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import ClassVar

from .modifiers import ModifierStack


@dataclass
class PreviewSession:
    session_id: str
    stack: ModifierStack
    state: str = "preview"

    @property
    def stack_hash(self) -> str:
        payload = json.dumps(self.stack.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "state": self.state,
            "lifecycle": self.stack.lifecycle,
            "stack_hash": self.stack_hash,
            "stack": self.stack.to_dict(),
        }


class PreviewSessionRegistry:
    """In-memory registry; persistence belongs to the eventual UE audit layer."""

    VALID_TRANSITIONS: ClassVar[dict[str, frozenset[str]]] = {
        "preview": frozenset({"committed", "cleared"}),
        "committed": frozenset({"baked", "cleared"}),
        "baked": frozenset({"cleared"}),
    }

    def __init__(self) -> None:
        self._sessions: dict[str, PreviewSession] = {}

    def create(self, stack: ModifierStack, session_id: str) -> PreviewSession:
        errors = stack.validate()
        if errors:
            raise ValueError("invalid stack: " + "; ".join(errors))
        if session_id in self._sessions:
            raise ValueError(f"duplicate session_id: {session_id}")
        stack.mark_previewed()
        session = PreviewSession(session_id=session_id, stack=stack)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> PreviewSession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise KeyError(f"unknown preview session: {session_id}") from exc

    def transition(self, session_id: str, target_state: str) -> PreviewSession:
        session = self.get(session_id)
        allowed = self.VALID_TRANSITIONS.get(session.state, frozenset())
        if target_state not in allowed:
            raise ValueError(f"invalid lifecycle transition: {session.state} -> {target_state}")
        if target_state == "committed":
            session.stack.mark_committed()
        elif target_state == "baked":
            session.stack.mark_baked()
        session.state = target_state
        if target_state == "cleared":
            del self._sessions[session_id]
        return session

    def clear(self, session_id: str) -> dict[str, object]:
        session = self.get(session_id)
        result = session.to_dict()
        self.transition(session_id, "cleared")
        result["state"] = "cleared"
        return result


SESSIONS = PreviewSessionRegistry()
