#!/usr/bin/env python
"""Safe, portable Git MCP server for MelodiaMelusinaV2.

This server must never guess the author's main-PC path or sweep an entire
worktree into a commit. It resolves the active checkout in this order:

1. explicit MELODIA_PROJECT_ROOT, if it is the Melodia repository;
2. the MCP process current working directory's Git root;
3. the checkout containing this script.

Mutation rules:
- never operate directly on main;
- never git add .;
- commit only exact requested paths;
- never rebase/reset/clean/stash/force-push;
- "git_pull" means fetch + fast-forward-only when clean and non-divergent.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_REPO = "fromage3900/MelodiaMelusinaV2"


def _run(root: Path, args: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({proc.returncode}): "
            f"{(proc.stderr or proc.stdout).strip()}"
        )
    return proc


def _origin_matches(root: Path) -> bool:
    proc = _run(root, ["remote", "get-url", "origin"])
    if proc.returncode != 0:
        return False
    value = proc.stdout.strip().replace("\\", "/").lower()
    return (
        "fromage3900/melodiamelusinav2" in value
        or "fromage3900:melodiamelusinav2" in value
    )


def _git_root_from(path: Path) -> Path | None:
    proc = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    root = Path(proc.stdout.strip()).resolve()
    return root if _origin_matches(root) else None


def _resolve_project_root() -> Path:
    explicit = os.environ.get("MELODIA_PROJECT_ROOT", "").strip()
    if explicit:
        root = _git_root_from(Path(explicit).expanduser().resolve())
        if root is None:
            raise RuntimeError(
                "MELODIA_PROJECT_ROOT is set but is not the "
                f"{EXPECTED_REPO} checkout: {explicit}"
            )
        return root

    cwd_root = _git_root_from(Path.cwd())
    if cwd_root is not None:
        return cwd_root

    script_root = _git_root_from(Path(__file__).resolve().parent.parent)
    if script_root is not None:
        return script_root

    raise RuntimeError(
        f"Could not resolve an active {EXPECTED_REPO} checkout from env, cwd, or script path."
    )


PROJECT_ROOT = _resolve_project_root()


def _text(proc: subprocess.CompletedProcess[str]) -> str:
    return ((proc.stdout or "") + (proc.stderr or "")).strip()


def _branch() -> str:
    return _run(PROJECT_ROOT, ["branch", "--show-current"], check=True).stdout.strip()


def _head() -> str:
    return _run(PROJECT_ROOT, ["rev-parse", "HEAD"], check=True).stdout.strip()


def _status_lines() -> list[str]:
    out = _run(PROJECT_ROOT, ["status", "--porcelain"], check=True).stdout
    return [line for line in out.splitlines() if line]


def _ahead_behind(left: str, right: str) -> dict[str, int | None]:
    proc = _run(PROJECT_ROOT, ["rev-list", "--left-right", "--count", f"{left}...{right}"])
    if proc.returncode != 0:
        return {"ahead": None, "behind": None}
    parts = proc.stdout.split()
    if len(parts) != 2:
        return {"ahead": None, "behind": None}
    return {"ahead": int(parts[0]), "behind": int(parts[1])}


def _remote_ref_exists(ref: str) -> bool:
    return _run(PROJECT_ROOT, ["show-ref", "--verify", "--quiet", ref]).returncode == 0


def git_status() -> dict[str, Any]:
    branch = _branch()
    status = _status_lines()
    tracking = f"origin/{branch}" if branch and _remote_ref_exists(f"refs/remotes/origin/{branch}") else "origin/main"
    return {
        "status": "success",
        "project_root": str(PROJECT_ROOT),
        "origin": _run(PROJECT_ROOT, ["remote", "get-url", "origin"], check=True).stdout.strip(),
        "branch": branch,
        "head": _head(),
        "dirty": bool(status),
        "working_tree": status,
        "tracking_ref": tracking,
        "tracking_delta": _ahead_behind("HEAD", tracking),
        "main_delta": _ahead_behind("HEAD", "origin/main"),
    }


def _validate_exact_paths(paths: list[str]) -> list[str]:
    if not paths:
        raise RuntimeError("paths is required; git add . is intentionally forbidden")

    clean: list[str] = []
    for raw in paths:
        value = str(raw).strip().replace("\\", "/")
        if not value or value.startswith("/") or value.startswith("../") or "/../" in f"/{value}/":
            raise RuntimeError(f"Only exact repository-relative paths are allowed: {raw!r}")
        if any(ch in value for ch in ("*", "?", "[", "]")):
            raise RuntimeError(f"Globs are not allowed; provide exact paths: {raw!r}")
        clean.append(value)
    return list(dict.fromkeys(clean))


def git_add_commit_push(message: str, paths: list[str]) -> dict[str, Any]:
    branch = _branch()
    if not branch:
        return {"status": "error", "message": "Detached HEAD; refusing mutation."}
    if branch == "main":
        return {"status": "error", "message": "Direct commits/pushes on main are forbidden."}
    if not message.strip():
        return {"status": "error", "message": "A non-empty commit message is required."}

    staged_before = _run(PROJECT_ROOT, ["diff", "--cached", "--name-only"], check=True).stdout.splitlines()
    if staged_before:
        return {
            "status": "error",
            "message": "Pre-existing staged changes found; refusing to mix batches.",
            "staged": staged_before,
        }

    try:
        exact_paths = _validate_exact_paths(paths)
        add = _run(PROJECT_ROOT, ["add", "--", *exact_paths], check=True)
        staged = _run(PROJECT_ROOT, ["diff", "--cached", "--name-only"], check=True).stdout.splitlines()
        unexpected = [path for path in staged if path not in set(exact_paths)]
        if unexpected:
            _run(PROJECT_ROOT, ["restore", "--staged", "--", *staged])
            return {
                "status": "error",
                "message": "Staged set exceeded the requested exact paths; batch was unstaged.",
                "unexpected": unexpected,
            }
        if not staged:
            return {"status": "noop", "message": "No requested changes to commit."}

        commit = _run(PROJECT_ROOT, ["commit", "-m", message.strip()], check=True)
        push = _run(PROJECT_ROOT, ["push", "origin", f"HEAD:refs/heads/{branch}"], check=True)
        return {
            "status": "success",
            "project_root": str(PROJECT_ROOT),
            "branch": branch,
            "head": _head(),
            "paths": staged,
            "add": _text(add),
            "commit": _text(commit),
            "push": _text(push),
        }
    except Exception as exc:
        # Leave any intentionally staged requested paths visible rather than hiding
        # work with a stash/reset. The caller can inspect git_status and decide.
        return {"status": "error", "message": str(exc), "project_root": str(PROJECT_ROOT)}


def git_pull() -> dict[str, Any]:
    """Compatibility name: safe fetch + fast-forward-only synchronization."""
    if _status_lines():
        return {
            "status": "blocked",
            "message": "Working tree is dirty; refusing automatic synchronization.",
            **git_status(),
        }

    branch = _branch()
    if not branch:
        return {"status": "blocked", "message": "Detached HEAD; refusing synchronization."}

    fetch = _run(PROJECT_ROOT, ["fetch", "--prune", "origin"])
    if fetch.returncode != 0:
        return {"status": "error", "message": _text(fetch), "project_root": str(PROJECT_ROOT)}

    remote_ref = f"origin/{branch}"
    if not _remote_ref_exists(f"refs/remotes/origin/{branch}"):
        return {
            "status": "no_remote_branch",
            "message": "Current branch has no same-name remote branch; push it before handoff.",
            **git_status(),
        }

    delta = _ahead_behind("HEAD", remote_ref)
    ahead, behind = delta["ahead"], delta["behind"]
    if ahead and behind:
        return {
            "status": "diverged",
            "message": "Local and remote both moved; explicit reconciliation required.",
            **git_status(),
        }
    if ahead:
        return {
            "status": "ahead",
            "message": "This machine has unpublished commits; push before switching machines.",
            **git_status(),
        }
    if behind:
        merge = _run(PROJECT_ROOT, ["merge", "--ff-only", remote_ref])
        if merge.returncode != 0:
            return {"status": "error", "message": _text(merge), **git_status()}
        return {"status": "synced", "message": "Fast-forward applied.", **git_status()}

    return {"status": "synced", "message": "Already synchronized.", **git_status()}


def git_diff(staged: bool = True) -> dict[str, Any]:
    cmd = ["diff", "--cached"] if staged else ["diff"]
    result = _run(PROJECT_ROOT, cmd)
    return {
        "status": "success" if result.returncode == 0 else "error",
        "project_root": str(PROJECT_ROOT),
        "diff": result.stdout,
        "stderr": result.stderr,
    }


TOOLS = [
    {
        "name": "git_status",
        "description": "Get checkout identity, branch, HEAD, dirty state, and remote deltas.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "git_add_commit_push",
        "description": "Commit and push an exact reviewed path batch on a non-main branch. git add . is forbidden.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exact repository-relative paths only; no globs.",
                },
            },
            "required": ["message", "paths"],
        },
    },
    {
        "name": "git_pull",
        "description": "Safe sync compatibility tool: fetch + fast-forward-only; refuses dirty/ahead/diverged state.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "git_diff",
        "description": "Show staged or unstaged diff.",
        "inputSchema": {
            "type": "object",
            "properties": {"staged": {"type": "boolean"}},
            "required": [],
        },
    },
]


def _write(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        rid = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            _write({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "melodia-safe-git-mcp", "version": "2.0.0"},
                },
            })
        elif method == "tools/list":
            _write({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if name == "git_status":
                    result = git_status()
                elif name == "git_add_commit_push":
                    result = git_add_commit_push(args.get("message", ""), args.get("paths", []))
                elif name == "git_pull":
                    result = git_pull()
                elif name == "git_diff":
                    result = git_diff(bool(args.get("staged", True)))
                else:
                    result = {"status": "error", "message": f"Unknown tool: {name}"}
            except Exception as exc:
                result = {"status": "error", "message": str(exc), "project_root": str(PROJECT_ROOT)}

            _write({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
            })
        elif method == "notifications/initialized":
            continue
        else:
            _write({
                "jsonrpc": "2.0",
                "id": rid,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            })


if __name__ == "__main__":
    main()
