"""GMM-facing PCG validation and release-gate orchestration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gmm.core import GmmAudit
from gmm.pcg.manifest import manifest_summary



def validate_manifest_file(path: str | Path, *, for_apply: bool = False) -> dict:
    manifest_path = Path(path).expanduser().resolve()
    if not manifest_path.is_file():
        return {"ok": False, "path": str(manifest_path), "errors": ["manifest file does not exist"]}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "path": str(manifest_path), "errors": [f"JSON load failed: {exc}"]}
    return {"path": str(manifest_path), **manifest_summary(data, require_resolved_meshes=for_apply)}


def _result_ok(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if "ok" in value:
        return bool(value["ok"])
    if "passed" in value:
        return bool(value["passed"])
    if "clean" in value:
        return bool(value["clean"])
    summary = value.get("summary")
    if isinstance(summary, dict):
        return bool(summary.get("passed", summary.get("ok", False)))
    return False


def preflight(*, include_pillars: bool = True) -> dict:
    """Run non-mutating PCG checks inside Unreal and emit one truthful envelope."""
    audit = GmmAudit(action="pcg.preflight")
    checks: dict[str, dict] = {}
    try:
        import unreal  # noqa: F401
    except ImportError:
        audit.fail("PCG preflight must run inside Unreal Editor")
        audit.ok(runtime="outside_unreal", checks=checks, all_ok=False)
        audit.status = "error"
        audit.save("gmm_pcg_preflight.json")
        return audit.to_dict()

    try:
        import audit_pcg_portfolio
        result = audit_pcg_portfolio._audit_in_ue()
        checks["portfolio"] = {"ok": _result_ok(result), "result": result}
    except Exception as exc:
        checks["portfolio"] = {"ok": False, "error": str(exc)}

    if include_pillars:
        try:
            import setup_wp_pillar_levels as wp
            pillars = {key: wp.verify(key, save_report=False) for key in wp.PILLARS}
            checks["wp_pillars"] = {
                "ok": bool(pillars) and all(_result_ok(result) for result in pillars.values()),
                "result": pillars,
            }
        except Exception as exc:
            checks["wp_pillars"] = {"ok": False, "error": str(exc)}

    all_ok = bool(checks) and all(check.get("ok", False) for check in checks.values())
    if all_ok:
        audit.ok(checks=checks, all_ok=True)
    else:
        audit.fail("One or more PCG preflight checks failed")
        audit.data.update(checks=checks, all_ok=False)
    audit.save("gmm_pcg_preflight.json")
    return audit.to_dict()


def repair_quarantined_references(*, save: bool = True) -> dict:
    """Replace quarantined shipping graph references without generating them."""
    audit = GmmAudit(action="pcg.repair_quarantined_references")
    try:
        import unreal
        import pcg_graph_builder as graph_builder
        import pcg_portfolio_standards as standards
    except ImportError as exc:
        audit.fail(f"Quarantine repair must run inside Unreal Editor: {exc}")
        audit.save("gmm_pcg_quarantine_repair.json")
        return audit.to_dict()

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_editor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    replacements: list[dict] = []
    errors: list[str] = []
    for level_path in standards.SHIPPING_LEVELS:
        try:
            level_editor.load_level(level_path)
            try:
                wp = unreal.WorldPartitionBlueprintLibrary
                wp.load_actors([descriptor.guid for descriptor in wp.get_actor_descs()])
            except Exception:
                pass
            level_changed = False
            for actor in actor_editor.get_all_level_actors() or []:
                component = actor.get_component_by_class(unreal.PCGComponent)
                if not component:
                    continue
                current = graph_builder.graph_package_path(component)
                replacement = standards.QUARANTINE_REPLACEMENTS.get(current)
                if not replacement:
                    continue
                graph = unreal.EditorAssetLibrary.load_asset(replacement)
                if not graph:
                    errors.append(f"{level_path}: replacement missing: {replacement}")
                    continue
                graph_builder.assign_pcg_graph(component, graph)
                replacements.append({
                    "level": level_path,
                    "actor": actor.get_actor_label(),
                    "from": current,
                    "to": replacement,
                })
                level_changed = True
            if save and level_changed:
                level_editor.save_current_level()
        except Exception as exc:
            errors.append(f"{level_path}: {exc}")

    if errors:
        audit.fail("One or more quarantine references could not be repaired")
        audit.data.update(replacements=replacements, errors=errors, generated=False)
    else:
        audit.ok(replacements=replacements, replacement_count=len(replacements), generated=False)
    audit.save("gmm_pcg_quarantine_repair.json")
    return audit.to_dict()


def release_gate(manifest_path: str | Path | None = None) -> dict:
    """Require PCG health and, when supplied, an apply-ready world manifest."""
    preflight_report = preflight(include_pillars=True)
    checks: dict[str, dict] = {
        "pcg_preflight": {
            "ok": preflight_report.get("status") == "ok" and bool(preflight_report.get("data", {}).get("all_ok")),
            "result": preflight_report,
        }
    }
    if manifest_path:
        checks["world_manifest"] = validate_manifest_file(manifest_path, for_apply=True)
    else:
        checks["world_manifest"] = {
            "ok": False,
            "errors": ["An apply-ready world manifest is required for the release gate"],
        }
    all_ok = all(check.get("ok", False) for check in checks.values())
    audit = GmmAudit(action="pcg.release_gate")
    if all_ok:
        audit.ok(checks=checks, all_ok=True)
    else:
        audit.fail("PCG release gate failed")
        audit.data.update(checks=checks, all_ok=False)
    audit.save("gmm_pcg_release_gate.json")
    return audit.to_dict()
