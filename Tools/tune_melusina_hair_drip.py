# -*- coding: utf-8 -*-
"""Minimal Melusina water-hair - Flip globules + drip as the hair body.

Product: visible hair = Flip `fluid_surface` (coalescing globules + drip),
not Stylized Hair PRO strands and not a water shader on SK_MelusinaHair.

  Hair Strand.*              = Flip obstacle / guide (hide_render for beauty)
  FF_MelusinaHair_Domain     = hide_render (cube filled Cam_Beauty)
  fluid_surface + drip       = hair body
  Niagara Melusina_WaterFX   = UE drip (closed-editor prep; do not drive Unreal)

Do not start Flip bake while a beauty still is rendering.
Rebake only if globules are missing from the existing 1-240 cache.

Usage (live 5.2 GUI, same PID - no second Blender):
  exec(open(r"G:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\tune_melusina_hair_drip.py").read())
"""
from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
FLIP_CACHE = ROOT / "KitbashExport" / "flip_cache_melusina_waterhair"
AUDIT = ROOT / "Saved" / "Audit" / "melusina_hair_drip_tune.json"
FLOOR_Z = -0.2935
HAIR_NAMES = ("Hair Strand.002", "Hair Strand.004", "Hair Strand.007")


def _log(msg: str) -> None:
    print(f"[hair-drip] {msg}", flush=True)


def _world_bbox(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    mw = obj.matrix_world
    corners = [mw @ Vector(c) for c in obj.bound_box]
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    zs = [c.z for c in corners]
    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


def _hair_tip(obj: bpy.types.Object) -> Vector | None:
    """Lowest ~2% of points. Hair Strand.002 is CURVES on v22; 004/007 are MESH."""
    pts: list[Vector] = []
    if obj.type == "CURVES":
        attr = obj.data.attributes.get("position")
        if attr is None:
            return None
        pts = [obj.matrix_world @ Vector(item.vector) for item in attr.data]
    elif hasattr(obj.data, "vertices"):
        pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    if not pts:
        return None
    zs = sorted(p.z for p in pts)
    thresh = zs[max(0, int(len(zs) * 0.02))]
    tips = [p for p in pts if p.z <= thresh + 1e-5]
    if not tips:
        return None
    return sum(tips, Vector()) / len(tips)


def _ensure_flip(obj: bpy.types.Object, otype: str) -> str:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if not getattr(obj, "flip_fluid", None) or not getattr(obj.flip_fluid, "is_active", True):
        try:
            bpy.ops.flip_fluid_operators.flip_fluid_add()
        except Exception as exc:
            return f"add_failed:{exc}"
    try:
        obj.flip_fluid.object_type = otype
    except Exception as exc:
        return f"type_failed:{exc}"
    if otype in ("TYPE_FLUID", "TYPE_INFLOW"):
        try:
            if hasattr(obj.flip_fluid, "fluid") and hasattr(obj.flip_fluid.fluid, "is_inflow"):
                obj.flip_fluid.fluid.is_inflow = True
        except Exception:
            pass
        # Prefer native inflow when available
        if otype != "TYPE_INFLOW":
            try:
                obj.flip_fluid.object_type = "TYPE_INFLOW"
                return "TYPE_INFLOW"
            except Exception:
                pass
    return otype


def main() -> dict:
    report: dict = {"actions": [], "errors": []}

    floor = bpy.data.objects.get("Studio_FloorCard")
    if floor and abs(floor.location.z - FLOOR_Z) > 0.001:
        report["errors"].append(f"FloorCard Z drift {floor.location.z}")

    wfx = bpy.data.collections.get("Melusina_WaterFX")
    domain = bpy.data.objects.get("FF_MelusinaHair_Domain")
    drip = bpy.data.objects.get("FF_MelusinaHair_Drip")
    sheet = bpy.data.objects.get("FF_MelusinaHair_Sheet")
    if not wfx or not domain or not drip:
        raise RuntimeError("Missing Melusina_WaterFX / domain / drip - run upgrade_stage_core_and_waterhair.py")

    # Tip samples
    tips: dict[str, Vector] = {}
    hair_mins: list[Vector] = []
    hair_maxs: list[Vector] = []
    for name in HAIR_NAMES:
        ob = bpy.data.objects.get(name)
        if not ob:
            continue
        tip = _hair_tip(ob)
        if tip:
            tips[name] = tip
        mn, mx = _world_bbox(ob)
        hair_mins.append(mn)
        hair_maxs.append(mx)

    if not tips:
        raise RuntimeError("No Hair Strand.* tips - Melusina hair missing from stage")

    # Prefer front bangs strand for "little drip"
    primary = tips.get("Hair Strand.002") or next(iter(tips.values()))
    report["tips"] = {k: [round(x, 4) for x in v] for k, v in tips.items()}

    # --- Domain: shift so current bbox covers hair+pad (preserve mesh authorship) ---
    dmn, dmx = _world_bbox(domain)
    dcenter = (dmn + dmx) * 0.5
    hmn = Vector((min(v.x for v in hair_mins), min(v.y for v in hair_mins), min(v.z for v in hair_mins)))
    hmx = Vector((max(v.x for v in hair_maxs), max(v.y for v in hair_maxs), max(v.z for v in hair_maxs)))
    pad = Vector((0.35, 0.40, 0.45))
    target_min = hmn - pad
    target_max = hmx + pad
    # Keep Z from just below lowest tip to above bangs
    target_min.z = min(target_min.z, primary.z - 0.55)
    target_max.z = max(target_max.z, primary.z + 0.35)
    tcenter = (target_min + target_max) * 0.5
    delta = tcenter - dcenter
    domain.location += delta
    # Nudge uniform scale if domain is too small after shift
    dmn2, dmx2 = _world_bbox(domain)
    need = target_max - target_min
    have = dmx2 - dmn2
    sx = max(1.0, (need.x / max(have.x, 1e-4)) * 1.05)
    sy = max(1.0, (need.y / max(have.y, 1e-4)) * 1.05)
    sz = max(1.0, (need.z / max(have.z, 1e-4)) * 1.05)
    if sx > 1.01 or sy > 1.01 or sz > 1.01:
        domain.scale = Vector((domain.scale.x * sx, domain.scale.y * sy, domain.scale.z * sz))
    report["actions"].append(
        {
            "domain_delta": [round(x, 4) for x in delta],
            "domain_loc": [round(x, 4) for x in domain.location],
            "domain_scale": [round(x, 4) for x in domain.scale],
            "target_bbox_min": [round(x, 4) for x in target_min],
            "target_bbox_max": [round(x, 4) for x in target_max],
        }
    )

    # --- Little drip at bangs tip (continuous inflow) ---
    # Inflow along the strand volume (not tips-only)
    hmid = (hmn + hmx) * 0.5
    drip.location = Vector((hmid.x, hmid.y, (hmn.z + hmx.z) * 0.5))
    length = max(hmx.z - hmn.z, 0.25)
    drip.scale = (0.35, 0.35, max(length * 0.55, 0.45))
    drip.hide_viewport = False
    drip.hide_render = False
    drip.hide_set(False)
    report["actions"].append(
        {
            "drip_loc": [round(x, 4) for x in drip.location],
            "drip_scale": [round(x, 4) for x in drip.scale],
            "anchored_to": "Hair Strand.002" if "Hair Strand.002" in tips else "first_tip",
        }
    )

    # --- Product visibility: hair IS the Flip surface (globules + drip) ---
    # Domain cube filled Cam_Beauty - hide from render. Show fluid_surface + drip.
    domain.hide_render = True
    domain.hide_viewport = True
    drip.hide_viewport = False
    drip.hide_render = False
    drip.hide_set(False)
    if sheet:
        sheet.hide_viewport = True
        sheet.hide_render = True
        sheet.hide_set(True)
        try:
            if getattr(sheet, "flip_fluid", None):
                sheet.flip_fluid.is_enabled = True
        except Exception:
            pass
        report["actions"].append({"sheet": "inflow_enabled_hide_render"})
    wfx.hide_viewport = False
    wfx.hide_render = False
    surf = bpy.data.objects.get("fluid_surface") or bpy.data.objects.get("FF_fluid_surface")
    if surf:
        surf.hide_render = False
        surf.hide_viewport = False
        surf.hide_set(False)
        report["actions"].append({"fluid_surface": "shown_as_hair_body"})

    # Strands = Flip obstacle / guide; hide strand look for beauty
    for name in HAIR_NAMES:
        ob = bpy.data.objects.get(name)
        if not ob:
            continue
        ob.hide_render = True
        try:
            _ensure_flip(ob, "TYPE_OBSTACLE")
        except Exception as exc:
            report["errors"].append(f"{name} obstacle: {exc}")
    report["actions"].append({"strands": "obstacle_hide_render"})

    # FLIP types - drip is inflow along the hair volume, not a one-shot fluid blob
    report["flip_types"] = {
        "domain": _ensure_flip(domain, "TYPE_DOMAIN"),
        "drip": _ensure_flip(drip, "TYPE_INFLOW"),
    }
    if sheet:
        report["flip_types"]["sheet"] = _ensure_flip(sheet, "TYPE_INFLOW")

    # Soft sim window - match existing 1-240 cache; do not start a bake here
    FLIP_CACHE.mkdir(parents=True, exist_ok=True)
    try:
        dprops = domain.flip_fluid.domain
        if hasattr(dprops, "cache") and hasattr(dprops.cache, "cache_directory"):
            dprops.cache.cache_directory = str(FLIP_CACHE)
        if hasattr(dprops, "simulation"):
            sim = dprops.simulation
            if hasattr(sim, "resolution"):
                sim.resolution = 72
            if hasattr(sim, "frame_start"):
                sim.frame_start = 1
            if hasattr(sim, "frame_end"):
                sim.frame_end = 240
        # Surface tension high enough to bead / globulate
        for attr_path in (
            ("world", "surface_tension"),
            ("world", "surface_tension_accuracy"),
            ("surface_tension",),
        ):
            try:
                obj = dprops
                for part in attr_path[:-1]:
                    obj = getattr(obj, part)
                setattr(obj, attr_path[-1], 0.45 if attr_path[-1] == "surface_tension" else getattr(obj, attr_path[-1], 0.45))
            except Exception:
                pass
        try:
            world = getattr(dprops, "world", None)
            if world is not None and hasattr(world, "surface_tension"):
                world.surface_tension = 0.45
                if hasattr(world, "enable_surface_tension"):
                    world.enable_surface_tension = True
        except Exception as exc:
            report["errors"].append(f"surface_tension: {exc}")
        report["actions"].append({
            "resolution": 72, "frame_end": 240, "cache": str(FLIP_CACHE),
            "rebake": "only_if_globules_missing",
        })
    except Exception as exc:
        report["errors"].append(f"domain props: {exc}")

    # Post-check: drip inside domain?
    dmn3, dmx3 = _world_bbox(domain)
    dp = drip.matrix_world.translation
    inside = (
        dmn3.x <= dp.x <= dmx3.x
        and dmn3.y <= dp.y <= dmx3.y
        and dmn3.z <= dp.z <= dmx3.z
    )
    report["drip_inside_domain"] = inside
    report["domain_bbox_after"] = {
        "min": [round(x, 4) for x in dmn3],
        "max": [round(x, 4) for x in dmx3],
    }
    if not inside:
        report["errors"].append("Drip still outside domain after shift - inspect transforms")

    bobj = list(FLIP_CACHE.rglob("*.bobj")) if FLIP_CACHE.exists() else []
    report["cache_bobj_count"] = len(bobj)
    report["lanes"] = {
        "hair_body": "Flip fluid_surface - globules + drip (product)",
        "drip_inflow": "FF_MelusinaHair_Drip TYPE_INFLOW along strand volume",
        "strands": "Hair Strand.* Flip obstacle / hide_render",
        "fallback_ue": "SK_MelusinaHair + ABP_Melusina_WaterHair until owner sockets GC",
        "liquifeel": "Asset_melusina_elixir untouched",
    }
    report["next"] = [
        "Do not start Flip bake while a beauty still is rendering",
        "Rebake 1-240 only if fluid_surface is a connected mass with no globules",
        "Export Alembic with domain frame range; socket GC + Niagara to head_x",
    ]
    if floor:
        report["floor_z"] = round(floor.location.z, 6)

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _log(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
