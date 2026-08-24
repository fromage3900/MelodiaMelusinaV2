#!/usr/bin/env python3
"""Inventory and execute the explicitly safe non-UE test gates.

Discovery is AST/text-only: test modules are never imported.  Execution is
limited to the repository's explicit offline contract runner and GMM unittest
discovery, both in bounded ``python -B`` subprocesses.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
AUDIT_DATE = "2026-08-24"
DISCOVERY_ROOTS = (
    "Tools",
    "Content/Python",
    "Docs/T3D_Baseline",
    "deploy",
    "_TouchDesigner",
    "Plugins",
)
DISCOVERY_PATTERNS = ("test_*.py", "*_test.py")
TEST_DIRECTORY_NAMES = {"test", "tests"}
EXCLUDED_DIRECTORY_NAMES = {
    ".git", ".claude", "__pycache__", ".pytest_cache", ".mypy_cache",
    "binaries", "deriveddatacache", "intermediate", "node_modules",
    "saved", "site-packages", "venv",
}
SAFE_RUNNER = "Tools/run_contract_tests.py"
GMM_ROOT = "Content/Python/gmm/tests"
NETWORK_NAMES = {"aiohttp", "boto3", "ftplib", "http", "httpx", "requests", "socket", "urllib"}
EDITOR_NAMES = {"bpy", "unreal"}
PROCESS_NAMES = {"subprocess"}
WRITE_METHODS = {
    "copy", "copy2", "copyfile", "mkdir", "move", "remove", "rename", "replace",
    "rmdir", "rmtree", "touch", "unlink", "write_bytes", "write_text",
}
ASSERT_METHOD_RE = re.compile(
    r"^(assert|fail|subTest$|raises$|warns$|match$)", re.IGNORECASE
)
SUCCESS_RE = re.compile(
    r"(?:passed|validated|\"ok\"\s*:\s*true|\bOK\b|accepted)", re.IGNORECASE
)


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _source_line(lines: list[str], line: int) -> str:
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()[:280]
    return ""


def _evidence(path: str, line: int, lines: list[str], kind: str) -> dict[str, Any]:
    return {"kind": kind, "path": path, "line": line, "source": _source_line(lines, line)}


def _excluded_directory(name: str) -> bool:
    lowered = name.casefold()
    return lowered in EXCLUDED_DIRECTORY_NAMES or lowered.startswith((".venv", "_stub_"))


def _test_shaped(path: Path, scan_root: Path) -> bool:
    if path.name == "__init__.py" or path.suffix.casefold() != ".py":
        return False
    relative_parts = path.relative_to(scan_root).parts
    return (
        path.name.startswith("test_")
        or path.name.endswith("_test.py")
        or any(part.casefold() in TEST_DIRECTORY_NAMES for part in relative_parts[:-1])
    )


def discover(root: Path = ROOT) -> list[Path]:
    """Find first-party Python test surfaces without importing any module.

    Installed environments, agent worktrees, generated ``_stub_*`` packages,
    build output, and package ``__init__.py`` markers are intentionally excluded.
    """
    found: set[Path] = set()
    for path in root.glob("*.py"):
        if _test_shaped(path, root):
            found.add(path)
    for relative in DISCOVERY_ROOTS:
        base = root / relative
        if not base.is_dir():
            continue
        for current, directories, files in os.walk(base):
            directories[:] = sorted(
                (name for name in directories if not _excluded_directory(name)),
                key=str.casefold,
            )
            current_path = Path(current)
            for name in sorted(files, key=str.casefold):
                path = current_path / name
                if _test_shaped(path, base):
                    found.add(path)
    return sorted(found, key=lambda item: item.relative_to(root).as_posix().casefold())


def _imports(tree: ast.AST) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend((alias.name.split(".")[0], node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.append((node.module.split(".")[0], node.lineno))
    return sorted(set(result), key=lambda item: (item[0].casefold(), item[1]))


def _call_name(call: ast.Call) -> str:
    target: ast.AST = call.func
    parts: list[str] = []
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts))


def _main_guard(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        try:
            text = ast.unparse(node.test)
        except Exception:
            continue
        if "__name__" in text and "__main__" in text:
            return True
    return False


def _domain(path: str) -> str:
    lowered = path.casefold()
    rules = (
        ("wardrobe", "wardrobe"), ("save", "save"), ("economy", "economy"),
        ("currency", "economy"), ("rhythm", "rhythm"), ("battle", "combat"),
        ("skill", "combat"), ("world", "world_generation"), ("pcg", "world_generation"),
        ("material", "lookdev"), ("texture", "lookdev"), ("audio", "audio"),
        ("echo", "orchestration"), ("mcp", "tooling"), ("daemon", "tooling"),
        ("t3d", "blueprint_contract"), ("melodia", "integration"),
    )
    for token, value in rules:
        if token in lowered:
            return value
    return "general"


def _gate(path: str) -> str:
    if path.startswith("Content/Python/gmm/tests/"):
        return "gmm_unittest_discovery"
    if path == "Docs/T3D_Baseline/test_canonical.py":
        return "shared_contract_runner"
    if path.startswith("Tools/"):
        return "shared_contract_candidate"
    return "unregistered_test"


def _repeated_call_findings(
    tree: ast.AST, path: str, lines: list[str]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
        assignments: dict[str, list[tuple[str, int]]] = {}
        compared_pairs: set[frozenset[str]] = set()
        for node in ast.walk(function):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                names = [target.id for target in node.targets if isinstance(target, ast.Name)]
                if names:
                    signature = ast.dump(node.value, include_attributes=False)
                    assignments.setdefault(signature, []).append((names[0], node.lineno))
            elif isinstance(node, ast.Compare):
                names = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
                for left in names:
                    for right in names:
                        if left != right:
                            compared_pairs.add(frozenset((left, right)))
            elif isinstance(node, ast.Call) and ASSERT_METHOD_RE.match(_call_name(node).split(".")[-1]):
                names = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
                for left in names:
                    for right in names:
                        if left != right:
                            compared_pairs.add(frozenset((left, right)))
        for items in assignments.values():
            if len(items) < 2:
                continue
            first, second = items[0], items[1]
            pair = frozenset((first[0], second[0]))
            names = f"{first[0]} {second[0]}".casefold()
            repeat_intent = bool(re.search(
                r"\b(first|second|before|after|again|replay|rerun|repeat|initial)\b|\b[a-z_]+[12]\b",
                names,
            )) or bool(re.search(r"repeat|replay|rerun|idempoten", function.name.casefold()))
            if (
                first[0] == second[0]
                or not repeat_intent
                or second[1] - first[1] > 12
                or pair in compared_pairs
            ):
                continue
            findings.append({
                **_evidence(path, second[1], lines, "repeated_operation_without_state_comparison"),
                "detail": f"same call assigned to {first[0]} and {second[0]} without comparing their state/results",
            })
    return findings


def analyze(path: Path, root: Path = ROOT) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    try:
        tree = ast.parse(text, filename=relative)
        parse_error: dict[str, Any] | None = None
    except SyntaxError as exc:
        tree = ast.Module(body=[], type_ignores=[])
        parse_error = {"line": exc.lineno or 0, "message": exc.msg}

    imports_with_lines = _imports(tree)
    imports = sorted({name for name, _ in imports_with_lines}, key=str.casefold)
    stdlib = getattr(sys, "stdlib_module_names", frozenset())
    non_stdlib = sorted(name for name in imports if name not in stdlib and name != "__future__")
    test_nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test")
    ]
    assert_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    assert_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and ASSERT_METHOD_RE.match(_call_name(node).split(".")[-1])
    ]
    assertions = len(assert_nodes) + len(assert_calls)
    uses_unittest = "unittest" in imports or any(
        isinstance(node, ast.ClassDef)
        and any("TestCase" in ast.dump(base, include_attributes=False) for base in node.bases)
        for node in ast.walk(tree)
    )
    uses_pytest = "pytest" in imports or "@pytest." in text
    has_main = _main_guard(tree)
    if uses_pytest and uses_unittest:
        runner = "pytest_or_unittest"
    elif uses_pytest:
        runner = "pytest"
    elif uses_unittest:
        runner = "unittest"
    elif has_main:
        runner = "script"
    else:
        runner = "unknown"

    risks: dict[str, list[dict[str, Any]]] = {"editor": [], "network": [], "process": []}
    references: dict[str, list[dict[str, Any]]] = {"editor": [], "network": [], "process": []}
    side_effects: list[dict[str, Any]] = []
    for name, line in imports_with_lines:
        if name in EDITOR_NAMES:
            risks["editor"].append(_evidence(relative, line, lines, f"imports_{name}"))
        if name in NETWORK_NAMES:
            references["network"].append(_evidence(relative, line, lines, f"imports_{name}"))
            risks["network"].append(_evidence(relative, line, lines, f"imports_{name}"))
        if name == "boto3":
            risks["network"].append(_evidence(relative, line, lines, "imports_cloud_sdk"))
        if name in PROCESS_NAMES:
            references["process"].append(_evidence(relative, line, lines, "imports_subprocess"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        call = _call_name(node)
        tail = call.split(".")[-1]
        if call in {"os.system", "os.popen"} or tail in {"Popen", "run", "check_call", "check_output"} and call.startswith("subprocess"):
            risks["process"].append(_evidence(relative, node.lineno, lines, "process_call"))
        if (
            call in {"urllib.request.urlopen", "socket.socket", "http.client.HTTPConnection", "http.client.HTTPSConnection"}
            or call.startswith(("requests.", "httpx.", "aiohttp."))
            or tail in {"ThreadingHTTPServer", "HTTPServer"}
        ):
            risks["network"].append(_evidence(relative, node.lineno, lines, "network_call"))
        if call in {"op", "hou.node", "maya.cmds.file", "nuke.scriptOpen"}:
            risks["editor"].append(_evidence(relative, node.lineno, lines, "dcc_runtime_call"))
        if tail in WRITE_METHODS:
            side_effects.append(_evidence(relative, node.lineno, lines, f"filesystem_{tail}"))
        if tail == "open":
            mode = ""
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
            for keyword in node.keywords:
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                    mode = str(keyword.value.value)
            if any(flag in mode for flag in "wax+"):
                side_effects.append(_evidence(relative, node.lineno, lines, "filesystem_open_write"))
    for line_number, line in enumerate(lines, 1):
        lowered = line.casefold()
        if ("http://" in lowered or "https://" in lowered or "localhost:" in lowered) and not lowered.lstrip().startswith("#"):
            references["network"].append(_evidence(relative, line_number, lines, "endpoint_literal"))
        if any(token in lowered for token in ("monolith", "unrealeditor", "editor_query run_python")):
            references["editor"].append(_evidence(relative, line_number, lines, "editor_bridge_reference"))

    findings: list[dict[str, Any]] = []
    for node in assert_nodes:
        if isinstance(node.test, ast.BoolOp) and isinstance(node.test.op, ast.Or):
            finding = _evidence(relative, node.lineno, lines, "broad_or_assertion")
            branch_text = " ".join(ast.unparse(value) for value in node.test.values)
            if re.search(r"\.get\(['\"](?:skill|command|action|id)['\"]\)", branch_text):
                finding["kind"] = "echo_based_broad_or_assertion"
            finding["detail"] = f"assert succeeds through any of {len(node.test.values)} branches"
            findings.append(finding)
    findings.extend(_repeated_call_findings(tree, relative, lines))
    custom_check_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            _call_name(node).split(".")[-1].casefold() in {"_check", "check", "_expect", "expect", "_fail"}
            or _call_name(node).casefold() in {"results.append", "_results.append", "checks.append"}
        )
    ]
    nonzero_returns = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Return)
        and node.value is not None
        and any(
            isinstance(child, ast.Constant)
            and isinstance(child.value, int)
            and not isinstance(child.value, bool)
            and child.value != 0
            for child in ast.walk(node.value)
        )
    ]
    assertion_raises = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Raise) and "AssertionError" in ast.dump(node, include_attributes=False)
    ]
    exit_controls = [
        node for node in ast.walk(tree)
        if (
            isinstance(node, ast.Call) and _call_name(node) in {"sys.exit", "exit"}
        ) or (
            isinstance(node, ast.Raise) and "SystemExit" in ast.dump(node, include_attributes=False)
        )
    ]
    marker_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _call_name(node).split(".")[-1] == "print"
        and any(
            isinstance(child, ast.Constant)
            and isinstance(child.value, str)
            and SUCCESS_RE.search(child.value)
            for argument in node.args
            for child in ast.walk(argument)
        )
    ]
    marker_lines = sorted({node.lineno for node in marker_calls})
    failure_controls = custom_check_calls + nonzero_returns + assertion_raises + exit_controls
    if marker_lines and assertions == 0 and not test_nodes and not failure_controls:
        findings.append({
            **_evidence(relative, marker_lines[0], lines, "marker_only_success"),
            "detail": "success text exists without a local assertion or discoverable test callable",
        })
    for index, line in enumerate(lines, 1):
        if re.search(r"\b0\s*/\s*0\b", line):
            findings.append({
                **_evidence(relative, index, lines, "zero_test_success_literal"),
                "detail": "literal zero-of-zero success surface",
            })

    risky = bool(risks["editor"] or risks["network"] or risks["process"])
    assertion_bearing = bool(assertions or failure_controls)
    if assertions:
        success_kind = "python_assertions"
    elif failure_controls:
        success_kind = "custom_failure_checks"
    elif test_nodes:
        success_kind = "test_callables_without_local_assertions"
    elif marker_lines:
        success_kind = "marker_text_only"
    else:
        success_kind = "process_exit_only_or_none"
    oracle_strength = "weak" if findings else ("assertion_bearing" if assertion_bearing else "none")
    timeout = 120 if risks["process"] else 60
    return {
        "path": relative,
        "sha256": digest,
        "parse_error": parse_error,
        "runner": runner,
        "interpreter": {"name": "python", "bytecode_disabled": True},
        "dependencies": {
            "imports": imports,
            "non_stdlib": non_stdlib,
            "availability": "NOT_PROBED_WITH_IMPORTS",
        },
        "test_callable_count": len(test_nodes),
        "assertion_count": assertions,
        "assertion_bearing_success": assertion_bearing,
        "success_condition": {
            "kind": success_kind,
            "assertion_count": assertions,
            "custom_check_count": len(failure_controls),
        },
        "oracle_strength": oracle_strength,
        "oracle_findings": sorted(findings, key=lambda item: (item["line"], item["kind"])),
        "risks": {key: value[:12] for key, value in risks.items()},
        "references": {key: value[:12] for key, value in references.items()},
        "side_effects": side_effects[:12],
        "timeout_seconds": timeout,
        "domain": _domain(relative),
        "gate": _gate(relative),
        "execution_policy": "HOLD_UNSAFE" if risky else "INVENTORY_ONLY",
        "current_result": "HOLD_UNSAFE" if risky else "NOT_RUN",
        "execution": {
            "launched": False,
            "command": None,
            "timeout_seconds": timeout,
            "captured_result": "HOLD_UNSAFE" if risky else "NOT_RUN",
        },
    }


def _pytest_config(root: Path) -> dict[str, Any]:
    # Primary is pyproject.toml [tool.pytest.ini_options] (stdlib tomllib), fallback to pytest.ini.
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        testpaths: list[str] = []
        # Try structured parse with tomllib (Python 3.11+).
        try:
            import tomllib  # type: ignore
            data = tomllib.loads(text)
            opts = data.get("tool", {}).get("pytest", {}).get("ini_options", {})
            if isinstance(opts, dict) and "testpaths" in opts:
                raw = opts["testpaths"]
                if isinstance(raw, list):
                    testpaths = [str(item) for item in raw]
                elif isinstance(raw, str):
                    testpaths = raw.split()
        except Exception:
            # Fallback text scan for testpaths = [...]
            for line in lines:
                if "testpaths" in line:
                    # crude: extract quoted strings or bracket contents
                    try:
                        if "[" in line and "]" in line:
                            inner = line.split("[", 1)[1].split("]", 1)[0]
                            testpaths = [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
                        else:
                            testpaths = line.split("=", 1)[1].strip().strip("\"'").split()
                    except Exception:
                        testpaths = []
                    break
        evidence = [
            {"path": pyproject.relative_to(root).as_posix(), "line": index, "source": line}
            for index, line in enumerate(lines, 1)
            if "testpaths" in line or "pythonpath" in line or "python_files" in line
        ]
        parent_config = root.parent / "pytest.ini"
        parent_evidence: list[dict[str, Any]] = []
        if parent_config.is_file():
            parent_lines = parent_config.read_text(encoding="utf-8", errors="replace").splitlines()
            parent_evidence = [
                {"path": "../pytest.ini", "line": index, "source": line}
                for index, line in enumerate(parent_lines, 1)
                if line.strip().startswith(("testpaths", "pythonpath", "python_files", "norecursedirs"))
            ]
        return {
            "path": pyproject.relative_to(root).as_posix(),
            "testpaths": testpaths,
            "python_files": ["test_*.py", "*_test.py"],
            "evidence": (evidence + parent_evidence)[:12],
            "coverage_explanation": (
                "From BS_GodFile, pyproject.toml limits pytest to Content/Python and deploy with "
                "test_*.py and *_test.py. It excludes Tools, Docs/T3D_Baseline, _TouchDesigner, "
                "plugin tests, and root-level tests. From the parent EnvironmentPortfolio directory, "
                "../pytest.ini instead limits collection to wix/tests and tests, excluding BS_GodFile. "
                "No pytest collection was launched because this audit discovers by AST/text and the "
                "selected interpreter reports pytest unavailable during GMM discovery."
            ),
        }
    candidates = (root / "pytest.ini", root.parent / "pytest.ini")
    for path in candidates:
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        testpaths: list[str] = []
        in_pytest = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("["):
                in_pytest = stripped.casefold() == "[pytest]"
            elif in_pytest and stripped.startswith("testpaths"):
                testpaths = stripped.split("=", 1)[1].split()
        relative = path.relative_to(root.parent).as_posix() if path.is_relative_to(root.parent) else str(path)
        return {
            "path": relative,
            "testpaths": testpaths,
            "evidence": [
                {"line": index, "source": line}
                for index, line in enumerate(lines, 1)
                if line.strip().startswith(("testpaths", "pythonpath", "norecursedirs"))
            ],
            "coverage_explanation": (
                "pytest collection is rooted at the parent repository and limited to wix/tests and tests; "
                "it does not collect BS_GodFile/Tools, BS_GodFile/Content/Python/gmm/tests, "
                "BS_GodFile/Content/Python/Tests, or BS_GodFile/Docs/T3D_Baseline."
            ),
        }
    return {"path": None, "testpaths": [], "evidence": [], "coverage_explanation": "No pytest config found."}


def build_inventory(root: Path = ROOT) -> dict[str, Any]:
    discovered_paths = discover(root)
    entries = [analyze(path, root) for path in discovered_paths]
    return {
        "schema_version": "1.0",
        "kind": "non_ue_gate_inventory",
        "discovery": {
            "roots": [".", *DISCOVERY_ROOTS],
            "patterns": list(DISCOVERY_PATTERNS),
            "test_directory_names": sorted(TEST_DIRECTORY_NAMES),
            "exclusions": [
                "installed environments and site-packages",
                "agent worktrees under .claude",
                "generated deploy/_stub_* packages",
                "Saved/Intermediate/Binaries/DerivedDataCache output",
                "package __init__.py markers",
            ],
        },
        "discovery_method": "stdlib pathlib + ast; modules are never imported",
        "discovered_file_count": len(discovered_paths),
        "entry_count": len(entries),
        "reconciled": (
            len(discovered_paths) == len(entries) == len({entry["path"] for entry in entries})
        ),
        "pytest": _pytest_config(root),
        "entries": entries,
    }


def _run(command: list[str], *, cwd: Path, timeout: int, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False, timeout=timeout,
        )
        return {
            "status": "PASS" if completed.returncode == 0 else "FAIL",
            "returncode": completed.returncode,
            "stdout": completed.stdout or "",
            "stderr": completed.stderr or "",
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "TIMEOUT", "returncode": None,
            "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "") if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def _shared_runner_oracles(root: Path) -> dict[str, dict[str, Any]]:
    """Read the shared runner's suite table without importing the runner."""
    path = root / SAFE_RUNNER
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    tree = ast.parse(text, filename=SAFE_RUNNER)
    suites: dict[str, dict[str, Any]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_name(node) != "Suite" or len(node.args) < 2:
            continue
        suite_path = node.args[0]
        compiled = node.args[1]
        if not isinstance(suite_path, ast.Constant) or not isinstance(suite_path.value, str):
            continue
        pattern = None
        if (
            isinstance(compiled, ast.Call)
            and _call_name(compiled) == "re.compile"
            and compiled.args
            and isinstance(compiled.args[0], ast.Constant)
            and isinstance(compiled.args[0].value, str)
        ):
            pattern = compiled.args[0].value
        groups = re.compile(pattern).groups if pattern else 0
        counter_coupled = groups >= 2
        if counter_coupled:
            oracle_kind = "positive_equal_counter_marker"
        elif pattern and "Ran" in pattern and "tests" in pattern:
            oracle_kind = "uncaptured_test_count_marker"
        else:
            oracle_kind = "marker_text_plus_returncode"
        suites[suite_path.value] = {
            "pattern": pattern,
            "oracle_kind": oracle_kind,
            "counter_coupled": counter_coupled,
            "evidence": _evidence(SAFE_RUNNER, node.lineno, lines, "shared_runner_marker_oracle"),
        }
    return suites


def _shared_contract(root: Path) -> dict[str, Any]:
    raw = _run([sys.executable, "-B", SAFE_RUNNER, "--json"], cwd=root, timeout=240)
    runner_oracles = _shared_runner_oracles(root)
    payload: dict[str, Any] | None = None
    if raw["stdout"]:
        try:
            payload = json.loads(raw["stdout"])
        except json.JSONDecodeError:
            payload = None
    results: list[dict[str, Any]] = []
    if payload:
        for item in payload.get("results", []):
            output = str(item.get("output_tail", ""))
            result = {
                "path": item.get("path"),
                "status": str(item.get("status", "unknown")).upper(),
                "returncode": item.get("returncode"),
                "success_marker_observed": bool(item.get("success_marker_observed")),
                "reason": item.get("reason"),
            }
            oracle = runner_oracles.get(str(item.get("path")))
            if oracle:
                result["runner_oracle"] = oracle
            if re.search(r"\b0\s*/\s*0\b", output):
                result["runtime_oracle_warning"] = "zero_test_success_output"
            if re.search(r"Ran\s+0\s+tests?", output):
                result["runtime_oracle_warning"] = "zero_test_success_output"
            assertion = re.search(r"AssertionError:\s*(.+)", output)
            if assertion:
                result["failure_excerpt"] = assertion.group(1).strip()[:300]
            results.append(result)
    return {
        "command": f"{Path(sys.executable).name} -B {SAFE_RUNNER} --json",
        "timeout_seconds": 240,
        "status": raw["status"],
        "returncode": raw["returncode"],
        "parsed": payload is not None,
        "suite_count": payload.get("suite_count") if payload else None,
        "passed": payload.get("passed") if payload else None,
        "failed": payload.get("failed") if payload else None,
        "coverage_floor": payload.get("coverage_floor") if payload else None,
        "results": results,
        "runner_oracle_findings": [
            {
                **value["evidence"],
                "kind": value["oracle_kind"],
                "suite_path": path,
                "detail": "shared runner observes process return code plus marker text without a positive equal counter",
            }
            for path, value in sorted(runner_oracles.items())
            if not value["counter_coupled"]
        ],
    }


def _gmm_discovery(root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(root / "Content/Python")
    raw = _run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", GMM_ROOT, "-p", "test_*.py", "-v"],
        cwd=root, timeout=240, env=env,
    )
    output = raw["stdout"] + raw["stderr"]
    ran = re.search(r"Ran\s+(\d+)\s+tests?", output)
    summary = re.search(r"FAILED\s*\(([^)]*)\)", output)
    error_headers = sorted(set(re.findall(r"^ERROR:\s+(.+)$", output, re.MULTILINE)))
    failure_headers = sorted(set(re.findall(r"^FAIL:\s+(.+)$", output, re.MULTILINE)))
    owners: list[dict[str, str]] = []
    if "No module named 'pytest'" in output:
        owners.append({"owner": "environment", "issue": "pytest dependency is unavailable"})
    if "cannot import name 'VERSION' from 'gmm'" in output:
        owners.append({"owner": "harness", "issue": "gmm package discovery does not expose VERSION"})
    if "cannot import name 'GmmAudit' from 'gmm.core'" in output:
        owners.append({"owner": "harness", "issue": "gmm.core discovery does not expose GmmAudit"})
    if failure_headers:
        owners.append({"owner": "production", "issue": "GMM assertion failures"})
    return {
        "command": f"{Path(sys.executable).name} -B -m unittest discover -s {GMM_ROOT} -p test_*.py -v",
        "timeout_seconds": 240,
        "status": raw["status"],
        "returncode": raw["returncode"],
        "tests_run": int(ran.group(1)) if ran else 0,
        "summary": summary.group(1) if summary else ("OK" if raw["status"] == "PASS" else "unparsed"),
        "error_count": len(error_headers),
        "failure_count": len(failure_headers),
        "errors": error_headers,
        "failures": failure_headers,
        "failure_owners": owners,
    }


def _apply_results(inventory: dict[str, Any], shared: dict[str, Any], gmm: dict[str, Any]) -> None:
    shared_results = {item["path"]: item for item in shared["results"] if item.get("path")}
    for entry in inventory["entries"]:
        path = entry["path"]
        if path in shared_results:
            entry["execution_policy"] = "RUN_SHARED_OFFLINE_CONTRACT"
            entry["current_result"] = shared_results[path]["status"]
            entry["execution"] = {
                "launched": True,
                "command": shared["command"],
                "timeout_seconds": shared["timeout_seconds"],
                "timeout_scope": "outer shared-runner process",
                "captured_result": shared_results[path]["status"],
                "returncode": shared_results[path]["returncode"],
            }
        elif path.startswith(GMM_ROOT + "/"):
            entry["execution_policy"] = "RUN_GMM_OFFLINE_DISCOVERY"
            entry["current_result"] = "PASS" if gmm["status"] == "PASS" else "FAIL_GROUPED"
            entry["execution"] = {
                "launched": True,
                "command": gmm["command"],
                "timeout_seconds": gmm["timeout_seconds"],
                "timeout_scope": "GMM unittest discovery process",
                "captured_result": entry["current_result"],
                "returncode": gmm["returncode"],
            }


def _fix_queue(inventory: dict[str, Any], shared: dict[str, Any], gmm: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    queue: dict[str, list[dict[str, Any]]] = {"harness": [], "oracle": [], "production": [], "environment": []}
    for owner in gmm["failure_owners"]:
        queue[owner["owner"]].append({"source": "gmm_unittest_discovery", "issue": owner["issue"]})
    for item in shared["results"]:
        if item["status"] == "FAIL":
            queue["production"].append({
                "source": item["path"],
                "issue": item.get("failure_excerpt") or item.get("reason") or "shared contract failure",
            })
        if item.get("runtime_oracle_warning"):
            queue["oracle"].append({"source": item["path"], "issue": item["runtime_oracle_warning"]})
    for finding in shared["runner_oracle_findings"]:
        queue["oracle"].append({
            "source": f"{finding['path']}:{finding['line']} ({finding['suite_path']})",
            "issue": finding["kind"],
        })
    for entry in inventory["entries"]:
        for finding in entry["oracle_findings"]:
            queue["oracle"].append({
                "source": f"{finding['path']}:{finding['line']}",
                "issue": finding["kind"],
            })
    for key in queue:
        unique = {(item["source"], item["issue"]): item for item in queue[key]}
        queue[key] = [unique[token] for token in sorted(unique)]
    return queue


def run_audit(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    inventory = build_inventory(root)
    shared = _shared_contract(root)
    gmm = _gmm_discovery(root)
    _apply_results(inventory, shared, gmm)
    file_weak = [
        finding
        for entry in inventory["entries"]
        for finding in entry["oracle_findings"]
    ]
    weak = file_weak + shared["runner_oracle_findings"]
    audit = {
        "schema_version": "1.0",
        "kind": "non_ue_gate_truth_audit",
        "offline_only": True,
        "bytecode_disabled": True,
        "dependency_install_attempted": False,
        "editor_contacted": False,
        "network_contacted": False,
        "inventory_entry_count": inventory["entry_count"],
        "inventory_reconciled": inventory["reconciled"],
        "current_results": {
            "PASS": sum(entry["current_result"] == "PASS" for entry in inventory["entries"]),
            "FAIL": sum(entry["current_result"] in {"FAIL", "FAIL_GROUPED"} for entry in inventory["entries"]),
            "HOLD_UNSAFE": sum(entry["current_result"] == "HOLD_UNSAFE" for entry in inventory["entries"]),
            "NOT_RUN": sum(entry["current_result"] == "NOT_RUN" for entry in inventory["entries"]),
        },
        "shared_contract_runner": shared,
        "gmm_unittest_discovery": gmm,
        "weak_oracle_count": len(weak) + sum(
            bool(item.get("runtime_oracle_warning")) for item in shared["results"]
        ),
        "weak_oracles": sorted(weak, key=lambda item: (item["path"], item["line"], item["kind"])),
        "fix_queue": _fix_queue(inventory, shared, gmm),
    }
    return inventory, audit


def render_report(inventory: dict[str, Any], audit: dict[str, Any]) -> str:
    shared = audit["shared_contract_runner"]
    gmm = audit["gmm_unittest_discovery"]
    counts = audit["current_results"]
    held_launched = [
        entry for entry in inventory["entries"]
        if entry["execution_policy"] == "HOLD_UNSAFE" and entry["execution"]["launched"]
    ]
    runnable_missing = [
        entry for entry in inventory["entries"]
        if entry["execution"]["launched"]
        and not all((
            entry["execution"].get("command"),
            entry["execution"].get("timeout_seconds"),
            entry["execution"].get("captured_result"),
        ))
    ]
    lines = [
        f"# Non-UE Gate Truth Audit — {AUDIT_DATE}", "",
        "## Verdict", "",
        f"**HOLD.** The inventory reconciles at **{inventory['entry_count']} files**, but the current offline shared contract run is "
        f"**{shared['passed']}/{shared['suite_count']}** and GMM discovery is **{gmm['status']}** "
        f"after running {gmm['tests_run']} tests. Unsafe candidates remain HOLD; no editor, network, build, or dependency install was used.", "",
        "## What was actually run", "",
        f"- `{shared['command']}` — return {shared['returncode']}; {shared['passed']} pass, {shared['failed']} fail; floor {shared['coverage_floor']}.",
        f"- `{gmm['command']}` — return {gmm['returncode']}; {gmm['summary']}.",
        f"- Inventory results: PASS {counts['PASS']}, FAIL/grouped FAIL {counts['FAIL']}, HOLD_UNSAFE {counts['HOLD_UNSAFE']}, NOT_RUN {counts['NOT_RUN']}.", "",
        "Both commands ran in bounded subprocesses with `-B`. Tests were discovered with `pathlib` and `ast`; no test module was imported for inventory.", "",
        "## Pytest coverage truth", "",
        inventory["pytest"]["coverage_explanation"], "",
    ]
    for evidence in inventory["pytest"]["evidence"]:
        lines.append(f"- `{evidence.get('path', inventory['pytest']['path'])}:{evidence['line']}` — `{evidence['source'].strip()}`")
    lines.extend(["", "## Shared runner failures", ""])
    failures = [item for item in shared["results"] if item["status"] == "FAIL"]
    if failures:
        for item in failures:
            lines.append(f"- `{item['path']}` — {item.get('failure_excerpt') or item.get('reason') or 'failed'}")
    else:
        lines.append("- None.")
    lines.extend(["", "## GMM discovery failures", ""])
    if gmm["failure_owners"]:
        for owner in gmm["failure_owners"]:
            lines.append(f"- **{owner['owner']}** — {owner['issue']}.")
    else:
        lines.append("- None.")
    lines.extend(["", "## Weak oracle evidence", ""])
    weak = audit["weak_oracles"]
    if weak:
        for finding in weak:
            suite = f" for `{finding['suite_path']}`" if finding.get("suite_path") else ""
            lines.append(f"- `{finding['path']}:{finding['line']}` — **{finding['kind']}**{suite}: `{finding['source']}`")
    for item in shared["results"]:
        if item.get("runtime_oracle_warning"):
            lines.append(f"- `{item['path']}` runtime output — **{item['runtime_oracle_warning']}**.")
    if not weak and not any(item.get("runtime_oracle_warning") for item in shared["results"]):
        lines.append("- None detected.")
    lines.extend(["", "## Fix queue (ownership, not fixes)", ""])
    for owner in ("harness", "oracle", "production", "environment"):
        lines.append(f"### {owner.title()}")
        lines.append("")
        items = audit["fix_queue"][owner]
        if not items:
            lines.append("- None.")
        else:
            for item in items:
                lines.append(f"- `{item['source']}` — {item['issue']}")
        lines.append("")
    lines.extend([
        "## Acceptance reconciliation", "",
        f"- Discovered paths: {inventory['entry_count']}",
        f"- Unique inventory entries: {len({entry['path'] for entry in inventory['entries']})}",
        f"- Reconciled: `{str(inventory['reconciled']).lower()}`",
        "- Exclusions: installed environments/site-packages, `.claude` worktrees, generated `_stub_*` packages, build/Saved output, and `__init__.py` package markers.",
        f"- Runnable entries missing command/timeout/result: {len(runnable_missing)}",
        f"- Unsafe HOLD entries launched: {len(held_launched)}",
        "- Unsafe execution policy: `HOLD_UNSAFE`", "",
        "Machine-readable evidence: `specs/testing/non_ue_gate_inventory.v1.json` and "
        "`Saved/Audit/non_ue_gate_truth_20260824.json`.", "",
    ])
    return "\n".join(lines)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the assigned inventory, audit, and report artifacts")
    args = parser.parse_args(argv)
    inventory, audit = run_audit(ROOT)
    if args.write:
        inventory_path = ROOT / "specs/testing/non_ue_gate_inventory.v1.json"
        audit_path = ROOT / "Saved/Audit/non_ue_gate_truth_20260824.json"
        report_path = ROOT / "Docs/Reports/Overnight/NON_UE_GATE_TRUTH_AUDIT_2026-08-24.md"
        _write_json(inventory_path, inventory)
        _write_json(audit_path, audit)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_report(inventory, audit), encoding="utf-8")
    else:
        print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if inventory["reconciled"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
