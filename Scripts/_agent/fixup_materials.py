import json, unreal

KEYWORDS = {
    "nature": "MI_Env_NatureMegaKit", "tree": "MI_Env_NatureMegaKit", "leaf": "MI_Env_NatureMegaKit",
    "grass": "MI_Env_NatureMegaKit", "flower": "MI_Env_NatureMegaKit", "bush": "MI_Env_NatureMegaKit",
    "rock": "MI_Env_NatureMegaKit", "plant": "MI_Env_NatureMegaKit",
    "musical": "MI_Env_MusicalInstruments", "instrument": "MI_Env_MusicalInstruments",
    "piano": "MI_Env_MusicalInstruments", "guitar": "MI_Env_MusicalInstruments", "violin": "MI_Env_MusicalInstruments",
    "cello": "MI_Env_MusicalInstruments", "harp": "MI_Env_MusicalInstruments", "flute": "MI_Env_MusicalInstruments",
    "trumpet": "MI_Env_MusicalInstruments", "oboe": "MI_Env_MusicalInstruments", "lyre": "MI_Env_MusicalInstruments",
    "accordion": "MI_Env_MusicalInstruments", "stage": "MI_Env_MusicalInstruments", "mic": "MI_Env_MusicalInstruments",
    "speaker": "MI_Env_MusicalInstruments",
    "medieval": "MI_Env_MedievalBuilder", "kaykit": "MI_Env_MedievalBuilder", "castle": "MI_Env_CastleKit",
    "knight": "MI_Env_MedievalBuilder", "arch": "MI_Env_MedievalBuilder", "window": "MI_Env_MedievalBuilder",
    "wall": "MI_Env_MedievalBuilder", "column": "MI_Env_MedievalBuilder", "door": "MI_Env_MedievalBuilder",
    "roof": "MI_Env_MedievalBuilder", "gate": "MI_Env_MedievalBuilder", "banner": "MI_Env_CastleKit",
    "tower": "MI_Env_CastleKit", "bridge": "MI_Env_CastleKit",
    "cave": "MI_Env_ModularCave", "grotto": "MI_Env_ModularCave",
    "crystal": "MI_Env_LowPolyCrystals", "lowpoly": "MI_Env_LowPolyCrystals", "gem": "MI_Env_LowPolyCrystals",
    "forest": "MI_Env_MiniForest", "mini": "MI_Env_MiniForest",
    "cross": "MI_Env_MedievalBuilder", "heart": "MI_Env_CastleKit",
    "chair": "MI_Env_CastleKit", "table": "MI_Env_CastleKit", "bed": "MI_Env_CastleKit",
    "carpet": "MI_Env_CastleKit", "furniture": "MI_Env_CastleKit", "cabinet": "MI_Env_CastleKit",
    "arm": "MI_Env_CastleKit", "barrel": "MI_Env_CastleKit", "chest": "MI_Env_CastleKit",
}
FOLDER_DEFAULT = {
    "/Game/EnvSandbox/Meshes/Cathedral": "MI_Env_MedievalBuilder",
    "/Game/EnvSandbox/Meshes/OrnamentMusical": "MI_Env_MusicalInstruments",
    "/Game/EnvSandbox/Meshes/Ornament": "MI_Env_MedievalBuilder",
    "/Game/EnvSandbox/Meshes/Environment": "MI_Env_NatureMegaKit",
}

reg = unreal.AssetRegistryHelpers.get_asset_registry()
assigned = 0
for folder, fallback in FOLDER_DEFAULT.items():
    mi_fallback = unreal.load_asset("/Game/EnvSandbox/Materials/Instances/Environment/ImportedPacks/" + fallback)
    for a in reg.get_assets_by_path(folder, recursive=True):
        if str(a.asset_class_path.asset_name) != "StaticMesh":
            continue
        m = unreal.load_asset(str(a.package_name) + "." + str(a.asset_name))
        if not m:
            continue
        mat0 = m.get_material(0)
        name0 = str(mat0.get_name()) if mat0 else ""
        if name0.startswith("MI_Env_") or name0.startswith("MI_Universal_"):
            continue
        mesh_name = str(a.asset_name).lower()
        mi = None
        for kw, target in KEYWORDS.items():
            if kw in mesh_name:
                mi = unreal.load_asset("/Game/EnvSandbox/Materials/Instances/Environment/ImportedPacks/" + target)
                if mi:
                    break
        if not mi:
            mi = mi_fallback
        if not mi:
            continue
        m.set_material(0, mi)
        unreal.EditorAssetLibrary.save_asset(m.get_path_name())
        assigned += 1
json.dump({"assigned": assigned}, open(r"C:\Users\froma\AppData\Local\Temp\opencode\mi_fixup.json", "w"))
