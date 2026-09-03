#!/usr/bin/env python3
"""Diagnose Melusina Animation Blueprint for T-pose and animation issues via Monolith MCP."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

MONOLITH_URL = "http://127.0.0.1:9316/mcp"
CHAR_BP = "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter"
ABP_SEARCH_TERMS = ["AnimBP", "AnimationBlueprint", "ABP_Melusina"]
SKELETAL_SEARCH_TERM = "SkeletalMesh"
MELUSINA_FILTER = "Melusina"
OUT_PATH = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\anim_diagnostic_report.json")


def monolith_call(tool: str, arguments: dict) -> dict:
    body = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    req = Request(
        MONOLITH_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except (URLError, TimeoutError, json.JSONDecodeError) as e:
        return {"_error": f"Monolith unreachable: {e}"}

    if "error" in data:
        return {"_error": data["error"]}

    result = data.get("result", {})
    if result.get("isError"):
        content = result.get("content", [])
        msg = content[0].get("text", "MCP error") if content else "MCP error"
        return {"_error": msg}

    content = result.get("content", [])
    if content and content[0].get("type") == "text":
        raw = content[0]["text"]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"_raw_text": raw}
    return result


def search_assets(query: str) -> list[dict]:
    result = monolith_call("project_query", {"action": "search", "query": query})
    if "_error" in result:
        return [result]
    if isinstance(result, dict) and result.get("success") and result.get("results"):
        return result["results"]
    if isinstance(result, list):
        return result
    raw = result.get("_raw_text")
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and parsed.get("results"):
                return parsed["results"]
        except json.JSONDecodeError:
            pass
    return [result]


def compile_blueprint(asset_path: str) -> dict:
    return monolith_call("blueprint_query", {"action": "compile_blueprint", "asset_path": asset_path})


def get_inherited_component_override(asset_path: str) -> dict:
    return monolith_call("blueprint_query", {"action": "get_inherited_component_override", "asset_path": asset_path})


def validate_animbp_variable_contract(abp_path: str, bp_path: str) -> dict:
    return monolith_call("blueprint_query", {
        "action": "validate_animbp_variable_contract",
        "abp_asset_path": abp_path,
        "bp_asset_path": bp_path,
    })


def find_abps() -> list[dict]:
    seen = set()
    results = []
    for term in ABP_SEARCH_TERMS:
        assets = search_assets(term)
        for a in assets:
            if not isinstance(a, dict):
                continue
            path = a.get("asset_path", a.get("path", ""))
            if path and path not in seen:
                seen.add(path)
                results.append(a)
    return results


def find_melusina_skeletal_meshes() -> list[dict]:
    assets = search_assets(SKELETAL_SEARCH_TERM)
    return [a for a in assets if isinstance(a, dict) and MELUSINA_FILTER in a.get("asset_path", a.get("path", ""))]


def main() -> int:
    report = {
        "tool": "anim_diagnostic",
        "target_character_bp": CHAR_BP,
        "steps": {},
    }

    report["steps"]["find_animation_blueprints"] = find_abps()

    report["steps"]["find_melusina_skeletal_meshes"] = find_melusina_skeletal_meshes()

    report["steps"]["character_bp_anim_class"] = get_inherited_component_override(CHAR_BP)

    abps_found = report["steps"]["find_animation_blueprints"]
    compile_results = {}
    for abp in abps_found:
        if not isinstance(abp, dict):
            continue
        path = abp.get("asset_path", abp.get("path", ""))
        if path:
            compile_results[path] = compile_blueprint(path)
    report["steps"]["compile_results"] = compile_results

    contract_results = {}
    for abp in abps_found:
        if not isinstance(abp, dict):
            continue
        path = abp.get("asset_path", abp.get("path", ""))
        if path:
            contract_results[path] = validate_animbp_variable_contract(path, CHAR_BP)
    report["steps"]["variable_contract"] = contract_results

    errors = []
    warnings = []
    for path, cr in compile_results.items():
        if "_error" in cr:
            errors.append(f"{path}: compile error - {cr['_error']}")
        elif isinstance(cr, dict):
            status = cr.get("status", cr.get("result", ""))
            err_count = cr.get("error_count", cr.get("errors", 0))
            if err_count:
                errors.append(f"{path}: compile errors ({err_count})")
            if status and "error" in str(status).lower():
                errors.append(f"{path}: compile status - {status}")
    for path, vr in contract_results.items():
        if "_error" in vr:
            errors.append(f"{path}: contract validation failed - {vr['_error']}")
        elif isinstance(vr, dict):
            missing = vr.get("missing_variables", vr.get("missing", []))
            mismatched = vr.get("mismatched_types", vr.get("mismatched", []))
            if missing:
                warnings.append(f"{path}: missing variables - {missing}")
            if mismatched:
                warnings.append(f"{path}: type mismatches - {mismatched}")
    report["summary"] = {"errors": errors, "warnings": warnings, "error_count": len(errors), "warning_count": len(warnings)}

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Report written to {OUT_PATH}")
    print(json.dumps(report["summary"], indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
