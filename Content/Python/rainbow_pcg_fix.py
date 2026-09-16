import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/rainbow_pcg_fix.json"
rep = {"cleanup": [], "templates": [], "branches": []}
al = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# verify the true petal mesh
petal = al.load_asset("/Game/EnvSandbox/Meshes/SurrealFlora/Petal_petal_mid_2")
rep["petal_class"] = petal.get_class().get_name() if petal else "MISSING"

g = al.load_asset("/Game/EnvSandbox/PCG/House/PCG_MelusinaHouse_MorningDell")
# remove stray grid nodes (graph had none before today)
n = 0
for x in list(g.get_editor_property("nodes")):
    try:
        if "CreatePointsGrid" in str(x.get_path_name()):
            g.remove_node(x)
            n += 1
    except Exception as e:
        rep["cleanup"].append(str(e)[:120])
        break
rep["cleanup"].append("removed_grids=%d" % n)

NAMES = ["B0_Red", "B1_Orange", "B2_Gold", "B3_Green", "B4_Blue", "B5_Indigo", "B6_Violet"]
LETTERS = "ROYGBIV"
EXTENTS = [350.0, 600.0, 850.0, 1100.0, 1350.0, 1600.0, 1850.0]
CELLS = [110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0]
by_label = {}
for a in svc.get_all_level_actors():
    try:
        by_label[a.get_actor_label()] = a
    except Exception:
        pass
vol_node = None
for x in g.get_editor_property("nodes"):
    try:
        if str(x.get_path_name()).split(":")[-1] == "GetVolumeData_0":
            vol_node = x
            break
    except Exception:
        pass
for b in range(7):
    brec = {"band": LETTERS[b]}
    try:
        t = by_label.get("PetalTemplate_" + LETTERS[b])
        mi = al.load_asset("/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_" + NAMES[b])
        smc = t.get_component_by_class(unreal.StaticMeshComponent)
        smc.set_static_mesh(petal)
        smc.set_material(0, mi)
        brec["template"] = "dressed"
    except Exception as e:
        brec["template_err"] = str(e)[:180]
        rep["branches"].append(brec)
        continue
    try:
        grid = g.add_node_of_type(unreal.PCGCreatePointsGridSettings)[0]
        gs = grid.get_settings()
        gs.set_editor_property("grid_extents", unreal.Vector(EXTENTS[b], EXTENTS[b], 200.0))
        gs.set_editor_property("cell_size", unreal.Vector(CELLS[b], CELLS[b], 100.0))
        gs.set_editor_property("cull_points_outside_volume", True)
        ray = g.add_node_of_type(unreal.PCGWorldRaycastElementSettings)[0]
        rs = ray.get_settings()
        rs.set_editor_property("ray_direction", unreal.Vector(0.0, 0.0, -1.0))
        rs.set_editor_property("ray_length", 3000.0)
        sp = g.add_node_of_type(unreal.PCGSpawnActorSettings)[0]
        ss = sp.get_settings()
        ss.set_editor_property("template_actor", t)
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

fvol = by_label.get("RainbowBloom_Field")
try:
    comp = fvol.get_component_by_class(unreal.PCGComponent)
    comp.generate(True)
    rep["generated"] = True
except Exception as e:
    rep["generate_err"] = str(e)[:200]
tagged = 0
for a in svc.get_all_level_actors():
    try:
        if "RainbowBloom" in ",".join([str(t) for t in list(a.tags)]):
            tagged += 1
    except Exception:
        pass
rep["spawned_tagged"] = tagged
open(OUT, "w").write(json.dumps(rep, indent=1))
print("FIX_WROTE tagged=" + str(tagged))
