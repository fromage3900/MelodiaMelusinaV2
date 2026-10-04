"""Durable goal/checkpoint/evidence state for cross-agent continuity.

The JSONL event log is the append-only source of truth. SQLite is a local
projection for fast reads and can be rebuilt later from the event log.
All state stays under Saved/AgentState by default.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class ContinuityStore:
    """Small durable store for agent goals and receipts."""

    def __init__(self, project_root: str | Path, state_dir: str | Path | None = None):
        self.project_root = Path(project_root).resolve()
        self.state_dir = (
            Path(state_dir).resolve()
            if state_dir is not None
            else self.project_root / "Saved" / "AgentState"
        )
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.state_dir / "events.jsonl"
        self.db_path = self.state_dir / "melodia_state.sqlite"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS goals (
                    goal_id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    phase TEXT NOT NULL DEFAULT 'planning',
                    status TEXT NOT NULL DEFAULT 'active',
                    next_action TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    goal_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(goal_id) REFERENCES goals(goal_id)
                );

                CREATE INDEX IF NOT EXISTS idx_events_goal_seq
                ON events(goal_id, seq DESC);

                CREATE INDEX IF NOT EXISTS idx_events_goal_kind
                ON events(goal_id, kind, seq DESC);
                """
            )

    def _require_goal(self, conn: sqlite3.Connection, goal_id: str) -> None:
        row = conn.execute(
            "SELECT 1 FROM goals WHERE goal_id = ?", (goal_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown goal: {goal_id}")

    def _append_event(
        self,
        goal_id: str,
        kind: str,
        actor: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        event = {
            "event_id": str(uuid.uuid4()),
            "goal_id": goal_id,
            "kind": kind,
            "actor": actor,
            "payload": payload,
            "created_at": _utc_now(),
        }

        # Fail closed before touching the append-only log.
        with self._connect() as conn:
            self._require_goal(conn, goal_id)

        # JSONL is the append-only authority. SQLite remains a rebuildable view.
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(_json(event) + "\n")
            handle.flush()

        with self._connect() as conn:
            self._require_goal(conn, goal_id)
            conn.execute(
                """
                INSERT INTO events
                    (event_id, goal_id, kind, actor, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    goal_id,
                    kind,
                    actor,
                    _json(payload),
                    event["created_at"],
                ),
            )
            conn.execute(
                "UPDATE goals SET updated_at = ? WHERE goal_id = ?",
                (event["created_at"], goal_id),
            )
        return event

    def upsert_goal(
        self,
        goal_id: str,
        objective: str,
        *,
        phase: str = "planning",
        status: str = "active",
        next_action: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "orchestrator",
    ) -> dict[str, Any]:
        if not goal_id.strip():
            raise ValueError("goal_id is required")
        if not objective.strip():
            raise ValueError("objective is required")

        now = _utc_now()
        metadata = metadata or {}
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT created_at FROM goals WHERE goal_id = ?", (goal_id,)
            ).fetchone()
            created_at = existing["created_at"] if existing else now
            conn.execute(
                """
                INSERT INTO goals
                    (goal_id, objective, phase, status, next_action,
                     metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(goal_id) DO UPDATE SET
                    objective = excluded.objective,
                    phase = excluded.phase,
                    status = excluded.status,
                    next_action = excluded.next_action,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    goal_id,
                    objective,
                    phase,
                    status,
                    next_action,
                    _json(metadata),
                    created_at,
                    now,
                ),
            )

        self._append_event(
            goal_id,
            "goal_upserted",
            actor,
            {
                "objective": objective,
                "phase": phase,
                "status": status,
                "next_action": next_action,
                "metadata": metadata,
            },
        )
        return self.get_goal(goal_id)

    def get_goal(self, goal_id: str, *, recent_events: int = 12) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM goals WHERE goal_id = ?", (goal_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Unknown goal: {goal_id}")

        result = dict(row)
        result["metadata"] = json.loads(result.pop("metadata_json"))
        result["recent_events"] = self.list_events(goal_id, limit=recent_events)
        return result

    def list_goals(self, *, status: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM goals"
        params: tuple[Any, ...] = ()
        if status:
            sql += " WHERE status = ?"
            params = (status,)
        sql += " ORDER BY updated_at DESC"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        goals = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item.pop("metadata_json"))
            goals.append(item)
        return goals

    def list_events(
        self,
        goal_id: str,
        *,
        limit: int = 50,
        kinds: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        if int(limit) <= 0:
            return []

        kind_list = list(kinds or [])
        params: list[Any] = [goal_id]
        sql = "SELECT * FROM events WHERE goal_id = ?"
        if kind_list:
            sql += " AND kind IN (" + ",".join("?" for _ in kind_list) + ")"
            params.extend(kind_list)
        sql += " ORDER BY seq DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))

        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        events = []
        for row in reversed(rows):
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            events.append(item)
        return events

    def checkpoint(
        self,
        goal_id: str,
        *,
        actor: str,
        summary: str,
        completed: list[str] | None = None,
        blockers: list[str] | None = None,
        next_action: str | None = None,
        session: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "summary": summary,
            "completed": completed or [],
            "blockers": blockers or [],
            "next_action": next_action,
            "session": session or {},
        }
        event = self._append_event(goal_id, "checkpoint", actor, payload)
        if next_action is not None:
            self.set_next_action(goal_id, next_action, actor=actor, emit_event=False)
        return event

    def add_evidence(
        self,
        goal_id: str,
        *,
        actor: str,
        evidence_type: str,
        uri: str,
        summary: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._append_event(
            goal_id,
            "evidence",
            actor,
            {
                "evidence_type": evidence_type,
                "uri": uri,
                "summary": summary,
                "metadata": metadata or {},
            },
        )

    def record_decision(
        self,
        goal_id: str,
        *,
        actor: str,
        decision: str,
        rationale: str = "",
        supersedes: str | None = None,
    ) -> dict[str, Any]:
        return self._append_event(
            goal_id,
            "decision",
            actor,
            {
                "decision": decision,
                "rationale": rationale,
                "supersedes": supersedes,
            },
        )

    def attach_session(
        self,
        goal_id: str,
        *,
        actor: str,
        provider: str,
        session_id: str,
        model: str | None = None,
        workspace: str | None = None,
    ) -> dict[str, Any]:
        return self._append_event(
            goal_id,
            "session_attached",
            actor,
            {
                "provider": provider,
                "session_id": session_id,
                "model": model,
                "workspace": workspace,
            },
        )

    def set_next_action(
        self,
        goal_id: str,
        next_action: str | None,
        *,
        actor: str = "orchestrator",
        emit_event: bool = True,
    ) -> dict[str, Any]:
        now = _utc_now()
        with self._connect() as conn:
            self._require_goal(conn, goal_id)
            conn.execute(
                "UPDATE goals SET next_action = ?, updated_at = ? WHERE goal_id = ?",
                (next_action, now, goal_id),
            )
        if emit_event:
            self._append_event(
                goal_id,
                "next_action_set",
                actor,
                {"next_action": next_action},
            )
        return self.get_goal(goal_id, recent_events=6)
