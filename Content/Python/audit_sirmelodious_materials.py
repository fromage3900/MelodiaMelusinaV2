"""Audit Sir Melodious material instances, textures, and mesh slot assignments.

Run in UE Python console:
    exec(open(r'G:/EnvironmentPortfolio/BS_GodFile/Content/Python/audit_sirmelodious_materials.py').read())
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


SIRMELO_ROOT = "/Game/Melodia/Characters/SirMelodious"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
REPORT = Path("G:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/sirmelodious_material_audit.json")

PARAM_TO_MAP = {
    "Albedo": "BaseColor",
    "NormalMap": "Normal",
    "RoughnessMap": "Roughness",
    "MetallicMap": "Metallic",
    "HeightMap": "Displacement",
}


def _path(obj) -> str:
    return obj.get_path_name() if obj else ""


def _mi_audit(mi_path: str) -> dict:
    mi = unreal.load_asset(mi_path)
    if not mi:
        return {"path": mi_path, "exists": False}

    parent = mi.get_editor_property("parent")
    r = {
        "path": mi_path,
        "parent": _path(parent),
        "parent_ok": bool(parent and _path(parent).startswith(MASTER)),
        "textures": {},
        "switches": {},
    }

    for param, maptype in PARAM_TO_MAP.items():
        tex = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, param)
        path = _path(tex)
        r["textures"][param] = {
            "texture": path,
            "map_type": maptype,
            "resolves": bool(tex and unreal.EditorAssetLibrary.does_asset_exist(path.split(".")[0])),
        }

    for sw in ("bUseSeparateRoughnessMap", "bUseSeparateMetallicMap"):
        try:
            val = unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(mi, sw)
            r["switches"][sw] = bool(val)
        except Exception:
            r["switches"][sw] = "unreadable"

    issues = []
    if not r["parent_ok"]:
        issues.append("wrong or missing parent")
    for param, tinfo in r["textures"].items():
        if not tinfo["texture"]:
            issues.append(f"missing texture: {param}")
        elif not tinfo["resolves"]:
            issues.append(f"stale texture ref: {param} -> {tinfo['texture']}")
    for sw, val in r["switches"].items():
        if val is not True:
            issues.append(f"switch off: {sw} = {val}")

    r["issues"] = issues
    r["ok"] = not issues
    return r


def _mesh_slot_audit(mesh_path: str) -> dict:
    mesh = unreal.load_asset(mesh_path)
    if not mesh:
        return {"mesh": mesh_path, "exists": False}

    skeleton = mesh.get_editor_property("skeleton")
    materials = mesh.get_editor_property("materials") or []

    slots = []
    issues = []
    for i, slot in enumerate(materials):
        mat = slot.get_editor_property("material_interface") if slot else None
        name = slot.get_editor_property("material_slot_name") if slot else "unknown"
        parent = None
        is_fbx_stub = False
        if mat:
            try:
                mat_class = mat.get_class().get_name()
                if mat_class in ("MaterialInstanceConstant",):
                    parent = _path(mat.get_editor_property("parent"))
                else:
                    is_fbx_stub = True
            except Exception:
                is_fbx_stub = True

        slot_info = {
            "index": i,
            "slot_name": name,
            "material": _path(mat),
            "material_class": mat.get_class().get_name() if mat else "",
            "parent": parent or "",
            "is_fbx_stub": is_fbx_stub,
        }
        if is_fbx_stub:
            issues.append(f"slot {i} '{name}' uses raw FBX material, not a Toon MI")
        elif not parent or not parent.startswith(MASTER):
            issues.append(f"slot {i} '{name}' MI parent mismatch: {parent}")
        slots.append(slot_info)

    return {
        "mesh": mesh_path,
        "skeleton": _path(skeleton),
        "slot_count": len(slots),
        "fbx_stub_count": sum(1 for s in slots if s["is_fbx_stub"]),
        "mi_count": sum(1 for s in slots if s["material"] and not s["is_fbx_stub"]),
        "slots": slots,
        "issues": issues,
    }


def _texture_inventory() -> dict:
    mi_lib = unreal.MaterialEditingLibrary
    tex_dir = f"{SIRMELO_ROOT}/Textures"
    missing_expected = []
    present = []

    expected_sets = {
        "sirmelo": ["BaseColor", "Normal", "Roughness", "Metallic", "Alpha", "Emission", "Displacement"],
        "feet": ["BaseColor", "Normal", "Roughness", "Metallic", "Emission", "Displacement"],
    }

    for prefix, maptypes in expected_sets.items():
        for mt in maptypes:
            path = f"{tex_dir}/T_SirMelodious_{prefix}_{mt}"
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                tex = unreal.load_asset(path)
                comp = str(tex.get_editor_property("compression_settings")) if tex else "?"
                srgb = bool(tex.get_editor_property("srgb")) if tex else None
                present.append({
                    "name": f"T_SirMelodious_{prefix}_{mt}",
                    "compression": comp,
                    "srgb": srgb,
                })
            else:
                missing_expected.append(f"T_SirMelodious_{prefix}_{mt}")

    return {"present": len(present), "missing": missing_expected, "textures": present}


def _raw_materials_cleanup() -> dict:
    """List orphan Material_0NN stubs from FBX import that should be cleaned."""
    stubs = []
    for path in unreal.EditorAssetLibrary.list_assets(SIRMELO_ROOT, recursive=False, include_folder=False):
        asset = unreal.load_asset(path)
        if not asset:
            continue
        name = asset.get_name()
        if name.startswith("Material_") and name.split("_")[-1].isdigit():
            klass = asset.get_class().get_name()
            stubs.append({"name": name, "class": klass, "path": path})
    return {"count": len(stubs), "stubs": stubs}


def main():
    print("=== Sir Melodious Material Audit ===")

    # 1. Audit material instances
    mi_paths = [
        f"{SIRMELO_ROOT}/Materials/MI_SirMelodious_Sirmelo",
        f"{SIRMELO_ROOT}/Materials/MI_SirMelodious_Feet",
    ]
    mi_results = {}
    for p in mi_paths:
        print(f"\nAuditing: {p}")
        r = _mi_audit(p)
        mi_results[str(p)] = r
        for issue in r["issues"]:
            print(f"  ISSUE: {issue}")
        if r["ok"]:
            print(f"  OK")

    # 2. Audit mesh slots
    mesh_paths = [
        f"{SIRMELO_ROOT}/Rigged/SK_SirMelodious_Rigged",
        f"{SIRMELO_ROOT}/Retopo_Cube_001",
        f"{SIRMELO_ROOT}/Retopo_PM3D_Cube3D1_011",
        f"{SIRMELO_ROOT}/Retopo_PM3D_Cube3D25",
        f"{SIRMELO_ROOT}/Retopo_PM3D_Cube3D27",
        f"{SIRMELO_ROOT}/Retopo_PM3D_Ring3D2_001",
        f"{SIRMELO_ROOT}/Retopo_PM3D_Ring3D2_1_001",
        f"{SIRMELO_ROOT}/BezierCurve_001",
    ]
    mesh_results = {}
    for mp in mesh_paths:
        r = _mesh_slot_audit(mp)
        if r.get("exists", True):
            mesh_results[mp] = r
            print(f"\n{mp}: {r['slot_count']} slots, {r['fbx_stub_count']} FBX stubs, {r['mi_count']} MIs")
            for issue in r["issues"]:
                print(f"  ISSUE: {issue}")

    # 3. Texture inventory
    tex_inv = _texture_inventory()
    print(f"\nTextures: {tex_inv['present']} present, {len(tex_inv['missing'])} missing")
    for m in tex_inv["missing"]:
        print(f"  MISSING: {m}")

    # 4. Raw material stubs
    stubs = _raw_materials_cleanup()
    print(f"\nRaw FBX material stubs: {stubs['count']}")
    for s in stubs["stubs"]:
        print(f"  {s['name']} ({s['class']})")

    report = {
        "material_instances": mi_results,
        "meshes": mesh_results,
        "textures": tex_inv,
        "raw_material_stubs": stubs,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nReport: {REPORT}")
    return report


if __name__ == "__main__":
    main()
