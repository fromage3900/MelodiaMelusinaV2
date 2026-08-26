#!/usr/bin/env python3
"""Read-only Perforce migration preflight for the Melodia workspace.

This tool reports provenance and readiness. It never runs p4 add, reconcile,
submit, revert, clean, reset, prune, garbage collection, or history rewrite.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def run(command: list[str], cwd: Path, timeout: int = 30) -> dict[str, Any]:
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"returncode": 127, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired:
        return {"returncode": 124, "stdout": "", "stderr": "command timed out"}
    return {
        "returncode": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }


def find_repo_root(requested: Path | None) -> Path:
    if requested:
        return requested.expanduser().resolve()
    script_root = Path(__file__).resolve().parent.parent
    if (script_root / ".git").exists() or (script_root / "BS_GodFile.uproject").exists():
        return script_root
    return Path.cwd().resolve()


def first_line(value: str) -> str:
    return value.splitlines()[0] if value else ""


def git_value(root: Path, *arguments: str) -> str:
    result = run(["git", *arguments], root)
    return result["stdout"] if result["returncode"] == 0 else ""


def lfs_summary(root: Path) -> dict[str, Any]:
    if shutil.which("git") is None:
        return {"available": False, "reason": "git not found"}

    version = run(["git", "lfs", "version"], root)
    if version["returncode"] != 0:
        return {"available": False, "reason": first_line(version["stderr"])}

    listed = run(["git", "lfs", "ls-files", "--long"], root, timeout=120)
    hydrated = 0
    pointers = 0
    paths: list[str] = []
    if listed["returncode"] == 0:
        for line in listed["stdout"].splitlines():
            fields = line.split(maxsplit=2)
            if len(fields) < 3:
                continue
            state = fields[1]
            path = fields[2]
            paths.append(path)
            if state == "*":
                hydrated += 1
            else:
                pointers += 1

    pointer_check = run(["git", "lfs", "fsck", "--pointers"], root, timeout=180)
    return {
        "available": True,
        "version": first_line(version["stdout"]),
        "tracked_count": len(paths),
        "hydrated_count": hydrated,
        "pointer_or_unhydrated_count": pointers,
        "pointer_check_returncode": pointer_check["returncode"],
        "pointer_check": first_line(pointer_check["stdout"] or pointer_check["stderr"]),
    }


def p4_summary(root: Path) -> dict[str, Any]:
    executable = shutil.which("p4")
    if executable is None:
        return {"available": False, "reason": "p4 not found on PATH"}
    info = run(["p4", "info"], root, timeout=30)
    return {
        "available": True,
        "executable": executable,
        "info_returncode": info["returncode"],
        "info": info["stdout"] if info["returncode"] == 0 else first_line(info["stderr"]),
    }


def collect(root: Path) -> dict[str, Any]:
    status = run(["git", "status", "--short"], root)
    tracked = run(["git", "ls-files", "-z"], root)
    tracked_count = len([item for item in tracked["stdout"].split("\0") if item])
    return {
        "repo": str(root),
        "project_file_present": (root / "BS_GodFile.uproject").is_file(),
        "git": {
            "available": shutil.which("git") is not None,
            "head": git_value(root, "rev-parse", "HEAD"),
            "branch": git_value(root, "branch", "--show-current"),
            "status_returncode": status["returncode"],
            "dirty": bool(status["stdout"]),
            "status": status["stdout"].splitlines(),
            "tracked_file_count": tracked_count,
        },
        "lfs": lfs_summary(root),
        "perforce": p4_summary(root),
        "safety": {
            "mutating_commands_run": False,
            "migration_started": False,
            "note": "A clean status is recommended before staging any Perforce seed.",
        },
    }


def print_human(report: dict[str, Any]) -> None:
    print("MELODIA PERFORCE MIGRATION PREFLIGHT")
    print(f"Repo:   {report['repo']}")
    git_report = report["git"]
    print(f"HEAD:   {git_report['head'] or 'unavailable'}")
    print(f"Branch: {git_report['branch'] or '(detached or unavailable)'}")
    print(f"Git:    {'DIRTY' if git_report['dirty'] else 'clean'}")
    print(f"Files:  {git_report['tracked_file_count']}")
    lfs_report = report["lfs"]
    if lfs_report["available"]:
        print(
            "LFS:    "
            f"{lfs_report['tracked_count']} tracked; "
            f"{lfs_report['hydrated_count']} hydrated; "
            f"{lfs_report['pointer_or_unhydrated_count']} pointer/unhydrated"
        )
        print(f"LFS pointer check: {lfs_report['pointer_check'] or 'no output'}")
    else:
        print(f"LFS:    unavailable ({lfs_report['reason']})")
    p4_report = report["perforce"]
    if p4_report["available"]:
        print(f"p4:     available at {p4_report['executable']}")
        print(f"p4 info: {first_line(p4_report['info']) or 'not authenticated or unavailable'}")
    else:
        print(f"p4:     not ready ({p4_report['reason']})")
    if git_report["status"]:
        print("Working-tree entries:")
        for line in git_report["status"]:
            print(f"  {line}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="Melodia repository root")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    parser.add_argument(
        "--require-p4",
        action="store_true",
        help="return non-zero when p4 is unavailable or p4 info fails",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="return non-zero when the Git worktree is dirty",
    )
    parser.add_argument(
        "--fail-on-unhydrated",
        action="store_true",
        help="return non-zero when Git LFS reports pointer/unhydrated files",
    )
    args = parser.parse_args()

    root = find_repo_root(args.repo)
    report = collect(root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    exit_code = 0
    if args.require_p4 and (
        not report["perforce"]["available"]
        or report["perforce"].get("info_returncode") != 0
    ):
        exit_code = 1
    if args.require_clean and report["git"]["dirty"]:
        exit_code = 1
    if args.fail_on_unhydrated and report["lfs"].get("pointer_or_unhydrated_count", 0):
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
