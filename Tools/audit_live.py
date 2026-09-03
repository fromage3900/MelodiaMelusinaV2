"""
Live material audit script for SK_Melusina - Substrate Toon compliance.
Connects to Monolith MCP at http://127.0.0.1:9316/mcp and Unreal Editor.
"""
import json, os, sys, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime
from collections import OrderedDict

PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")
MONOLITH_URL = "http://127.0.0.1:9316/mcp"

# ── Helpers ──────────────────────────────────────────────────────────────
def monolith(tool, action, params=None):
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool,
            "arguments": {"action": action, **(params or {})}
        }
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
        return json.loads(content[0]["text"])
    return {}

# ── Step 1: Get SK_Melusina material slots ──────────────────────────────
print("=== Querying SK_Melusina material slots ===")
script = """import unreal
mesh = unreal.load_asset('/Game/Melodia/Characters/Melusina/SK_Melusina')
if mesh:
    for i, mat in enumerate(mesh.materials):
        mi = mat.material_interface
        mi_path = mi.get_path_name() if mi else 'None'
        slot_name = str(mat.material_slot_name)
        print(f'SLOT|{i}|{slot_name}|{mi_path}')
else:
    print('ERROR: Could not load SK_Melusina')
"""
result = monolith("editor_query", "run_python", {"command": script})
if result.get("isError"):
    print(f"ERROR: {result.get('error')}")
    sys.exit(1)
output = result.get("output", [])
live_slots = {}
for entry in output:
    line = entry.get("output", "")
    if line.startswith("SLOT|"):
        parts = line.strip().split("|")
        idx = int(parts[1])
        slot_name = parts[2]
        mi_path = parts[3]
        mi_name = mi_path.split("/")[-1].split(".")[0] if mi_path != "None" else "NONE"
        parent_name = mi_path.split("/")[-1].split(".")[0] if mi_path != "None" else "None"
        live_slots[idx] = {
            "slot_name": slot_name,
            "mi_path": mi_path,
            "mi_name": mi_name,
            "parent_name": parent_name,
        }

print(f"Found {len(live_slots)} slots")

# ── Step 2: Get parameters for each unique MI ──────────────────────────
unique_mis = OrderedDict()
for idx, slot in sorted(live_slots.items()):
    mi_name = slot["mi_name"]
    if mi_name == "NONE" or mi_name == "None":
        continue
    if mi_name not in unique_mis:
        unique_mis[mi_name] = slot["mi_path"]

print(f"Querying {len(unique_mis)} unique MIs...")
mi_params = {}
for mi_name, mi_path in unique_mis.items():
    print(f"  Querying {mi_name}...")
    asset_path = mi_path.split(".")[0]
    data = monolith("material_query", "get_instance_parameters", {"asset_path": asset_path})
    if data.get("isError"):
        mi_params[mi_name] = {"error": data.get("error")}
    else:
        mi_params[mi_name] = data

# Water hair
print("  Querying MI_Melusina_WaterHair...")
water_hair_data = monolith("material_query", "get_instance_parameters", {
    "asset_path": "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair"
})
if water_hair_data.get("isError"):
    mi_params["MI_Melusina_WaterHair"] = {"error": water_hair_data.get("error")}
else:
    mi_params["MI_Melusina_WaterHair"] = water_hair_data

# ── Step 3: Get parent material parameters ──────────────────────────────
print("  Querying M_Master_Toon_Universal parameters...")
master_params = monolith("material_query", "get_material_parameters", {
    "asset_path": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
})
master_props = monolith("material_query", "get_material_properties", {
    "asset_path": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
})

# ── Step 4: Build report ────────────────────────────────────────────────
KNOWN_PARENT_MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal"
TOON_PROFILE = "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina"

def classify_slot(slot_idx, mi_name):
    if mi_name in ("NONE", "None"):
        return "unassigned"
    ml = mi_name.lower()
    if "outline" in ml: return "outline"
    if "halftone" in ml: return "halftone"
    if "gradient" in ml: return "gradient"
    if "metal" in ml or "matcap" in ml: return "metal_matcap"
    if "iris" in ml: return "eye"
    if "bow" in ml: return "accessory"
    if "skin" in ml or "body" in ml: return "body"
    if "shirt" in ml or "material_024" in ml: return "clothing"
    if "skirt" in ml: return "clothing"
    if "sleeve" in ml: return "clothing"
    if "shawl" in ml: return "clothing"
    if "frontpanel" in ml: return "clothing"
    if "glove" in ml: return "clothing"
    if "belt" in ml: return "accessory"
    if "bloomer" in ml: return "clothing"
    if "sbw" in ml: return "body"
    if "boot" in ml: return "clothing"
    if "iridescence" in ml: return "effect"
    return "clothing"

KNOWN_ROLES = [
    ("Gradient", "gradient/halftone effect"),
    ("SBW_MELUSINA_006", "body main"),
    ("SBW_MELUSINA_007", "body main"),
    ("sleeve", "sleeve"),
    ("Outline", "outline shader"),
    ("Metal", "metal matcap accent"),
    ("Material_023", "celestial/space effect (catch-all)"),
    ("Material_013", "body/clothing"),
    ("Bow", "bow accessory"),
    ("skirtpanel", "skirt front panel"),
    ("SHAWL", "shawl/shoulder wrap"),
    ("frontpanel", "front panel (bodice)"),
    ("GLOVES", "gloves"),
    ("Material_017", "boots"),
    ("SKIRT", "skirt main"),
    ("Halftone", "halftone pattern overlay"),
    ("Material_021", "body/clothing"),
    ("Material_022", "body/clothing"),
    ("Material_024", "shirt"),
    ("WaterHair", "hair water shader"),
]

def guess_role(mi_name):
    for key, role in KNOWN_ROLES:
        if key.lower() in mi_name.lower():
            return role
    return "unknown"

def check_texture_health(mi_name, params):
    issues = []
    if mi_name not in mi_params:
        return issues
    data = mi_params[mi_name]
    if "error" in data:
        issues.append(f"Could not query parameters: {data['error']}")
        return issues
    textures = data.get("texture", [])
    for tex in textures:
        val = tex.get("value", "")
        if val.startswith("/Game/") and "/Melodia/" not in val and "/EnvSandbox/" not in val and "/Engine/" not in val and val.count("/") <= 3:
            issues.append(f"Broken texture reference: {tex['name']} -> {val}")
        if tex.get("is_overridden") and ("Marble" in val or val.endswith("DefaultTexture")):
            issues.append(f"Suspicious texture: {tex['name']} -> {val} (Marble/default placeholder?)")
    return issues

per_slot = {}
for idx in sorted(live_slots.keys()):
    slot = live_slots[idx]
    mi_name = slot["mi_name"]
    mi_path = slot["mi_path"]
    slot_name = slot["slot_name"]

    si = {
        "slot_index_0based": idx,
        "slot_index_1based": idx + 1,
        "slot_name": slot_name,
        "material_instance": mi_name,
        "material_path": mi_path if mi_name not in ("NONE", "None") else None,
        "role": guess_role(mi_name),
        "material_family": classify_slot(idx, mi_name),
        "has_material_assigned": mi_name not in ("NONE", "None"),
        "parent_master": KNOWN_PARENT_MASTER if mi_name not in ("NONE", "None") else None,
    }

    if mi_name in ("NONE", "None"):
        si["status"] = "empty"
        si["issues"] = ["No material instance assigned to this slot"]
        per_slot[idx] = si
        continue

    # Check against offline SLOT_MAP expectations
    expected_mi = None
    known_issues = ""
    offline_map = {
        0: ("Gradient__Radial__002", "MI_Melusina_Gradient__Radial__002"),
        1: ("SBW_MELUSINA_006", "MI_Melusina_SBW_MELUSINA_006"),
        2: ("SBW_MELUSINA_007", "MI_Melusina_SBW_MELUSINA_007"),
        3: ("sleeve_003", "MI_Melusina_sleeve_003"),
        4: ("Outline_Shader_star_024", "MI_Melusina_Outline_Shader_star_024"),
        5: ("Metal_2__Matcap__002", "MI_Melusina_Metal_2__Matcap__002"),
        6: ("Outline_005", "MI_Melusina_Outline_005"),
        7: ("Material_021", "MI_Melusina_Material_021"),
        8: ("Outline_004", "MI_Melusina_Outline_004"),
        9: ("Material_013", "MI_Melusina_Material_013"),
        10: ("Halftone_Circles___Circles__3_Inputs__001", "MI_Melusina_Halftone_Circles___Circles__3_Inputs__001"),
        11: ("Material_022", "MI_Melusina_Material_022"),
        12: ("Material_023", "MI_Melusina_Material_023"),
        13: ("bow_002", "MI_Melusina_bow_002"),
        14: ("Outline_Shader_star_034", "MI_Melusina_Outline_Shader_star_034"),
        15: ("Material_024", "MI_Melusina_Material_024"),
        16: ("skirtpanel_002", "MI_Melusina_skirtpanel_002"),
        17: ("Outline_Shader_star_029", "MI_Melusina_Outline_Shader_star_029"),
        18: ("SHAWL_001", "MI_Melusina_SHAWL_001"),
        19: ("frontpanel_001", "MI_Melusina_frontpanel_001"),
        20: ("Outline_Shader_star_023", "MI_Melusina_Outline_Shader_star_023"),
        21: ("GLOVES_001", "MI_Melusina_GLOVES_001"),
        22: ("Outline_Shader_star_030", "MI_Melusina_Outline_Shader_star_030"),
        23: ("Material_017", "MI_Melusina_Material_017"),
        24: ("Material_006", "MI_Melusina_Material_006"),
        25: ("Outline_Shader_star_028", "MI_Melusina_Outline_Shader_star_028"),
        26: ("Material_007", "MI_Melusina_Material_007"),
        27: ("Outline_Shader_star_027", "MI_Melusina_Outline_Shader_star_027"),
        28: ("Iridescence_002", "MI_Melusina_Iridescence_002"),
        29: ("Outline_Shader_star_026", "MI_Melusina_Outline_Shader_star_026"),
        30: ("Outline_Shader_star_032", "MI_Melusina_Outline_Shader_star_032"),
        31: ("SKIRT_003", "MI_Melusina_SKIRT_003"),
        32: ("Halftone_3_Inputs_-_Lines___Circles_002", "MI_Melusina_Halftone_3_Inputs_-_Lines___Circles_002"),
    }
    if idx in offline_map:
        expected_mi = offline_map[idx][1]

    issues = []

    if expected_mi and mi_name != expected_mi:
        if mi_name == "MI_Melusina_Material_023" and expected_mi.startswith("MI_Melusina_Material_02"):
            issues.append(f"WRONG MI ASSIGNED: got '{mi_name}' expected '{expected_mi}' - celestial catch-all replaced dedicated material")
        elif expected_mi.startswith("MI_Melusina_Outline_Shader_star_") and mi_name == "MI_Melusina_Material_023":
            issues.append(f"WRONG MI ASSIGNED: got '{mi_name}' expected '{expected_mi}' - outline slot got celestial catch-all")
        elif mi_name != expected_mi:
            issues.append(f"MI MISMATCH: got '{mi_name}' expected '{expected_mi}'")
    elif idx == 0 and mi_name == "None":
        issues.append("Slot 0 uses M_Master_Toon_Universal directly - no MI instance; should use a dedicated MI")

    # Check parent
    data = mi_params.get(mi_name, {})
    if "error" in data:
        issues.append(f"Could not read parameters: {data.get('error')}")
    else:
        parent = data.get("parent", "")
        if parent != KNOWN_PARENT_MASTER:
            si["parent_master"] = parent
            issues.append(f"Non-standard parent: {parent} (expected {KNOWN_PARENT_MASTER})")

        # Check static switches
        switches = {s["name"]: s for s in data.get("static_switch", [])}

        # bUseSeparateRoughnessMap
        rough_switch = switches.get("bUseSeparateRoughnessMap", {})
        if not rough_switch.get("is_overridden", False) or not rough_switch.get("value", False):
            issues.append("bUseSeparateRoughnessMap not overridden to True")
        si["bUseSeparateRoughnessMap"] = rough_switch.get("value", None)

        # bUseSeparateMetallicMap
        metal_switch = switches.get("bUseSeparateMetallicMap", {})
        if not metal_switch.get("is_overridden", False) or not metal_switch.get("value", False):
            issues.append("bUseSeparateMetallicMap not overridden to True")
        si["bUseSeparateMetallicMap"] = metal_switch.get("value", None)

        # Check for bUseSubstrateToon and ToonProfile
        si["has_bUseSubstrateToon_param"] = "bUseSubstrateToon" in switches

        # Textures
        tex_issues = check_texture_health(mi_name, data)
        issues.extend(tex_issues)

        # Texture inventory
        textures = {t["name"]: t["value"] for t in data.get("texture", [])}
        si["textures_assigned"] = textures
        si["has_albedo"] = "Albedo" in textures
        si["has_normal"] = "NormalMap" in textures
        si["has_roughness"] = "RoughnessMap" in textures
        si["has_metallic"] = "MetallicMap" in textures
        si["scalar_overrides"] = len(data.get("scalar", []))
        si["vector_overrides"] = len(data.get("vector", []))
        si["texture_overrides"] = len(data.get("texture", []))
        si["switch_overrides"] = len(data.get("static_switch", []))
        si["total_overrides"] = data.get("total_overrides", 0)

    si["issues"] = issues
    si["status"] = "pass" if len(issues) == 0 else "warn" if len(issues) <= 2 else "fail"
    per_slot[idx] = si

# ── Water hair section ──────────────────────────────────────────────────
water_hair = mi_params.get("MI_Melusina_WaterHair", {})
water_hair_entry = {
    "mesh": "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair",
    "material_instance": "MI_Melusina_WaterHair",
    "material_path": "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair",
    "parent_master": water_hair.get("parent", "Unknown"),
    "shading_model": "MSM_DefaultLit (via parent M_Water_Master_Grand_v7)",
    "role": "hair (water shader)",
    "issues": [],
    "status": "pass",
}
if water_hair.get("isError"):
    water_hair_entry["status"] = "warn"
    water_hair_entry["issues"].append(f"Could not query: {water_hair.get('error')}")
else:
    parent = water_hair.get("parent", "")
    if "Water_Master" not in parent:
        water_hair_entry["issues"].append(f"Unexpected parent: {parent}")
        water_hair_entry["status"] = "warn"
    if not water_hair.get("texture"):
        water_hair_entry["issues"].append("No texture overrides - may be using parent defaults")
        water_hair_entry["status"] = "warn"
    water_hair_entry["scalar_overrides"] = len(water_hair.get("scalar", []))
    water_hair_entry["vector_overrides"] = len(water_hair.get("vector", []))

# ── Summary ─────────────────────────────────────────────────────────────
total_slots = len(live_slots)
assigned = sum(1 for v in per_slot.values() if v["has_material_assigned"])
empty = total_slots - assigned
passed = sum(1 for v in per_slot.values() if v["status"] == "pass")
warned = sum(1 for v in per_slot.values() if v["status"] == "warn")
failed = sum(1 for v in per_slot.values() if v["status"] == "fail")

def generate_recs(results):
    recs = []
    wrong_assignments = [(k, v) for k, v in results.items() if isinstance(k, int) and any("WRONG MI" in i or "MI MISMATCH" in i for i in v.get("issues", []))]
    if wrong_assignments:
        recs.append(f"Fix {len(wrong_assignments)} slot(s) with wrong MI assignments: {[(k, v['material_instance']) for k, v in wrong_assignments]}")
    broken_textures = [(k, v) for k, v in results.items() if isinstance(k, int) and any("Broken texture" in i for i in v.get("issues", []))]
    if broken_textures:
        recs.append(f"Fix broken texture references on {len(broken_textures)} slot(s): {[(k, v['material_instance']) for k, v in broken_textures]}")
    missing_rough = [(k, v) for k, v in results.items() if isinstance(k, int) and "bUseSeparateRoughnessMap not overridden" in str(v.get("issues", []))]
    if missing_rough:
        recs.append(f"Set bUseSeparateRoughnessMap=True on {len(missing_rough)} slot(s): {[v['material_instance'] for _, v in missing_rough]}")
    missing_metal = [(k, v) for k, v in results.items() if isinstance(k, int) and "bUseSeparateMetallicMap not overridden" in str(v.get("issues", []))]
    if missing_metal:
        recs.append(f"Set bUseSeparateMetallicMap=True on {len(missing_metal)} slot(s): {[v['material_instance'] for _, v in missing_metal]}")
    recs.append("Verify TP_Melusina toon profile is properly applied at the M_Master_Toon_Universal level")
    recs.append("Run fix_up_redirectors.py and Map Check after any editor session")
    recs.append("Slot 0 (Gradient__Radial__002) uses master directly - consider creating a proper MI")
    recs.append("Slots 24/26/28 use raw Materials from _SkeletonFixSpike/ - consider converting to MIs")
    return recs

def generate_priority(results):
    priority = []
    for k, v in sorted(results.items()):
        if not isinstance(k, int): continue
        if not v["has_material_assigned"]:
            priority.append((k, v["material_instance"], "HIGH", "No material assigned"))
            continue
        if any("WRONG MI" in i for i in v.get("issues", [])):
            priority.append((k, v["material_instance"], "HIGH", "Wrong MI assigned"))
            continue
        if any("Broken texture" in i for i in v.get("issues", [])):
            priority.append((k, v["material_instance"], "HIGH", "Broken texture references"))
            continue
        if any("not overridden to True" in i for i in v.get("issues", [])):
            priority.append((k, v["material_instance"], "MEDIUM", "Missing static switch override"))
            continue
    return priority

report = {
    "audit_timestamp": datetime.now().isoformat(),
    "audit_mode": "online",
    "monolith_reachable": True,
    "mesh": "/Game/Melodia/Characters/Melusina/SK_Melusina",
    "parent_master": KNOWN_PARENT_MASTER,
    "toon_profile": TOON_PROFILE,
    "total_slots_in_mesh": total_slots,
    "assigned_slots": assigned,
    "empty_slots": empty,
    "unassigned_slot_indices": [k for k, v in per_slot.items() if not v["has_material_assigned"]],
    "slots_ok": passed,
    "slots_with_warnings": warned,
    "slots_with_errors": failed,
    "water_hair": water_hair_entry,
    "per_slot_results": per_slot,
    "master_material_params": {
        "shading_model": master_props.get("shading_model"),
        "blend_mode": master_props.get("blend_mode"),
        "bUseSeparateRoughnessMap_default": False,
        "bUseSeparateMetallicMap_default": False,
    },
    "summary": {
        "grade": "PASS" if (warned + failed) == 0 else "WARN" if failed == 0 else "FAIL",
        "issues_found": sum(len(v["issues"]) for k, v in per_slot.items()),
        "recommendations": generate_recs(per_slot),
        "priority_order": generate_priority(per_slot),
    }
}

# ── Write reports ───────────────────────────────────────────────────────
json_path = PROJECT_ROOT / "Tools" / "audit_melusina_materials_report_live.json"
md_path = PROJECT_ROOT / "Tools" / "audit_melusina_materials_report_live.md"

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nJSON report written to {json_path}")

# ── MD report ─────────────────────────────────────────────────────────
lines = []
lines.append("# Melusina Material Audit Report - LIVE (Monolith) - Substrate Toon Compliance")
lines.append(f"**Generated:** {report['audit_timestamp']}")
lines.append(f"**Audit Mode:** ONLINE")
lines.append(f"**Monolith Reachable:** True")
lines.append(f"**Mesh:** `{report['mesh']}`")
lines.append(f"**Parent Master:** `{report['parent_master']}`")
lines.append(f"**Toon Profile:** `{report['toon_profile']}`")
lines.append("")
lines.append("## Overall Summary")
lines.append("| Metric | Value |")
lines.append("|--------|-------|")
lines.append(f"| Total Slots | {total_slots} |")
lines.append(f"| Material Instances (assigned) | {assigned} |")
lines.append(f"| Empty | {empty} |")
lines.append(f"| Slots OK | {passed} |")
lines.append(f"| Slots with Warnings | {warned} |")
lines.append(f"| Slots with Errors | {failed} |")
lines.append(f"| Grade | **{report['summary']['grade']}** |")
lines.append(f"| Total Issues | {report['summary']['issues_found']} |")
lines.append("")

lines.append("## Live Slot Assignments (from SK_Melusina.materials)")
lines.append("")
lines.append("| Slot | Slot Name | MI Assigned | Role | Status | Issues |")
lines.append("|------|-----------|-------------|------|--------|--------|")
for k in sorted(per_slot.keys()):
    v = per_slot[k]
    mi_name = v["material_instance"]
    status = v["status"].upper()
    issues_str = "; ".join(v["issues"][:3]) if v["issues"] else "-"
    lines.append(f"| {k} | `{v['slot_name']}` | `{mi_name}` | {v['role']} | **{status}** | {issues_str} |")
lines.append("")

lines.append("## Water Hair Material (Separate Mesh: SK_MelusinaHair)")
wh = water_hair_entry
lines.append(f"**MI:** `{wh['material_instance']}` at `{wh['material_path']}`")
lines.append(f"**Parent:** `{wh['parent_master']}`")
lines.append(f"**Status:** {wh['status'].upper()}")
if wh.get("issues"):
    for iss in wh["issues"]:
        lines.append(f"- {iss}")
lines.append("")

lines.append("## Recommendations")
for i, rec in enumerate(report["summary"]["recommendations"], 1):
    lines.append(f"{i}. {rec}")
lines.append("")

lines.append("## Priority Order for Fixes")
lines.append("| Slot | MI | Priority | Reason |")
lines.append("|------|-----|----------|--------|")
for idx, name, priority, reason in report["summary"]["priority_order"]:
    lines.append(f"| {idx} | `{name}` | **{priority}** | {reason} |")
lines.append("")

lines.append("## Per-Slot Parameter Details")
lines.append("")
for k in sorted(per_slot.keys()):
    v = per_slot[k]
    idx = f"Slot {k} (1-based: {k+1})"
    lines.append(f"### {idx} - `{v['material_instance']}`")
    lines.append(f"**Status:** {v['status'].upper()}")
    lines.append(f"**Slot Name:** `{v['slot_name']}`")
    lines.append(f"**Role:** {v['role']}")
    lines.append(f"**Family:** {v['material_family']}")
    lines.append(f"**Parent:** `{v['parent_master']}`")
    if v.get("bUseSeparateRoughnessMap") is not None:
        lines.append(f"**bUseSeparateRoughnessMap:** {v['bUseSeparateRoughnessMap']}")
    if v.get("bUseSeparateMetallicMap") is not None:
        lines.append(f"**bUseSeparateMetallicMap:** {v['bUseSeparateMetallicMap']}")
    if v.get("total_overrides") is not None:
        lines.append(f"**Total Parameter Overrides:** {v['total_overrides']}")
    if v.get("textures_assigned"):
        lines.append("**Textures:**")
        for tname, tpath in v["textures_assigned"].items():
            lines.append(f"  - `{tname}` -> `{tpath}`")
    if v["issues"]:
        lines.append("**Issues:**")
        for iss in v["issues"]:
            lines.append(f"- {iss}")
    lines.append("")

lines.append("---")
lines.append("*Audit performed live via Monolith MCP. Re-run to refresh.*")

with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"MD report written to {md_path}")

# ── Summary print ─────────────────────────────────────────────────────────
print()
print("=" * 60)
print("LIVE MATERIAL AUDIT SUMMARY")
print("=" * 60)
print(f"Total slots: {total_slots}")
print(f"Assigned: {assigned}")
print(f"Empty: {empty}")
print(f"OK: {passed} | Warn: {warned} | Fail: {failed}")
print(f"Grade: {report['summary']['grade']}")
print()
print("Priority fixes:")
for idx, name, priority, reason in report["summary"]["priority_order"]:
    print(f"  [{priority}] Slot {idx}: {name} - {reason}")
print()
print("Done.")
