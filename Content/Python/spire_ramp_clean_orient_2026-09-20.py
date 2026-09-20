"""Clean rebuild of SpireRamp transforms: level yaw, linear Z climb, radius hug, bottom edge XY if solid."""
import json, math
from pathlib import Path
import unreal

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

def good(L, C):
    if not L or L.startswith(("WC_", "Oceanology")): return False
    if L == "Morning_SheepDell_Lake": return False
    return (
        L.startswith(("BrushifyIsland_", "SM_classic_arch_", "WC_EscherWalk_"))
        or "melusina" in L.lower() or "house" in L.lower()
        or L.startswith("SM_wall")
        or "Landscape" in (C or "")
    )

def trace(world, x, y, zhint, ignore):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x,y,zhint+5000), unreal.Vector(x,y,zhint-15000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, True, ignore,
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]: return None
    actor = t[9]
    L = actor.get_actor_label() if actor else ""
    C = actor.get_class().get_name() if actor else ""
    if not good(L, C) or float(t[5].z) < 0.5: return None
    return t[4], L

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
shaft = next(a for a in svc.get_all_level_actors() if lab(a) == "WC_GreySpire_Shaft")
floor = next((a for a in svc.get_all_level_actors() if lab(a) == "WC_GreySpire_Chamber_Floor"), None)
so, se = shaft.get_actor_bounds(False, False)
cx, cy = float(so.x), float(so.y)

ignore = [a for a in svc.get_all_level_actors() if lab(a).startswith(("WC_SpireRamp", "WC_Grey", "WC_Walk", "WC_Phylo"))]
# base ground at shaft
bg = trace(world, cx, cy, 4000, ignore)
base_z = float(bg[0].z) + 15 if bg else 914.0
top_z = float(floor.get_actor_location().z) - 50 if floor else base_z + 2100

stairs = sorted([a for a in svc.get_all_level_actors() if lab(a).startswith("WC_SpireRamp_Stair_")], key=lab)
n = len(stairs)
turns = 1.25
radius = 300.0
out = []
before = []
for i, a in enumerate(stairs):
    rot = a.get_actor_rotation()
    before.append({"label": lab(a), "yaw": float(rot.yaw), "pitch": float(rot.pitch), "roll": float(rot.roll), "z": float(a.get_actor_location().z)})
    ang = (i / max(1, n - 1)) * turns * math.tau
    yaw = math.degrees(ang) + 90.0
    z = base_z + (top_z - base_z) * (i / max(1, n - 1))
    x = cx + radius * math.cos(ang)
    y = cy + radius * math.sin(ang)
    ground = None
    # bottom third: try pull XY onto solid within band, but Z stays climb (clamp to climb ±80)
    if i <= n // 3:
        for r in range(200, 481, 40):
            xx = cx + r * math.cos(ang)
            yy = cy + r * math.sin(ang)
            hit = trace(world, xx, yy, z + 200, ignore)
            if hit:
                loc, ground = hit
                # only accept if ground Z near climb Z
                if abs(float(loc.z) - z) <= 120:
                    x, y = float(loc.x), float(loc.y)
                    z = float(loc.z) + 12.0
                    radius_used = r
                    break
    a.set_actor_location(unreal.Vector(x, y, z), False, False)
    a.set_actor_rotation(unreal.Rotator(0.0, yaw, 0.0), False)
    out.append({"label": lab(a), "yaw": yaw, "pitch": 0.0, "roll": 0.0, "z": z, "ground": ground})

for a in svc.get_all_level_actors():
    L = lab(a)
    if not L.startswith("WC_SpireRamp_Rail_"): continue
    try: idx = int(L.rsplit("_", 1)[-1])
    except: continue
    ang = (idx / max(1, n - 1)) * turns * math.tau
    yaw = math.degrees(ang) + 90.0
    st = next((s for s in stairs if lab(s) == f"WC_SpireRamp_Stair_{idx:02d}"), None)
    if st:
        sl = st.get_actor_location()
        dx, dy = float(sl.x) - cx, float(sl.y) - cy
        d = math.hypot(dx, dy) or 1.0
        a.set_actor_location(unreal.Vector(sl.x + 70*dx/d, sl.y + 70*dy/d, sl.z + 40), False, False)
    a.set_actor_rotation(unreal.Rotator(0.0, yaw, 0.0), False)

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
rep = {
    "schema": "melodia.spire_ramp_clean_orient.v1",
    "base_z": base_z, "top_z": top_z, "radius": radius,
    "before_sample": before[:4],
    "after_sample": out[:4],
    "after_tail": out[-3:],
    "all_level": all(abs(o["pitch"]) < 0.01 and abs(o["roll"]) < 0.01 for o in out),
    "z_monotonic": all(out[i]["z"] <= out[i+1]["z"] + 1 for i in range(len(out)-1)),
    "grounds": list({o["ground"] for o in out if o.get("ground")}),
}
Path(unreal.Paths.project_dir()).joinpath("Saved/Audit/spire_ramp_clean_orient_2026-09-20.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
print("CLEAN", json.dumps({k: rep[k] for k in ("base_z","top_z","all_level","z_monotonic","grounds","before_sample","after_sample")}, default=str))
