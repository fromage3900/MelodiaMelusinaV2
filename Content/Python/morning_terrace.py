import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_terrace.json"
rep = {}
al = unreal.EditorAssetLibrary
try:
    plane = al.load_asset("/Engine/BasicShapes/Plane")
    mi = al.load_asset("/Game/EnvSandbox/Materials/Instances/Tilable/SurrealCobble/MI_Tilable_SurrealCobble_MoonlitCobble_R060_Tile4")
    if plane is None or mi is None:
        rep = {"ok": False, "plane": bool(plane), "mi": bool(mi)}
    else:
        t = al.load_asset(
            "/Game/EnvSandbox/Textures/SurrealCobble/T_SurrealCobble_MoonlitCobble_BaseColor")
        av = None
        if t is not None:
            try:
                from unreal import MaterialEditingLibrary as MEL
                parent = al.load_asset("/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
                _ = MEL.get_texture_parameter_names(parent)
                av = "master_params_readable"
            except Exception as e:
                av = "ERR " + str(e)[:100]
        rep["albedo_check"] = av
        w = unreal.EditorLevelLibrary.spawn_actor_from_object(
            plane, unreal.Vector(-950.0, 2300.0, -648.0), unreal.Rotator(0, 0, 0))
        w.set_actor_label("Morning_Dell_Terrace")
        w.set_actor_scale3d(unreal.Vector(14.0, 14.0, 1.0))
        comp = w.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_editor_property("override_materials", [mi])
        rep.update({"ok": True, "loc": [-950.0, 2300.0, -648.0]})
except Exception as e:
    rep = {"ok": False, "err": str(e)[:200]}
open(OUT, "w").write(json.dumps(rep, indent=1))
print("TERRACE_WROTE " + json.dumps(rep))
