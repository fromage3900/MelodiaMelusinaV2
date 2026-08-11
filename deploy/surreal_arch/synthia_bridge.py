"""Synthia math→geometry spawn bridge."""
from __future__ import annotations

import bpy
import bmesh

from .capabilities import is_available

SYNTHIA_ARCH_MAP = {
    "SYNTHIA_TORUS_KNOT": ("torus_knot", "EQUATION"),
    "SYNTHIA_MOBIUS": ("mobius", "EQUATION"),
    "SYNTHIA_LORENZ": ("lorenz", "EQUATION"),
    "SYNTHIA_PLATONIC": ("platonic_solids", "GEOMETRY"),
}

TAG_KEY = "surreal_synthia_source"


def spawn(preset_id: str, preset_type: str = "EQUATION", *, formula: str | None = None):
    """Spawn Synthia mesh; return new object or None."""
    if not is_available("synthia"):
        return None

    before = {o.name for o in bpy.data.objects}
    try:
        if formula:
            bpy.ops.synthia.custom_formula(formula=formula)
        else:
            bpy.ops.synthia.spawn_preset(preset_name=preset_id, preset_type=preset_type)
    except Exception as exc:
        print(f"[Surreal Architecture] Synthia spawn failed: {exc}")
        return None

    new_objs = [o for o in bpy.data.objects if o.name not in before and o.type == "MESH"]
    if not new_objs:
        new_objs = [o for o in bpy.data.objects if o.name not in before]
    if not new_objs:
        return None
    obj = new_objs[-1]
    obj[TAG_KEY] = preset_id
    return obj


def transfer_mesh(source, target) -> None:
    """Copy mesh data from source onto target object."""
    if source is None or target is None or source.type != "MESH":
        return
    if source.data is target.data:
        return
    old = target.data
    target.data = source.data.copy()
    target[TAG_KEY] = source.get(TAG_KEY, "")
    if old and old.users == 0:
        bpy.data.meshes.remove(old)


def _fallback_bmesh(preset_id: str, size: float = 1.0):
    bm = bmesh.new()
    if preset_id in ("torus_knot", "mobius"):
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=size)
    elif preset_id == "lorenz":
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=size)
    elif preset_id == "platonic_solids":
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size)
    else:
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=size)
    bm.normal_update()
    return bm


def materialize_on_object(obj, props, preset_id: str, preset_type: str) -> bool:
    """Replace active object mesh with Synthia output or native fallback."""
    spawned = None
    if is_available("synthia"):
        if getattr(props, "synthia_use_custom", False):
            spawned = spawn("", "EQUATION", formula=getattr(props, "synthia_custom_formula", "sin(x)"))
        else:
            spawned = spawn(preset_id, preset_type)

    if spawned:
        transfer_mesh(spawned, obj)
        try:
            bpy.data.objects.remove(spawned, do_unlink=True)
        except Exception:
            pass
        return True

    bm = _fallback_bmesh(preset_id, size=max(0.2, getattr(props, "base_radius", 1.0)))
    mesh = obj.data
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj[TAG_KEY] = f"fallback:{preset_id}"
    return False


def materialize_arch_type(obj, props) -> bool:
    entry = SYNTHIA_ARCH_MAP.get(props.arch_type)
    if not entry:
        return False
    preset_id, preset_type = entry
    return materialize_on_object(obj, props, preset_id, preset_type)


def apply_post_spawn(obj, props, monolith) -> None:
    """Bevel + material after Synthia spawn (used by spawn_synthia operator)."""
    from .bevel_bridge import apply_bevel
    from .pipeline import run_post_generate

    if getattr(props, "synthia_apply_bevel", True):
        apply_bevel(obj, props, backend="auto", monolith=monolith)
    if getattr(props, "synthia_apply_material", True) and monolith:
        fn = getattr(monolith, "apply_material_to_object", None)
        if fn:
            try:
                fn(obj, props)
            except Exception:
                pass
    run_post_generate(obj, props, monolith, skip_bevel=True)
