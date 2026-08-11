"""Beavel Pro + native MOD_BEVEL hybrid bevel pipeline."""
from __future__ import annotations

import math

import bpy
import bmesh

from .capabilities import is_available


def _profile_map(props):
    ptype = getattr(props, "bevel_profile_type", "CONVEX")
    if ptype == "CHAMFER":
        return "SQUARE"
    if ptype == "CONCAVE":
        return "CONCAVE"
    return "ROUND"


def _select_sharp_edges(obj, angle_deg: float):
    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    sharp = math.radians(angle_deg)
    count = 0
    for edge in bm.edges:
        edge.select = False
        if not edge.is_manifold or len(edge.link_faces) != 2:
            continue
        n0 = edge.link_faces[0].normal
        n1 = edge.link_faces[1].normal
        dot = max(-1.0, min(1.0, n0.dot(n1)))
        if math.acos(dot) < sharp:
            edge.select = True
            count += 1
    bmesh.update_edit_mesh(obj.data)
    return count


def apply_beavel_destructive(obj, props) -> bool:
    """Run Beavel Pro on selected sharp edges (EDIT mode, destructive)."""
    if not is_available("beavel"):
        return False
    if obj is None or obj.type != "MESH":
        return False
    if getattr(props, "bevel_mode", "NONE") == "NONE":
        return False

    ctx = bpy.context
    prev_mode = obj.mode
    prev_active = ctx.view_layer.objects.active
    try:
        ctx.view_layer.objects.active = obj
        obj.select_set(True)
        if obj.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        n = _select_sharp_edges(obj, getattr(props, "bevel_angle_deg", 35.0))
        if n == 0:
            return False
        ths = 0.01 if getattr(props, "bevel_clamp_overlap", True) else 0.001
        bpy.ops.mesh.beavel_operator(
            prop_plen=max(0.001, getattr(props, "bevel_amount", 0.04)),
            prop_ths=ths,
            prop_merge=False,
            prop_mdist=0.04,
            prop_engine=1,
            prop_cut=max(1, getattr(props, "bevel_subdiv_level", 3)),
            prop_profile_type=_profile_map(props),
            prop_profile_segments=max(2, getattr(props, "bevel_subdiv_level", 3)),
        )
        return True
    except Exception as exc:
        print(f"[Surreal Architecture] Beavel failed: {exc}")
        return False
    finally:
        try:
            if obj.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
        except Exception:
            pass
        if prev_active:
            ctx.view_layer.objects.active = prev_active


def apply_modifier_bevel(obj, props, monolith=None) -> None:
    """Non-destructive MOD_BEVEL via original monolith helpers (not patched wrappers)."""
    if monolith is None:
        return
    mode = getattr(props, "bevel_mode", "NONE")
    if mode == "NONE":
        return
    if mode == "EDGE":
        fn = getattr(monolith, "_apply_edge_bevel_orig", None)
    else:
        fn = getattr(monolith, "_apply_bevel_addon_orig", None)
    if fn:
        fn(obj, props)


def apply_bevel(obj, props, *, backend="auto", monolith=None) -> str:
    """Apply bevel using backend: AUTO | BEAVEL | MODIFIER. Returns backend used."""
    if getattr(props, "bevel_mode", "NONE") == "NONE":
        return "none"
    if not getattr(props, "auto_bevel_on_generate", True) and backend == "auto":
        return "skipped"

    backend = (backend or "auto").upper()
    if backend == "AUTO":
        backend = getattr(props, "bevel_backend", "MODIFIER")

    if backend == "BEAVEL" and is_available("beavel"):
        if apply_beavel_destructive(obj, props):
            return "BEAVEL"
        backend = "MODIFIER"

    if backend in ("MODIFIER", "AUTO"):
        apply_modifier_bevel(obj, props, monolith)
        return "MODIFIER"
    return "none"
