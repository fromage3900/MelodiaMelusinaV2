# -*- coding: utf-8 -*-
"""Headless QA: load SurrealArch and bake the four cute kitbash arch_types.

Run:
  "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe" --factory-startup -b -P Tools/test_cute_gn_ornaments.py

Writes KitbashExport/OrnamentalMeshes/SM_Orn_{VaultRibs,CorbelBracket,CrownMolding,TorusKnot}.fbx
(and Products/OrnamentKitbash/FBX copies) when SurrealArch generate succeeds.
Falls back note if generate fails — use blender_ornament_cute_replacements.py.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import traceback

import bpy

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ADDON = os.path.join(ROOT, "deploy", "surreal_architecture_gen.py")
OUT_DIR = os.path.join(ROOT, "KitbashExport", "OrnamentalMeshes")
PRODUCT_FBX = os.path.join(ROOT, "Products", "OrnamentKitbash", "FBX")

SPECS = [
    ("SM_Orn_VaultRibs", "BAROQUE_VAULT", {
        "baroque_vault_span": 2.4,
        "baroque_vault_depth": 2.4,
        "baroque_vault_rise": 1.35,
        "baroque_vault_style": "RIBBED",
        "baroque_rib_count": 6,
    }),
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
    print(f"[cute-gn-qa] {msg}", flush=True)


def load_addon() -> bool:
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
        log(f"loaded addon version={getattr(mod, 'bl_info', {}).get('version')}")
        return True
    except Exception:
        log("addon load failed:\n" + traceback.format_exc())
        return False


def clear() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def export_fbx(obj: bpy.types.Object, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp.fbx"
    if os.path.isfile(tmp):
        try:
            os.remove(tmp)
        except OSError:
            pass
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError as exc:
            log(f"WARN could not remove old {path}: {exc}")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=tmp.replace("\\", "/"),
        use_selection=True,
        apply_scale_options="FBX_SCALE_ALL",
        object_types={"MESH"},
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        path_mode="AUTO",
    )
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass
    os.replace(tmp, path)


def generate_one(name: str, arch_type: str, overrides: dict) -> bool:
    clear()
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    if not hasattr(obj, "surreal_arch_props"):
        log(f"FAIL no surreal_arch_props on {name}")
        return False
    props = obj.surreal_arch_props
    try:
        props.arch_type = arch_type
    except Exception as exc:
        log(f"FAIL arch_type {arch_type}: {exc}")
        return False
    props.apply_modifiers = True
    for k, v in overrides.items():
        if hasattr(props, k):
            try:
                setattr(props, k, v)
            except Exception as exc:
                log(f"WARN {k}={v}: {exc}")
        else:
            log(f"WARN missing prop {k}")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        result = bpy.ops.surreal_arch.generate()
    except Exception:
        log(f"FAIL generate exception {name}:\n" + traceback.format_exc())
        return False
    if "FINISHED" not in result:
        log(f"FAIL generate {name} {result}")
        return False
    for mod in list(obj.modifiers):
        if mod.type == "NODES" and mod.name.startswith("SurrealArch"):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as exc:
                log(f"WARN apply {mod.name}: {exc}")
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    nverts = len(obj.data.vertices)
    dims = list(obj.dimensions)
    log(f"OK {name} ← {arch_type} verts={nverts} dims={[round(d, 3) for d in dims]}")
    if nverts < 64:
        log(f"WARN low verts {name}")
        return False
    out = os.path.join(OUT_DIR, f"{name}.fbx")
    export_fbx(obj, out)
    os.makedirs(PRODUCT_FBX, exist_ok=True)
    shutil.copy2(out, os.path.join(PRODUCT_FBX, f"{name}.fbx"))
    log(f"wrote {out} ({os.path.getsize(out)} bytes)")
    return True


def main() -> None:
    log("start")
    if not load_addon():
        raise SystemExit(2)
    ok = 0
    for name, arch, ov in SPECS:
        if generate_one(name, arch, ov):
            ok += 1
    log(f"done {ok}/{len(SPECS)}")
    if ok < len(SPECS):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
