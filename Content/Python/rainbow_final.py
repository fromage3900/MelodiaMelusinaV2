import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/rainbow_final.json"
rep = {"templates": [], "grids": [], "spawners": []}
al = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ELL = unreal.EditorLevelLibrary

LAKE = unreal.Vector(-950.0, 2300.0, -615.4)
NAMES = ["B0_Red", "B1_Orange", "B2_Gold", "B3_Green", "B4_Blue", "B5_Indigo", "B6_Violet"]
LETTERS = "ROYGBIV"
petal = al.load_asset("/Game/EnvSandbox/Meshes/SurrealFlora/Petal_petal_mid_2")

# destroy strays (origin floater + test volume)
for a in list(svc.get_all_level_actors()):
    try:
        if a.get_actor_label() in ("RainbowBloom_R", "RainbowBloom_TestVol"):
            svc.destroy_actor(a)
            rep.setdefault("destroyed", []).append(a.get_actor_label())
    except Exception:
        pass

# recreate templates
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
        rb_m = smc.get_static_mesh()
        rb_t = smc.get_material(0)
        rec["mesh_rb"] = str(rb_m.get_path_name()).split(".")[-1][:30] if rb_m else "NONE"
        rec["mat_rb"] = str(rb_t.get_path_name()).split(".")[-1][:30] if rb_t else "NONE"
    except Exception as e:
        rec["dress_err"] = str(e)[:180]
    templates.append(t)
    rep["templates"].append(rec)

g = al.load_asset("/Game/EnvSandbox/PCG/House/PCG_MelusinaHouse_MorningDell")
grids = sorted([n for n in g.get_editor_property("nodes") if str(n.get_path_name()).split(":")[-1].startswith("CreatePointsGrid_")],
               key=lambda n: str(n.get_path_name()))
rays = sorted([n for n in g.get_editor_property("nodes") if str(n.get_path_name()).split(":")[-1].startswith("WorldRaycast_")],
              key=lambda n: str(n.get_path_name()))
spawners = sorted([n for n in g.get_editor_property("nodes") if str(n.get_path_name()).split(":")[-1].startswith("SpawnActor_")],
                  key=lambda n: str(n.get_path_name()))
for b, gr in enumerate(grids):
    EXT = [350.0, 600.0, 850.0, 1100.0, 1350.0, 1600.0, 1850.0][b]
    CELL = [110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0][b]
    rec = {"band": LETTERS[b]}
    try:
        gs = gr.get_settings()
        errs = []
        for prop, val in (("grid_extents", unreal.Vector(EXT, EXT, 200.0)),
                          ("cell_size", unreal.Vector(CELL, CELL, 100.0)),
                          ("cull_points_outside_volume", True)):
            try:
                gs.set_editor_property(prop, val)
            except Exception as e:
                errs.append(prop + ":" + str(e)[:100])
        try:
            gs.set_editor_property("point_position", unreal.Vector(LAKE.x, LAKE.y, LAKE.z + 300.0))
        except Exception as e:
            errs.append("point_position:" + str(e)[:100])
        rec["set_errs"] = errs
        rec["pos_rb"] = str(gs.get_editor_property("point_position"))[:80]
    except Exception as e:
        rec["err"] = str(e)[:200]
    rep["grids"].append(rec)
for b, sp in enumerate(spawners):
    rec = {"band": LETTERS[b]}
    try:
        ss = sp.get_settings()
        errs = []
        for prop, val in (("template_actor", templates[b]),
                          ("template_actor_class", unreal.StaticMeshActor),
                          ("delete_actors_before_generation", False)):
            try:
                ss.set_editor_property(prop, val)
            except Exception as e:
                errs.append(prop + ":" + str(e)[:100])
        try:
            ss.set_editor_property("tags_to_add_on_actors", ["RainbowBloom"])
        except Exception as e:
            errs.append("tags:" + str(e)[:100])
        rec["set_errs"] = errs
        try:
            rec["template_rb"] = str(ss.get_editor_property("template_actor").get_actor_label())
        except Exception as e:
            rec["template_rb"] = "READERR " + str(e)[:100]
        try:
            rec["cleanup_rb"] = str(ss.get_editor_property("delete_actors_before_generation"))
        except Exception as e:
            rec["cleanup_rb"] = "READERR " + str(e)[:100]
    except Exception as e:
        rec["err"] = str(e)[:200]
    rep["spawners"].append(rec)
# restore R band raycast link (was bypassed): ray.Out -> spawner.In alongside direct edge is fine (merge); ensure ray wired
try:
    rep["ray_restore"] = bool(g.add_edge(rays[0], "Out", spawners[0], "In"))
except Exception as e:
    rep["ray_restore_err"] = str(e)[:150]
open(OUT, "w").write(json.dumps(rep, indent=1))
print("FINAL_WROTE")
