"""
FV2 accordion skirt: align + lightweight Cloth (no ARMATURE_AUTO).

Blender 5.1 / Melodia stage. Prefer MCP chunked calls — ARMATURE_AUTO on 40k
verts freezes the session. This script:
  1) Aligns FV2 mesh to Melusina hips
  2) Parents with KEEP_TRANSFORM (no deform weights yet)
  3) Builds Pin VG (top verts) + Cloth modifier
  4) Adds Collision on Melusina_Skirt / body mesh
  5) Sets cache range — does NOT bake_all (scrub Timeline instead)

Optional later: Tools/bind_fv2_skirt_weights.py or Data Transfer weights.

Usage (Text Editor in open 5.1 stage, or MCP execute_blender_code):
  exec(open(r"G:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\setup_fv2_skirt_cloth.py").read())
"""
from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
AUDIT = ROOT / "Saved" / "Audit" / "fv2_skirt_cloth_setup.json"
FV2_NAMES = ("Wardrobe_fv2_accordion", "FV2_Accordion_Skirt")
CACHE_START = 1
CACHE_END = 48


def _log(msg: str) -> None:
    print(f"[fv2_cloth] {msg}")


def _find_fv2() -> bpy.types.Object | None:
    for name in FV2_NAMES:
        obj = bpy.data.objects.get(name)
        if obj and obj.type == "MESH":
            return obj
    for obj in bpy.data.objects:
        if obj.type == "MESH" and "fv2" in obj.name.lower() and "accordion" in obj.name.lower():
            return obj
    return None


def _find_character_rig() -> bpy.types.Object | None:
    for name in ("character_rig", "FinalUERig43"):
        obj = bpy.data.objects.get(name)
        if obj and obj.type == "ARMATURE":
            return obj
    return None


def _find_collision_mesh() -> bpy.types.Object | None:
    for name in ("Melusina_Skirt", "simply_coll", "Body", "body", "Melusina_Body"):
        obj = bpy.data.objects.get(name)
        if obj and obj.type == "MESH":
            return obj
    rig = _find_character_rig()
    if not rig:
        return None
    for child in rig.children_recursive:
        if child.type == "MESH" and "hair" not in child.name.lower() and "shp" not in child.name.lower():
            return child
    return None


def _hips_world(rig: bpy.types.Object) -> Vector:
    for bname in ("hips", "pelvis", "root", "spine", "spine_01"):
        if bname in rig.pose.bones:
            return rig.matrix_world @ rig.pose.bones[bname].head
        for pb in rig.pose.bones:
            if bname in pb.name.lower():
                return rig.matrix_world @ pb.head
    return rig.matrix_world.translation.copy()


def align_skirt(skirt: bpy.types.Object, rig: bpy.types.Object) -> dict:
    hips = _hips_world(rig)
    deps = bpy.context.evaluated_depsgraph_get()
    ev = skirt.evaluated_get(deps)
    corners = [skirt.matrix_world @ Vector(c) for c in ev.bound_box]
    top_z = max(c.z for c in corners)
    cx = sum(c.x for c in corners) / 8.0
    cy = sum(c.y for c in corners) / 8.0
    delta = Vector((hips.x - cx, hips.y - cy, hips.z - top_z + 0.02))
    skirt.location += delta
    bpy.context.view_layer.update()
    return {"hips": list(hips), "delta": list(delta), "top_z_before": top_z}


def parent_keep(skirt: bpy.types.Object, rig: bpy.types.Object) -> None:
    if skirt.parent == rig:
        return
    skirt.parent = rig
    skirt.parent_type = "OBJECT"
    skirt.matrix_parent_inverse = rig.matrix_world.inverted()


def ensure_pin_vg(skirt: bpy.types.Object, top_fraction: float = 0.18) -> str:
    mesh = skirt.data
    zs = [v.co.z for v in mesh.vertices]
    z_min, z_max = min(zs), max(zs)
    span = max(z_max - z_min, 1e-6)
    threshold = z_max - span * top_fraction
    vg = skirt.vertex_groups.get("Pin") or skirt.vertex_groups.new(name="Pin")
    pin_idx = [v.index for v in mesh.vertices if v.co.z >= threshold]
    loose = [v.index for v in mesh.vertices if v.index not in set(pin_idx)]
    if pin_idx:
        vg.add(pin_idx, 1.0, "REPLACE")
    if loose:
        vg.add(loose, 0.0, "REPLACE")
    _log(f"Pin VG: {len(pin_idx)} pinned / {len(mesh.vertices)} verts (z>={threshold:.4f})")
    return "Pin"


def ensure_cloth(skirt: bpy.types.Object, pin_name: str) -> None:
    cloth = next((m for m in skirt.modifiers if m.type == "CLOTH"), None)
    if cloth is None:
        cloth = skirt.modifiers.new(name="Cloth", type="CLOTH")
    settings = cloth.settings
    settings.quality = 8
    settings.time_scale = 1.0
    settings.mass = 0.25
    settings.air_damping = 1.0
    if hasattr(settings, "vertex_group_mass"):
        settings.vertex_group_mass = pin_name
    if hasattr(settings, "pin_stiffness"):
        settings.pin_stiffness = 1.0
    # Soft cloth for accordion pleats
    if hasattr(settings, "tension_stiffness"):
        settings.tension_stiffness = 12.0
    if hasattr(settings, "compression_stiffness"):
        settings.compression_stiffness = 12.0
    if hasattr(settings, "bending_stiffness"):
        settings.bending_stiffness = 0.4
    if hasattr(settings, "shear_stiffness"):
        settings.shear_stiffness = 12.0
    coll = cloth.collision_settings
    coll.use_collision = True
    coll.distance_min = 0.004
    coll.self_distance_min = 0.003
    coll.collision_quality = 3
    cache = cloth.point_cache
    cache.frame_start = CACHE_START
    cache.frame_end = CACHE_END
    _log(f"Cloth ready cache {CACHE_START}-{CACHE_END} (scrub Timeline; do not bake_all via MCP)")


def ensure_body_collision(body: bpy.types.Object | None) -> bool:
    if body is None:
        return False
    if not any(m.type == "COLLISION" for m in body.modifiers):
        body.modifiers.new(name="Collision", type="COLLISION")
    if hasattr(body, "collision") and body.collision:
        body.collision.thickness_outer = 0.012
        body.collision.thickness_inner = 0.2
    _log(f"Collision on {body.name}")
    return True


def main() -> dict:
    skirt = _find_fv2()
    if skirt is None:
        raise RuntimeError("FV2 skirt mesh not found (Wardrobe_fv2_accordion)")
    rig = _find_character_rig()
    if rig is None:
        raise RuntimeError("character_rig / FinalUERig43 not found")
    body = _find_collision_mesh()

    align = align_skirt(skirt, rig)
    parent_keep(skirt, rig)
    pin = ensure_pin_vg(skirt)
    ensure_cloth(skirt, pin)
    coll_ok = ensure_body_collision(body)

    result = {
        "skirt": skirt.name,
        "rig": rig.name,
        "collision_mesh": body.name if body else None,
        "collision_ok": coll_ok,
        "align": align,
        "pin_group": pin,
        "vertex_groups": [g.name for g in skirt.vertex_groups],
        "modifiers": [m.type for m in skirt.modifiers],
        "cache": [CACHE_START, CACHE_END],
        "note": "No ARMATURE_AUTO (too heavy). Parent KEEP_TRANSFORM + Cloth Pin. Scrub 1-48. Bind weights later if needed.",
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _log(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
