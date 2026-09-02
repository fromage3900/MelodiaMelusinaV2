import unreal

# Apply all Copernicus MIs to cathedral pieces
actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]

# Get all MIs
mi_dir = "/Game/EnvSandbox/Materials/Instances/Copernicus/"
mis = unreal.EditorAssetLibrary.list_assets(mi_dir)
mis = [m for m in mis if "MI_Copernicus_" in m]

# Load MI objects
mi_objs = {}
for m in mis:
    obj = unreal.EditorAssetLibrary.load_asset(m)
    if obj:
        mi_objs[m.split(".")[-2]] = obj

print(f"Loaded {len(mi_objs)} MIs")
print(f"Applying to {len(sma)} cathedral pieces...")

applied = 0
for i, actor in enumerate(sma):
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not comp:
        continue
    
    label = actor.get_actor_label()
    
    # Pick MI based on label keywords
    mi = None
    label_lower = label.lower()
    
    if "arch" in label_lower or "column" in label_lower or "pier" in label_lower:
        mi = mi_objs.get("MI_Copernicus_CavernWeave") or mi_objs.get("MI_Copernicus_ChoirStone")
    elif "bench" in label_lower or "chair" in label_lower or "table" in label_lower or "stool" in label_lower:
        mi = mi_objs.get("MI_Copernicus_PearlWeave") or mi_objs.get("MI_Copernicus_SingingSilk")
    elif "tree" in label_lower or "shrub" in label_lower or "ivy" in label_lower:
        mi = mi_objs.get("MI_Copernicus_FrostBloom") or mi_objs.get("MI_Copernicus_FrozenFracture")
    elif "window" in label_lower or "portal" in label_lower or "rose" in label_lower:
        mi = mi_objs.get("MI_Copernicus_CrystalCathedral") or mi_objs.get("MI_Copernicus_FractalCathedral")
    elif "altar" in label_lower or "stall" in label_lower or "chandelier" in label_lower:
        mi = mi_objs.get("MI_Copernicus_GildedCoral") or mi_objs.get("MI_Copernicus_MoltenCore")
    elif "buttress" in label_lower or "wall" in label_lower or "parapet" in label_lower:
        mi = mi_objs.get("MI_Copernicus_CavernWeave") or mi_objs.get("MI_Copernicus_ChoirStone")
    elif "vault" in label_lower or "spire" in label_lower or "tower" in label_lower:
        mi = mi_objs.get("MI_Copernicus_StarlitLoom") or mi_objs.get("MI_Copernicus_SpiralMonument")
    elif "tracery" in label_lower or "garland" in label_lower or "relief" in label_lower:
        mi = mi_objs.get("MI_Copernicus_DancingCrystals") or mi_objs.get("MI_Copernicus_EnchantedTome")
    elif "stained" in label_lower or "glass" in label_lower or "panel" in label_lower:
        mi = mi_objs.get("MI_Copernicus_CherryBlossomWood") or mi_objs.get("MI_Copernicus_SingingConstellations")
    elif "orb" in label_lower or "harmonic" in label_lower or "music" in label_lower:
        mi = mi_objs.get("MI_Copernicus_CymaticReactive")
    else:
        mi = mis[i % len(mis)] if mis else None
    
    if mi:
        try:
            comp.set_editor_property("override_materials", [mi])
            applied += 1
        except:
            pass

print(f"Applied MIs to {applied} pieces")
unreal.EditorLevelLibrary.save_current_level()
print("Saved.")
