import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_house_dell.v2.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
pts = []
for a in svc.get_all_level_actors():
    try:
        lbl = a.get_actor_label()
    except Exception:
        continue
    if lbl.startswith("MH_"):
        l = a.get_actor_location()
        pts.append({"label": lbl,
                    "loc": [round(l.x, 1), round(l.y, 1), round(l.z, 1)]})
pts.sort(key=lambda p: p["label"])
open(OUT, "w").write(json.dumps(
    {"seed": 2026, "note": "live resnap: rim-walk ring +150, bowl floor -640, canopy excluded",
     "count": len(pts), "points": pts}, indent=1))
print("DELLV2_WROTE " + str(len(pts)))
