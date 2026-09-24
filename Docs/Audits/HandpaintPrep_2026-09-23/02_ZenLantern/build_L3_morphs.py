"""ZenLantern V2 L3 — morph shape keys + FBX export (copy-first)."""
from __future__ import annotations

import json
import math
import os
from datetime import datetime

import bpy
from mathutils import Matrix, Vector

ROOT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\02_ZenLantern"
BLEND_OUT = os.path.join(ROOT, "ZenLantern_V2_L3_morphs.blend")
FBX_OUT = os.path.join(ROOT, "substance", "meshes", "ZenLantern_V2_L3_morphs.fbx")
JSON_OUT = os.path.join(ROOT, "L3_morph_report.json")
RECEIPT = os.path.join(ROOT, "L3_MORPH_RECEIPT.md")
RECEIPT_AUDIT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\HandpaintPrep_2026-09-23\L3_MORPH_RECEIPT.md"

BODY = "zenlantern_V2"
EXPORT_NAME = "zenlantern_V2_L3"


def log(msg: str) -> None:
    print(f"[L3] {msg}", flush=True)


def unhide(o: bpy.types.Object) -> None:
    o.hide_set(False)
    o.hide_viewport = False
    o.hide_render = False
    for c in list(o.users_collection):
        c.hide_viewport = False


def world_bbox(obj: bpy.types.Object):
    mat = obj.matrix_world
    coords = [mat @ Vector(c) for c in obj.bound_box]
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    zs = [c.z for c in coords]
    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


def vg_weight(obj: bpy.types.Object, vi: int, gname: str) -> float:
    if gname not in obj.vertex_groups:
        return 0.0
    try:
        return obj.vertex_groups[gname].weight(vi)
    except RuntimeError:
        return 0.0


def reset_key_values(obj: bpy.types.Object) -> None:
    sk = obj.data.shape_keys
    if not sk:
        return
    for kb in sk.key_blocks:
        kb.value = 0.0


def ensure_basis(obj: bpy.types.Object):
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
    return obj.data.shape_keys


def clear_non_basis_keys(obj: bpy.types.Object) -> None:
    sk = obj.data.shape_keys
    if sk is None:
        return
    for kb in list(sk.key_blocks)[1:]:
        obj.shape_key_remove(kb)


def main() -> None:
    os.makedirs(os.path.join(ROOT, "substance", "meshes"), exist_ok=True)
    os.makedirs(os.path.dirname(RECEIPT_AUDIT), exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT, copy=True)
    log(f"working blend -> {BLEND_OUT}")

    body = bpy.data.objects.get(BODY)
    if body is None or body.type != "MESH":
        raise RuntimeError(f"missing body mesh {BODY!r}")

    charms = sorted(
        [
            o
            for o in bpy.data.objects
            if o.type == "MESH" and o.name.startswith("zenlantern_V2_charm_")
        ],
        key=lambda o: o.name,
    )
    log(f"body={body.name} v={len(body.data.vertices)} f={len(body.data.polygons)} charms={len(charms)}")

    # Duplicate body + charms (leave originals in blend intact)
    bpy.ops.object.select_all(action="DESELECT")
    for o in [body] + charms:
        unhide(o)
        o.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.duplicate()
    dupes = list(bpy.context.selected_objects)
    body_d = next(o for o in dupes if o.name.startswith(BODY))
    charm_ds = [o for o in dupes if "charm_" in o.name]
    log(f"dup body={body_d.name} charms={len(charm_ds)}")

    bmin, bmax = world_bbox(body)
    mid_x = 0.5 * (bmin.x + bmax.x)

    for o in charm_ds:
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode="OBJECT")
        ox = o.matrix_world.translation.x
        side = "CHARM_L" if ox < mid_x else "CHARM_R"
        for gname in ("CHARM", side):
            if gname not in o.vertex_groups:
                o.vertex_groups.new(name=gname)
            o.vertex_groups[gname].add([v.index for v in o.data.vertices], 1.0, "REPLACE")
        log(f"  tag {o.name} {side}")

    # Body zone groups
    for gname in ("ZONE_FIRE", "ZONE_ROOF", "ZONE_BODY"):
        if gname not in body_d.vertex_groups:
            body_d.vertex_groups.new(name=gname)
    z0, z1 = bmin.z, bmax.z
    zspan = max(z1 - z0, 1e-6)
    mw = body_d.matrix_world
    fire_idxs, roof_idxs, body_idxs = [], [], []
    for v in body_d.data.vertices:
        t = ((mw @ v.co).z - z0) / zspan
        if 0.40 <= t <= 0.62:
            fire_idxs.append(v.index)
        elif t >= 0.72:
            roof_idxs.append(v.index)
        else:
            body_idxs.append(v.index)
    body_d.vertex_groups["ZONE_FIRE"].add(fire_idxs, 1.0, "REPLACE")
    body_d.vertex_groups["ZONE_ROOF"].add(roof_idxs, 1.0, "REPLACE")
    body_d.vertex_groups["ZONE_BODY"].add(body_idxs, 1.0, "REPLACE")
    log(f"zones fire={len(fire_idxs)} roof={len(roof_idxs)} body={len(body_idxs)}")

    # Join
    bpy.ops.object.select_all(action="DESELECT")
    body_d.select_set(True)
    for o in charm_ds:
        o.select_set(True)
    bpy.context.view_layer.objects.active = body_d
    bpy.ops.object.join()
    host = bpy.context.view_layer.objects.active
    host.name = EXPORT_NAME
    host.data.name = EXPORT_NAME
    log(f"host={host.name} v={len(host.data.vertices)} f={len(host.data.polygons)}")

    bmin, bmax = world_bbox(host)
    mid = Vector(
        (
            0.5 * (bmin.x + bmax.x),
            0.5 * (bmin.y + bmax.y),
            0.5 * (bmin.z + bmax.z),
        )
    )
    z0, z1 = bmin.z, bmax.z
    zspan = max(z1 - z0, 1e-6)
    mw = host.matrix_world
    mwi = mw.inverted()

    clear_non_basis_keys(host)
    ensure_basis(host)

    def new_key(name: str):
        reset_key_values(host)
        return host.shape_key_add(name=name, from_mix=False)

    def write_key(kb, mutator):
        basis = host.data.shape_keys.key_blocks["Basis"]
        for i in range(len(host.data.vertices)):
            w = mw @ basis.data[i].co
            kb.data[i].co = mwi @ mutator(i, w)

    # SK_FlameBreath
    kb = new_key("SK_FlameBreath")

    def flame(i, w):
        t = (w.z - z0) / zspan
        if t < 0.38 or t > 0.64:
            return w
        fall = max(0.0, min(1.0, 1.0 - abs(t - 0.51) / 0.13))
        xy = Vector((w.x - mid.x, w.y - mid.y, 0.0))
        if xy.length > 1e-8:
            xy2 = xy * (1.0 + 0.08 * fall)
            w = Vector((mid.x + xy2.x, mid.y + xy2.y, w.z + 0.012 * fall))
        else:
            w = Vector((w.x, w.y, w.z + 0.012 * fall))
        return w

    write_key(kb, flame)
    log("SK_FlameBreath ok")

    # SK_RoofLift
    kb = new_key("SK_RoofLift")

    def roof(i, w):
        t = (w.z - z0) / zspan
        if t < 0.68:
            return w
        ramp = min(1.0, (t - 0.68) / 0.10)
        lift = 0.15 * ramp + 0.04 * vg_weight(host, i, "CHARM") * ramp
        return Vector((w.x, w.y, w.z + lift))

    write_key(kb, roof)
    log("SK_RoofLift ok")

    def make_sway(side: str, degrees: float):
        ang = math.radians(degrees)
        pivot = Vector((mid.x, mid.y, z0 + 0.70 * zspan))
        rot = Matrix.Rotation(ang, 4, "Y")

        def mut(i, w):
            wgt = vg_weight(host, i, side)
            if wgt <= 1e-4:
                t = (w.z - z0) / zspan
                side_ok = (w.x < mid.x) if side.endswith("_L") else (w.x >= mid.x)
                if not (side_ok and 0.62 <= t <= 0.78):
                    return w
                wgt = 0.25
            local = w - pivot
            target = pivot + (rot @ local.to_4d()).to_3d()
            return w.lerp(target, wgt)

        return mut

    kb = new_key("SK_CharmSway_L")
    write_key(kb, make_sway("CHARM_L", -12.0))
    log("SK_CharmSway_L ok")

    kb = new_key("SK_CharmSway_R")
    write_key(kb, make_sway("CHARM_R", 12.0))
    log("SK_CharmSway_R ok")

    # SK_DawnDusk
    kb = new_key("SK_DawnDusk")

    def dawn(i, w):
        t = (w.z - z0) / zspan
        xy = Vector((w.x - mid.x, w.y - mid.y, 0.0))
        if t >= 0.72:
            scale = 1.0 + 0.02 * min(1.0, (t - 0.72) / 0.2)
            if xy.length > 1e-8:
                xy2 = xy * scale
                w = Vector((mid.x + xy2.x, mid.y + xy2.y, w.z - 0.008 * (t - 0.72)))
        elif 0.40 <= t <= 0.62:
            fall = max(0.0, 1.0 - abs(t - 0.51) / 0.13)
            scale = 1.0 - 0.015 * fall
            if xy.length > 1e-8:
                xy2 = xy * scale
                w = Vector((mid.x + xy2.x, mid.y + xy2.y, w.z))
        return w

    write_key(kb, dawn)
    log("SK_DawnDusk ok")

    reset_key_values(host)
    key_names = [k.name for k in host.data.shape_keys.key_blocks]

    basis = host.data.shape_keys.key_blocks["Basis"]
    deltas = {}
    for kb in host.data.shape_keys.key_blocks[1:]:
        mx = 0.0
        for i in range(len(basis.data)):
            d = (kb.data[i].co - basis.data[i].co).length
            if d > mx:
                mx = d
        deltas[kb.name] = mx
    log(f"keys={key_names}")
    log(f"max_deltas_m={deltas}")

    # Export FBX
    unhide(host)
    bpy.ops.object.select_all(action="DESELECT")
    host.select_set(True)
    bpy.context.view_layer.objects.active = host
    if os.path.exists(FBX_OUT):
        os.remove(FBX_OUT)
    bpy.ops.export_scene.fbx(
        filepath=FBX_OUT,
        use_selection=True,
        object_types={"MESH"},
        mesh_smooth_type="OFF",
        use_mesh_modifiers=False,
        add_leaf_bones=False,
        bake_anim=False,
    )
    log(f"FBX {FBX_OUT} bytes={os.path.getsize(FBX_OUT)}")

    bpy.ops.wm.save_mainfile(filepath=BLEND_OUT)

    report = {
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "source_blend": "ZenLantern_V2_L1L2_vcol_charmfix.blend",
        "working_blend": BLEND_OUT,
        "fbx": FBX_OUT,
        "export_object": host.name,
        "verts": len(host.data.vertices),
        "faces": len(host.data.polygons),
        "shape_keys": key_names,
        "max_delta_m": deltas,
        "charms_joined": len(charms),
        "paint_original_untouched": True,
    }
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    md = f"""# L3 Morph Receipt — ZenLantern V2

Date: {report['built_at']} (America/Toronto)

## Summary
Living morph layer on a **joined duplicate** of `zenlantern_V2` + eave charms.
Paint original + L1L2 charmfix source objects kept intact (Save-As workflow).

## Shape keys
| Key | Intent | Max delta (m) |
|---|---|---|
| `SK_FlameBreath` | Fire-box radial expand ~+8% + slight lift | {deltas.get('SK_FlameBreath', 0):.5f} |
| `SK_RoofLift` | Roof tier +15 cm Z (ramped) | {deltas.get('SK_RoofLift', 0):.5f} |
| `SK_CharmSway_L` | Left charms tilt -12° about eave pivot | {deltas.get('SK_CharmSway_L', 0):.5f} |
| `SK_CharmSway_R` | Right charms tilt +12° about eave pivot | {deltas.get('SK_CharmSway_R', 0):.5f} |
| `SK_DawnDusk` | Subtle dusk bias (roof flare / fire soft squash) | {deltas.get('SK_DawnDusk', 0):.5f} |

## Paths
- Working blend: `{BLEND_OUT}`
- Morph FBX: `{FBX_OUT}`
- JSON: `{JSON_OUT}`
- Source (untouched via Save-As): `ZenLantern_V2_L1L2_vcol_charmfix.blend`

## Mesh
- Export object: `{host.name}`
- Verts / faces: **{len(host.data.vertices)}** / **{len(host.data.polygons)}**
- Charms joined: **{len(charms)}**

## UE drivers (plan — not wired this pass)
| Key | Suggested driver |
|---|---|
| SK_FlameBreath | BeatPulse |
| SK_RoofLift | BeatPhase crest one-shot |
| SK_CharmSway_L/R | BassIntensity |
| SK_DawnDusk | W_Melodia_FadeDayNight |

## Gates
- G2 morph FBX authored: **YES** (UE re-import proof still owner session)
- L4 shine / L5 evidence: **NOT this pass**
- Painter SMS / real `.spsm`: still owner-gated (M2)

## Hard-rule compliance
- Paint original not mutated
- No Monolith save_packages / recompile_material
- Melodia naming only
"""
    for path in (RECEIPT, RECEIPT_AUDIT):
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        log(f"receipt {path}")

    log("DONE")
    os._exit(0)


if __name__ == "__main__":
    main()
