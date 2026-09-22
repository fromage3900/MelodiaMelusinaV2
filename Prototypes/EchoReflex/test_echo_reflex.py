#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "echo_reflex.py"
spec = importlib.util.spec_from_file_location("echo_reflex", MODULE_PATH)
er = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["echo_reflex"] = er
spec.loader.exec_module(er)


def registry():
    return {
        "read": {
            "id": "read",
            "mutation": "none",
            "resources": [],
            "executor": {"type": "read_file"},
        },
        "edit": {
            "id": "edit",
            "mutation": "ue_editor",
            "resources": ["ue_editor_writer"],
            "executor": {"type": "x"},
        },
        "review": {
            "id": "review",
            "mutation": "human",
            "resources": [],
            "executor": {"type": "human"},
        },
    }


def mission(nodes):
    return {
        "$schema": "melodia.echo_reflex_mission.v1",
        "id": "test",
        "goal": "prove controller behavior",
        "planner": {"kind": "test"},
        "policies": {
            "human_review_mutations": [
                "ue_editor", "repo_write", "human"
            ]
        },
        "nodes": nodes,
    }


class EchoReflexTests(unittest.TestCase):
    def test_serial_mission_selects_only_legal_node(self):
        m = mission([
            {
                "id": "a",
                "capability": "read",
                "depends_on": [],
            },
            {
                "id": "b",
                "capability": "edit",
                "depends_on": ["a"],
            },
        ])
        er.validate_mission(m, registry())
        state = er.initial_state(m)

        first = er.choose_next(
            m, registry(), state, live_jev=False
        )
        self.assertEqual(
            ("SELECT", "a", "deterministic"),
            (first.action, first.node_id, first.source),
        )
        self.assertFalse(first.needs_human)

        er.mark(m, state, "a", "PASS", {"proof": True})
        second = er.choose_next(
            m, registry(), state, live_jev=False
        )
        self.assertEqual(
            ("SELECT", "b"),
            (second.action, second.node_id),
        )
        self.assertTrue(second.needs_human)

    def test_parallel_roots_hold_without_jev(self):
        m = mission([
            {
                "id": "a",
                "capability": "read",
                "depends_on": [],
            },
            {
                "id": "b",
                "capability": "read",
                "depends_on": [],
            },
        ])
        er.validate_mission(m, registry())
        decision = er.choose_next(
            m, registry(), er.initial_state(m),
            live_jev=False,
        )
        self.assertEqual("HOLD", decision.action)
        self.assertEqual("fail-closed", decision.source)
        self.assertTrue(decision.needs_human)
        self.assertEqual(
            {"a", "b"},
            set(decision.distribution),
        )

    def test_resource_lock_blocks_writer(self):
        m = mission([
            {
                "id": "edit",
                "capability": "edit",
                "depends_on": [],
            }
        ])
        er.validate_mission(m, registry())
        state = er.initial_state(m)
        state["held_resources"] = ["ue_editor_writer"]
        self.assertEqual(
            [],
            er.eligible_nodes(m, registry(), state),
        )
        decision = er.choose_next(
            m, registry(), state, live_jev=False
        )
        self.assertEqual("HOLD", decision.action)

    def test_failed_dependency_requests_replan(self):
        m = mission([
            {
                "id": "a",
                "capability": "read",
                "depends_on": [],
            },
            {
                "id": "b",
                "capability": "review",
                "depends_on": ["a"],
            },
        ])
        er.validate_mission(m, registry())
        state = er.initial_state(m)
        er.mark(
            m, state, "a", "FAIL",
            {"error": "boom"},
        )
        decision = er.choose_next(
            m, registry(), state, live_jev=False
        )
        self.assertEqual("REPLAN", decision.action)

    def test_all_pass_is_complete(self):
        m = mission([
            {
                "id": "a",
                "capability": "read",
                "depends_on": [],
            }
        ])
        er.validate_mission(m, registry())
        state = er.initial_state(m)
        er.mark(m, state, "a", "PASS")
        decision = er.choose_next(
            m, registry(), state, live_jev=False
        )
        self.assertEqual("COMPLETE", decision.action)

    def test_unknown_capability_rejected(self):
        m = mission([
            {
                "id": "x",
                "capability": "missing",
                "depends_on": [],
            }
        ])
        with self.assertRaises(er.ReflexError):
            er.validate_mission(m, registry())

    def test_cycle_rejected(self):
        m = mission([
            {
                "id": "a",
                "capability": "read",
                "depends_on": ["b"],
            },
            {
                "id": "b",
                "capability": "read",
                "depends_on": ["a"],
            },
        ])
        with self.assertRaises(er.ReflexError):
            er.validate_mission(m, registry())

    def test_registry_rejects_duplicate_ids(self):
        raw = {
            "$schema": "melodia.echo_reflex_capabilities.v1",
            "capabilities": [
                {"id": "x", "mutation": "none"},
                {"id": "x", "mutation": "none"},
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "registry.json"
            path.write_text(
                json.dumps(raw),
                encoding="utf-8",
            )
            with self.assertRaises(er.ReflexError):
                er.load_registry(path)


if __name__ == "__main__":
    unittest.main()
