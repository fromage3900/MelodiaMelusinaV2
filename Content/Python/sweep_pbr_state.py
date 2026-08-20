"""Phase 0 census: full PBR/material state of every StaticMesh + MI in the sweep scope.

Read-only. Dumps:
  - every StaticMesh under EnvSandbox/Meshes/Environment (recursive), EnvSandbox/Library/Migrated,
    Library/Migrated: slot index, slot name, material path (or NONE/WorldGrid).
  - every MaterialInstanceConstant in those trees: parent, override state for
    TextureWeight / LayerA_TextureWeight / bLayerA_Active / Albedo / NormalMap / ORM /
    RoughnessMap / MetallicMap / HeightMap / EmissiveMap / BaseTint.
  - referencer counts for duplicate-mesh candidates (root-level <stem> vs <stem>/StaticMeshes/<stem>)
    and for every MI (to find unused duplicates).

Writes Saved/Audit/sweep_pbr_state.json.
Run via: UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript Content/Python/sweep_pbr_state.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved" / "Audit" / "sweep_pbr_state.json"

MESH_ROOTS = [
    "/Game/EnvSandbox/Meshes/Environment",
    "/Game/EnvSandbox/Library/Migrated",
    "/Game/Library/Migrated",
]
MI_PARAMS = [
    "TextureWeight", "LayerA_TextureWeight",
    "Albedo", "NormalMap", "ORM", "RoughnessMap", "MetallicMap", "HeightMap", "EmissiveMap",
]
VEC_PARAMS = ["BaseTint"]
SW_PARAMS = ["bLayerA_Active"]

BAD_MAT_MARKERS = ("WorldGridMaterial", "MI_Universal_", "/Game/EnvSandbox/Meshes/Environment/MI_Env", "ImportedPacks/MI_Env")


def asset_registry():
    return unreal.AssetRegistryHelpers.get_asset_registry()


def referencers(package_name: str) -> list:
    opts = unreal.AssetRegistryDependencyOptions(
        include_hard_package_references=True,
        include_soft_package_references=True,
        include_searchable_names=False,
        include_hard_management_references=True,
        include_soft_management_references=True,
    )
    try:
        return sorted(asset_registry().get_referencers(package_name, opts) or [])
    except Exception:
        return []


def mi_state(path: str) -> dict:
    a = unreal.load_asset(path)
    if not isinstance(a, unreal.MaterialInstanceConstant):
        return None
    lib = unreal.MaterialEditingLibrary
    info = {"path": path, "parent": ""}
    try:
        info["parent"] = a.parent.get_path_name() if a.parent else ""
    except Exception:
        pass
    state = {}
    for p in MI_PARAMS:
        try:
            v = lib.get_material_instance_scalar_parameter_value(a, p)
            ov = lib.get_material_instance_scalar_parameter_overridden(a, p)
        except Exception:
            v, ov = None, None
        state[p] = {"overridden": bool(ov), "value": v}
    for p in VEC_PARAMS:
        try:
            v = lib.get_material_instance_vector_parameter_value(a, p)
            ov = lib.get_material_instance_vector_parameter_overridden(a, p)
        except Exception:
            v, ov = None, None
        state[p] = {"overridden": bool(ov), "value": [round(x, 4) for x in v] if v else None}
    for p in SW_PARAMS:
        try:
            v = lib.get_material_instance_static_switch_parameter_value(a, p)
            ov = lib.get_material_instance_static_switch_parameter_overridden(a, p)
        except Exception:
            v, ov = None, None
        state[p] = {"overridden": bool(ov), "value": v}
    for p in ("Albedo", "NormalMap", "ORM", "RoughnessMap", "MetallicMap", "HeightMap", "EmissiveMap"):
        try:
            t = lib.get_material_instance_texture_parameter_value(a, p)
            state[p]["texture"] = t.get_path_name() if t else None
        except Exception:
            state[p]["texture"] = None
    info["params"] = state
    info["referencers"] = referencers(path.split(".")[0])
    return info


def mesh_state(path: str) -> dict:
    a = unreal.load_asset(path)
    if not isinstance(a, (unreal.StaticMesh, unreal.SkeletalMesh)):
        return None
    mats = getattr(a, "static_materials", None) or getattr(a, "materials", None) or []
    slots = []
    for i, s in enumerate(mats):
        mat = getattr(s, "material_interface", None)
        mat_path = mat.get_path_name() if mat else "NONE"
        slots.append({"i": i, "name": str(getattr(s, "material_slot_name", "")), "mat": mat_path})
    return {"path": path, "slots": slots}


def asset_class_name(path: str) -> str:
    try:
        d = unreal.EditorAssetLibrary.find_asset_data(path)
        if not d or not d.is_valid():
            return ""
        return str(d.asset_class_path.asset_name)
    except Exception:
        return ""


def main() -> int:
    ea = unreal.EditorAssetLibrary
    meshes, mics = [], []
    for root in MESH_ROOTS:
        if not ea.does_directory_exist(root):
            continue
        for p in ea.list_assets(root, recursive=True, include_folder=False):
            cls = asset_class_name(p)
            if cls in ("StaticMesh", "SkeletalMesh"):
                m = mesh_state(p)
                if m:
                    meshes.append(m)
            elif cls == "MaterialInstanceConstant":
                mi = mi_state(p)
                if mi:
                    mics.append(mi)

    dupes = {}
    env = "/Game/EnvSandbox/Meshes/Environment"
    if ea.does_directory_exist(env):
        for p in ea.list_assets(env, recursive=False, include_folder=False):
            stem = p.rsplit("/", 1)[-1].split(".")[0]
            twin = f"{env}/{stem}/StaticMeshes/{stem}"
            if ea.does_asset_exist(twin):
                dupes[p] = {"twin": twin, "root_refs": referencers(p.split(".")[0]), "twin_refs": referencers(twin.split(".")[0])}

    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mesh_count": len(meshes),
        "mi_count": len(mics),
        "meshes": meshes,
        "mics": mics,
        "duplicate_candidates": dupes,
        "bad_slots": [
            {"path": m["path"], "slot": s}
            for m in meshes for s in m["slots"]
            if s["mat"] == "NONE" or any(mark in s["mat"] for mark in BAD_MAT_MARKERS)
        ],
        "unfinished_mics": [
            mi for mi in mics
            if mi["params"]["LayerA_TextureWeight"].get("value") != 1.0
            or mi["params"]["bLayerA_Active"].get("value") is not True
            or (mi["params"]["Albedo"].get("overridden") and mi["params"]["Albedo"].get("texture") is None)
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, default=lambda o: str(o)), encoding="utf-8")
    print(f"meshes={len(meshes)} mics={len(mics)} bad_slots={len(report['bad_slots'])} "
          f"unfinished_mics={len(report['unfinished_mics'])} dupes={len(dupes)}")
    return 0


if __name__ == "__main__":
    import traceback
    print("SWEEP_PBR_STATE: SCRIPT STARTED", flush=True)
    crash = ROOT / "Saved" / "Audit" / "sweep_pbr_crash.txt"
    try:
        time.sleep(5)
        sys.exit(main())
    except Exception:
        tb = traceback.format_exc()
        print("SWEEP_PBR_STATE: CRASHED\n" + tb, flush=True)
        crash.write_text(tb, encoding="utf-8")
        sys.exit(2)
