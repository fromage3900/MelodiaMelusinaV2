import copy
import unittest

from gmm.family.fixture import musical_ornament_manifest
from gmm.family.manifest import validate_manifest


class TestFamilyContract(unittest.TestCase):
    def test_musical_ornament_fixture_is_valid(self):
        report = validate_manifest(musical_ornament_manifest())
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["errors"], [])

    def test_rejects_unknown_style(self):
        manifest = musical_ornament_manifest()
        manifest["style_id"] = "NOT_A_STYLE"
        report = validate_manifest(manifest)
        self.assertFalse(report["ok"])
        self.assertIn("unknown style_id: NOT_A_STYLE", report["errors"])

    def test_rejects_non_finite_transform(self):
        manifest = musical_ornament_manifest()
        manifest["instances"][0]["transform"][0][0] = float("nan")
        report = validate_manifest(manifest)
        self.assertFalse(report["ok"])
        self.assertTrue(any("finite 4x4" in error for error in report["errors"]))

    def test_missing_validation_is_a_warning(self):
        manifest = copy.deepcopy(musical_ornament_manifest())
        del manifest["validation"]
        report = validate_manifest(manifest)
        self.assertTrue(report["ok"])
        self.assertIn("manifest has no producer validation block", report["warnings"])


if __name__ == "__main__":
    unittest.main()
