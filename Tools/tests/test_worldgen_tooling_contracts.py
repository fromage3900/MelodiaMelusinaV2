import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from worldgen_tooling_contracts import (  # noqa: E402
    builder_entry_passes,
    daemon_run_passes,
    path_is_within,
    report_exit_code,
    scene_entry_passes,
    sha256_file,
)


class BuilderEntryTests(unittest.TestCase):
    def valid_entry(self):
        return {
            "errors": [],
            "nodes": 4,
            "links": 3,
            "outputs": 1,
            "duplicate_inputs": False,
            "nan_values": False,
            "verts": 8,
            "edges": 12,
            "polygons": 6,
            "nan_vertices": 0,
            "zero_area_faces": 0,
        }

    def test_complete_geometry_passes(self):
        self.assertTrue(builder_entry_passes(self.valid_entry()))

    def test_empty_geometry_fails(self):
        entry = self.valid_entry()
        entry.update(verts=0, edges=0, polygons=0)
        self.assertFalse(builder_entry_passes(entry))

    def test_zero_area_or_nan_fails(self):
        entry = self.valid_entry()
        entry["zero_area_faces"] = 1
        self.assertFalse(builder_entry_passes(entry))
        entry = self.valid_entry()
        entry["nan_vertices"] = 1
        self.assertFalse(builder_entry_passes(entry))

    def test_missing_evidence_fails(self):
        self.assertFalse(builder_entry_passes({"errors": []}))


class SceneEntryTests(unittest.TestCase):
    def test_opened_measured_rendered_scene_passes(self):
        entry = {
            "opened": True,
            "preview_ok": True,
            "errors": [],
            "stats": {"objects": 2, "meshes": 1, "triangles": 12},
        }
        self.assertTrue(scene_entry_passes(entry))

    def test_render_failure_cannot_pass(self):
        entry = {
            "opened": True,
            "preview_ok": False,
            "errors": [],
            "stats": {"objects": 2, "meshes": 1, "triangles": 12},
        }
        self.assertFalse(scene_entry_passes(entry))


class ProcessVerdictTests(unittest.TestCase):
    def test_only_explicit_pass_exits_zero(self):
        self.assertEqual(report_exit_code({"verdict": "PASS"}), 0)
        for verdict in ("FAIL", "ERROR", None):
            self.assertEqual(report_exit_code({"verdict": verdict}), 1)

    def test_daemon_requires_all_jobs_and_no_errors(self):
        good = {"midi_found": 2, "processed": 6, "skipped": 4, "errors": 0}
        self.assertTrue(daemon_run_passes(good, 5))
        bad = dict(good, errors=1)
        self.assertFalse(daemon_run_passes(bad, 5))
        incomplete = dict(good, processed=5)
        self.assertFalse(daemon_run_passes(incomplete, 5))
        self.assertFalse(daemon_run_passes(
            {"midi_found": 0, "processed": 0, "skipped": 0, "errors": 0},
            5,
        ))

    def test_artifact_hash_is_content_based(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "artifact.bin"
            artifact.write_bytes(b"melodia-evidence")
            self.assertEqual(
                sha256_file(artifact),
                "cd7f63b8bf14a48ea20c50d143cb2833b343258e283da52a086b8334e1c3e887",
            )

    def test_job_paths_cannot_escape_allowlist(self):
        root = Path("C:/evidence")
        self.assertTrue(path_is_within(root / "renders" / "proof.png", root))
        self.assertFalse(path_is_within(root.parent / "outside.png", root))


if __name__ == "__main__":
    unittest.main()
