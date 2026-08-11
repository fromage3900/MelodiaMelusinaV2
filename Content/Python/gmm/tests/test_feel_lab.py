import unittest

from gmm.feel_lab import PROFILES, run_lab, run_seed_matrix, simulate, simulate_campaign


class FeelLabTests(unittest.TestCase):
    def test_profiles_cover_skill_levels(self):
        self.assertEqual({"newcomer", "learning", "confident"}, set(PROFILES))

    def test_simulation_is_deterministic(self):
        first = simulate("CrystalShard", "learning", seed=7)
        second = simulate("CrystalShard", "learning", seed=7)
        self.assertEqual(first, second)

    def test_lab_covers_three_encounters_and_profiles(self):
        report = run_lab(seed=11)
        self.assertEqual(9, len(report["runs"]))
        self.assertTrue(all(run["turns"] > 0 for run in report["runs"]))

    def test_onboarding_targets_pass(self):
        report = run_lab(seed=1337)
        self.assertTrue(report["ok"], report["findings"])

    def test_targets_are_robust_across_seed_matrix(self):
        matrix = run_seed_matrix(start_seed=100, seed_count=25)
        self.assertTrue(matrix["ok"], matrix["failures"])

    def test_unknown_profile_is_rejected(self):
        with self.assertRaises(ValueError):
            simulate("CrystalShard", "impossible")

    def test_onboarding_campaign_persists_crescendo(self):
        campaign = simulate_campaign("learning", seed=11)
        self.assertTrue(campaign["completed"])
        self.assertTrue(campaign["ultimate_used"] or campaign["final_crescendo"] > 0)


if __name__ == "__main__":
    unittest.main()
