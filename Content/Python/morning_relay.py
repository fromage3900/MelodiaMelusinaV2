import unreal, json, math
from unreal import EditorActorSubsystem

MANIFEST = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_house_dell.v2.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
want = json.load(open(MANIFEST))["points"]
pool = {}
for a in list(svc.get_all_level_actors()):
    try:
        pool.setdefault(a.get_actor_label(), []).append(a)
    except Exception:
        pass
moved, missing = 0, []


def dist(a, loc):
    l = a.get_actor_location()
    return math.dist((l.x, l.y, l.z), tuple(loc))


for p in want:
    cands = pool.get(p["label"], [])
    if not cands:
        missing.append(p["label"])
        continue
    cands.sort(key=lambda a: dist(a, p["loc"]))
    a = cands.pop(0)
    a.set_actor_location(unreal.Vector(*p["loc"]), False, True)
    moved += 1
print("RELAY_WROTE moved=%d missing=%d" % (moved, len(missing)))
