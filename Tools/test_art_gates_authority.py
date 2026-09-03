from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("art_gates", ROOT / "Tools" / "art_gates.py")
assert SPEC and SPEC.loader
art_gates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(art_gates)


class AssetAuthorityTests(unittest.TestCase):
    @mock.patch.object(art_gates, "_git", return_value=["Content/A.uasset"])
    @mock.patch.object(art_gates, "_p4_workspace_uassets")
    def test_auto_prefers_git_during_cutover(self, p4_assets, _git):
        assets, authority = art_gates._tracked_uassets("auto")
        self.assertEqual((assets, authority), (["Content/A.uasset"], "git"))
        p4_assets.assert_not_called()

    @mock.patch.object(art_gates, "_git", return_value=[])
    @mock.patch.object(
        art_gates, "_p4_workspace_uassets", return_value=["Content/B.uasset"]
    )
    def test_auto_uses_perforce_after_git_content_cutover(self, _p4, _git):
        assets, authority = art_gates._tracked_uassets("auto")
        self.assertEqual((assets, authority), (["Content/B.uasset"], "perforce"))

    @mock.patch.object(art_gates, "_git", return_value=["Content/A.uasset"])
    @mock.patch.object(art_gates, "_p4_workspace_uassets", return_value=[])
    def test_explicit_perforce_never_falls_back_to_git(self, _p4, _git):
        self.assertEqual(
            art_gates._tracked_uassets("perforce"), ([], "perforce")
        )

    @mock.patch.object(art_gates, "ROOT", Path("C:/Project"))
    @mock.patch.object(art_gates.subprocess, "run")
    def test_p4_paths_are_scoped_to_project_content(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=(
                "... clientFile C:/Project/Content/Level/A.uasset\n"
                "... clientFile C:/Other/Content/Wrong.uasset\n"
            ),
            stderr="",
        )
        self.assertEqual(
            art_gates._p4_workspace_uassets(), ["Content/Level/A.uasset"]
        )


if __name__ == "__main__":
    unittest.main()
