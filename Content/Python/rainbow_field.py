import unreal, json, math, random

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/rainbow_field.json"
rep = {"bands": []}
random.seed(20260915)
al = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ELL = unreal.EditorLevelLibrary

lake_pos, lake_lbl = None, None
for a in svc.get_all_level_actors():
    try:
        lbl = a.get_actor_label()
        if "Lake" in lbl or "Pond" in lbl or "Oceanology" in lbl:
            lake_pos, lake_lbl = a.get_actor_location(), lbl
            break
    except Exception:
        pass
if lake_pos is None:
    lake_pos = unreal.Vector(-950.0, 2300.0, -500.0)
rep["lake"] = {"label": lake_lbl, "pos": [round(lake_pos.x, 1), round(lake_pos.y, 1), round(lake_pos.z, 1)]}

petal = al.load_asset("/Game/EnvSandbox/Meshes/SurrealFlora/M_GhostPetalMid")
NAMES = ["B0_Red", "B1_Orange", "B2_Gold", "B3_Green", "B4_Blue", "B5_Indigo", "B6_Violet"]
GOLD = 2.399963
total = 0
for b in range(7):
    mi = al.load_asset("/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_" + NAMES[b])
    holder = ELL.spawn_actor_from_class(unreal.Actor, lake_pos, unreal.Rotator(0, 0, 0))
    holder.set_actor_label("RainbowBloom_" + "ROYGBIV"[b])
    comp = unreal.InstancedStaticMeshComponent()
    holder.add_instance_component(comp)
    comp.set_static_mesh(petal)
    comp.set_material(0, mi)
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    n = 0
    for i in range(120):
        idx = b * 120 + i
        r = 260.0 + b * 150.0 + (i % 30) * 4.0 + random.uniform(-18, 18)
        th = idx * GOLD
        x = lake_pos.x + r * math.cos(th)
        y = lake_pos.y + r * math.sin(th)
        z = lake_pos.z
        try:
            hit = unreal.SystemLibrary.line_trace_single_for_objects(
                None, unreal.Vector(x, y, lake_pos.z + 1500.0), unreal.Vector(x, y, lake_pos.z - 1500.0),
                [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1], False, [], unreal.DrawDebugTrace.NO_DEBUG, True)
            if hit is not None:
                try:
                    hz = hit.to_dict().get("location", {}).get("z", None)
                    if hz is not None:
                        z = hz
                except Exception:
                    pass
        except Exception:
            pass
        s = random.uniform(0.5, 1.1)
        comp.add_instance(unreal.Transform(unreal.Vector(x, y, z + 4.0),
                                           unreal.Rotator(0, random.uniform(0, 360), 0),
                                           unreal.Vector(s, s, s)))
        n += 1
    rep["bands"].append({"band": "ROYGBIV"[b], "count": comp.get_instance_count()})
    total += comp.get_instance_count()
rep["total"] = total
open(OUT, "w").write(json.dumps(rep, indent=1))
print("FIELD_WROTE total=" + str(total))
