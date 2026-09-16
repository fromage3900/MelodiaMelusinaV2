from pathlib import Path
import shutil
import tempfile
import unittest
from Tools.scaffold_chapter import ROOT, CONFIG_ASSET, scaffold


class ScaffoldTest(unittest.TestCase):
    def test_valid_ids_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "Chapters/_template", root / "Chapters/_template")
            asset = root / CONFIG_ASSET.relative_to(ROOT)
            asset.parent.mkdir(parents=True)
            shutil.copyfile(CONFIG_ASSET, asset)
            target = scaffold("97_contract_test", root)
            text = (target / "quill/TideListening.qsc").read_text()
            self.assertNotIn("{{chapter}}", text)
            self.assertIn("intent.97_contract_test.listen", text)
            self.assertEqual(text.count("<@> ") + text.count("@ Start"), 4)
            with self.assertRaises(FileExistsError):
                scaffold("97_contract_test", root)
            with self.assertRaises(ValueError):
                scaffold("../escape", root)
            asset.write_bytes(b"missing required IDs")
            with self.assertRaises(ValueError):
                scaffold("98_rejected", root)
            self.assertFalse((root / "Chapters/98_rejected").exists())
