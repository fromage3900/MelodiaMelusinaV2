import unittest
from pathlib import Path
import sys

# Ensure local path is on path
sys.path.append(str(Path(__file__).resolve().parents[3]))

from gmm.core.settings import GmmSettings, SETTINGS_PATH


class TestGmmSettings(unittest.TestCase):

    def setUp(self):
        self.settings = GmmSettings()
        # Backup current settings data
        self.backup_data = self.settings.data.copy()
        self.settings.reset_defaults()

    def tearDown(self):
        # Restore backup
        self.settings.data = self.backup_data
        self.settings.save()

    def test_default_values(self):
        self.assertEqual(self.settings.get("active_genome"), "NikkiFlorawish")
        self.assertEqual(self.settings.get("mcp_server_port"), 9316)

    def test_set_and_get(self):
        # Set a valid parameter
        ok = self.settings.set("active_genome", "NikkiMirage")
        self.assertTrue(ok)
        self.assertEqual(self.settings.get("active_genome"), "NikkiMirage")

    def test_type_coercion(self):
        # Set an integer where a float is expected
        ok = self.settings.set("perfect_accuracy_window_s", 1)
        self.assertTrue(ok)
        self.assertEqual(self.settings.get("perfect_accuracy_window_s"), 1.0)
        self.assertIsInstance(self.settings.get("perfect_accuracy_window_s"), float)

    def test_invalid_key(self):
        # Setting a key that is not in DEFAULT_SETTINGS should return False
        ok = self.settings.set("nonexistent_setting", "value")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
