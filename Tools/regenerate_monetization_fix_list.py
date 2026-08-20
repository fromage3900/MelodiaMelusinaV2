# -*- coding: utf-8 -*-
"""Regenerate monetization FIX-LIST ornaments only (no Melody Tokens).

blender --factory-startup -b -P Tools/regenerate_monetization_fix_list.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone

import bpy

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT_G = os.path.join(ROOT, "KitbashExport", "OrnamentalMeshes")
OUT_M = os.path.join(ROOT, "KitbashExport", "MusicalOrnamentalMeshes")
PROD_G = os.path.join(ROOT, "Products", "OrnamentKitbash", "FBX")
PROD_M = os.path.join(ROOT, "Products", "MusicalOrnamentKitbash", "FBX")
STATUS = os.path.join(ROOT, "Saved", "Audit", "monetization_fix_regen.json")

GOTHIC = [
    ("SM_Orn_TorusKnot", "TORUS_KNOT_ORNAMENT", {
        "torus_knot_p": 3, "torus_knot_q": 2, "torus_knot_major": 0.55,
        "torus_knot_minor": 0.22, "torus_knot_bevel": 0.048,
        "torus_knot_petal": 0.08, "torus_knot_jewel": True,
    }),
    ("SM_Orn_FiligreeRing", "FILIGREE_PANEL", {
        "filigree_style": "ARTNOUVEAU_VINE", "filigree_width": 1.8, "filigree_height": 1.8,
        "filigree_thickness": 0.02, "filigree_density": 0.7, "filigree_include_frame": True,
    }),
    ("SM_Orn_CrownMolding", "CORNICE", {
        "cornice_length": 2.2, "cornice_height": 0.28, "cornice_depth": 0.24,
        "cornice_layers": 4, "cornice_scallops": 7,
    }),
    ("SM_Orn_RoseWindow_8Petal", "ROSE_WINDOW", {
        "rose_outer_radius": 1.6, "rose_inner_radius": 0.28, "rose_petal_count": 8,
        "rose_spoke_count": 8, "gothic_thickness": 0.08,
    }),
    ("SM_Orn_VaultRibs", "BAROQUE_VAULT", {
        "baroque_vault_span": 2.4, "baroque_vault_depth": 2.4, "baroque_vault_rise": 1.35,
        "baroque_vault_style": "RIBBED", "baroque_rib_count": 6,
    }),
    ("SM_Orn_OculusFrame", "CUSPED_ARCH", {
        "gothic_width": 1.8, "gothic_radius": 1.1, "gothic_thickness": 0.1,
    }),
    ("SM_Orn_SpiralStaircase", "STAIRCASE", {
        "stair_step_count": 18, "stair_rise": 0.18, "stair_run": 0.32,
        "stair_width": 1.4, "stair_spiral_deg": 360.0, "stair_with_rails": True,
    }),
]

MUSICAL = [
    ("SM_Orn_TrebleClef", "TREBLE_CLEF", {
        "clef_size": 1.8, "clef_thickness": 0.055, "clef_curls": 1.4,
    }),
    ("SM_Orn_MusicalCorner", "FILIGREE_PANEL", {
        "filigree_style": "ARTNOUVEAU_VINE", "filigree_width": 1.2, "filigree_height": 1.2,
        "filigree_thickness": 0.02, "filigree_density": 0.7, "filigree_include_frame": True,
    }),
]


def log(msg: str) -> None:
    print(f"[fix-regen] {msg}", flush=True)


def ensure_addon() -> bool:
    import importlib.util
    addon = os.path.join(ROOT, "deploy", "surreal_architecture_gen.py")
    deploy = os.path.dirname(addon)
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
        spec = importlib.util.spec_from_file_location(name, addon)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        mod.register()
        log(f"addon ok version={getattr(mod, 'bl_info', {}).get('version')}")
        return hasattr(bpy.types.Object, "surreal_arch_props")
    except Exception as e:
        log(f"addon fail: {e}")
        return False


def ensure_mats(obj: bpy.types.Object) -> None:
    for mn, col in (("M_Orn_Base", (0.72, 0.68, 0.78, 1.0)), ("M_Orn_Trim", (0.92, 0.78, 0.42, 1.0))):
        mat = bpy.data.materials.get(mn) or bpy.data.materials.new(mn)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = col
        if obj.data.materials.find(mn) < 0:
            obj.data.materials.append(mat)
    n = len(obj.data.polygons)
    mid = max(1, n // 2) if n else 0
    for i, poly in enumerate(obj.data.polygons):
        poly.material_index = 0 if i < mid else 1


def generate_one(name: str, arch: str, overrides: dict, out_dir: str, prod_dir: str) -> dict:
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    if not hasattr(obj, "surreal_arch_props"):
        return {"name": name, "ok": False, "error": "no props"}
    props = obj.surreal_arch_props
    try:
        props.arch_type = arch
    except Exception as e:
        bpy.data.objects.remove(obj, do_unlink=True)
        return {"name": name, "ok": False, "error": f"arch:{e}"}
    props.apply_modifiers = True
    for k, v in overrides.items():
        if hasattr(props, k):
            try:
                setattr(props, k, v)
            except Exception:
                pass
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        result = bpy.ops.surreal_arch.generate()
    except Exception as e:
        return {"name": name, "ok": False, "error": str(e)}
    if "FINISHED" not in result:
        return {"name": name, "ok": False, "error": str(list(result))}
    for mod in list(obj.modifiers):
        if mod.type == "NODES" and mod.name.startswith("SurrealArch"):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    ensure_mats(obj)
    verts = len(obj.data.vertices)
    faces = len(obj.data.polygons)
    if faces < 1:
        return {"name": name, "ok": False, "error": "0 faces", "verts": verts}
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(prod_dir, exist_ok=True)
    tmp = os.path.join(ROOT, "Saved", "Audit", f"_tmp_{name}.fbx")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    except Exception:
        pass
    bpy.ops.export_scene.fbx(
        filepath=tmp,
        use_selection=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
    )
    for d in (out_dir, prod_dir):
        shutil.copy2(tmp, os.path.join(d, f"{name}.fbx"))
    log(f"OK {name} verts={verts} faces={faces}")
    return {"name": name, "ok": True, "verts": verts, "faces": faces, "arch": arch}


def main() -> None:
    if not ensure_addon():
        raise SystemExit(1)
    # clear default cube scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    results = []
    for name, arch, ov in GOTHIC:
        results.append(generate_one(name, arch, ov, OUT_G, PROD_G))
    for name, arch, ov in MUSICAL:
        results.append(generate_one(name, arch, ov, OUT_M, PROD_M))
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skipped": ["SM_Orn_MelodyToken_01", "SM_Orn_MelodyToken_02", "SM_Orn_MelodyToken_03"],
        "results": results,
        "ok_count": sum(1 for r in results if r.get("ok")),
        "fail_count": sum(1 for r in results if not r.get("ok")),
    }
    os.makedirs(os.path.dirname(STATUS), exist_ok=True)
    with open(STATUS, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    log(json.dumps({"ok": payload["ok_count"], "fail": payload["fail_count"]}))
    if payload["fail_count"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
