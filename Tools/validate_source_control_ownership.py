#!/usr/bin/env python3
"""Read-only validation of the Git/Perforce ownership contract."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "specs" / "source_control_ownership.v1.json"


def norm(value: str) -> str:
    value = value.replace("\\", "/").lstrip("./")
    return value if value.endswith("/") else value


def covers(root: str, path: str) -> bool:
    root, path = norm(root), norm(path)
    return path == root.rstrip("/") or path.startswith(root.rstrip("/") + "/")


def validate(data: dict, check_files: bool = False) -> list[str]:
    errors: list[str] = []
    authorities = data.get("authorities")
    if not isinstance(authorities, dict) or not authorities.get("git") or not authorities.get("perforce"):
        return ["manifest must define git and perforce authorities"]
    roots: dict[str, list[str]] = {}
    for name in ("git", "perforce"):
        raw = authorities[name].get("roots")
        if not isinstance(raw, list) or not raw or any(not isinstance(x, str) or not x for x in raw):
            errors.append(f"{name} authority must have non-empty string roots")
        roots[name] = [norm(x) for x in (raw or [])]
    for git in roots.get("git", []):
        for p4 in roots.get("perforce", []):
            if covers(git, p4) or covers(p4, git):
                errors.append(f"dual ownership overlap: {git!r} and {p4!r}")
    required = data.get("required_external_roots", [])
    p4_roots = roots.get("perforce", [])
    for required_root in required:
        if not any(covers(root, required_root) for root in p4_roots):
            errors.append(f"required external root is not Perforce-owned: {required_root}")
    bundles = data.get("level_bundles")
    if not isinstance(bundles, list) or len(bundles) != 3:
        errors.append("level_bundles must contain exactly the three live maps")
        bundles = bundles if isinstance(bundles, list) else []
    names: set[str] = set()
    for bundle in bundles:
        if not isinstance(bundle, dict):
            errors.append("each level bundle must be an object")
            continue
        name = bundle.get("name")
        if not isinstance(name, str) or not name or name in names:
            errors.append(f"invalid or duplicate level bundle name: {name!r}")
        names.add(name)
        for field in ("map", "external_actors", "external_objects"):
            path = bundle.get(field)
            if not isinstance(path, str) or not path:
                errors.append(f"{name or '<unnamed>'} missing {field}")
            elif not any(covers(root, path) for root in p4_roots):
                errors.append(f"{name or '<unnamed>'} {field} is not Perforce-owned: {path}")
            elif check_files:
                target = ROOT / path.rstrip("/")
                if not target.exists():
                    errors.append(f"{name or '<unnamed>'} {field} missing on disk: {path}")
    return errors


def validate_git_cutover(data: dict) -> list[str]:
    """Prove that no target-Perforce path remains tracked by Git."""
    p4_roots = data["authorities"]["perforce"]["roots"]
    proc = subprocess.run(
        ["git", "ls-files", "--", *p4_roots],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        return [f"git ownership query failed: {proc.stderr.strip() or proc.returncode}"]
    conflicts = [line for line in proc.stdout.splitlines() if line.strip()]
    if not conflicts:
        return []
    sample = ", ".join(conflicts[:5])
    suffix = f" (+{len(conflicts) - 5} more)" if len(conflicts) > 5 else ""
    return [
        f"cutover incomplete: {len(conflicts)} target-Perforce files remain Git-owned: "
        f"{sample}{suffix}"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--check-files", action="store_true", help="also check the three bundle paths exist")
    parser.add_argument(
        "--check-cutover",
        action="store_true",
        help="fail while any target-Perforce path remains tracked by Git",
    )
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"FAIL: manifest not found: {args.manifest}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read manifest: {exc}", file=sys.stderr)
        return 2
    errors = validate(data, args.check_files)
    if args.check_cutover and not errors:
        errors.extend(validate_git_cutover(data))
    if errors:
        print("FAIL: source-control ownership contract")
        print("\n".join(f"  - {error}" for error in errors))
        return 1
    print(f"PASS: source-control ownership contract ({len(data['level_bundles'])} level bundles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
