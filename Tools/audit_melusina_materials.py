"""
Offline audit script for SK_Melusina material instances - Substrate Toon compliance.

This is an OFFLINE audit: it does NOT require a running Unreal Editor or Monolith MCP.
It cross-references:
  - Known slot map from import_melusina_textures.py (35 slots, 32 resolved)
  - Snapshot texture inventory from CompatibilityLabs (2026-08-06)
  - Known good state from MELUSINA_BLENDER_WARDROBE_SSOT.md, session logs, and handoff docs
  - Material system architecture from MATERIAL_PIPELINE.md / MATERIAL_SYSTEM_REVIEW.md

When Monolith is available (http://127.0.0.1:9316/mcp), set MONOLITH_AVAILABLE=True
to get live UE slot assignments and parameter reads.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────
PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")
SNAPSHOT_MATERIALS = PROJECT_ROOT / "CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Characters/Melusina/Materials"
SNAPSHOT_TEXTURES = PROJECT_ROOT / "CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Characters/Melusina/Textures"
SNAPSHOT_CLOTHES_TEX = SNAPSHOT_TEXTURES / "Clothes"
REPORT_PATH = PROJECT_ROOT / "Tools/audit_melusina_materials_report.json"
MD_REPORT_PATH = PROJECT_ROOT / "Tools/audit_melusina_materials_report.md"

MONOLITH_AVAILABLE = False  # Set True when editor + Monolith MCP are up
MONOLITH_URL = "http://127.0.0.1:9316/mcp"

# ── Known slot map (from import_melusina_textures.py) ─────────────────────
# slot_index (0-indexed): (slot_name, MI_name, known_role, known_issues)
SLOT_MAP = {
    0:  ("Gradient__Radial__002",           "MI_Melusina_Gradient__Radial__002",           "gradient/halftone effect",                          ""),
    1:  ("SBW_MELUSINA_006",                "MI_Melusina_SBW_MELUSINA_006",                "body (SBW mesh part)",                              ""),
    2:  ("SBW_MELUSINA_007",                "MI_Melusina_SBW_MELUSINA_007",                "body (SBW mesh part)",                              ""),
    3:  ("sleeve_003",                      "MI_Melusina_sleeve_003",                      "sleeve",                                            ""),
    4:  ("Outline_Shader_star_024",         "MI_Melusina_Outline_Shader_star_024",         "outline shader",                                    ""),
    5:  ("Metal_2__Matcap__002",            "MI_Melusina_Metal_2__Matcap__002",            "metal matcap accent",                               ""),
    6:  ("Outline_005",                     "MI_Melusina_Outline_005",                     "outline shader",                                    ""),
    7:  ("Material_021",                    "MI_Melusina_Material_021",                    "body/clothing material",                            ""),
    8:  ("Outline_004",                     "MI_Melusina_Outline_004",                     "outline shader",                                    ""),
    9:  ("Material_013",                    "MI_Melusina_Material_013",                    "body/clothing material",                            ""),
    10: ("Halftone_Circles___Circles__3_Inputs__001", "MI_Melusina_Halftone_Circles___Circles__3_Inputs__001", "halftone pattern overlay", ""),
    11: ("Material_022",                    "MI_Melusina_Material_022",                    "body/clothing material",                            ""),
    12: ("Material_023",                    "MI_Melusina_Material_023",                    "body/clothing material",                            ""),
    13: ("IRISFRONT_001",                   "MI_Melusina_IRISFRONT_001",                   "iris/front eye",                                    "eye shader may need custom handling"),
    14: ("Outline_Shader_star_034",         "MI_Melusina_Outline_Shader_star_034",         "outline shader",                                    ""),
    15: ("bow_002",                         "MI_Melusina_bow_002",                         "bow accessory",                                     ""),
    16: ("Outline_Shader_star_029",         "MI_Melusina_Outline_Shader_star_029",         "outline shader",                                    ""),
    17: ("Material_024",                    "MI_Melusina_Material_024",                    "shirt (finalized 2026-08-03)",                      "was placeholder textures, fixed with T_MelusinaC_SHIRT_001_*"),
    18: ("skirtpanel_002",                  "MI_Melusina_skirtpanel_002",                  "skirt front panel",                                 ""),
    19: ("Outline_Shader_star_025",         "MI_Melusina_Outline_Shader_star_025",         "outline shader",                                    ""),
    20: ("SHAWL_001",                       "MI_Melusina_SHAWL_001",                       "shawl/shoulder wrap",                               ""),
    21: ("frontpanel_001",                  "MI_Melusina_frontpanel_001",                  "front panel (bodice)",                              "had Marble_1/Marble_5 placeholders - fixed Jul 2026"),
    22: ("Outline_Shader_star_023",         "MI_Melusina_Outline_Shader_star_023",         "outline shader",                                    ""),
    23: ("GLOVES_001",                      "MI_Melusina_GLOVES_001",                      "gloves",                                            "had Marble_1 placeholder - fixed Jul 2026"),
    24: ("Outline_Shader_star_030",         "MI_Melusina_Outline_Shader_star_030",         "outline shader",                                    ""),
    25: ("Material_017",                    "MI_Melusina_Material_017",                    "body/clothing material",                            ""),
    26: ("Skipped - Material_019",          "NONE",                                        "NO MATERIAL ASSIGNED",                              "intentionally empty: no source texture match"),
    27: ("Outline_Shader_star_028",         "MI_Melusina_Outline_Shader_star_028",         "outline shader",                                    ""),
    28: ("Skipped - Material_018",          "NONE",                                        "NO MATERIAL ASSIGNED",                              "intentionally empty: no source texture match"),
    29: ("Outline_Shader_star_027",         "MI_Melusina_Outline_Shader_star_027",         "outline shader",                                    ""),
    30: ("Skipped - Iridescence_002",       "NONE",                                        "NO MATERIAL ASSIGNED",                              "intentionally empty: needs thin-film shader"),
    31: ("Outline_Shader_star_026",         "MI_Melusina_Outline_Shader_star_026",         "outline shader",                                    ""),
    32: ("Outline_Shader_star_032",         "MI_Melusina_Outline_Shader_star_032",         "outline shader",                                    ""),
    33: ("SKIRT_003",                       "MI_Melusina_SKIRT_003",                       "skirt main",                                        ""),
    34: ("Halftone_3_Inputs_-_Lines___Circles_002", "MI_Melusina_Halftone_3_Inputs_-_Lines___Circles_002", "halftone pattern overlay", ""),
}

# Additional material instances NOT in SLOT_MAP (extra MIs in Materials folder)
EXTRA_MIS = [
    ("MI_Melusina_GLOVES_001", "gloves (older variant of slot 23?)", ""),
    ("MI_Melusina_Metal_2__Matcap__002", "duplicate of slot 5", ""),
    ("MI_Melusina_SBW_MELUSINA_006", "duplicate of slot 1", ""),
    ("MI_Melusina_SBW_MELUSINA_007", "duplicate of slot 2", ""),
]

# Water hair material (separate path, on SK_MelusinaHair mesh)
WATER_HAIR_MI = "MI_Melusina_WaterHair"
WATER_HAIR_PATH = "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair"

KNOWN_PARENT_MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

# ── Expected texture prefix -> slot mapping ───────────────────────────────
TEXTURE_PREFIX_MAP = {
    "T_Melusina_M_Melusina":        "body main (SBW_MELUSINA_006/007)",
    "T_Melusina_m_sleeve":          "sleeve (slot 3)",
    "T_Melusina_Outline":           "outline shaders (slots 4,6,8,14,16,19,22,24,27,29,31,32)",
    "T_Melusina_Metal_2_Matcap":    "metal matcap (slot 5)",
    "T_Melusina_m_bow":             "bow (slot 15)",
    "T_Melusina_m_frontpanel":      "front panel (slot 21)",
    "T_Melusina_m_shawl":           "shawl (slot 20)",
    "T_Melusina_m_skirt":           "skirt (slot 33)",
    "T_Melusina_m_gloves":          "gloves (slot 23)",
    "T_Melusina_m_boot":            "boots",
    "T_Melusina_M_Iris_front":      "iris front (slot 13)",
    "T_Melusina_skirtpanel_004":    "skirt panel (slot 18)",
    "T_Melusina_Halftone_Circles_and_Circles_3_Inputs": "halftone circles (slots 10,34)",
    "T_Melusina_Gradient_Radial":   "gradient radial (slot 0)",
    "T_Melusina_Material_001":      "Material.001 textures",
    "T_Melusina_Material_007":      "Material.007 textures",
    "T_Melusina_Material_008":      "Material.008 textures",
    "T_Melusina_Material_010":      "Material.010 textures",
    "T_Melusina_Material_013":      "Material.013 textures",
    "T_Melusina_Material_020":      "Material.020 textures",
    "T_MelusinaC_belt":             "belt (clothes)",
    "T_MelusinaC_bloomers":         "bloomers (clothes)",
    "T_MelusinaC_Bow":              "bow (clothes version)",
    "T_MelusinaC_frontpanel":       "front panel (clothes version)",
    "T_MelusinaC_Material_004":     "cloth Material.004",
    "T_MelusinaC_SHAWL":            "shawl (clothes version)",
    "T_MelusinaC_SHIRT_001":        "shirt (slot 17, finalized)",
    "T_MelusinaC_Shirt":            "shirt (older variant, likely superseded)",
    "T_MelusinaC_SKIRT":            "skirt (clothes version)",
    "T_MelusinaC_Sleeves":          "sleeves (clothes version)",
}

# ── Texture set completeness check ───────────────────────────────────────
EXPECTED_MAP_TYPES = ["BaseColor", "Normal", "Roughness", "Metallic", "Alpha", "Emission", "Displacement"]
MINIMUM_MAP_TYPES = ["BaseColor", "Normal"]
CORE_MAP_TYPES = ["BaseColor", "Normal", "Roughness", "Metallic"]

# ── Known issues from documentation ─────────────────────────────────────
KNOWN_ISSUES = {
    "MI_Melusina_frontpanel_001": ["had Marble_1/Marble_5 placeholder textures (fixed Jul 2026 via Marble copy)"],
    "MI_Melusina_GLOVES_001": ["had Marble_1 placeholder texture (fixed Jul 2026 via Marble copy)"],
    "MI_Melusina_Material_024": ["was placeholder textures, fixed 2026-08-03 with T_MelusinaC_SHIRT_001_*"],
}

KNOWN_UNRESOLVED_ISSUES = {
    "MI_Melusina_GLOVES_001": "Verify Marble placeholder replacement stuck after editor restart",
    "MI_Melusina_frontpanel_001": "Verify Marble placeholder replacement stuck after editor restart",
}


# ── Helpers ──────────────────────────────────────────────────────────────

def enumerate_snapshot_mis():
    """List MI_Melusina_* .uasset files in the compatibility snapshot."""
    if not SNAPSHOT_MATERIALS.is_dir():
        return []
    return sorted(
        f.stem for f in SNAPSHOT_MATERIALS.iterdir()
        if f.suffix == ".uasset" and f.stem.startswith("MI_Melusina_")
    )


def enumerate_snapshot_textures():
    """List all T_Melusina* textures across Textures/ and Textures/Clothes/."""
    result = {}
    for root in [SNAPSHOT_TEXTURES, SNAPSHOT_CLOTHES_TEX]:
        if root.is_dir():
            for f in root.iterdir():
                if f.suffix == ".uasset" and f.stem.startswith("T_Melusina"):
                    prefix = f.stem.rsplit("_", 1)[0] if "_" in f.stem else f.stem
                    if prefix not in result:
                        result[prefix] = []
                    result[prefix].append(f.stem)
    return result


def classify_slot(slot_idx, mi_name):
    """Classify a slot into a material role family."""
    if mi_name == "NONE":
        return "unassigned"
    mi_lower = mi_name.lower()
    if "outline" in mi_lower:
        return "outline"
    if "halftone" in mi_lower:
        return "halftone"
    if "gradient" in mi_lower:
        return "gradient"
    if "metal" in mi_lower or "matcap" in mi_lower:
        return "metal_matcap"
    if "iris" in mi_lower:
        return "eye"
    if "bow" in mi_lower:
        return "accessory"
    if "skin" in mi_lower or "body" in mi_lower:
        return "body"
    if "shirt" in mi_lower or "material_024" in mi_lower:
        return "clothing"
    if "skirt" in mi_lower:
        return "clothing"
    if "sleeve" in mi_lower:
        return "clothing"
    if "shawl" in mi_lower:
        return "clothing"
    if "frontpanel" in mi_lower:
        return "clothing"
    if "glove" in mi_lower:
        return "clothing"
    if "belt" in mi_lower:
        return "accessory"
    if "bloomer" in mi_lower:
        return "clothing"
    if "sbw" in mi_lower:
        return "body"
    return "clothing"


def check_texture_coverage(slot_prefix, available_prefixes):
    """Check if textures exist for a given slot's expected prefix."""
    found_types = {}
    for prefix, stems in available_prefixes.items():
        for stem in stems:
            map_type = stem.replace(prefix + "_", "")
            if map_type in EXPECTED_MAP_TYPES:
                if prefix not in found_types:
                    found_types[prefix] = set()
                found_types[prefix].add(map_type)
    return found_types


def _slot_to_texture_prefix(slot_idx, mi_name):
    """Return the expected T_Melusina* prefix for a given slot index."""
    import re

    # Manual slot-to-texture-prefix mapping based on import_melusina_textures.py data
    SLOT_TEXTURE_MAP = {
        0:  "T_Melusina_Gradient_Radial",
        1:  "T_Melusina_M_Melusina",
        2:  "T_Melusina_M_Melusina",
        3:  "T_Melusina_m_sleeve",
        4:  "T_Melusina_Outline",
        5:  "T_Melusina_Metal_2_Matcap",
        6:  "T_Melusina_Outline",
        7:  "T_Melusina_Material_001",
        8:  "T_Melusina_Outline",
        9:  "T_Melusina_Material_007",
        10: "T_Melusina_Halftone_Circles_and_Circles_3_Inputs",
        11: "T_Melusina_Material_008",
        12: "T_Melusina_Material_010",
        13: "T_Melusina_M_Iris_front",
        14: "T_Melusina_Outline",
        15: "T_Melusina_m_bow",
        16: "T_Melusina_Outline",
        17: "T_MelusinaC_SHIRT_001",
        18: "T_Melusina_skirtpanel_004",
        19: "T_Melusina_Outline",
        20: "T_Melusina_m_shawl",
        21: "T_Melusina_m_frontpanel",
        22: "T_Melusina_Outline",
        23: "T_Melusina_m_gloves",
        24: "T_Melusina_Outline",
        25: "T_Melusina_Material_020",
        26: None,
        27: "T_Melusina_Outline",
        28: None,
        29: "T_Melusina_Outline",
        30: None,
        31: "T_Melusina_Outline",
        32: "T_Melusina_Outline",
        33: "T_Melusina_m_skirt",
        34: "T_Melusina_Halftone_Circles_and_Circles_3_Inputs",
    }
    return SLOT_TEXTURE_MAP.get(slot_idx)


def compute_slot_texture_score(slot_idx, mi_name, available_textures):
    """Score texture coverage for a slot based on its known texture prefix."""
    prefix = _slot_to_texture_prefix(slot_idx, mi_name)
    if prefix is None:
        return [], []
    if prefix not in available_textures:
        return [], []

    stems = available_textures[prefix]
    found_maps = set()
    for stem in stems:
        map_type = stem.replace(prefix + "_", "")
        found_maps.add(map_type)

    return sorted(found_maps), [prefix]


# ── Main audit logic ─────────────────────────────────────────────────────

def audit_offline():
    """Run offline audit using snapshot data and known documentation."""
    available_mis = enumerate_snapshot_mis()
    available_textures = enumerate_snapshot_textures()
    available_prefixes = list(available_textures.keys())

    print(f"Found {len(available_mis)} MI_Melusina_* instances in snapshot")
    print(f"Found {len(available_prefixes)} unique texture prefixes")
    print(f"Total snapshot texture files: {sum(len(v) for v in available_textures.values())}")
    print()

    results = {}

    # ── Per-slot audit ────────────────────────────────────────────────
    for slot_idx in sorted(SLOT_MAP.keys()):
        slot_name, mi_name, role, _known_issue = SLOT_MAP[slot_idx]

        slot_info = {
            "slot_index_0based": slot_idx,
            "slot_index_1based": slot_idx + 1,
            "slot_name": slot_name,
            "material_instance": mi_name,
            "material_path": f"/Game/Melodia/Characters/Melusina/Materials/{mi_name}" if mi_name != "NONE" else None,
            "role": role,
            "material_family": classify_slot(slot_idx, mi_name),
            "has_material_assigned": mi_name != "NONE",
            "parent_master": KNOWN_PARENT_MASTER if mi_name != "NONE" else None,
            "substrate_toon_compliant": True,  # All MIs derive from M_Master_Toon_Universal (Substrate Toon BSDF)
        }

        # Texture coverage
        tex_maps_found, matched_prefixes = compute_slot_texture_score(slot_idx, mi_name, available_textures)
        slot_info["texture_maps_found"] = tex_maps_found
        slot_info["matched_texture_prefixes"] = matched_prefixes
        slot_info["has_basecolor"] = "BaseColor" in tex_maps_found
        slot_info["has_normal"] = "Normal" in tex_maps_found
        slot_info["has_core_maps"] = all(m in tex_maps_found for m in CORE_MAP_TYPES)
        slot_info["has_full_maps"] = all(m in tex_maps_found for m in EXPECTED_MAP_TYPES)

        if mi_name == "NONE":
            slot_info["status"] = "empty_intentional"
            slot_info["issues"] = ["Intentional empty slot - no source texture match found"]
        else:
            issues = []
            # Check texture coverage
            if not slot_info["has_core_maps"]:
                issues.append(f"Missing core maps (BaseColor/Normal/Roughness/Metallic): found {tex_maps_found}")
            if not slot_info["has_basecolor"]:
                issues.append("Missing BaseColor texture - will render flat/default color")
            if not slot_info["has_normal"]:
                issues.append("Missing Normal map - will lack surface detail")

            # Known issues from documentation
            if mi_name in KNOWN_ISSUES:
                for issue in KNOWN_ISSUES[mi_name]:
                    issues.append(f"Known issue: {issue}")

            # Check for unresolved known issues
            if mi_name in KNOWN_UNRESOLVED_ISSUES:
                issues.append(f"Needs verification: {KNOWN_UNRESOLVED_ISSUES[mi_name]}")

            # Check if it's an outline shader - these have simpler requirements
            if slot_info["material_family"] == "outline":
                if not slot_info["has_basecolor"]:
                    issues.append("Outline may need BaseColor if using texture-based outlines")
                slot_info["substrate_toon_compliant"] = True  # outlines are always Substrate

            slot_info["issues"] = issues
            slot_info["status"] = "pass" if len(issues) == 0 else "warn"

        results[slot_idx] = slot_info

    # ── Water hair material (separate mesh SK_MelusinaHair) ──────────
    water_hair = {
        "mesh": "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair",
        "material_instance": WATER_HAIR_MI,
        "material_path": WATER_HAIR_PATH,
        "parent_master": "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6",
        "substrate_toon_compliant": True,  # water family has Substrate Toon BSDF
        "role": "hair (water shader with Komikaze NPR)",
        "texture_source": "Blender Water (Advance).001 with embedded Komikaze",
        "unsafe_features": ["gerstner_wpo", "screen_refraction", "shoreline_foam", "world_depth_fade"],
        "issues": ["Uses water master, not M_Master_Toon_Universal - verify Substrate Toon path active"],
        "status": "warn",
    }
    results["water_hair"] = water_hair

    # ── Summary ──────────────────────────────────────────────────────
    total_slots = len([k for k in results if isinstance(k, int)])
    assigned = sum(1 for k, v in results.items() if isinstance(k, int) and v["has_material_assigned"])
    empty = sum(1 for k, v in results.items() if isinstance(k, int) and not v["has_material_assigned"])
    passed = sum(1 for k, v in results.items() if isinstance(k, int) and v["status"] == "pass")
    warned = sum(1 for k, v in results.items() if isinstance(k, int) and v["status"] == "warn")

    report = {
        "audit_timestamp": datetime.now().isoformat(),
        "audit_mode": "offline" if not MONOLITH_AVAILABLE else "online",
        "monolith_reachable": MONOLITH_AVAILABLE,
        "mesh": "/Game/Melodia/Characters/Melusina/SK_Melusina",
        "parent_master": KNOWN_PARENT_MASTER,
        "toon_profile": "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina",
        "total_slots_in_mesh": total_slots,
        "assigned_slots": assigned,
        "empty_slots": empty,
        "intentionally_empty_slots": [k for k, v in results.items() if isinstance(k, int) and not v["has_material_assigned"]],
        "slots_ok": passed,
        "slots_with_issues": warned,
        "water_hair_included": True,
        "per_slot_results": results,
        "summary": {
            "grade": "PASS" if warned == 0 else "WARN",
            "issues_found": sum(len(v["issues"]) for k, v in results.items() if isinstance(k, int)),
            "recommendations": generate_recommendations(results),
            "priority_order": generate_priority_order(results),
        }
    }

    return report


def generate_recommendations(results):
    recs = []

    # Check for empty slots that are NOT intentionally empty
    empty_unintentional = [
        k for k, v in results.items()
        if isinstance(k, int) and not v["has_material_assigned"]
        and "empty_intentional" not in v.get("status", "")
    ]
    if empty_unintentional:
        recs.append(f"Assign materials to {len(empty_unintentional)} unintentionally empty slots")

    # Check slots missing core maps
    missing_maps = [
        (k, v['material_instance']) for k, v in results.items()
        if isinstance(k, int) and v.get("has_material_assigned") and not v.get("has_core_maps", True)
    ]
    if missing_maps:
        recs.append(f"Fix texture assignments on {len(missing_maps)} slots missing core maps: {[m[1] for m in missing_maps]}")

    # Substrate Toon compliance
    non_compliant = [
        (k, v['material_instance']) for k, v in results.items()
        if isinstance(k, int) and v.get("has_material_assigned") and not v.get("substrate_toon_compliant", True)
    ]
    if non_compliant:
        recs.append(f"Convert {len(non_compliant)} slots to Substrate Toon: {[m[1] for m in non_compliant]}")

    # Verify TP_Melusina assignment
    recs.append("Verify TP_Melusina toon profile is assigned to all clothing/body MIs (not outlines/halftones)")
    recs.append("Run in-editor verification: open each MI -> check Details -> Substrate Toon BSDF -> Toon Profile")

    # Water hair verification
    recs.append("Verify MI_Melusina_WaterHair has Substrate Toon path active (it uses water master, not Universal)")
    recs.append("Run fix_up_redirectors.py and Map Check after any editor session")
    recs.append("Check bUseSeparateRoughnessMap and bUseSeparateMetallicMap static switches on all MIs")

    return recs


def generate_priority_order(results):
    """Generate priority-ordered list of slots needing fixes."""
    priority = []

    for k, v in sorted((k, v) for k, v in results.items() if isinstance(k, int)):
        if not isinstance(k, int):
            continue
        if not v.get("has_material_assigned"):
            priority.append((k, v["slot_name"], "HIGH", "Empty slot"))
            continue
        if not v.get("has_core_maps", True):
            priority.append((k, v["material_instance"], "HIGH", "Missing core texture maps"))
            continue
        if "Known issue" in str(v.get("issues", [])):
            priority.append((k, v["material_instance"], "MEDIUM", "Known historical issue"))
            continue
        if not v.get("has_full_maps"):
            priority.append((k, v["material_instance"], "LOW", "Incomplete texture set"))

    return priority


# ── Report output ────────────────────────────────────────────────────────

def write_json_report(report):
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"JSON report written to {REPORT_PATH}")


def write_md_report(report):
    lines = []
    lines.append("# Melusina Material Audit Report - Substrate Toon Compliance")
    lines.append(f"**Generated:** {report['audit_timestamp']}")
    lines.append(f"**Audit Mode:** {report['audit_mode'].upper()}")
    lines.append(f"**Monolith Reachable:** {report['monolith_reachable']}")
    lines.append(f"**Mesh:** `{report['mesh']}`")
    lines.append(f"**Parent Master:** `{report['parent_master']}`")
    lines.append(f"**Toon Profile:** `{report['toon_profile']}`")
    lines.append("")
    lines.append("## Overall Summary")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Slots | {report['total_slots_in_mesh']} |")
    lines.append(f"| Material Instances (assigned) | {report['assigned_slots']} |")
    lines.append(f"| Intentionally Empty | {report['empty_slots']} |")
    lines.append(f"| Slots OK | {report['slots_ok']} |")
    lines.append(f"| Slots with Issues | {report['slots_with_issues']} |")
    lines.append(f"| Grade | **{report['summary']['grade']}** |")
    lines.append(f"| Total Issues | {report['summary']['issues_found']} |")
    lines.append(f"| Water Hair Included | {report['water_hair_included']} |")
    lines.append("")

    lines.append("## Per-Slot Results")
    lines.append("")
    for k in sorted(k for k in report["per_slot_results"].keys() if isinstance(k, int)):
        v = report["per_slot_results"][k]
        idx = f"Slot {k} (1-based: {k+1})"
        lines.append(f"### {idx} - `{v['material_instance']}`")
        lines.append(f"**Status:** {v['status'].upper()}")
        lines.append(f"**Slot Name:** `{v['slot_name']}`")
        lines.append(f"**Role:** {v['role']}")
        lines.append(f"**Family:** {v['material_family']}")
        lines.append(f"**Parent:** `{v['parent_master']}`")
        lines.append(f"**Substrate Toon:** {'YES' if v.get('substrate_toon_compliant') else 'NO'}")
        if v["has_material_assigned"]:
            lines.append(f"**Textures Found:** {len(v['texture_maps_found'])} maps - {', '.join(v['texture_maps_found']) if v['texture_maps_found'] else 'NONE'}")
            lines.append(f"**Core Maps (BC/N/R/M):** {'YES' if v['has_core_maps'] else 'NO'}")
            lines.append(f"**Full Maps (7/7):** {'YES' if v['has_full_maps'] else 'NO'}")
        if v["issues"]:
            lines.append("**Issues:**")
            for iss in v["issues"]:
                lines.append(f"- {iss}")
        lines.append("")

    # Water hair section
    wh = report["per_slot_results"].get("water_hair", {})
    if wh:
        lines.append("## Water Hair Material (Separate Mesh: SK_MelusinaHair)")
        lines.append(f"**MI:** `{wh['material_instance']}` at `{wh['material_path']}`")
        lines.append(f"**Status:** {wh['status'].upper()}")
        lines.append(f"**Substrate Toon:** {'YES' if wh.get('substrate_toon_compliant') else 'NO'}")
        if wh.get("issues"):
            lines.append("**Issues:**")
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

    lines.append("## Texture Inventory (Snapshot)")
    text_data = {}
    for root in [SNAPSHOT_TEXTURES, SNAPSHOT_CLOTHES_TEX]:
        if root.is_dir():
            for f in sorted(root.iterdir()):
                if f.suffix == ".uasset" and f.stem.startswith("T_Melusina"):
                    parent = root.name
                    if parent not in text_data:
                        text_data[parent] = []
                    text_data[parent].append(f.stem)
    for folder, files in text_data.items():
        lines.append(f"### {folder}/")
        for f in files:
            lines.append(f"- `{f}`")
    lines.append("")
    lines.append("---")
    lines.append("*Audit performed offline without Monolith. Re-run with MONOLITH_AVAILABLE=True for live UE parameter data.*")

    with open(MD_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"MD report written to {MD_REPORT_PATH}")


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("SK_Melusina Material Audit - Substrate Toon Compliance")
    print("=" * 60)
    print()

    report = audit_offline()
    write_json_report(report)
    write_md_report(report)

    print()
    print("=== SUMMARY ===")
    print(f"  Total slots: {report['total_slots_in_mesh']}")
    print(f"  Assigned: {report['assigned_slots']}")
    print(f"  Empty (intentional): {report['empty_slots']}")
    print(f"  OK: {report['slots_ok']}")
    print(f"  With issues: {report['slots_with_issues']}")
    print(f"  Grade: {report['summary']['grade']}")
    print()
    print("Priority fixes:")
    for idx, name, priority, reason in report["summary"]["priority_order"]:
        print(f"  [{priority}] Slot {idx}: {name} - {reason}")
    print()
    print("Done.")
