# _sheep_look2.py — read-only: deeper traces + camera fly (corrected). Prints only.
import unreal

eas = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = eas.get_editor_world()


def trace(x, y, z0, z1):
    start = unreal.Vector(x, y, z0)
    end = unreal.Vector(x, y, z1)
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            ew, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
            unreal.DrawDebugTrace.NONE, True,
            unreal.LinearColor(0, 0, 0, 1), unreal.LinearColor(0, 0, 0, 1), 0.0)
    except Exception as e:
        print('LK trace err', e)
        return None
    if hit is None:
        return None
    d = hit.to_dict()
    loc = d.get('location')
    act = d.get('hit_actor')
    return (round(loc.x, 1), round(loc.y, 1), round(loc.z, 2), act.get_actor_label() if act else None)


def multi(x, y, z0, z1, max_hits):
    hits = []
    zc = z0
    for _ in range(max_hits):
        h = trace(x, y, zc, z1)
        if h is None:
            break
        hits.append(h)
        zc = h[2] - 1.0
    return hits


print('LK sheep deep:', multi(-1567.778313, 1004.910798, -140.0, -6000.0, 6))
print('LK trig full:', multi(-1489.472783, 2019.464320, 3000.0, -6000.0, 22))
print('LK trig deep:', multi(-1489.472783, 2019.464320, 260.0, -6000.0, 6))

lsub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
target = unreal.Vector(-1567.778313, 1004.910798, 560.629455)
pos = unreal.Vector(target.x - 1200.0, target.y - 1200.0, target.z + 300.0)
rot = unreal.MathLibrary.find_look_at_rotation(pos, target)
ok = False
try:
    lsub.set_level_viewport_camera_info(pos, rot, 'LevelEditorViewport')
    ok = True
except Exception as e:
    print('LK cam key1 err:', e)
if not ok:
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(pos, rot)
        ok = True
    except Exception as e:
        print('LK cam legacy err:', e)
print('LK camera ok:', ok)
print('LK done')