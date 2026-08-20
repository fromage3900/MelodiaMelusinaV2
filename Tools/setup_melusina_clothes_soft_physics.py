"""Melusina wardrobe soft-sway + stable cloth preset (Blender 5.1 stage).

Default preset = ``stable_wardrobe`` (Infinity Nikki–style simple cloth):
  - Per-island top Pin (holds main skirt waist + bottom ruffle island attach)
  - Soft low gravity, no self-collision on dense skirt
  - Body-only collider (never re-add Collision on wardrobe Cloth meshes)
  - Mute hidden accordion Cloth
  - Optional gentle Swingy tip sway

Does NOT move Studio_FloorCard. Does NOT touch materials / Water hair.

Usage:
  exec(open(r"G:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\setup_melusina_clothes_soft_physics.py").read())
  # or with preset override before exec:
  #   PRESET = "soft_sway"  # legacy tip-sway heavy
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import bpy

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
AUDIT = ROOT / "Saved" / "Audit" / "melusina_clothes_soft_physics.json"
STABLE_AUDIT = ROOT / "Saved" / "Audit" / "melusina_cloth_stable_2026-07-13.json"
FLOOR_Z_PIN = -0.2935

# Prefer stable_wardrobe; set PRESET="soft_sway" before exec for legacy.
PRESET = globals().get("PRESET", "stable_wardrobe")

SWINGY_LEAVES = [
    f"c_kilt_{i:02d}_04.{s}" for i in range(1, 9) for s in ("l", "r")
] + [
    "c_kilt_main_03_03.l",
    "c_kilt_main_03_03.r",
    "c_kilt_main_05_03.l",
    "c_kilt_main_05_03.r",
    "c_kilt_main_07_03.l",
    "c_kilt_main_07_03.r",
]

SOFT_SWINGY = {
    "pSwDrbDamping": 0.42,
    "pSwDrbDrag": 0.35,
    "pSwDrbStiffness": 0.50,
    "pSwDrbGravityFactor": 0.18,
    "pSwDrbWindFactor": 0.25,
    "pSwDrbFriction": 0.08,
    "pSwDrbCollIntra": False,
    "pSwDrbUseAmplitude": True,
    "pSwDrbAmplitude": 11.0,
    "pSwDrbAmplitude2": 11.0,
    "pSwDrbLockRoll": True,
}

CLOTH_ENABLE = (
    "Melusina_Skirt",
    "Melusina_Shawl",
    "Melusina_SkirtPanel",
    "Melusina_FrontPanel",
    "Melusina_Bow.001",
)

ACCORDION = "outfit_fv2_accordion_FV2 Accordion-Pleated Skirt_fbx_thick"

SKIP = (
    "Melusina_Gloves",
    "Melusina_Sleeve",
    "Melusina_Bow",
)

# Nikki-like soft cloth defaults (stable_wardrobe)
STABLE_CLOTH = {
    "Melusina_Skirt": dict(quality=8, mass=0.12, gravity=0.2, dist_min=0.01, tension=14.0, bending=0.4),
    "Melusina_Shawl": dict(quality=5, mass=0.10, gravity=0.18, dist_min=0.014, tension=10.0, bending=0.3),
    "Melusina_SkirtPanel": dict(quality=5, mass=0.10, gravity=0.2, dist_min=0.012, tension=12.0, bending=0.35),
    "Melusina_FrontPanel": dict(quality=5, mass=0.10, gravity=0.2, dist_min=0.012, tension=12.0, bending=0.35),
    "Melusina_Bow.001": dict(quality=5, mass=0.10, gravity=0.2, dist_min=0.012, tension=12.0, bending=0.35),
}

# Global Z pin fractions for single-island pieces
STABLE_PIN_FRAC = {
    "Melusina_Shawl": 0.32,
    "Melusina_SkirtPanel": 0.35,
    "Melusina_FrontPanel": 0.22,
    "Melusina_Bow.001": 0.35,
}


def _log(msg: str) -> None:
    print(f"[soft-sway] {msg}", flush=True)


def _soft_pb(pb: bpy.types.PoseBone) -> None:
    for k, v in SOFT_SWINGY.items():
        setattr(pb, k, v)
    height = (pb.tail - pb.head).length
    pb.pSwDrbRadius = max(height * 0.20, 0.012)
    pb.custom_shape_scale_xyz = [pb.pSwDrbRadius] * 3


def _clear_pin(pin: bpy.types.VertexGroup, mesh: bpy.types.Mesh) -> None:
    idxs = [v.index for v in mesh.vertices]
    try:
        pin.remove(idxs)
    except RuntimeError:
        for i in idxs:
            try:
                pin.remove([i])
            except RuntimeError:
                pass


def _connected_islands(mesh: bpy.types.Mesh) -> list[list[int]]:
    n = len(mesh.vertices)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for e in mesh.edges:
        union(e.vertices[0], e.vertices[1])
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    return sorted(groups.values(), key=len, reverse=True)


def _pin_island_tops(
    obj: bpy.types.Object,
    top_fraction: float = 0.16,
    hard_fraction: float = 0.08,
) -> dict:
    """Pin the top rim of EACH mesh island (fixes detached bottom ruffles)."""
    mesh = obj.data
    pin = obj.vertex_groups.get("Pin") or obj.vertex_groups.new(name="Pin")
    _clear_pin(pin, mesh)
    islands = _connected_islands(mesh)
    island_info = []
    pinned = 0
    for idxs in islands:
        zs = [mesh.vertices[i].co.z for i in idxs]
        zmax, zmin = max(zs), min(zs)
        span = max(zmax - zmin, 1e-6)
        hard = zmax - span * hard_fraction
        soft = zmax - span * top_fraction
        island_pin = 0
        for i in idxs:
            z = mesh.vertices[i].co.z
            if z < soft:
                continue
            w = 1.0 if z >= hard else (z - soft) / max(hard - soft, 1e-6)
            if w > 0.01:
                pin.add([i], float(w), "REPLACE")
                pinned += 1
                island_pin += 1
        island_info.append(
            {
                "count": len(idxs),
                "zmin": round(zmin, 4),
                "zmax": round(zmax, 4),
                "pinned": island_pin,
                "pin_pct_island": round(100 * island_pin / max(len(idxs), 1), 2),
            }
        )
    return {
        "islands": island_info,
        "pinned_total": pinned,
        "pin_pct": round(100 * pinned / max(len(mesh.vertices), 1), 2),
    }


def _expand_pin(obj: bpy.types.Object, fraction: float = 0.42) -> dict:
    mesh = obj.data
    zs = [v.co.z for v in mesh.vertices]
    zmax, zmin = max(zs), min(zs)
    span = max(zmax - zmin, 1e-6)
    hard = zmax - span * (fraction * 0.4)
    soft = zmax - span * fraction
    pin = obj.vertex_groups.get("Pin") or obj.vertex_groups.new(name="Pin")
    _clear_pin(pin, mesh)
    pinned = 0
    for i, v in enumerate(mesh.vertices):
        z = v.co.z
        if z < soft:
            continue
        w = 1.0 if z >= hard else (z - soft) / max(hard - soft, 1e-6)
        if w > 0.01:
            pin.add([i], float(w), "REPLACE")
            pinned += 1
    return {"pinned": pinned, "pct": round(100 * pinned / max(len(mesh.vertices), 1), 2), "pin": "Pin"}


def _remove_collision_mods(obj: bpy.types.Object) -> list[str]:
    removed = []
    for m in list(obj.modifiers):
        if m.type == "COLLISION":
            removed.append(m.name)
            obj.modifiers.remove(m)
    return removed


def _apply_cloth(
    obj: bpy.types.Object,
    *,
    quality: int = 5,
    mass: float = 0.1,
    gravity: float = 0.2,
    dist_min: float = 0.012,
    tension: float = 12.0,
    bending: float = 0.35,
) -> bpy.types.Modifier:
    cloth = next((m for m in obj.modifiers if m.type == "CLOTH"), None)
    if not cloth:
        cloth = obj.modifiers.new(name="Cloth", type="CLOTH")
    s = cloth.settings
    s.vertex_group_mass = "Pin"
    s.pin_stiffness = 1.0
    s.mass = mass
    s.quality = quality
    s.tension_stiffness = tension
    s.compression_stiffness = tension
    s.shear_stiffness = 5.0
    s.bending_stiffness = bending
    s.air_damping = 2.0
    s.tension_damping = 10.0
    if getattr(s, "effector_weights", None):
        s.effector_weights.gravity = gravity
    c = cloth.collision_settings
    c.use_collision = True
    c.distance_min = dist_min
    c.use_self_collision = False
    cloth.point_cache.frame_start = 1
    cloth.point_cache.frame_end = 96
    cloth.show_viewport = True
    cloth.show_render = True
    return cloth


def _enable_soft_cloth(obj: bpy.types.Object) -> dict:
    """Legacy soft_sway single-island pin helper."""
    created = not any(m.type == "CLOTH" for m in obj.modifiers)
    pin_info = _expand_pin(obj, fraction=0.42)
    _apply_cloth(obj, quality=5, mass=0.08, gravity=0.25, dist_min=0.01, tension=12.0, bending=0.35)
    return {"name": obj.name, "created": created, "pin": pin_info}


def _enable_stable_cloth(obj: bpy.types.Object) -> dict:
    rem = _remove_collision_mods(obj)
    created = not any(m.type == "CLOTH" for m in obj.modifiers)
    if obj.name == "Melusina_Skirt":
        pin_info = _pin_island_tops(obj, top_fraction=0.16, hard_fraction=0.08)
        if pin_info["pin_pct"] < 2.0:
            pin_info = _pin_island_tops(obj, top_fraction=0.22, hard_fraction=0.10)
    else:
        frac = STABLE_PIN_FRAC.get(obj.name, 0.32)
        pin_info = _expand_pin(obj, fraction=frac)
    params = STABLE_CLOTH.get(obj.name, STABLE_CLOTH["Melusina_Shawl"])
    _apply_cloth(obj, **params)
    return {
        "name": obj.name,
        "created": created,
        "removed_collision": rem,
        "pin": pin_info,
        "cloth": params,
    }


def _mute_accordion() -> dict:
    acc = bpy.data.objects.get(ACCORDION)
    if not acc:
        return {"missing": True}
    muted = []
    for m in acc.modifiers:
        if m.type == "CLOTH":
            m.show_viewport = False
            m.show_render = False
            muted.append(m.name)
    acc.hide_viewport = True
    acc.hide_render = True
    return {"object": ACCORDION, "cloth_mods": muted, "hidden": True}


def _add_leaf_drb(rig: bpy.types.Object, root_name: str, extra_child: bool = True) -> str:
    root = rig.pose.bones.get(root_name)
    if not root:
        return "missing"
    if root.bIsDRB:
        _soft_pb(root)
        return "already"

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    for pb in rig.pose.bones:
        pb.select = False
    root.select = True
    try:
        rig.data.bones.active = root.bone
    except Exception:
        pass

    scene = bpy.context.scene
    prev = scene.bSwMultiSelectChain
    scene.bSwMultiSelectChain = False
    try:
        result = bpy.ops.sw.ot_drbadd("EXEC_DEFAULT")
    finally:
        scene.bSwMultiSelectChain = prev
    if result != {"FINISHED"}:
        bpy.ops.object.mode_set(mode="OBJECT")
        return f"op:{result}"

    _soft_pb(root)
    if extra_child:
        ch = rig.data.drbList.boneChainCollection[-1]
        if not ch.bExtraChild:
            ch.bExtraChild = True
        for b in ch.boneCollection:
            pb = rig.pose.bones.get(b.boneName)
            if pb:
                _soft_pb(pb)
    bpy.ops.object.mode_set(mode="OBJECT")
    return "added"


def main() -> dict:
    preset = PRESET if PRESET in ("stable_wardrobe", "soft_sway") else "stable_wardrobe"
    report: dict = {
        "preset": preset,
        "cloth": [],
        "swingy": {},
        "skipped": list(SKIP),
        "accordion": None,
        "floor_z": None,
        "errors": [],
        "colliders": [],
    }

    floor = bpy.data.objects.get("Studio_FloorCard")
    rig = bpy.data.objects.get("character_rig")
    if not rig or rig.type != "ARMATURE":
        raise RuntimeError("character_rig armature not found")

    body = bpy.data.objects.get("Melusina")
    if body and getattr(body, "collision", None):
        body.collision.thickness_outer = 0.012

    for name in CLOTH_ENABLE:
        obj = bpy.data.objects.get(name)
        if not obj:
            report["cloth"].append({name: "missing"})
            continue
        try:
            if preset == "stable_wardrobe":
                report["cloth"].append(_enable_stable_cloth(obj))
            else:
                report["cloth"].append(_enable_soft_cloth(obj))
        except Exception as exc:
            report["errors"].append(f"cloth {name}: {exc}")

    if preset == "stable_wardrobe":
        report["accordion"] = _mute_accordion()

    # Swingy tips (both presets; soft_sway always, stable optional via ENABLE_SWINGY)
    do_swingy = preset == "soft_sway" or bool(globals().get("ENABLE_SWINGY", True))
    if do_swingy:
        for root_name in SWINGY_LEAVES:
            try:
                report["swingy"][root_name] = _add_leaf_drb(rig, root_name, extra_child=True)
            except Exception as exc:
                report["swingy"][root_name] = f"error:{exc}"

        for pb in rig.pose.bones:
            if getattr(pb, "bIsDRB", False):
                _soft_pb(pb)

        if hasattr(rig, "bSwSimulate"):
            rig.bSwSimulate = True
        if hasattr(rig, "swWindMean"):
            rig.swWindMean = 0.12
        if hasattr(rig, "swWindStd"):
            rig.swWindStd = 0.04

    coll = bpy.data.collections.get("Melusina_WaterFX")
    if coll:
        coll.hide_viewport = False
        coll.hide_render = False
    for name in ("FF_MelusinaHair_Domain", "FF_MelusinaHair_Drip", "FF_MelusinaHair_Sheet", "fluid_surface"):
        o = bpy.data.objects.get(name)
        if not o:
            continue
        o.hide_set(False)
        o.hide_viewport = False
        o.hide_render = False

    bpy.ops.object.mode_set(mode="OBJECT")
    report["drb_bones"] = sum(1 for p in rig.pose.bones if getattr(p, "bIsDRB", False))
    report["swingy_settings"] = SOFT_SWINGY if do_swingy else None
    report["filepath"] = bpy.data.filepath
    report["colliders"] = [
        o.name
        for o in bpy.data.objects
        for m in o.modifiers
        if m.type == "COLLISION" and m.show_viewport
    ]
    if floor:
        if abs(floor.location.z - FLOOR_Z_PIN) > 0.001:
            floor.location.z = FLOOR_Z_PIN
        report["floor_z"] = round(floor.location.z, 6)

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2)
    AUDIT.write_text(text, encoding="utf-8")
    if preset == "stable_wardrobe":
        STABLE_AUDIT.write_text(text, encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
