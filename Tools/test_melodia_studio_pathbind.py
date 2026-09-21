#!/usr/bin/env python3
"""Host tests for typed Melodia Studio path binding. No bpy required."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from melodia_studio_pathbind import (  # noqa: E402
    SourceBindError,
    bind_checkout_deploy,
    is_blender_user_addons_path,
    known_blender_user_addon_roots,
    measured_builder_ids,
    purge_surreal_arch_modules,
    shadowing_surreal_arch_paths,
)


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class PathbindTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_path = list(sys.path)
        self._orig_appdata = os.environ.get("APPDATA")
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        sys.path[:] = self._orig_path
        if self._orig_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = self._orig_appdata
        purge_surreal_arch_modules()
        self._tmp.cleanup()

    def test_measured_builder_ids_fail_closed_on_untyped_mapping(self) -> None:
        with self.assertRaises(SourceBindError):
            measured_builder_ids(["not-a-dict"])
        with self.assertRaises(SourceBindError):
            measured_builder_ids({1: lambda: None})
        with self.assertRaises(SourceBindError):
            measured_builder_ids({"MEL_x": "not-callable"})
        typed = measured_builder_ids({"MEL_x": lambda: None})
        self.assertEqual(set(typed), {"MEL_x"})

    def test_bind_strips_appdata_and_refuses_remaining_shadow(self) -> None:
        appdata = self.root / "AppData"
        os.environ["APPDATA"] = str(appdata)
        live = (
            appdata
            / "Blender Foundation"
            / "Blender"
            / "5.2"
            / "scripts"
            / "addons"
        )
        _write(live / "surreal_arch" / "melodia_gn" / "__init__.py", "ORIGIN = 'live'\n")
        _write(live / "surreal_arch" / "__init__.py", "")

        checkout = self.root / "checkout"
        deploy = checkout / "deploy"
        _write(deploy / "surreal_arch" / "__init__.py", "ORIGIN = 'checkout'\n")
        _write(deploy / "surreal_arch" / "melodia_gn" / "__init__.py", "ORIGIN = 'checkout'\n")

        sys.path.insert(0, str(live))
        bind = bind_checkout_deploy(checkout)
        self.assertEqual(bind.deploy_root, deploy.resolve())
        self.assertTrue(any(path == live.resolve() for path in bind.stripped_appdata_paths))
        self.assertEqual(sys.path[0], str(bind.deploy_root))
        self.assertEqual(shadowing_surreal_arch_paths(bind.deploy_root), ())
        self.assertFalse(
            is_blender_user_addons_path(str(bind.deploy_root), known_blender_user_addon_roots())
        )

    def test_bind_fails_if_second_surreal_arch_remains_on_path(self) -> None:
        checkout = self.root / "checkout"
        deploy = checkout / "deploy"
        _write(deploy / "surreal_arch" / "__init__.py", "")
        _write(deploy / "surreal_arch" / "melodia_gn" / "__init__.py", "")
        other = self.root / "other_deploy"
        _write(other / "surreal_arch" / "melodia_gn" / "__init__.py", "")
        _write(other / "surreal_arch" / "__init__.py", "")
        sys.path.append(str(other))
        with self.assertRaises(SourceBindError) as ctx:
            bind_checkout_deploy(checkout)
        self.assertIn("shadowed", str(ctx.exception))

    def test_bind_fails_closed_when_gn_init_missing(self) -> None:
        checkout = self.root / "empty"
        checkout.mkdir()
        with self.assertRaises(SourceBindError):
            bind_checkout_deploy(checkout)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
