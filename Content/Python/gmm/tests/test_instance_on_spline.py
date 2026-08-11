import unittest

from gmm.pcg.instance_on_spline import default_request, serialize_request, validate_request


class SplineInstanceContractTests(unittest.TestCase):
    def test_valid_provisional_request(self):
        self.assertTrue(validate_request(default_request())["ok"])

    def test_invalid_spacing_and_scale(self):
        request = default_request()
        request.update(spacing_cm=0, scale_range=[1.2, 0.8])
        report = validate_request(request)
        self.assertIn("spacing_cm must be finite and positive", report["errors"])
        self.assertIn("scale_range must satisfy 0 < min <= max", report["errors"])

    def test_machine_path_rejected(self):
        request = default_request()
        request["mesh_asset"] = r"G:\\Assets\\mesh.uasset"
        self.assertFalse(validate_request(request)["ok"])

    def test_major_fails_minor_warns(self):
        request = default_request()
        request["schema_version"] = 2
        self.assertFalse(validate_request(request)["ok"])
        request["schema_version"] = 1
        request["schema_minor"] = 99
        self.assertIn("unknown schema minor version: 99", validate_request(request)["warnings"])

    def test_serialization_is_stable(self):
        request = default_request()
        self.assertEqual(serialize_request(request), serialize_request(dict(reversed(list(request.items())))))

    def test_resolved_results_are_required_for_release(self):
        report = validate_request(default_request(), require_ue_results=True)
        self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
