"""Re-import and validate the emitted Melusina V2 skeletal FBX pieces.

This is intentionally a Blender-side audit.  The bind/export report proves
the in-memory contract rig; this tool proves the actual FBX payload contains
the canonical 465-bone armature and that every imported mesh is skinned to it.
It never saves the imported Blender scene or modifies the source stage.

Usage::

    blender --factory-startup --background --python \
      Tools/validate_melusina_v2_fbx_contract.py -- \
      --contract-bones specs/anim_presets/melusina_contract_bones.json \
      --fbx Exports/MelusinaClothes/V2/SK_Melusina_V2_Body.fbx

If --fbx is omitted, all five SK_Melusina_V2_*.fbx files are audited.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = PROJECT / "specs" / "anim_presets" / "melusina_contract_bones.json"
DEFAULT_ROOT = PROJECT / "Exports" / "MelusinaClothes" / "V2"
DEFAULT_REPORT = PROJECT / "Saved" / "Audit" / "melusina_v2_actual_fbx_contract_report.json"
EXPECTED_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
EXPECTED_BONES = 465
MIN_CM_PROBE_EXTENT = 5.0
# Small pieces such as boots can legitimately be under 50 cm on their
# shortest/overall axis.  Five centimetres is still safely above the v22
# meter-scale payloads while allowing a shoe/accessory export to pass when the
# armature probe proves the shared centimetre contract.
MIN_CM_MESH_EXTENT = 5.0
FORBIDDEN_MATERIAL_MARKERS = (
    "worldgrid", "world_grid", "placeholder", "v2test", "m_master", "marble"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-bones", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--fbx", action="append", default=[])
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


def read_contract(path: Path) -> tuple[set[str], dict[str, str | None]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    bones = data.get("bone_names")
    if not isinstance(bones, list) or not all(isinstance(item, str) for item in bones):
        raise ValueError(f"contract has no bone_names list: {path}")
    hierarchy_path = path.with_name("melusina_contract_hierarchy.json")
    hierarchy = json.loads(hierarchy_path.read_text(encoding="utf-8"))
    parent_map = {
        str(k): (None if v in (None, "") else str(v))
        for k, v in dict(hierarchy.get("parent_map", {})).items()
    }
    if set(parent_map) != set(bones):
        raise ValueError("canonical hierarchy does not exactly match contract bone_names")
    return set(bones), parent_map


def clear_imported_scene() -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def used_groups(mesh: bpy.types.Object) -> set[str]:
    used: set[str] = set()
    for vertex in mesh.data.vertices:
        for assignment in vertex.groups:
            if assignment.weight > 1.0e-7 and assignment.group < len(mesh.vertex_groups):
                used.add(mesh.vertex_groups[assignment.group].name)
    return used


def zero_weight_vertices(mesh: bpy.types.Object) -> int:
    return sum(
        1
        for vertex in mesh.data.vertices
        if sum(assignment.weight for assignment in vertex.groups) <= 1.0e-7
    )


def imported_armature(meshes: list[bpy.types.Object], armatures: list[bpy.types.Object]) -> bpy.types.Object | None:
    linked = []
    for mesh in meshes:
        for modifier in mesh.modifiers:
            if modifier.type == "ARMATURE" and modifier.object in armatures:
                linked.append(modifier.object)
    if linked:
        return max(set(linked), key=lambda item: len(item.data.bones))
    return max(armatures, key=lambda item: len(item.data.bones), default=None)


def audit_one(fbx_path: Path, contract: set[str], parent_map: dict[str, str | None]) -> dict:
    clear_imported_scene()
    entry = {
        "fbx": str(fbx_path),
        "ok": False,
        "errors": [],
        "warnings": [],
        "expected_skeleton": EXPECTED_SKELETON,
        "contract_bone_count": len(contract),
    }
    sidecar_path = fbx_path.with_suffix(".json")
    if not fbx_path.is_file():
        entry["errors"].append(f"FBX not found: {fbx_path}")
        return entry
    if not sidecar_path.is_file():
        entry["errors"].append(f"sidecar not found: {sidecar_path}")
    else:
        try:
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            entry["sidecar_exporter"] = sidecar.get("exporter")
            entry["sidecar_skeleton"] = sidecar.get("skeleton")
            entry["sidecar_morph_targets"] = sidecar.get("shape_key_count", 0)
            entry["sidecar_units"] = sidecar.get("units")
            entry["sidecar_cm_bake_factor"] = sidecar.get("cm_bake_factor")
            if not str(sidecar.get("exporter", "")).startswith("bpy.ops.arp."):
                entry["errors"].append("sidecar exporter is not the approved ARP operator")
            if sidecar.get("skeleton") != EXPECTED_SKELETON:
                entry["errors"].append("sidecar skeleton is not SK_Melusina_Skeleton")
            if sidecar.get("units") != "centimeters_baked":
                entry["errors"].append("sidecar does not prove baked centimeter coordinates")
            if float(sidecar.get("cm_bake_factor") or 0.0) != 100.0:
                entry["errors"].append("sidecar centimeter bake factor is not 100")
        except (OSError, json.JSONDecodeError) as exc:
            entry["errors"].append(f"invalid sidecar: {exc}")

    try:
        bpy.ops.import_scene.fbx(filepath=str(fbx_path), use_image_search=False)
    except Exception as exc:
        entry["errors"].append(f"FBX import failed: {exc}")
        return entry

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    rig = imported_armature(meshes, armatures)
    entry["imported_mesh_count"] = len(meshes)
    entry["imported_armature_count"] = len(armatures)
    entry["imported_armatures"] = [
        {"name": arm.name, "bone_count": len(arm.data.bones)} for arm in armatures
    ]
    if rig is None:
        entry["errors"].append("no imported armature found")
        return entry

    bone_names = {bone.name for bone in rig.data.bones}
    entry["actual_armature"] = rig.name
    entry["armature_object_scale"] = [float(value) for value in rig.scale]
    entry["actual_bone_count"] = len(bone_names)
    entry["dotted_bones"] = sorted(name for name in bone_names if "." in name)
    entry["missing_contract_bones"] = sorted(contract - bone_names)
    entry["unexpected_bones"] = sorted(bone_names - contract)
    root_shim = rig.name == "root" and "root" not in bone_names and len(bone_names) == EXPECTED_BONES - 1
    entry["root_shim"] = root_shim
    if len(bone_names) != EXPECTED_BONES and not root_shim:
        entry["errors"].append(f"actual armature has {len(bone_names)} bones, expected {EXPECTED_BONES}")
    if bone_names != contract and not root_shim:
        entry["errors"].append("actual FBX bone table does not exactly match the contract")
    if entry["dotted_bones"]:
        entry["errors"].append("actual FBX contains dotted bone names")
    actual_parent_map = {
        bone.name: (bone.parent.name if bone.parent else None)
        for bone in rig.data.bones
    }
    if root_shim:
        actual_parent_map["root"] = None
        for name, parent in list(actual_parent_map.items()):
            if parent is None and name != "root" and parent_map.get(name) == "root":
                actual_parent_map[name] = "root"
    entry["hierarchy_mismatches"] = sorted(
        name for name in contract if actual_parent_map.get(name) != parent_map.get(name)
    )
    if entry["hierarchy_mismatches"]:
        entry["errors"].append(
            f"actual FBX hierarchy differs from live UE contract ({len(entry['hierarchy_mismatches'])} bones)"
        )

    mesh_reports = []
    for mesh in meshes:
        used = used_groups(mesh)
        linked = [
            modifier.object.name
            for modifier in mesh.modifiers
            if modifier.type == "ARMATURE" and modifier.object is not None
        ]
        materials = [slot.material.name for slot in mesh.material_slots if slot.material]
        forbidden = sorted(
            material for material in materials
            if any(marker in material.lower() for marker in FORBIDDEN_MATERIAL_MARKERS)
        )
        mesh_entry = {
            "name": mesh.name,
            "vertices": len(mesh.data.vertices),
            "dimensions": [float(value) for value in mesh.dimensions],
            "object_scale": [float(value) for value in mesh.scale],
            "used_deform_groups": sorted(used),
            "unmatched_used_groups": sorted(used - contract),
            "zero_weight_vertices": zero_weight_vertices(mesh),
            "armature_modifiers": linked,
            "shape_key_count": len(mesh.data.shape_keys.key_blocks) if mesh.data.shape_keys else 0,
            "materials": materials,
            "forbidden_materials": forbidden,
        }
        mesh_reports.append(mesh_entry)
        if not linked:
            entry["errors"].append(f"{mesh.name}: no armature modifier")
        if mesh_entry["unmatched_used_groups"]:
            entry["errors"].append(f"{mesh.name}: unmatched used vertex groups")
        if mesh_entry["zero_weight_vertices"]:
            entry["errors"].append(f"{mesh.name}: zero-weight vertices")
        if forbidden:
            entry["errors"].append(f"{mesh.name}: forbidden placeholder materials {forbidden}")
        if max((abs(value) for value in mesh.dimensions), default=0.0) < MIN_CM_MESH_EXTENT:
            entry["errors"].append(
                f"{mesh.name}: mesh dimensions are meter-scale; expected baked centimeters"
            )
    entry["meshes"] = mesh_reports
    probe_bone = rig.data.bones.get("c_spine_02_x") or rig.data.bones.get("spine_02_x")
    if probe_bone:
        probe_extent = max(
            abs(float(value)) for value in (*probe_bone.head_local, *probe_bone.tail_local)
        )
        entry["spine_probe_bone"] = {
            "name": probe_bone.name,
            "head_local": [float(value) for value in probe_bone.head_local],
            "tail_local": [float(value) for value in probe_bone.tail_local],
            "length": float(probe_bone.length),
            "cm_probe_extent": probe_extent,
        }
        if probe_extent < MIN_CM_PROBE_EXTENT:
            entry["errors"].append(
                "spine probe is meter-scale; centimeter bind matrices were not baked"
            )
    else:
        entry["errors"].append("missing c_spine_02_x/spine_02_x centimeter probe")
    entry["actual_shape_key_count"] = sum(item["shape_key_count"] for item in mesh_reports)
    expected_morphs = int(entry.get("sidecar_morph_targets") or 0)
    if entry["actual_shape_key_count"] < expected_morphs:
        entry["errors"].append(
            f"morph targets lost during export: actual {entry['actual_shape_key_count']} "
            f"< sidecar proof {expected_morphs}"
        )
    entry["ok"] = not entry["errors"]
    return entry


def main() -> int:
    args = parse_args()
    contract, parent_map = read_contract(Path(args.contract_bones).resolve())
    paths = [Path(raw).resolve() for raw in args.fbx]
    if not paths:
        # *.arp.fbx is retained as ARP audit evidence, but is deliberately not
        # a gameplay candidate: ARP's M-ped output is not the 465-bone UE
        # contract.  Audit the five contract-finalized files only.
        paths = sorted(
            path for path in DEFAULT_ROOT.glob("SK_Melusina_V2_*.fbx")
            if not path.name.endswith(".arp.fbx")
        )
    report = {
        "schema": "melodia.melusina_v2_actual_fbx_contract_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": bool(paths) and len(paths) == 5,
        "expected_skeleton": EXPECTED_SKELETON,
        "contract_bone_count": len(contract),
        "fbx_count": len(paths),
        "checks": [],
    }
    if len(paths) != 5:
        report["errors"] = [f"expected five V2 FBXs, found {len(paths)}"]
    else:
        report["errors"] = []
    for path in paths:
        check = audit_one(path, contract, parent_map)
        report["checks"].append(check)
        report["ok"] = report["ok"] and check["ok"]
    report_path = Path(args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for check in report["checks"]:
        print(f"{'OK' if check['ok'] else 'FAIL'}: {Path(check['fbx']).name}")
        for error in check.get("errors", []):
            print(f"  ERROR: {error}")
    print(f"Report: {report_path}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
