#!/usr/bin/env python3
"""Agent lane registry -- claims, single-writer enforcement, lane bookkeeping.

Why this exists: several agents share one repository. Nothing stopped two of them
from editing the same file, or from committing straight onto `main` in the primary
checkout, which moved HEAD under whoever was not looking. That is the whole failure
mode. This module is the offline half of the fix; `.githooks/pre-commit` is the
enforced half.

Design notes, deliberately boring:

- A lane is a JSON file under `.agents/lanes/<lane_id>.json`. No daemon, no lock
  service, no database.
- Claims are live for a TTL based on `heartbeat_at` (default 30 minutes), so a
  crashed agent stops blocking the repo without anyone having to clean up.
- The lane id is normally supplied by the `LANE_ID` environment variable, which
  `deploy/new_agent_lane.ps1` sets. An empty `LANE_ID` means "integrator/owner",
  which is allowed to write the single-writer paths.

    python Tools/agent_lane_registry.py init --lane cline --worktree <path> --branch <ref>
    python Tools/agent_lane_registry.py claim --lane cline --path Tools/world_compiler.py
    python Tools/agent_lane_registry.py guard --lane cline           # reads the git index
    python Tools/agent_lane_registry.py status
    python Tools/agent_lane_registry.py release --lane cline
    python Tools/agent_lane_registry.py reap --confirm
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LANES_DIR = ROOT / ".agents" / "lanes"
DEFAULT_TTL_MINUTES = 30

SCHEMA = "melodia.agent_lane.v1"

# Paths only the integrator/owner may write. Mirrors specs/source_control_ownership.v1.json
# "single_writer"; duplicated here so the hook does not have to parse that file.
SINGLE_WRITER = (
    "CURRENT_STATE.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".gitignore",
    ".gitattributes",
    "specs/source_control_ownership.v1.json",
    "deploy/run_verify.ps1",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def _lane_path(lane_id: str) -> Path:
    safe = lane_id.strip().lower().replace("\\", "-").replace("/", "-")
    if not safe:
        raise ValueError("lane id must not be empty")
    return LANES_DIR / f"{safe}.json"


def load_lane(lane_id: str) -> dict[str, Any] | None:
    path = _lane_path(lane_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_lane(lane: dict[str, Any]) -> Path:
    LANES_DIR.mkdir(parents=True, exist_ok=True)
    path = _lane_path(str(lane["lane"]))
    path.write_text(json.dumps(lane, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def all_lanes() -> list[dict[str, Any]]:
    if not LANES_DIR.exists():
        return []
    lanes = []
    for path in sorted(LANES_DIR.glob("*.json")):
        try:
            lanes.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return lanes


def is_live(lane: dict[str, Any], ttl_minutes: int = DEFAULT_TTL_MINUTES) -> bool:
    if lane.get("status") != "active":
        return False
    stamp = lane.get("heartbeat_at") or lane.get("started_at")
    if not stamp:
        return False
    try:
        beat = datetime.fromisoformat(str(stamp))
    except ValueError:
        return False
    if beat.tzinfo is None:
        beat = beat.replace(tzinfo=timezone.utc)
    return _now() - beat <= timedelta(minutes=ttl_minutes)


def _matches(lane: dict[str, Any], rel: str) -> bool:
    claims = lane.get("claims") or {}
    for candidate in claims.get("paths", []):
        if rel == candidate:
            return True
    for pattern in claims.get("globs", []):
        if fnmatch(rel, pattern):
            return True
    return False


def conflicts(lane_id: str, rel_paths: list[str], ttl_minutes: int = DEFAULT_TTL_MINUTES) -> list[tuple[str, str]]:
    """Return (other_lane, path) pairs where another LIVE lane already has a claim."""
    found: list[tuple[str, str]] = []
    for lane in all_lanes():
        other = str(lane.get("lane", ""))
        if other == lane_id or not is_live(lane, ttl_minutes):
            continue
        for rel in rel_paths:
            if _matches(lane, rel):
                found.append((other, rel))
    return found


def staged_paths() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z"],
        cwd=ROOT, capture_output=True, check=False,
    )
    if out.returncode != 0:
        return []
    return [p for p in out.stdout.decode("utf-8", "replace").split("\0") if p]


def current_branch() -> str:
    out = subprocess.run(
        ["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, check=False,
    )
    return out.stdout.decode("utf-8", "replace").strip()


# --------------------------------------------------------------------------- commands

def cmd_init(args: argparse.Namespace) -> int:
    lane = load_lane(args.lane) or {
        "schema": SCHEMA,
        "lane": args.lane,
        "started_at": _iso(_now()),
        "claims": {"paths": [], "globs": []},
    }
    lane.update({
        "worktree": args.worktree or lane.get("worktree", ""),
        "branch": args.branch or lane.get("branch", ""),
        "tier": args.tier or lane.get("tier", ""),
        "heartbeat_at": _iso(_now()),
        "status": "active",
    })
    path = save_lane(lane)
    print(f"lane '{args.lane}' registered -> {path}")
    return 0


def cmd_claim(args: argparse.Namespace) -> int:
    lane = load_lane(args.lane)
    if lane is None:
        print(f"ERROR: lane '{args.lane}' is not registered (run init first)", file=sys.stderr)
        return 2
    claimed = list(lane.get("claims", {}).get("paths", []))
    for rel in args.path or []:
        if rel not in claimed:
            claimed.append(rel)
    globs = list(lane.get("claims", {}).get("globs", []))
    for pattern in args.glob or []:
        if pattern not in globs:
            globs.append(pattern)

    hits = conflicts(args.lane, list(args.path or []), args.ttl_minutes)
    if hits:
        print("ERROR: claim refused, another live lane owns these paths:", file=sys.stderr)
        for other, rel in hits:
            print(f"  {rel}  <- lane '{other}'", file=sys.stderr)
        print("Wait for that lane to release, or pick different paths.", file=sys.stderr)
        return 1

    lane["claims"] = {"paths": claimed, "globs": globs}
    lane["heartbeat_at"] = _iso(_now())
    save_lane(lane)
    print(f"lane '{args.lane}' now claims {len(claimed)} path(s), {len(globs)} glob(s)")
    return 0


def cmd_heartbeat(args: argparse.Namespace) -> int:
    lane = load_lane(args.lane)
    if lane is None:
        return 2
    lane["heartbeat_at"] = _iso(_now())
    lane["status"] = "active"
    save_lane(lane)
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    lane = load_lane(args.lane)
    if lane is None:
        print(f"lane '{args.lane}' not found (nothing to release)")
        return 0
    lane["status"] = "released"
    lane["heartbeat_at"] = _iso(_now())
    lane["claims"] = {"paths": [], "globs": []}
    save_lane(lane)
    print(f"lane '{args.lane}' released")
    return 0


def cmd_guard(args: argparse.Namespace) -> int:
    """The pre-commit check. Exit 0 = allow, 1 = refuse, 2 = misconfigured."""
    errors: list[str] = []
    lane_id = (args.lane or os.environ.get("LANE_ID", "")).strip()
    paths = staged_paths()

    # 1. nobody commits onto main except the integrator.
    if args.check_main and current_branch() == "main" and os.environ.get("ALLOW_MAIN_COMMIT") != "1":
        errors.append(
            "HEAD is 'main'. main is not a working branch: it advances only when the "
            "integrator lands a lane. Work in a lane worktree "
            "(deploy/new_agent_lane.ps1), or set ALLOW_MAIN_COMMIT=1 for a deliberate "
            "integrator commit."
        )

    if lane_id:
        # 2. single-writer paths belong to the integrator.
        trespass = [p for p in paths if p in SINGLE_WRITER]
        if trespass:
            errors.append(
                "single-writer path(s) staged by lane '%s': %s\n"
                "    These belong to the integrator. Put status changes in your PR body "
                "or in your lane's own doc." % (lane_id, ", ".join(trespass))
            )
        # 3. overlapping claims.
        hits = conflicts(lane_id, paths, args.ttl_minutes)
        if hits:
            errors.append(
                "path(s) already claimed by another live lane:\n"
                + "\n".join(f"    {rel}  <- lane '{other}'" for other, rel in hits)
            )

    if errors:
        print("ERROR: [agent-lanes] commit refused.", file=sys.stderr)
        for item in errors:
            print(f"  - {item}", file=sys.stderr)
        print("", file=sys.stderr)
        print("  Override only when this change IS the reviewed one:", file=sys.stderr)
        print("    SKIP_LANE_GUARD=1 git commit ...", file=sys.stderr)
        return 1
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    lanes = all_lanes()
    if not lanes:
        print("no lanes registered")
        return 0
    print(f"{'lane':<18} {'state':<6} {'heartbeat':<20} {'claims':>7}  branch")
    for lane in lanes:
        state = "LIVE" if is_live(lane, args.ttl_minutes) else "stale"
        claims = lane.get("claims") or {}
        count = len(claims.get("paths", [])) + len(claims.get("globs", []))
        print(f"{lane.get('lane',''):<18} {state:<6} {lane.get('heartbeat_at',''):<20} "
              f"{count:>7}  {lane.get('branch','')}")
    return 0


def cmd_reap(args: argparse.Namespace) -> int:
    stale = [lane for lane in all_lanes()
             if lane.get("status") == "active" and not is_live(lane, args.ttl_minutes)]
    if not stale:
        print("nothing to reap")
        return 0
    for lane in stale:
        print(f"stale lane (claim expired): {lane.get('lane')}")
        if args.confirm:
            lane["status"] = "stale"
            lane["claims"] = {"paths": [], "globs": []}
            save_lane(lane)
    if not args.confirm:
        print("dry run; re-run with --confirm to release their claims")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ttl-minutes", type=int, default=DEFAULT_TTL_MINUTES)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.add_argument("--lane", required=True)
    p.add_argument("--worktree", default=""); p.add_argument("--branch", default="")
    p.add_argument("--tier", default=""); p.set_defaults(func=cmd_init)

    p = sub.add_parser("claim"); p.add_argument("--lane", required=True)
    p.add_argument("--path", action="append"); p.add_argument("--glob", action="append")
    p.set_defaults(func=cmd_claim)

    p = sub.add_parser("heartbeat"); p.add_argument("--lane", required=True)
    p.set_defaults(func=cmd_heartbeat)

    p = sub.add_parser("release"); p.add_argument("--lane", required=True)
    p.set_defaults(func=cmd_release)

    p = sub.add_parser("guard"); p.add_argument("--lane", default="")
    p.add_argument("--no-check-main", dest="check_main", action="store_false")
    p.set_defaults(func=cmd_guard, check_main=True)

    p = sub.add_parser("status"); p.set_defaults(func=cmd_status)

    p = sub.add_parser("reap"); p.add_argument("--confirm", action="store_true")
    p.set_defaults(func=cmd_reap)

    args = parser.parse_args(argv)
    if args.cmd == "guard" and os.environ.get("SKIP_LANE_GUARD") == "1":
        print("SKIP_LANE_GUARD=1: lane guard bypassed by explicit override")
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
