"""Tests for the Melodia continuity V0.1 core."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from Tools.continuity import ContinuityStore, compile_handoff


class ContinuityStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = ContinuityStore(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_goal_checkpoint_and_handoff_roundtrip(self) -> None:
        goal = self.store.upsert_goal(
            "melusina-final-polish",
            "Finalize Melusina runtime presentation",
            phase="runtime-polish",
            next_action="Verify animation state in PIE",
            metadata={"runtime_character": "MelusinaFinal"},
        )
        self.assertEqual(goal["goal_id"], "melusina-final-polish")

        self.store.record_decision(
            "melusina-final-polish",
            actor="codex",
            decision="MelusinaFinal is the canonical runtime output.",
        )
        self.store.add_evidence(
            "melusina-final-polish",
            actor="codex",
            evidence_type="commit",
            uri="commit:abc123",
            summary="Legacy retarget outputs archived.",
        )
        self.store.checkpoint(
            "melusina-final-polish",
            actor="codex",
            summary="Retarget convergence complete; PIE proof remains.",
            completed=["retarget convergence"],
            next_action="Run bounded PIE animation verification",
            session={"provider": "codex", "thread_id": "thread-123"},
        )

        handoff = compile_handoff(
            self.store,
            "melusina-final-polish",
            target="opencode",
            token_budget=2000,
        )
        self.assertIn("Run bounded PIE animation verification", handoff["markdown"])
        self.assertIn("MelusinaFinal is the canonical", handoff["markdown"])
        self.assertTrue((self.root / "Saved" / "AgentState" / "events.jsonl").exists())
        self.assertTrue((self.root / "Saved" / "AgentState" / "melodia_state.sqlite").exists())

    def test_unknown_goal_fails_closed(self) -> None:
        with self.assertRaises(KeyError):
            self.store.get_goal("missing")

    def test_session_attachment_is_receipted(self) -> None:
        self.store.upsert_goal("g", "Goal")
        event = self.store.attach_session(
            "g",
            actor="orchestrator",
            provider="codex",
            session_id="thread-xyz",
            model="gpt",
            workspace="G:/MelodiaMelusinaV2",
        )
        self.assertEqual(event["kind"], "session_attached")
        events = self.store.list_events("g", kinds=["session_attached"])
        self.assertEqual(events[-1]["payload"]["session_id"], "thread-xyz")


if __name__ == "__main__":
    unittest.main()
