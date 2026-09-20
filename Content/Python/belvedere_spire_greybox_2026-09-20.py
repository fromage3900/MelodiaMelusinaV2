"""Belvedere Spire greybox from morning_escher_spire_architect_2026-09-20.json
Destroy-only WC_GreyRoad_*/WC_GreySpire_*/WC_GreyGrotto_*/WC_GreySpline_*/WC_GreyApproach_*
Never touch lake/PCG/cams/PPV/NS_Morning_*
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
GREY = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m"
OWN = ("WC_GreyRoad_", "WC_GreySpire_", "WC_GreyGrotto_", "WC_GreySpline_", "WC_GreyApproach_")
PLAN = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "morning_escher_spire_architect_2026-09-20.json"

def _label(a):
    try: return a.get_actor_label() or ""
    except: return ""

def ground_at(world, x, y, zhint):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, zhint + 10000), unreal.Vector(x, y, zhint - 25000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, True, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    actor = t[9]
    lab = actor.get_actor_label() if actor else ""
    cls = actor.get_class().get_name() if actor else ""
    if lab.startswith(OWN) or lab.startswith(("WC_MA_Dress", "WC_HeroDress", "WC_Grey")):
        return None
    if lab == "Morning_SheepDell_Lake" or "Oceanology" in (cls or ""):
        return None
    # Accept Brushify / walks / landscape / environment static meshes (arches, islands).
    # Never lake / Oceanology / PCG volumes / cameras.
    if "PCG" in cls or "Camera" in cls or "Volume" in cls and "PCG" in lab:
        return None
    if lab.startswith(("WC_HeroCorner_", "WC_Lookdev_", "WC_morning_")):
        return None
    ok = (
        lab.startswith("Brushify") or lab.startswith("WC_EscherWalk_")
        or "Landscape" in (cls or "") or lab.startswith("Landscape")
        or cls == "StaticMeshActor" or lab.startswith("SM_")
    )
    if not ok:
        return None
    if float(t[5].z) < 0.4:
        return None
    return {"loc": t[4], "actor": lab, "nz": float(t[5].z)}

def clear_own(svc):
    rem = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if any(lab.startswith(p) for p in OWN):
            if svc.destroy_actor(a):
                rem.append(lab)
    return rem

def spawn_cube(mesh, loc, scale, yaw, label, folder):
    a = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, unreal.Rotator(0, yaw, 0))
    if not a:
        return None
    a.set_actor_label(label)
    a.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    try:
        a.set_folder_path(folder)
        a.tags = ["Portfolio", "Greybox", "Belvedere", "SpireDual"]
    except Exception:
        pass
    return a

def polyline_points(pts_xy, z_hints, spacing):
    """Sample along XY polyline; return list of (x,y,zhint)."""
    out = []
    for i in range(len(pts_xy) - 1):
        x0, y0 = pts_xy[i]
        x1, y1 = pts_xy[i + 1]
        z0 = z_hints[i] if i < len(z_hints) else 1000
        z1 = z_hints[i + 1] if (i + 1) < len(z_hints) else z0
        dx, dy = x1 - x0, y1 - y0
        seg = math.hypot(dx, dy)
        n = max(1, int(seg / spacing))
        for k in range(n):
            t = k / n
            out.append((x0 + dx * t, y0 + dy * t, z0 + (z1 - z0) * t))
    out.append((pts_xy[-1][0], pts_xy[-1][1], z_hints[-1] if z_hints else 1000))
    return out

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_name() != "L_MelusinaMorning":
        print("BELVEDERE " + json.dumps({"error": "need_L_MelusinaMorning", "world": world.get_name() if world else None}))
        return 1

    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    spire = plan["spire"]
    roads = plan["roads"]
    px, py, pz = spire["base_xyz_provisional"]

    if not EAL.does_asset_exist(GREY):
        print("BELVEDERE " + json.dumps({"error": "no_greybox_mesh"}))
        return 1
    mesh = EAL.load_asset(GREY)
    removed = clear_own(svc)
    placed = []

    # Snap base to live ground near provisional
    g = ground_at(world, px, py, pz)
    if not g:
        for r in (150, 300, 500, 800):
            for ang in range(0, 360, 45):
                g = ground_at(world, px + r * math.cos(math.radians(ang)), py + r * math.sin(math.radians(ang)), pz)
                if g:
                    break
            if g:
                break
    if not g:
        print("BELVEDERE " + json.dumps({"error": "no_ground_at_spire", "provisional": [px, py, pz], "removed": len(removed)}))
        return 1

    bx, by, bz = float(g["loc"].x), float(g["loc"].y), float(g["loc"].z)
    shaft_h = float(spire["shaft_height_cm"])  # 2200
    fp = spire["shaft_footprint_cm"]  # 400,400
    ch = spire["chamber_size_cm"]  # 500,500,400
    helix = spire["helix"]
    pool = spire["pool"]

    # --- Shaft as single tall mass (4x4x22 m) ---
    shaft_z = bz + shaft_h * 0.5
    lab = "WC_GreySpire_Shaft"
    if spawn_cube(mesh, unreal.Vector(bx, by, shaft_z), (fp[0] / 100.0, fp[1] / 100.0, shaft_h / 100.0), 0, lab, "Greybox/Belvedere/Spire"):
        placed.append({"label": lab, "role": "shaft", "loc": [bx, by, shaft_z], "scale_m": [fp[0]/100, fp[1]/100, shaft_h/100], "extent_cm_approx": [fp[0]/2, fp[1]/2, shaft_h/2]})

    # --- Chamber at top ---
    top_z = bz + shaft_h
    chamber_parts = [
        ("WC_GreySpire_Chamber_Floor", (bx, by, top_z + 20), (ch[0]/100, ch[1]/100, 0.35)),
        ("WC_GreySpire_Chamber_N", (bx, by + ch[1]/2 - 20, top_z + ch[2]/2), (ch[0]/100, 0.35, ch[2]/100)),
        ("WC_GreySpire_Chamber_S", (bx, by - ch[1]/2 + 20, top_z + ch[2]/2), (ch[0]/100, 0.35, ch[2]/100)),
        ("WC_GreySpire_Chamber_E", (bx + ch[0]/2 - 20, by, top_z + ch[2]/2), (0.35, ch[1]/100, ch[2]/100)),
        ("WC_GreySpire_Chamber_W", (bx - ch[0]/2 + 20, by, top_z + ch[2]/2), (0.35, ch[1]/100, ch[2]/100)),
        ("WC_GreySpire_Chamber_Crown", (bx, by, top_z + ch[2] + 80), (3.0, 3.0, 1.8)),
        ("WC_GreySpire_PortalCard", (bx, by - 80, top_z + ch[2]/2), (0.25, 3.8, 3.2)),
    ]
    for lab, (x, y, z), sc in chamber_parts:
        if spawn_cube(mesh, unreal.Vector(x, y, z), sc, 0 if "Crown" not in lab else 45, lab, "Greybox/Belvedere/Chamber"):
            placed.append({"label": lab, "role": "chamber", "loc": [x, y, z], "scale_m": list(sc)})

    # --- Helix stairs (88 steps) ---
    rad = float(helix["radius_cm"])
    rise = float(helix["rise_cm"])
    steps = int(helix["steps"])
    turns = float(helix.get("approx_turns") or helix.get("turns") or 1.25)
    for i in range(steps):
        ang = (i / steps) * turns * math.tau
        x = bx + rad * math.cos(ang)
        y = by + rad * math.sin(ang)
        z = bz + 40 + i * rise
        lab = f"WC_GreySpire_Helix_{i:02d}"
        yaw = math.degrees(ang) + 90
        if spawn_cube(mesh, unreal.Vector(x, y, z), (1.0, 0.45, 0.2), yaw, lab, "Greybox/Belvedere/Helix"):
            placed.append({"label": lab, "role": "helix", "i": i})

    # --- Grotto / crypt under base (pool) ---
    depth = float(pool["depth_cm"])
    pr = float(pool["radius_cm"])
    crypt_z = bz - depth * 0.5
    # sunken floor
    if spawn_cube(mesh, unreal.Vector(bx, by, crypt_z), (pr * 2 / 100.0, pr * 2 / 100.0, 0.4), 0, "WC_GreyGrotto_CryptFloor", "Greybox/Belvedere/Grotto"):
        placed.append({"label": "WC_GreyGrotto_CryptFloor", "role": "grotto", "loc": [bx, by, crypt_z]})
    # ring pillars
    for i in range(8):
        ang = i * (math.tau / 8)
        x = bx + (pr * 0.85) * math.cos(ang)
        y = by + (pr * 0.85) * math.sin(ang)
        lab = f"WC_GreyGrotto_Pillar_{i:02d}"
        if spawn_cube(mesh, unreal.Vector(x, y, bz - depth * 0.35), (0.6, 0.6, depth / 100.0 * 0.7), 0, lab, "Greybox/Belvedere/Grotto"):
            placed.append({"label": lab, "role": "grotto"})
    # portal twin card in crypt
    if spawn_cube(mesh, unreal.Vector(bx, by - 60, bz - depth * 0.55), (0.25, 3.2, 2.6), 0, "WC_GreyGrotto_PortalTwin", "Greybox/Belvedere/Grotto"):
        placed.append({"label": "WC_GreyGrotto_PortalTwin", "role": "grotto_portal", "loc": [bx, by - 60, bz - depth * 0.55]})

    # --- Roads ---
    road_counts = {}
    for road_id, rd in roads.items():
        pts = polyline_points(rd["pts_xy"], rd.get("z_hints") or [], float(rd.get("spacing_cm") or 200))
        # remap last approach points toward live base for ApproachNorth / SpireRing
        if road_id in ("ApproachNorth_to_Spire", "SpireRing_to_NorthDress"):
            # replace provisional spire xy with live base in samples near end
            pts2 = []
            for (x, y, zh) in pts:
                if abs(x - px) < 400 and abs(y - py) < 400:
                    pts2.append((bx, by, zh))
                else:
                    pts2.append((x, y, zh))
            pts = pts2
        n = 0
        w_m = float(rd.get("width_cm") or 200) / 100.0
        for i, (x, y, zh) in enumerate(pts):
            gg = ground_at(world, x, y, zh)
            if not gg:
                continue
            loc = gg["loc"]
            lab = f"WC_GreyRoad_{road_id}_{i:02d}"
            if spawn_cube(mesh, unreal.Vector(loc.x, loc.y, loc.z + 15), (w_m, 1.0, 0.2), 0, lab, f"Greybox/Belvedere/Roads/{road_id}"):
                placed.append({"label": lab, "role": "road", "road": road_id, "ground": gg["actor"]})
                n += 1
        road_counts[road_id] = n

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    # extents sample
    extents = {}
    for a in svc.get_all_level_actors():
        lab = _label(a)
        if lab in ("WC_GreySpire_Shaft", "WC_GreySpire_Chamber_Floor", "WC_GreyGrotto_CryptFloor", "WC_GreyGrotto_PortalTwin"):
            try:
                o, e = a.get_actor_bounds(False, False)
                extents[lab] = {"loc": [o.x, o.y, o.z], "half": [e.x, e.y, e.z]}
            except Exception:
                pass

    report = {
        "schema": "melodia.belvedere_spire_greybox.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "plan": str(PLAN),
        "world": "L_MelusinaMorning",
        "base_provisional": [px, py, pz],
        "base_live": [bx, by, bz],
        "base_ground_actor": g["actor"],
        "shaft_height_cm": shaft_h,
        "chamber_top_z": top_z,
        "helix_steps": steps,
        "removed_own": removed,
        "placed_count": len(placed),
        "road_counts": road_counts,
        "roles": {
            "shaft": sum(1 for p in placed if p.get("role") == "shaft"),
            "chamber": sum(1 for p in placed if p.get("role") == "chamber"),
            "helix": sum(1 for p in placed if p.get("role") == "helix"),
            "grotto": sum(1 for p in placed if str(p.get("role", "")).startswith("grotto")),
            "road": sum(1 for p in placed if p.get("role") == "road"),
        },
        "extents_sample": extents,
        "sdf_handoff": plan.get("materials") or {
            "shaft": "MI_SDF_CrystallineSpire",
            "chamber": "CosmicPortal+Musical",
            "grotto": "Caustics_Shallow+Anemone+Kelp",
        },
        "never_touched": ["Morning_SheepDell_Lake", "HeroCorner PCG/cams", "PPV", "NS_Morning_*"],
        "level_saved": saved,
        "placed": placed,
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "belvedere_spire_greybox_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("BELVEDERE " + json.dumps({
        "base_live": [bx, by, bz],
        "ground": g["actor"],
        "placed": len(placed),
        "roles": report["roles"],
        "roads": road_counts,
        "extents": extents,
        "saved": saved,
        "out": str(out),
    }, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
