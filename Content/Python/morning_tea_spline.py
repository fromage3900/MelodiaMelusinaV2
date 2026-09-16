import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_tea_spline.json"
rep = {"splines": []}
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
al = unreal.EditorAssetLibrary

before = set()
for a in svc.get_all_level_actors():
    try:
        before.add(a.get_actor_label())
    except Exception:
        pass

try:
    vol = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PCGVolume, unreal.Vector(-1400.0, 2600.0, -450.0),
        unreal.Rotator(0, 0, 0))
    vol.set_actor_label("Morning_TeaGarden_Test")
    vol.set_actor_scale3d(unreal.Vector(4.0, 4.0, 2.0))
    comp = vol.get_component_by_class(unreal.PCGComponent)
    g = al.load_asset("/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Hero_TeaGarden")
    comp.set_graph(g)
    comp.generate(True)
    rep["tea_generate_ok"] = True
except Exception as e:
    rep["tea_generate_ok"] = False
    rep["tea_err"] = str(e)[:200]

after = {}
for a in svc.get_all_level_actors():
    try:
        after[a.get_actor_label()] = a
    except Exception:
        pass
new_labels = sorted(set(after) - set(before))
rep["new_count"] = len(new_labels)
rep["new_labels"] = new_labels[:30]

for a in svc.get_all_level_actors():
    try:
        for comp in a.get_components_by_class(unreal.SplineComponent):
            n = comp.get_number_of_spline_points()
            p0 = comp.get_location_at_spline_point(0, unreal.SplineCoordinateSpace.WORLD)
            rep["splines"].append({
                "actor": a.get_actor_label(),
                "points": n,
                "p0": [round(p0.x, 1), round(p0.y, 1), round(p0.z, 1)],
            })
            break
    except Exception:
        continue

open(OUT, "w").write(json.dumps(rep, indent=1))
print("TEA_SPLINE_WROTE")
