"""Bake trim-group metadata onto mesh attributes for UE FBX export."""

from __future__ import annotations

import json

# Stable integer IDs for vertex-color / face-attribute trim assignment in UE
TRIM_COLOR_MAP = {
    "wall_panel_recess": 1,
    "floor_ledge": 2,
    "ceiling_slab": 3,
    "colonette": 4,
    "impost_block": 5,
    "arch_ring": 6,
    "barrel_vault": 7,
    "apse_shell": 8,
    "pilaster": 9,
    "recess_panel": 10,
    "baseboard": 11,
    "bifora_void": 12,
    "cornice_shelf": 13,
    "sill_band": 14,
    "gasket_ring": 15,
    "pressure_frame": 16,
    "door_void": 17,
    "door_frame": 18,
    "window_reveal": 19,
    "wainscot": 20,
    "water_gate": 21,
    "canal_wall": 22,
}

LAYER_NAME = "trim_id"


def _trim_id_for_groups(trim_groups):
    """Pick dominant trim id (first group) for whole-mesh tagging when zones unknown."""
    if not trim_groups:
        return 0
    gid = trim_groups[0].get("id", "")
    return TRIM_COLOR_MAP.get(gid, 1)


def apply_trim_bake(obj, props, monolith=None):
    """Write trim_id vertex color layer + face attribute from surreal_trim_groups metadata."""
    from .snap_export import build_trim_groups

    raw = obj.get("surreal_trim_groups")
    if raw:
        try:
            groups = json.loads(raw) if isinstance(raw, str) else list(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            groups = build_trim_groups(props, monolith)
    else:
        groups = build_trim_groups(props, monolith)

    if not groups:
        return False

    mesh = obj.data
    if mesh is None or not hasattr(mesh, "vertices"):
        return False

    if getattr(props, "gb_bake_trim_colors", False):
        from .trim_color_bake import bake_trim_vertex_colors

        painted = bake_trim_vertex_colors(obj, props, monolith)
        has_layer = "SURREAL_TRIM" in getattr(mesh, "color_attributes", {})
        if painted > 0 and has_layer:
            obj["surreal_trim_bake"] = json.dumps({
                "layer": "SURREAL_TRIM",
                "mode": "per_face_zones",
                "groups": [g.get("id") for g in groups],
                "painted_loops": painted,
                "ue_hint": "Read CORNER color layer SURREAL_TRIM for per-zone trim sheets",
            })
            mesh.update()
            return True

    trim_id = _trim_id_for_groups(groups)
    norm = trim_id / 255.0 if trim_id else 0.0

    if not mesh.vertex_colors:
        mesh.vertex_colors.new(name=LAYER_NAME)
    vcol = mesh.vertex_colors.get(LAYER_NAME) or mesh.vertex_colors[0]
    vcol.name = LAYER_NAME

    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vcol.data[li].color = (norm, norm, norm, 1.0)

    try:
        if "trim_id" not in mesh.attributes:
            mesh.attributes.new(name="trim_id", type="INT", domain="FACE")
        attr = mesh.attributes["trim_id"]
        for i in range(len(mesh.polygons)):
            attr.data[i].value = trim_id
    except Exception:
        pass

    obj["surreal_trim_bake"] = json.dumps({
        "layer": LAYER_NAME,
        "trim_id": trim_id,
        "groups": [g.get("id") for g in groups],
        "ue_hint": "Read vertex color R channel or face attribute trim_id for material slot",
    })
    mesh.update()
    return True
