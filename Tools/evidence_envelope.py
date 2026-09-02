#!/usr/bin/env python3
"""Create and validate durable evidence envelopes for Melodia gates.

This is intentionally dependency-free. The JSON Schema files are canonical;
this module enforces the subset needed by local gate tooling and CI bootstrap.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "specs" / "schemas"


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _repository_branch() -> str:
    """Return a useful ref name in local, CI, and detached checkouts."""
    branch = _git("branch", "--show-current")
    if branch:
        return branch
    for name in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    # GitHub Actions and several archive/check-only workflows intentionally use
    # detached HEAD. Evidence still needs a non-empty, honest locator.
    commit = _git("rev-parse", "--short", "HEAD")
    return f"detached@{commit}" if commit and commit != "unknown" else "detached"


def validate_envelope(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["envelope must be an object"]
    required = [
        "schema", "evidence_id", "run_id", "kind", "status", "recorded_at_utc",
        "repository", "producer", "checks", "artifacts",
    ]
    for field in required:
        if field not in value:
            errors.append(f"missing required field: {field}")
    if value.get("schema") != "melodia.evidence_envelope.v1":
        errors.append("schema must be melodia.evidence_envelope.v1")
    if value.get("kind") not in {"gate", "static", "runtime", "t3d_mutation", "build", "package", "model"}:
        errors.append("kind is not supported")
    if value.get("status") not in {"pass", "fail", "hold"}:
        errors.append("status must be pass, fail, or hold")
    repository = value.get("repository")
    if not isinstance(repository, dict):
        errors.append("repository must be an object")
    else:
        for field in ("root", "commit", "branch"):
            if not isinstance(repository.get(field), str) or not repository[field]:
                errors.append(f"repository.{field} must be a non-empty string")
    producer = value.get("producer")
    if not isinstance(producer, dict):
        errors.append("producer must be an object")
    else:
        for field in ("tool", "version"):
            if not isinstance(producer.get(field), str) or not producer[field]:
                errors.append(f"producer.{field} must be a non-empty string")
    checks = value.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty array")
    else:
        for index, check in enumerate(checks):
            if not isinstance(check, dict):
                errors.append(f"checks[{index}] must be an object")
                continue
            if not check.get("name"):
                errors.append(f"checks[{index}].name is required")
            if check.get("status") not in {"pass", "fail", "hold"}:
                errors.append(f"checks[{index}].status is invalid")
    if not isinstance(value.get("artifacts"), list):
        errors.append("artifacts must be an array")
    return errors


def make_envelope(
    *,
    kind: str,
    status: str,
    producer: str,
    check_name: str,
    check_status: str,
    note: str = "",
    gate_id: str | None = None,
    subject: dict[str, Any] | None = None,
    artifacts: list[str] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    run_id = f"run-{uuid.uuid4().hex[:16]}"
    envelope: dict[str, Any] = {
        "schema": "melodia.evidence_envelope.v1",
        "evidence_id": f"evidence-{uuid.uuid4().hex[:16]}",
        "run_id": run_id,
        "kind": kind,
        "status": status,
        "recorded_at_utc": now,
        "repository": {
            "root": str(ROOT),
            "commit": _git("rev-parse", "HEAD"),
            "branch": _repository_branch(),
        },
        "producer": {"tool": producer, "version": "1"},
        "checks": [{"name": check_name, "status": check_status, "note": note}],
        "artifacts": [{"path": path} for path in (artifacts or [])],
    }
    if gate_id:
        envelope["gate_id"] = gate_id
    if subject:
        envelope["subject"] = subject
    if note:
        envelope["notes"] = note
    errors = validate_envelope(envelope)
    if errors:
        raise ValueError("; ".join(errors))
    return envelope


def write_envelope(envelope: dict[str, Any], path: Path) -> None:
    errors = validate_envelope(envelope)
    if errors:
        raise ValueError("; ".join(errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or validate a Melodia evidence envelope")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--kind", required=True, choices=["gate", "static", "runtime", "t3d_mutation", "build", "package", "model"])
    create.add_argument("--status", required=True, choices=["pass", "fail", "hold"])
    create.add_argument("--producer", required=True)
    create.add_argument("--check-name", required=True)
    create.add_argument("--check-status", required=True, choices=["pass", "fail", "hold"])
    create.add_argument("--note", default="")
    create.add_argument("--gate-id")
    create.add_argument("--subject-json")
    create.add_argument("--artifact", action="append", default=[])
    create.add_argument("--output", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    args = parser.parse_args()

    if args.command == "validate":
        value = json.loads(Path(args.path).read_text(encoding="utf-8"))
        errors = validate_envelope(value)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print(f"PASS: {args.path}")
        return 0

    subject = json.loads(args.subject_json) if args.subject_json else None
    envelope = make_envelope(
        kind=args.kind,
        status=args.status,
        producer=args.producer,
        check_name=args.check_name,
        check_status=args.check_status,
        note=args.note,
        gate_id=args.gate_id,
        subject=subject,
        artifacts=args.artifact,
    )
    write_envelope(envelope, Path(args.output))
    print(json.dumps(envelope, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
