import unreal, os, json, time

MI_ROOT = "/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto"
PROGRESS_PATH = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/bulk_mi_progress.json"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

ORPHANS = [
    "BezierDetails","Brick01","Brick02","DefaultMaterial","Foot","KB3D_ATL_AtlasDecalOrnamets",
    "KB3D_ATL_AtlasOrnaments","KB3D_ATL_BrickStoneCleanBlueC","KB3D_ATL_BrickStoneCleanRedB",
    "KB3D_ATL_BrickStoneCleanTrimA","KB3D_ATL_BrickStoneCleanWhiteA","KB3D_ATL_BrickStoneDamagedD",
    "KB3D_ATL_Burlap","KB3D_ATL_FabricSail","KB3D_ATL_FabricTentBlueA","KB3D_ATL_PropsChariot",
    "KB3D_ATL_PropsShields","KB3D_ATL_PropsStele","KB3D_ATL_PropsTrident","KB3D_ATL_SandStoneDamagedWhite",
    "KB3D_ATL_SandStonePaintedBlueA","KB3D_ATL_SandStoneWhiteBBrickDamage","KB3D_ATL_SandStoneWhiteMBrickDamage",
    "KB3D_ATL_ScrollPaperTrim","KB3D_ATL_StoneCleanTrimC","KB3D_ATL_StoneFloorMosaicTrimA",
    "KB3D_ATL_StoneFloorPolishedC","KB3D_ATL_StoneGrayMossy","KB3D_ATL_TerracottaTileB",
    "KB3D_ATL_WoodBrownTrimC","KB3D_ATL_WoodPaintedBlueA","KB3D_ATL_WoodPaintedWhiteA","KB3D_ATL_WoodPlankA",
    "Strings","T_Bling_Rhinestone01","T_Bling_Rhinestone02","T_Bling_Rhinestone03","T_Bling_Rhinestone04",
    "T_Bling_Rhinestone05","T_Bling_Rhinestone06","T_Bling_Rhinestone07","T_Bling_Rhinestone08",
    "T_Bling_Rhinestone09","T_Bling_Rhinestone10","T_Bling_Rhinestone11","T_Bling_Rhinestone12",
    "T_Bling_Rhinestone13","T_Bling_Rhinestone14","T_Bling_Rhinestone15",
    "T_Cathedral_Baptistery_TwelveFoldRosace","T_Cathedral_BasilicaNave_BookmatchedCipollino",
    "T_Cathedral_ByzantineApse_GildedSmalti","T_Cathedral_CloisterWalk_WornTravertine",
    "T_Cathedral_Cosmati_QuincunxGuilloche","T_Cathedral_OpusSectile_ImperialPorphyry",
    "T_Cello","T_ClothTrim_Base4K","T_ClothTrim_Gingham","T_ClothTrim_Linen","T_ClothTrim_Plush",
    "T_Crystal","T_Fabric_AquaticVelvet_CrushedFuzz","T_Fabric_BaroqueFiligreeLace","T_Fabric_BaroqueLace",
    "T_Fabric_CelestialWeave","T_Fabric_ChromaticJacquard_AcanthusBrocade","T_Fabric_GildedBrocade",
    "T_Fabric_GildedJacquard","T_Fabric_GoldEmbroidery","T_Fabric_GoldThreadedEmbroidery",
    "T_Fabric_IridescentCelestialWeave","T_Fabric_IridescentDuchessSatin_ChampagneRose",
    "T_Fabric_OpalescentChiffon_Plisse","T_Fabric_RoyalVelvet","T_Fabric_SheerSilk",
    "T_FarawayMother_Corset_GildedAcanthusBrocade","T_FarawayMother_Cradle_CarvedAlabasterWood",
    "T_FarawayMother_Gown_CelestialSilkJacquard","T_FarawayMother_Mantle_NightSkyVelvet",
    "T_FarawayMother_Ornament_NacreMusicBoxJewel","T_FarawayMother_Veil_AquaticLullabyLace",
    "T_GildedPea","T_Houdini_BaroqueAcanthus_GildedMagentaSilk","T_Houdini_CathedralStainedGlass_RosaceAzurePink",
    "T_Houdini_ChladniAcoustic_UltravioletVelvet","T_Houdini_DifferentialOrganza_NeonHydrangea",
    "T_Houdini_ReactionDiffusion_AmethystLapis","T_Houdini_VoronoiCrystal_PinkSapphire",
    "T_LandscapeGrayscale","T_Leafcool","T_Lookdev_GildedAquaticFiligree_Trim","T_Lookdev_IridescentSilkVelvet",
    "T_Lookdev_WatercolorStudio_CalibPlaster","T_MelodyToken_Heart","T_Melusina_BaroqueAquatic_MosaicTile",
    "T_Melusina_BaroqueTiara_RoseGoldFiligree","T_Melusina_CathedralPearl_MarbleTile",
    "T_Melusina_EtherealVeil_StarlightChantilly","T_Melusina_FrontPanel",
    "T_Melusina_IridescentSiren_ScaleTessellation","T_Melusina_MoonlitHarbor_WaterRippleParquet",
    "T_Melusina_PorcelainMusicBox_KintsugiLapis","T_Melusina_SakuraLullaby_SilkOrganza",
    "T_Melusina_UpdatedShirt","T_Melusina_WatercolourWave_Parquet","T_Note","T_PrettyRock","T_SadRock",
    "T_Sand","T_Stem1","T_Stembell","T_Terrace_MossyGrotto_GlazedTerracotta",
    "T_Terrace_PetalFountain_HexMosaic","T_Terrace_SunkenPlaza_MarbleTessellation",
    "T_Terrace_WaterOrgan_MajolicaTile","T_Treble","T_Trimsheet_Concrete","T_Trimsheet_HeartTiles",
    "T_WaterBase","T_WaterHighlight","T_WaterLayer2","T_WaterLayerMid","T_ZenTrim_Base4K",
    "Untitled_material","ViolinBase","ViolinTop",
    "bling_surface_vol3_01","bling_surface_vol3_02","bling_surface_vol3_03","bling_surface_vol3_04",
    "bling_surface_vol3_05","bling_surface_vol3_06","bling_surface_vol3_07","bling_surface_vol3_08",
    "bling_surface_vol3_09","bling_surface_vol3_10","bling_surface_vol3_11","bling_surface_vol3_12",
    "bling_surface_vol3_13","bling_surface_vol3_14","bling_surface_vol3_15",
    "crystal1","crystal2","crystal3",
]

SUFFIX_MAP = [
    ("_basecolor", "Albedo"), ("_albedo", "Albedo"), ("_bc", "Albedo"),
    ("_normal", "NormalMap"), ("_norm", "NormalMap"), ("_nrm", "NormalMap"),
    ("_roughness", "RoughnessMap"), ("_rough", "RoughnessMap"), ("_rgh", "RoughnessMap"),
    ("_metallic", "MetallicMap"), ("_metal", "MetallicMap"), ("_mtl", "MetallicMap"),
    ("_height", "HeightMap"), ("_hgt", "HeightMap"), ("_disp", "HeightMap"),
    ("_orm", "ORM"),
]

TEXTURE_ROOTS = [
    "/Game/Textures", "/Game/EnvSandbox/Textures", "/Game/Content/Textures",
    "/Game/Melodia/_PROJECT/04_Materials/Textures", "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype",
    "/Game/EnvSandbox/Textures/Melusina", "/Game/EnvSandbox/Textures/Melodia",
]

def main():
    # Load progress
    done = set()
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH) as f:
            done = set(json.load(f).get("done", []))
    print(f"[resume] {len(done)} orphans already completed")

    # Index textures
    print("[scan] indexing textures...")
    tex_index = {}  # lowercase name -> full path
    for root in TEXTURE_ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True):
            name = p.split("/")[-1]
            tex_index[name.lower()] = p
    print(f"[scan] indexed {len(tex_index)} texture assets")

    # Get parent params
    parent = unreal.load_asset(PARENT)
    parent_tex = set(unreal.MaterialEditingLibrary.get_texture_parameter_names(parent) or [])
    print(f"[master] texture params: {sorted(parent_tex)}")

    if not unreal.EditorAssetLibrary.does_directory_exist(MI_ROOT):
        unreal.EditorAssetLibrary.make_directory(MI_ROOT)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    created = 0
    no_tex = 0

    for stem in ORPHANS:
        if stem in done:
            continue
        
        mi_name = f"MI_Orphan_{stem}"
        mi_path = f"{MI_ROOT}/{mi_name}"
        
        # Skip if already exists
        if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            done.add(stem)
            continue
        
        # Find textures matching this stem
        stem_lower = stem.lower()
        matches = {}
        for name_lower, path in tex_index.items():
            if not name_lower.startswith(stem_lower):
                continue
            rest = name_lower[len(stem_lower):]
            for suffix, param in SUFFIX_MAP:
                if rest.startswith(suffix) or name_lower.endswith(suffix):
                    if param not in matches:
                        matches[param] = path
                    break
        
        if not matches:
            no_tex += 1
            done.add(stem)
            continue
        
        # Create MI (skip check already done above)
        mi = tools.create_asset(mi_name, MI_ROOT, unreal.MaterialInstanceConstant, None)
        if not mi:
            continue
        mi.set_editor_property("parent", parent)
        
        # Bind textures
        bound = 0
        for param, tex_path in matches.items():
            if param in parent_tex:
                tex = unreal.load_asset(tex_path)
                if tex:
                    try:
                        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, param, tex)
                        bound += 1
                    except:
                        pass
        
        if bound > 0:
            try:
                unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
            except:
                pass
            created += 1
            print(f"  [ok] {mi_name}: {bound} textures")
        else:
            # Delete empty MI
            try:
                unreal.EditorAssetLibrary.delete_asset(mi_path)
            except:
                pass
        
        done.add(stem)
        
        # Save progress every 5
        if created % 5 == 0:
            with open(PROGRESS_PATH, 'w') as f:
                json.dump({"done": list(done), "failed": []}, f)
    
    # Final save
    with open(PROGRESS_PATH, 'w') as f:
        json.dump({"done": list(done), "failed": []}, f)
    
    print(f"\n[done] created={created} no_tex={no_tex}")
    print(f"[done] MIs at {MI_ROOT}/")

if __name__ == "__main__":
    main()
