import json
import unittest

from gmm.daemon.generators import gen_command_manifest


class TestDaemonGenerators(unittest.TestCase):
    def test_command_manifest_handles_envui_registrations(self):
        manifest = json.loads(gen_command_manifest())
        self.assertEqual(manifest["command_count"], len(manifest["commands"]))
        self.assertGreaterEqual(manifest["command_count"], 20)
        self.assertTrue(all(entry["section"] == "Grandmaster" for entry in manifest["commands"]))
        self.assertTrue(all(entry["callable"].startswith("_") for entry in manifest["commands"]))


if __name__ == "__main__":
    unittest.main()
