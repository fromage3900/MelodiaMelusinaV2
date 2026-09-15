import unreal, json, os

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/eigen_lotus_import.json"
rep = {"imported": [], "failed": []}
JOBS = [
    ("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/eigenplate",
     "/Game/EnvSandbox/Textures/Eigenplate", ["Height", "Normal"]),
    ("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/surreal_sweep/flora/textures",
     "/Game/EnvSandbox/Textures/SurrealFlora", None),
]
at = unreal.AssetToolsHelpers.get_asset_tools()
for src, dest, kinds in JOBS:
    if not os.path.isdir(src):
        rep["failed"].append(src + " NO DIR")
        continue
    for f in sorted(os.listdir(src)):
        if not f.endswith(".png"):
            continue
        if kinds and not any(k in f for k in kinds):
            continue
        stem = os.path.splitext(f)[0]
        try:
            task = unreal.AssetImportTask()
            task.filename = os.path.join(src, f)
            task.destination_path = dest
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
        name = obj.split(".")[-1]
        is_color = name.endswith("_Albedo") or name.endswith("_BaseColor")
        try:
            tex.set_editor_property("srgb", is_color)
        except Exception:
            pass
        if name.endswith("_Normal"):
            try:
                tex.set_editor_property(
                    "compression_settings",
                    unreal.TextureCompressionSettings.TC_NORMALMAP)
            except Exception:
                pass
    except Exception:
        pass
open(OUT, "w").write(json.dumps(rep, indent=1))
print("LOTUSINGEST_WROTE imported=%d failed=%d" % (len(rep["imported"]), len(rep["failed"])))
