# -*- coding: utf-8 -*-
"""Spawn ornaments with LIVE Geometry Nodes (editable) in proper collections.

Collections:
  OrnamentGN_Editable  — gothic monetization fix-list
  MusicalGN_Editable   — full musical kitbash (10) + Melodia GN where routed

Keeps SurrealArch / Melodia GN modifiers live (apply_modifiers=False).
Does NOT overwrite KitbashExport FBX. No WIP / HandRemake / review-folder deps.

Blender:
  blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -P Tools/spawn_editable_ornament_gn.py

Or MCP / Scripting:
  exec(open(r'G:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\spawn_editable_ornament_gn.py').read())
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import bpy

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
AUDIT = os.path.join(ROOT, "Saved", "Audit", "editable_ornament_gn_spawn.json")

COL_GOTHIC = "OrnamentGN_Editable"
COL_MUSICAL = "MusicalGN_Editable"

# (asset_name, arch_type, overrides)
GOTHIC_TARGETS = [
    ("SM_Orn_TorusKnot", "TORUS_KNOT_ORNAMENT", {
        "torus_knot_p": 3, "torus_knot_q": 2, "torus_knot_major": 0.55,
        "torus_knot_minor": 0.22, "torus_knot_bevel": 0.048,
        "torus_knot_petal": 0.08, "torus_knot_jewel": True,
    }),
    ("SM_Orn_FiligreeRing", "FILIGREE_PANEL", {
        "filigree_style": "ARTNOUVEAU_VINE", "filigree_width": 1.8, "filigree_height": 1.8,
        "filigree_thickness": 0.02, "filigree_density": 0.65, "filigree_include_frame": True,
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

# Full musical kitbash (10) — SurrealArch / Melodia GN builders only
MUSICAL_TARGETS = [
    ("SM_Orn_TrebleClef", "TREBLE_CLEF", {
        "clef_size": 2.0, "clef_thickness": 0.06, "clef_curls": 1.5,
    }),
    ("SM_Orn_NoteHead", "NOTE_HEAD", {
        "note_kind": "QUARTER", "note_size": 0.45, "note_stem_len": 1.35,
    }),
    ("SM_Orn_NoteBeam", "NOTE_HEAD", {
        "note_kind": "QUARTER", "note_size": 0.38, "note_stem_len": 1.1,
    }),
    ("SM_Orn_SheetMusicRail", "SHEET_MUSIC_RAIL", {}),
    ("SM_Orn_MusicalCorner", "FILIGREE_PANEL", {
        "filigree_style": "ARTNOUVEAU_VINE", "filigree_width": 1.2, "filigree_height": 1.2,
        "filigree_thickness": 0.022, "filigree_density": 0.75, "filigree_include_frame": True,
    }),
    ("SM_Orn_MusicalDivider", "FILIGREE_PANEL", {
        "filigree_style": "ARTNOUVEAU_VINE", "filigree_width": 2.4, "filigree_height": 0.55,
        "filigree_thickness": 0.02, "filigree_density": 0.7, "filigree_include_frame": True,
    }),
    ("SM_Orn_PearlJewel", "TORUS_KNOT_ORNAMENT", {
        "torus_knot_p": 2, "torus_knot_q": 3, "torus_knot_major": 0.28,
        "torus_knot_minor": 0.12, "torus_knot_bevel": 0.04,
        "torus_knot_petal": 0.04, "torus_knot_jewel": True,
    }),
    ("SM_Orn_MelodyToken_01", "ROSE_WINDOW", {
        "rose_outer_radius": 0.55, "rose_inner_radius": 0.12, "rose_petal_count": 6,
        "rose_spoke_count": 6, "gothic_thickness": 0.045,
    }),
    ("SM_Orn_MelodyToken_02", "ROSE_WINDOW", {
        "rose_outer_radius": 0.62, "rose_inner_radius": 0.14, "rose_petal_count": 8,
        "rose_spoke_count": 8, "gothic_thickness": 0.05,
    }),
    ("SM_Orn_MelodyToken_03", "FILIGREE_PANEL", {
        "filigree_style": "ARTNOUVEAU_VINE", "filigree_width": 0.95, "filigree_height": 0.95,
        "filigree_thickness": 0.018, "filigree_density": 0.85, "filigree_include_frame": True,
    }),
]


def log(msg: str) -> None:
    print(f"[editable-gn] {msg}", flush=True)


def ensure_addon() -> bool:
    import importlib.util

    deploy = os.path.join(ROOT, "deploy")
    addon = os.path.join(deploy, "surreal_architecture_gen.py")
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
        return hasattr(bpy.types.Object, "surreal_arch_props")


def ensure_collection(col_name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(col_name)
    if col is None:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    return col


def clear_edit_names(names: list[str]) -> None:
    for name in names:
        for prefix in ("_edit_", "_ref_"):
            old = bpy.data.objects.get(prefix + name)
            if old is not None:
                bpy.data.objects.remove(old, do_unlink=True)


def enable_melodia_gn() -> None:
    try:
        from surreal_arch.quality_props import register_quality_props

        register_quality_props()
        q = bpy.context.scene.surreal_arch_quality
        q.export_quality = "EXPORT"
        q.prefer_melodia_gn = True
        log("prefer_melodia_gn=True quality=EXPORT")
    except Exception as e:
        log(f"quality_props skip: {e}")
    try:
        from surreal_arch.melodia_gn.bake import bake_all

        baked = bake_all(overwrite=False)
        log(f"melodia_gn library ready count={len(baked) if isinstance(baked, dict) else baked}")
    except Exception as e:
        log(f"melodia_gn bake skip: {e}")


def _mat(name: str, rgba: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.35
    return mat


def ensure_mats(obj: bpy.types.Object, lane: str) -> None:
    if lane == "musical":
        specs = (
            ("M_MusicalGold", (1.0, 0.9, 0.4, 1.0)),
            ("M_MusicalPearl", (0.94, 0.86, 0.94, 1.0)),
        )
    elif lane == "token":
        specs = (
            ("M_Token_Base", (0.88, 0.82, 0.96, 1.0)),
            ("M_Token_Trim", (1.0, 0.9, 0.45, 1.0)),
        )
    else:
        specs = (
            ("M_Orn_Base", (0.72, 0.68, 0.78, 1.0)),
            ("M_Orn_Trim", (0.92, 0.78, 0.42, 1.0)),
        )
    for mn, col in specs:
        _mat(mn, col)
        if obj.data.materials.find(mn) < 0:
            obj.data.materials.append(bpy.data.materials[mn])
    n = len(obj.data.polygons)
    if n:
        mid = max(1, n // 2)
        for i, poly in enumerate(obj.data.polygons):
            poly.material_index = 0 if i < mid else min(1, len(obj.data.materials) - 1)


def lane_for(name: str, default: str) -> str:
    if "MelodyToken" in name:
        return "token"
    return default


def polish_editable(obj: bpy.types.Object, lane: str, asset_name: str) -> list[str]:
    steps: list[str] = []
    ensure_mats(obj, lane)
    steps.append("mats")

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        steps.append("origin")
    except Exception:
        pass

    if not any(m.name == "Editable_WeightedNormal" for m in obj.modifiers):
        wn = obj.modifiers.new("Editable_WeightedNormal", "WEIGHTED_NORMAL")
        wn.keep_sharp = True
        steps.append("weighted_normal")

    if asset_name == "SM_Orn_FiligreeRing" and not any(m.name == "Editable_Decimate" for m in obj.modifiers):
        dec = obj.modifiers.new("Editable_Decimate", "DECIMATE")
        dec.ratio = 0.38
        dec.use_collapse_triangulate = True
        steps.append("decimate_filigree")

    if asset_name == "SM_Orn_TrebleClef":
        obj.rotation_euler[1] = 0.0
        steps.append("treble_upright")

    return steps


# Melodia GN builders verified working on Blender 5.1
FORCE_SURREAL_ARCH = frozenset()


def _set_prefer_melodia(prefer: bool) -> None:
    try:
        q = bpy.context.scene.surreal_arch_quality
        q.prefer_melodia_gn = prefer
    except Exception:
        pass


def spawn_one(
    name: str,
    arch: str,
    overrides: dict,
    lane: str,
    col: bpy.types.Collection,
    index: int,
    *,
    row_offset: float = 0.0,
) -> dict:
    edit_name = f"_edit_{name}"
    old = bpy.data.objects.get(edit_name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    x = (index % 5) * 4.0
    y = -(index // 5) * 4.0 + row_offset
    bpy.ops.mesh.primitive_cube_add(size=0.15, location=(x, y, 0.0))
    obj = bpy.context.active_object
    obj.name = edit_name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

    if not hasattr(obj, "surreal_arch_props"):
        return {"name": edit_name, "ok": False, "error": "no surreal_arch_props"}

    props = obj.surreal_arch_props
    try:
        props.arch_type = arch
    except Exception as e:
        return {"name": edit_name, "ok": False, "error": f"arch:{e}"}

    if hasattr(props, "apply_modifiers"):
        props.apply_modifiers = False
    if hasattr(props, "auto_update"):
        props.auto_update = True  # Melodia Studio RNA sliders regenerate live GN

    for k, v in overrides.items():
        if hasattr(props, k):
            try:
                setattr(props, k, v)
            except Exception:
                pass

    force_surreal = arch in FORCE_SURREAL_ARCH
    if force_surreal:
        _set_prefer_melodia(False)

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        result = bpy.ops.surreal_arch.generate()
    except Exception as e:
        if force_surreal:
            _set_prefer_melodia(True)
        return {"name": edit_name, "ok": False, "error": str(e)}
    finally:
        if force_surreal:
            _set_prefer_melodia(True)

    if "FINISHED" not in result:
        return {"name": edit_name, "ok": False, "error": str(list(result))}

    polish_steps = polish_editable(obj, lane, name)
    deps = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(deps)
    verts_eval = len(eval_obj.data.vertices) if eval_obj.type == "MESH" else 0
    mods = [m.name for m in obj.modifiers]

    return {
        "name": edit_name,
        "ok": True,
        "source": "surreal_arch_native" if force_surreal else "surreal_arch_gn",
        "arch": arch,
        "lane": lane,
        "collection": col.name,
        "modifiers": mods,
        "polish": polish_steps,
        "location": list(obj.location),
        "verts_eval": verts_eval,
    }


def spawn_group(
    targets: list[tuple],
    col_name: str,
    default_lane: str,
    *,
    row_offset: float = 0.0,
) -> tuple[bpy.types.Collection, list[dict]]:
    col = ensure_collection(col_name)
    clear_edit_names([t[0] for t in targets])
    results = []
    for i, (name, arch, ov) in enumerate(targets):
        lane = lane_for(name, default_lane)
        log(f"spawn {name} ({arch}) → {col_name}")
        results.append(spawn_one(name, arch, ov, lane, col, i, row_offset=row_offset))
    return col, results


def main() -> dict:
    if not ensure_addon():
        raise SystemExit("SurrealArch addon unavailable")
    enable_melodia_gn()

    gothic_col, gothic_results = spawn_group(GOTHIC_TARGETS, COL_GOTHIC, "gothic", row_offset=0.0)
    musical_col, musical_results = spawn_group(MUSICAL_TARGETS, COL_MUSICAL, "musical", row_offset=-20.0)

    results = gothic_results + musical_results
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collections": {
            COL_GOTHIC: {"count": len(gothic_results), "ok": sum(1 for r in gothic_results if r.get("ok"))},
            COL_MUSICAL: {"count": len(musical_results), "ok": sum(1 for r in musical_results if r.get("ok"))},
        },
        "policy": "live GN modifiers kept; polish pass; no FBX overwrite; no WIP/review-folder deps",
        "how_to_edit": [
            f"Gothic: select _edit_SM_Orn_* in {COL_GOTHIC}",
            f"Musical: select _edit_SM_Orn_* in {COL_MUSICAL}",
            "Modifier Properties → SurrealArch / MelodiaGN node trees",
            "Melodia Studio → RNA tweaks → generate again",
            "When final: apply modifiers → export FBX to KitbashExport flat SSOT",
        ],
        "results": results,
        "ok_count": sum(1 for r in results if r.get("ok")),
        "fail_count": sum(1 for r in results if not r.get("ok")),
    }
    os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
    with open(AUDIT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    log(json.dumps({
        "ok": payload["ok_count"],
        "fail": payload["fail_count"],
        "gothic": gothic_col.name,
        "musical": musical_col.name,
    }))
    return payload


if __name__ == "__main__":
    main()
