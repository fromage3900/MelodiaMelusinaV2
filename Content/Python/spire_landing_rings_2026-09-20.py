"""Belvedere climb rebuild: quarter-turn landing rings + short stair connectors + walk hook.
Labels: WC_SpireRamp_Landing_*, WC_SpireRamp_Conn_*, WC_SpireRamp_Rail_*
Destroys prior WC_SpireRamp_* only. Keeps shaft/chamber/portal. Hooks WC_WalkPath into landing 0.
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
FLOOR = [
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorC",
]
STAIR = "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StairsA"
RAIL = "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailA"
PREFIX = "WC_SpireRamp_"

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

def load(p):
    return EAL.load_asset(p) if EAL.does_asset_exist(p) else None

def autofit(mesh, desired, cap=280.0):
    try:
        box = mesh.get_bounding_box()
        half = max(abs(box.max.x - box.min.x), abs(box.max.y - box.min.y), abs(box.max.z - box.min.z)) * 0.5
        if half < 1e-3:
            return desired
        return min(desired, cap / half)
    except Exception:
        return desired

def spawn(mesh, loc, scale, yaw, label, folder):
    if isinstance(scale, (int, float)):
        sc = unreal.Vector(scale, scale, scale)
    else:
        sc = unreal.Vector(scale[0], scale[1], scale[2])
    a = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, unreal.Rotator(0.0, yaw, 0.0))
    if not a:
        return None
    a.set_actor_label(label)
    a.set_actor_scale3d(sc)
    try:
        a.set_folder_path(folder)
        a.tags = ["Portfolio", "SpireRamp", "LandingRing", "Belvedere"]
    except Exception:
        pass
    return a

def ground_at(world, x, y, zhint, ignore):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, zhint + 8000), unreal.Vector(x, y, zhint - 20000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, True, ignore,
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    actor = t[9]
    L = actor.get_actor_label() if actor else ""
    C = actor.get_class().get_name() if actor else ""
    if L.startswith(("WC_SpireRamp", "WC_Grey", "WC_Walk", "WC_Phylo")):
        return None
    if L == "Morning_SheepDell_Lake" or "Oceanology" in C:
        return None
    ok = (
        L.startswith(("BrushifyIsland_", "SM_classic_arch_", "WC_EscherWalk_", "SM_wall"))
        or "Landscape" in C
        or "house" in L.lower()
        or "melusina" in L.lower()
    )
    if not ok or float(t[5].z) < 0.5:
        return None
    return t[4], L

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_name() != "L_MelusinaMorning":
        print("LANDINGS " + json.dumps({"error": "need_morning", "world": world.get_name() if world else None}))
        return 1

    # clear old ramp pieces
    destroyed = []
    for a in list(svc.get_all_level_actors()):
        L = lab(a)
        if L.startswith(PREFIX):
            if svc.destroy_actor(a):
                destroyed.append(L)

    shaft = next((a for a in svc.get_all_level_actors() if lab(a) == "WC_GreySpire_Shaft"), None)
    floor_c = next((a for a in svc.get_all_level_actors() if lab(a) == "WC_GreySpire_Chamber_Floor"), None)
    if not shaft:
        print("LANDINGS " + json.dumps({"error": "no_shaft"}))
        return 1

    so, se = shaft.get_actor_bounds(False, False)
    cx, cy = float(so.x), float(so.y)
    ignore = [a for a in svc.get_all_level_actors() if lab(a).startswith(("WC_Grey", "WC_Walk", "WC_Phylo", "WC_SpireRamp"))]

    g0 = ground_at(world, cx, cy, 4000, ignore)
    base_z = float(g0[0].z) + 20 if g0 else 920.0
    top_z = float(floor_c.get_actor_location().z) - 60 if floor_c else base_z + 2000

    floors = [load(p) for p in FLOOR]
    floors = [m for m in floors if m]
    stair_m = load(STAIR)
    rail_m = load(RAIL)
    if not floors or not stair_m:
        print("LANDINGS " + json.dumps({"error": "missing_meshes"}))
        return 1

    # Landing every 90° / quarter turn, rising to chamber
    # ~8 landings over 2 full turns for readable stack
    n_land = 8
    turns = 2.0
    radius = 380.0  # wider for walkable deck
    floor_sc = autofit(floors[0], 0.85, cap=320)
    stair_sc = autofit(stair_m, 0.55, cap=260)
    rail_sc = autofit(rail_m, 0.4, cap=220) if rail_m else 0.3

    placed = []
    landing_pts = []  # (x,y,z,yaw,ang)

    for i in range(n_land):
        t = i / max(1, n_land - 1)
        ang = t * turns * math.tau
        yaw = math.degrees(ang)  # face outward for deck read
        z = base_z + (top_z - base_z) * t
        x = cx + radius * math.cos(ang)
        y = cy + radius * math.sin(ang)
        # snap first landing to ground if possible
        if i == 0:
            hit = ground_at(world, x, y, z + 500, ignore)
            if hit:
                x, y = float(hit[0].x), float(hit[0].y)
                z = float(hit[0].z) + 15
                ground = hit[1]
            else:
                # try around shaft foot
                for r in (300, 400, 500):
                    for k in range(8):
                        a2 = k * (math.tau / 8)
                        hit = ground_at(world, cx + r * math.cos(a2), cy + r * math.sin(a2), 4000, ignore)
                        if hit:
                            x, y = float(hit[0].x), float(hit[0].y)
                            z = float(hit[0].z) + 15
                            ang = a2
                            yaw = math.degrees(ang)
                            ground = hit[1]
                            break
                    else:
                        continue
                    break
                else:
                    ground = None
        else:
            ground = None

        mesh = floors[i % len(floors)]
        # landing as slightly elongated pad toward tangent
        label = f"{PREFIX}Landing_{i:02d}"
        a = spawn(mesh, unreal.Vector(x, y, z), (floor_sc * 1.2, floor_sc * 1.2, floor_sc * 0.35), yaw, label, "Greybox/Belvedere/SpireRamp/Landings")
        if a:
            placed.append({"label": label, "role": "landing", "loc": [x, y, z], "yaw": yaw, "ground": ground if i == 0 else None})
            landing_pts.append((x, y, z, yaw, ang))
            ignore.append(a)

        # outer rail on landing
        if rail_m:
            rx = cx + (radius + 90) * math.cos(ang)
            ry = cy + (radius + 90) * math.sin(ang)
            rl = f"{PREFIX}Rail_{i:02d}"
            ra = spawn(rail_m, unreal.Vector(rx, ry, z + 40), rail_sc, yaw + 90, rl, "Greybox/Belvedere/SpireRamp/Landings")
            if ra:
                placed.append({"label": rl, "role": "rail"})
                ignore.append(ra)

    # Short stair connectors between consecutive landings (3 stairs each)
    for i in range(len(landing_pts) - 1):
        x0, y0, z0, yaw0, ang0 = landing_pts[i]
        x1, y1, z1, yaw1, ang1 = landing_pts[i + 1]
        for k in range(1, 4):
            u = k / 4.0
            x = x0 + (x1 - x0) * u
            y = y0 + (y1 - y0) * u
            z = z0 + (z1 - z0) * u
            # yaw along connector direction
            yaw = math.degrees(math.atan2(y1 - y0, x1 - x0))
            label = f"{PREFIX}Conn_{i:02d}_{k}"
            a = spawn(stair_m, unreal.Vector(x, y, z), stair_sc, yaw, label, "Greybox/Belvedere/SpireRamp/Connectors")
            if a:
                placed.append({"label": label, "role": "connector", "loc": [x, y, z], "yaw": yaw})
                ignore.append(a)

    # Hook ground walk into first landing
    walk_hook = []
    if landing_pts:
        lx, ly, lz, _, _ = landing_pts[0]
        # find nearest walk path pad
        walks = [a for a in svc.get_all_level_actors() if lab(a).startswith("WC_WalkPath_Belvedere_")]
        start = None
        if walks:
            # use last walk pad as approach end, or closest to landing
            best = None
            best_d = 1e18
            for a in walks:
                p = a.get_actor_location()
                d = (float(p.x) - lx) ** 2 + (float(p.y) - ly) ** 2
                if d < best_d:
                    best_d = d
                    best = a
            start = best
        if start:
            s = start.get_actor_location()
            sx, sy, sz = float(s.x), float(s.y), float(s.z)
        else:
            # EastBank-ish fallback
            hit = ground_at(world, -1450, 1520, 2000, ignore)
            if hit:
                sx, sy, sz = float(hit[0].x), float(hit[0].y), float(hit[0].z) + 12
            else:
                sx, sy, sz = lx - 400, ly, lz

        # destroy old hook pads only
        for a in list(svc.get_all_level_actors()):
            if lab(a).startswith("WC_WalkPath_Belvedere_Hook_"):
                svc.destroy_actor(a)

        segs = 8
        for i in range(segs + 1):
            u = i / segs
            x = sx + (lx - sx) * u
            y = sy + (ly - sy) * u
            hit = ground_at(world, x, y, 3000, ignore)
            if hit:
                x, y = float(hit[0].x), float(hit[0].y)
                z = float(hit[0].z) + 12
                g = hit[1]
            else:
                # intentional bridge pad at blend height
                z = sz + (lz - sz) * u
                g = "bridge"
            yaw = math.degrees(math.atan2(ly - sy, lx - sx))
            label = f"WC_WalkPath_Belvedere_Hook_{i:02d}"
            mesh = floors[i % len(floors)]
            sc = autofit(mesh, 0.7, cap=300)
            a = spawn(mesh, unreal.Vector(x, y, z), (sc, sc, sc * 0.3), yaw, label, "Greybox/Belvedere/WalkPath")
            if a:
                walk_hook.append({"label": label, "ground": g, "loc": [x, y, z]})
                ignore.append(a)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    report = {
        "schema": "melodia.spire_landing_rings.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "destroyed_prior_ramp": len(destroyed),
        "center": [cx, cy],
        "base_z": base_z,
        "top_z": top_z,
        "n_landings": n_land,
        "turns": turns,
        "radius_cm": radius,
        "floor_scale": floor_sc,
        "stair_scale": stair_sc,
        "placed": placed,
        "placed_count": len(placed),
        "walk_hook": walk_hook,
        "walk_hook_count": len(walk_hook),
        "level_saved": saved,
        "roles": {
            "landing": sum(1 for p in placed if p.get("role") == "landing"),
            "connector": sum(1 for p in placed if p.get("role") == "connector"),
            "rail": sum(1 for p in placed if p.get("role") == "rail"),
        },
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "spire_landing_rings_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("LANDINGS " + json.dumps({
        "destroyed": len(destroyed),
        "landings": report["roles"]["landing"],
        "connectors": report["roles"]["connector"],
        "rails": report["roles"]["rail"],
        "hook": len(walk_hook),
        "base_z": base_z,
        "top_z": top_z,
        "radius": radius,
        "saved": saved,
        "out": str(out),
    }, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
