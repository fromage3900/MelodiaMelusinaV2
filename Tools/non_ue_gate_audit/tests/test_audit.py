from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from Tools.non_ue_gate_audit import audit


class AuditTests(unittest.TestCase):
    def _file(self, root: Path, relative: str, text: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_ast_inventory_does_not_import_test(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = self._file(
                root,
                "Tools/test_trap.py",
                "raise RuntimeError('imported')\n\ndef test_contract():\n    assert True\n",
            )
            item = audit.analyze(path, root)
            self.assertEqual(item["test_callable_count"], 1)
            self.assertEqual(item["assertion_count"], 1)

    def test_risk_and_oracle_classification_has_line_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = self._file(
                root,
                "Tools/test_risky.py",
                "import requests\n\ndef test_cast():\n    cast = {'skill': 'utility_debuff'}\n    assert cast.get('ok') or cast.get('skill') == 'utility_debuff'\n",
            )
            item = audit.analyze(path, root)
            self.assertEqual(item["execution_policy"], "HOLD_UNSAFE")
            self.assertEqual(item["oracle_findings"][0]["kind"], "echo_based_broad_or_assertion")
            self.assertEqual(item["oracle_findings"][0]["line"], 5)

    def test_repeated_operation_without_comparison_is_weak(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = self._file(
                root,
                "Tools/test_repeat.py",
                "def test_repeat():\n    first = resolve('x')\n    second = resolve('x')\n    assert second['ok']\n",
            )
            item = audit.analyze(path, root)
            kinds = {finding["kind"] for finding in item["oracle_findings"]}
            self.assertIn("repeated_operation_without_state_comparison", kinds)

    def test_inventory_is_sorted_unique_and_json_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._file(root, "Tools/test_z.py", "def test_z():\n    assert True\n")
            self._file(root, "Content/Python/test_a.py", "def test_a():\n    assert True\n")
            first = audit.build_inventory(root)
            second = audit.build_inventory(root)
            self.assertTrue(first["reconciled"])
            self.assertEqual(first["entry_count"], 2)
            self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
            self.assertEqual([item["path"] for item in first["entries"]], [
                "Content/Python/test_a.py", "Tools/test_z.py",
            ])

    def test_discovery_covers_pytest_suffixes_and_test_directories(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._file(root, "deploy/stage_contract_test.py", "assert True\n")
            self._file(root, "Tools/widget/tests/runner.py", "assert True\n")
            self._file(root, "Plugins/Demo/test_proxy.py", "assert True\n")
            self._file(root, "deploy/_stub_generated/tests/test_skip.py", "assert False\n")
            paths = [path.relative_to(root).as_posix() for path in audit.discover(root)]
            self.assertEqual(paths, [
                "deploy/stage_contract_test.py",
                "Plugins/Demo/test_proxy.py",
                "Tools/widget/tests/runner.py",
            ])

    def test_shared_runner_marks_uncounted_markers_as_weak(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._file(
                root,
                "Tools/run_contract_tests.py",
                "import re\n"
                "SUITES = (\n"
                "    Suite('Tools/test_counted.py', re.compile(r'=== (\\d+)/(\\d+) passed ===')),\n"
                "    Suite('Tools/test_marker.py', re.compile(r'validated marker')),\n"
                ")\n",
            )
            result = audit._shared_runner_oracles(root)
            self.assertTrue(result["Tools/test_counted.py"]["counter_coupled"])
            self.assertEqual(
                result["Tools/test_marker.py"]["oracle_kind"],
                "marker_text_plus_returncode",
            )

    def test_marker_only_requires_printed_success_without_failure_control(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            weak = self._file(root, "Tools/test_weak.py", "print('PASSED')\n")
            guarded = self._file(
                root,
                "Tools/test_guarded.py",
                "import sys\n\ndef main(ok):\n    if not ok:\n        sys.exit(1)\n    print('PASSED')\n",
            )
            self.assertEqual(audit.analyze(weak, root)["oracle_findings"][0]["kind"], "marker_only_success")
            self.assertFalse(any(
                item["kind"] == "marker_only_success"
                for item in audit.analyze(guarded, root)["oracle_findings"]
            ))


if __name__ == "__main__":
    unittest.main()
