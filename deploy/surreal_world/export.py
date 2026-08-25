"""UE world manifest export - surreal_arch_world_v1."""

from __future__ import annotations

import json
import os
import sys
import logging
# --factory-startup strips site-packages; re-add standard paths
import site as _site_mod
_site_mod.addsitedir(_site_mod.getusersitepackages())
_site_mod.addsitedir(os.path.abspath(os.path.join(os.path.dirname(sys.executable), '..', 'Lib', 'site-packages')))
import jsonschema
from pathlib import Path
from datetime import datetime, timezone

import bpy
from mathutils import Matrix

FORMAT_ID = "surreal_arch_world_v1"
SCHEMA_VERSION = 1
COORDINATE_SYSTEM = "blender_z_up"

MATERIALS_ROOT = "/Game/EnvSandbox/Materials/Instances/Environment"

ROLE_UE_HINTS = {
    "large": f"{MATERIALS_ROOT}/Stylized/MI_Show_StoneCliff",
    "medium": f"{MATERIALS_ROOT}/Stylized/MI_Show_Default",
    "small": f"{MATERIALS_ROOT}/Stylized/MI_Show_Default",
    "wall": f"{MATERIALS_ROOT}/Stylized/MI_Trimsheet_HeavyWear",
    "corner_tower": f"{MATERIALS_ROOT}/Stylized/MI_Show_StoneCliff",
    "gate": f"{MATERIALS_ROOT}/Stylized/MI_Show_ContactRimHero",
    "monument": f"{MATERIALS_ROOT}/Stylized/MI_Show_StoneCliff",
    "sacred": f"{MATERIALS_ROOT}/Zen/MI_Zen_Karesansui",
    "joined_mesh": f"{MATERIALS_ROOT}/Stylized/MI_Show_Default",
}

STYLE_ROLE_OVERRIDES = {
    "ZEN_SHRINE": {
        "gate": f"{MATERIALS_ROOT}/Zen/MI_Zen_ToriiVermillion",
        "sacred": f"{MATERIALS_ROOT}/Zen/MI_Zen_HondenSanctum",
        "large": f"{MATERIALS_ROOT}/Zen/MI_Zen_MossGarden",
        "monument": f"{MATERIALS_ROOT}/Zen/MI_Zen_SakuraDrift",
    },
}

logger = logging.getLogger(__name__)


def material_hint(style, role):
    overrides = STYLE_ROLE_OVERRIDES.get(style, {})
    return overrides.get(role, ROLE_UE_HINTS.get(role, f"{MATERIALS_ROOT}/Stylized/MI_Show_Default"))


def _matrix_list(obj):
    m = obj.matrix_world
    return [list(row) for row in m]


def find_world_root(obj):
    if obj is None:
        return None
    if obj.type == "EMPTY" and obj.get("surreal_composed_from"):
        return obj
    root_name = obj.get("surreal_world_root")
    if root_name:
        return bpy.data.objects.get(root_name)
    src = obj.get("surreal_composed_from")
    if src:
        plan = bpy.data.objects.get(src)
        if plan and plan.get("surreal_world_root"):
            return bpy.data.objects.get(plan["surreal_world_root"])
    return None


def build_hism_groups(instances):
    """Group instances by (role, lib) for UE HISM placement."""
    groups = {}
    for entry in instances:
        key = (entry["role"], entry["lib"])
        if key not in groups:
            groups[key] = {
                "role": entry["role"],
                "lib": entry["lib"],
                "ue_material_hint": entry.get("ue_material_hint", ""),
                "static_mesh_path": entry.get("static_mesh_path", ""),
                "instance_count": 0,
                "transforms": [],
            }
        groups[key]["transforms"].append(entry["transform"])
        groups[key]["instance_count"] += 1
    return list(groups.values())


def validate_manifest(payload):
    """Validate the manifest against the JSON‑Schema.
    Returns a list of error messages (empty list means the manifest is valid)."""
    schema_path = Path(__file__).resolve().parents[2] / "Config" / "world_schema.json"
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        return ["schema file missing"]
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft7Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(payload), key=str):
        errors.append(error.message)
    return errors


def build_world_manifest(world_root, monolith=None):
    from . import instance

    if world_root is None:
        return None
    plan_name = world_root.get("surreal_composed_from", "")
    style = world_root.get("surreal_compose_style", "")
    genome_id = world_root.get("surreal_style_genome_id", "")
    style_genome = {}
    if monolith is not None or genome_id:
        try:
            import sys
            import os
            deploy = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if deploy not in sys.path:
                sys.path.insert(0, deploy)
            from surreal_os.genome import resolve_genome_manifest
            style_genome = resolve_genome_manifest(monolith, style, genome_id or None)
            if style_genome and monolith is not None:
                try:
                    from .compose import resolve_compose_style
                    compose_style = style_genome.get("compose_style") or style
                    gid = style_genome.get("id")
                    saved_genome = getattr(monolith, "_active_style_genome", None)
                    try:
                        if gid:
                            from surreal_os.genome import load_genome
                            monolith._active_style_genome = load_genome(gid)
                        roles = resolve_compose_style(monolith, compose_style)
                        if roles:
                            style_genome = dict(style_genome)
                            style_genome["resolved_compose_roles"] = dict(roles)
                    finally:
                        monolith._active_style_genome = saved_genome
                except Exception as exc:
                    print(f"[SurrealWorld] resolved_compose_roles skipped: {exc}")
        except Exception as exc:
            print(f"[SurrealWorld] style_genome embed skipped: {exc}")
    entries = []
    collections = []
    for inst in instance.iter_world_instances(world_root):
        role = inst.get("surreal_world_role", "unknown")
        entries.append({
            "role": role,
            "lib": inst.get("surreal_lib_piece", ""),
            "object": inst.name,
            "plan_face": inst.get("surreal_plan_face", -1),
            "transform": _matrix_list(inst),
            "ue_material_hint": material_hint(style, role),
            "static_mesh_path": "",
        })
        for c in inst.users_collection:
            if c.name not in collections:
                collections.append(c.name)
    payload = {
        "format": FORMAT_ID,
        "schema_version": SCHEMA_VERSION,
        "coordinate_system": COORDINATE_SYSTEM,
        "style": style,
        "plan": plan_name,
        "world_root": world_root.name,
        "compose_mode": world_root.get("surreal_compose_mode", "COLLECTION"),
        "instance_count": len(entries),
        "instances": entries,
        "hism_groups": build_hism_groups(entries),
        "collections": collections,
    }
    if style_genome:
        payload["style_genome"] = style_genome
    return payload


def write_world_manifest(obj, filepath=None, monolith=None):
    root = find_world_root(obj)
    if root is None and obj and obj.type == "MESH":
        style = obj.get("surreal_compose_style", "")
        payload = {
            "format": FORMAT_ID,
            "schema_version": SCHEMA_VERSION,
            "coordinate_system": COORDINATE_SYSTEM,
            "style": style,
            "plan": obj.get("surreal_composed_from", ""),
            "world_root": obj.name,
            "compose_mode": "JOINED",
            "instance_count": 1,
            "instances": [{
                "role": "joined_mesh",
                "lib": "",
                "object": obj.name,
                "transform": _matrix_list(obj),
                "ue_material_hint": material_hint(style, "joined_mesh"),
                "static_mesh_path": "",
            }],
            "hism_groups": [],
            "collections": [c.name for c in obj.users_collection],
        }
    else:
        payload = build_world_manifest(root, monolith=monolith)
    if payload is None:
        return None
    errors = validate_manifest(payload)
    if errors:
        print(f"[SurrealWorld] manifest validation warnings: {errors}")
    if filepath is None:
        base = bpy.path.abspath("//")
        filepath = os.path.join(base, f"{payload.get('world_root', 'world')}.world.json")
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return filepath


def export_role_fbx_batches(context, world_root, out_dir=None):
    """Export one FBX per role group (best-effort)."""
    from . import instance

    if out_dir is None:
        out_dir = bpy.path.abspath("//WorldExport")
    os.makedirs(out_dir, exist_ok=True)
    by_role = {}
    for inst in instance.iter_world_instances(world_root):
        by_role.setdefault(inst.get("surreal_world_role", "misc"), []).append(inst)
    exported = []
    for role, objs in by_role.items():
        if not objs:
            continue
        fbx_path = os.path.join(out_dir, f"World_{role}.fbx")
        for o in context.view_layer.objects:
            o.select_set(False)
        for o in objs:
            o.select_set(True)
        context.view_layer.objects.active = objs[0]
        try:
            bpy.ops.export_scene.fbx(
                filepath=fbx_path,
                use_selection=True,
                apply_scale_options="FBX_SCALE_ALL",
            )
            if os.path.isfile(fbx_path):
                exported.append(fbx_path)
        except Exception as e:
            print(f"[SurrealWorld] FBX export {role}: {e}")
    return exported
