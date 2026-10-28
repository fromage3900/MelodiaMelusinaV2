"""Pure-Python safety tests for Grandmaster custom Houdini setup auditing.

Run from repo root:
    python -m unittest discover -s deploy/houdini -p test_audit_custom_setup.py
"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("houdini_custom_setup_audit", HERE / "audit_custom_setup.py")
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class CustomSetupAuditTests(unittest.TestCase):
    def test_discovers_custom_sources_without_modifying_them(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "ArtistStudio"
            hda = root / "hda" / "ArtistForest.hda"
            hip = root / "ArtistWorld.hip"
            script = root / "Tools" / "Houdini" / "artist_nodes.py"
            unrelated = root / "Content" / "Heavy" / "DoNotScan.hda"
            for path in (hda, hip, script, unrelated):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"owner-custom-asset")
            baseline = {str(path): path.read_bytes() for path in (hda, hip, script, unrelated)}

            items = audit.find_local_files(root)
            seen = {x["relative"] for x in items}
            self.assertIn("hda/ArtistForest.hda", seen)
            self.assertIn("ArtistWorld.hip", seen)
            self.assertIn("Tools/Houdini/artist_nodes.py", seen)
            self.assertNotIn("Content/Heavy/DoNotScan.hda", seen)
            self.assertTrue(all(x["path"].startswith(str(root)) for x in items))
            self.assertEqual({str(path): path.read_bytes() for path in (hda, hip, script, unrelated)}, baseline)

    def test_warns_on_conflicting_hda_basename_without_loading(self):
        with tempfile.TemporaryDirectory() as temp:
            roots = [Path(temp) / "SchoolA", Path(temp) / "SchoolB"]
            for root, data in zip(roots, (b"version-a", b"version-b")):
                path = root / "hda" / "DifferentArtistAsset.hda"
                path.parent.mkdir(parents=True)
                path.write_bytes(data)
            report = audit.build_report(roots)
            self.assertEqual(report["mode"], "READ_ONLY")
            self.assertTrue(any("non-identical custom HDAs" in w for w in report["warnings"]))
            self.assertEqual((roots[0] / "hda" / "DifferentArtistAsset.hda").read_bytes(), b"version-a")
            self.assertEqual((roots[1] / "hda" / "DifferentArtistAsset.hda").read_bytes(), b"version-b")

    def test_no_overwrite_of_existing_report(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "existing.json"
            target.write_text("user report", encoding="utf-8")
            with self.assertRaises(SystemExit) as cm:
                audit.main(["--out", str(target)])
            self.assertEqual(cm.exception.code, 2)
            self.assertEqual(target.read_text(encoding="utf-8"), "user report")


if __name__ == "__main__":
    unittest.main()
