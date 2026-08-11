"""Central rules — snap pairing, compose roles, surreal transforms."""

from __future__ import annotations

from mathutils import Vector

from ._io import load_data


def snap_compat_table() -> set[tuple[str, str]]:
    data = load_data("rules", "snap_compat.json")
    pairs = data.get("compatible_pairs") or []
    return {tuple(p) for p in pairs}


def must_connect_bonus() -> float:
    data = load_data("rules", "snap_compat.json")
    return float(data.get("must_connect_bonus", 6.0))


def min_align_dot() -> float:
    data = load_data("rules", "snap_compat.json")
    return float(data.get("min_align_dot", -0.35))


def best_snap_pair(monolith, obj_a, obj_b):
    """Drop-in compatible with greybox_graph.best_snap_pair using OS rules file."""
    pts_a = monolith._gb_load_snap_points(obj_a)
    pts_b = monolith._gb_load_snap_points(obj_b)
    if not pts_a or not pts_b:
        return None
    compatible = snap_compat_table()
    best = None
    best_score = -1e9
    bonus = must_connect_bonus()
    min_dot = min_align_dot()
    for pa in pts_a:
        for pb in pts_b:
            key = (pa.get("type"), pb.get("type"))
            if key not in compatible and pa.get("type") != pb.get("type"):
                continue
            da = monolith._gb_snap_world_dir(obj_a, pa)
            db = monolith._gb_snap_world_dir(obj_b, pb)
            align = da.dot(db)
            if align > min_dot:
                continue
            wa = monolith._gb_snap_world_point(obj_a, pa)
            wb = monolith._gb_snap_world_point(obj_b, pb)
            dist = (wa - wb).length
            score = -dist + abs(align) * 3.0
            if pa.get("rule") == "MUST_CONNECT":
                score += bonus
            if pb.get("rule") == "MUST_CONNECT":
                score += bonus
            if score > best_score:
                best_score = score
                best = (pa, pb, wa, wb)
    return best


def load_compose_styles() -> dict:
    data = load_data("rules", "compose_roles.json")
    return dict(data.get("styles") or {})


def load_compose_fallbacks() -> dict:
    data = load_data("rules", "compose_roles.json")
    return dict(data.get("fallbacks") or {})


def get_transform(transform_id: str) -> dict | None:
    data = load_data("surreal_transforms.json")
    return (data.get("transforms") or {}).get(transform_id)


def apply_surreal_transform(objs, transform_id: str, genome: dict | None = None, graph_id: str | None = None):
    """Apply post-spawn transform to object chain."""
    if not objs or not transform_id:
        return
    spec = get_transform(transform_id)
    if not spec:
        return
    applies = spec.get("applies_to") or []
    if applies and graph_id and graph_id not in applies:
        return
    ttype = spec.get("type")
    params = spec.get("params") or {}
    if ttype == "graph_wrap":
        axis = params.get("axis", "Z").upper()
        scale_min = float(params.get("scale_min", 0.92))
        scale_max = float(params.get("scale_max", 1.12))
        v = 0.85
        if genome:
            key = params.get("scale_from_genome", "verticality")
            v = float(genome.get(key, v))
        scale = scale_min + (scale_max - scale_min) * v
        for i, obj in enumerate(objs):
            t = 1.0 + (scale - 1.0) * (i / max(len(objs) - 1, 1))
            if axis == "Z":
                obj.scale.z *= t
            elif axis == "Y":
                obj.scale.y *= t
            else:
                obj.scale.x *= t
    elif ttype == "modifier":
        decay = float(params.get("scale_decay", 0.85))
        depth = max(1, int(params.get("depth", 3)))
        influence = float(genome.get("cosmic_influence", 0.5)) if genome else 0.5
        for i, obj in enumerate(objs):
            step = min(i, depth - 1)
            s = decay ** step * (1.0 + influence * 0.08)
            obj.scale = (obj.scale.x * s, obj.scale.y * s, obj.scale.z * s)
