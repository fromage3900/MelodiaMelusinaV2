import unreal, json
from unreal import EditorActorSubsystem
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
import collections
c = collections.Counter()
lake_loc = None
for a in svc.get_all_level_actors():
    try:
        lbl = a.get_actor_label()
    except Exception:
        continue
    if "ArpeggioBridge Music Node" in lbl:
        c["arp"] += 1
    elif "BellTreeGarden Music Node" in lbl:
        c["bells"] += 1
    elif lbl == "Morning_SheepDell_Lake":
        c["lake"] += 1
        l = a.get_actor_location()
        lake_loc = [round(l.x, 1), round(l.y, 1), round(l.z, 1)]
    elif lbl == "Morning_SheepDell_Water":
        c["plane"] += 1
    elif lbl in ("Morning_Dell_Banks", "Morning_Brook_Arpeggio"):
        c["vols"] += 1
out = dict(c)
out["lake_loc"] = lake_loc
open("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_final_proof.json",
     "w").write(json.dumps(out, indent=1))
print("FINALPROOF_WROTE " + json.dumps(out))
