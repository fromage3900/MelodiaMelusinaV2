import unreal, json, os

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/cobble_tex_import.json"
rep = {"imported": [], "failed": [], "fixed": []}
SRC = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/copernicus_cobble"
DEST = "/Game/EnvSandbox/Textures/SurrealCobble"
LINEAR = ("Normal", "Roughness", "Metallic", "Height", "ORM", "Iridescence", "MovingPearlMask")

at = unreal.AssetToolsHelpers.get_asset_tools()
files = sorted([f for f in os.listdir(SRC) if f.endswith(".png") and "MoonlitCobble" in f])
for f in files:
    stem = os.path.splitext(f)[0]
    try:
        task = unreal.AssetImportTask()
        task.filename = os.path.join(SRC, f)
        task.destination_path = DEST
        task.destination_name = stem
        task.replace_existing = True
        task.automated = True
        task.save = True
        at.import_asset_tasks([task])
        for obj in task.imported_object_paths or []:
            rep["imported"].append(obj)
    except Exception as e:
        rep["failed"].append(f + " ERR " + str(e)[:150])

al = unreal.EditorAssetLibrary
for obj in rep["imported"]:
    try:
        tex = al.load_asset(obj)
        if tex is None:
            continue
        is_linear = any(k in obj for k in LINEAR)
        try:
            tex.set_editor_property("srgb", not is_linear)
        except Exception:
            pass
        if "Normal" in obj:
            try:
                tex.set_editor_property(
                    "compression_settings",
                    unreal.TextureCompressionSettings.TC_NORMALMAP)
            except Exception:
                pass
        rep["fixed"].append(obj.split(".")[-1])
    except Exception as e:
        rep["failed"].append(obj + " FIX ERR " + str(e)[:100])

open(OUT, "w").write(json.dumps(rep, indent=1))
print("TEXIMPORT_WROTE imported=%d failed=%d" % (len(rep["imported"]), len(rep["failed"])))
