"""Plan vertex-group tagging conventions."""

from __future__ import annotations

TAG_COLORS = {
    "is_keep": (0.95, 0.75, 0.25, 1.0),
    "is_corner_tower": (0.35, 0.55, 0.95, 1.0),
    "is_gate": (0.95, 0.35, 0.30, 1.0),
    "is_plaza": (0.60, 0.90, 0.40, 1.0),
    "is_sacred": (0.85, 0.55, 0.95, 1.0),
}


def vertex_in_group(obj, vert_idx, group_name):
    vg = obj.vertex_groups.get(group_name)
    if vg is None:
        return False
    try:
        for g in obj.data.vertices[vert_idx].groups:
            if g.group == vg.index and g.weight > 0.5:
                return True
    except Exception:
        pass
    return False


def face_role_from_tags(plan_obj, face, default_by_area_fn):
    for v_idx in face.vertices:
        if vertex_in_group(plan_obj, v_idx, "is_sacred"):
            return "sacred"
        if vertex_in_group(plan_obj, v_idx, "is_keep"):
            return "large"
        if vertex_in_group(plan_obj, v_idx, "is_plaza"):
            return "monument"
    return default_by_area_fn(face)
