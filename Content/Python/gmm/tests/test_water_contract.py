import unittest

from gmm.geometry.water import default_request, serialize_request, validate_request


class WaterContractTests(unittest.TestCase):
    def test_valid_water_body(self):
        self.assertTrue(validate_request(default_request())["ok"])

    def test_spline_requires_id(self):
        request = default_request()
        request.update(authoring_mode="spline_sheet", spline_id=None)
        self.assertFalse(validate_request(request)["ok"])

    def test_water_body_warns_on_spline(self):
        request = default_request()
        request["spline_id"] = "UnusedSpline"
        self.assertIn("ignored", " ".join(validate_request(request)["warnings"]))

    def test_invalid_dimensions_and_flow(self):
        request = default_request()
        request.update(dimensions_cm=[0, 2, 3], flow_speed=-1)
        report = validate_request(request)
        self.assertFalse(report["ok"])
        self.assertTrue(any("dimensions" in e for e in report["errors"]))
        self.assertTrue(any("flow_speed" in e for e in report["errors"]))

    def test_machine_path_rejected(self):
        request = default_request()
        request["material_instance"] = r"G:\\water.uasset"
        self.assertFalse(validate_request(request)["ok"])

    def test_versions(self):
        request = default_request()
        request["schema_version"] = 2
        self.assertFalse(validate_request(request)["ok"])
        request["schema_version"] = 1
        request["schema_minor"] = 9
        self.assertIn("unknown schema minor", " ".join(validate_request(request)["warnings"]))

    def test_serialization_is_stable(self):
        request = default_request()
        self.assertEqual(serialize_request(request), serialize_request(dict(reversed(list(request.items())))))


if __name__ == "__main__":
    unittest.main()
