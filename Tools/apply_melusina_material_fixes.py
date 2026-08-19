"""
Apply fixes to SK_Melusina material instances based on live audit findings.
Connects to Monolith MCP at http://127.0.0.1:9316/mcp.
"""
import json, sys, urllib.request
from pathlib import Path

MONOLITH_URL = "http://127.0.0.1:9316/mcp"

def monolith(tool, action, params=None):
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": {"action": action, **(params or {})}}
    }).encode()
    req = urllib.request.Request(MONOLITH_URL, body, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"isError": True, "error": str(e)}
    if data.get("error"):
        return {"isError": True, "error": data["error"]}
    result = data.get("result", {})
    if result.get("isError"):
        return {"isError": True, "error": result.get("content", [{}])[0].get("text", "Unknown")}
    content = result.get("content", [])
    if content:
        try:
            return json.loads(content[0]["text"])
        except:
            return {"raw": content[0]["text"]}
    return {}

def report(msg):
    print(f"  {msg}")

print("=" * 60)
print("SK_Melusina Material Fix Application")
print("=" * 60)

# ── Step 1: Set bUseSeparateRoughnessMap=True and bUseSeparateMetallicMap=True ──
# Based on audit, MI_Melusina_GLOVES_001 has both False (not overridden)
# Parent material defaults are False, so inheriting instances also need fixing

FIX_SWITCHES = [
    {
        "mi": "MI_Melusina_GLOVES_001",
        "path": "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_GLOVES_001",
        "reason": "bUseSeparateRoughnessMap=False, bUseSeparateMetallicMap=False (inherited parent default)",
    },
    {
        "mi": "MI_Melusina_Material_023",
        "path": "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_023",
        "reason": "bUseSeparateRoughnessMap=True, bUseSeparateMetallicMap=True already — verifying",
        "verify_only": True,
    },
]

print("\n[1/3] Fixing static switch overrides...")
fix_results = []
for entry in FIX_SWITCHES:
    mi_name = entry["mi"]
    path = entry["path"]
    reason = entry["reason"]
    verify_only = entry.get("verify_only", False)

    report(f"Checking {mi_name}...")

    if verify_only:
        data = monolith("material_query", "get_instance_parameters", {"asset_path": path})
        switches = {s["name"]: s for s in data.get("static_switch", [])}
        rough = switches.get("bUseSeparateRoughnessMap", {})
        metal = switches.get("bUseSeparateMetallicMap", {})
        rough_ok = rough.get("is_overridden", False) and rough.get("value", False)
        metal_ok = metal.get("is_overridden", False) and metal.get("value", False)
        if rough_ok and metal_ok:
            report(f"  OK — both switches already True and overridden")
            fix_results.append({mi_name: {"status": "already_ok", "detail": "Switches already set correctly"}})
        else:
            report(f"  WARN — expected both True, got Roughness={rough.get('value')}(overridden={rough.get('is_overridden')}), Metallic={metal.get('value')}(overridden={metal.get('is_overridden')})")
            fix_results.append({mi_name: {"status": "unexpected", "detail": "Switches not as expected"}})
        continue

    # Fix: batch-set both switches
    params = {"asset_path": path, "parameters": [
        {"name": "bUseSeparateRoughnessMap", "type": "switch", "value": True},
        {"name": "bUseSeparateMetallicMap", "type": "switch", "value": True},
    ]}
    result = monolith("material_query", "set_instance_parameters", params)
    if result.get("isError"):
        report(f"  FAILED: {result.get('error')}")
        fix_results.append({mi_name: {"status": "error", "error": result.get("error")}})
    else:
        report(f"  Set bUseSeparateRoughnessMap=True, bUseSeparateMetallicMap=True")

        # Recompile
        comp = monolith("material_query", "recompile_material", {"asset_path": path, "include_stats": True})
        if comp.get("isError"):
            report(f"  Recompile FAILED: {comp.get('error')}")
            fix_results.append({mi_name: {"status": "compiled_error", "error": comp.get("error")}})
        else:
            report(f"  Recompile OK")
            fix_results.append({mi_name: {"status": "fixed_and_compiled"}})

# ── Step 2: Fix frontpanel_001 broken texture references ──
print("\n[2/3] Fixing broken texture references on MI_Melusina_frontpanel_001...")
fp_path = "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_frontpanel_001"
fp_params = {"asset_path": fp_path, "parameters": [
    {"name": "Albedo", "type": "texture", "value": "/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_frontpanel_BaseColor.T_MelusinaC_frontpanel_BaseColor"},
    {"name": "NormalMap", "type": "texture", "value": "/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_frontpanel_Normal.T_MelusinaC_frontpanel_Normal"},
    {"name": "RoughnessMap", "type": "texture", "value": "/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_frontpanel_Roughness.T_MelusinaC_frontpanel_Roughness"},
    {"name": "MetallicMap", "type": "texture", "value": "/Game/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_frontpanel_Metallic.T_MelusinaC_frontpanel_Metallic"},
]}
result = monolith("material_query", "set_instance_parameters", fp_params)
if result.get("isError"):
    report(f"  FAILED: {result.get('error')}")
    fp_fix = {"MI_Melusina_frontpanel_001": {"status": "error", "error": result.get("error")}}
else:
    report(f"  Set 4 texture overrides to T_MelusinaC_frontpanel_* paths")
    comp = monolith("material_query", "recompile_material", {"asset_path": fp_path, "include_stats": True})
    if comp.get("isError"):
        report(f"  Recompile FAILED: {comp.get('error')}")
        fp_fix = {"MI_Melusina_frontpanel_001": {"status": "compiled_error", "error": comp.get("error")}}
    else:
        report(f"  Recompile OK")
        fp_fix = {"MI_Melusina_frontpanel_001": {"status": "fixed_and_compiled"}}

# ── Step 3: Set bUseSeparateRoughnessMap/MetallicMap=True on all clothing/body MIs that don't have it ──
print("\n[3/3] Auditing and fixing remaining clothing/body MIs...")
# Query all instances to check
CLOTHING_MIS = [
    "MI_Melusina_SBW_MELUSINA_006",
    "MI_Melusina_SBW_MELUSINA_007",
    "MI_Melusina_sleeve_003",
    "MI_Melusina_Material_013",
    "MI_Melusina_bow_002",
    "MI_Melusina_skirtpanel_002",
    "MI_Melusina_SHAWL_001",
    "MI_Melusina_Material_017",
    "MI_Melusina_SKIRT_003",
    "MI_Melusina_Material_023",
]

additional_fixes = []
for mi_name in CLOTHING_MIS:
    path = f"/Game/Melodia/Characters/Melusina/Materials/{mi_name}"
    data = monolith("material_query", "get_instance_parameters", {"asset_path": path})
    if data.get("isError"):
        report(f"  {mi_name}: SKIP — could not query ({data.get('error')})")
        continue
    switches = {s["name"]: s for s in data.get("static_switch", [])}
    rough = switches.get("bUseSeparateRoughnessMap", {})
    metal = switches.get("bUseSeparateMetallicMap", {})
    rough_ok = rough.get("is_overridden", False) and rough.get("value", False)
    metal_ok = metal.get("is_overridden", False) and metal.get("value", False)

    params_to_set = []
    if not rough_ok:
        params_to_set.append({"name": "bUseSeparateRoughnessMap", "type": "switch", "value": True})
    if not metal_ok:
        params_to_set.append({"name": "bUseSeparateMetallicMap", "type": "switch", "value": True})

    if params_to_set:
        report(f"  {mi_name}: setting {[p['name'] for p in params_to_set]}")
        result = monolith("material_query", "set_instance_parameters", {
            "asset_path": path, "parameters": params_to_set
        })
        if result.get("isError"):
            report(f"    FAILED: {result.get('error')}")
            additional_fixes.append({mi_name: {"status": "error", "error": result.get("error")}})
        else:
            comp = monolith("material_query", "recompile_material", {"asset_path": path, "include_stats": True})
            if comp.get("isError"):
                report(f"    Recompile FAILED: {comp.get('error')}")
                additional_fixes.append({mi_name: {"status": "compiled_error", "error": comp.get("error")}})
            else:
                report(f"    Recompile OK")
                additional_fixes.append({mi_name: {"status": "fixed_and_compiled"}})
    else:
        report(f"  {mi_name}: OK — both switches already correct")

# ── Summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("FIX APPLICATION SUMMARY")
print("=" * 60)
all_fixes = fix_results + [fp_fix] + additional_fixes

fixed = sum(1 for f in all_fixes if any(v.get("status") == "fixed_and_compiled" for v in f.values()))
errors = sum(1 for f in all_fixes if any("error" in v.get("status", "") for v in f.values()))
already = sum(1 for f in all_fixes if any(v.get("status") == "already_ok" for v in f.values()))

print(f"  Fixed and compiled: {fixed}")
print(f"  Already correct: {already}")
print(f"  Errors: {errors}")

for entry in all_fixes:
    for name, detail in entry.items():
        status = detail.get("status", "unknown")
        err = detail.get("error", "")
        print(f"  [{status.upper()}] {name}" + (f" — {err}" if err else ""))

print()
print("Done.")
