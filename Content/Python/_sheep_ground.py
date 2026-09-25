# Read-only: ground traces near the Choral Sheep + local actors. Prints only.
import math
import unreal

eas = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = eas.get_editor_world()


def ground_at(x, y):
    start = unreal.Vector(x, y, 3000.0)
    end = unreal.Vector(x, y, -5000.0)
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            ew, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
            unreal.DrawDebugTrace.NONE, True,
            unreal.LinearColor(0, 0, 0, 1), unreal.LinearColor(0, 0, 0, 1), 0.0)
    except Exception as e:
        return 'TRACE ERR ' + str(e)
    if hit is None:
        return 'NO HIT'
    d = hit.to_dict()
    loc = d.get('location')
    act = d.get('hit_actor')
    return 'z=%s hit=%s actor=%s' % (
        round(loc.z, 2) if loc else None, d.get('blocking_hit'),
        act.get_actor_label() if act else None)


spots = [
    ('sheep', (-1567.778313, 1004.910798)),
    ('sheep_trigger', (-1489.472783, 2019.464320)),
    ('pondbed', (-950.0, 2300.0)),
    ('wool_motes', (-1059.713276, 2502.498964)),
    ('beatburst', (86.486256, 2430.076530)),
    ('melusina_spawn', (1320.0, 1858.0)),
]
for name, (x, y) in spots:
    print('SG', name, '->', ground_at(x, y))

sx, sy = -1567.778313, 1004.910798
near = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    try:
        l = a.get_actor_location()
        d = math.hypot(l.x - sx, l.y - sy)
        if d < 1500:
            near.append((round(d, 1), a.get_actor_label(), a.get_class().get_name(), round(l.z, 1)))
    except Exception:
        pass
near.sort()
print('SG near count:', len(near))
for n in near[:45]:
    print('SG near', n)
print('SG done')