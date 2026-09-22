#!/usr/bin/env python3
"""Echo Reflex canary.

Adaptive controller layered on top of Melodia's existing Echo contracts.

- Astra/human plans a mission DAG using registered capability IDs.
- Code computes legal/eligible nodes and enforces resources/policy.
- Jev may choose among already-legal eligible nodes.
- Existing owners execute; this canary never invents shell commands.
- v0 is preview-only and never writes the Echo gate ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "specs" / "echo_reflex_capabilities.v1.json"

TERMINAL = {"PASS", "FAIL", "HOLD"}
OPEN = {"PENDING", "RUNNING"}


class ReflexError(ValueError):
    """Invalid registry/mission/state."""


@dataclass(frozen=True)
class ReflexDecision:
    action: str  # SELECT | HOLD | REPLAN | COMPLETE
    node_id: Optional[str]
    source: str  # deterministic | jev-live | fail-closed
    confidence: float
    reason: str
    distribution: dict[str, float]
    needs_human: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "node_id": self.node_id,
            "source": self.source,
            "confidence": round(float(self.confidence), 4),
            "reason": self.reason,
            "distribution": {
                k: round(float(v), 4) for k, v in self.distribution.items()
            },
            "needs_human": self.needs_human,
        }


def _load_json(path: str | Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReflexError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ReflexError(f"invalid JSON {path}: {exc}") from exc


def load_registry(
    path: str | Path = DEFAULT_REGISTRY,
) -> dict[str, dict[str, Any]]:
    raw = _load_json(path)
    if raw.get("$schema") != "melodia.echo_reflex_capabilities.v1":
        raise ReflexError("registry must use melodia.echo_reflex_capabilities.v1")
    caps = raw.get("capabilities")
    if not isinstance(caps, list) or not caps:
        raise ReflexError("registry.capabilities must be a non-empty list")

    out: dict[str, dict[str, Any]] = {}
    for cap in caps:
        if not isinstance(cap, dict) or not isinstance(cap.get("id"), str):
            raise ReflexError("every capability needs a string id")
        cid = cap["id"]
        if cid in out:
            raise ReflexError(f"duplicate capability id: {cid}")
        mutation = cap.get("mutation", "none")
        if mutation not in {"none", "saved_output", "repo_write", "ue_editor", "human"}:
            raise ReflexError(f"{cid}: unknown mutation class {mutation}")
        out[cid] = cap
    return out


def _node_map(mission: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = mission.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ReflexError("mission.nodes must be a non-empty list")
    out: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ReflexError("mission node must be an object")
        nid = node.get("id")
        if not isinstance(nid, str) or not nid:
            raise ReflexError("mission node needs non-empty string id")
        if nid in out:
            raise ReflexError(f"duplicate mission node id: {nid}")
        out[nid] = node
    return out


def validate_mission(
    mission: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> None:
    if mission.get("$schema") != "melodia.echo_reflex_mission.v1":
        raise ReflexError("mission must use melodia.echo_reflex_mission.v1")
    if not isinstance(mission.get("goal"), str) or not mission["goal"].strip():
        raise ReflexError("mission.goal must be non-empty")

    nodes = _node_map(mission)
    for nid, node in nodes.items():
        cid = node.get("capability")
        if cid not in registry:
            raise ReflexError(f"{nid}: unknown capability {cid!r}")
        deps = node.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(d, str) for d in deps):
            raise ReflexError(f"{nid}: depends_on must be a string list")
        if nid in deps:
            raise ReflexError(f"{nid}: self dependency")
        missing = [d for d in deps if d not in nodes]
        if missing:
            raise ReflexError(f"{nid}: unknown dependencies {missing}")

    indeg = {nid: 0 for nid in nodes}
    adj = {nid: [] for nid in nodes}
    for nid, node in nodes.items():
        for dep in node.get("depends_on", []):
            indeg[nid] += 1
            adj[dep].append(nid)
    queue = sorted(nid for nid, degree in indeg.items() if degree == 0)
    visited: list[str] = []
    while queue:
        cur = queue.pop(0)
        visited.append(cur)
        for nxt in adj[cur]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
                queue.sort()
    if len(visited) != len(nodes):
        raise ReflexError("mission graph contains a cycle")


def initial_state(mission: dict[str, Any]) -> dict[str, Any]:
    nodes = _node_map(mission)
    return {
        "mission_id": mission.get("id", "unnamed"),
        "nodes": {
            nid: {"status": "PENDING", "attempts": 0}
            for nid in nodes
        },
        "held_resources": [],
        "history": [],
    }


def normalize_state(
    mission: dict[str, Any],
    state: Optional[dict[str, Any]],
) -> dict[str, Any]:
    if state is None:
        return initial_state(mission)
    nodes = _node_map(mission)
    state_nodes = state.get("nodes", {})
    if not isinstance(state_nodes, dict):
        raise ReflexError("state.nodes must be an object")
    for nid in nodes:
        rec = state_nodes.setdefault(
            nid, {"status": "PENDING", "attempts": 0}
        )
        status = rec.get("status", "PENDING")
        if status not in TERMINAL | OPEN:
            raise ReflexError(f"{nid}: invalid state status {status!r}")
    state.setdefault("held_resources", [])
    state.setdefault("history", [])
    return state


def eligible_nodes(
    mission: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    state: dict[str, Any],
) -> list[str]:
    nodes = _node_map(mission)
    held = set(state.get("held_resources", []))
    ready: list[str] = []
    for nid, node in nodes.items():
        rec = state["nodes"][nid]
        if rec.get("status") != "PENDING":
            continue
        deps = node.get("depends_on", [])
        if not all(
            state["nodes"][dep].get("status") == "PASS"
            for dep in deps
        ):
            continue
        cap = registry[node["capability"]]
        required = set(cap.get("resources", []))
        if required & held:
            continue
        ready.append(nid)
    return sorted(ready)


def mission_complete(
    mission: dict[str, Any],
    state: dict[str, Any],
) -> bool:
    return all(
        state["nodes"][nid].get("status") == "PASS"
        for nid in _node_map(mission)
    )


def mission_blocked(
    mission: dict[str, Any],
    state: dict[str, Any],
) -> bool:
    nodes = _node_map(mission)
    for nid, node in nodes.items():
        if state["nodes"][nid].get("status") != "PENDING":
            continue
        for dep in node.get("depends_on", []):
            if state["nodes"][dep].get("status") in {"FAIL", "HOLD"}:
                return True
    return False


def _requires_human(
    node: dict[str, Any],
    cap: dict[str, Any],
    mission: dict[str, Any],
) -> bool:
    if cap.get("executor", {}).get("type") == "human":
        return True
    policies = mission.get("policies", {})
    classes = set(
        policies.get(
            "human_review_mutations",
            ["repo_write", "ue_editor", "human"],
        )
    )
    return cap.get("mutation", "none") in classes


def _selection_state(
    mission: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    state: dict[str, Any],
    eligible: Iterable[str],
) -> dict[str, Any]:
    nodes = _node_map(mission)
    eligible = list(eligible)
    return {
        "mission": {
            "id": mission.get("id"),
            "goal": mission.get("goal"),
            "planner": mission.get("planner"),
        },
        "eligible": [
            {
                "node_id": nid,
                "capability": nodes[nid]["capability"],
                "label": nodes[nid].get("label", nid),
                "mutation": registry[nodes[nid]["capability"]].get(
                    "mutation", "none"
                ),
                "resources": registry[nodes[nid]["capability"]].get(
                    "resources", []
                ),
                "acceptance": nodes[nid].get("acceptance", []),
            }
            for nid in eligible
        ],
        "history": state.get("history", [])[-8:],
    }


def _jev_choose(
    mission: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    state: dict[str, Any],
    eligible: list[str],
) -> Optional[ReflexDecision]:
    """One Jev Choice over legal node ids only."""
    if not os.environ.get("TYPESAFE_API_KEY"):
        return None
    try:
        from typesafe_sdk import TypeSafeClient  # type: ignore
    except Exception:
        return None

    nodes = _node_map(mission)
    options = list(eligible) + ["HOLD", "REPLAN"]
    instructions = (
        "Choose the single best next transition for this already-validated "
        "Melodia mission. Node ids are legal executable candidates computed "
        "by deterministic code. Choose HOLD if owner judgment or missing "
        "evidence should stop work. Choose REPLAN if the current mission "
        "graph cannot reach the goal without changing the plan. Never invent "
        "another action."
    )
    try:
        with TypeSafeClient() as client:
            result = client.system_one.create(
                state=_selection_state(
                    mission, registry, state, eligible
                ),
                questions=[{
                    "id": "next_transition",
                    "type": "choice",
                    "options": options,
                    "instructions": instructions,
                }],
            )
        answer = result.answers[0]
        choice = str(answer.answer)
        confidence = float(answer.confidence or 0.0)
        raw_probs = getattr(answer, "probabilities", None) or {}
        if isinstance(raw_probs, dict):
            distribution = {
                str(k): float(v)
                for k, v in raw_probs.items()
                if str(k) in options
            }
        else:
            distribution = {choice: confidence}

        if choice not in options:
            return ReflexDecision(
                "HOLD", None, "fail-closed", 1.0,
                "Jev returned an unauthored transition",
                {}, True,
            )
        if choice == "HOLD":
            return ReflexDecision(
                "HOLD", None, "jev-live", confidence,
                "Jev selected HOLD", distribution, True,
            )
        if choice == "REPLAN":
            return ReflexDecision(
                "REPLAN", None, "jev-live", confidence,
                "Jev selected REPLAN", distribution, False,
            )

        cap = registry[nodes[choice]["capability"]]
        return ReflexDecision(
            "SELECT", choice, "jev-live", confidence,
            "Jev selected legal mission node",
            distribution,
            _requires_human(nodes[choice], cap, mission),
        )
    except Exception as exc:
        return ReflexDecision(
            "HOLD", None, "fail-closed", 1.0,
            f"Jev call failed: {type(exc).__name__}",
            {}, True,
        )


def choose_next(
    mission: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    state: dict[str, Any],
    live_jev: bool = True,
) -> ReflexDecision:
    ready = eligible_nodes(mission, registry, state)

    if mission_complete(mission, state):
        return ReflexDecision(
            "COMPLETE", None, "deterministic", 1.0,
            "all mission nodes are PASS", {}, False,
        )

    if not ready:
        if mission_blocked(mission, state):
            return ReflexDecision(
                "REPLAN", None, "deterministic", 1.0,
                "a failed/held dependency blocks remaining work",
                {}, False,
            )
        return ReflexDecision(
            "HOLD", None, "deterministic", 1.0,
            "no legal node is currently eligible", {}, True,
        )

    if len(ready) == 1:
        nid = ready[0]
        node = _node_map(mission)[nid]
        cap = registry[node["capability"]]
        return ReflexDecision(
            "SELECT", nid, "deterministic", 1.0,
            "only one legal next node", {nid: 1.0},
            _requires_human(node, cap, mission),
        )

    if live_jev:
        decision = _jev_choose(
            mission, registry, state, ready
        )
        if decision is not None:
            return decision

    return ReflexDecision(
        "HOLD", None, "fail-closed", 1.0,
        "multiple legal nodes require Jev or owner judgment",
        {
            nid: round(1.0 / len(ready), 4)
            for nid in ready
        },
        True,
    )


def preview_node(
    mission: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    node_id: str,
) -> dict[str, Any]:
    nodes = _node_map(mission)
    if node_id not in nodes:
        raise ReflexError(f"unknown node {node_id}")
    node = nodes[node_id]
    cap = registry[node["capability"]]
    return {
        "node_id": node_id,
        "capability": node["capability"],
        "label": node.get("label", node_id),
        "args": node.get("args", {}),
        "mutation": cap.get("mutation", "none"),
        "resources": cap.get("resources", []),
        "executor": cap.get("executor", {}),
        "auto_execute": bool(cap.get("auto_execute", False)),
        "acceptance": node.get("acceptance", []),
        "note": (
            "preview only; v0 does not execute or write gate ledger"
        ),
    }



def _safe_repo_path(value: Any, spec: dict[str, Any]) -> str:
    if not isinstance(value, str) or not value:
        raise ReflexError("path argument must be a non-empty string")
    rel = Path(value.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts:
        raise ReflexError(f"unsafe repo path: {value!r}")
    norm = rel.as_posix()
    prefixes = spec.get("allowed_prefixes", [])
    if prefixes and not any(norm.startswith(prefix) for prefix in prefixes):
        raise ReflexError(f"path outside allowed prefixes: {norm}")
    suffixes = spec.get("suffixes", [])
    if suffixes and not any(norm.endswith(suffix) for suffix in suffixes):
        raise ReflexError(f"path has disallowed suffix: {norm}")
    return norm


def _render_python_argv(
    node: dict[str, Any],
    cap: dict[str, Any],
) -> list[str]:
    executor = cap.get("executor", {})
    kind = executor.get("type")
    if kind not in {"python", "python_template"}:
        raise ReflexError(f"executor {kind!r} is not a Python read-only action")

    args = node.get("args", {})
    declared = cap.get("arguments", {})
    unknown = sorted(set(args) - set(declared))
    if unknown:
        raise ReflexError(f"undeclared capability arguments: {unknown}")

    resolved: dict[str, str] = {}
    for name, arg_spec in declared.items():
        if name not in args:
            raise ReflexError(f"missing required capability argument: {name}")
        if arg_spec.get("type") == "repo_path":
            resolved[name] = _safe_repo_path(args[name], arg_spec)
        else:
            raise ReflexError(f"unsupported argument type for {name}")

    argv = []
    for token in executor.get("argv", []):
        if not isinstance(token, str):
            raise ReflexError("executor argv entries must be strings")
        argv.append(token.format(**resolved))
    if not argv:
        raise ReflexError("empty Python executor argv")

    script = _safe_repo_path(
        argv[0],
        {"allowed_prefixes": ["Tools/", "Content/Python/"], "suffixes": [".py"]},
    )
    if not (ROOT / script).is_file():
        raise ReflexError(f"registered Python tool does not exist: {script}")
    argv[0] = script
    return argv


def execute_readonly(
    mission: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    node_id: str,
    timeout: int = 120,
) -> tuple[str, dict[str, Any]]:
    """Execute only registry-approved mutation=none capabilities.

    This is intentionally narrower than a general executor. It cannot execute
    repo writes, editor writes, specialist agents, Hython, or human actions.
    """
    nodes = _node_map(mission)
    if node_id not in nodes:
        raise ReflexError(f"unknown node {node_id}")
    node = nodes[node_id]
    cap = registry[node["capability"]]

    if cap.get("mutation", "none") != "none":
        raise ReflexError("read-only executor refused a mutating capability")
    if not cap.get("auto_execute", False):
        raise ReflexError("capability is not allowlisted for read-only auto execution")

    executor = cap.get("executor", {})
    kind = executor.get("type")

    if kind == "read_file":
        rel = _safe_repo_path(
            executor.get("path"),
            {"allowed_prefixes": ["CURRENT_STATE.md", "Docs/", "specs/"]},
        )
        path = (ROOT / rel).resolve()
        try:
            path.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ReflexError("read_file escaped repository root") from exc
        data = path.read_bytes()
        return "PASS", {
            "kind": "read_file",
            "path": rel,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    if kind in {"python", "python_template"}:
        argv = _render_python_argv(node, cap)
        try:
            run = subprocess.run(
                [sys.executable, *argv],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return "FAIL", {
                "kind": kind,
                "argv": argv,
                "error": "timeout",
                "timeout_seconds": timeout,
                "stdout": (exc.stdout or "")[-16000:],
                "stderr": (exc.stderr or "")[-16000:],
            }
        evidence = {
            "kind": kind,
            "argv": argv,
            "exit_code": run.returncode,
            "stdout": run.stdout[-16000:],
            "stderr": run.stderr[-16000:],
        }
        return ("PASS" if run.returncode == 0 else "FAIL"), evidence

    raise ReflexError(f"executor type {kind!r} is not allowed by read-only v0")


def mark(
    mission: dict[str, Any],
    state: dict[str, Any],
    node_id: str,
    status: str,
    evidence: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    nodes = _node_map(mission)
    if node_id not in nodes:
        raise ReflexError(f"unknown node {node_id}")
    if status not in TERMINAL:
        raise ReflexError(
            "mark status must be PASS, FAIL, or HOLD"
        )
    rec = state["nodes"][node_id]
    rec["status"] = status
    rec["attempts"] = int(rec.get("attempts", 0)) + 1
    rec["evidence"] = evidence or {}
    state["history"].append({
        "node": node_id,
        "status": status,
        "evidence": evidence or {},
    })
    return state


def _cmd_validate(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    mission = _load_json(args.mission)
    validate_mission(mission, registry)
    print(json.dumps({
        "ok": True,
        "mission_id": mission.get("id"),
        "nodes": len(mission["nodes"]),
        "capabilities": sorted({
            node["capability"]
            for node in mission["nodes"]
        }),
    }, indent=2))
    return 0


def _cmd_next(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    mission = _load_json(args.mission)
    validate_mission(mission, registry)
    state = normalize_state(
        mission,
        _load_json(args.state) if args.state else None,
    )
    decision = choose_next(
        mission, registry, state,
        live_jev=not args.no_jev,
    )
    out = decision.to_dict()
    if decision.node_id:
        out["preview"] = preview_node(
            mission, registry, decision.node_id
        )
        if args.execute_readonly and not decision.needs_human:
            try:
                status, evidence = execute_readonly(
                    mission, registry, decision.node_id,
                    timeout=args.timeout,
                )
            except ReflexError as exc:
                out["execution"] = {
                    "status": "REFUSED",
                    "reason": str(exc),
                }
            else:
                mark(
                    mission, state, decision.node_id,
                    status, evidence,
                )
                out["execution"] = {
                    "status": status,
                    "evidence": evidence,
                }
                out["updated_state"] = state
    print(json.dumps(out, indent=2))
    if out.get("execution", {}).get("status") == "FAIL":
        return 1
    return 0 if decision.action in {
        "SELECT", "COMPLETE"
    } else 2


def _cmd_init(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    mission = _load_json(args.mission)
    validate_mission(mission, registry)
    print(json.dumps(initial_state(mission), indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--registry", default=str(DEFAULT_REGISTRY)
    )
    sub = ap.add_subparsers(
        dest="cmd", required=True
    )

    p = sub.add_parser(
        "validate",
        help="validate mission against capability registry",
    )
    p.add_argument("mission")
    p.set_defaults(func=_cmd_validate)

    p = sub.add_parser(
        "init-state",
        help="emit initial mission state JSON",
    )
    p.add_argument("mission")
    p.set_defaults(func=_cmd_init)

    p = sub.add_parser(
        "next",
        help="choose/preview next legal transition",
    )
    p.add_argument("mission")
    p.add_argument("--state")
    p.add_argument("--no-jev", action="store_true")
    p.add_argument(
        "--execute-readonly",
        action="store_true",
        help="execute only registry-approved mutation=none capabilities",
    )
    p.add_argument("--timeout", type=int, default=120)
    p.set_defaults(func=_cmd_next)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
