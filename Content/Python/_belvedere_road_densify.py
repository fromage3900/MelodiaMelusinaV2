"""Densify SpireRing + ApproachNorth grey roads only."""
import json, math
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
GREY = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m"
OWN = ("WC_GreyRoad_SpireRing_to_NorthDress_", "WC_GreyRoad_ApproachNorth_to_Spire_")

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

def ground_at(world, x, y, zhint):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, zhint + 12000), unreal.Vector(x, y, zhint - 30000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, True, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    actor = t[9]
    L = actor.get_actor_label() if actor else ""
    C = actor.get_class().get_name() if actor else ""
    if L.startswith(("WC_Grey", "WC_MA_Dress", "WC_HeroDress")):
        return None
    if L == "Morning_SheepDell_Lake" or "Oceanology" in C:
        return None
    if "Camera" in C or "PCGVolume" in C:
        return None
    if float(t[5].z) < 0.35:
        return None
    # accept almost any solid mesh
    return {"loc": t[4], "actor": L}

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
# find live spire base from shaft
base = None
for a in svc.get_all_level_actors():
    if lab(a) == "WC_GreySpire_Shaft":
        t = a.get_actor_transform()
        # shaft center; base approx center.z - half height
        try:
            o, e = a.get_actor_bounds(False, False)
            base = (o.x, o.y, o.z - e.z)
        except Exception:
            base = (t.translation.x, t.translation.y, t.translation.z - 1100)
        break
if not base:
    base = (160.0, 1600.0, 914.0)

# clear only these two road prefixes
rem = []
for a in list(svc.get_all_level_actors()):
    L = lab(a)
    if L.startswith(OWN):
        if svc.destroy_actor(a):
            rem.append(L)

mesh = EAL.load_asset(GREY)
north = (900.0, 2300.0, 960.0)
east = (-1450.0, 1520.0, 1500.0)
placed = []

def place_road(prefix, pts, spacing, width_m):
    n = 0
    for i in range(len(pts) - 1):
        x0, y0, z0 = pts[i]
        x1, y1, z1 = pts[i + 1]
        seg = math.hypot(x1 - x0, y1 - y0)
        steps = max(2, int(seg / spacing))
        for k in range(steps + 1):
            t = k / steps
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            zh = z0 + (z1 - z0) * t
            g = ground_at(world, x, y, zh)
            if not g:
                # try slight offsets
                for dx, dy in ((80,0),(-80,0),(0,80),(0,-80),(120,120)):
                    g = ground_at(world, x+dx, y+dy, zh)
                    if g: break
            if not g:
                continue
            loc = g["loc"]
            label = f"{prefix}{n:02d}"
            a = unreal.EditorLevelLibrary.spawn_actor_from_object(
                mesh, unreal.Vector(loc.x, loc.y, loc.z + 15), unreal.Rotator(0, 0, 0))
            if a:
                a.set_actor_label(label)
                a.set_actor_scale3d(unreal.Vector(width_m, 1.0, 0.2))
                try: a.set_folder_path("Greybox/Belvedere/Roads")
                except: pass
                placed.append(label)
                n += 1
    return n

# Approach: EastBank -> spire
c1 = place_road("WC_GreyRoad_ApproachNorth_to_Spire_", [(*east,), ( -600.0, 1750.0, 1200.0), (*base,)], 160, 2.2)
# Ring: spire -> NorthDress
c2 = place_road("WC_GreyRoad_SpireRing_to_NorthDress_", [(*base,), (500.0, 1900.0, base[2]), (*north,)], 150, 2.0)

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("ROAD_DENSE", json.dumps({"removed": len(rem), "approach": c1, "ring": c2, "base": base, "labels": placed[:20]}))
