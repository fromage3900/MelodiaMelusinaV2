"""Bake trim-group IDs into vertex colors for FBX / UE export."""

from __future__ import annotations

import bpy

from .snap_export import build_trim_groups

TRIM_ATTR = "surreal_trim_id"
TRIM_ZONE_ATTR = "surreal_trim_zone"
COLOR_LAYER = "SURREAL_TRIM"
BODY_RGBA = (0.08, 0.08, 0.09, 1.0)
TRIM_PALETTE = (
    BODY_RGBA,
    (1.0, 0.35, 0.05, 1.0),
    (0.25, 0.85, 1.0, 1.0),
    (0.95, 0.25, 0.65, 1.0),
    (0.45, 1.0, 0.35, 1.0),
    (1.0, 0.85, 0.2, 1.0),
    (0.65, 0.45, 1.0, 1.0),
)


def trim_color_for_index(order_index, n_groups):
    slots = max(1, min(n_groups, len(TRIM_PALETTE) - 1))
    slot = (order_index % slots) + 1
    return TRIM_PALETTE[slot]


def reset_trim_zones(monolith):
    monolith._trim_zone_seq = 0


def count_eval_trim_zone_faces(obj):
    """Count evaluated mesh faces with surreal_trim_zone > 0 (GN trim stamp QA)."""
    import bpy

    if obj is None or obj.type != "MESH":
        return 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    try:
        zone_attr = me.attributes.get(TRIM_ZONE_ATTR)
        if zone_attr is None or zone_attr.domain != "FACE":
            return 0
        return sum(1 for item in zone_attr.data if float(item.value) > 0.5)
    finally:
        ev.to_mesh_clear()


def resolve_trim_zone(monolith, label, props=None):
    """Map _gb_box label to per-face trim zone id (1-based)."""
    if label == "trim":
        seq = getattr(monolith, "_trim_zone_seq", 0) + 1
        monolith._trim_zone_seq = seq
        return float(seq)
    if not label.startswith("trim:"):
        return None
    suffix = label[5:].strip()
    if suffix.isdigit():
        return float(suffix)
    if props is not None:
        groups = build_trim_groups(props, monolith)
        for idx, grp in enumerate(groups, start=1):
            if grp.get("id") == suffix or grp.get("role") == suffix:
                return float(idx)
    return 1.0


def tag_face_trim_attrs(monolith, tree, geom, x, y, zone_value=0.0, trim_flag=0.0):
    """Store per-face trim zone + trim flag on GN geometry (all faces for JoinGeometry parity)."""
    if geom is None:
        return None
    out = geom
    for attr_name, value in ((TRIM_ZONE_ATTR, zone_value), (TRIM_ATTR, trim_flag)):
        store = monolith._safe_node(tree, "GeometryNodeStoreNamedAttribute", (x + 420, y))
        if store is None:
            continue
        store.domain = "FACE"
        try:
            store.data_type = "FLOAT"
        except Exception:
            pass
        try:
            store.inputs["Name"].default_value = attr_name
            store.inputs["Value"].default_value = float(value)
        except Exception:
            continue
        monolith._link(tree, out, store.inputs["Geometry"])
        out = store.outputs["Geometry"]
        y += 80
    return out


def tag_trim_geometry(monolith, tree, geom, x, y, trim_value=1.0):
    """Store trim zone id + trim flag=1 on trim-labelled geometry."""
    return tag_face_trim_attrs(monolith, tree, geom, x, y, zone_value=trim_value, trim_flag=1.0)


def bake_trim_vertex_colors(obj, props, monolith=None):
    """Copy surreal_trim_id face attribute to CORNER color layer SURREAL_TRIM."""
    if not getattr(props, "gb_bake_trim_colors", False):
        return 0
    if obj is None or obj.type != "MESH":
        return 0

    groups = build_trim_groups(props, monolith)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    painted = 0
    mesh = obj.data
    source_mesh = mesh
    if not mesh.polygons:
        baked_mesh = bpy.data.meshes.new_from_object(eval_obj, depsgraph=depsgraph)
        if not baked_mesh.polygons:
            return 0
        obj.data = baked_mesh
        mesh = baked_mesh
        source_mesh = baked_mesh
    elif any(m.type == "NODES" for m in obj.modifiers):
        baked_mesh = bpy.data.meshes.new_from_object(eval_obj, depsgraph=depsgraph)
        if baked_mesh.polygons:
            obj.data = baked_mesh
            mesh = baked_mesh
            source_mesh = baked_mesh

    try:
        attr = source_mesh.attributes.get(TRIM_ATTR)
        if COLOR_LAYER not in mesh.color_attributes:
            mesh.color_attributes.new(name=COLOR_LAYER, type="BYTE_COLOR", domain="CORNER")
        colors = mesh.color_attributes[COLOR_LAYER]

        zone_attr = source_mesh.attributes.get(TRIM_ZONE_ATTR)
        trim_faces = []
        face_zones = {}
        if attr is not None and attr.domain == "FACE":
            for i, item in enumerate(attr.data):
                if float(item.value) > 0.5:
                    trim_faces.append(i)
        if zone_attr is not None and zone_attr.domain == "FACE":
            for i, item in enumerate(zone_attr.data):
                zone = int(round(float(item.value)))
                if zone > 0:
                    face_zones[i] = zone

        if not trim_faces and not face_zones:
            return 0

        trim_rank = {fid: idx for idx, fid in enumerate(trim_faces)}
        for poly in mesh.polygons:
            if poly.index in face_zones:
                rgba = trim_color_for_index(face_zones[poly.index] - 1, len(groups) or 8)
            elif poly.index in trim_rank:
                rgba = trim_color_for_index(trim_rank[poly.index], len(groups) or len(trim_faces))
            else:
                rgba = BODY_RGBA
            for li in poly.loop_indices:
                colors.data[li].color = rgba
                painted += 1
    except Exception:
        return 0

    if painted == 0:
        return 0

    obj["surreal_trim_color_layer"] = COLOR_LAYER
    obj["surreal_trim_color_count"] = len(groups)
    return painted
