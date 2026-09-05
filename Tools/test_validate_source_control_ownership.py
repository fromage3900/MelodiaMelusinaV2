#!/usr/bin/env python3
"""Contract tests for the read-only Git/Perforce ownership validator."""
import copy
import importlib.util
from unittest import mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ownership", HERE / "validate_source_control_ownership.py")
ownership = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ownership)
DATA = ownership.json.loads((HERE.parent / "specs/source_control_ownership.v1.json").read_text(encoding="utf-8"))


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    # The manifest is checked into Git, while the three level bundles are
    # Perforce-owned and may not exist in a Git-only checkout/CI runner.
    check(not ownership.validate(DATA, check_files=False), "ownership manifest must be internally valid")
    overlap = copy.deepcopy(DATA)
    overlap["authorities"]["git"]["roots"].append("Content/Shared/")
    check(any("dual ownership overlap" in e for e in ownership.validate(overlap)), "overlap must fail")
    missing = copy.deepcopy(DATA)
    missing["level_bundles"][0].pop("external_objects")
    check(any("missing external_objects" in e for e in ownership.validate(missing)), "missing external root must fail")
    with mock.patch.object(ownership.subprocess, "run") as run:
        run.return_value = ownership.subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Content/A.uasset\n", stderr=""
        )
        check(
            any("cutover incomplete" in e for e in ownership.validate_git_cutover(DATA)),
            "remaining Git-owned Content must fail cutover",
        )
    print("PASS: source-control ownership validator contract (4 assertions)")


if __name__ == "__main__":
    main()
