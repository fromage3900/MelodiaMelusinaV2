import json
import sys
import unittest
from pathlib import Path


QUANTUM_DIR = Path(__file__).resolve().parent
PYTHON_DIR = QUANTUM_DIR.parent
sys.path.insert(0, str(QUANTUM_DIR))
sys.path.insert(0, str(PYTHON_DIR))

from resonant_movement_ranker import MovementCandidate, candidates_from_atlas, rank_movements
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
        self.assertEqual(result["backend"], "classical-baseline")
        self.assertEqual(result["backend_requested"], "qsharp-simulator")
        self.assertEqual(len(result["candidate_scores"]), 3)

    def test_atlas_candidates_cover_all_authored_movements(self):
        atlas = build_asset_atlas(PROJECT_ROOT)
        candidates = candidates_from_atlas(atlas)
        self.assertEqual(
            {candidate.movement_id for candidate in candidates},
            set(atlas["world_movements"]),
        )
        self.assertTrue(all(0.0 <= value <= 1.0 for candidate in candidates for value in candidate.features.values()))
        json.dumps(rank_movements(3900, candidates))


if __name__ == "__main__":
    unittest.main()
