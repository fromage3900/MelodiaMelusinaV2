#!/usr/bin/env python3
"""Offline H1 tests for the Melodia editor lease and task router."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import agent_lease  # noqa: E402
import model_router  # noqa: E402


class LeaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "deploy").mkdir(parents=True)
        (self.root / "Saved" / "Agents").mkdir(parents=True)
        (self.root / "Saved" / "Logs").mkdir(parents=True)
        self.lease = self.root / "Saved" / "Agents" / "editor.lease"
        self.now = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def acquire(self, holder="hermes", session="s1", surface="monolith", ttl=30):
        return agent_lease.acquire_lease(
            holder,
            session,
            surface,
            ttl_minutes=ttl,
            project_root=self.root,
            lease_path=self.lease,
            now=self.now,
        )

    def test_first_holder_acquires_and_second_holder_is_refused(self):
        first = self.acquire()
        self.assertTrue(first["ok"])
        second = self.acquire(holder="claude", session="s2")
        self.assertFalse(second["ok"])
        self.assertEqual(second["reason"], "editor lease already held")

    def test_same_holder_session_can_refresh(self):
        first = self.acquire()
        refreshed = self.acquire()
        self.assertTrue(first["ok"])
        self.assertTrue(refreshed["ok"])

    def test_expired_lease_can_be_replaced(self):
        self.acquire(ttl=1)
        later = self.now + timedelta(minutes=2)
        result = agent_lease.acquire_lease(
            "claude",
            "s2",
            "monolith",
            ttl_minutes=30,
            project_root=self.root,
            lease_path=self.lease,
            now=later,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["lease"]["holder"], "claude")

    def test_loop_stop_blocks_acquisition(self):
        (self.root / "deploy" / "SURREAL_ARCH_LOOP_STOP").write_text("", encoding="utf-8")
        result = self.acquire()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "loop stop marker present")

    def test_modal_open_blocks_until_closed(self):
        log = self.root / "Saved" / "Logs" / "BS_GodFile.log"
        log.write_text("x\nMODAL_OPEN\n", encoding="utf-8")
        self.assertFalse(self.acquire()["ok"])
        log.write_text("x\nMODAL_OPEN\nMODAL_CLOSED\n", encoding="utf-8")
        self.assertTrue(self.acquire()["ok"])

    def test_invalid_lease_blocks_acquisition(self):
        self.lease.write_text("{not-json", encoding="utf-8")
        result = self.acquire()
        self.assertFalse(result["ok"])
        self.assertIn("invalid", result["reason"])

    def test_wrong_holder_cannot_release_active_lease(self):
        self.acquire()
        result = agent_lease.release_lease(
            "claude",
            lease_path=self.lease,
            now=self.now,
        )
        self.assertFalse(result["ok"])
        self.assertTrue(self.lease.exists())

    def test_owner_can_release_own_lease(self):
        self.acquire()
        result = agent_lease.release_lease(
            "hermes",
            session="s1",
            lease_path=self.lease,
            now=self.now,
        )
        self.assertTrue(result["ok"])
        self.assertFalse(self.lease.exists())


class RouterTests(unittest.TestCase):
    def packet(self, **overrides):
        p = {
            "schema": "melodia.agent_task_packet/v1",
            "id": "MEL-CTRL-TEST",
            "goal": "Add an offline Python test for a bounded tool",
            "inputs": [],
            "surfaces": ["repo"],
            "may_write": ["Tools/example.py"],
            "must_not": ["Content/**"],
            "mutation_scope": "files",
            "done_when": ["python -m py_compile Tools/example.py passes"],
            "artifacts_expected": ["Saved/Audit/MEL-CTRL-TEST/result.json"],
            "budget_usd": 2.0,
            "max_turns": 40,
        }
        p.update(overrides)
        return p

    def test_fallback_never_auto_dispatches(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            route = model_router.route_packet(self.packet(), allow_jev=False)
        self.assertEqual(route["source"], "classical-fallback")
        self.assertFalse(route["auto_dispatch"])
        self.assertEqual(route["task_class"], "code")
        self.assertEqual(route["tier"], "T2_EXECUTOR")

    def test_editor_scope_requires_editor_and_verifier_tier(self):
        route = model_router.route_packet(
            self.packet(
                goal="Change a Blueprint graph in the editor and verify it",
                surfaces=["repo", "editor"],
                may_write=["Content/Melodia/Test.uasset"],
                mutation_scope="editor",
            ),
            allow_jev=False,
        )
        self.assertTrue(route["needs_editor"])
        self.assertEqual(route["tier"], "T1_VERIFIER")

    def test_git_scope_escalates_to_architect(self):
        route = model_router.route_packet(
            self.packet(
                goal="Prepare a branch strategy and merge operation",
                mutation_scope="git",
                may_write=[],
            ),
            allow_jev=False,
        )
        self.assertEqual(route["tier"], "T0_ARCHITECT")
        self.assertFalse(route["auto_dispatch"])

    def test_docs_route_is_bulk(self):
        route = model_router.route_packet(
            self.packet(
                goal="Update documentation prose and repair links",
                may_write=["Docs/Production/EXAMPLE.md"],
            ),
            allow_jev=False,
        )
        self.assertEqual(route["task_class"], "docs")
        self.assertEqual(route["tier"], "T3_BULK")


class SchemaTests(unittest.TestCase):
    def test_task_packet_schema_is_present_and_has_core_fields(self):
        path = ROOT / "Tools" / "agent_router" / "task_packet.schema.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "melodia.agent_task_packet/v1")
        required = set(data["required"])
        self.assertTrue({"id", "goal", "done_when", "mutation_scope", "budget_usd", "max_turns"} <= required)


if __name__ == "__main__":
    unittest.main(verbosity=2)
