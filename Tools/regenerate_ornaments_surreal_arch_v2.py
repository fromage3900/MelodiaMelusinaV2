# -*- coding: utf-8 -*-
"""Regenerate Melodia ornament kitbash FBXs via SurrealArch GeoNodes.

Run inside Blender (addon loaded):
  blender --factory-startup  # then enable SurrealArch, OR use live MCP Blender
  exec(open(r'G:\\...\\Tools\\regenerate_ornaments_surreal_arch.py').read())

Overwrites KitbashExport/OrnamentalMeshes/SM_Orn_*.fbx and copies to
Products/OrnamentKitbash/FBX/. Does not delete originals elsewhere.
"""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone

import bpy
from mathutils import Vector

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT_DIR = os.path.join(ROOT, "KitbashExport", "OrnamentalMeshes")
PRODUCT_FBX = os.path.join(ROOT, "Products", "OrnamentKitbash", "FBX")
STATUS_PATH = os.path.join(ROOT, "Saved", "Audit", "ornament_surreal_regen.json")

# SM_Orn name → (arch_type, prop overrides)
SPECS = [
    ("SM_Orn_RoseWindow_8Petal", "ROSE_WINDOW", {
        "rose_outer_radius": 1.6,
        "rose_inner_radius": 0.28,
        "rose_petal_count": 8,
        "rose_spoke_count": 8,
        "gothic_thickness": 0.08,
    }),
    ("SM_Orn_RosetteMedallion", "ROSE_WINDOW", {
        "rose_outer_radius": 1.0,
        "rose_inner_radius": 0.22,
        "rose_petal_count": 6,
        "rose_spoke_count": 6,
        "gothic_thickness": 0.07,
    }),
    ("SM_Orn_GothicTracery", "FILIGREE_PANEL", {
        "filigree_style": "GOTHIC_IRON",
        "filigree_width": 2.0,
        "filigree_height": 2.4,
        "filigree_thickness": 0.025,
        "filigree_density": 0.75,
        "filigree_include_frame": True,
    }),
    ("SM_Orn_VaultRibs", "BAROQUE_VAULT", {
        "baroque_vault_span": 2.4,
        "baroque_vault_depth": 2.4,
        "baroque_vault_rise": 1.35,
        "baroque_vault_style": "RIBBED",
        "baroque_rib_count": 6,
    }),
    ("SM_Orn_DoorArchway", "GOTHIC_ARCH", {
        "gothic_width": 2.2,
        "gothic_radius": 1.4,
        "gothic_thickness": 0.14,
    }),
    ("SM_Orn_QuatrefoilArch", "TREFOIL", {
        "trefoil_lobes": 4,
        "trefoil_radius": 0.45,
        "trefoil_outer": 1.15,
        "gothic_thickness": 0.09,
    }),
    ("SM_Orn_OculusFrame", "CUSPED_ARCH", {
        "gothic_width": 1.8,
        "gothic_radius": 1.1,
        "gothic_thickness": 0.1,
    }),
    ("SM_Orn_FiligreeRing", "FILIGREE_PANEL", {
        "filigree_style": "ARTNOUVEAU_VINE",
        "filigree_width": 1.8,
        "filigree_height": 1.8,
        "filigree_thickness": 0.02,
        "filigree_density": 0.7,
        "filigree_include_frame": True,
    }),
    ("SM_Orn_WovenRing", "FILIGREE_PANEL", {
        "filigree_style": "GEOMETRIC_ARABESQUE",
        "filigree_width": 1.6,
        "filigree_height": 1.6,
        "filigree_thickness": 0.022,
        "filigree_density": 0.65,
        "filigree_include_frame": True,
    }),
    ("SM_Orn_SpiralStaircase", "STAIRCASE", {
        "stair_step_count": 18,
        "stair_rise": 0.18,
        "stair_run": 0.32,
        "stair_width": 1.4,
        "stair_spiral_deg": 360.0,
        "stair_with_rails": True,
    }),
    ("SM_Orn_ColumnCapital", "PILLAR", {}),
    ("SM_Orn_CorbelBracket", "CORBEL_BRACKET", {
        "corbel_reach": 0.55,
        "corbel_height": 0.75,
        "corbel_thickness": 0.038,
        "corbel_cute": True,
    }),
    ("SM_Orn_CrownMolding", "CORNICE", {
        "cornice_length": 2.2,
        "cornice_height": 0.28,
        "cornice_depth": 0.24,
        "cornice_layers": 4,
        "cornice_scallops": 7,
    }),
    ("SM_Orn_PendantFinial", "PILLAR", {}),
    ("SM_Orn_TorusKnot", "TORUS_KNOT_ORNAMENT", {
        "torus_knot_p": 3,
        "torus_knot_q": 2,
        "torus_knot_major": 0.55,
        "torus_knot_minor": 0.22,
        "torus_knot_bevel": 0.048,
        "torus_knot_petal": 0.08,
        "torus_knot_jewel": True,
    }),
]


def log(msg: str) -> None:
    print(f"[orn-regen] {msg}", flush=True)


def ensure_surreal_arch() -> bool:
    import importlib.util, sys, traceback
    # Melodia Studio / SurrealArch: always (re)register from deploy for headless
    ADDON = os.path.join(ROOT, "deploy", "surreal_architecture_gen.py")
    if not os.path.isfile(ADDON):
        log(f"missing addon {ADDON}")
        return False
    deploy = os.path.dirname(ADDON)
    if deploy not in sys.path:
        sys.path.insert(0, deploy)
    name = "surreal_architecture_gen"
    try:
        if name in sys.modules:
            mod = sys.modules[name]
            if hasattr(mod, "unregister"):
                try:
                    mod.unregister()
                except Exception:
                    pass
        spec = importlib.util.spec_from_file_location(name, ADDON)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        if hasattr(mod, "register"):
            mod.register()
        log(f"loaded SurrealArch version={getattr(mod, 'bl_info', {}).get('version')}")
        return hasattr(bpy.types.Object, "surreal_arch_props")
    except Exception:
        log("addon load failed:\n" + traceback.format_exc())
        return False


def ensure_base_trim_materials(obj: bpy.types.Object) -> None:
    base = bpy.data.materials.get("M_Orn_Base")
    if base is None:
        base = bpy.data.materials.new("M_Orn_Base")
        base.use_nodes = True
        nt = base.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.72, 0.68, 0.78, 1.0)
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = 0.55
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = 0.05
    trim = bpy.data.materials.get("M_Orn_Trim")
    if trim is None:
        trim = bpy.data.materials.new("M_Orn_Trim")
        trim.use_nodes = True
        nt = trim.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.92, 0.78, 0.42, 1.0)
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = 0.28
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = 0.65
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (0.55, 0.35, 0.75, 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = 0.08
    mesh = obj.data
    mesh.materials.clear()
    mesh.materials.append(base)
    mesh.materials.append(trim)
    n = len(mesh.polygons)
    if n:
        mid = max(1, n // 2)
        for i, poly in enumerate(mesh.polygons):
            poly.material_index = 0 if i < mid else 1
    log(f"materials Base+Trim on {obj.name} faces={n}")


def clear_work_objects() -> None:
    for o in list(bpy.data.objects):
        if o.name.startswith("SM_Orn_") or o.name.startswith("TEST_") or o.name.startswith("_regen_"):
            bpy.data.objects.remove(o, do_unlink=True)


def generate_one(name: str, arch_type: str, overrides: dict) -> bpy.types.Object | None:
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    if not hasattr(obj, "surreal_arch_props"):
        log(f"FATAL no surreal_arch_props on {name}")
        return None
    props = obj.surreal_arch_props
    try:
        props.arch_type = arch_type
    except Exception as exc:
        log(f"SKIP bad arch_type {arch_type}: {exc}")
        bpy.data.objects.remove(obj, do_unlink=True)
        return None
    props.apply_modifiers = True
    for k, v in overrides.items():
        if hasattr(props, k):
            try:
                setattr(props, k, v)
            except Exception as exc:
                log(f"WARN set {k}={v}: {exc}")
        else:
            log(f"WARN missing prop {k}")

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        result = bpy.ops.surreal_arch.generate()
    except Exception as exc:
        log(f"FAIL generate exception {name}: {exc}")
        bpy.data.objects.remove(obj, do_unlink=True)
        return None
    if "FINISHED" not in result:
        log(f"FAIL generate {name} {result}")
        bpy.data.objects.remove(obj, do_unlink=True)
        return None

    # Keep GeoNodes output clean — do NOT stack aest_goth_* polish
    # (those inject spikes/finials that wreck kitbash silhouettes).

    # Apply remaining SurrealArch node mods if any
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        if mod.type == "NODES" and mod.name.startswith("SurrealArch"):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as exc:
                log(f"WARN apply mod {mod.name}: {exc}")

    # Shade smooth
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass

    nverts = len(obj.data.vertices)
    log(f"OK {name} ← {arch_type} verts={nverts} dims={list(obj.dimensions)}")
    if nverts < 32:
        log(f"WARN low vert count for {name}")
    return obj


def export_fbx(obj: bpy.types.Object, path: str) -> bool:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    zmin = min(v.z for v in bbox)
    obj.location.z -= zmin
    # Export via temp to avoid Windows Errno 22 on overwrite
    tmp = os.path.join(ROOT, "Saved", "Audit", f"_tmp_{obj.name}.fbx")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    try:
        bpy.ops.export_scene.fbx(
            filepath=tmp,
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_NONE",
            axis_forward="-Y",
            axis_up="Z",
            mesh_smooth_type="FACE",
            use_mesh_modifiers=True,
        )
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
        shutil.copy2(tmp, path)
        log(f"exported {path} ({os.path.getsize(path)} bytes)")
        return True
    except Exception as exc:
        log(f"FAIL export {path}: {exc}")
        return False


def run() -> dict:
    if not ensure_surreal_arch():
        raise RuntimeError("SurrealArch generate op unavailable")
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PRODUCT_FBX, exist_ok=True)
    os.makedirs(os.path.dirname(STATUS_PATH), exist_ok=True)

    # Keep cross/lights; remove prior regen meshes
    clear_work_objects()

    results = []
    for name, arch_type, overrides in SPECS:
        log(f"=== {name} / {arch_type}")
        obj = generate_one(name, arch_type, overrides)
        if obj is None:
            results.append({"name": name, "ok": False, "reason": "generate"})
            continue
        ensure_base_trim_materials(obj)
        out_path = os.path.join(OUT_DIR, f"{name}.fbx")
        ok = export_fbx(obj, out_path)
        if ok:
            dest = os.path.join(PRODUCT_FBX, f"{name}.fbx")
            try:
                shutil.copy2(out_path, dest)
            except Exception as exc:
                log(f"WARN copy product: {exc}")
        results.append(
            {
                "name": name,
                "ok": ok,
                "arch_type": arch_type,
                "verts": len(obj.data.vertices) if obj else 0,
                "path": out_path if ok else None,
            }
        )
        # hide from next gens clutter
        obj.hide_viewport = True
        obj.hide_render = True

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": sum(1 for r in results if r["ok"]),
        "fail": sum(1 for r in results if not r["ok"]),
        "results": results,
    }
    import json

    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    log(f"done {summary['ok']}/{len(results)} → {STATUS_PATH}")
    return summary


if __name__ == "__main__":
    run()
