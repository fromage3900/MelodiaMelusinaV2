"""Offline, standard-library release-gate tests for the Musical Ornament Kitbash.

Run: python -m unittest discover -s Tools -p test_musical_ornament_packaging.py
These tests use synthetic FBX fixtures; they do not prove source-asset quality or rights.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Content" / "Python"))
import package_musical_ornament_kitbash as packager


class MusicalOrnamentPackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.source = root / "KitbashExport"
        self.product = root / "Products" / "MusicalOrnamentKitbash"
        self.web_catalog = root / "web" / "musical_ornament_kitbash_catalog.json"
        self.bake_manifest = root / "not_present_bake_manifest.json"
        for name, value in (
            ("FBX_EXPORT_DIR", self.source),
            ("PRODUCT_ROOT", self.product),
            ("WEB_CATALOG", self.web_catalog),
            ("BAKE_MANIFEST", self.bake_manifest),
        ):
            mocked = patch.object(packager, name, value)
            mocked.start()
            self.addCleanup(mocked.stop)

    def create_sources(self, *, missing: str | None = None, empty: str | None = None) -> None:
        self.source.mkdir(parents=True, exist_ok=True)
        for mesh in packager.MESHES:
            if mesh.fbx_name == missing:
                continue
            (self.source / mesh.fbx_name).write_bytes(
                b"" if mesh.fbx_name == empty else b"fixture-fbx-not-real"
            )

    def test_missing_mesh_holds_before_creating_any_product(self) -> None:
        self.create_sources(missing=packager.MESHES[-1].fbx_name)
        with self.assertRaisesRegex(FileNotFoundError, "missing:"):
            packager.build_product_folder(make_zip=True)
        self.assertFalse(self.product.exists())
        self.assertFalse(self.web_catalog.exists())

    def test_zero_byte_mesh_holds_release(self) -> None:
        self.create_sources(empty=packager.MESHES[0].fbx_name)
        with self.assertRaisesRegex(FileNotFoundError, "empty:"):
            packager.build_product_folder(make_zip=True)
        self.assertFalse(self.product.exists())

    def test_zip_allowlists_exact_catalog_not_stale_files(self) -> None:
        self.create_sources()
        (self.source / "SM_Orn_Unrelated.fbx").write_bytes(b"unrelated")
        staging = self.product / "FBX"
        staging.mkdir(parents=True)
        (staging / "SM_Orn_Stale.fbx").write_bytes(b"stale")

        packager.build_product_folder(make_zip=True)
        manifest = json.loads((self.product / "product_manifest.json").read_text())
        self.assertFalse(manifest["store_live"])
        self.assertEqual(manifest["fbx_count"], len(packager.MESHES))

        archives = list((self.product / "releases").glob("*.zip"))
        self.assertEqual(len(archives), 1)
        expected = {f"FBX/{mesh.fbx_name}" for mesh in packager.MESHES}
        expected |= {"Docs/README.md", "Docs/LICENSE.txt"}
        with zipfile.ZipFile(archives[0]) as archive:
            self.assertEqual(set(archive.namelist()), expected)


if __name__ == "__main__":
    unittest.main()
