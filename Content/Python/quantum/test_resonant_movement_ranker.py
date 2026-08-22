import json
import sys
import unittest
from pathlib import Path


QUANTUM_DIR = Path(__file__).resolve().parent
PYTHON_DIR = QUANTUM_DIR.parent
sys.path.insert(0, str(QUANTUM_DIR))
sys.path.insert(0, str(PYTHON_DIR))

from resonant_movement_ranker import MovementCandidate, candidates_from_atlas, rank_movements
import resonant_movement_ranker as ranker
from resonant_world_asset_atlas import build_asset_atlas


PROJECT_ROOT = QUANTUM_DIR.parents[2]


class ResonantMovementRankerTests(unittest.TestCase):
    def test_classical_selection_is_deterministic_and_records_baseline(self):
        candidates = [
            MovementCandidate("quiet", "petal_cantata", {"asset_coverage": 0.3, "outfit_synergy": 0.4}),
            MovementCandidate("strong", "star_loom", {"asset_coverage": 0.9, "outfit_synergy": 1.0}),
        ]
        first = rank_movements(3900, candidates)
        second = rank_movements(3900, candidates)
        self.assertEqual(first, second)
        self.assertEqual(first["backend"], "classical-baseline")
        self.assertEqual(first["winner_id"], first["classical_baseline_winner_id"])
        self.assertTrue(first["replay_contract"]["persist_result_before_world_apply"])

    def test_qsharp_request_is_safe_for_more_than_two_candidates(self):
        candidates = [
            MovementCandidate(str(i), str(i), {"asset_coverage": 0.5 + i / 10})
            for i in range(3)
        ]
        result = rank_movements(3900, candidates, backend="qsharp-simulator")
        self.assertIn(result["backend"], {"classical-baseline", "qsharp-tournament"})
        self.assertEqual(result["backend_requested"], "qsharp-simulator")
        self.assertEqual(len(result["candidate_scores"]), 3)

    def test_qsharp_tournament_composes_the_two_candidate_kernel(self):
        candidates = [
            MovementCandidate("a", "petal_cantata", {"asset_coverage": 0.4}),
            MovementCandidate("b", "star_loom", {"asset_coverage": 0.8}),
            MovementCandidate("c", "liquid_cathedral", {"asset_coverage": 0.6}),
        ]
        old_available = ranker._QSHARP_AVAILABLE
        old_pick = ranker._qsharp_pick
        ranker._QSHARP_AVAILABLE = True
        ranker._qsharp_pick = lambda _left, _right: 0
        try:
            result = rank_movements(3900, candidates, backend="qsharp-simulator")
        finally:
            ranker._QSHARP_AVAILABLE = old_available
            ranker._qsharp_pick = old_pick

        self.assertEqual(result["backend"], "qsharp-tournament")
        self.assertEqual(result["selection_protocol"], "pairwise_tournament_amplitude_measurement")
        self.assertEqual(len(result["measurement_log"]), 2)
        for round_record in result["measurement_log"]:
            self.assertAlmostEqual(sum(round_record["probabilities"]), 1.0, places=5)
        self.assertTrue(result["replay_contract"]["measurement_log_required_for_replay"])

    def test_asset_provenance_changes_replay_identity(self):
        first = rank_movements(
            3900,
            [MovementCandidate("a", "petal_cantata", {"asset_coverage": 0.5}, {"source": "atlas-a"})],
        )
        second = rank_movements(
            3900,
            [MovementCandidate("a", "petal_cantata", {"asset_coverage": 0.5}, {"source": "atlas-b"})],
        )
        self.assertNotEqual(first["trace_id"], second["trace_id"])
        self.assertTrue(first["provenance"]["source_evidence_embedded_in_trace"])

    def test_atlas_candidates_cover_all_authored_movements(self):
        atlas = build_asset_atlas(PROJECT_ROOT)
        candidates = candidates_from_atlas(atlas)
        self.assertEqual(
            {candidate.movement_id for candidate in candidates},
            set(atlas["world_movements"]),
        )
        self.assertTrue(all(0.0 <= value <= 1.0 for candidate in candidates for value in candidate.features.values()))
        self.assertTrue(all(candidate.provenance["atlas_movement_id"] for candidate in candidates))
        json.dumps(rank_movements(3900, candidates))


if __name__ == "__main__":
    unittest.main()
