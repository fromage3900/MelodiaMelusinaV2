#!/usr/bin/env python3
"""Validate the Melodia model tier registry as a routing contract, not a suggestion.

Checks the registry against `Tools/model_router.py` (the only live routing authority) so
tier policy cannot silently drift away from the model policy it describes. Read-only:
this never dispatches a call and never writes a ledger row.

Run from the repository root:
    python Tools/validate_model_tiers.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "specs" / "orchestration" / "model_tiers.v1.json"
ROUTER = ROOT / "Tools" / "model_router.py"

TIER_ORDER = ("T0_ARCHITECT", "T1_VERIFIER", "T2_EXECUTOR", "T3_BULK", "T4_LOCAL")
VERIFY_KINDS = {"artifact_open", "test_log", "image_look", "diff_review", "log_cite", "none"}
REQUIRED_TIER_KEYS = {
    "id", "label", "intent", "cost_profile", "default_classes", "may_write",
    "must_not", "context_policy", "evidence", "budget_usd_default", "budget_usd_max", "handoff",
}
# Tiers that may never hold a Source/** write fence.
NO_SOURCE_TIERS = {"T0_ARCHITECT", "T1_VERIFIER", "T3_BULK", "T4_LOCAL"}
# Owner-sign-off surfaces that no tier below the frontier architect may write.
OWNER_SIGNOFF_GLOBS = ("Config/**", "BS_GodFile.uproject", ".gitignore", ".gitattributes")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _router_module():
    spec = importlib.util.spec_from_file_location("melodia_model_router", ROUTER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _glob_covers(pattern: str, path: str) -> bool:
    """Minimal ** glob matcher - stdlib only, explicit about cross-segment intent."""
    pattern = pattern.replace("\\", "/")
    path = path.replace("\\", "/")
    if pattern.endswith("/**"):
        return path == pattern[:-3] or path.startswith(pattern[:-2])
    if pattern.startswith("**/"):
        return path.endswith(pattern[2:]) or f"/{pattern[3:]}" in f"/{path}"
    if "**" in pattern:
        head, _, tail = pattern.partition("**")
        return path.startswith(head) and path.endswith(tail.lstrip("/"))
    if "*" in pattern:
        prefix, _, suffix = pattern.partition("*")
        return path.startswith(prefix) and path.endswith(suffix)
    return path == pattern


def validate(registry: dict, router, check_files: bool = True) -> list[str]:
    errors: list[str] = []
    if registry.get("schema") != "melodia.model_tiers/v1":
        errors.append("unexpected registry schema")

    authority = registry.get("authority") or {}
    if authority.get("live_routing") != "Tools/model_router.py":
        errors.append("registry must declare Tools/model_router.py as the live routing authority")
    for key in ("task_class_policy", "routing_canon", "orchestration_plan", "current_status"):
        if not authority.get(key):
            errors.append(f"registry authority is missing {key}")
    if check_files:
        for value in authority.values():
            # Only bare paths are checked; prose values (e.g. "Tools/echo_run.py (gate ledger)") are skipped.
            if isinstance(value, str) and "/" in value and " " not in value and not (ROOT / value).exists():
                errors.append(f"authority reference missing on disk: {value}")

    rules = registry.get("rules") or {}
    for required in ("deterministic", "extend_not_replace", "no_self_certification", "widest_tier_wins"):
        if not rules.get(required):
            errors.append(f"registry rules must state {required}")

    kinds = registry.get("verification_kinds")
    if not isinstance(kinds, list) or not kinds:
        errors.append("verification_kinds must be a non-empty list")

    triggers = registry.get("escalation_triggers")
    if not isinstance(triggers, list) or not triggers:
        errors.append("escalation_triggers must be a non-empty list")
        triggers = []
    trigger_ids: set[str] = set()
    for trigger in triggers:
        tid = trigger.get("id")
        if not isinstance(tid, str) or not tid or tid in trigger_ids:
            errors.append(f"invalid or duplicate escalation trigger id: {tid!r}")
            continue
        trigger_ids.add(tid)
        if trigger.get("required_tier") not in TIER_ORDER:
            errors.append(f"{tid}: invalid required_tier {trigger.get('required_tier')!r}")
        if not trigger.get("why"):
            errors.append(f"{tid}: escalation trigger must state why")
        if not (trigger.get("path_globs") or trigger.get("goal_keywords")):
            errors.append(f"{tid}: escalation trigger must match a path glob or a goal keyword")

    cheap = registry.get("cheap_tier_eligible")
    if not isinstance(cheap, list) or not cheap:
        errors.append("cheap_tier_eligible must be a non-empty list")
        cheap = []
    for entry in cheap:
        if not entry.get("why"):
            errors.append(f"cheap_tier_eligible {entry.get('id')!r}: must state why")
        if not entry.get("globs"):
            errors.append(f"cheap_tier_eligible {entry.get('id')!r}: must declare globs")

    tiers = registry.get("tiers")
    if not isinstance(tiers, list) or [t.get("id") for t in tiers if isinstance(t, dict)] != list(TIER_ORDER):
        errors.append("tiers must be exactly, in order: " + ", ".join(TIER_ORDER))
        tiers = tiers if isinstance(tiers, list) else []

    policy_classes = set(router.POLICY)
    claimed: dict[str, str] = {}
    for tier in tiers:
        if not isinstance(tier, dict):
            errors.append("tier entry must be an object")
            continue
        tid = tier.get("id")
        missing = REQUIRED_TIER_KEYS - set(tier)
        if missing:
            errors.append(f"{tid}: tier is missing keys {sorted(missing)}")
        evidence = tier.get("evidence") or {}
        if evidence.get("verify_kind") not in VERIFY_KINDS:
            errors.append(f"{tid}: invalid verify_kind {evidence.get('verify_kind')!r}")
        if not evidence.get("verified_by"):
            errors.append(f"{tid}: evidence must name who verifies")
        for cls in tier.get("default_classes", []):
            if cls not in policy_classes:
                errors.append(f"{tid}: unknown router class {cls!r}")
            elif cls in claimed:
                errors.append(f"{cls}: claimed by both {claimed[cls]} and {tid}")
            else:
                claimed[cls] = tid
        if not isinstance(tier.get("budget_usd_max"), (int, float)):
            errors.append(f"{tid}: budget_usd_max must be numeric")
        if not tier.get("must_not"):
            errors.append(f"{tid}: must_not cannot be empty")
        context = tier.get("context_policy") or {}
        if not context.get("include") or not isinstance(context.get("max_tokens"), int):
            errors.append(f"{tid}: context_policy needs include and an integer max_tokens")
        if tid in NO_SOURCE_TIERS and any(g.startswith("Source/") for g in tier.get("may_write", [])):
            errors.append(f"{tid}: must not hold a Source/** write fence")
        if tid != "T0_ARCHITECT":
            for glob in tier.get("may_write", []):
                for protected in OWNER_SIGNOFF_GLOBS:
                    if glob == protected or _glob_covers(glob, protected):
                        errors.append(f"{tid}: may_write {glob!r} crosses owner-sign-off surface {protected}")
        if tid == "T4_LOCAL" and tier.get("budget_usd_max") != 0:
            errors.append("T4_LOCAL: budget_usd_max must be 0 (local lanes never bill)")

    for cls in sorted(policy_classes - set(claimed)):
        errors.append(f"router class {cls!r} is not claimed by any tier")

    # A local-only router class must never be routed to a cloud-capable tier.
    for cls in sorted(router.LOCAL_ONLY_CLASSES & policy_classes):
        tier_id = claimed.get(cls)
        if tier_id in (None, "T0_ARCHITECT", "T1_VERIFIER", "T2_EXECUTOR", "T3_BULK"):
            errors.append(f"local-only class {cls!r} must be claimed by T4_LOCAL, found {tier_id!r}")

    return errors


def main() -> int:
    registry = _load(REGISTRY)
    router = _router_module()
    errors = validate(registry, router, check_files=True)
    if errors:
        print("FAIL: model tier contract")
        for error in errors:
            print(f"  - {error}")
        return 1
    total_classes = len({c for t in registry["tiers"] for c in t["default_classes"]})
    print(
        f"PASS: model tier contract ({len(registry['tiers'])} tiers, {total_classes} router classes, "
        f"{len(registry['escalation_triggers'])} escalation triggers, "
        f"{len(registry['cheap_tier_eligible'])} bulk-eligible shapes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
