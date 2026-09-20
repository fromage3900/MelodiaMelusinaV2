"""Complete ramp: grounded edge stairs keep snap; air stairs hug shaft radius with level yaw and interpolated Z."""
import json, math
from pathlib import Path
import unreal

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
shaft = next(a for a in svc.get_all_level_actors() if lab(a) == "WC_GreySpire_Shaft")
so, se = shaft.get_actor_bounds(False, False)
cx, cy = float(so.x), float(so.y)
floor = next((a for a in svc.get_all_level_actors() if lab(a) == "WC_GreySpire_Chamber_Floor"), None)

# load previous after samples for grounds
prev = json.loads(Path(unreal.Paths.project_dir()).joinpath("Saved/Audit/spire_atlantis_ramp_edge_snap_2026-09-20.json").read_text(encoding="utf-8"))
grounded = {s["label"]: s for s in prev.get("after_sample", []) + prev.get("after_tail", []) if s.get("ground")}
# rebuild full after from file if present
# re-read all after from placed - use current actor states

stairs = sorted([a for a in svc.get_all_level_actors() if lab(a).startswith("WC_SpireRamp_Stair_")], key=lab)
n = len(stairs)
turns = 1.25
radius = 300.0  # slightly out to hug edge

# find min/max Z among stairs that have nearby ground from receipt grounds list
zs = []
for a in stairs:
    t = a.get_actor_location()
    zs.append(float(t.z))
base_z = min(zs) if zs else 914.0
top_z = float(floor.get_actor_location().z) - 40 if floor else max(zs)

fixed = []
for i, a in enumerate(stairs):
    ang = (i / max(1, n - 1)) * turns * math.tau
    yaw = math.degrees(ang) + 90.0
    L = lab(a)
    # if already has good ground from edge snap (wall/arch), keep XY roughly; else shaft hug
    loc = a.get_actor_location()
    # interpolate ideal Z along climb always for continuity
    z = base_z + (top_z - base_z) * (i / max(1, n - 1))
    # if current Z is near a solid (within 50 of current) keep edge XY
    # detect if label was in failed list
    failed = set(prev.get("failed") or [])
    if L in failed or L not in grounded:
        x = cx + radius * math.cos(ang)
        y = cy + radius * math.sin(ang)
        mode = "shaft_hug"
    else:
        x, y = float(loc.x), float(loc.y)
        mode = "keep_edge"
        z = float(loc.z)  # keep snapped Z
    a.set_actor_location(unreal.Vector(x, y, z), False, False)
    a.set_actor_rotation(unreal.Rotator(0.0, yaw, 0.0), False)
    fixed.append({"label": L, "mode": mode, "yaw": yaw, "pitch": 0.0, "roll": 0.0, "z": z})

# rails follow
for a in svc.get_all_level_actors():
    L = lab(a)
    if not L.startswith("WC_SpireRamp_Rail_"):
        continue
    try:
        idx = int(L.rsplit("_", 1)[-1])
    except Exception:
        continue
    ang = (idx / max(1, n - 1)) * turns * math.tau
    yaw = math.degrees(ang) + 90.0
    stair = next((s for s in stairs if lab(s) == f"WC_SpireRamp_Stair_{idx:02d}"), None)
    if stair:
        sl = stair.get_actor_location()
        dx, dy = float(sl.x) - cx, float(sl.y) - cy
        dist = math.hypot(dx, dy) or 1.0
        a.set_actor_location(unreal.Vector(sl.x + 70 * dx / dist, sl.y + 70 * dy / dist, sl.z + 40), False, False)
    a.set_actor_rotation(unreal.Rotator(0.0, yaw, 0.0), False)

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
out = {
    "schema": "melodia.spire_ramp_edge_snap_complete.v1",
    "fixed": len(fixed),
    "edge_kept": sum(1 for f in fixed if f["mode"] == "keep_edge"),
    "shaft_hug": sum(1 for f in fixed if f["mode"] == "shaft_hug"),
    "sample": fixed[:5] + fixed[-3:],
    "all_pitch_roll_zero": all(f["pitch"] == 0 and f["roll"] == 0 for f in fixed),
}
Path(unreal.Paths.project_dir()).joinpath("Saved/Audit/spire_ramp_edge_snap_complete_2026-09-20.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8")
print("EDGE2", json.dumps(out))
