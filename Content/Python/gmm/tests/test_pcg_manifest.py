from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from gmm.pcg.control import validate_manifest_file
from gmm.pcg.manifest import (
    COORDINATE_SYSTEM,
    FORMAT_ID,
    manifest_summary,
    stable_instance_id,
    validate_manifest,
)


IDENTITY_AT_OFFSET = [
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 2.0],
    [0.0, 0.0, 1.0, 3.0],
    [0.0, 0.0, 0.0, 1.0],
]


def sample_manifest() -> dict:
    stable_id = stable_instance_id("World", "wall", "Kit", "face:0", 0)
    instance = {
        "id": stable_id,
        "role": "wall",
        "lib": "Kit",
        "object": "Wall",
        "transform": IDENTITY_AT_OFFSET,
        "static_mesh_path": "/Game/Test/SM_Wall",
    }
    return {
        "format": FORMAT_ID,
        "schema_version": 2,
        "coordinate_system": COORDINATE_SYSTEM,
        "instance_count": 1,
        "instances": [instance],
        "hism_groups": [{
            "role": "wall",
            "lib": "Kit",
            "static_mesh_path": "/Game/Test/SM_Wall",
            "instance_count": 1,
            "transforms": [IDENTITY_AT_OFFSET],
        }],
    }


class PcgManifestTests(unittest.TestCase):
    def test_apply_ready_manifest_is_valid(self) -> None:
        manifest = sample_manifest()
        self.assertEqual([], validate_manifest(manifest, require_resolved_meshes=True))
        self.assertTrue(manifest_summary(manifest, require_resolved_meshes=True)["ok"])

    def test_duplicate_id_and_count_mismatch_fail(self) -> None:
        manifest = sample_manifest()
        manifest["instances"].append(dict(manifest["instances"][0]))
        errors = validate_manifest(manifest)
        self.assertTrue(any("instance_count" in error for error in errors))
        self.assertTrue(any("duplicate" in error for error in errors))

    def test_apply_gate_rejects_unresolved_mesh(self) -> None:
        manifest = sample_manifest()
        manifest["instances"][0]["static_mesh_path"] = ""
        manifest["hism_groups"][0]["static_mesh_path"] = ""
        errors = validate_manifest(manifest, require_resolved_meshes=True)
        self.assertTrue(any("instances[0].static_mesh_path" in error for error in errors))
        self.assertTrue(any("hism_groups[0].static_mesh_path" in error for error in errors))

    def test_instances_require_import_groups(self) -> None:
        manifest = sample_manifest()
        manifest["hism_groups"] = []
        errors = validate_manifest(manifest)
        self.assertTrue(any("must not be empty" in error for error in errors))

    def test_file_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "world.world.json"
            path.write_text(json.dumps(sample_manifest()), encoding="utf-8")
            self.assertTrue(validate_manifest_file(path, for_apply=True)["ok"])


if __name__ == "__main__":
    unittest.main()
