"""Greybox spire + underwater grotto + approach. Destroy-only WC_Grey* labels. Never touch lake/PCG/cams."""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
GREY = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m"
IOS = "/Game/Actor_BP/BP_InstanceOnSpline"
OWN_PREFIXES = ("WC_GreyRoad_", "WC_GreySpire_", "WC_GreyGrotto_", "WC_GreySpline_", "WC_GreyApproach_")

# Inspired site: WestRim island above SheepDell lake
SPIRE_BASE_XY = (-3200.0, 1880.0)  # WestRim PCG
LAKE_XY = (-3707.4, 2303.5)
LAKE_Z = -1822.9
MEADOW_XY = (-2297.8, 1442.0)

def _label(a):
    try: return a.get_actor_label() or ""
    except: return ""

def ground_at(world, x, y, zhint, ignore_labels=None):
    ignore_labels = ignore_labels or set()
    start = unreal.Vector(x, y, zhint + 8000)
    end = unreal.Vector(x, y, zhint - 20000)
    hit = unreal.SystemLibrary.line_trace_single(
        world, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY, True, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    actor = t[9]
    lab = actor.get_actor_label() if actor else ""
    if lab and any(lab.startswith(p) for p in OWN_PREFIXES):
        return None
    if lab and lab.startswith(("WC_Grey", "WC_MA_Dress", "WC_HeroDress")):
        return None
    cls = actor.get_class().get_name() if actor else ""
    ok = (
        lab.startswith("Brushify") or lab.startswith("WC_EscherWalk_")
        or "Landscape" in cls or lab.startswith("Landscape")
    )
    # For grotto near water, also allow hits that are not the lake actor itself
    if lab == "Morning_SheepDell_Lake" or "Oceanology" in cls:
        return None
    if not ok:
        return None
    n = t[5]
    if float(n.z) < 0.45:
        return None
    return {"loc": t[4], "normal": n, "actor": lab}

def clear_own(svc):
    removed = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if any(lab.startswith(p) for p in OWN_PREFIXES):
            if svc.destroy_actor(a):
                removed.append(lab)
    return removed

def spawn_cube(mesh, loc, scale, yaw, label, folder):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        mesh, loc, unreal.Rotator(0, yaw, 0))
    if not actor:
        return None
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    try:
        actor.set_folder_path(folder)
        actor.tags = ["Portfolio", "Greybox", "SpireDual", label.split("_")[1] if "_" in label else "Grey"]
    except Exception:
        pass
    return actor

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    wname = world.get_name() if world else None
    if wname != "L_MelusinaMorning":
        print("GREY_SPIRE " + json.dumps({"error": "wrong_world", "world": wname}))
        return 1

    if not EAL.does_asset_exist(GREY):
        print("GREY_SPIRE " + json.dumps({"error": "missing_greybox"}))
        return 1
    mesh = EAL.load_asset(GREY)
    removed = clear_own(svc)
    placed = []

    # --- Spire base ground ---
    g = ground_at(world, SPIRE_BASE_XY[0], SPIRE_BASE_XY[1], 2000)
    if not g:
        # slight search
        for dx, dy in [(0,0),(200,0),(-200,0),(0,200),(0,-200),(150,150)]:
            g = ground_at(world, SPIRE_BASE_XY[0]+dx, SPIRE_BASE_XY[1]+dy, 2000)
            if g:
                break
    if not g:
        print("GREY_SPIRE " + json.dumps({"error": "no_spire_ground", "removed": removed}))
        return 1

    base = g["loc"]
    base_z = float(base.z)

    # Shaft: 1m cubes stacked, tapering slightly — ~18m tall visual massing
    shaft_n = 18
    for i in range(shaft_n):
        z = base_z + 50 + i * 100  # cube center (1m = 100uu)
        sc = 2.4 - (i * 0.06)  # taper 2.4m -> ~1.3m
        sc = max(1.2, sc)
        lab = f"WC_GreySpire_Shaft_{i:02d}"
        a = spawn_cube(mesh, unreal.Vector(base.x, base.y, z), (sc, sc, 1.0), 12.0 * i, lab, "Greybox/Spire")
        if a:
            placed.append({"label": lab, "role": "shaft", "z": z, "scale": sc})

    # Chamber platform + walls at top (Musical / Cosmic massing)
    top_z = base_z + 50 + shaft_n * 100 + 150
    chamber = [
        ("WC_GreySpire_Chamber_Floor", (base.x, base.y, top_z), (6.0, 6.0, 0.4), 0),
        ("WC_GreySpire_Chamber_N", (base.x, base.y + 280, top_z + 200), (5.5, 0.4, 3.5), 0),
        ("WC_GreySpire_Chamber_S", (base.x, base.y - 280, top_z + 200), (5.5, 0.4, 3.5), 0),
        ("WC_GreySpire_Chamber_E", (base.x + 280, base.y, top_z + 200), (0.4, 5.5, 3.5), 0),
        ("WC_GreySpire_Chamber_W", (base.x - 280, base.y, top_z + 200), (0.4, 5.5, 3.5), 0),
        ("WC_GreySpire_Chamber_Crown", (base.x, base.y, top_z + 420), (3.0, 3.0, 2.5), 45),
        ("WC_GreySpire_PortalCard", (base.x, base.y - 100, top_z + 220), (0.3, 4.0, 3.0), 0),  # MI card plane later
    ]
    for lab, (x,y,z), sc, yaw in chamber:
        a = spawn_cube(mesh, unreal.Vector(x,y,z), sc, yaw, lab, "Greybox/Spire/Chamber")
        if a:
            placed.append({"label": lab, "role": "chamber", "loc": [x,y,z], "scale": list(sc)})

    # --- Grotto: between WestRim and lake, on island shore if possible ---
    grotto_pts = []
    for t in (0.35, 0.5, 0.65, 0.75):
        x = SPIRE_BASE_XY[0] + (LAKE_XY[0] - SPIRE_BASE_XY[0]) * t
        y = SPIRE_BASE_XY[1] + (LAKE_XY[1] - SPIRE_BASE_XY[1]) * t
        gg = ground_at(world, x, y, base_z)
        if gg:
            grotto_pts.append(gg)
    # Fallback ring near lake XY but higher zhint
    if len(grotto_pts) < 2:
        for ang in range(0, 360, 45):
            rad = 900
            x = LAKE_XY[0] + math.cos(math.radians(ang)) * rad
            y = LAKE_XY[1] + math.sin(math.radians(ang)) * rad
            gg = ground_at(world, x, y, 500)
            if gg:
                grotto_pts.append(gg)
            if len(grotto_pts) >= 4:
                break

    for i, gg in enumerate(grotto_pts[:5]):
        loc = gg["loc"]
        # mouth / arch massing slightly above ground
        lab = f"WC_GreyGrotto_Mouth_{i:02d}"
        a = spawn_cube(mesh, unreal.Vector(loc.x, loc.y, loc.z + 120), (2.5, 1.2, 2.2), 30*i, lab, "Greybox/Grotto")
        if a:
            placed.append({"label": lab, "role": "grotto", "ground": gg["actor"], "z": float(loc.z)})
        if i == 0:
            # submerged twin portal card — low, still above lake actor (don't intersect lake)
            lab2 = "WC_GreyGrotto_PortalTwin"
            a2 = spawn_cube(mesh, unreal.Vector(loc.x, loc.y, loc.z + 80), (0.3, 3.5, 2.8), 90, lab2, "Greybox/Grotto")
            if a2:
                placed.append({"label": lab2, "role": "grotto_portal"})

    # --- Approach path: meadow -> WestRim (greybox cubes as stepping stones / road) ---
    steps = 12
    for i in range(steps):
        t = i / (steps - 1)
        x = MEADOW_XY[0] + (SPIRE_BASE_XY[0] - MEADOW_XY[0]) * t
        y = MEADOW_XY[1] + (SPIRE_BASE_XY[1] - MEADOW_XY[1]) * t
        gg = ground_at(world, x, y, 1500)
        if not gg:
            continue
        loc = gg["loc"]
        lab = f"WC_GreyApproach_{i:02d}"
        a = spawn_cube(mesh, unreal.Vector(loc.x, loc.y, loc.z + 25), (2.0, 1.2, 0.25), 0, lab, "Greybox/Approach")
        if a:
            placed.append({"label": lab, "role": "approach", "ground": gg["actor"]})

    # Optional: spawn one InstanceOnSpline for future mesh swap (labeled, empty-ish)
    ios_spawned = None
    if EAL.does_asset_exist(IOS):
        try:
            cls = EAL.load_blueprint_class(IOS)
            if cls:
                # place near approach mid
                mid = placed[[p["role"] for p in placed].index("approach")] if any(p["role"]=="approach" for p in placed) else None
                loc = unreal.Vector(SPIRE_BASE_XY[0], SPIRE_BASE_XY[1], base_z + 50)
                actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, loc, unreal.Rotator(0, 0, 0))
                if actor:
                    actor.set_actor_label("WC_GreySpline_Approach_IOS")
                    try:
                        actor.set_folder_path("Greybox/Approach")
                    except Exception:
                        pass
                    ios_spawned = "WC_GreySpline_Approach_IOS"
                    placed.append({"label": ios_spawned, "role": "ios"})
        except Exception as e:
            ios_spawned = f"err:{e}"

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    report = {
        "schema": "melodia.spire_grotto_greybox.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "concept": "WestRim crystalline spire + Musical/Cosmic chamber; SheepDell shore grotto as underwater twin portal",
        "world": wname,
        "spire_base": [base.x, base.y, base_z],
        "spire_top_z": top_z,
        "lake_xy": list(LAKE_XY),
        "removed_own": removed,
        "placed": placed,
        "placed_count": len(placed),
        "ios": ios_spawned,
        "sdf_next": [
            "/Game/EnvSandbox/Materials/Instances/SDFArchitecture/MI_SDF_CrystallineSpire",
            "/Game/EnvSandbox/Materials/Instances/SDFArchitecture/MI_SDF_Musical",
            "/Game/EnvSandbox/Materials/Instances/SDFArchitecture/MI_SDF_Cathedral_Vault",
        ],
        "never_touched": ["Morning_SheepDell_Lake", "PCG", "HeroCorner cams", "PPV", "NS_Morning_*"],
        "level_saved": saved,
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "spire_grotto_greybox_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("GREY_SPIRE " + json.dumps({
        "placed": len(placed),
        "shaft": sum(1 for p in placed if p.get("role")=="shaft"),
        "chamber": sum(1 for p in placed if p.get("role")=="chamber"),
        "grotto": sum(1 for p in placed if str(p.get("role","")).startswith("grotto")),
        "approach": sum(1 for p in placed if p.get("role")=="approach"),
        "base_z": base_z,
        "top_z": top_z,
        "ios": ios_spawned,
        "saved": saved,
        "out": str(out),
    }, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
