import unreal, json
from unreal import EditorActorSubsystem
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
labels = [a.get_actor_label() for a in svc.get_all_level_actors()]
import collections
c = collections.Counter()
for l in labels:
    if "ArpeggioBridge Music Node" in l:
        c["arp"] += 1
    elif "BellTreeGarden Music Node" in l:
        c["bells"] += 1
    elif l == "Morning_SheepDell_Water":
        c["water"] += 1
    elif l in ("Morning_Dell_Banks", "Morning_Brook_Arpeggio"):
        c["vols"] += 1
open("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_reload_proof.json",
     "w").write(json.dumps(dict(c), indent=1))
print("RELOAD_WROTE")
