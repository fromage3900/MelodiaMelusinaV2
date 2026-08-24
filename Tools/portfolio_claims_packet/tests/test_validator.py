from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


PACKET_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKET_ROOT.parents[1]
sys.path.insert(0, str(PACKET_ROOT))

from validator import STATUS_VOCABULARY, load_claims, validate_claims  # noqa: E402


class ClaimsPacketValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_claims(REPO_ROOT / "Docs" / "Portfolio" / "gameplay_system_claims_2026-08-24.json")

    def test_packet_is_valid(self) -> None:
        self.assertEqual(validate_claims(self.data, REPO_ROOT), [])

    def test_missing_source_is_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["claims"][0]["evidence"][0]["path"] = "Docs/Portfolio/no_such_source.md"
        self.assertTrue(any("source does not exist" in error for error in validate_claims(data, REPO_ROOT)))

    def test_open_gate_cannot_be_described_as_complete(self) -> None:
        data = copy.deepcopy(self.data)
        data["claims"][0]["gate_refs"] = ["hud_single_writer"]
        data["claims"][0]["copy"] = "The HUD single-writer gate is complete."
        data["claims"][0]["proof_status"] = "NEED_EVIDENCE"
        errors = validate_claims(data, REPO_ROOT)
        self.assertTrue(any("described as complete" in error or "phrased as complete" in error for error in errors))

    def test_ephemeral_evidence_is_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["claims"][0]["evidence"][0]["ephemeral"] = True
        self.assertTrue(any("marked ephemeral" in error for error in validate_claims(data, REPO_ROOT)))

    def test_intent_cannot_be_presented_as_implementation(self) -> None:
        data = copy.deepcopy(self.data)
        data["claims"][0]["proof_status"] = "SOURCE_BUILT_LIVE_PENDING"
        data["claims"][0]["copy"] = "The system will ship the completed wardrobe hook."
        errors = validate_claims(data, REPO_ROOT)
        self.assertTrue(any("phrased as intent" in error for error in errors))

    def test_status_vocabulary_is_exact(self) -> None:
        self.assertEqual(
            tuple(self.data["status_vocabulary"]),
            STATUS_VOCABULARY,
        )
        self.assertEqual(
            set(self.data["status_vocabulary"]),
            {
                "VERIFIED_RUNTIME",
                "VERIFIED_OFFLINE",
                "SOURCE_BUILT_LIVE_PENDING",
                "DESIGN_INTENT",
                "RETIRED_PROTOTYPE",
                "NEED_EVIDENCE",
            },
        )


if __name__ == "__main__":
    unittest.main()
