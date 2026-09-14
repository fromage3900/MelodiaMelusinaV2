import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from Tools import guard_collapsed_paths as guard


class CollapseGuardTest(unittest.TestCase):
    def test_add_rename_and_unchanged_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            old = Path.cwd()
            try:
                os.chdir(directory)
                def git(*args):
                    return subprocess.check_output(["git", *args], text=True).strip()
                git("init", "-q")
                git("config", "user.email", "test@example.invalid")
                git("config", "user.name", "Contract test")
                Path("retired.md").write_text("old status")
                git("add", ".")
                git("commit", "-qm", "before collapse")
                git("rm", "retired.md")
                git("commit", "-qm", "collapse")
                collapse = git("rev-parse", "HEAD")
                with patch.object(guard, "COLLAPSE", collapse):
                    Path("valid.md").write_text("durable reference")
                    git("add", ".")
                    git("commit", "-qm", "valid addition")
                    self.assertEqual(guard.violations(collapse), [])
                    git("mv", "valid.md", "retired.md")
                    git("commit", "-qm", "rename resurrection")
                    self.assertEqual(guard.violations(collapse), ["retired.md"])
                    self.assertEqual(guard.violations("HEAD"), [])
            finally:
                os.chdir(old)
