#!/usr/bin/env python3
"""Pure contract tests for evidence envelopes."""
from __future__ import annotations

import sys
import unittest
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence_envelope import make_envelope, validate_envelope  # noqa: E402


class EvidenceEnvelopeTests(unittest.TestCase):
    def test_make_envelope_is_valid(self):
        envelope = make_envelope(
            kind="gate",
            status="fail",
            producer="echo_run",
            check_name="static_gates",
            check_status="fail",
            gate_id="static_gates",
            note="baseline drift",
            artifacts=["Saved/Dashboards/t3d_baseline.txt"],
        )
        self.assertEqual(validate_envelope(envelope), [])
        self.assertEqual(envelope["schema"], "melodia.evidence_envelope.v1")

    def test_missing_check_is_rejected(self):
        envelope = make_envelope(
            kind="runtime",
            status="hold",
            producer="test",
            check_name="runtime",
            check_status="hold",
        )
        envelope["checks"] = []
        self.assertTrue(validate_envelope(envelope))

    def test_core_p0_golden_run_contract_is_explicit(self):
        path = Path(__file__).resolve().parents[1] / "specs" / "p0" / "core_p0_dream_golden_run.v1.json"
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(contract["kind"], "melodia_player_facing_playtest_contract")
        self.assertEqual(contract["status"], "owner_run_required")
        self.assertEqual(contract["owner_boundary"]["required_editor_writers"], 1)
        self.assertTrue(contract["owner_boundary"]["no_duplicate_editor_or_proxy_owner"])
        self.assertEqual(
            contract["map_authority"]["player_route"],
            [
                "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
                "/Game/EnvSandbox/Environments/L_KaleidoNave",
            ],
        )
        phase_ids = [phase["id"] for phase in contract["route_phases"]]
        self.assertEqual(phase_ids[0], "new_game")
        self.assertIn("process_restart_continue", phase_ids)
        self.assertIn("repeatability_check", phase_ids)
        self.assertIn("fresh_slot_id", contract["required_record_fields"])
        self.assertIn("claiming the player route from integration-map PIE alone", contract["forbidden_shortcuts"])


if __name__ == "__main__":
    unittest.main()
