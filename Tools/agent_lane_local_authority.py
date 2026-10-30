#!/usr/bin/env python3
"""Fail-closed local production authority decisions for agent-lane scripts.

This module is the single policy surface for:
  - lane reuse safety (never reset an existing refs/agents/<lane>)
  - pre-land local production authority (owner attestation + UE/Houdini/P4 probes)

PowerShell entrypoints gather probe facts and call this evaluator. Mocked unit
tests exercise the decision table; they do NOT establish real workstation
safety. Real C:/G:/Perforce/Unreal/Houdini verification remains an owner gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping, Sequence


UNREAL_PROCESS_NAMES = frozenset(
    {
        "unrealeditor",
        "unrealeditor-cmd",
        "unrealeditor-win64-debug",
        "unrealeditor-win64-debuggame",
    }
)

HOUDINI_PROCESS_NAMES = frozenset(
    {
        "houdini",
        "houdinifx",
        "houdinicore",
        "hython",
        "happrentice",
    }
)

PRODUCTION_DIRT_HINTS = (
    ".uasset",
    ".umap",
    ".hip",
    ".hiplc",
    ".hipnc",
    "content/",
    "saved/",
)


@dataclass(frozen=True)
class Decision:
    ok: bool
    code: str
    message: str
    may_reset_ref: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LocalAuthoritySnapshot:
    """Probe facts gathered by the caller. Missing facts fail closed as unknown."""

    owner_reviewed_local_state: bool = False
    uproject_present: bool = False
    unreal_running: bool = False
    houdini_running: bool = False
    primary_git_porcelain: Sequence[str] = field(default_factory=tuple)
    lane_git_porcelain: Sequence[str] = field(default_factory=tuple)
    primary_ignored_porcelain: Sequence[str] = field(default_factory=tuple)
    lane_ignored_porcelain: Sequence[str] = field(default_factory=tuple)
    p4_available: bool = False
    p4_info_ok: bool = False
    p4_info_lines: Sequence[str] = field(default_factory=tuple)
    p4_opened_code: int = 1
    p4_opened_lines: Sequence[str] = field(default_factory=tuple)
    git_status_failed: bool = False
    p4_info_failed: bool = False
    p4_opened_failed: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "LocalAuthoritySnapshot":
        def _lines(key: str) -> tuple[str, ...]:
            raw = data.get(key, ())
            if raw is None:
                return ()
            if isinstance(raw, str):
                return tuple(line for line in raw.splitlines() if line.strip())
            return tuple(str(item) for item in raw if str(item).strip())

        return cls(
            owner_reviewed_local_state=bool(data.get("owner_reviewed_local_state", False)),
            uproject_present=bool(data.get("uproject_present", False)),
            unreal_running=bool(data.get("unreal_running", False)),
            houdini_running=bool(data.get("houdini_running", False)),
            primary_git_porcelain=_lines("primary_git_porcelain"),
            lane_git_porcelain=_lines("lane_git_porcelain"),
            primary_ignored_porcelain=_lines("primary_ignored_porcelain"),
            lane_ignored_porcelain=_lines("lane_ignored_porcelain"),
            p4_available=bool(data.get("p4_available", False)),
            p4_info_ok=bool(data.get("p4_info_ok", False)),
            p4_info_lines=_lines("p4_info_lines"),
            p4_opened_code=int(data.get("p4_opened_code", 1)),
            p4_opened_lines=_lines("p4_opened_lines"),
            git_status_failed=bool(data.get("git_status_failed", False)),
            p4_info_failed=bool(data.get("p4_info_failed", False)),
            p4_opened_failed=bool(data.get("p4_opened_failed", False)),
        )


def evaluate_reuse(
    *,
    ref_exists: bool,
    ref_sha: str | None,
    head_sha: str | None,
    lane_ref: str = "refs/agents/<lane>",
) -> Decision:
    """Reuse must never rewrite an existing agent lane ref."""
    if not ref_exists or not ref_sha:
        return Decision(
            ok=False,
            code="reuse_ref_missing",
            message=(
                f"SAFE STOP: {lane_ref} missing. Preserve worktree HEAD and reflog; "
                "do not reinitialize."
            ),
            may_reset_ref=False,
        )
    if not head_sha:
        return Decision(
            ok=False,
            code="reuse_head_unknown",
            message=(
                f"SAFE STOP: worktree HEAD unknown for {lane_ref}. "
                "Preserve both for manual recovery."
            ),
            may_reset_ref=False,
        )
    if ref_sha.strip().lower() != head_sha.strip().lower():
        return Decision(
            ok=False,
            code="reuse_ref_head_mismatch",
            message=(
                f"SAFE STOP: existing {lane_ref} ({ref_sha}) differs from HEAD ({head_sha}). "
                "Preserve both for manual recovery."
            ),
            may_reset_ref=False,
        )
    return Decision(
        ok=True,
        code="reuse_preserved",
        message=f"preserved existing lane ref {lane_ref} ({ref_sha[:8]})",
        may_reset_ref=False,
    )


def _nonempty_lines(lines: Iterable[str]) -> list[str]:
    return [line for line in lines if str(line).strip()]


def _looks_like_production_dirt(lines: Iterable[str]) -> list[str]:
    hits: list[str] = []
    for line in _nonempty_lines(lines):
        lower = line.lower()
        if any(hint in lower for hint in PRODUCTION_DIRT_HINTS):
            hits.append(line)
    return hits


def _p4_has_server_address(lines: Iterable[str]) -> bool:
    return any("server address:" in str(line).lower() for line in lines)


def _p4_opened_is_empty(code: int, lines: Sequence[str]) -> bool:
    text = "\n".join(lines)
    if "file(s) not opened" in text.lower():
        return True
    if code != 0:
        return False
    return not bool(_nonempty_lines(lines))


def evaluate_local_authority(snapshot: LocalAuthoritySnapshot | Mapping[str, Any]) -> Decision:
    """Fail closed when local UE/Houdini/Perforce state cannot be verified."""
    snap = (
        snapshot
        if isinstance(snapshot, LocalAuthoritySnapshot)
        else LocalAuthoritySnapshot.from_mapping(snapshot)
    )

    if not snap.owner_reviewed_local_state:
        return Decision(
            ok=False,
            code="owner_review_missing",
            message=(
                "SAFE STOP: owner must review live C:/G: workspaces, native "
                "Unreal/Houdini files, Perforce and unsaved editor state first. "
                "Re-run with -OwnerReviewedLocalState only after real review."
            ),
        )

    if not snap.uproject_present:
        return Decision(
            ok=False,
            code="uproject_missing",
            message=(
                "SAFE STOP: no local Unreal project (.uproject). "
                "Git-only integration cannot certify production state; state is UNKNOWN."
            ),
        )

    if snap.unreal_running:
        return Decision(
            ok=False,
            code="unreal_running",
            message=(
                "SAFE STOP: Unreal Editor is running and may have unsaved changes. "
                "Preserve them before landing."
            ),
        )

    if snap.houdini_running:
        return Decision(
            ok=False,
            code="houdini_running",
            message=(
                "SAFE STOP: Houdini is running and may have unsaved scene state. "
                "Preserve .hip work before landing."
            ),
        )

    if snap.git_status_failed:
        return Decision(
            ok=False,
            code="git_status_failed",
            message=(
                "SAFE STOP: git status failed; local tracked/ignored production "
                "dirt is UNKNOWN, not clean."
            ),
        )

    primary_dirt = _nonempty_lines(snap.primary_git_porcelain)
    if primary_dirt:
        return Decision(
            ok=False,
            code="primary_dirty",
            message="SAFE STOP: primary worktree has local changes. Preserve/reconcile before landing.",
        )

    lane_dirt = _nonempty_lines(snap.lane_git_porcelain)
    if lane_dirt:
        return Decision(
            ok=False,
            code="lane_dirty",
            message=(
                "SAFE STOP: lane worktree has uncommitted/untracked files. "
                "Preserve before landing."
            ),
        )

    ignored_hits = _looks_like_production_dirt(snap.primary_ignored_porcelain) + _looks_like_production_dirt(
        snap.lane_ignored_porcelain
    )
    if ignored_hits:
        sample = ignored_hits[0]
        return Decision(
            ok=False,
            code="ignored_production_dirt",
            message=(
                "SAFE STOP: ignored Unreal/Houdini production assets have local dirt "
                f"(example: {sample}). State is UNKNOWN/DIRTY, not clean."
            ),
        )

    if not snap.p4_available:
        return Decision(
            ok=False,
            code="p4_unavailable",
            message="SAFE STOP: Perforce client unavailable; binary production state UNKNOWN.",
        )

    if snap.p4_info_failed or not snap.p4_info_ok or not _p4_has_server_address(snap.p4_info_lines):
        return Decision(
            ok=False,
            code="p4_info_failed",
            message=(
                "SAFE STOP: Perforce server inaccessible; cannot assume Git contains "
                "the full project. State is UNKNOWN."
            ),
        )

    if snap.p4_opened_failed or not _p4_opened_is_empty(snap.p4_opened_code, snap.p4_opened_lines):
        opened_text = "\n".join(_nonempty_lines(snap.p4_opened_lines)) or "(no output)"
        if snap.p4_opened_failed or (
            snap.p4_opened_code != 0 and "file(s) not opened" not in opened_text.lower()
        ):
            return Decision(
                ok=False,
                code="p4_opened_failed",
                message=f"SAFE STOP: Perforce opened check failed: {opened_text}",
            )
        return Decision(
            ok=False,
            code="p4_pending_opened",
            message=(
                "SAFE STOP: Perforce has pending opened files. "
                "Inspect and preserve native assets first."
            ),
        )

    return Decision(
        ok=True,
        code="local_gate_passed",
        message=(
            "local gate passed: owner attestation + bounded probes "
            "(NOT proof of C:/G: backup; mocked tests do not establish workstation safety)"
        ),
    )


def evaluate_missing_lane_target(*, named_lane: bool, worktree_exists: bool, ref_exists: bool) -> Decision:
    """Named lane landings fail closed; -All may report UNKNOWN and continue."""
    if worktree_exists and ref_exists:
        return Decision(ok=True, code="lane_target_ok", message="lane worktree and ref present")
    missing = []
    if not worktree_exists:
        missing.append("worktree")
    if not ref_exists:
        missing.append("ref")
    detail = "+".join(missing)
    if named_lane:
        return Decision(
            ok=False,
            code="named_lane_target_missing",
            message=(
                f"SAFE STOP: named lane target missing ({detail}). "
                "State is UNKNOWN; do not soft-skip a requested landing."
            ),
        )
    return Decision(
        ok=False,
        code="batch_lane_target_unknown",
        message=(
            f"UNKNOWN: lane target missing ({detail}) under -All; "
            "not clean — skipping without claiming success."
        ),
    )


def processes_indicate_unreal(names: Iterable[str]) -> bool:
    return any(str(name).strip().lower() in UNREAL_PROCESS_NAMES for name in names)


def processes_indicate_houdini(names: Iterable[str]) -> bool:
    return any(str(name).strip().lower() in HOUDINI_PROCESS_NAMES for name in names)


def _cmd_reuse(args: argparse.Namespace) -> int:
    decision = evaluate_reuse(
        ref_exists=bool(args.ref_exists),
        ref_sha=args.ref_sha,
        head_sha=args.head_sha,
        lane_ref=args.lane_ref,
    )
    print(json.dumps(decision.to_dict(), indent=2))
    return 0 if decision.ok else 2


def _cmd_evaluate(args: argparse.Namespace) -> int:
    if args.snapshot_json:
        data = json.loads(args.snapshot_json)
    elif args.snapshot_file:
        data = json.loads(PathRead(args.snapshot_file))
    else:
        data = json.load(sys.stdin)
    decision = evaluate_local_authority(data)
    print(json.dumps(decision.to_dict(), indent=2))
    return 0 if decision.ok else 2


def PathRead(path: str) -> str:
    from pathlib import Path

    return Path(path).read_text(encoding="utf-8")


def _cmd_missing_target(args: argparse.Namespace) -> int:
    decision = evaluate_missing_lane_target(
        named_lane=bool(args.named_lane),
        worktree_exists=bool(args.worktree_exists),
        ref_exists=bool(args.ref_exists),
    )
    print(json.dumps(decision.to_dict(), indent=2))
    # For -All UNKNOWN skips, exit 3 so the caller can soft-continue without
    # treating the target as clean. Named-lane missing still exits 2 (hard fail).
    if decision.ok:
        return 0
    if decision.code == "batch_lane_target_unknown":
        return 3
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    reuse = sub.add_parser("reuse", help="Evaluate lane reuse safety")
    reuse.add_argument("--lane-ref", default="refs/agents/<lane>")
    reuse.add_argument("--ref-exists", action="store_true")
    reuse.add_argument("--ref-sha", default="")
    reuse.add_argument("--head-sha", default="")
    reuse.set_defaults(func=_cmd_reuse)

    evaluate = sub.add_parser("evaluate", help="Evaluate local production authority snapshot")
    evaluate.add_argument("--snapshot-json", default="")
    evaluate.add_argument("--snapshot-file", default="")
    evaluate.set_defaults(func=_cmd_evaluate)

    missing = sub.add_parser("missing-target", help="Evaluate missing worktree/ref policy")
    missing.add_argument("--named-lane", action="store_true")
    missing.add_argument("--worktree-exists", action="store_true")
    missing.add_argument("--ref-exists", action="store_true")
    missing.set_defaults(func=_cmd_missing_target)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
