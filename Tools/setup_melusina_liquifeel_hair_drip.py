# -*- coding: utf-8 -*-
"""LiquiFeel tip-drip proxies for restored old Melusina hair (Stage v9).

Does NOT:
  - replace Water (Advance).001 look on Hair Strand*
  - modify Asset_melusina_elixir
  - rebuild FLIP domain
  - put drip objects into FX_Hero

Does:
  - Melusina_HairDrip collection
  - small tip proxies at Hair Strand.002/.004/.007 tips
  - parent to strand (follow armature/soft physics)
  - copy LiquiFeel GN groups from melusina_ElixirGlass when present
  - try liquifeel ops on proxies when addon available

Usage (GUI - preferred; do not auto-save stage):
  Open Melodia_Portfolio_Stage_v10.blend yourself, then:
  exec(open(r"G:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\setup_melusina_liquifeel_hair_drip.py").read())

  CLI audit-only (no save):
  blender KitbashExport/Melodia_Portfolio_Stage_v10.blend -P Tools/setup_melusina_liquifeel_hair_drip.py

  Explicit save of the stage (rare - requires env):
  set MELODIA_ALLOW_STAGE_SAVE=1
  blender ... -P Tools/setup_melusina_liquifeel_hair_drip.py -- --save
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved" / "Audit" / "melusina_liquifeel_hair_drip.json"
COLL_NAME = "Melusina_HairDrip"
HAIR_NAMES = ("Hair Strand.002", "Hair Strand.004", "Hair Strand.007")
ELIXIR_GLASS = "melusina_ElixirGlass"
PROXY_SCALE = 0.018


def _log(msg: str) -> None:
    print(f"[hair-drip-lf] {msg}", flush=True)


def _want_save() -> bool:
    argv = sys.argv
    flag = False
    if "--" in argv:
        flag = "--save" in argv[argv.index("--") + 1 :]
    else:
        flag = "--save" in argv
    if not flag:
        return False
    # Hard gate: never overwrite portfolio stage without explicit env opt-in
    allow = os.environ.get("MELODIA_ALLOW_STAGE_SAVE", "").strip() in ("1", "true", "yes")
    fp = (bpy.data.filepath or "").replace("\\", "/").lower()
    if "melodia_portfolio_stage" in fp and not allow:
        _log(
            "REFUSING save: portfolio stage file. "
            "Set MELODIA_ALLOW_STAGE_SAVE=1 only if you really mean it."
        )
        return False
    return True


def _ensure_coll(name: str) -> bpy.types.Collection:
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    # Not under FX_Hero
    fx = bpy.data.collections.get("FX_Hero")
    if fx and name in [c.name for c in fx.children]:
        try:
            fx.children.unlink(coll)
        except Exception:
            pass
    return coll


def _link(obj: bpy.types.Object, coll: bpy.types.Collection) -> None:
    for c in list(obj.users_collection):
        try:
            c.objects.unlink(obj)
        except Exception:
            pass
    if obj.name not in coll.objects:
        coll.objects.link(obj)


def _world_tip(obj: bpy.types.Object) -> Vector | None:
    if obj.type != "MESH" or not obj.data.vertices:
        return None
    zs = sorted(v.co.z for v in obj.data.vertices)
    thresh = zs[max(0, int(len(zs) * 0.02))]
    tips = [obj.matrix_world @ v.co for v in obj.data.vertices if v.co.z <= thresh + 1e-5]
    if not tips:
        return None
    return sum(tips, Vector()) / len(tips)


def _elixir_liquifeel_groups() -> list[bpy.types.NodeTree]:
    glass = bpy.data.objects.get(ELIXIR_GLASS)
    groups: list[bpy.types.NodeTree] = []
    if not glass:
        # Fallback: any LiquiFeel node group in file
        for ng in bpy.data.node_groups:
            if "liqui" in ng.name.lower():
                groups.append(ng)
        return groups
    for m in glass.modifiers:
        if m.type == "NODES" and m.node_group and "liqui" in m.node_group.name.lower():
            if m.node_group not in groups:
                groups.append(m.node_group)
    return groups


def _clear_proxy_mods(obj: bpy.types.Object) -> None:
    for m in list(obj.modifiers):
        if m.type == "NODES" and m.node_group and "liqui" in (m.node_group.name or "").lower():
            obj.modifiers.remove(m)


def _apply_liquifeel_groups(obj: bpy.types.Object, groups: list) -> list[str]:
    applied = []
    _clear_proxy_mods(obj)
    for ng in groups:
        mod = obj.modifiers.new(name=f"LF_{ng.name}"[:50], type="NODES")
        mod.node_group = ng
        applied.append(ng.name)
    return applied


def _try_liquifeel_ops(obj: bpy.types.Object) -> list[str]:
    notes = []
    if not hasattr(bpy.ops, "liquifeel"):
        notes.append("liquifeel_ops_missing")
        return notes
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for op_name in (
        "fills_active_object",
        "shade_active_object_via_fill",
        "add_condensation_to_active_object",
    ):
        op = getattr(bpy.ops.liquifeel, op_name, None)
        if not op:
            continue
        try:
            op()
            notes.append(f"ok:{op_name}")
        except Exception as exc:
            notes.append(f"skip:{op_name}:{exc}")
    return notes


def _make_proxy(name: str, world: Vector, parent: bpy.types.Object) -> bpy.types.Object:
    existing = bpy.data.objects.get(name)
    if existing:
        obj = existing
    else:
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2, radius=1.0, location=world
        )
        obj = bpy.context.active_object
        obj.name = name
    obj.scale = (PROXY_SCALE, PROXY_SCALE, PROXY_SCALE)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    except Exception:
        pass
    obj.location = world
    obj.parent = parent
    # Keep world position after parenting
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj["melodia_role"] = "liquifeel_hair_tip_drip"
    obj["melodia_tip_of"] = parent.name
    return obj


def setup(*, save: bool = False) -> dict:
    coll = _ensure_coll(COLL_NAME)
    # Beauty default: drip off for clean plates; on for drip shoot
    coll.hide_render = False
    coll.hide_viewport = False

    groups = _elixir_liquifeel_groups()
    _log(f"LiquiFeel groups from elixir/file: {[g.name for g in groups]}")

    results = []
    for hair_name in HAIR_NAMES:
        hair = bpy.data.objects.get(hair_name)
        if not hair:
            results.append({"hair": hair_name, "ok": False, "error": "missing"})
            continue
        tip = _world_tip(hair)
        if tip is None:
            results.append({"hair": hair_name, "ok": False, "error": "no_tip"})
            continue
        proxy_name = f"LF_TipDrip_{hair_name.replace(' ', '_')}"
        proxy = _make_proxy(proxy_name, tip, hair)
        _link(proxy, coll)
        applied = _apply_liquifeel_groups(proxy, groups) if groups else []
        ops = _try_liquifeel_ops(proxy) if not applied else ["groups_copied_skip_ops"]
        if not applied and not groups:
            ops = _try_liquifeel_ops(proxy)
        results.append(
            {
                "hair": hair_name,
                "proxy": proxy.name,
                "tip": [round(tip.x, 4), round(tip.y, 4), round(tip.z, 4)],
                "liquifeel_groups": applied,
                "ops": ops,
                "ok": True,
            }
        )
        _log(f"{hair_name} -> {proxy.name} tip={tip} groups={applied}")

    # Ensure FX_Hero does not contain proxies
    fx = bpy.data.collections.get("FX_Hero")
    if fx:
        for row in results:
            p = bpy.data.objects.get(row.get("proxy") or "")
            if p and p.name in fx.objects:
                try:
                    fx.objects.unlink(p)
                except Exception:
                    pass

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filepath": bpy.data.filepath,
        "collection": COLL_NAME,
        "groups_available": [g.name for g in groups],
        "results": results,
        "notes": [
            "Keep Water (Advance).001 on hair strands.",
            "FX_Hero remains dressing only.",
            "Asset_melusina_elixir untouched.",
            "Toggle Melusina_HairDrip hide_render for beauty vs drip plates.",
            "Scrub timeline so soft hair moves; proxies are parented to tip strands.",
        ],
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _log(f"wrote {AUDIT}")

    if save and bpy.data.is_saved:
        bpy.ops.wm.save_mainfile()
        _log("saved mainfile")
    elif save:
        _log("WARN --save requested but file not saved to disk path")
    return report


def main() -> int:
    report = setup(save=_want_save())
    ok = any(r.get("ok") for r in report.get("results") or [])
    print(json.dumps({"ok": ok, "count": sum(1 for r in report["results"] if r.get("ok"))}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
