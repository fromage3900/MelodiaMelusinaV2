import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/rainbow_forge.json"
rep = {"mis": []}
al = unreal.EditorAssetLibrary
am = unreal.AssetToolsHelpers.get_asset_tools()
parent = al.load_asset("/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
BANDS = [
    ("B0_Red", (1.0, 0.18, 0.22)),
    ("B1_Orange", (1.0, 0.45, 0.10)),
    ("B2_Gold", (1.0, 0.80, 0.20)),
    ("B3_Green", (0.35, 0.95, 0.45)),
    ("B4_Blue", (0.30, 0.55, 1.0)),
    ("B5_Indigo", (0.45, 0.30, 0.95)),
    ("B6_Violet", (0.75, 0.35, 1.0)),
]
for label, rgb in BANDS:
    name = "MI_RainbowPetal_" + label
    path = "/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/" + name
    rec = {"mi": path}
    try:
        if al.does_asset_exist(path):
            rec["exists"] = True
        else:
            mi = am.create_asset(name, "/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/",
                                 unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            mi.set_editor_property("parent", parent)
            rec["created"] = True
        g = al.load_asset(path)
        try:
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(g, "BaseTint", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
            rec["tint"] = rgb
        except Exception as e:
            rec["tint_err"] = str(e)[:150]
        for tex_param, tex_path in (("Albedo", "/Game/EnvSandbox/Textures/SurrealFlora/T_Surreal_GhostLotus_Albedo"),
                                    ("EmissiveMap", "/Game/EnvSandbox/Textures/SurrealFlora/T_Surreal_GhostLotus_Emissive"),
                                    ("Normal", "/Game/EnvSandbox/Textures/SurrealFlora/T_Surreal_GhostLotus_Normal")):
            try:
                t = al.load_asset(tex_path)
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(g, tex_param, t)
                rec.setdefault("maps", []).append(tex_param)
            except Exception as e:
                rec.setdefault("map_err", {})[tex_param] = str(e)[:120]
    except Exception as e:
        rec["err"] = str(e)[:200]
    rep["mis"].append(rec)
open(OUT, "w").write(json.dumps(rep, indent=1))
print("FORGE_WROTE")
