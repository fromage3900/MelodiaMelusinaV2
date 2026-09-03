"""Non-destructive library instancing with metadata."""

from __future__ import annotations

import bpy


def stamp_instance_metadata(obj, *, role, style_key, lib_name, plan_name, plan_face=-1):
    obj["surreal_world_role"] = role
    obj["surreal_compose_style"] = style_key
    obj["surreal_lib_piece"] = lib_name
    obj["surreal_composed_from"] = plan_name
    if plan_face >= 0:
        obj["surreal_plan_face"] = int(plan_face)


def create_instance_root(plan_obj, style_key):
    root_name = f"{plan_obj.name}_WorldRoot"
    existing = bpy.data.objects.get(root_name)
    if existing:
        for child in list(existing.children):
            bpy.data.objects.remove(child, do_unlink=True)
        root = existing
    else:
        root = bpy.data.objects.new(root_name, None)
        root.empty_display_type = "PLAIN_AXES"
        root.empty_display_size = 1.0
        bpy.context.scene.collection.objects.link(root)
    root.location = plan_obj.matrix_world.translation.copy()
    root["surreal_composed_from"] = plan_obj.name
    root["surreal_compose_style"] = style_key
    root["surreal_compose_mode"] = "COLLECTION"
    plan_obj["surreal_world_root"] = root.name
    return root


def instance_library_piece(
    lib_obj,
    location,
    rotation_z=0.0,
    scale=1.0,
    scale_xyz=None,
    link_to_coll=None,
    name_hint="instance",
    material=None,
    parent=None,
    metadata=None,
):
    """Link shared mesh data via parent empty (wall stretch on empty scale.x)."""
    if lib_obj is None or lib_obj.data is None:
        return None

    lib_slug = lib_obj.name[5:] if lib_obj.name.startswith("_lib_") else lib_obj.name
    root = bpy.data.objects.new(f"{name_hint}_{lib_slug}", None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.25
    root.location = location
    root.rotation_euler = (0.0, 0.0, rotation_z)
    if scale_xyz:
        root.scale = scale_xyz
    else:
        root.scale = (scale, scale, scale)

    inst = bpy.data.objects.new(f"{name_hint}_{lib_slug}_mesh", lib_obj.data)
    inst.parent = root
    inst.matrix_parent_inverse = root.matrix_world.inverted()

    target = link_to_coll or bpy.context.scene.collection
    if parent is not None:
        root.parent = parent
        root.matrix_parent_inverse = parent.matrix_world.inverted()
    target.objects.link(root)
    target.objects.link(inst)

    if material is not None:
        if inst.data.materials:
            inst.data.materials[0] = material
        else:
            inst.data.materials.append(material)

    if metadata:
        stamp_instance_metadata(inst, **metadata)
        stamp_instance_metadata(root, **metadata)

    return root


def iter_world_instances(world_root):
    if world_root is None:
        return
    for child in world_root.children:
        for obj in (child,) + tuple(child.children):
            if obj.type == "MESH" and obj.get("surreal_world_role"):
                yield obj


def clear_composed_world(plan_obj):
    root_name = plan_obj.get("surreal_world_root")
    if root_name:
        root = bpy.data.objects.get(root_name)
        if root:
            for child in list(root.children):
                for sub in list(child.children):
                    bpy.data.objects.remove(sub, do_unlink=True)
                bpy.data.objects.remove(child, do_unlink=True)
            return root
    coll = bpy.data.collections.get(f"{plan_obj.name}_Composed")
    if coll:
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    legacy = bpy.data.objects.get(f"{plan_obj.name}_World")
    if legacy:
        bpy.data.objects.remove(legacy, do_unlink=True)
    return None
