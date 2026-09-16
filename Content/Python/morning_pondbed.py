import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_pondbed.json"
rep = {}
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
al = unreal.EditorAssetLibrary
for a in list(svc.get_all_level_actors()):
    try:
        if a.get_actor_label() == "Morning_SheepDell_Water":
            a.set_actor_label("Morning_SheepDell_PondBed")
            a.set_actor_location(unreal.Vector(-950.0, 2300.0, -660.0), False, True)
            mi = al.load_asset("/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_ChoirStone")
            if mi is not None:
                comp = a.get_component_by_class(unreal.StaticMeshComponent)
                if comp is not None:
                    comp.set_editor_property("override_materials", [mi])
                    rep["mi"] = True
            rep["ok"] = True
    except Exception as e:
        rep["err"] = str(e)[:200]
open(OUT, "w").write(json.dumps(rep, indent=1))
print("PONDBED_WROTE " + json.dumps(rep))
