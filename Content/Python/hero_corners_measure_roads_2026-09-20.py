# -*- coding: utf-8 -*-
"""READ-ONLY: measure HeroCorner anchors + existing splines/roads in L_MelusinaMorning.
No spawn/destroy. Writes Saved/Audit/hero_corners_road_measure_2026-09-20.json
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "hero_corners_road_measure_2026-09-20.json"

ANCHORS = {
    "WestRim_pcg": (-3200.0, 1880.0, 1285.55),
    "EastBank_pcg": (-1450.0, 1520.0, 2585.50),
    "MeadowChorus_cam": (-3197.79, 742.03, 585.86),
    "NorthDress_pcg": (900.0, 2300.0, 959.69),
    "WestRim_cam": (-2550.0, 1480.0, 2515.51),
    "EastBank_cam": (-1950.0, 2070.0, 2905.50),
    "NorthDress_cam": (100.0, 1700.0, 1409.69),
}

INTEREST = (
    "Spline", "Road", "Path", "Walk", "InstanceOnSpline", "GreyRoad", "GreySpline",
    "Escher", "TeaGarden", "BP_InstanceOnSpline", "BP_RoadBuilder",
)


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _cls(a):
    try:
        return a.get_class().get_name()
    except Exception:
        return ""


def _horiz(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _ground(world, x, y, z_hint):
    start = unreal.Vector(x, y, z_hint + 5000.0)
    end = unreal.Vector(x, y, z_hint - 8000.0)
    hit = unreal.SystemLibrary.line_trace_single(
        world, start, end,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
    )
    try:
        t = hit.to_tuple()
    except Exception:
        return None
    if not t or not t[0]:
        return None
    actor = t[9]
    lab = _label(actor) if actor else ""
    return {
        "loc": [float(t[4].x), float(t[4].y), float(t[4].z)],
        "normal_z": float(t[5].z),
        "actor": lab,
    }


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    pairs = [
        ("WestRim_pcg", "MeadowChorus_cam"),
        ("WestRim_pcg", "EastBank_pcg"),
        ("EastBank_pcg", "NorthDress_pcg"),
        ("MeadowChorus_cam", "NorthDress_pcg"),
        ("WestRim_cam", "EastBank_cam"),
        ("EastBank_cam", "NorthDress_cam"),
    ]
    distances = {}
    for a, b in pairs:
        distances["%s__%s" % (a, b)] = {
            "horiz_uu": round(_horiz(ANCHORS[a], ANCHORS[b]), 1),
            "dz_uu": round(ANCHORS[b][2] - ANCHORS[a][2], 1),
        }

    ground = {}
    for name, (x, y, z) in ANCHORS.items():
        g = _ground(world, x, y, z)
        ground[name] = g

    existing = []
    for a in svc.get_all_level_actors():
        lab = _label(a)
        cn = _cls(a)
        blob = lab + " " + cn
        if any(tok.lower() in blob.lower() for tok in INTEREST):
            loc = a.get_actor_location()
            existing.append({
                "label": lab,
                "class": cn,
                "loc": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
            })

    # live cam/pcg reconcile
    live = {}
    for want in (
        "WC_HeroCorner_WestRim_Cam", "WC_HeroCorner_EastBank_Cam",
        "WC_HeroCorner_MeadowChorus_Cam", "WC_HeroCorner_NorthDress_Cam",
        "WC_HeroCorner_WestRim_PCG", "WC_HeroCorner_EastBank_PCG",
        "WC_morning_rainbow_bloom_Field", "WC_HeroCorner_NorthDress_PCG",
        "Morning_SheepDell_Lake", "SeaAbove_InfiniteOcean_Canopy",
    ):
        found = None
        for a in svc.get_all_level_actors():
            if _label(a) == want or want in _label(a):
                loc = a.get_actor_location()
                found = {
                    "label": _label(a),
                    "class": _cls(a),
                    "loc": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
                }
                break
        live[want] = found

    report = {
        "schema": "melodia.hero_corners_road_measure.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "anchors": {k: list(v) for k, v in ANCHORS.items()},
        "distances_horiz_uu": distances,
        "ground_at_anchors": ground,
        "existing_spline_roadish": existing,
        "live_actors_of_interest": live,
        "bp_paths": {
            "InstanceOnSpline": "/Game/Actor_BP/BP_InstanceOnSpline",
            "InstanceOnSpline_alt": "/Game/EnvSandbox/PCG/Universal/BP_InstanceOnSpline",
            "RoadBuilder": "/Game/Actor_BP/BP_RoadBuilder",
            "greybox": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("ROAD_MEASURE " + json.dumps({
        "existing": len(existing),
        "lake": live.get("Morning_SheepDell_Lake") is not None,
        "ocean_hit": any(live.get(k) for k in live if "Ocean" in k or "ocean" in k),
        "out": str(OUT),
    }))
    unreal.log("ROAD_MEASURE wrote " + str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
