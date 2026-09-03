import unittest
from pathlib import Path
import sys

# Ensure local path is on path
sys.path.append(str(Path(__file__).resolve().parents[3]))

from gmm.ui.commands import run_gmm, _ACTIVE_STACKS


class TestModifierCommands(unittest.TestCase):

    def setUp(self):
        # Clear active stacks before each test
        _ACTIVE_STACKS.clear()

    def test_modifiers_summary(self):
        res = run_gmm("gmm.modifiers.summary", {})
        self.assertTrue(res.ok)
        self.assertIn("ids", res.outputs)
        self.assertIn("GuardHymn", res.outputs["ids"])

    def test_modifiers_stack_lifecycle(self):
        # Check initial view
        res = run_gmm("gmm.modifiers.stack", {"unit": "Player", "action": "view"})
        self.assertTrue(res.ok)
        self.assertEqual(len(res.outputs["active"]), 0)

        # Add modifier
        res = run_gmm("gmm.modifiers.stack", {"unit": "Player", "action": "add", "modifier_id": "GuardHymn"})
        self.assertTrue(res.ok)
        self.assertEqual(len(res.outputs["active"]), 1)
        self.assertEqual(res.outputs["active"][0]["id"], "GuardHymn")

        # Evaluate modifier
        # GuardHymn op=mul, value=0.8 on damage_taken (reduces damage taken to 80%)
        res = run_gmm("gmm.modifiers.stack", {"unit": "Player", "action": "evaluate", "stat": "damage_taken", "base_value": 100.0})
        self.assertTrue(res.ok)
        self.assertAlmostEqual(res.outputs["result"], 80.0)

        # Clear modifiers
        run_gmm("gmm.modifiers.stack", {"unit": "Player", "action": "clear"})

        # Add Crescendo_Minor (duration 2)
        res = run_gmm("gmm.modifiers.stack", {"unit": "Player", "action": "add", "modifier_id": "Crescendo_Minor"})
        self.assertTrue(res.ok)
        self.assertEqual(len(res.outputs["active"]), 1)

        # Tick turn
        res = run_gmm("gmm.modifiers.stack", {"unit": "Player", "action": "tick"})
        self.assertTrue(res.ok)
        # Crescendo_Minor duration is 2 turns. After 1 tick, it should still be active
        self.assertEqual(len(res.outputs["active"]), 1)

        # Tick turn again (expires)
        run_gmm("gmm.modifiers.stack", {"unit": "Player", "action": "tick"})
        res = run_gmm("gmm.modifiers.stack", {"unit": "Player", "action": "view"})
        self.assertTrue(res.ok)
        self.assertEqual(len(res.outputs["active"]), 0)


if __name__ == "__main__":
    unittest.main()
