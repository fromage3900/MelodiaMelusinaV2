# -*- coding: utf-8 -*-
"""Rebuild WC_SpireRamp_* snapped to Melusina house / island edges; level yaw only.
- One stair mesh + one rail mesh, uniform scale
- pitch=0 roll=0; yaw = radial tangent (degrees)
- Per-step radius from outward edge probe to BrushifyIsland_*/Melusina/SM_classic_arch_*
- Destroys prior WC_SpireRamp_* only; keeps shaft/chamber/portal
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "spire_atlantis_ramp_edge_snap_2026-09-20.json"

STAIR = "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StairsA"
RAIL = "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailA"
CENTER = (160.0, 1600.0)
BASE_Z = 914.0
TOP_Z = 3094.0
STEPS = 36
TURNS = 1.25
R_MIN = 220.0
R_MAX = 520.0
R_DEFAULT = 300.0
STAIR_SCALE = 0.35
RAIL_SCALE = 0.30
YAW_OFFSET = 90.0  # tread faces along climb tangent

GOOD = ("BrushifyIsland_", "Melusina", "Melusine", "House", "SM_classic_arch", "Island")
IGNORE_PREFIX = ("WC_SpireRamp_", "WC_GreySpire_", "WC_GreyGrotto_", "WC_GreyRoad_",
                 "WC_PhyloWalk_", "WC_WalkPath_", "WC_MA_Dress_")


def _lab(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _ignore(svc):
    return [a for a in svc.get_all_level_actors() if any(_lab(a).startswith(p) for p in IGNORE_PREFIX)]


def _good(lab):
    if not lab or any(lab.startswith(p) for p in IGNORE_PREFIX):
        return False
    return any(t in lab for t in GOOD)


def _trace(world, start, end, ignore):
    hit = unreal.SystemLibrary.line_trace_single(
        world, start, end,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
    )
    try:
        t = hit.to_tuple()
    except Exception:
        return None
    if not t or not t[0]:
        return None
    lab = _lab(t[9]) if t[9] else ""
    if not _good(lab):
        return None
    return t[4], lab, float(t[5].z)


def _edge_radius(world, cx, cy, z, ang, ignore):
    """Cast outward horizontally; return radius to first good hit."""
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    # also slightly downward so we catch ledges
    for z_off in (0.0, -40.0, 40.0, -80.0):
        start = unreal.Vector(cx + cos_a * R_MIN, cy + sin_a * R_MIN, z + z_off)
        end = unreal.Vector(cx + cos_a * R_MAX, cy + sin_a * R_MAX, z + z_off - 30.0)
        h = _trace(world, start, end, ignore)
        if h:
            hx, hy = float(h[0].x), float(h[0].y)
            r = math.hypot(hx - cx, hy - cy)
            return max(R_MIN, min(R_MAX, r - 40.0)), h[1]  # sit just inside edge
    # downward ground at default radius as fallback
    x = cx + cos_a * R_DEFAULT
    y = cy + sin_a * R_DEFAULT
    g = _trace(
        world,
        unreal.Vector(x, y, z + 2000.0),
        unreal.Vector(x, y, z - 4000.0),
        ignore,
    )
    if g:
        return R_DEFAULT, g[1]
    return R_DEFAULT, "fallback"


def _ground_z(world, x, y, z_hint, ignore):
    g = _trace(
        world,
        unreal.Vector(x, y, z_hint + 2500.0),
        unreal.Vector(x, y, z_hint - 5000.0),
        ignore,
    )
    if g:
        return float(g[0].z), g[1]
    return z_hint, "no_ground"


def _destroy_ramps(svc):
    gone = []
    for a in list(svc.get_all_level_actors()):
        lab = _lab(a)
        if lab.startswith("WC_SpireRamp_"):
            if svc.destroy_actor(a):
                gone.append(lab)
    return gone


def _spawn(mesh, loc, yaw_deg, scale, label, ignore):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        mesh, loc, unreal.Rotator(0.0, yaw_deg, 0.0)  # pitch, yaw, roll — level tread
    )
    if not actor:
        return None
    actor.set_actor_label(label)
    try:
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        # force level again after spawn
        actor.set_actor_rotation(unreal.Rotator(0.0, yaw_deg, 0.0), False)
        actor.set_folder_path("HeroCorners/SpireRamp")
        actor.tags = ["Portfolio", "SpireRamp", "Atlantis", "Belvedere"]
    except Exception:
        pass
    ignore.append(actor)
    return actor


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignore = _ignore(svc)
    stair = EAL.load_asset(STAIR) if EAL.does_asset_exist(STAIR) else None
    rail = EAL.load_asset(RAIL) if EAL.does_asset_exist(RAIL) else None
    report = {
        "schema": "melodia.spire_atlantis_ramp_edge_snap.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "destroyed": _destroy_ramps(svc),
        "stair_mesh": STAIR,
        "rail_mesh": RAIL,
        "uniform_scale": {"stair": STAIR_SCALE, "rail": RAIL_SCALE},
        "rotation_policy": "pitch=0 roll=0 yaw=tangent+90",
        "placed": [],
    }
    if not stair:
        report["error"] = "missing stair mesh"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("EDGE_SNAP_ERR no stair")
        return 1

    cx, cy = CENTER
    placed = 0
    for i in range(STEPS):
        t = i / max(1, STEPS - 1)
        ang = t * TURNS * 2.0 * math.pi
        z_helix = BASE_Z + t * (TOP_Z - BASE_Z)
        # yaw: tangent to circle (perpendicular to radius)
        yaw = math.degrees(ang) + YAW_OFFSET

        r, edge_lab = _edge_radius(world, cx, cy, z_helix, ang, ignore)
        x = cx + math.cos(ang) * r
        y = cy + math.sin(ang) * r
        # prefer level on local ground if near island/house; else keep helix z
        gz, g_lab = _ground_z(world, x, y, z_helix, ignore)
        # blend: if ground close to helix band, snap z to ground+lift; else keep helix
        if abs(gz - z_helix) < 350.0:
            z = gz + 8.0
            z_src = g_lab
        else:
            z = z_helix
            z_src = "helix_" + edge_lab

        loc = unreal.Vector(x, y, z)
        lab = "WC_SpireRamp_Stair_%02d" % i
        a = _spawn(stair, loc, yaw, STAIR_SCALE, lab, ignore)
        if a:
            placed += 1
            report["placed"].append({
                "label": lab, "r": r, "yaw": yaw, "pitch": 0.0, "roll": 0.0,
                "z": z, "edge": edge_lab, "z_src": z_src,
                "scale": STAIR_SCALE,
            })

        if rail and i % 3 == 0:
            # rail slightly outside
            rr = r + 35.0
            rx = cx + math.cos(ang) * rr
            ry = cy + math.sin(ang) * rr
            rloc = unreal.Vector(rx, ry, z + 40.0)
            rlab = "WC_SpireRamp_Rail_%02d" % i
            ra = _spawn(rail, rloc, yaw, RAIL_SCALE, rlab, ignore)
            if ra:
                placed += 1
                report["placed"].append({
                    "label": rlab, "r": rr, "yaw": yaw, "pitch": 0.0, "roll": 0.0,
                    "z": z + 40.0, "edge": edge_lab, "scale": RAIL_SCALE,
                })

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    report["counts"] = {"placed": placed, "steps": STEPS}
    # yaw uniqueness check
    yaws = [p["yaw"] for p in report["placed"] if "Stair" in p["label"]]
    pitches = [p["pitch"] for p in report["placed"]]
    report["rotation_check"] = {
        "all_pitch_zero": all(abs(p) < 1e-6 for p in pitches),
        "all_roll_zero": True,
        "yaw_min": min(yaws) if yaws else None,
        "yaw_max": max(yaws) if yaws else None,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("EDGE_SNAP_RAMP " + json.dumps(report["counts"] | report["rotation_check"]))
    unreal.log("EDGE_SNAP_RAMP wrote " + str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
