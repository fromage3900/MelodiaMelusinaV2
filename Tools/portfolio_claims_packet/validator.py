"""Validate the publication-safe gameplay systems claims packet.

The validator is intentionally filesystem-local and dependency-free. It checks that every public
claim points at a durable, line-addressable source, that open gates cannot be described as shipped,
and that design intent is not phrased as implementation evidence.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CLAIMS_PATH = REPO_ROOT / "Docs" / "Portfolio" / "gameplay_system_claims_2026-08-24.json"
STATUS_VOCABULARY = (
    "VERIFIED_RUNTIME",
    "VERIFIED_OFFLINE",
    "SOURCE_BUILT_LIVE_PENDING",
    "DESIGN_INTENT",
    "RETIRED_PROTOTYPE",
    "NEED_EVIDENCE",
)
CLAIM_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,80}$")
OPEN_GATE_STATES = {"OPEN", "VIOLATED", "NOT_WIRED", "FAIL"}
COMPLETE_TERMS_RE = re.compile(
    r"\b(?:complete(?:d)?|works?|working|shipped|closed|proven|verified|passed|live|done)\b",
    re.IGNORECASE,
)
INTENT_TERMS_RE = re.compile(
    r"\b(?:will|should|plan(?:ned)?|intend(?:ed)?|target|would|to be built|to be wired)\b",
    re.IGNORECASE,
)
EPHEMERAL_TERMS_RE = re.compile(
    r"(?:local session|current pid|editor reservation|localhost|127\.0\.0\.1|just now|in this run|overnight)",
    re.IGNORECASE,
)
RETIRED_TERMS_RE = re.compile(r"\b(?:retired|dead|compatibility-only|not on the shipping path)\b", re.IGNORECASE)


def _as_repo_path(repo_root: Path, raw_path: Any) -> tuple[Path | None, str | None]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None, "evidence path must be a non-empty relative string"
    candidate_text = raw_path.replace("\\", "/")
    candidate = Path(candidate_text)
    if candidate.is_absolute() or ":" in candidate_text.split("/")[0]:
        return None, f"evidence path must be relative: {raw_path}"
    resolved = (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None, f"evidence path escapes repository: {raw_path}"
    return resolved, None


def _validate_evidence(
    evidence: Any,
    *,
    repo_root: Path,
    claim_id: str,
    errors: list[str],
) -> None:
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{claim_id}: evidence must be a non-empty list")
        return
    for index, item in enumerate(evidence):
        prefix = f"{claim_id}: evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if item.get("ephemeral") is True or item.get("kind") == "ephemeral":
            errors.append(f"{prefix} is marked ephemeral")
        path, path_error = _as_repo_path(repo_root, item.get("path"))
        if path_error:
            errors.append(f"{prefix}: {path_error}")
        elif path is not None and not path.is_file():
            errors.append(f"{prefix}: source does not exist: {item.get('path')}")
        line = item.get("line")
        if not isinstance(line, int) or isinstance(line, bool) or line < 1:
            errors.append(f"{prefix}: line must be a positive integer")
        elif path is not None and path.is_file():
            line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
            if line > line_count:
                errors.append(f"{prefix}: line {line} exceeds {line_count} lines in {item.get('path')}")
        if not isinstance(item.get("note"), str) or not item["note"].strip():
            errors.append(f"{prefix}: note must be non-empty")


def validate_claims(data: Any, repo_root: Path = REPO_ROOT) -> list[str]:
    """Return human-readable validation errors; an empty list means valid."""

    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be an object"]
    if data.get("schema") != "melodia.gameplay_system_claims.v1":
        errors.append("root schema must be melodia.gameplay_system_claims.v1")
    if tuple(data.get("status_vocabulary", ())) != STATUS_VOCABULARY:
        errors.append("status_vocabulary must exactly match the six approved statuses")

    open_gates = data.get("open_gates")
    gate_states: dict[str, str] = {}
    if not isinstance(open_gates, list):
        errors.append("open_gates must be a list")
    else:
        for index, gate in enumerate(open_gates):
            prefix = f"open_gates[{index}]"
            if not isinstance(gate, dict):
                errors.append(f"{prefix} must be an object")
                continue
            gate_id = gate.get("id")
            state = gate.get("state")
            if not isinstance(gate_id, str) or not CLAIM_ID_RE.fullmatch(gate_id):
                errors.append(f"{prefix}: invalid gate id")
            elif gate_id in gate_states:
                errors.append(f"duplicate open gate id: {gate_id}")
            else:
                gate_states[gate_id] = state if isinstance(state, str) else ""
            if state not in OPEN_GATE_STATES:
                errors.append(f"{prefix}: state must be one of {sorted(OPEN_GATE_STATES)}")
            _validate_evidence(gate.get("evidence"), repo_root=repo_root, claim_id=prefix, errors=errors)

    claims = data.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append("claim must be an object")
            continue
        claim_id = claim.get("id")
        label = claim_id if isinstance(claim_id, str) else "<missing-id>"
        if not isinstance(claim_id, str) or not CLAIM_ID_RE.fullmatch(claim_id):
            errors.append(f"{label}: id must be stable snake_case")
        elif claim_id in seen_ids:
            errors.append(f"duplicate claim id: {claim_id}")
        else:
            seen_ids.add(claim_id)

        copy = claim.get("copy")
        if not isinstance(copy, str) or not copy.strip():
            errors.append(f"{label}: copy must be non-empty")
            copy = ""
        status = claim.get("proof_status")
        if status not in STATUS_VOCABULARY:
            errors.append(f"{label}: invalid proof_status {status!r}")
        approved = claim.get("approved_for_publication")
        if not isinstance(approved, bool):
            errors.append(f"{label}: approved_for_publication must be boolean")
        elif status in {"VERIFIED_RUNTIME", "VERIFIED_OFFLINE"} and not approved:
            errors.append(f"{label}: verified claims must be approved_for_publication=true")
        elif status in {"SOURCE_BUILT_LIVE_PENDING", "DESIGN_INTENT", "RETIRED_PROTOTYPE", "NEED_EVIDENCE"} and approved:
            errors.append(f"{label}: non-verified claims cannot be approved_for_publication")

        if EPHEMERAL_TERMS_RE.search(copy):
            errors.append(f"{label}: copy contains an ephemeral local fact")
        if status != "DESIGN_INTENT" and INTENT_TERMS_RE.search(copy):
            errors.append(f"{label}: implementation claim is phrased as intent")
        if status in {"VERIFIED_RUNTIME", "VERIFIED_OFFLINE"} and re.search(r"\b(?:open|pending|unproven|not wired|not proven)\b", copy, re.IGNORECASE):
            errors.append(f"{label}: verified claim contains open/pending language")
        if status in {"NEED_EVIDENCE", "SOURCE_BUILT_LIVE_PENDING"} and COMPLETE_TERMS_RE.search(copy):
            errors.append(f"{label}: open or pending claim is phrased as complete")
        if status == "RETIRED_PROTOTYPE" and not RETIRED_TERMS_RE.search(copy):
            errors.append(f"{label}: retired claim must state its retired/compatibility posture")
        _validate_evidence(claim.get("evidence"), repo_root=repo_root, claim_id=label, errors=errors)

        gate_refs = claim.get("gate_refs", [])
        if not isinstance(gate_refs, list):
            errors.append(f"{label}: gate_refs must be a list")
            gate_refs = []
        for gate_id in gate_refs:
            if gate_id not in gate_states:
                errors.append(f"{label}: gate_ref is not listed in open_gates: {gate_id}")
            elif status in {"VERIFIED_RUNTIME", "VERIFIED_OFFLINE"} or approved or COMPLETE_TERMS_RE.search(copy):
                errors.append(f"{label}: open gate {gate_id} is described as complete")

    return errors


def load_claims(path: Path = CLAIMS_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    try:
        errors = validate_claims(load_claims())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}")
        return 1
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VALID: {CLAIMS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
