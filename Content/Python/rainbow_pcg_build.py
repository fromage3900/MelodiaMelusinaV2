import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/rainbow_pcg_build.json"
rep = {"templates": [], "branches": []}
random_seed_base = 1500
al = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ELL = unreal.EditorLevelLibrary

LAKE = unreal.Vector(-950.0, 2300.0, -500.0)
for a in svc.get_all_level_actors():
    try:
        lbl = a.get_actor_label()
        if "Lake" in lbl or ("Pond" in lbl and "bed" not in lbl.lower()):
            LAKE = a.get_actor_location()
            rep["lake"] = {"label": lbl, "pos": [round(LAKE.x, 1), round(LAKE.y, 1), round(LAKE.z, 1)]}
            break
    except Exception:
        pass

petal = al.load_asset("/Game/EnvSandbox/Meshes/SurrealFlora/M_GhostPetalMid")
NAMES = ["B0_Red", "B1_Orange", "B2_Gold", "B3_Green", "B4_Blue", "B5_Indigo", "B6_Violet"]
LETTERS = "ROYGBIV"
EXTENTS = [350.0, 600.0, 850.0, 1100.0, 1350.0, 1600.0, 1850.0]
CELLS = [110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0]

# 1. templates (backstage)
templates = []
for b in range(7):
    mi = al.load_asset("/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_" + NAMES[b])
    t = ELL.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(6000.0 + b * 120.0, 6500.0, 200.0), unreal.Rotator(0, 0, 0))
    t.set_actor_label("PetalTemplate_" + LETTERS[b])
    rec = {"band": LETTERS[b]}
    try:
        smc = t.get_component_by_class(unreal.StaticMeshComponent)
        smc.set_static_mesh(petal)
        smc.set_material(0, mi)
        rec["dressed"] = True
    except Exception as e:
        rec["dress_err"] = str(e)[:150]
    templates.append(t)
    rep["templates"].append(rec)

# 2. graph branches
g = al.load_asset("/Game/EnvSandbox/PCG/House/PCG_MelusinaHouse_MorningDell")
vol_node = None
for n in g.get_editor_property("nodes"):
    try:
        if str(n.get_path_name()).split(":")[-1] == "GetVolumeData_0":
            vol_node = n
            break
    except Exception:
        pass
for b in range(7):
    brec = {"band": LETTERS[b]}
    try:
        grid = g.add_node_of_type(unreal.PCGCreatePointsGridSettings)[0]
        gs = grid.get_settings()
        gs.set_editor_property("grid_extents", unreal.Vector(EXTENTS[b], EXTENTS[b], 200.0))
        gs.set_editor_property("cell_size", unreal.Vector(CELLS[b], CELLS[b], 100.0))
        gs.set_editor_property("cull_points_outside_volume", True)
        gs.set_editor_property("use_seed", True)
        gs.set_editor_property("seed", random_seed_base + b)
        ray = g.add_node_of_type(unreal.PCGWorldRaycastElementSettings)[0]
        rs = ray.get_settings()
        rs.set_editor_property("ray_direction", unreal.Vector(0.0, 0.0, -1.0))
        rs.set_editor_property("ray_length", 3000.0)
        try:
            rs.set_editor_property("keep_original_point_on_miss", True)
        except Exception:
            pass
        sp = g.add_node_of_type(unreal.PCGSpawnActorSettings)[0]
        ss = sp.get_settings()
        ss.set_editor_property("template_actor", templates[b])
        try:
            ss.set_editor_property("delete_actors_before_generation", True)
        except Exception:
            pass
        try:
            ss.set_editor_property("tags_to_add_on_actors", ["RainbowBloom"])
        except Exception:
            pass
        if vol_node is not None:
            g.add_edge(vol_node, "Out", grid, "In")
        g.add_edge(grid, "Out", ray, "In")
        g.add_edge(ray, "Out", sp, "In")
        brec["wired"] = True
    except Exception as e:
        brec["err"] = str(e)[:200]
    rep["branches"].append(brec)

# 3. field volume
fvol = ELL.spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(LAKE.x, LAKE.y, LAKE.z + 200.0), unreal.Rotator(0, 0, 0))
fvol.set_actor_label("RainbowBloom_Field")
fvol.set_actor_scale3d(unreal.Vector(40.0, 40.0, 12.0))
comp = fvol.get_component_by_class(unreal.PCGComponent)
comp.set_graph(g)
try:
    comp.generate(True)
    rep["generated"] = True
except Exception as e:
    rep["generate_err"] = str(e)[:200]
tagged = 0
try:
    for a in svc.get_all_level_actors():
        try:
            if "RainbowBloom" in ",".join([str(t) for t in list(a.tags)]):
                tagged += 1
        except Exception:
            pass
except Exception as e:
    rep["count_err"] = str(e)[:150]
rep["spawned_tagged"] = tagged
open(OUT, "w").write(json.dumps(rep, indent=1))
print("PCGBUILD_WROTE tagged=" + str(tagged))
