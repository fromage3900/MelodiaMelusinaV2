#!/usr/bin/env python3
"""Internal H1 task-packet routing helpers.

This module is not a second router. Tools/model_router.py remains the public
routing authority and calls these helpers for its `route` subcommand.
"""

from __future__ import annotations

import fnmatch
import json
import os
from typing import Any

TIER_ORDER = ("T0_ARCHITECT", "T1_VERIFIER", "T2_EXECUTOR", "T3_BULK", "T4_LOCAL")

LANES = {
    "code": "Bounded Python/tool/test implementation under an existing contract.",
    "cpp": "C++/Unreal source implementation under an existing architecture.",
    "mcp": "MCP/client/tool integration; editor use is separately lease-gated.",
    "docs": "Documentation prose, indexes, references, and link repair.",
    "audit": "Read-only audit, log triage, manifests, and verification support.",
    "review": "Independent artifact verification; never the artifact producer.",
    "vision": "Screenshot/render/visual evidence review.",
    "author": "Narrative/dialogue/Quill authored-content drafting.",
    "orchestrator": "Architecture/convergence/routing decisions.",
    "daemon": "Local/free unattended analysis or draft generation.",
    "playtest": "Runtime/playtest verification and evidence review.",
    "triage": "Fast bounded classification of logs, failures, or queue items.",
}

VERIFY_KINDS = {
    "artifact_open": "Open and inspect the named artifact.",
    "test_log": "Read the actual test/build/lint log.",
    "image_look": "Inspect an image/render/capture as evidence.",
    "diff_review": "Inspect the patch/diff for scope and invariants.",
    "log_cite": "Inspect and cite the relevant runtime/log lines.",
}


def validate_packet(packet: dict[str, Any]) -> None:
    required = ("id", "goal", "done_when", "mutation_scope", "budget_usd", "max_turns")
    missing = [k for k in required if k not in packet]
    if missing:
        raise ValueError("task packet missing required field(s): " + ", ".join(missing))
    if not isinstance(packet.get("goal"), str) or not packet["goal"].strip():
        raise ValueError("task packet goal must be a non-empty string")
    if packet.get("mutation_scope") not in {"none", "files", "editor", "git"}:
        raise ValueError("mutation_scope must be none|files|editor|git")
    if not isinstance(packet.get("done_when"), list) or not packet["done_when"]:
        raise ValueError("done_when must be a non-empty list")
    if float(packet.get("budget_usd", -1)) < 0:
        raise ValueError("budget_usd must be >= 0")
    if int(packet.get("max_turns", 0)) < 1:
        raise ValueError("max_turns must be >= 1")


def _text(packet: dict[str, Any]) -> str:
    parts = [
        packet.get("goal", ""),
        " ".join(str(x) for x in packet.get("surfaces", [])),
        " ".join(str(x) for x in packet.get("may_write", [])),
        " ".join(str(x) for x in packet.get("must_not", [])),
        " ".join(str(x) for x in packet.get("done_when", [])),
    ]
    return " ".join(parts).lower()


def classical_task_class(packet: dict[str, Any]) -> str:
    text = _text(packet)
    paths = [str(x).replace("\\", "/").lower() for x in packet.get("may_write", [])]
    if packet.get("mutation_scope") == "git" or any(
        k in text for k in ("branch strategy", "merge operation", "rebase operation", "architecture", "new subsystem")
    ):
        return "orchestrator"
    if paths and all(p.endswith(".md") or p.startswith("docs/") for p in paths):
        return "docs"
    if any(p.endswith((".cpp", ".h", ".hpp", ".build.cs")) or p.startswith("source/") for p in paths):
        return "cpp"
    if any(k in text for k in ("verify", "prove", "falsif", "independent review", "certif")):
        return "review"
    if any(k in text for k in ("render", "screenshot", "image", "visual", "beauty frame")):
        return "vision"
    if any(k in text for k in ("log triage", "audit", "manifest", "inventory", "census")):
        return "audit"
    if any(k in text for k in ("dialogue", "narrative", "quill", "story", "author")):
        return "author"
    if any(k in text for k in ("mcp", "blueprint", "unreal editor", "monolith", "claireon")):
        return "mcp"
    if any(k in text for k in ("overnight", "daemon", "unattended")):
        return "daemon"
    if any(k in text for k in ("playtest", "pie capture", "runtime capture")):
        return "playtest"
    if "triage" in text:
        return "triage"
    return "code"


def classical_verify_kind(packet: dict[str, Any]) -> str:
    text = _text(packet)
    if any(k in text for k in ("render", "screenshot", "image", "visual", "beauty frame")):
        return "image_look"
    if any(k in text for k in ("runtime log", "log line", "log triage")):
        return "log_cite"
    if any(k in text for k in ("test", "pytest", "unittest", "compile", "lint", "build")):
        return "test_log"
    if packet.get("mutation_scope") in {"files", "git"}:
        return "diff_review"
    return "artifact_open"


def policy_needs_editor(packet: dict[str, Any]) -> bool:
    if packet.get("mutation_scope") == "editor":
        return True
    surfaces = {str(x).strip().lower() for x in packet.get("surfaces", [])}
    if surfaces & {"editor", "ue", "unreal", "unreal_editor", "monolith", "claireon"}:
        return True
    for raw in packet.get("may_write", []):
        p = str(raw).replace("\\", "/").lower()
        if p.endswith(".uasset") or p.endswith(".umap"):
            return True
    return False


def _match(path: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(path.replace("\\", "/").lower(), pattern.replace("\\", "/").lower())


def enforced_tier(packet: dict[str, Any], task_class: str, spec: dict[str, Any]) -> tuple[str, list[str]]:
    default = "T2_EXECUTOR"
    for tier in spec.get("tiers", []):
        if task_class in (tier.get("default_classes") or []):
            default = tier.get("id", default)
            break

    candidates = [default]
    matched: list[str] = []
    goal = str(packet.get("goal", "")).lower()
    paths = [str(x).replace("\\", "/") for x in packet.get("may_write", [])]

    for trigger in spec.get("escalation_triggers", []):
        path_hit = any(
            _match(path, pattern)
            for path in paths
            for pattern in (trigger.get("path_globs") or [])
        )
        keyword_hit = any(
            str(keyword).lower() in goal
            for keyword in (trigger.get("goal_keywords") or [])
        )
        if path_hit or keyword_hit:
            candidates.append(trigger.get("required_tier", default))
            matched.append(str(trigger.get("id")))

    if packet.get("mutation_scope") == "editor":
        candidates.append("T1_VERIFIER")
        matched.append("editor_mutation")
    if packet.get("mutation_scope") == "git":
        candidates.append("T0_ARCHITECT")
        matched.append("vcs_operation")

    rank = {tier_id: i for i, tier_id in enumerate(TIER_ORDER)}
    tier = min(candidates, key=lambda t: rank.get(t, 999))
    return tier, sorted(set(matched))


def try_jev(packet: dict[str, Any], policy: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        return None, "TYPESAFE_API_KEY missing"
    try:
        from typesafe_sdk import TypeSafeClient  # type: ignore
    except Exception as exc:
        return None, "typesafe_sdk unavailable: %r" % (exc,)

    lane_criteria = {k: v for k, v in LANES.items() if k in policy}
    state = {
        "task_id": packet.get("id"),
        "goal": packet.get("goal"),
        "surfaces": packet.get("surfaces", []),
        "may_write": packet.get("may_write", []),
        "must_not": packet.get("must_not", []),
        "mutation_scope": packet.get("mutation_scope"),
        "done_when": packet.get("done_when", []),
        "budget_usd": packet.get("budget_usd"),
        "max_turns": packet.get("max_turns"),
    }
    try:
        with TypeSafeClient(api_key=key) as client:
            response = client.system_one(
                state=state,
                questions={
                    "lane": {
                        "type": "choice",
                        "instructions": "Choose one existing Melodia model-router task class. Do not invent a new lane.",
                        "criteria": lane_criteria,
                    },
                    "needs_editor": {
                        "type": "choice",
                        "instructions": "Choose YES only if execution requires live editor mutation.",
                        "criteria": {
                            "NO": "Repository/files/shell work only.",
                            "YES": "Requires a live editor mutation surface and therefore a lease.",
                        },
                    },
                    "verify_kind": {
                        "type": "choice",
                        "instructions": "Choose the evidence-review method that can falsify completion.",
                        "criteria": VERIFY_KINDS,
                    },
                },
            )
        answers = response.answers
        lane = answers["lane"].choice
        verify_kind = answers["verify_kind"].choice
        if lane not in lane_criteria or verify_kind not in VERIFY_KINDS:
            return None, "Jev returned a value outside the closed option set"
        return {
            "task_class": lane,
            "jev_needs_editor": answers["needs_editor"].choice == "YES",
            "verify_kind": verify_kind,
            "model": getattr(response, "model", None),
        }, None
    except Exception as exc:
        return None, "Jev call failed: %r" % (exc,)


def route_packet(
    packet: dict[str, Any],
    *,
    policy: dict[str, Any],
    tier_spec: dict[str, Any],
    allow_jev: bool = True,
) -> dict[str, Any]:
    validate_packet(packet)
    fallback_class = classical_task_class(packet)
    fallback_verify = classical_verify_kind(packet)
    policy_editor = policy_needs_editor(packet)

    live = None
    live_error = None
    if allow_jev:
        live, live_error = try_jev(packet, policy)

    source = "jev-live" if live else "classical-fallback"
    task_class = live["task_class"] if live else fallback_class
    verify_kind = live["verify_kind"] if live else fallback_verify
    needs_editor = policy_editor or bool(live and live.get("jev_needs_editor"))
    tier, triggers = enforced_tier(packet, task_class, tier_spec)

    auto_dispatch = (
        source == "jev-live"
        and not needs_editor
        and packet.get("mutation_scope") != "git"
        and tier != "T0_ARCHITECT"
    )
    return {
        "schema": "melodia.route_decision/v1",
        "task_id": packet.get("id"),
        "task_class": task_class,
        "tier": tier,
        "needs_editor": needs_editor,
        "verify_kind": verify_kind,
        "source": source,
        "model": live.get("model") if live else None,
        "auto_dispatch": auto_dispatch,
        "matched_escalation_triggers": triggers,
        "fallback_task_class": fallback_class,
        "fallback_verify_kind": fallback_verify,
        "reason": (
            "Jev System One selected closed-set routing; checked-in policy enforced."
            if live
            else "Deterministic fallback only; owner review required before dispatch. " + (live_error or "Jev disabled")
        ),
    }


def load_packet(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
