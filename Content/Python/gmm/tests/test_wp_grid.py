import unittest

from gmm.pcg.wp_grid import validate_wp_grid_file, validate_wp_grid_report


def report():
    levels = ("SakuraDream", "SpaceCathedral", "BaroqueGrotto", "CosmicOrrery")
    return {"results": [{
        "level": level,
        "graph": "/Game/EnvSandbox/PCG/Styles/Escher/PCG_EscherRelativityRoom",
        "style_id": level,
        "navigation_configured": True,
        "platforms": 1,
        "pcg_volumes": 1,
        "links": 0,
        "route_nodes": [{"id": "0_0", "location_cm": [0, 0, 50], "encounter_clear": True}],
    } for level in levels]}


class WorldPartitionGridTests(unittest.TestCase):
    def test_valid_report(self):
        self.assertEqual([], validate_wp_grid_report(report()))

    def test_rejects_missing_route_contract(self):
        value = report()
        value["results"][0]["route_nodes"] = []
        self.assertTrue(validate_wp_grid_report(value))

    def test_rejects_non_finite_location(self):
        value = report()
        value["results"][0]["route_nodes"][0]["location_cm"][0] = float("nan")
        self.assertTrue(validate_wp_grid_report(value))

    def test_missing_file_is_actionable(self):
        result = validate_wp_grid_file("Saved/Audit/does_not_exist.json")
        self.assertFalse(result["ok"])
        self.assertIn("does not exist", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
