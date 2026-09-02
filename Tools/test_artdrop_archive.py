from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path


HERE = Path(__file__).resolve().parent
TEST_TEMP_ROOT = HERE.parent / "Saved"
SPEC = importlib.util.spec_from_file_location("artdrop_archive", HERE / "artdrop_archive.py")
assert SPEC and SPEC.loader
archive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive)


@contextmanager
def writable_test_root():
    root = TEST_TEMP_ROOT / f"artdrop_archive_test_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    try:
        yield root
    finally:
        resolved = root.resolve()
        if resolved.parent == TEST_TEMP_ROOT.resolve():
            shutil.rmtree(resolved, ignore_errors=True)


class ArtDropArchiveTests(unittest.TestCase):
    def test_inventory_is_allowlisted_and_deterministic(self):
        with writable_test_root() as root:
            included = root / "RawArt" / "Hero"
            included.mkdir(parents=True)
            (included / "b.txt").write_text("b", encoding="utf-8")
            (included / "a.txt").write_text("a", encoding="utf-8")
            (root / "RawArt" / "Marketplace").mkdir()
            (root / "RawArt" / "Marketplace" / "paid.bin").write_bytes(b"paid")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps({"include": ["RawArt"], "exclude": ["Marketplace"]}),
                encoding="utf-8",
            )
            report = archive.inventory(root, manifest)
            self.assertEqual(
                [item["path"] for item in report["files"]],
                ["RawArt/Hero/a.txt", "RawArt/Hero/b.txt"],
            )
            self.assertEqual(report, archive.inventory(root, manifest))

    def test_bundle_bytes_are_reproducible(self):
        with writable_test_root() as root:
            source = root / "RawArt"
            source.mkdir()
            (source / "hero.bin").write_bytes(b"irreplaceable")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"include": ["RawArt"]}), encoding="utf-8")
            report = archive.inventory(root, manifest)
            first, second = root / "first.tar.gz", root / "second.tar.gz"
            archive.write_bundle(root, first, report)
            archive.write_bundle(root, second, report)
            digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest(first), digest(second))

    def test_missing_include_is_reported(self):
        with writable_test_root() as root:
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"include": ["Missing"]}), encoding="utf-8")
            self.assertEqual(archive.inventory(root, manifest)["missing_includes"], ["Missing"])


if __name__ == "__main__":
    unittest.main()
